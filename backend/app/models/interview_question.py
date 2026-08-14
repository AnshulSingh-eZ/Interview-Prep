from sqlalchemy import Column, String, Float, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    question = Column(String, nullable=False)
    category = Column(String, nullable=False)  # e.g., resume, behavioral, cs, dsa
    difficulty = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
