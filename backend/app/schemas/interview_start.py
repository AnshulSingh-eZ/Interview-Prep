from pydantic import BaseModel, Field
from typing import List

class InterviewStartOut(BaseModel):
    session_id: str = Field(..., description="UUID of the created InterviewSession")
    questions: List[dict] = Field(..., description="List of generated questions with their ids, category and difficulty")

    class Config:
        orm_mode = True
