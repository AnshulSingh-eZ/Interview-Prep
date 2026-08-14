from pydantic import BaseModel, Field
from typing import List

class InterviewResultOut(BaseModel):
    overall_score: float = Field(..., description="Overall interview score 0-100")
    resume_score: float = Field(..., description="Resume category score 0-100")
    behavioral_score: float = Field(..., description="Behavioral category score 0-100")
    dsa_score: float = Field(..., description="DSA category score 0-100")
    os_score: float = Field(..., description="OS category score 0-100")
    dbms_score: float = Field(..., description="DBMS category score 0-100")
    cn_score: float = Field(..., description="CN category score 0-100")
    weak_topics: List[str] = Field(default_factory=list)
    strong_topics: List[str] = Field(default_factory=list)

    class Config:
        orm_mode = True
