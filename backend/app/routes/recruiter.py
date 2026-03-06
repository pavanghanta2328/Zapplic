from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud

router = APIRouter(
    prefix="/api/recruiter",
    tags=["Recruiter"]
)


@router.get("/profile/{recruiter_id}")
def get_recruiter_profile(
    recruiter_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetch recruiter profile with total resume count.
    
    Returns:
    - id: Recruiter ID
    - email: Email address
    - full_name: Full name
    - phone_number: Phone number
    - role: "recruiter"
    - total_resumes_uploaded: Count of resumes uploaded by this recruiter
    - created_at: Account creation timestamp
    """
    profile = crud.get_recruiter_profile(db, recruiter_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    
    return {
        "status": "success",
        "recruiter": profile
    }


@router.get("/resume-count/{recruiter_id}")
def get_resume_count(
    recruiter_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the count of resumes uploaded by a recruiter.
    """
    count = crud.get_recruiter_resume_count(db, recruiter_id)
    
    return {
        "status": "success",
        "recruiter_id": recruiter_id,
        "total_resumes_uploaded": count
    }
