import uuid
from typing import List, Dict

from sqlalchemy.orm import Session

from app.models.company import CompanyProfile
from app.models.topic_score import TopicScore
from app.models.interview_session import InterviewSession
from app.models.interview_response import InterviewResponse
from app.models.interview_question import InterviewQuestion

# Utility: fetch or default score for a topic (0-10 scale)
def _topic_score_lookup(scores: Dict[str, TopicScore], topic: str) -> float:
    ts = scores.get(topic)
    return ts.average_score if ts else 0.0

def _fetch_user_topic_scores(db: Session, user_id: uuid.UUID) -> Dict[str, TopicScore]:
    rows = db.query(TopicScore).filter(TopicScore.user_id == user_id).all()
    return {row.topic: row for row in rows}

def calculate_readiness(db: Session, *, user_id: uuid.UUID, company_id: str) -> Dict:
    """Calculate company‑specific readiness for a user.

    Returns a dict matching the ``ReadinessOut`` schema.
    Uses the company profile's weight fields (behavioral_weight, resume_weight,
    dsa_weight, cs_weight) and the user’s historical TopicScores.
    """
    # 1️⃣ fetch company profile and weights
    company: CompanyProfile = (
        db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    )
    if not company:
        raise ValueError("Company profile not found")

    # Default weight dict (percentage values). If a weight is missing treat as 0.
    weights = {
        "Behavioral": company.behavioral_weight or 0.0,
        "Resume": company.resume_weight or 0.0,
        "DSA": company.dsa_weight or 0.0,
        # CS fundamentals weight is stored in cs_weight – we map it to the "CS" topic.
        "CS": company.cs_weight or 0.0,
    }

    # 2️⃣ fetch user's topic scores
    user_scores = _fetch_user_topic_scores(db, user_id)

    # 3️⃣ compute per‑category percentage scores (scale 0‑10 -> 0‑100)
    per_category = {}
    for cat in weights.keys():
        raw = _topic_score_lookup(user_scores, cat)
        per_category[cat] = round(raw * 10, 2)  # convert to 0‑100 scale

    # 4️⃣ weighted overall readiness (weights sum to 100)
    overall = 0.0
    for cat, weight in weights.items():
        overall += per_category.get(cat, 0.0) * (weight / 100.0)
    overall = round(overall, 2)

    # 5️⃣ expose the full response structure (include OS, DBMS, CN even if weight 0)
    result = {
        "readiness_score": overall,
        "resume_score": per_category.get("Resume", 0.0),
        "behavioral_score": per_category.get("Behavioral", 0.0),
        "dsa_score": per_category.get("DSA", 0.0),
        "os_score": per_category.get("OS", 0.0),
        "dbms_score": per_category.get("DBMS", 0.0),
        "cn_score": per_category.get("CN", 0.0),
    }
    return result

def get_weak_topics(db: Session, *, user_id: uuid.UUID) -> List[Dict[str, float]]:
    """Return topics whose average score is below the weak‑threshold (6/10).

    The response matches ``WeakTopicsOut`` – a list of ``{"topic": str, "score": float}``.
    Scores are reported on a 0‑100 scale for consistency with the readiness API.
    """
    rows = db.query(TopicScore).filter(TopicScore.user_id == user_id).all()
    weak = []
    for row in rows:
        if row.average_score < 6.0:  # threshold on 0‑10 scale
            weak.append({"topic": row.topic, "score": round(row.average_score * 10, 2)})
    return weak

def get_history(db: Session, *, user_id: uuid.UUID) -> List[Dict]:
    """Return a list of past interview sessions with aggregate scores.

    Each entry contains ``session_id``, the associated company name, the
    overall session score (average of all response scores, scaled to 0‑100),
    and the creation timestamp.
    """
    sessions = (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == user_id)
        .order_by(InterviewSession.created_at.desc())
        .all()
    )
    history = []
    for sess in sessions:
        # fetch all responses belonging to this session
        responses = (
            db.query(InterviewResponse)
            .join(InterviewQuestion, InterviewResponse.question_id == InterviewQuestion.id)
            .filter(InterviewQuestion.session_id == sess.id)
            .all()
        )
        if responses:
            avg_score = sum(r.score for r in responses) / len(responses)
            avg_score = round(avg_score * 10, 2)  # 0‑10 -> 0‑100
        else:
            avg_score = 0.0
        # fetch company name
        company = db.query(CompanyProfile).filter(CompanyProfile.id == sess.company_id).first()
        company_name = company.name if company else "Unknown"
        history.append(
            {
                "session_id": str(sess.id),
                "company": company_name,
                "score": avg_score,
                "created_at": sess.created_at,
            }
        )
    return history
