"""
Company seeding: called once at startup if the company_profiles table is empty.
All weights must sum to 100 per company.
"""
import logging
from sqlalchemy.orm import Session
from app.models.company import CompanyProfile

logger = logging.getLogger(__name__)

SEED_COMPANIES = [
    {
        "name": "Amazon",
        "behavioral_weight": 35.0,
        "resume_weight": 25.0,
        "dsa_weight": 25.0,
        "cs_weight": 15.0,
        "focus_topics": ["Leadership Principles", "Graphs", "Dynamic Programming", "System Design", "OS"],
    },
    {
        "name": "Google",
        "behavioral_weight": 15.0,
        "resume_weight": 25.0,
        "dsa_weight": 50.0,
        "cs_weight": 10.0,
        "focus_topics": ["Graphs", "Dynamic Programming", "Trees", "System Design", "Coding Efficiency"],
    },
    {
        "name": "Microsoft",
        "behavioral_weight": 20.0,
        "resume_weight": 25.0,
        "dsa_weight": 35.0,
        "cs_weight": 20.0,
        "focus_topics": ["Trees", "Graphs", "System Design", "OOP", "DBMS"],
    },
    {
        "name": "Adobe",
        "behavioral_weight": 20.0,
        "resume_weight": 30.0,
        "dsa_weight": 30.0,
        "cs_weight": 20.0,
        "focus_topics": ["OOP", "Dynamic Programming", "Arrays", "System Design", "CN"],
    },
    {
        "name": "Atlassian",
        "behavioral_weight": 30.0,
        "resume_weight": 25.0,
        "dsa_weight": 25.0,
        "cs_weight": 20.0,
        "focus_topics": ["Agile", "System Design", "Graphs", "DBMS", "CN"],
    },
    {
        "name": "Uber",
        "behavioral_weight": 20.0,
        "resume_weight": 20.0,
        "dsa_weight": 35.0,
        "cs_weight": 25.0,
        "focus_topics": ["Distributed Systems", "Graphs", "Concurrency", "OS", "System Design"],
    },
    {
        "name": "Walmart",
        "behavioral_weight": 30.0,
        "resume_weight": 25.0,
        "dsa_weight": 25.0,
        "cs_weight": 20.0,
        "focus_topics": ["System Design", "DBMS", "Java", "Microservices", "CN"],
    },
    {
        "name": "Apple",
        "behavioral_weight": 25.0,
        "resume_weight": 30.0,
        "dsa_weight": 30.0,
        "cs_weight": 15.0,
        "focus_topics": ["OOP", "Memory Management", "Concurrency", "System Design", "OS"],
    },
    {
        "name": "Goldman Sachs",
        "behavioral_weight": 25.0,
        "resume_weight": 30.0,
        "dsa_weight": 30.0,
        "cs_weight": 15.0,
        "focus_topics": ["Dynamic Programming", "Arrays", "DBMS", "System Design", "CN"],
    },
    {
        "name": "Flipkart",
        "behavioral_weight": 25.0,
        "resume_weight": 20.0,
        "dsa_weight": 35.0,
        "cs_weight": 20.0,
        "focus_topics": ["System Design", "Graphs", "Dynamic Programming", "OS", "DBMS"],
    },
]


def seed_companies(db: Session) -> None:
    """Seed companies if the company_profiles table is empty."""
    count = db.query(CompanyProfile).count()
    if count > 0:
        logger.info("company_profiles table already has %d rows – skipping seed.", count)
        return

    logger.info("Seeding %d companies into company_profiles.", len(SEED_COMPANIES))
    for data in SEED_COMPANIES:
        company = CompanyProfile(**data)
        db.add(company)
    try:
        db.commit()
        logger.info("Company seeding complete.")
    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed companies: %s", exc)
        raise
