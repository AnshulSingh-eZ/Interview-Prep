import uuid
import json
import logging
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from app.models.company import CompanyProfile
from app.models.interview_session import InterviewSession
from app.models.interview_question import InterviewQuestion
from app.models.interview_response import InterviewResponse
from app.models.resume import Resume
from app.models.topic_score import TopicScore
from app.models.job_description import JobDescription
from app.services.evaluation_service import (
    generate_interview_questions,
    evaluate_answer,
    generate_mode_questions,
    generate_followup_questions,
)
from app.services.jd_parser import parse_job_description
from app.services.rag_service import index_source, retrieve
from app.redis_store import clear_followup_evals, list_followup_evals, save_followup_eval

logger = logging.getLogger(__name__)

# Topic category names used throughout the system (must match TopicScore.topic values)
ALL_TOPICS = ["Resume", "Behavioral", "DSA", "OS", "DBMS", "CN"]

# Mapping from category name to company weight field
CATEGORY_WEIGHT_MAP = {
    "Behavioral": "behavioral_weight",
    "Resume": "resume_weight",
    "DSA": "dsa_weight",
    "OS": "cs_weight",
    "DBMS": "cs_weight",
    "CN": "cs_weight",
}


def _fetch_latest_resume(db: Session, user_id: uuid.UUID) -> Resume:
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == user_id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    if not resume:
        raise ValueError("No resume found. Please upload a resume before starting an interview.")
    return resume


def _fetch_company(db: Session, company_id: str) -> CompanyProfile:
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    if not company:
        raise ValueError(f"Company with id '{company_id}' not found.")
    return company


def _get_user_topic_scores(db: Session, user_id: uuid.UUID) -> Dict[str, float]:
    """Return dict of topic -> average_score (0-10 scale)."""
    rows = db.query(TopicScore).filter(TopicScore.user_id == user_id).all()
    return {row.topic: row.average_score for row in rows}


def _build_adaptive_distribution(
    topic_scores: Dict[str, float],
    company: CompanyProfile,
    total_questions: int = 10,
) -> Dict[str, int]:
    """
    Build the question count per category using adaptive logic:
      - Identify weak topics (score < 6/10).
      - Distribute: 40% to weakest topics, 30% to company focus, 30% baseline.
    Returns {category: count}.
    """
    weak_topics = [t for t, s in topic_scores.items() if s < 6.0]

    # Company focus is derived from which weights are highest
    company_weights = {
        "Behavioral": company.behavioral_weight,
        "Resume": company.resume_weight,
        "DSA": company.dsa_weight,
        # Treat OS, DBMS, CN equally from cs_weight
        "OS": company.cs_weight / 3.0,
        "DBMS": company.cs_weight / 3.0,
        "CN": company.cs_weight / 3.0,
    }
    # Pick the top 3 company-focus topics by weight
    company_focus_topics = sorted(company_weights, key=company_weights.get, reverse=True)[:3]

    # Base allocation: at least 1 question per category across 6 categories
    base_alloc = {cat: 1 for cat in ALL_TOPICS}
    remaining = total_questions - len(ALL_TOPICS)  # = 4 extra questions to distribute

    # Distribute the extras
    if weak_topics:
        # Give ~40% of remaining to weak topics (rounded)
        weak_budget = round(remaining * 0.4)
        company_budget = round(remaining * 0.3)
        for t in weak_topics[:weak_budget]:
            if t in base_alloc:
                base_alloc[t] += 1
        for t in company_focus_topics[:company_budget]:
            if t in base_alloc:
                base_alloc[t] += 1
        # Rest goes to DSA (most universally tested)
        leftover = total_questions - sum(base_alloc.values())
        base_alloc["DSA"] = base_alloc.get("DSA", 0) + max(leftover, 0)
    else:
        # No weak topics yet: follow company weights
        for t in company_focus_topics[:remaining]:
            if t in base_alloc:
                base_alloc[t] += 1
        leftover = total_questions - sum(base_alloc.values())
        base_alloc["DSA"] = base_alloc.get("DSA", 0) + max(leftover, 0)

    return base_alloc


def _company_dict(company: CompanyProfile, topic_scores: Dict[str, float]) -> Dict[str, Any]:
    return {
        "name": company.name,
        "focus_topics": company.focus_topics or [],
        "behavioral_weight": company.behavioral_weight,
        "resume_weight": company.resume_weight,
        "dsa_weight": company.dsa_weight,
        "cs_weight": company.cs_weight,
        "weak_topics": [t for t, s in topic_scores.items() if s < 6.0],
    }


def _resume_document(resume: Resume) -> str:
    parsed = resume.parsed_data or {}
    return f"{resume.raw_text or ''}\n{json.dumps(parsed)[:4000]}"


