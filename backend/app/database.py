import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL") or ""
# SQLAlchemy's plain postgresql:// URL now loads psycopg v3. This project installs psycopg2.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL[len("postgresql://"):]
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL[len("postgres://"):]
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit = False,
    autoflush = False,
    bind = engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_extra_columns() -> None:
    """Add columns introduced after the first create_all, without a migration tool."""
    from sqlalchemy import text

    statements = [
        "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS job_description_id UUID",
        "ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS position INTEGER",
        "ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS parent_question_id UUID",
        "ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS is_followup BOOLEAN NOT NULL DEFAULT FALSE",
    ]
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))