from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.resume import Resume
from app.auth.dependencies import get_current_user
from app.services.resume_parser import extract_text_from_pdf
from app.services.resume_structurer import structure_resume

router = APIRouter(
    prefix="/resume", 
    tags=["Resume"]
)

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
        raw_text = extract_text_from_pdf(
            file.file
        )
        parsed_data = structure_resume(
            raw_text
        )
        resume = Resume(
            user_id=current_user.id,
            raw_text=raw_text,
            parsed_data=parsed_data
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        return {
            "resume_id": str(resume.id),
            "message": "Resume uploaded successfully"
        }