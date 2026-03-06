from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any,Dict
from datetime import datetime

# --- AUTH SCHEMAS (Recruiter, Token, etc. remain unchanged) ---

# ======================================================
# AUTH / RECRUITER SCHEMAS
# ======================================================

class RecruiterCreate(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) > 72:
            raise ValueError("Password must be at most 72 characters")
        return v

    @field_validator("confirm_password")
    @classmethod
    def match(cls, v, info):
        if v != info.data.get("password"):
            raise ValueError("Passwords do not match")
        return v

class RecruiterLogin(BaseModel):
    email: EmailStr
    password: str
    
class TokenRefresh(BaseModel):
    refresh_token: str
    

class RecruiterResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    role: str
    class Config: from_attributes = True
    
class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: RecruiterResponse
    
class RecruiterProfileResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    phone_number: Optional[str] = None
    experience: Optional[str] = None
    age: Optional[int] = None
    role: str
    resume_count: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecruiterProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    experience: Optional[str] = None
    age: Optional[int] = None

    class Config:
        from_attributes = True



# --- RESUME SCHEMAS ---
class ResumeBase(BaseModel):
    original_filename: str
    file_path: str
    file_type: str
    file_hash: str
    name: Optional[str] = None
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    location: Optional[str]=None
    employee_name: Optional[str] = None
    parsing_quality: Optional[str] = "unknown"
    extraction_method: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    personal_details: Optional[Dict[str, Any]] = None

class ResumeCreate(ResumeBase):
    parsed_data: Any
    search_text: str

# ---------- UPDATE ----------
class ResumeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    location: Optional[str] = None
    employee_name: Optional[str] = None
    parsing_quality: Optional[str] = None
    extraction_method: Optional[str] = None  # After parsing_quality

class ResumeResponse(BaseModel):
    id: int

    original_filename: str
    file_path: str
    file_type: str
    file_hash: Optional[str] = None

    name: Optional[str]
    email: Optional[str]
    mobile_number: Optional[str]
    location: Optional[str]
    employee_name: Optional[str]=None

    parsed_data: Optional[Any]
    search_text: Optional[str]
    parsing_quality: Optional[str]
    extraction_method: Optional[str] = None  # After parsing_quality
    created_at: Optional[datetime]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    personal_details: Optional[str]

    class Config:
        from_attributes = True  # ✅ REQUIRED FOR SQLALCHEMY
    
# ---------- LIST RESPONSE ----------
class ResumeListResponse(BaseModel):
    total: int
    resumes: List[ResumeResponse]

    class Config:
        from_attributes = True

class SemanticSearchResponse(BaseModel):
    resume_id: int
    candidate_name: Optional[str]
    location: Optional[str]
    ai_accuracy_score: float

class RecallBenchmarkResponse(BaseModel):
    search_query: str
    k_requested: int
    exact_ids: List[int]
    ivfflat_ann_ids: List[int]
    true_recall_percentage: float
    developer_note: str