def _jd_document(raw_text: str, parsed: Dict[str, Any]) -> str:
    return f"{raw_text}\n{json.dumps(parsed)[:3000]}"


def _company_document(company: CompanyProfile) -> str:
    topics = ", ".join(company.focus_topics or [])
    return (
        f"Company: {company.name}. Focus topics: {topics}. "
        f"Interview weights out of 100 — behavioral {company.behavioral_weight}, "
        f"resume {company.resume_weight}, DSA {company.dsa_weight}, "
        f"CS fundamentals {company.cs_weight}."
    )


def _question_payload(question: InterviewQuestion, number: int) -> Dict[str, Any]:
    return {
        "id": str(question.id),
        "number": number,
        "category": question.category,
        "text": question.question,
        "difficulty": question.difficulty,
        "is_followup": bool(question.is_followup),
    }


def start_interview(
    db: Session,
    *,
    user_id: uuid.UUID,
    company_ids: List[str],
    job_description: str,
) -> Tuple[uuid.UUID, List[Dict[str, Any]]]:
    """
    Store the job description, index resume + JD + company, then generate 5 questions
    from the retrieved context.
    """
    resume = _fetch_latest_resume(db, user_id)
    if not company_ids:
        raise ValueError("A company must be selected.")
    jd_text = (job_description or "").strip()
    if len(jd_text) < 40:
        raise ValueError("Paste or upload a job description (at least a short paragraph).")

    company = _fetch_company(db, company_ids[0])
    topic_scores = _get_user_topic_scores(db, user_id)
    company_dict = _company_dict(company, topic_scores)
    parsed_jd = parse_job_description(jd_text)

    job = JobDescription(
        user_id=user_id,
        company_id=uuid.UUID(str(company.id)),
        raw_text=jd_text,
        parsed_data=parsed_jd,
    )
    db.add(job)
    db.flush()

    session = InterviewSession(
        user_id=user_id,
        company_id=uuid.UUID(str(company.id)),
        job_description_id=job.id,
        readiness_before=0.0,
        readiness_after=0.0,
    )
    db.add(session)
    db.flush()

    index_source(db, user_id=user_id, session_id=session.id, source="resume", text=_resume_document(resume))
    index_source(db, user_id=user_id, session_id=session.id, source="job_description", text=_jd_document(jd_text, parsed_jd))
    index_source(db, user_id=user_id, session_id=session.id, source="company", text=_company_document(company))
    db.flush()

    retrieval_query = (
        f"Interview questions for {company.name} role {parsed_jd.get('role_title', '')}. "
        f"Focus: {', '.join(company.focus_topics or [])}. "
        "Candidate skills, projects, experience, and job requirements."
    )
    context = retrieve(db, session_id=session.id, query=retrieval_query, k=5)

    logger.info("Starting interview for user=%s company=%s", user_id, company.name)
    raw_questions: List[Dict] = generate_interview_questions(
        resume_json=resume.parsed_data or {"raw_text": (resume.raw_text or "")[:1500]},
        company_profile=company_dict,
        retrieved_context=context,
    )

    questions_out = []
    for i, q in enumerate(raw_questions[:5]):
        question_text = (q.get("question") or "").strip()
        if not question_text:
            continue
        category = q.get("category") or "General"
        try:
            difficulty = float(q.get("difficulty", 50.0))
        except (TypeError, ValueError):
            difficulty = 50.0
        iq = InterviewQuestion(
            session_id=session.id,
            question=question_text,
            category=category,
            difficulty=difficulty,
            position=i + 1,
            is_followup=False,
        )
        db.add(iq)
        db.flush()
        questions_out.append(_question_payload(iq, i + 1))

    db.commit()
    logger.info("Created session %s with %d questions.", session.id, len(questions_out))
    return session.id, questions_out

