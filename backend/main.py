# import email
from fastapi import FastAPI, File, Form, UploadFile, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os,shutil,hashlib,traceback,zipfile,tempfile
from datetime import datetime
from dotenv import load_dotenv

from app import crud, models, schemas
from app.auth_controller import router as auth_router
from app.database import get_db, engine
from app.resume_parser_enhanced import ResumeParser
from app.debug_routes import debug_router

load_dotenv()

# ======================================================
# APP
# ======================================================
app = FastAPI(
    title="Zapplic API",
    description="Recruitment platform with authentication and resume parsing",
    version="1.0.0",
)

# ======================================================
# DATABASE
# ======================================================
models.Base.metadata.create_all(bind=engine)

# ======================================================
# ✅ CORS (DEV MODE – SAFE)
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
app.include_router(auth_router, prefix="/api")
app.include_router(debug_router, prefix="/api")

# ======================================================
# FILE CONFIG
# ======================================================
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads/resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# HEAD
ALLOWED_EXTENSIONS = {"pdf", "docx", "zip"}

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "zip"}
# pavan_rewardsystem


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_rollback(db: Session):
    try:
        db.rollback()
    except Exception:
        pass

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ======================================================
# HELPER FUNCTION: Secure Filename
# ======================================================
def secure_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks.
    Removes special characters and keeps only alphanumeric, dots, underscores, and hyphens.
    """
    import re
    
    # Remove any directory paths
    filename = os.path.basename(filename)
    
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    
    # Remove any characters that aren't alphanumeric, dots, underscores, or hyphens
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    
    # Limit filename length (keep extension)
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext


# ======================================================
# HEALTH
# ======================================================
@app.get("/")
def root():
    return {"status": "Zapplic API running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# ======================================================
# UPLOAD RESUME (SINGLE)
# ======================================================
@app.post("/api/resumes/upload", response_model=schemas.ResumeResponse)
# async def upload_resume(
#     file: UploadFile = File(...),
#     employee_name: Optional[str] = Form(None),
#     db: Session = Depends(get_db),
# ):
#     print(f"\n{'='*60}")
#     print(f"🚀 UPLOAD REQUEST RECEIVED")
#     print(f"  File: {file.filename}")
#     print(f"  employee_name (form): '{employee_name}' (type: {type(employee_name).__name__})")
#     print(f"{'='*60}\n")
    
#     if not allowed_file(file.filename):
#         raise HTTPException(status_code=400, detail="Invalid file type")

#     timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
#     file_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{file.filename}")

#     try:
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         with open(file_path, "rb") as f:
#             file_hash = hashlib.sha256(f.read()).hexdigest()

#         parser = ResumeParser(file_path, use_ocr_fallback=True)

#         # full = parser.parse_full()
#         full=await run_in_threadpool(parser.parse_full)
#         basic = full["basic_fields"]
#         quality = full["parsing_quality"]
#         # ✅ Fix email variable
#         candidate_email = basic.get("email")

#         if not isinstance(candidate_email, str):
#             candidate_email = None


#         print(f"🔍 DEBUG: Extraction method = {full.get('extraction_method')}")
#         print(f"🔍 DEBUG: Name = {basic.get('name')}")

#         if crud.check_duplicate_resume(db, file_hash, basic.get("email")):
#             os.remove(file_path)
#             raise HTTPException(status_code=409, detail="Duplicate resume")

#         resume_data = schemas.ResumeCreate(
#             original_filename=file.filename,
#             file_path=file_path,
#             file_type=file.filename.rsplit(".", 1)[1].lower(),
#             file_hash=file_hash,
#             name=basic.get("name"),
#             email=candidate_email,
#             mobile_number=basic.get("mobile_number"),
#             location=basic.get("location"),
#             employee_name=employee_name,
#             parsed_data=full["parsed_data"],
#             search_text=full["search_text"],
#             parsing_quality=quality,
#             extraction_method=full.get("extraction_method"),
#         )

#         print(f"\n{'='*60}")
#         print(f"📋 RESUME DATA CONSTRUCTED")
#         print(f"  resume_data.employee_name: '{resume_data.employee_name}'")
#         print(f"  resume_data.name: '{resume_data.name}'")
#         print(f"{'='*60}\n")

#         # --- NEW DEBUG STEPS ---
#         print("🛠️ DEBUG: Calling crud.create_resume...")
        
#         # We wrap this in run_in_threadpool because database and 
#         # embedding generation are "blocking" sync tasks.
#         created_resume = await run_in_threadpool(crud.create_resume, db, resume_data)
        
#         print(f"✅ DEBUG: Success! Resume ID: {created_resume.id}")
#         return created_resume

#     except HTTPException:
#         raise
#     except Exception as e:
#         if os.path.exists(file_path):
#             try:
#                 os.remove(file_path)
#             except Exception:
#                 pass
#         tb = traceback.format_exc()
#         print(tb)
#         # Return the actual error message in dev to help debugging
#         raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/resumes/upload", response_model=schemas.ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    employee_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    print(f"\n{'='*60}")
    print(f"🚀 UPLOAD REQUEST RECEIVED: {file.filename}")
    print(f"{'='*60}\n")
    
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    # ============================================================
    # STEP 1: PRE-EMPTIVE DUPLICATE CHECK (FAST)
    # ============================================================
    # Read bytes in memory to hash BEFORE saving or parsing
    file_content = await file.read()
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Check if hash already exists in DB
    existing_by_hash = crud.check_duplicate_resume(db, file_hash=file_hash)
    if existing_by_hash:
        print(f"⚠️ SKIPPED: Duplicate file detected by hash: {file.filename}")
        raise HTTPException(status_code=409, detail="Duplicate resume file already exists.")

    # Reset file pointer so we can save it to disk
    await file.seek(0)

    # ============================================================
    # STEP 2: PROCEED ONLY IF NEW
    # ============================================================
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{file.filename}")

    try:
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse the resume
        parser = ResumeParser(file_path, use_ocr_fallback=True)
        full = await run_in_threadpool(parser.parse_full)
        basic = full["basic_fields"]
        candidate_email = basic.get("email")
        
        if not isinstance(candidate_email, str):
            candidate_email = None


        print(f"🔍 DEBUG: Extraction method = {full.get('extraction_method')}")
        print(f"🔍 DEBUG: Name = {basic.get('name')}")

        # ============================================================
        # STEP 3: SECONDARY DUPLICATE CHECK (BY EMAIL)
        # ============================================================
        if candidate_email and crud.check_duplicate_resume(db, file_hash=None, email=candidate_email):
            if os.path.exists(file_path):
                os.remove(file_path)
            print(f"⚠️ SKIPPED: Candidate email {candidate_email} already exists.")
            raise HTTPException(status_code=409, detail="A resume with this email already exists.")

        # Construct data for DB
        resume_data = schemas.ResumeCreate(
            original_filename=file.filename,
            file_path=file_path,
            file_type=file.filename.rsplit(".", 1)[1].lower(),
            file_hash=file_hash,
            name=basic.get("name"),
            email=candidate_email if isinstance(candidate_email, str) else None,
            mobile_number=basic.get("mobile_number"),
            location=basic.get("location"),
            employee_name=employee_name,
            linkedin_url=basic.get("linkedin_url"),
            github_url=basic.get("github_url"),
            personal_details=basic.get("personal_details", {}),
            parsed_data=full["parsed_data"],
            search_text=full["search_text"],
            parsing_quality=full["parsing_quality"],
            extraction_method=full.get("extraction_method"),
        )
        print(f"\n{'='*60}")
        print(f"📋 RESUME DATA CONSTRUCTED")
        print(f"  resume_data.employee_name: '{resume_data.employee_name}'")
        print(f"  resume_data.name: '{resume_data.name}'")
        print(f"{'='*60}\n")

        # --- NEW DEBUG STEPS ---
        print("🛠️ DEBUG: Calling crud.create_resume...")

        # Create record
        created_resume = await run_in_threadpool(crud.create_resume, db, resume_data)
        print(f"✅ SUCCESS: Saved Resume ID {created_resume.id}")
        
        return created_resume

    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# ✅ LIST RESUMES (DASHBOARD)
# ======================================================
@app.get("/api/resumes", response_model=schemas.ResumeListResponse)
def get_resumes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    try:
        return {
            "total": crud.get_resumes_count(db),
            "resumes": crud.get_resumes(db, skip, limit),
        }
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# ✅ SEARCH RESUMES
# ======================================================
@app.get("/api/resumes/search", response_model=schemas.ResumeListResponse)
def search_resumes(
    q: Optional[str] = Query(None, description="Keyword / role / tech"),
    location: Optional[str] = Query(None, description="Location"),
    skills: Optional[str] = Query(None, description="Skills"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    resumes = crud.search_resumes_with_filters(
        db=db,
        query=q,
        location=location,
        skills=skills,
        skip=skip,
        limit=limit
    )

    return {
        "total": len(resumes),
        "resumes": resumes
    }

@app.get("/resumes/semantic-search", response_model=List[schemas.SemanticSearchResponse], tags=["Search"])
def search_resumes_semantic(
    query: str = Query(..., description="The semantic search query (e.g., 'Data Scientist with Python')"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Perform a purely semantic vector search using pgvector.
    Returns the top candidates along with an AI mathematical accuracy score (Cosine Similarity).
    """
    try:
        results = crud.semantic_vector_search(db, search_query=query, limit=limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")

# ======================================================
# ✅ GET SINGLE RESUME (DETAIL PAGE FIX)
# ======================================================
@app.get("/api/resumes/{resume_id}", response_model=schemas.ResumeResponse)
def get_resume_by_id(
    resume_id: int,
    db: Session = Depends(get_db),
):
    try:
        resume = crud.get_resume(db, resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        return resume
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# ✅ UPDATE RESUME
# ======================================================
@app.put("/api/resumes/{resume_id}", response_model=schemas.ResumeResponse)
def update_resume(
    resume_id: int,
    resume_update: schemas.ResumeUpdate,
    db: Session = Depends(get_db),
):
    updated_resume = crud.update_resume(db, resume_id, resume_update)

    if not updated_resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return updated_resume


# ======================================================
# ✅ DELETE RESUME
# ======================================================
@app.delete("/api/resumes/{resume_id}")
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
):
    deleted = crud.delete_resume(db, resume_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {"message": "Resume deleted successfully"}


# ======================================================
# BULK UPLOAD RESUMES - FIXED VERSION
# ======================================================
# @app.post("/api/resumes/bulk-upload")
# async def bulk_upload_resumes(
#     files: List[UploadFile] = File(...),
#     employee_name: Optional[str] = Form(None),
#     db: Session = Depends(get_db),
# ):
#     """
#     Bulk upload multiple resume files.
#     Supports: PDF, DOCX (DOC not recommended)
#     Features: Duplicate detection, JD filtering, comprehensive error reporting
#     """
#     results = {
#         "total": len(files),
#         "successful": 0,
#         "failed": 0,
#         "resumes": [],
#         "errors": [],
#         "summary": {
#             "duplicates": 0,
#             "job_descriptions": 0,
#             "parsing_errors": 0,
#             "invalid_format": 0,
#             "poor_quality": 0
#         }
#     }

#     for idx, file in enumerate(files):
#         file_path = None
#         parser = None

#         # map provided employee_names (if any) to each file by index
#         current_employee_name = employee_name

#         try:
#             # ============================================================
#             # STEP 1: FILE VALIDATION
#             # ============================================================
#             if not allowed_file(file.filename):
#                 results["failed"] += 1
#                 results["summary"]["invalid_format"] += 1
#                 results["errors"].append({
#                     "filename": file.filename,
#                     "error": "Invalid file type. Supported: PDF, DOCX",
#                     "error_type": "invalid_format"
#                 })
#                 continue

#             # ============================================================
#             # STEP 2: SAVE FILE
#             # ============================================================
#             timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
#             safe_filename_str = secure_filename(file.filename)
#             file_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{safe_filename_str}")

#             try:
#                 with open(file_path, "wb") as buffer:
#                     shutil.copyfileobj(file.file, buffer)
#             except Exception as save_error:
#                 results["failed"] += 1
#                 results["errors"].append({
#                     "filename": file.filename,
#                     "error": f"Failed to save file: {str(save_error)}",
#                     "error_type": "file_save_error"
#                 })
#                 continue

#             if file.filename.lower().endswith('.zip'):
#                 # ZIP handling
#                 with tempfile.TemporaryDirectory() as temp_dir:
#                     try:
#                         with zipfile.ZipFile(file_path, 'r') as zip_ref:
#                             zip_ref.extractall(temp_dir)
#                             extracted_files = zip_ref.namelist()
#                     except Exception as e:
#                         os.remove(file_path)
#                         results["failed"] += 1
#                         results["errors"].append({
#                             "filename": file.filename,
#                             "error": f"Failed to extract ZIP: {str(e)}",
#                             "error_type": "zip_extraction_error"
#                         })
#                         continue
#                     invalid_files = [ef for ef in extracted_files if not allowed_file(ef)]
#                     if invalid_files:
#                         os.remove(file_path)
#                         results["failed"] += 1
#                         results["errors"].append({
#                             "filename": file.filename,
#                             "error": f"ZIP contains invalid files: {invalid_files}",
#                             "error_type": "invalid_zip_contents"
#                         })
#                         continue
#                     # Process each extracted file
#                     for ef in extracted_files:
#                         ef_path = os.path.join(temp_dir, ef)
#                         # File size check
#                         file_size = os.path.getsize(ef_path)
#                         MAX_FILE_SIZE = 10 * 1024 * 1024
#                         if file_size > MAX_FILE_SIZE:
#                             results["failed"] += 1
#                             results["errors"].append({
#                                 "filename": ef,
#                                 "error": f"File too large ({file_size / 1024 / 1024:.2f}MB). Max: 10MB",
#                                 "error_type": "file_too_large"
#                             })
#                             continue
#                         if file_size == 0:
#                             results["failed"] += 1
#                             results["errors"].append({
#                                 "filename": ef,
#                                 "error": "File is empty",
#                                 "error_type": "empty_file"
#                             })
#                             continue
#                         # Compute hash
#                         with open(ef_path, "rb") as f:
#                             file_hash = hashlib.sha256(f.read()).hexdigest()
#                         # Duplicate check by hash
#                         existing_hash = db.query(models.Resume).filter(
#                             models.Resume.file_hash == file_hash
#                         ).first()
#                         if existing_hash:
#                             results["failed"] += 1
#                             results["summary"]["duplicates"] += 1
#                             results["errors"].append({
#                                 "filename": ef,
#                                 "error": f"Duplicate file (already uploaded as: {existing_hash.original_filename})",
#                                 "error_type": "duplicate_hash",
#                                 "existing_resume_id": existing_hash.id,
#                                 "existing_filename": existing_hash.original_filename
#                             })
#                             continue
#                         # Create parser & extract text
#                         try:
#                             parser = ResumeParser(ef_path, use_ocr_fallback=True)
#                             parser.extract_text()
#                             # Special handling for .doc
#                             if ef.endswith('.doc') and (not parser.text or len(parser.text.strip()) < 10):
#                                 results["failed"] += 1
#                                 results["summary"]["parsing_errors"] += 1
#                                 results["errors"].append({
#                                     "filename": ef,
#                                     "error": "Legacy .doc format not supported. Please convert to .docx or PDF format.",
#                                     "error_type": "legacy_doc_format",
#                                     "solution": "Convert to DOCX or PDF"
#                                 })
#                                 continue
#                         except ValueError as ve:
#                             results["failed"] += 1
#                             results["summary"]["parsing_errors"] += 1
#                             if ef.endswith('.doc'):
#                                 results["errors"].append({
#                                     "filename": ef,
#                                     "error": str(ve),
#                                     "error_type": "legacy_doc_unsupported",
#                                     "solution": "Convert to DOCX or PDF format"
#                                 })
#                             else:
#                                 results["errors"].append({
#                                     "filename": ef,
#                                     "error": f"Failed to extract text: {str(ve)}",
#                                     "error_type": "extraction_error"
#                                 })
#                             continue
#                         except Exception as parse_error:
#                             results["failed"] += 1
#                             results["summary"]["parsing_errors"] += 1
#                             results["errors"].append({
#                                 "filename": ef,
#                                 "error": f"Failed to extract text: {str(parse_error)}",
#                                 "error_type": "extraction_error"
#                             })
#                             continue
#                         # Job description detection
#                         if parser.is_job_description():
#                             results["failed"] += 1
#                             results["summary"]["job_descriptions"] += 1
#                             results["errors"].append({
#                                 "filename": ef,
#                                 "error": "Document appears to be a Job Description, not a resume",
#                                 "error_type": "job_description"
#                             })
#                             continue
#                         # Full parsing
#                         try:
#                             full = parser.parse_full()
#                             basic = full["basic_fields"]
#                             quality = full["parsing_quality"]
#                             candidate_email = basic.get("email")
#                         except Exception as full_parse_error:
#                             results["failed"] += 1
#                             results["summary"]["parsing_errors"] += 1
#                             results["errors"].append({
#                                 "filename": ef,
#                                 "error": f"Failed to parse resume: {str(full_parse_error)}",
#                                 "error_type": "parsing_error"
#                             })
#                             continue
#                         # Duplicate check by email
#                         email = basic.get("email")
#                         if email:
#                             existing_email = db.query(models.Resume).filter(
#                                 models.Resume.email == email,
#                                 models.Resume.file_hash != file_hash
#                             ).first()
#                             if existing_email:
#                                 pass
#                         # Move to UPLOAD_DIR
#                         timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
#                         safe_filename = secure_filename(ef)
#                         final_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{safe_filename}")
#                         shutil.move(ef_path, final_path)
#                         # Save to database
#                         resume_data = schemas.ResumeCreate(
#                             original_filename=ef,
#                             file_path=final_path,
#                             file_type=ef.rsplit(".", 1)[1].lower(),
#                             file_hash=file_hash,
#                             name=basic.get("name"),
#                             email=candidate_email if isinstance(candidate_email, str) else None,
#                             mobile_number=basic.get("mobile_number"),
#                             location=basic.get("location"),
#                             employee_name=current_employee_name,
#                             parsed_data=full["parsed_data"],
#                             search_text=full["search_text"],
#                             parsing_quality=quality,
#                         )
#                         try:
#                             created = crud.create_resume(db, resume_data)
#                             results["successful"] += 1
#                             uploaded_timestamp = created.created_at.isoformat() if created.created_at else None
#                             results["resumes"].append({
#                                 "id": created.id,
#                                 "filename": ef,
#                                 "name": created.name,
#                                 "email": created.email,
#                                 "mobile_number": created.mobile_number,
#                                 "location": created.location,
#                                 "employee_name": created.employee_name,
#                                 "parsing_quality": created.parsing_quality,
#                                 "uploaded_at": uploaded_timestamp
#                             })
#                         except Exception as db_error:
#                             os.remove(final_path)
#                             results["failed"] += 1
#                             results["errors"].append({
#                                 "filename": ef,
#                                 "error": f"Database error: {str(db_error)}",
#                                 "error_type": "database_error"
#                             })
#                             continue
#                 # After processing all extracted, remove the ZIP
#                 os.remove(file_path)
#                 continue

#             # ============================================================
#             # STEP 3: FILE SIZE CHECK
#             # ============================================================
#             file_size = os.path.getsize(file_path)
#             MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
            
#             if file_size > MAX_FILE_SIZE:
#                 os.remove(file_path)
#                 results["failed"] += 1
#                 results["errors"].append({
#                     "filename": file.filename,
#                     "error": f"File too large ({file_size / 1024 / 1024:.2f}MB). Max: 10MB",
#                     "error_type": "file_too_large"
#                 })
#                 continue
            
#             if file_size == 0:
#                 os.remove(file_path)
#                 results["failed"] += 1
#                 results["errors"].append({
#                     "filename": file.filename,
#                     "error": "File is empty",
#                     "error_type": "empty_file"
#                 })
#                 continue

#             # ============================================================
#             # STEP 4: COMPUTE FILE HASH
#             # ============================================================
#             with open(file_path, "rb") as f:
#                 file_hash = hashlib.sha256(f.read()).hexdigest()

#             # Early duplicate check by hash
#             existing_hash = db.query(models.Resume).filter(
#                 models.Resume.file_hash == file_hash
#             ).first()
            
#             if existing_hash:
#                 os.remove(file_path)
#                 results["failed"] += 1
#                 results["summary"]["duplicates"] += 1
#                 results["errors"].append({
#                     "filename": file.filename,
#                     "error": f"Duplicate file (already uploaded as: {existing_hash.original_filename})",
#                     "error_type": "duplicate_hash",
#                     "existing_resume_id": existing_hash.id,
#                     "existing_filename": existing_hash.original_filename
#                 })
#                 continue

#             # ============================================================
#             # STEP 5: CREATE PARSER & EXTRACT TEXT
#             # ============================================================
#             try:
#                 parser = ResumeParser(file_path, use_ocr_fallback=True)
#                 parser.extract_text()
                
#                 # Special handling for .doc files with no text
#                 if file.filename.endswith('.doc') and (not parser.text or len(parser.text.strip()) < 10):
#                     os.remove(file_path)
#                     results["failed"] += 1
#                     results["summary"]["parsing_errors"] += 1
#                     results["errors"].append({
#                         "filename": file.filename,
#                         "error": (
#                             "Legacy .doc format not supported. "
#                             "Please convert to .docx or PDF format."
#                         ),
#                         "error_type": "legacy_doc_format",
#                         "solution": "Convert to DOCX or PDF"
#                     })
#                     continue
                    
#             except ValueError as ve:
#                 os.remove(file_path)
#                 results["failed"] += 1
#                 results["summary"]["parsing_errors"] += 1
                
#                 if file.filename.endswith('.doc'):
#                     results["errors"].append({
#                         "filename": file.filename,
#                         "error": str(ve),
#                         "error_type": "legacy_doc_unsupported",
#                         "solution": "Convert to DOCX or PDF format"
#                     })
#                 else:
#                     results["errors"].append({
#                         "filename": file.filename,
#                         "error": f"Failed to extract text: {str(ve)}",
#                         "error_type": "extraction_error"
#                     })
#                 continue
                
#             except Exception as parse_error:
#                 os.remove(file_path)
#                 results["failed"] += 1
#                 results["summary"]["parsing_errors"] += 1
#                 results["errors"].append({
#                     "filename": file.filename,
#                     "error": f"Failed to extract text: {str(parse_error)}",
#                     "error_type": "extraction_error"
#                 })
#                 continue

#             # ============================================================
#             # STEP 6: JOB DESCRIPTION DETECTION
#             # ============================================================
#             if parser.is_job_description():
#                 os.remove(file_path)
#                 results["failed"] += 1
#                 results["summary"]["job_descriptions"] += 1
#                 results["errors"].append({
#                     "filename": file.filename,
#                     "error": "Document appears to be a Job Description, not a resume",
#                     "error_type": "job_description"
#                 })
#                 continue

#             # ============================================================
#             # STEP 7: FULL PARSING
#             # ============================================================
#             try:
#                 full = parser.parse_full()
#                 basic = full["basic_fields"]
#                 quality = full["parsing_quality"]
#                 candidate_email = basic.get("email")
#             except Exception as full_parse_error:
#                 os.remove(file_path)
#                 results["failed"] += 1
#                 results["summary"]["parsing_errors"] += 1
#                 results["errors"].append({
#                     "filename": file.filename,
#                     "error": f"Failed to parse resume: {str(full_parse_error)}",
#                     "error_type": "parsing_error"
#                 })
#                 continue

#             # ============================================================
#             # STEP 8: DUPLICATE CHECK BY EMAIL
#             # ============================================================
#             email = basic.get("email")
            
#             if email:
#                 existing_email = db.query(models.Resume).filter(
#                     models.Resume.email == email,
#                     models.Resume.file_hash != file_hash
#                 ).first()
                
#                 if existing_email:
#                     # Add warning but continue (optional: you can reject here)
#                     pass

#             # ============================================================
#             # STEP 9: SAVE TO DATABASE
#             # ============================================================
#             resume_data = schemas.ResumeCreate(
#                 original_filename=file.filename,
#                 file_path=file_path,
#                 file_type=file.filename.rsplit(".", 1)[1].lower(),
#                 file_hash=file_hash,
#                 name=basic.get("name"),
#                 email=candidate_email if isinstance(candidate_email, str) else None,
#                 mobile_number=basic.get("mobile_number"),
#                 location=basic.get("location"),
#                 employee_name=employee_name,
#                 parsed_data=full["parsed_data"],
#                 search_text=full["search_text"],
#                 parsing_quality=quality,
#             )

#             try:
#                 created = crud.create_resume(db, resume_data)
#             except Exception as db_error:
#                 os.remove(file_path)
#                 results["failed"] += 1
#                 results["errors"].append({
#                     "filename": file.filename,
#                     "error": f"Database error: {str(db_error)}",
#                     "error_type": "database_error"
#                 })
#                 continue

#             # ============================================================
#             # STEP 10: SUCCESS - FIXED ATTRIBUTE ACCESS
#             # ============================================================
#             results["successful"] += 1
            
#             # Safe timestamp extraction
#             uploaded_timestamp = None
#             if hasattr(created, 'upload_timestamp') and created.upload_timestamp:
#                 uploaded_timestamp = created.upload_timestamp.isoformat()
#             elif hasattr(created, 'created_at') and created.created_at:
#                 uploaded_timestamp = created.created_at.isoformat()
            
#             results["resumes"].append({
#                 "id": created.id,
#                 "filename": file.filename,
#                 "name": created.name,
#                 "email": created.email,
#                 "mobile_number": created.mobile_number,
#                 "location": created.location,
#                 "employee_name": created.employee_name if hasattr(created, 'employee_name') else employee_name,
#                 "parsing_quality": created.parsing_quality,
#                 "uploaded_at": uploaded_timestamp
#             })

#         except Exception as e:
#             # ============================================================
#             # GENERAL ERROR HANDLER
#             # ============================================================
#             results["failed"] += 1
#             results["summary"]["parsing_errors"] += 1
#             results["errors"].append({
#                 "filename": file.filename,
#                 "error": f"Unexpected error: {str(e)}",
#                 "error_type": "unexpected_error",
#                 "traceback": traceback.format_exc()
#             })

#             # Cleanup
#             if file_path and os.path.exists(file_path):
#                 try:
#                     os.remove(file_path)
#                 except Exception as cleanup_error:
#                     print(f"Failed to cleanup file {file_path}: {cleanup_error}")

#     # ============================================================
#     # FINAL RESPONSE
#     # ============================================================
#     return {
#         **results,
#         "success_rate": f"{(results['successful'] / results['total'] * 100):.1f}%" if results['total'] > 0 else "0%"
#     }

@app.post("/api/resumes/bulk-upload")
async def bulk_upload_resumes(
    files: List[UploadFile] = File(...),
    employee_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Bulk upload multiple resume files.
    Supports: PDF, DOCX (DOC not recommended)
    Features: Duplicate detection, JD filtering, comprehensive error reporting
    """
    results = {
        "total": len(files),
        "successful": 0,
        "failed": 0,
        "resumes": [],
        "errors": [],
        "summary": {
            "duplicates": 0,
            "job_descriptions": 0,
            "parsing_errors": 0,
            "invalid_format": 0,
            "poor_quality": 0
        }
    }
    # if isinstance(employee_names, str):
    #     employee_names = [employee_names]
        
    for idx, file in enumerate(files):
        file_path = None
        parser = None

        # map provided employee_names (if any) to each file by index
        # current_employee_name=employee_name
        try:
            # ============================================================
            # STEP 1: FILE VALIDATION
            # ============================================================
            if not (file.filename.lower().endswith(('.pdf', '.docx', '.zip'))):
                results["failed"] += 1
                results["summary"]["invalid_format"] += 1
                results["errors"].append({
                    "filename": file.filename,
                    "error": "Invalid file type. Supported: PDF, DOCX",
                    "error_type": "invalid_format"
                })
                continue
            # 2. Read bytes and Hash IMMEDIATELY (Memory-based)
            file_content = await file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()

            # 3. BLOCKING DUPLICATE CHECK
            # We call the crud function using the hash we just generated
            if crud.check_duplicate_resume(db, file_hash=file_hash):
                results["failed"] += 1
                results["summary"]["duplicates"] += 1
                results["errors"].append({
                    "filename": file.filename, 
                    "error": "Duplicate file detected by hash", 
                    "error_type": "duplicate_hash"
                })
                continue

            # IMPORTANT: Reset pointer so shutil can save the file next
            await file.seek(0)
            
            # ============================================================
            # STEP 2: SAVE FILE
            # ============================================================
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            # safe_filename_str = secure_filename(file.filename)
            safe_filename_str = "".join([c for c in file.filename if c.isalnum() or c in (' ', '.', '_')]).strip()
            file_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{safe_filename_str}")

            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
            except Exception as save_error:
                results["failed"] += 1
                results["errors"].append({
                    "filename": file.filename,
                    "error": f"Failed to save file: {str(save_error)}",
                    "error_type": "file_save_error"
                })
                continue

            if file.filename.lower().endswith('.zip'):
                # ZIP handling
                with tempfile.TemporaryDirectory() as temp_dir:
                    try:
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)
                            extracted_files = zip_ref.namelist()
                    except Exception as e:
                        if os.path.exists(file_path): os.remove(file_path)
                        results["failed"] += 1
                        results["errors"].append({
                            "filename": file.filename,
                            "error": f"Failed to extract ZIP: {str(e)}",
                            "error_type": "zip_extraction_error"
                        })
                        continue
                    invalid_files = [ef for ef in extracted_files if not allowed_file(ef)]
                    if invalid_files:
                        os.remove(file_path)
                        results["failed"] += 1
                        results["errors"].append({
                            "filename": file.filename,
                            "error": f"ZIP contains invalid files: {invalid_files}",
                            "error_type": "invalid_zip_contents"
                        })
                        continue
                    # Process each extracted file
                    for ef in extracted_files:
                        ef_path = os.path.join(temp_dir, ef)
                        # File size check
                        file_size = os.path.getsize(ef_path)
                        MAX_FILE_SIZE = 10 * 1024 * 1024
                        if file_size > MAX_FILE_SIZE:
                            results["failed"] += 1
                            results["errors"].append({
                                "filename": ef,
                                "error": f"File too large ({file_size / 1024 / 1024:.2f}MB). Max: 10MB",
                                "error_type": "file_too_large"
                            })
                            continue
                        if file_size == 0:
                            results["failed"] += 1
                            results["errors"].append({
                                "filename": ef,
                                "error": "File is empty",
                                "error_type": "empty_file"
                            })
                            continue
                        # Compute hash
                        with open(ef_path, "rb") as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()
                        # Duplicate check by hash
                        existing_hash = db.query(models.ResumeN).filter(
                            models.ResumeN.file_hash == file_hash
                        ).first()
                        if existing_hash:
                            results["failed"] += 1
                            results["summary"]["duplicates"] += 1
                            results["errors"].append({
                                "filename": ef,
                                "error": f"Duplicate file (already uploaded as: {existing_hash.original_filename})",
                                "error_type": "duplicate_hash",
                                "existing_resume_id": existing_hash.id,
                                "existing_filename": existing_hash.original_filename
                            })
                            continue
                        # Create parser & extract text
                        try:
                            parser = ResumeParser(ef_path, use_ocr_fallback=True)
                            parser._extract_text()
                            # Special handling for .doc
                            if ef.endswith('.doc') and (not parser.text or len(parser.text.strip()) < 10):
                                results["failed"] += 1
                                results["summary"]["parsing_errors"] += 1
                                results["errors"].append({
                                    "filename": ef,
                                    "error": "Legacy .doc format not supported. Please convert to .docx or PDF format.",
                                    "error_type": "legacy_doc_format",
                                    "solution": "Convert to DOCX or PDF"
                                })
                                continue
                        except ValueError as ve:
                            results["failed"] += 1
                            results["summary"]["parsing_errors"] += 1
                            if ef.endswith('.doc'):
                                results["errors"].append({
                                    "filename": ef,
                                    "error": str(ve),
                                    "error_type": "legacy_doc_unsupported",
                                    "solution": "Convert to DOCX or PDF format"
                                })
                            else:
                                results["errors"].append({
                                    "filename": ef,
                                    "error": f"Failed to extract text: {str(ve)}",
                                    "error_type": "extraction_error"
                                })
                            continue
                        except Exception as parse_error:
                            results["failed"] += 1
                            results["summary"]["parsing_errors"] += 1
                            results["errors"].append({
                                "filename": ef,
                                "error": f"Failed to extract text: {str(parse_error)}",
                                "error_type": "extraction_error"
                            })
                            continue
                        # Job description detection
                        if parser.is_job_description():
                            results["failed"] += 1
                            results["summary"]["job_descriptions"] += 1
                            results["errors"].append({
                                "filename": ef,
                                "error": "Document appears to be a Job Description, not a resume",
                                "error_type": "job_description"
                            })
                            continue
                        # Full parsing
                        try:
                            # full = parser.parse_full()
                            full = await run_in_threadpool(parser.parse_full)
                            basic = full["basic_fields"]
                            quality = full["parsing_quality"]
                            candidate_email = basic.get("email")
                        except Exception as full_parse_error:
                            results["failed"] += 1
                            results["summary"]["parsing_errors"] += 1
                            results["errors"].append({
                                "filename": ef,
                                "error": f"Failed to parse resume: {str(full_parse_error)}",
                                "error_type": "parsing_error"
                            })
                            continue
                        
                        # 2. EMAIL VALIDATION GATE (After parsing, before DB save)
                        candidate_email = basic.get("email")
                        if candidate_email:
                            # Use your CRUD function to see if this person already exists
                            if crud.check_duplicate_resume(db, file_hash=None, email=candidate_email):
                                # BLOCK HERE: Delete the file we just saved and skip
                                if os.path.exists(file_path): os.remove(file_path)
                                results["failed"] += 1
                                results["summary"]["duplicates"] += 1
                                continue
                        # # Duplicate check by email
                        # email = basic.get("email")
                        # if email:
                        #     existing_email = db.query(models.ResumeN).filter(
                        #         models.ResumeN.email == email,
                        #         models.ResumeN.file_hash != file_hash
                        #     ).first()
                        #     if existing_email:
                        #         pass
                        # # Move to UPLOAD_DIR
                        # timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
                        # safe_filename = secure_filename(ef)
                        # final_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{safe_filename}")
                        # shutil.move(ef_path, final_path)
                        # Save to database
                        resume_data = schemas.ResumeCreate(
                            original_filename=ef,
                            file_path=file_path,
                            file_type=ef.rsplit(".", 1)[1].lower(),
                            file_hash=file_hash,
                            name=basic.get("name"),
                            email=candidate_email if isinstance(candidate_email, str) else None,
                            mobile_number=basic.get("mobile_number"),
                            location=basic.get("location") or "unknown",
                            linkedin_url=basic.get("linkedin_url"),
                            github_url=basic.get("github_url"),
                            personal_details=basic.get("personal_details", {}),
                            employee_name=employee_name,
                            parsed_data=full["parsed_data"],
                            search_text=full["search_text"],
                            parsing_quality=quality,
                        )
                        try:
                            # created = crud.create_resume(db, resume_data)
                            created = await run_in_threadpool(crud.create_resume, db, resume_data)
                            results["successful"] += 1
                            uploaded_timestamp = created.created_at.isoformat() if created.created_at else None
                            results["resumes"].append({
                                "id": created.id,
                                "filename": ef,
                                "name": created.name,
                                "email": created.email,
                                "mobile_number": created.mobile_number,
                                "location": created.location,
                                "employee_name":created.employee_name,
                                "parsing_quality": created.parsing_quality,
                                "uploaded_at": uploaded_timestamp
                            })
                        except Exception as db_error:
                            os.remove(file_path)
                            results["failed"] += 1
                            results["errors"].append({
                                "filename": ef,
                                "error": f"Database error: {str(db_error)}",
                                "error_type": "database_error"
                            })
                            continue
                # After processing all extracted, remove the ZIP
                os.remove(file_path)
                continue

            # ============================================================
            # STEP 3: FILE SIZE CHECK
            # ============================================================
            file_size = os.path.getsize(file_path)
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
            
            if file_size > MAX_FILE_SIZE or file_size==0:
                os.remove(file_path)
                results["failed"] += 1
                results["errors"].append({
                    "filename": file.filename,
                    "error": f"File too large ({file_size / 1024 / 1024:.2f}MB). Max: 10MB",
                    "error_type": "file_too_large"
                })
                continue
            

            # ============================================================
            # STEP 4: COMPUTE FILE HASH
            # ============================================================
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            # Early duplicate check by hash
            existing_resume = db.query(models.ResumeN).filter(
                models.ResumeN.file_hash == file_hash
            ).first()
            
            if existing_resume:
                os.remove(file_path)
                results["failed"] += 1
                results["summary"]["duplicates"] += 1
                results["errors"].append({
                    "filename": file.filename,
                    "error": f"Duplicate file (already uploaded as: {existing_resume.original_filename})",
                    "error_type": "duplicate_hash",
                    "existing_resume_id": existing_resume.id,
                    "existing_filename": existing_resume.original_filename
                })
                continue

            # ============================================================
            # STEP 5: CREATE PARSER & EXTRACT TEXT
            # ============================================================
            try:
                parser = ResumeParser(file_path, use_ocr_fallback=True)
                parser._extract_text()
                # await asyncio.to_thread(parser.extract_text)
                
                # Special handling for .doc files with no text
                if file.filename.endswith('.doc') and (not parser.text or len(parser.text.strip()) < 10):
                    os.remove(file_path)
                    results["failed"] += 1
                    results["summary"]["parsing_errors"] += 1
                    results["errors"].append({
                        "filename": file.filename,
                        "error": (
                            "Legacy .doc format not supported. "
                            "Please convert to .docx or PDF format."
                        ),
                        "error_type": "legacy_doc_format",
                        "solution": "Convert to DOCX or PDF"
                    })
                    continue
                    
            except ValueError as ve:
                os.remove(file_path)
                results["failed"] += 1
                results["summary"]["parsing_errors"] += 1
                
                if file.filename.endswith('.doc'):
                    results["errors"].append({
                        "filename": file.filename,
                        "error": str(ve),
                        "error_type": "legacy_doc_unsupported",
                        "solution": "Convert to DOCX or PDF format"
                    })
                else:
                    results["errors"].append({
                        "filename": file.filename,
                        "error": f"Failed to extract text: {str(ve)}",
                        "error_type": "extraction_error"
                    })
                continue
                
            except Exception as parse_error:
                os.remove(file_path)
                results["failed"] += 1
                results["summary"]["parsing_errors"] += 1
                results["errors"].append({
                    "filename": file.filename,
                    "error": f"Failed to extract text: {str(parse_error)}",
                    "error_type": "extraction_error"
                })
                continue

            # ============================================================
            # STEP 6: JOB DESCRIPTION DETECTION
            # ============================================================
            if parser.is_job_description():
                os.remove(file_path)
                results["failed"] += 1
                results["summary"]["job_descriptions"] += 1
                results["errors"].append({
                    "filename": file.filename,
                    "error": "Document appears to be a Job Description, not a resume",
                    "error_type": "job_description"
                })
                continue

            # ============================================================
            # STEP 7: FULL PARSING
            # ============================================================
            try:
                full = parser.parse_full()
                # full = await asyncio.to_thread(parser.parse_full)
                basic = full["basic_fields"]
                quality = full["parsing_quality"]
                candidate_email = basic.get("email")
            except Exception as full_parse_error:
                os.remove(file_path)
                results["failed"] += 1
                results["summary"]["parsing_errors"] += 1
                results["errors"].append({
                    "filename": file.filename,
                    "error": f"Failed to parse resume: {str(full_parse_error)}",
                    "error_type": "parsing_error"
                })
                continue

            # ============================================================
            # STEP 8: DUPLICATE CHECK BY EMAIL
            # ============================================================
            email = basic.get("email")
            
            if email:
                existing_email = db.query(models.ResumeN).filter(
                    models.ResumeN.email == email,
                    models.ResumeN.file_hash != file_hash
                ).first()
                
                if existing_email:
                    # Add warning but continue (optional: you can reject here)
                    pass

            # ============================================================
            # STEP 9: SAVE TO DATABASE
            # ============================================================
            resume_data = schemas.ResumeCreate(
                original_filename=file.filename,
                file_path=file_path,
                file_type=file.filename.rsplit(".", 1)[1].lower(),
                file_hash=file_hash,
                name=basic.get("name"),
                email=candidate_email if isinstance(candidate_email, str) else None,
                mobile_number=basic.get("mobile_number"),
                location=basic.get("location") or "Unknown",
                linkedin_url=basic.get("linkedin_url"),
                github_url=basic.get("github_url"),
                personal_details=basic.get("personal_details", {}),
                employee_name=employee_name,
                parsed_data=full["parsed_data"],
                search_text=full["search_text"],
                parsing_quality=quality,
            )

            try:
                # created = crud.create_resume(db, resume_data)
                created = await run_in_threadpool(crud.create_resume, db, resume_data)
                
            except Exception as db_error:
                # changes done
                safe_rollback(db)
                if os.path.exists(file_path):
                    os.remove(file_path)
                results["failed"] += 1
                results["errors"].append({
                    "filename": file.filename,
                    "error": f"Database error: {str(db_error)}",
                    "error_type": "database_error"
                })
                continue

            # ============================================================
            # STEP 10: SUCCESS - FIXED ATTRIBUTE ACCESS
            # ============================================================
            results["successful"] += 1
            
            # Safe timestamp extraction
            uploaded_timestamp = None
            if hasattr(created, 'upload_timestamp') and created.upload_timestamp:
                uploaded_timestamp = created.upload_timestamp.isoformat()
            elif hasattr(created, 'created_at') and created.created_at:
                uploaded_timestamp = created.created_at.isoformat()
            
            results["resumes"].append({
                "id": created.id,
                "filename": file.filename,
                "name": created.name,
                "email": created.email,
                "mobile_number": created.mobile_number,
                "location": created.location,
                "employee_name": created.employee_name if hasattr(created, 'employee_name') else employee_name,
                "parsing_quality": created.parsing_quality,
                "uploaded_at": uploaded_timestamp
            })

        except Exception as e:
            # ============================================================
            # GENERAL ERROR HANDLER
            # ============================================================
            results["failed"] += 1
            results["summary"]["parsing_errors"] += 1
            results["errors"].append({
                "filename": file.filename,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unexpected_error",
                "traceback": traceback.format_exc()
            })
            safe_rollback(db)
            # Cleanup
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as cleanup_error:
                    print(f"Failed to cleanup file {file_path}: {cleanup_error}")

    # ============================================================
    # FINAL RESPONSE
    # ============================================================
    processed = results["successful"] + results["failed"],
    processed_count = processed[0] if isinstance(processed, tuple) else processed
    return {
        **results,
        # "success_rate": f"{(results['successful'] / results['total'] * 100):.1f}%" if results['total'] > 0 else "0%"
        "success_rate": f"{(results['successful'] / processed_count * 100):.1f}%" if processed_count > 0 else "0%"
    }
    

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app import crud, models, schemas
from app.database import get_db


# ============================================================
# COMPREHENSIVE SEARCH ENDPOINT
# ============================================================

@app.get("/api/resumes/search/comprehensive")
def comprehensive_search(
    role: Optional[str] = Query(None, description="Job title e.g. 'Java Developer'"),
    skills: Optional[str] = Query(None, description="Comma separated e.g. 'Java,AWS,Spring Boot'"),
    location: Optional[str] = Query(None, description="City e.g. 'Hyderabad'"),
    min_experience: Optional[int] = Query(None, description="Min years e.g. 4"),
    max_experience: Optional[int] = Query(None, description="Max years e.g. 7"),
    education: Optional[str] = Query(None, description="Degree e.g. 'B.Tech,MCA'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Comprehensive resume search with relevance scoring.
    
    Example:
    GET /api/resumes/search/comprehensive?
        role=Java Developer
        &skills=Java,AWS,Spring Boot,Microservices
        &location=Hyderabad
        &min_experience=4
        &max_experience=7
        &education=B.Tech
    """
    
    results = crud.comprehensive_search(
        db=db,
        role=role,
        skills=skills,
        location=location,
        min_experience=min_experience,
        max_experience=max_experience,
        education=education,
        skip=skip,
        limit=limit,
    )
    
    # Format response
    formatted = []
    for item in results:
        resume = item["resume"]
        score = item["score"]
        details = item["match_details"]
        
        formatted.append({
            "id": resume.id,
            "name": resume.name,
            "email": resume.email,
            "mobile_number": resume.mobile_number,
            "location": resume.location,
            "parsing_quality": resume.parsing_quality,
            "version": resume.version,
            "uploaded_at": resume.upload_timestamp.isoformat() if resume.upload_timestamp else None,
            
            # Relevance data
            "relevance_score": score,
            "match_percentage": min(round((score["total"] / 100) * 100), 100),
            "match_details": details,
        })
    
    return {
        "total": len(formatted),
        "filters_applied": {
            "role": role,
            "skills": skills.split(",") if skills else [],
            "location": location,
            "experience": f"{min_experience}-{max_experience} years" if min_experience else None,
            "education": education,
        },
        "results": formatted,
    }


# ============================================================
# VERSION CHECK ENDPOINT (Call BEFORE upload)
# ============================================================

@app.post("/api/resumes/check-version")
async def check_resume_version(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    import hashlib, shutil, os, traceback
    from datetime import datetime

    temp_path = None

    try:
        # ── STEP 1: Validate file type ──────────────────────────
        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Invalid file type. Use PDF or DOCX.")

        # ── STEP 2: Save temp file ───────────────────────────────
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        safe_name = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_DIR, f"temp_{timestamp}_{safe_name}")

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ── STEP 3: Compute file hash ────────────────────────────
        with open(temp_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        # ── STEP 4: Quick parse for email/phone ──────────────────
        email = None
        phone = None
        name = None

        try:
            from app.resume_parser_hybrid import HybridResumeParser
            parser = HybridResumeParser(temp_path, use_ocr_fallback=False)
            # Use sync parse only (faster for version check)
            full = parser.parse_full()
            basic = full.get("basic_fields", {})
            email = basic.get("email")
            phone = basic.get("mobile_number")
            name  = basic.get("name")
        except Exception as parse_err:
            print(f"⚠ Parse error during version check: {parse_err}")
            # Continue without parsed data - still check by hash

        # ── STEP 5: Check exact duplicate by hash ────────────────
        try:
            existing_hash = db.query(models.ResumeN).filter(
                models.ResumeN.file_hash == file_hash
            ).first()

            if existing_hash:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

                uploaded_at = None
                try:
                    ts = getattr(existing_hash, 'upload_timestamp', None) or getattr(existing_hash, 'created_at', None)
                    if ts:
                        uploaded_at = ts.strftime("%b %d, %Y")
                except:
                    pass

                return {
                    "status": "exact_duplicate",
                    "message": f"This exact file was already uploaded{' on ' + uploaded_at if uploaded_at else ''}.",
                    "existing_resume": {
                        "id": existing_hash.id,
                        "name": existing_hash.name,
                        "email": existing_hash.email,
                        "filename": existing_hash.original_filename,
                        "uploaded_at": uploaded_at,
                        "version": getattr(existing_hash, 'version', 1),
                    }
                }
        except Exception as hash_err:
            print(f"⚠ Hash check error: {hash_err}")

        # ── STEP 6: Check same person by email/phone ─────────────
        existing_person = None

        try:
            if email:
                existing_person = db.query(models.ResumeN).filter(
                    or_(
                        models.ResumeN.email == email,
                        models.ResumeN.employee_name == name  # ← ADD THIS
                    )
                ).order_by(models.ResumeN.id.desc()).first()

            if not existing_person and phone:
                existing_person = db.query(models.ResumeN).filter(
                    models.ResumeN.mobile_number == phone
                ).order_by(models.ResumeN.id.desc()).first()

        except Exception as person_err:
            print(f"⚠ Person check error: {person_err}")

        if existing_person:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

            uploaded_at = None
            try:
                ts = getattr(existing_person, 'upload_timestamp', None) or getattr(existing_person, 'created_at', None)
                if ts:
                    uploaded_at = ts.strftime("%b %d, %Y")
            except:
                pass

            return {
                "status": "new_version",
                "message": f"A resume for {existing_person.name or 'this candidate'} already exists{' (uploaded ' + uploaded_at + ')' if uploaded_at else ''}.",
                "existing_resume": {
                    "id": existing_person.id,
                    "name": existing_person.name,
                    "email": existing_person.email,
                    "filename": existing_person.original_filename,
                    "uploaded_at": uploaded_at,
                    "version": getattr(existing_person, 'version', 1),
                },
                # Pass temp file info so upload-with-action can reuse it
                "temp_path": temp_path,
                "file_hash": file_hash,
                "parsed_name": name,
                "parsed_email": email,
            }

        # ── STEP 7: Brand new candidate ──────────────────────────
        # Keep temp file for upload-with-action to reuse
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
        print(f"✗ check-version error: {traceback.format_exc()}")
        # Clean up temp file on error
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        raise HTTPException(
            status_code=500,
            detail=f"Version check failed: {str(e)}"
        )


# ============================================================
# UPLOAD WITH VERSION ACTION
# ============================================================

@app.post("/api/resumes/upload-with-action")
async def upload_with_version_action(
    file: UploadFile = File(...),
    action: str = Query(..., description="'new', 'replace', 'keep_both', 'skip'"),
    existing_resume_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Upload resume with explicit version action.
    
    Actions:
    - "new": Normal upload (brand new candidate)
    - "replace": Archive old, save new as latest
    - "keep_both": Keep old + add new version
    - "skip": Discard new, keep old
    """
    import hashlib, shutil, os, traceback
    from datetime import datetime
    
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # ── SKIP ACTION ───────────────────────────────────────────
    if action == "skip":
        return {
            "success": True,
            "action_taken": "skip",
            "message": "Kept existing resume, discarded new upload"
        }
    
    # ── SAVE FILE ─────────────────────────────────────────────
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        # ── PARSE RESUME ──────────────────────────────────────
        from app.resume_parser_hybrid import HybridResumeParser
        parser = HybridResumeParser(file_path, use_ocr_fallback=True)
        
        if parser.is_creative_resume():
            await file.seek(0)
            full = await parser.parse_async(file)
        else:
            full = parser.parse_full()
        
        basic = full["basic_fields"]
        quality = full["parsing_quality"]
        
        resume_data = schemas.ResumeCreate(
            original_filename=file.filename,
            file_path=file_path,
            file_type=file.filename.rsplit(".", 1)[1].lower(),
            file_hash=file_hash,
            name=basic.get("name"),
            email=basic.get("email"),
            employee_name=basic.get("employee_name"),
            mobile_number=basic.get("mobile_number"),
            location=basic.get("location"),
            parsed_data=full["parsed_data"],
            search_text=full["search_text"],
            parsing_quality=quality,
        )
        
        # ── HANDLE ACTIONS ────────────────────────────────────
        if action == "replace" and existing_resume_id:
            created = crud.replace_resume_version(
                db=db,
                old_resume_id=existing_resume_id,
                new_resume_data=resume_data,
                file_hash=file_hash,
            )
            action_message = f"Replaced old resume (v{created.version - 1}) with new version (v{created.version})"
            
        elif action == "keep_both" and existing_resume_id:
            created = crud.keep_both_versions(
                db=db,
                old_resume_id=existing_resume_id,
                new_resume_data=resume_data,
                file_hash=file_hash,
            )
            action_message = f"Saved as new version (v{created.version}), old version preserved"
            
        else:
            # Normal new upload
            created = crud.create_resume(db, resume_data)
            action_message = "New resume uploaded successfully"
        
        return {
            "success": True,
            "action_taken": action,
            "message": action_message,
            "resume": {
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


# ============================================================
# GET RESUME VERSION HISTORY
# ============================================================

@app.get("/api/resumes/{resume_id}/versions")
def get_resume_versions(
    resume_id: int,
    db: Session = Depends(get_db),
):
    """Get all versions of a resume"""
    resume = crud.get_resume(db, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if not resume.email:
        return {"versions": [resume], "total": 1}
    
    versions = crud.get_resume_versions(db, resume.email)
    
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