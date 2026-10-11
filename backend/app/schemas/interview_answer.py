from pydantic import BaseModel, Field
from typing import List, Optional

class InterviewAnswerCreate(BaseModel):
    question_id: str = Field(..., description="UUID of the InterviewQuestion being answered")
    answer: str = Field(..., description="User's textual answer")

class FollowupQuestionOut(BaseModel):
    id: str
    number: int
    category: str
    text: str
    difficulty: float = 50
    is_followup: bool = True


class InterviewAnswerOut(BaseModel):
    id: str
    question_id: str
    answer: str
    score: float
    feedback: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    created_at: str
    followups: List[FollowupQuestionOut] = Field(default_factory=list)

    class Config:
        orm_mode = True
