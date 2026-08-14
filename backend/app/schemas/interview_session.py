from pydantic import BaseModel, Field
from typing import List, Optional

class InterviewSessionCreate(BaseModel):
    company_id: str = Field(..., description="UUID of the target company profile")
    readiness_before: Optional[float] = Field(0.0, ge=0, le=100)

class InterviewSessionOut(BaseModel):
    id: str
    user_id: str
    company_id: str
    readiness_before: float
    readiness_after: float
    created_at: str

    class Config:
        orm_mode = True
