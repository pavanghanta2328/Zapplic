# Imports

from fastapi import FastAPI, File, Form, UploadFile, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
import os, shutil, hashlib, traceback, zipfile, tempfile, uuid
from datetime import datetime
from dotenv import load_dotenv
import time #
from datetime import timedelta


from app import crud, models, schemas
from app.auth_controller import router as auth_router
from app.permissions_controller import router as permissions_router
from app.profile_controller import router as profile_router
from app.team_controller import router as team_router
from app.jobs_controller import router as job_router
from app.database import get_db, engine,SessionLocal
from app.Candidate_parser_enhanced import CandidateParser
from app.debug_routes import debug_router

from app.security import get_current_user, PermissionChecker
from app.models import User
import logging
import uuid
import asyncio,io


import tika
from tika import parser as tika_parser
tika.initVM()

# 1. Global Semaphore to prevent Groq Rate Limits (429)
# Limit to 3 concurrent LLM calls across the entire app
ai_semaphore = asyncio.Semaphore(3)

load_dotenv()

# WARM-UP: This forces the Tika Server to start and wait for requests
# before the API starts accepting bulk uploads.
try:
    print("Pre-initializing Tika Server...")
    tika_parser.from_buffer("") 
    print("Tika Server is ready.")
except Exception as e:
    print(f"Tika warm-up failed: {e}")

# ======================================================
# APP
# ======================================================
app = FastAPI(
    title="Zapplic API",
    description="Recruitment platform with authentication and Candidate parsing",
    version="1.0.0",
)

# ======================================================
# DATABASE
# ======================================================
models.Base.metadata.create_all(bind=engine)

# ======================================================
# CORS (DEV MODE – SAFE)
# ======================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# ROUTERS
# ======================================================
app.include_router(job_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(permissions_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(team_router, prefix="/api")

app.include_router(debug_router, prefix="/api")

# ======================================================
# FILE CONFIG
# ======================================================
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads/Candidates")
UPLOAD_DIR = UPLOAD_DIR.replace("\\", "/") 
os.makedirs(UPLOAD_DIR, exist_ok=True)

# FIXED: Replaced duplicate extension lists
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "rtf", "zip"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_rollback(db: Session):
    try:
        db.rollback()
    except Exception:
        pass

# ======================================================
# HELPER FUNCTION: Secure Filename
# ======================================================
def secure_filename(filename: str) -> str:
    import re
    filename = os.path.basename(filename)
    filename = filename.replace(" ", "_")
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    return name + ext

def _safe_remove(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"⚠ Could not delete file: {e}")

# FIX: centralised helper — converts the string "None"/"null"/"" that FastAPI
#      passes for omitted form fields into Python None before it hits the DB.
def _clean_form_str(value) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return None if s.lower() in ("none", "null", "") else s

# ======================================================
# HEALTH
# ======================================================
@app.get("/")
def root():
    return {"status": "Zapplic API running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

def get_current_user_obj(
    db: Session = Depends(get_db),
    user_data: models.User = Depends(get_current_user)
):
    return user_data


# ======================================================
# UPLOAD Candidate (SINGLE) - WITH 2-STEP COMMIT
# ======================================================
@app.post("/api/Candidates/upload", response_model=schemas.CandidateResponse)
async def upload_Candidate(
    file: UploadFile = File(...),
    employee_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_obj),
):
    print(f"\n{'='*60}")
    print(f"🚀 SINGLE UPLOAD REQUEST RECEIVED: {file.filename}")
    print(f"{'='*60}\n")
    # FIX: sanitise "None" string from form field
    clean_employee_name = _clean_form_str(employee_name)
    user_id = current_user.id
    
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")
 
    # 1: PRE-EMPTIVE DUPLICATE CHECK
    file_content = await file.read()
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    if crud.check_duplicate_Candidate(db, file_hash=file_hash):
        raise HTTPException(status_code=409, detail="Duplicate Candidate file already exists.")
 
    await file.seek(0)
 
    # 2: SAVE FILE AND METADATA
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{safe_name}")
 
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
 
        file_size = os.path.getsize(file_path)
        file_url = f"/static/uploads/{os.path.basename(file_path)}"
 
        # 3: INITIAL DB PERSISTENCE (Skeleton Save)
        parser = CandidateParser(file_path, use_ocr_fallback=True)
        raw_text = parser._extract_text()
        
        if parser.is_job_description():
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Document appears to be a Job Description, not a Candidate")
 
        candidate_skeleton = schemas.CandidateCreate(
            original_filename=file.filename,
            file_path=file_path,
            file_type=file.filename.rsplit(".", 1)[1].lower(),
            file_hash=file_hash,
            resume_text=raw_text,
            location="Unknown",
            candidate_status="NEW",
            uploaded_by_user_id=current_user.id,
            employee_name=clean_employee_name, # Use sanitized name
            file_size_bytes=file_size, 
            resume_file_url=file_url,  
            parsed_data={},           
            search_text=raw_text   
        )
        
        db_candidate = crud.create_Candidate(db, candidate_skeleton)
        db.commit()
        db.refresh(db_candidate) 
 
        # 4: LLM PARSING & DYNAMIC QUALITY
        full_parse = await run_in_threadpool(parser.parse_full, candidate_id=db_candidate.id)
        
        db_candidate.name = full_parse["basic_fields"].get("name")
        db_candidate.email = full_parse["basic_fields"].get("email")
        db_candidate.mobile_number = full_parse["basic_fields"].get("mobile_number")
        db_candidate.parsed_data = full_parse["parsed_data"]
        db_candidate.parsing_quality = full_parse["parsing_quality"]
        db_candidate.extraction_method = full_parse.get("extraction_method")
        
        if full_parse["basic_fields"].get("location"):
            db_candidate.location = full_parse["basic_fields"].get("location")
 
        # Handle secondary duplicate check by email now that AI found it
        if db_candidate.email and crud.check_duplicate_Candidate(db, file_hash=None, email=db_candidate.email):
            if db_candidate.id != crud.check_duplicate_Candidate(db, file_hash=None, email=db_candidate.email).id:
                db.delete(db_candidate)
                db.commit()
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(status_code=409, detail="A Candidate with this email already exists.")
 
        db.commit()
        db.refresh(db_candidate)
        print(f"✅ SUCCESS: Saved Candidate ID {db_candidate.id}")
        return db_candidate
    except HTTPException:
        raise
    except Exception as e:
        _safe_remove(file_path)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))



 
