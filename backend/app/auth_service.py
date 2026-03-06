import os
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from jose import jwt, JWTError

from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests

from app import models, schemas
import secrets


from app.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    SECRET_KEY,
    ALGORITHM,
)

state = secrets.token_urlsafe(32)

# ---------- DB ----------

def get_user_by_email(db: Session, email: str):
    return db.query(models.Recruiter).filter(models.Recruiter.email == email).first()


# ---------- SIGNUP ----------

def create_email_user(db: Session, recruiter: schemas.RecruiterCreate):
    if get_user_by_email(db, recruiter.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = models.Recruiter(
        email=recruiter.email,
        hashed_password=get_password_hash(recruiter.password),
        full_name=recruiter.full_name,
        auth_provider="email",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ---------- LOGIN ----------

def login_email_user(db: Session, login_data: schemas.RecruiterLogin):
    user = get_user_by_email(db, login_data.email)

    if not user or not user.hashed_password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")

    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    return generate_auth_response(db, user)


# ================= GOOGLE AUTH =================

def get_google_flow():
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    if not redirect_uri:
        raise RuntimeError("GOOGLE_REDIRECT_URI not set")

    return Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        redirect_uri=redirect_uri,
    )


def get_google_login_url(state=None):
    flow = get_google_flow()
    url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return url


def google_callback(db: Session, code: str):
    try:
        # Check if required env vars exist
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        
        if not all([client_id, client_secret, redirect_uri]):
            missing = []
            if not client_id: missing.append("GOOGLE_CLIENT_ID")
            if not client_secret: missing.append("GOOGLE_CLIENT_SECRET")
            if not redirect_uri: missing.append("GOOGLE_REDIRECT_URI")
            raise Exception(f"Missing environment variables: {', '.join(missing)}")
        
        print(f"📝 Starting Google OAuth callback")
        print(f"   Redirect URI: {redirect_uri}")
        print(f"   Code length: {len(code)} chars")
        
        flow = get_google_flow()
        
        try:
            print("🔄 Exchanging auth code for tokens...")
            flow.fetch_token(code=code)
            print("✓ Token fetched successfully")
        except Exception as token_error:
            error_str = str(token_error)
            if "invalid_grant" in error_str:
                raise Exception(
                    "Authorization code is invalid or expired. "
                    "This usually means: "
                    "(1) Code was already used, "
                    "(2) Code expired (codes valid for 10 minutes), or "
                    "(3) Redirect URI in credentials doesn't match.\n"
                    f"Full error: {error_str}"
                )
            raise Exception(f"Failed to fetch token: {error_str}")

        try:
            print("🔐 Verifying ID token...")
            # Use the correct token endpoint and client
            idinfo = id_token.verify_oauth2_token(
                flow.credentials.id_token,
                requests.Request(),
                client_id,
            )
            print("✓ ID token verified successfully")
        except Exception as verify_error:
            raise Exception(f"Failed to verify token: {str(verify_error)}")
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Google Auth Error: {error_msg}")
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {error_msg}")

    email = idinfo.get("email")
    name = idinfo.get("name")

    if not email:
        raise HTTPException(400, "Google authentication failed: No email in response")

    print(f"👤 Authenticating user: {email}")
    user = get_user_by_email(db, email)

    if not user:
        print(f"✨ Creating new user: {email}")
        user = models.Recruiter(
            email=email,
            full_name=name,
            auth_provider="google",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✓ New user created: {email}")
    else:
        print(f"✓ Existing user found: {email}")

    return generate_auth_response(db, user)


# ---------- REFRESH ----------

def refresh_access_token(db: Session, refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "refresh":
            raise HTTPException(401, "Invalid refresh token")

        db_token = db.query(models.RefreshToken).filter(
            models.RefreshToken.token == refresh_token,
            models.RefreshToken.is_revoked == False,
        ).first()

        if not db_token:
            raise HTTPException(401, "Refresh token revoked")

        db_token.is_revoked = True
        db.commit()

        return generate_auth_response(db, db_token.user)

    except JWTError:
        raise HTTPException(401, "Invalid refresh token")


# ---------- LOGOUT ----------

def logout(db: Session, refresh_token: str):
    token = db.query(models.RefreshToken).filter(models.RefreshToken.token == refresh_token).first()
    if token:
        token.is_revoked = True
        db.commit()


# ---------- TOKEN RESPONSE ----------

def generate_auth_response(db: Session, user):
    access_token = create_access_token({"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.email})

    db.add(models.RefreshToken(token=refresh_token, user_id=user.id))
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }
