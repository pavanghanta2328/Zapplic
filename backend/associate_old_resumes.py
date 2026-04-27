"""
Script to associate old resumes (without recruiter_id) with the logged-in recruiter
Run this once to backfill old resume data
"""
from app.database import SessionLocal
from app import models
from sqlalchemy import text

def associate_old_resumes_with_recruiter(recruiter_email: str):
    """
    Associate all old resumes (with NULL uploaded_by_recruiter_id) 
    with the given recruiter
    """
    db = SessionLocal()
    
    try:
        # Get recruiter by email
        recruiter = db.query(models.Recruiter).filter(
            models.Recruiter.email == recruiter_email
        ).first()
        
        if not recruiter:
            print(f"❌ Recruiter with email '{recruiter_email}' not found")
            return
        
        # Update all resumes with NULL recruiter_id to this recruiter
        updated_count = db.query(models.Resume).filter(
            models.Resume.uploaded_by_recruiter_id == None,
            models.Resume.archived == False
        ).update({models.Resume.uploaded_by_recruiter_id: recruiter.id})
        
        db.commit()
        
        print(f"✅ Associated {updated_count} old resumes with recruiter: {recruiter_email}")
        print(f"   Recruiter ID: {recruiter.id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python associate_old_resumes.py <recruiter_email>")
        print("Example: python associate_old_resumes.py pavankarnati44@gmail.com")
        sys.exit(1)
    
    recruiter_email = sys.argv[1]
    associate_old_resumes_with_recruiter(recruiter_email)
