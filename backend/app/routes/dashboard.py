import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.schemas.dashboard import ReadinessOut, WeakTopicsOut
from app.services.readiness_service import calculate_readiness, get_weak_topics, get_history
from app.services.roadmap_service import generate_roadmap

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/readiness", response_model=ReadinessOut)
def readiness(
    company_id: str = Query(..., description="Company UUID for which to calculate readiness"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Company-specific readiness score for the authenticated user."""
    try:
        result = calculate_readiness(db, user_id=current_user.id, company_id=company_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/weak-topics", response_model=WeakTopicsOut)
def weak_topics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return topics where the user scores below 60% (6/10)."""
    weak = get_weak_topics(db, user_id=current_user.id)
    return {"weak_topics": weak}


@router.get("/history")
def history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List past interview sessions with aggregate scores, most recent first."""
    return get_history(db, user_id=current_user.id)


@router.get("/roadmap")
def roadmap(
    company_id: str = Query(..., description="Company UUID for roadmap generation"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate a 7-day personalized study roadmap for a company."""
    try:
        plan = generate_roadmap(db, user_id=current_user.id, company_id=company_id)
        return {"roadmap": plan}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Roadmap generation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate roadmap.")
