import os
import traceback
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user
from app import schemas, auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


# ======================================================
# EMAIL AUTH
# ======================================================

@router.post(
    "/signup",
    response_model=schemas.RecruiterResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(data: schemas.RecruiterCreate, db: Session = Depends(get_db)):
    try:
        return auth_service.create_email_user(db, data)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        print("❌ SIGNUP ERROR")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail="Internal server error during signup",
        )


@router.post("/login", response_model=schemas.AuthResponse)
def login(data: schemas.RecruiterLogin, db: Session = Depends(get_db)):
    try:
        return auth_service.login_email_user(db, data)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# ======================================================
# GOOGLE AUTH
# ======================================================

@router.get("/google/login")
def google_login(state: str | None = None):
    """
    Redirect user to Google OAuth consent screen
    """
    url = auth_service.get_google_login_url(state)
    return RedirectResponse(url, status_code=302)


@router.get("/google/config")
def google_config():
    """
    Endpoint to check Google OAuth configuration (DEBUG ONLY - Remove in production)
    """
    import os
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    frontend_url = os.getenv("FRONTEND_REDIRECT_URL")
    
    return {
        "status": "configured" if all([client_id, redirect_uri, frontend_url]) else "incomplete",
        "google_client_id": client_id[:30] + "..." if client_id and len(client_id) > 30 else client_id,
        "redirect_uri": redirect_uri or "NOT SET - Check .env file",
        "frontend_callback_url": frontend_url or "NOT SET - Check .env file",
        "expected_redirect_uri": "http://localhost:8000/api/auth/google/callback",
        "instructions": {
            "step_1": "Verify redirect_uri above matches exactly with Google OAuth Console",
            "step_2": "Clear browser cookies/cache before trying again",
            "step_3": "Each OAuth code can only be used ONCE and expires in 10 minutes",
            "step_4": "If still getting invalid_grant error, regenerate OAuth credentials in Google Console"
        }
    }


@router.get("/google/test-login")
def test_google_login():
    """
    Test endpoint showing the login URL (for debugging)
    Returns the exact login URL that will be used
    """
    try:
        login_url = auth_service.get_google_login_url()
        return {
            "url": login_url,
            "note": "Click this URL to start Google OAuth flow",
            "troubleshooting": "If you get invalid_grant after clicking, check /api/auth/google/config first"
        }
    except Exception as e:
        return {
            "error": str(e),
            "instructions": "Make sure GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI are set in .env"
        }


@router.get("/google/callback")
def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    frontend_url = os.getenv(
        "FRONTEND_REDIRECT_URL",
        "http://localhost:3000/oauth/callback",
    )

    # 🚨 Cancel pressed
    if error == "access_denied":
        redirect_url = f"{frontend_url}?error=access_denied"
        if state:
            redirect_url += f"&state={state}"
        return RedirectResponse(url=redirect_url, status_code=302)

    if not code:
        return RedirectResponse("http://localhost:3000/login")

    try:
        auth = auth_service.google_callback(db, code)

        params = {
            "access_token": auth["access_token"],
            "refresh_token": auth["refresh_token"],
            "token_type": "bearer",
        }

        if state:
            params["state"] = state

        redirect_url = f"{frontend_url}?{urlencode(params)}"
        return RedirectResponse(url=redirect_url, status_code=302)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
# @router.get("/google/callback")
# def google_callback(
#     code: str,
#     state: str | None = None,
#     db: Session = Depends(get_db),
# ):
#     """
#     Google redirects here after successful login.
#     We exchange `code` → tokens → redirect to frontend.
#     """
#     try:
#         # Exchange code with Google & create/login user
#         auth = auth_service.google_callback(db, code)

#         frontend_url = os.getenv(
#             "FRONTEND_REDIRECT_URL",
#             "http://localhost:3000/oauth/callback",
#         )

#         params = {
#             "access_token": auth["access_token"],
#             "refresh_token": auth["refresh_token"],
#             "token_type": "bearer",
#         }

#         if state:
#             params["state"] = state

#         redirect_url = f"{frontend_url}?{urlencode(params)}"

#         return RedirectResponse(url=redirect_url, status_code=302)

#     except HTTPException as he:
#         # Re-raise HTTPExceptions from auth_service with original detail
#         print(f"❌ GOOGLE CALLBACK HTTP ERROR: {he.detail}")
#         raise he
#     except Exception as e:
#         print("❌ GOOGLE CALLBACK ERROR")
#         print(f"Error: {str(e)}")
#         print(traceback.format_exc())
#         raise HTTPException(
#             status_code=400,
#             detail=f"Google authentication failed: {str(e)}",
#         )


# ======================================================
# TOKENS
# ======================================================

@router.post("/refresh", response_model=schemas.AuthResponse)
def refresh(data: schemas.TokenRefresh, db: Session = Depends(get_db)):
    try:
        return auth_service.refresh_access_token(db, data.refresh_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: schemas.TokenRefresh, db: Session = Depends(get_db)):
    auth_service.logout(db, data.refresh_token)
    return None


# ======================================================
# PROFILE
# ======================================================

@router.get("/me", response_model=schemas.RecruiterResponse)
def me(
    email: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = auth_service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ======================================================
# RECRUITER PROFILE (with resume count)
# ======================================================

@router.get("/profile", response_model=schemas.RecruiterProfileResponse)
def get_recruiter_profile(
    email: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recruiter profile with resume count for logged-in user"""
    from app import crud
    
    user = auth_service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get only resumes uploaded by THIS recruiter
    resume_count = crud.get_recruiter_resume_count(db, user.id)
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number if hasattr(user, 'phone_number') else None,
        "experience": user.experience if hasattr(user, 'experience') else None,
        "age": user.age if hasattr(user, 'age') else None,
        "role": user.role,
        "resume_count": resume_count,
        "created_at": user.created_at if hasattr(user, 'created_at') else None
    }


@router.put("/profile", response_model=schemas.RecruiterProfileResponse)
def update_recruiter_profile(
    profile_data: schemas.RecruiterProfileUpdate,
    email: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update recruiter profile"""
    from app import crud
    
    user = auth_service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields if provided
    if profile_data.full_name:
        user.full_name = profile_data.full_name
    if profile_data.phone_number:
        user.phone_number = profile_data.phone_number
    if profile_data.experience:
        user.experience = profile_data.experience
    if profile_data.age:
        user.age = profile_data.age
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    resume_count = crud.get_recruiter_resume_count(db, user.id)
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number if hasattr(user, 'phone_number') else None,
        "experience": user.experience if hasattr(user, 'experience') else None,
        "age": user.age if hasattr(user, 'age') else None,
        "role": user.role,
        "resume_count": resume_count,
        "created_at": user.created_at if hasattr(user, 'created_at') else None
    }