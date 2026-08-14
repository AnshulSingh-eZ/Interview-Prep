from pydantic import BaseModel, Field
from typing import List, Optional

class InterviewAnswerCreate(BaseModel):
    question_id: str = Field(..., description="UUID of the InterviewQuestion being answered")
    answer: str = Field(..., description="User's textual answer")

class InterviewAnswerOut(BaseModel):
    id: str
    question_id: str
    answer: str
    score: float
    feedback: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    created_at: str

    class Config:
        orm_mode = True
