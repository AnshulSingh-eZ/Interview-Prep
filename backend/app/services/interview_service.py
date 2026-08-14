"""
Core interview service: start_interview, submit_answer, get_results.

Adaptive logic (Phase 3):
  - Fetches existing TopicScores for the user.
  - Identifies weakest topics (score < 6/10).
  - Biases question generation: 40% weak topics, 30% company focus, 30% resume.
"""
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
from app.services.evaluation_service import generate_interview_questions, evaluate_answer, generate_mode_questions

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


def start_interview(
    db: Session,
    *,
    user_id: uuid.UUID,
    company_ids: List[str],
) -> Tuple[uuid.UUID, List[Dict[str, Any]]]:
    """
    Create an InterviewSession, generate questions adaptively, persist them.
    Returns (session_id, questions_list).
    """
    resume = _fetch_latest_resume(db, user_id)
    # Validate company selection
    if not company_ids:
        raise ValueError("At least one company_id must be provided.")
    # Fetch the primary company (first) for distribution and prompt
    company = _fetch_company(db, company_ids[0])

    # Adaptive distribution
    topic_scores = _get_user_topic_scores(db, user_id)
    distribution = _build_adaptive_distribution(topic_scores, company, total_questions=10)

    logger.info(
        "Starting interview for user=%s company=%s distribution=%s",
        user_id, company.name, distribution,
    )

    # Build company dict for Gemini prompt, now includes list of company_ids
    company_dict = {
        "name": company.name,
        "focus_topics": company.focus_topics or [],
        "behavioral_weight": company.behavioral_weight,
        "resume_weight": company.resume_weight,
        "dsa_weight": company.dsa_weight,
        "cs_weight": company.cs_weight,
        "question_distribution": distribution,
        "weak_topics": [t for t, s in topic_scores.items() if s < 6.0],
        "company_ids": company_ids,
    }

    # Generate questions via Gemini (or fallback)
    raw_questions: List[Dict] = generate_interview_questions(
        resume_json=resume.parsed_data or {"raw_text": resume.raw_text[:3000]},
        company_profile=company_dict,
    )

    # Create session
    session = InterviewSession(
        user_id=user_id,
        company_id=uuid.UUID(str(company.id)),
        readiness_before=0.0,
        readiness_after=0.0,
    )
    db.add(session)
    db.flush()  # get session.id without committing

    # Persist questions
    questions_out = []
    for i, q in enumerate(raw_questions[:10]):
        question_text = q.get("question", "")
        category = q.get("category", "General")
        difficulty = float(q.get("difficulty", 50.0))
        iq = InterviewQuestion(
            session_id=session.id,
            question=question_text,
            category=category,
            difficulty=difficulty,
        )
        db.add(iq)
        db.flush()
        questions_out.append({
            "id": str(iq.id),
            "number": i + 1,
            "category": category,
            "text": question_text,
            "difficulty": difficulty,
        })

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

    company_dict = {
        "name": company.name,
        "focus_topics": company.focus_topics or [],
    }

    # Evaluate with Gemini
    eval_result = evaluate_answer(
        answer=answer,
        question=question.question,
        category=question.category,
        resume_json=resume.parsed_data or {"raw_text": resume.raw_text[:3000]},
        company_profile=company_dict,
    )

    score = float(eval_result.get("score", 5.0))
    feedback = eval_result.get("feedback", "")
    strengths = eval_result.get("strengths", [])
    weaknesses = eval_result.get("weaknesses", [])

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

    db.commit()
    db.refresh(response)

    return {
        "id": str(response.id),
        "question_id": str(response.question_id),
        "answer": response.answer,
        "score": response.score,
        "feedback": feedback,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "created_at": response.created_at.isoformat() if response.created_at else "",
    }


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

    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session.id
    ).all()
    question_ids = [q.id for q in questions]
    question_map = {str(q.id): q for q in questions}

    responses = db.query(InterviewResponse).filter(
        InterviewResponse.question_id.in_(question_ids)
    ).all()

    # Group scores by category
    category_scores: Dict[str, List[float]] = {cat: [] for cat in ALL_TOPICS}
    for r in responses:
        q = question_map.get(str(r.question_id))
        if q and q.category in category_scores:
            # Score stored 0-10, convert to 0-100
            category_scores[q.category].append(r.score * 10.0)

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
    answered_scores = [s for _, s in all_scores if s > 0]
    overall_score = round(sum(answered_scores) / len(answered_scores), 1) if answered_scores else 0.0

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
