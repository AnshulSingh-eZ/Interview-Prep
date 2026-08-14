from pydantic import BaseModel

class ResumeResponse(BaseModel):
    resume_id: str
    messages: str