# ======================================================
# BULK UPLOAD CandidateS - WITH 2-STEP COMMIT
# ======================================================


@app.post("/api/Candidates/bulk-upload", tags=["Candidates"])
async def bulk_upload_Candidates(
    files: List[UploadFile] = File(...),
    employee_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_obj),
):
    batch_start_time = time.time() # Start tracking total batch time
    clean_employee_name = _clean_form_str(employee_name)
    user_id = current_user.id

    results = {
        "total": 0, "successful": 0, "failed": 0, "skipped": 0,
        "Candidates": [], "errors": [],
        "summary": {"duplicates": 0, "parsing_errors": 0, "invalid_format": 0},
        "processing_stats": {
            "total_time_taken": 0,
            "average_time_per_file": 0
        }
    }

    async def _process_saved_file(final_path: str, original_name: str):
        file_start_time = time.time() # Start tracking individual file time
        local_db = None
        try:
            local_db = SessionLocal()
            parser = CandidateParser(final_path, use_ocr_fallback=True)
            raw_text = await run_in_threadpool(parser._extract_text)

            with open(final_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
                
            if crud.check_duplicate_Candidate(local_db, file_hash=file_hash):
                results["skipped"] += 1
                return

            full_parse = await run_in_threadpool(parser.parse_full)
            basic = full_parse.get("basic_fields", {})
            parsed_blob = full_parse.get("parsed_data", {})
            parsed_email = basic.get("email")

            if parsed_email and crud.check_duplicate_Candidate(local_db, file_hash=None, email=parsed_email):
                results["skipped"] += 1
                return

            candidate_create_data = schemas.CandidateCreate(
                original_filename=original_name,
                file_path=final_path,
                file_type=original_name.rsplit(".", 1)[1].lower() if "." in original_name else "unknown",
                file_hash=file_hash,
                name=basic.get("name"),
                email=basic.get("email"),
                mobile_number=basic.get("mobile_number"),
                location=basic.get("location") or "Unknown",
                personal_details=parsed_blob.get("personal_details", {}),
                resume_text=raw_text,
                search_text=raw_text,
                parsed_data=parsed_blob,
                candidate_status="NEW",
                uploaded_by_user_id=current_user.id,
                employee_name=clean_employee_name,
                file_size_bytes=os.path.getsize(final_path),
                resume_file_url=f"/static/uploads/{os.path.basename(final_path)}",
                parsing_quality=full_parse.get("parsing_quality", "poor"),
                extraction_method=full_parse.get("extraction_method")
            )

            db_candidate = await run_in_threadpool(crud.create_Candidate, local_db, candidate_create_data)
            
            file_end_time = time.time()
            duration = round(file_end_time - file_start_time, 2) #

            results["successful"] += 1
            results["Candidates"].append({
                "filename": original_name,
                "name": db_candidate.name or "Unknown",
                "email": db_candidate.email or "—",
                "parsing_quality": db_candidate.parsing_quality or "poor",
                "processing_time": f"{duration}s" # Return time per file
            })

        except Exception as e:
            if local_db: local_db.rollback()
            logging.error(f"Failed {original_name}: {e}")
            results["failed"] += 1
            results["errors"].append({"filename": original_name, "error": str(e)})
        finally:
            if local_db:
                local_db.close()

    # ── SAVE FILES & PROCESS SEQUENTIALLY ──
    upload_dir = os.path.join(os.getcwd(), "uploads", "resumes")
    os.makedirs(upload_dir, exist_ok=True)
    temp_dir = tempfile.mkdtemp()

    try:
        saved_files = []
        for ext_file in files:
            if not ext_file.filename or not allowed_file(ext_file.filename):
                results["failed"] += 1
                continue

            if ext_file.filename.lower().endswith(".zip"):
                zip_bytes = await ext_file.read()
                with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                    for z_name in z.namelist():
                        if z_name.endswith("/") or "__MACOSX" in z_name: continue
                        clean = os.path.basename(z_name)
                        if not clean or not allowed_file(clean): continue
                        final_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}_{secure_filename(clean)}")
                        with open(final_path, "wb") as f:
                            f.write(z.read(z_name))
                        saved_files.append((final_path, clean))
            else:
                content = await ext_file.read()
                final_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}_{secure_filename(ext_file.filename)}")
                with open(final_path, "wb") as f:
                    f.write(content)
                saved_files.append((final_path, ext_file.filename))

        results["total"] = len(saved_files)

        # Process each file and track duration
        for final_path, original_name in saved_files:
            await _process_saved_file(final_path, original_name)

        # Calculate final stats
        total_duration = time.time() - batch_start_time #
        results["processing_stats"]["total_time_taken"] = f"{round(total_duration, 2)}s"
        
        if results["total"] > 0:
            avg_time = total_duration / results["total"]
            results["processing_stats"]["average_time_per_file"] = f"{round(avg_time, 2)}s"

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return results

