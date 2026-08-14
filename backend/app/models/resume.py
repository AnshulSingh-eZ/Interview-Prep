import uuid
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    raw_text = Column(
        Text,
        nullable=False
    )
    parsed_data = Column(
        JSONB,
        nullable=False
    )
    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )