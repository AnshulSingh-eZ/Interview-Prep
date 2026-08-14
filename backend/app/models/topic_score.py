from sqlalchemy import Column, String, Float, JSON, DateTime, func, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base

class TopicScore(Base):
    __tablename__ = "topic_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    topic = Column(String, nullable=False)
    average_score = Column(Float, default=0.0)
    attempts = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
