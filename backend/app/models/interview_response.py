from sqlalchemy import Column, String, Float, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base

class InterviewResponse(Base):
    __tablename__ = "interview_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), nullable=False)
    answer = Column(String, nullable=False)
    score = Column(Float, default=0.0)
    feedback = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
