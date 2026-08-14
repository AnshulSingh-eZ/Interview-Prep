from sqlalchemy import Column, String, Float, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base

class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    behavioral_weight = Column(Float, default=0.0)
    resume_weight = Column(Float, default=0.0)
    dsa_weight = Column(Float, default=0.0)
    cs_weight = Column(Float, default=0.0)
    focus_topics = Column(JSON, default=list)  # list of strings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
