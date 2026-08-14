import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.company import CompanyProfile
from app.models.resume import Resume
from app.models.interview_question import InterviewQuestion
from app.models.interview_session import InterviewSession
from app.models.interview_response import InterviewResponse
from app.models.preparation_plan import PreparationPlan
from app.models.topic_score import TopicScore

from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.routes.company import router as company_router
from app.routes.users import router as users_router
from app.routes.resume import router as resume_router
from app.routes.interview import router as interview_router
from app.routes.dashboard import router as dashboard_router

from app.db.seed_companies import seed_companies

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed data on startup."""
    logger.info("Creating database tables…")
    Base.metadata.create_all(bind=engine)

    logger.info("Running company seed check…")
    db = SessionLocal()
    try:
        seed_companies(db)
    finally:
        db.close()

    yield  # application runs here


app = FastAPI(
    title="Interview Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow all origins during development. Tighten in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(company_router)
app.include_router(users_router)
app.include_router(resume_router)
app.include_router(interview_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {"message": "Interview Intelligence Platform API", "status": "running"}