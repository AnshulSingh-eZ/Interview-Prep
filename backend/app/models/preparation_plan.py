from sqlalchemy import Column, String, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base

class PreparationPlan(Base):
    __tablename__ = "preparation_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    plan_json = Column(JSON, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
