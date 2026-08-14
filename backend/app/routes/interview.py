import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.schemas.interview_start import InterviewStartOut
from app.schemas.interview_answer import InterviewAnswerCreate, InterviewAnswerOut
from app.schemas.interview_result import InterviewResultOut
from app.models.interview_session import InterviewSession
from app.models.interview_question import InterviewQuestion
from app.services.interview_service import start_interview, submit_answer, get_results, get_mode_questions
from typing import List, Dict, Any
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/interview",
    tags=["Interview"]
)


@router.post("/start", response_model=InterviewStartOut, status_code=status.HTTP_201_CREATED)
def interview_start(
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Start a new interview session for the authenticated user.
    Expected payload: {"company_id": "<uuid>"}
    """
    company_ids = payload.get("company_ids")
    if not company_ids or not isinstance(company_ids, list):
        raise HTTPException(status_code=400, detail="company_ids must be a non-empty list")
    try:
        session_id, questions = start_interview(
            db, user_id=current_user.id, company_ids=company_ids
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to start Interview.")
        raise HTTPException(status_code=500, detail="Failed to start interview. Please try again.")
    return {"session_id": str(session_id), "questions": questions}


@router.get("/{session_id}/questions")
def interview_questions(
    session_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Fetch all questions for an existing session."""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    questions = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.session_id == session.id)
        .order_by(InterviewQuestion.created_at)
        .all()
    )
    return [
        {
            "id": str(q.id),
            "number": i + 1,
            "category": q.category,
            "text": q.question,
            "difficulty": q.difficulty,
        }
        for i, q in enumerate(questions)
    ]


@router.post("/{session_id}/answer", response_model=InterviewAnswerOut)
def interview_answer(
    session_id: str,
    payload: InterviewAnswerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Submit an answer for a specific question in a session."""
    try:
        result = submit_answer(
            db,
            user_id=current_user.id,
            session_id=session_id,
            question_id=payload.question_id,
            answer=payload.answer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to submit answer: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to evaluate answer. Please try again.")
    return result

# New endpoint to update interview mode
@router.patch("/{session_id}/mode")
def interview_mode_update(
    session_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update the current interview mode for an active session."""
    new_mode = payload.get("mode")
    if not new_mode:
        raise HTTPException(status_code=400, detail="Mode must be provided.")
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    # Update mode and history
    session.current_mode = new_mode
    history = session.mode_history or []
    if not history or history[-1]["mode"] != new_mode:
        history.append({"mode": new_mode, "questions_attempted": 0})
    session.mode_history = history
    
    # Update local topic score (logic hypothetical placeholder)
    # _update_topic_score(db, user_id=user_id, topic=question.category, new_score=score)

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

@router.get("/{session_id}/mode_questions", response_model=List[Dict[str, Any]])
def interview_mode_questions(
    session_id: str,
    mode: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Fetch mode‑specific questions for an active interview session.
    Query param `mode` should match one of the defined modes (e.g., "Technical DSA" or "System Design").
    """
    try:
        questions = get_mode_questions(
            db,
            user_id=current_user.id,
            session_id=session_id,
            mode=mode,
        )
        return questions
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to fetch mode questions.")
        raise HTTPException(status_code=500, detail="Unable to retrieve mode questions.")




@router.get("/{session_id}/results", response_model=InterviewResultOut)
def interview_results(
    session_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get aggregated results for a completed interview session."""
    try:
        return get_results(db, user_id=current_user.id, session_id=session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to get results: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve results.")
