from pydantic import BaseModel, Field
from typing import List, Optional

class InterviewQuestionCreate(BaseModel):
    session_id: str = Field(..., description="InterviewSession UUID")
    question: str
    category: str
    difficulty: Optional[float] = Field(0.0, ge=0, le=100)

class InterviewQuestionOut(BaseModel):
    id: str
    session_id: str
    question: str
    category: str
    difficulty: float
    created_at: str

    class Config:
        orm_mode = True