# ======================================================
# ✅ LIST CandidateS (DASHBOARD)
# ======================================================
@app.get("/api/Candidates", response_model=schemas.CandidateListResponse)
def get_Candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    try:
        return {
            "total": crud.get_Candidates_count(db),
            "Candidates": crud.get_Candidates(db, skip, limit),
        }
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        raise HTTPException(status_code=500, detail=str(e))
 
 
# ======================================================
# ✅ SEARCH CandidateS
# ======================================================
@app.get("/api/Candidates/search", response_model=schemas.CandidateListResponse)
def search_Candidates(
    q: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    skills: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    results = crud.comprehensive_search(
        db=db,
        role=q,
        required_skills=skills,  
        location=location
    )
    return {
        "total": len(results),
        "Candidates": results 
    }

@app.get("/Candidates/semantic-search", response_model=List[schemas.SemanticSearchResponse], tags=["Search"])
def search_Candidates_semantic(
    query: str = Query(..., description="The semantic search query"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
        results = crud.semantic_vector_search(db, search_query=query, limit=limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@app.get("/api/Candidates/search/comprehensive", tags=["Candidates"])
async def comprehensive_search(
    role: Optional[str] = Query(None),
    location: Optional[str] = Query(None),

    skills: Optional[str] = Query(None),
    required_skills: Optional[str] = Query(None),
    preferred_skills: Optional[str] = Query(None),

    min_experience: Optional[int] = Query(None),
    max_experience: Optional[int] = Query(None),
    education: Optional[str] = Query(None),

    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),

    db: Session = Depends(get_db)
):
    # ✅ ADD THIS BLOCK HERE
    designation_keywords = role.split() if role else []
    skill_recency_signal = True   # or make it dynamic later

    results = await run_in_threadpool(
        crud.comprehensive_search,
        db=db,
        role=role,
        location=location,

        skills=skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,

        min_experience=min_experience,
        max_experience=max_experience,
        education=education,

        # ✅ PASS HERE
        designation_keywords=designation_keywords,
        skill_recency_signal=skill_recency_signal,

        skip=skip,
        limit=limit,
    )

    return {
        "total": len(results),
        "Candidates": results,
    }

# def comprehensive_search(
#     role: Optional[str] = Query(None),
#     skills: Optional[str] = Query(None),
#     location: Optional[str] = Query(None),
#     min_experience: Optional[int] = Query(None),
#     max_experience: Optional[int] = Query(None),
#     education: Optional[str] = Query(None),
#     skip: int = Query(0, ge=0),
#     limit: int = Query(50, ge=1, le=200),
#     db: Session = Depends(get_db),
# ):
#     results = await run_in_threadpool( crud.comprehensive_search,
#         db=db, role=role, skills=skills, location=location,
#         min_experience=min_experience, max_experience=max_experience,
#         education=education, skip=skip, limit=limit,
#     )
    
#     return {
#         "total": len(results),
#         "active_filters": {
#             "role": role,
#             "skills": skills.split(",") if skills else [],
#             "location": location,
#             "experience_range": f"{min_experience or 0}-{max_experience or 'any'} years",
#             "education": education,
#         },
#         "results": [
#             {
#                 "id":               item["id"],
#                 "name":             item.get("name"),
#                 "email":            item.get("email"),
#                 "mobile_number":    item.get("mobile_number"),
#                 "location":         item.get("location"),
#                 "city":             item.get("city"),
#                 "state":            item.get("state"),
#                 "visa_type":        item.get("visa_type"),
#                 "years_experience": item.get("years_experience"),
#                 "version":          item.get("version"),
#                 "relevance_score":  item["score"],
#                 "match_grade":      item.get("match_grade"),
#                 "accuracy_metrics": item.get("accuracy_metrics", {}),
#             }
#             for item in results
#         ],
#     }

# ======================================================
# ✅ GET SINGLE Candidate
# ======================================================
@app.get("/api/Candidates/{Candidate_id}", response_model=schemas.CandidateResponse)
def get_Candidate_by_id(
    Candidate_id: int,
    db: Session = Depends(get_db),
):
    try:
        Candidate = crud.get_Candidate(db, Candidate_id)
        if not Candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        return Candidate
    except HTTPException:
        raise
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/Candidates/{Candidate_id}", response_model=schemas.CandidateResponse)
def update_Candidate(
    Candidate_id: int,
    Candidate_update: schemas.CandidateUpdate,
    db: Session = Depends(get_db),
):
    updated_Candidate = crud.update_Candidate(db, Candidate_id, Candidate_update)
    if not updated_Candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return updated_Candidate

@app.delete("/api/Candidates/{Candidate_id}")
def delete_Candidate(
    Candidate_id: int,
    db: Session = Depends(get_db),
):
    deleted = crud.delete_Candidate(db, Candidate_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"message": "Candidate deleted successfully"}


# ============================================================
# VERSION CHECK ENDPOINT (Call BEFORE upload)
# ============================================================
@app.post("/api/Candidates/check-version")
async def check_Candidate_version(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    temp_path = None
    try:
        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Invalid file type.")

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        safe_name = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_DIR, f"temp_{timestamp}_{safe_name}")

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with open(temp_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        email, phone, name = None, None, None

        try:
            from app.Candidate_parser_enhanced import HybridCandidateParser
            parser = HybridCandidateParser(temp_path, use_ocr_fallback=False)
            # Lightweight parse, no DB semantic check needed for version check
            full = parser.parse_full() 
            basic = full.get("basic_fields", {})
            email = basic.get("email")
            phone = basic.get("mobile_number")
            name  = basic.get("name")
        except Exception as parse_err:
            print(f"⚠ Parse error during version check: {parse_err}")

        existing_hash = db.query(models.Candidate).filter(models.Candidate.file_hash == file_hash).first()
        if existing_hash:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            uploaded_at = getattr(existing_hash, 'upload_timestamp', None) or getattr(existing_hash, 'created_at', None)
            return {
                "status": "exact_duplicate",
                "message": f"This exact file was already uploaded.",
                "existing_Candidate": {
                    "id": existing_hash.id,
                    "name": existing_hash.name,
                    "email": existing_hash.email,
                    "filename": existing_hash.original_filename,
                    "uploaded_at": uploaded_at.strftime("%b %d, %Y") if uploaded_at else None,
                    "version": getattr(existing_hash, 'version', 1),
                }
            }

        existing_person = None
        if email:
            existing_person = db.query(models.Candidate).filter(
                or_(models.Candidate.email == email, models.Candidate.employee_name == name)
            ).order_by(models.Candidate.id.desc()).first()

        if not existing_person and phone:
            existing_person = db.query(models.Candidate).filter(
                models.Candidate.mobile_number == phone
            ).order_by(models.Candidate.id.desc()).first()

        if existing_person:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            uploaded_at = getattr(existing_person, 'upload_timestamp', None) or getattr(existing_person, 'created_at', None)
            return {
                "status": "new_version",
                "message": f"A Candidate for {existing_person.name} already exists.",
                "existing_Candidate": {
                    "id": existing_person.id,
                    "name": existing_person.name,
                    "email": existing_person.email,
                    "filename": existing_person.original_filename,
                    "uploaded_at": uploaded_at.strftime("%b %d, %Y") if uploaded_at else None,
                    "version": getattr(existing_person, 'version', 1),
                },
                "temp_path": temp_path,
                "file_hash": file_hash,
                "parsed_name": name,
                "parsed_email": email,
            }

        return {
            "status": "new",
            "message": "New candidate. Safe to upload.",
            "temp_path": temp_path,
            "file_hash": file_hash,
            "parsed_name": name,
            "parsed_email": email,
        }
    except HTTPException:
        raise
    except Exception as e:
        _safe_remove(temp_path)
        print(traceback.format_exc())
        print(f"✗ check-version error: {traceback.format_exc()}")
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Version check failed: {e}")


# ============================================================
# UPLOAD WITH VERSION ACTION - WITH 2-STEP COMMIT
# ============================================================
@app.post("/api/Candidates/upload-with-action")
async def upload_with_version_action(
    file: UploadFile = File(...),
    action: str = Query(..., description="'new', 'replace', 'keep_both', 'skip'"),
    existing_Candidate_id: Optional[int] = Query(None),
    employee_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # FIX: sanitise form field
    clean_employee_name = _clean_form_str(employee_name)
    user_id = current_user.id
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    if action == "skip":
        return {"success": True, "action_taken": "skip", "message": "Kept existing Candidate"}
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{safe_name}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        file_url = f"/static/uploads/{os.path.basename(file_path)}"

        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        from app.Candidate_parser_enhanced import HybridCandidateParser
        parser = HybridCandidateParser(file_path, use_ocr_fallback=True)
        raw_text = parser._extract_text()

        # 1. SKELETON SAVE
        candidate_skeleton = schemas.CandidateCreate(
            original_filename=file.filename,
            file_path=file_path,
            file_type=file.filename.rsplit(".", 1)[1].lower(),
            file_hash=file_hash,
            resume_text=raw_text,
            location="Unknown",
            candidate_status="NEW",
            uploaded_by_user_id=current_user.id,
            file_size_bytes=file_size,
            resume_file_url=file_url,
            parsed_data={},           
            search_text=raw_text   
        )

        db_candidate = await run_in_threadpool(crud.create_Candidate, db, candidate_skeleton)
        db.commit()
        db.refresh(db_candidate) 

        # 2. AI PARSE
        full = await run_in_threadpool(parser.parse_full, candidate_id=db_candidate.id)
        
        db_candidate.name = full["basic_fields"].get("name")
        db_candidate.email = full["basic_fields"].get("email")
        db_candidate.mobile_number = full["basic_fields"].get("mobile_number")
        db_candidate.parsed_data = full["parsed_data"]
        db_candidate.parsing_quality = full["parsing_quality"]
        db_candidate.extraction_method = full.get("extraction_method")
        if full["basic_fields"].get("location"):
            db_candidate.location = full["basic_fields"].get("location")
            
        db.commit()
        db.refresh(db_candidate)

        # 3. HANDLE VERSION ACTIONS
        if action == "replace" and existing_Candidate_id:
            # Assumes your crud handles swapping status/archiving
            created = crud.replace_Candidate_version(db=db, old_Candidate_id=existing_Candidate_id, new_Candidate_data=db_candidate)
            action_message = f"Replaced old Candidate with new version"
        elif action == "keep_both" and existing_Candidate_id:
            created = crud.keep_both_versions(db=db, old_Candidate_id=existing_Candidate_id, new_Candidate_data=db_candidate)
            action_message = f"Saved as new version, old version preserved"
        else:
            created = db_candidate
            action_message = "New Candidate uploaded successfully"
        
        return {
            "success": True,
            "action_taken": action,
            "message": action_message,
            "Candidate": {
                "id": created.id,
                "name": created.name,
                "email": created.email,
                "version": created.version,
                "parsing_quality": created.parsing_quality,
            }
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/Candidates/{Candidate_id}/versions")
def get_Candidate_versions(Candidate_id: int, db: Session = Depends(get_db)):
    Candidate = crud.get_Candidate(db, Candidate_id)
    if not Candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    if not Candidate.email:
        return {"versions": [Candidate], "total": 1}
    
    versions = crud.get_Candidate_versions(db, Candidate.email)
    return {
        "total": len(versions),
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "filename": v.original_filename,
                "is_latest": v.is_latest,
                "archived": v.archived,
                "uploaded_at": v.upload_timestamp.isoformat() if v.upload_timestamp else None,
                "parsing_quality": v.parsing_quality,
            }
            for v in versions
        ]
    }
    

# ============================================================
# JOB MANAGEMENT (Connects to PostJob.js and MyJobs.js)
# ============================================================

@app.post("/api/jobs", response_model=schemas.JobResponse, tags=["Jobs"])
def create_job(
    job: schemas.JobCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user_obj)
):
    """Creates a new job posting from the PostJob.js form."""
    return crud.create_job(db=db, job_data=job, created_by=current_user.id)


@app.get("/api/jobs", response_model=schemas.JobListResponse, tags=["Jobs"])
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by ACTIVE, DRAFT, CLOSED"),
    my_jobs: bool = Query(False, description="Set to true to only see current user's jobs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_obj)
):
    """Fetches jobs for the MyJobs.js dashboard."""
    created_by_filter = current_user.id if my_jobs else None
    
    total_count, jobs_list = crud.get_jobs(
        db, 
        skip=skip, 
        limit=limit, 
        status=status, 
        created_by=created_by_filter
    )
    
    return {"total": total_count, "jobs": jobs_list}


@app.get("/api/jobs/{job_id}", response_model=schemas.JobResponse, tags=["Jobs"])
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Fetches a single job for detailed view."""
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.put("/api/jobs/{job_id}", response_model=schemas.JobResponse, tags=["Jobs"])
def update_job(
    job_id: int, 
    job_update: schemas.JobUpdate, 
    db: Session = Depends(get_db)
):
    """Updates an existing job."""
    job = crud.update_job(db, job_id, job_update)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.put("/api/jobs/{job_id}/close", response_model=schemas.JobResponse, tags=["Jobs"])
def close_job(job_id: int, db: Session = Depends(get_db)):
    """Soft-closes a job (triggered by the 'Close' button in MyJobs.js)."""
    job = crud.close_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.delete("/api/jobs/{job_id}", tags=["Jobs"])
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Hard-deletes a job (triggered by the 'Delete' button in MyJobs.js)."""
    success = crud.delete_job(db, job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "message": "Job deleted"}

# ============================================================
# PARSE JOB DESCRIPTION FILE (Auto-fill PostJob.js)
# ============================================================
@app.post("/api/jobs/parse-file", tags=["Jobs"])
async def parse_job_file(file: UploadFile = File(...)):
    """Receives a JD document, parses it with Tika & Groq, and returns structured data."""
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")
        
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    safe_name = secure_filename(file.filename)
    temp_path = os.path.join(UPLOAD_DIR, f"temp_jd_{timestamp}_{safe_name}")
    
    try:
        # Save file temporarily
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Run the parser
        from app.Candidate_parser_enhanced import JobDescriptionParser
        parser = JobDescriptionParser(file_path=temp_path)
        parsed_data = await run_in_threadpool(parser.parse)
        
        return {"success": True, "parsed_data": parsed_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse JD: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
# ============================================================
# JD MATCHING (Connects to SearchByJD.js)
# ============================================================

from pydantic import BaseModel

class JDMatchRequest(BaseModel):
    jd_text: str
    limit: int = 20

@app.post("/api/candidates/match-jd", tags=["Search"])
async def match_candidates_by_jd(
    request: JDMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_obj),
):
    """
    Paste a raw JD → LLM extracts structure → pure DB-side matching.

    Pipeline:
      1. JobDescriptionParser (Groq LLM) extracts title, skills, visa, experience
      2. crud.comprehensive_search runs a single SQL query using:
           - pgvector HNSW cosine similarity  (candidates.embedding)
           - PostgreSQL ts_rank_cd            (candidates.tsv_content GIN index)
           - JSONB skill overlap              (candidates.parsed_data->skills)
           - JSONB location / experience      (candidates.parsed_data city/state/years)
    """
    from app.Candidate_parser_enhanced import JobDescriptionParser

    if not request.jd_text or len(request.jd_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Job description text is too short.")

    # Step 1: LLM-parse the raw JD text
    parser    = JobDescriptionParser(raw_text=request.jd_text)
    jd_parsed = await run_in_threadpool(parser.parse)

    required_skills  = (jd_parsed.get("required_skills") or []) + (jd_parsed.get("core_competencies") or [])
    preferred_skills = (jd_parsed.get("preferred_skills") or []) + (jd_parsed.get("soft_skills") or [])
    all_skills       = required_skills + preferred_skills

    designation_kw       = jd_parsed.get("designation_keywords") or []
    skill_recency_signal = jd_parsed.get("skill_recency_signal", False)

    # Step 2: ATS-grade matching — all JD signals now passed through
    # role gets title + designation keywords so the embedding and FTS
    # are richer than just the bare job title.
    role_context = jd_parsed.get("title") or ""
    if designation_kw:
        role_context = role_context + " " + " ".join(designation_kw[:3])
    matches = await run_in_threadpool(
        crud.comprehensive_search,
        db=db,
        role=role_context.strip(),
        required_skills      = ",".join(required_skills)  if required_skills  else None,
        preferred_skills     = ",".join(preferred_skills) if preferred_skills else None,
        location             = jd_parsed.get("city") or jd_parsed.get("state"),
        min_experience       = jd_parsed.get("experience_min_years"),
        education            = jd_parsed.get("education_requirement"),
        designation_keywords = designation_kw,
        skill_recency_signal = skill_recency_signal,
        limit=request.limit,
    )

    import logging as _log
    _log.info(f"[match-jd] JD parsed title='{jd_parsed.get('title')}' req_skills={required_skills[:3]}... "
              f"pool_returned={len(matches)} candidates")

    # NOTE: Keys MUST match what SearchByJD.js reads:
    #   data.candidates  (was "matches" — caused 0 results displayed)
    #   data.parsed_jd   (was "jd_parsed_criteria" — caused AI criteria panel to be blank)
    return {
        "parsed_jd": {
            "title":                jd_parsed.get("title"),
            "skills":               all_skills,
            "required_skills":      required_skills,
            "preferred_skills":     preferred_skills,
            "designation_keywords": designation_kw,
            "visa_requirement":     jd_parsed.get("visa_requirement"),
            "experience_min":       jd_parsed.get("experience_min_years"),
            "location":             jd_parsed.get("city") or jd_parsed.get("state"),
            "is_remote":            jd_parsed.get("is_remote", False),
            "skill_recency_signal": skill_recency_signal,
            "education_requirement":jd_parsed.get("education_requirement"),
        },
        "total_found": len(matches),
        "candidates": matches,   # renamed from "matches" to match SearchByJD.js
    }

# ======================================================
# JOB-BASED CANDIDATE MATCHING
# ======================================================

# @app.get("/api/jobs/{job_id}/match", response_model=schemas.JobMatchResponse, tags=["Jobs"])
@app.post("/api/jobs/match_candidates_for_job", tags=["Matching"])
async def match_candidates_for_job(
    job_id:          int,
    limit:           int  = Query(20, ge=1, le=100),
    visa_filter:     bool = Query(True,  description="Hard-filter by visa_requirement"),
    location_filter: bool = Query(False, description="Narrow pool to job.state"),
    db:              Session = Depends(get_db),
    current_user:    User    = Depends(get_current_user_obj),
):
    """

    Everything runs inside PostgreSQL in a single query:
      Leg 1 — Hard SQL filters (visa, experience)         → narrows pool
      Leg 2 — pgvector HNSW  (candidates.embedding <=> job.embedding)  → semantic rank
      Leg 3 — ts_rank_cd     (candidates.tsv_content GIN)               → keyword rank
      Leg 4 — JSONB overlap  (parsed_data skills / city / years_exp)    → structured boost

    Weights: 55% vector + 30% FTS + 10% skills + 3% location + 2% experience
    Grades:  A ≥80  B ≥60  C ≥40  D <40
    """
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    matches = await run_in_threadpool(
        crud.match_candidates_for_job,
        db=db,
        job_id=job_id,
        limit=limit,
        visa_filter=visa_filter,
        location_filter=location_filter,
    )

    # Track recruiter engagement
    try:
        job.submission_count = (job.submission_count or 0) + 1
        db.commit()
    except Exception:
        db.rollback()

    return schemas.JobMatchResponse(
        job_id      = job.id,
        job_uid     = job.job_uid,
        job_title   = job.title,
        total_found = len(matches),
        candidates  = [schemas.CandidateMatchResult(**m) for m in matches],
    )


@app.post("/api/jobs/{job_id}/match", tags=["Jobs"])
async def rematch_job(
    job_id:          int,
    limit:           int  = Query(20, ge=1, le=100),
    visa_filter:     bool = Query(True),
    location_filter: bool = Query(False),
    db:              Session = Depends(get_db),
    current_user:    User    = Depends(get_current_user_obj),
):
    """POST alias for GET /api/jobs/{job_id}/match — same result."""
    return await match_candidates_for_job(
        job_id=job_id, limit=limit,
        visa_filter=visa_filter, location_filter=location_filter,
        db=db, current_user=current_user,
    )

# A: If you have a Job saved in the DB
@app.get("/api/jobs/{job_id}/match", tags=["Jobs"])
async def match_job_id(
    job_id: int, 
    limit: int = 20, 
    db: Session = Depends(get_db)
):
    # This calls your advanced crud.py function exactly
    return await run_in_threadpool(crud.match_candidates_for_job, db, job_id, limit)

# B: If you are pasting text into the UI (JD Search)
@app.post("/api/jobs/match-from-text", tags=["Matching"])
async def match_from_text(
    jd_text: str = Form(...), 
    db: Session = Depends(get_db)
):
    # We use a modified version of your logic that handles raw text
    results = await run_in_threadpool(crud.match_candidates_from_jd_text, db, jd_text)
    return results