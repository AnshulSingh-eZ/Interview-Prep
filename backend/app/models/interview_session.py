from sqlalchemy import Column, String, Float, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    readiness_before = Column(Float, default=0.0)
    readiness_after = Column(Float, default=0.0)
    # Store the current interview mode (e.g., DSA, Behavioural, etc.)
    current_mode = Column(String, nullable=False, default="MIXED")
    # History of modes with number of questions attempted per mode
    mode_history = Column(JSON, nullable=False, default=lambda: [])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
