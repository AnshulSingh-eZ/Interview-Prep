from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import CompanyProfile
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyOut
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/companies",
    tags=["Companies"]
)

@router.post("/", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Ensure the name is unique – FastAPI will raise 500 on DB IntegrityError otherwise
    from sqlalchemy.exc import IntegrityError
    try:
        company = CompanyProfile(**payload.dict())
        db.add(company)
        db.commit()
        db.refresh(company)
        return {
            "id": company.id,
            "name": company.name,
            "weight_distribution": {
                "behavioral": company.behavioral_weight,
                "resume": company.resume_weight,
                "dsa": company.dsa_weight,
                "cs_fundamentals": company.cs_weight,
            },
            "focus_topics": company.focus_topics,
            "created_at": company.created_at,
        }
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Company with this name already exists")


@router.get("/", response_model=list[CompanyOut])
def list_companies(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    companies = db.query(CompanyProfile).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "weight_distribution": {
                "behavioral": c.behavioral_weight,
                "resume": c.resume_weight,
                "dsa": c.dsa_weight,
                "cs_fundamentals": c.cs_weight,
            },
            "focus_topics": c.focus_topics,
            "created_at": c.created_at,
        }
        for c in companies
    ]

@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.patch("/{company_id}", response_model=CompanyOut)
def update_company(company_id: str, payload: CompanyUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company

@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return None
