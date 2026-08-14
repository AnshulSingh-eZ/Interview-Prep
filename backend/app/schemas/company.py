from uuid import UUID
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CompanyCreate(BaseModel):
    name: str = Field(..., example="Amazon")
    behavioral_weight: float = Field(0.0, ge=0, le=100)
    resume_weight: float = Field(0.0, ge=0, le=100)
    dsa_weight: float = Field(0.0, ge=0, le=100)
    cs_weight: float = Field(0.0, ge=0, le=100)
    focus_topics: Optional[List[str]] = None

class CompanyUpdate(BaseModel):
    behavioral_weight: Optional[float] = None
    resume_weight: Optional[float] = None
    dsa_weight: Optional[float] = None
    cs_weight: Optional[float] = None
    focus_topics: Optional[List[str]] = None

class WeightDistribution(BaseModel):
    behavioral: float
    resume: float
    dsa: float
    cs_fundamentals: float

class CompanyOut(BaseModel):
    id: UUID
    name: str
    weight_distribution: WeightDistribution
    focus_topics: List[str]
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