def get_mode_questions(db: Session, *, user_id: uuid.UUID, session_id: str, mode: str) -> List[Dict[str, Any]]:
    """Fetch mode‑specific questions for an existing session.

    Parameters
    ----------
    db: Session – DB session.
    user_id: uuid.UUID – current user.
    session_id: str – interview session identifier.
    mode: str – requested interview mode (e.g., "Technical DSA" or "System Design").
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == user_id,
    ).first()
    if not session:
        raise ValueError("Session not found.")

    # Fetch latest resume for the user
    resume = _fetch_latest_resume(db, user_id)

    # Fetch the company (the one stored in the session)
    company = db.query(CompanyProfile).filter(CompanyProfile.id == session.company_id).first()
    if not company:
        raise ValueError("Company not found for session.")

    # Build minimal company dict for Gemini prompts
    company_dict = {
        "name": company.name,
        "focus_topics": company.focus_topics or [],
        "behavioral_weight": company.behavioral_weight,
        "resume_weight": company.resume_weight,
        "dsa_weight": company.dsa_weight,
        "cs_weight": company.cs_weight,
    }

    # Generate mode‑specific questions via evaluation service
    mode_questions = generate_mode_questions(
        mode=mode,
        resume_json=resume.parsed_data or {"raw_text": resume.raw_text[:3000]},
        company_profile=company_dict,
    )
    # Ensure we return a list of dicts with expected keys for the frontend
    formatted = []
    for i, q in enumerate(mode_questions):
        formatted.append({
            "id": str(uuid.uuid4()),  # temporary id for UI – real persistence not needed here
            "number": i + 1,
            "category": q.get("category", mode),
            "text": q.get("question", ""),
            "difficulty": q.get("difficulty", 50.0),
        })
    return formatted

def submit_answer(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: str,
    question_id: str,
    answer: str,
) -> Dict[str, Any]:
    """
    Evaluate the user's answer, persist the response, update TopicScore.
    Returns the InterviewAnswerOut-compatible dict.
    """
    # Validate session ownership
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == user_id,
    ).first()
    if not session:
        raise ValueError("Interview session not found or not owned by this user.")

    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == question_id,
        InterviewQuestion.session_id == session.id,
    ).first()
    if not question:
        raise ValueError("Question not found in this session.")

    # Fetch resume and company for context
    resume = _fetch_latest_resume(db, user_id)
    company = _fetch_company(db, str(session.company_id))

    company_dict = _company_dict(company, _get_user_topic_scores(db, user_id))
    context = retrieve(
        db,
        session_id=session.id,
        query=f"{question.question}\n{answer}",
        k=4,
    )

    eval_result = evaluate_answer(
        answer=answer,
        question=question.question,
        category=question.category,
        resume_json=resume.parsed_data or {"raw_text": (resume.raw_text or "")[:1500]},
        company_profile=company_dict,
        retrieved_context=context,
    )

    score = float(eval_result.get("score", 5.0))
    feedback = eval_result.get("feedback", "")
    strengths = eval_result.get("strengths", [])
    weaknesses = eval_result.get("weaknesses", [])
    prior_answers = (
        db.query(InterviewResponse)
        .filter(InterviewResponse.question_id == question.id)
        .count()
    )

    # Follow-up scores stay in Redis until the interview results are opened.
    if question.is_followup:
        cached = {
            "id": str(uuid.uuid4()),
            "question_id": str(question.id),
            "answer": answer,
            "score": score,
            "feedback": feedback,
            "strengths": strengths if isinstance(strengths, list) else [],
            "weaknesses": weaknesses if isinstance(weaknesses, list) else [],
            "created_at": "",
            "category": question.category,
            "followups": [],
        }
        try:
            save_followup_eval(str(session.id), cached)
            logger.info("Saved follow-up eval in Redis for session %s", session.id)
            return cached
        except Exception:
            logger.warning("Redis unavailable, saving follow-up eval in Postgres instead.")

    # Persist the response
    response = InterviewResponse(
        question_id=question.id,
        answer=answer,
        score=score,
        feedback=json.dumps({
            "feedback": feedback,
            "strengths": strengths,
            "weaknesses": weaknesses,
        }),
    )
    db.add(response)

    # Update TopicScore for this category
    _update_topic_score(db, user_id=user_id, topic=question.category, new_score=score)

    # Increment attempts for current mode in session history
    if session.current_mode:
        hist = session.mode_history or []
        for entry in hist:
            if entry["mode"] == session.current_mode:
                entry["questions_attempted"] = entry.get("questions_attempted", 0) + 1
                break
        else:
            hist.append({"mode": session.current_mode, "questions_attempted": 1})
        session.mode_history = hist
        db.add(session)

    followups_out: List[Dict[str, Any]] = []
    if not question.is_followup and prior_answers == 0:
        raw_followups = generate_followup_questions(
            question=question.question,
            answer=answer,
            category=question.category,
            score=score,
            retrieved_context=context,
            company_profile=company_dict,
        )
        parent_pos = question.position or 0
        later = (
            db.query(InterviewQuestion)
            .filter(
                InterviewQuestion.session_id == session.id,
                InterviewQuestion.position.isnot(None),
                InterviewQuestion.position > parent_pos,
            )
            .all()
        )
        for later_q in later:
            later_q.position = (later_q.position or 0) + len(raw_followups)
        for offset, item in enumerate(raw_followups, start=1):
            text = (item.get("question") or "").strip()
            if not text:
                continue
            try:
                difficulty = float(item.get("difficulty", 55))
            except (TypeError, ValueError):
                difficulty = 55.0
            follow = InterviewQuestion(
                session_id=session.id,
                question=text,
                category=question.category,
                difficulty=difficulty,
                position=parent_pos + offset,
                parent_question_id=question.id,
                is_followup=True,
            )
            db.add(follow)
            db.flush()
            followups_out.append(_question_payload(follow, parent_pos + offset))

    db.commit()
    db.refresh(response)

    return {
        "id": str(response.id),
        "question_id": str(response.question_id),
        "answer": response.answer,
        "score": response.score,
        "feedback": feedback,
        "strengths": strengths if isinstance(strengths, list) else [],
        "weaknesses": weaknesses if isinstance(weaknesses, list) else [],
        "created_at": response.created_at.isoformat() if response.created_at else "",
        "followups": followups_out,
    }


def _flush_followup_evals(db: Session, *, user_id: uuid.UUID, session_id: str) -> None:
    """Copy follow-up evaluations from Redis into Postgres, then drop the Redis key."""
    try:
        cached = list_followup_evals(session_id)
    except Exception:
        logger.warning("Could not read follow-up evals from Redis.")
        return
    if not cached:
        return

    for item in cached:
        already = db.query(InterviewResponse).filter(
            InterviewResponse.question_id == item["question_id"]
        ).first()
        if already:
            continue
        db.add(InterviewResponse(
            question_id=item["question_id"],
            answer=item.get("answer") or "",
            score=float(item.get("score") or 0),
            feedback=json.dumps({
                "feedback": item.get("feedback") or "",
                "strengths": item.get("strengths") or [],
                "weaknesses": item.get("weaknesses") or [],
            }),
        ))
        _update_topic_score(
            db,
            user_id=user_id,
            topic=item.get("category") or "General",
            new_score=float(item.get("score") or 0),
        )
    db.commit()
    try:
        clear_followup_evals(session_id)
    except Exception:
        logger.warning("Follow-up evals were saved, but the Redis key was not deleted.")


def _update_topic_score(db: Session, *, user_id: uuid.UUID, topic: str, new_score: float) -> None:
    """Update rolling average score for a topic."""
    ts = db.query(TopicScore).filter(
        TopicScore.user_id == user_id,
        TopicScore.topic == topic,
    ).first()

    if ts:
        # Rolling average: new_avg = (old_avg * n + new_score) / (n + 1)
        new_avg = (ts.average_score * ts.attempts + new_score) / (ts.attempts + 1)
        ts.average_score = round(new_avg, 4)
        ts.attempts += 1
    else:
        ts = TopicScore(
            user_id=user_id,
            topic=topic,
            average_score=new_score,
            attempts=1,
        )
        db.add(ts)


def get_results(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: str,
) -> Dict[str, Any]:
    """
    Aggregate scores for a session across all 6 categories.
    Returns the InterviewResultOut-compatible dict.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == user_id,
    ).first()
    if not session:
        raise ValueError("Session not found.")

    _flush_followup_evals(db, user_id=user_id, session_id=str(session.id))

    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session.id
    ).all()
    question_ids = [q.id for q in questions]
    question_map = {str(q.id): q for q in questions}

    responses = db.query(InterviewResponse).filter(
        InterviewResponse.question_id.in_(question_ids)
    ).all()

    # Group scores by category. Overall is the average of every answer, including follow-ups.
    category_scores: Dict[str, List[float]] = {cat: [] for cat in ALL_TOPICS}
    all_response_scores: List[float] = []
    for r in responses:
        points = r.score * 10.0
        all_response_scores.append(points)
        q = question_map.get(str(r.question_id))
        if q and q.category in category_scores:
            category_scores[q.category].append(points)

    def avg(lst: List[float]) -> float:
        return round(sum(lst) / len(lst), 1) if lst else 0.0

    resume_score = avg(category_scores["Resume"])
    behavioral_score = avg(category_scores["Behavioral"])
    dsa_score = avg(category_scores["DSA"])
    os_score = avg(category_scores["OS"])
    dbms_score = avg(category_scores["DBMS"])
    cn_score = avg(category_scores["CN"])

    all_scores = [
        ("Resume", resume_score),
        ("Behavioral", behavioral_score),
        ("DSA", dsa_score),
        ("OS", os_score),
        ("DBMS", dbms_score),
        ("CN", cn_score),
    ]
    overall_score = round(sum(all_response_scores) / len(all_response_scores), 1) if all_response_scores else 0.0

    # Determine strong (>= 70) and weak (< 50) topics from answered categories
    strong_topics = [name for name, s in all_scores if s >= 70.0]
    weak_topics = [name for name, s in all_scores if 0 < s < 50.0]

    return {
        "overall_score": overall_score,
        "resume_score": resume_score,
        "behavioral_score": behavioral_score,
        "dsa_score": dsa_score,
        "os_score": os_score,
        "dbms_score": dbms_score,
        "cn_score": cn_score,
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
    }
