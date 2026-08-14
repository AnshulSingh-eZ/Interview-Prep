"""
Roadmap service: generates a personalized study roadmap based on weak topics,
company focus, and readiness. Stores results in PreparationPlan.
"""
import uuid
import logging
from typing import Dict, List, Any

from sqlalchemy.orm import Session

from app.models.topic_score import TopicScore
from app.models.company import CompanyProfile
from app.models.preparation_plan import PreparationPlan

logger = logging.getLogger(__name__)

# Study tasks per topic
TOPIC_TASKS: Dict[str, List[str]] = {
    "OS": [
        "Revise Deadlocks and Mutex",
        "Study Process Scheduling algorithms",
        "Practice Virtual Memory and Paging problems",
        "Review Semaphores and Synchronization",
    ],
    "DBMS": [
        "Revise Normalization (1NF–BCNF)",
        "Practice SQL Joins and Subqueries",
        "Study Indexing and Query Optimization",
        "Review Transactions and ACID properties",
    ],
    "CN": [
        "Revise OSI Model and TCP/IP stack",
        "Study HTTP vs HTTPS and REST",
        "Practice Subnetting problems",
        "Review DNS, CDN, and Load Balancers",
    ],
    "DSA": [
        "Solve 3 Graph problems (BFS/DFS)",
        "Solve 2 Dynamic Programming problems",
        "Revise Tree traversals and BST operations",
        "Practice Sliding Window and Two Pointer patterns",
    ],
    "Behavioral": [
        "Write STAR stories for 5 Leadership Principles",
        "Practice conflict resolution and ownership stories",
        "Mock behavioral interview with a peer",
    ],
    "Resume": [
        "Polish 2 resume project descriptions with metrics",
        "Prepare to deep-dive on your most complex project",
        "Update skills section to match target company stack",
    ],
}

SYSTEM_DESIGN_TASKS = [
    "Design a URL shortener (LLD + HLD)",
    "Design a rate limiter",
    "Design a distributed cache (Redis patterns)",
]


def _get_weak_topics(db: Session, user_id: uuid.UUID) -> List[str]:
    rows = db.query(TopicScore).filter(TopicScore.user_id == user_id).all()
    # Score < 6/10 = weak
    return [r.topic for r in rows if r.average_score < 6.0]


def _get_company_focus(company: CompanyProfile) -> List[str]:
    return company.focus_topics or []


def generate_roadmap(db: Session, *, user_id: uuid.UUID, company_id: str) -> Dict[str, Any]:
    """
    Generate a 7-day personalized study roadmap.
    Logic:
      - Days 1-3: Weak topics (40% allocation)
      - Days 4-5: Company focus areas (30% allocation)
      - Days 6-7: Resume polish + System Design (30% allocation)
    Saves to PreparationPlan and returns the plan JSON.
    """
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    if not company:
        raise ValueError("Company not found.")

    weak_topics = _get_weak_topics(db, user_id)
    company_focus = _get_company_focus(company)

    plan: Dict[str, List[str]] = {}

    # Days 1-3: Weak topics (cycle through them)
    weak_queue = list(weak_topics) or ["DSA"]  # default to DSA if no weak topics
    for day_num in range(1, 4):
        topic = weak_queue[(day_num - 1) % len(weak_queue)]
        tasks = TOPIC_TASKS.get(topic, [f"Study and practice {topic}"])
        plan[f"day{day_num}"] = tasks[:2]  # 2 tasks per day

    # Days 4-5: Company focus topics
    # Map focus topic strings to our known categories
    focus_categories = []
    for f in company_focus:
        for cat in ["OS", "DBMS", "CN", "DSA", "Behavioral", "Resume"]:
            if cat.lower() in f.lower() or f.lower() in cat.lower():
                if cat not in focus_categories:
                    focus_categories.append(cat)

    if not focus_categories:
        focus_categories = ["DSA", "Behavioral"]

    for i, day_num in enumerate([4, 5]):
        topic = focus_categories[i % len(focus_categories)]
        tasks = TOPIC_TASKS.get(topic, [f"Study {topic} for {company.name}"])
        plan[f"day{day_num}"] = tasks[:2]
        # Add company-specific context
        plan[f"day{day_num}"].append(
            f"Review {company.name} interview experiences for {topic}"
        )

    # Day 6: Resume polish
    plan["day6"] = TOPIC_TASKS["Resume"][:2] + [
        f"Research {company.name}'s products and tech stack"
    ]

    # Day 7: System Design + Mock Interview
    plan["day7"] = SYSTEM_DESIGN_TASKS[:2] + [
        f"Full mock interview targeting {company.name} style",
        "Review all weak topics one more time",
    ]

    # Persist the plan (upsert: replace latest for this user)
    existing = db.query(PreparationPlan).filter(PreparationPlan.user_id == user_id).first()
    if existing:
        existing.plan_json = plan
        db.commit()
        db.refresh(existing)
    else:
        prep = PreparationPlan(user_id=user_id, plan_json=plan)
        db.add(prep)
        db.commit()
        db.refresh(prep)

    logger.info("Generated roadmap for user=%s company=%s", user_id, company.name)
    return plan
