from pydantic import BaseModel, Field, RootModel
from typing import List
from datetime import datetime


class ReadinessOut(BaseModel):
    readiness_score: float = Field(..., description="Overall readiness score (0-100)")
    resume_score: float = Field(..., description="Average resume discussion score")
    behavioral_score: float = Field(..., description="Average behavioral score")
    dsa_score: float = Field(..., description="Average DSA score")
    os_score: float = Field(..., description="Average Operating Systems score")
    dbms_score: float = Field(..., description="Average DBMS score")
    cn_score: float = Field(..., description="Average Computer Networks score")

    model_config = {"from_attributes": True}


class WeakTopicItem(BaseModel):
    topic: str = Field(..., description="Topic name, e.g., OS, CN")
    score: float = Field(..., description="Average score for the topic (0-100)")


class WeakTopicsOut(BaseModel):
    weak_topics: List[WeakTopicItem]

    model_config = {"from_attributes": True}


class HistoryItem(BaseModel):
    session_id: str
    company: str
    score: float
    created_at: datetime

    model_config = {"from_attributes": True}


# Pydantic v2: use RootModel instead of __root__
class HistoryOut(RootModel[List[HistoryItem]]):
    pass
