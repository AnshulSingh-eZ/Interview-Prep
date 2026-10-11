import uuid
from sqlalchemy import Column, Text, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.database import Base


class KnowledgeChunk(Base):
    """One retrieved snippet for a session: resume, job description, or company profile."""

    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    source = Column(String, nullable=False)  # resume | job_description | company
    content = Column(Text, nullable=False)
    embedding = Column(JSONB, nullable=False)
    embed_model = Column(String, nullable=False, default="hash")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
