from sqlalchemy.orm import Session
from sqlalchemy import or_, text, func, and_
from typing import List, Optional, Dict
from . import models, schemas
from .embedding_service import generate_embedding
# Import your engine from your database config file
from .database import engine
import re,json
import concurrent.futures
import time
# ======================================================
# CREATE & VERSIONING
# ======================================================

# IMPORT: Make sure 'engine' is imported from your database configuration
from .database import engine 

def safe_partition_name(location: str) -> str:
    """Sanitizes location for PostgreSQL table names."""
    location = (location or "unknown").lower()
    location = re.sub(r"[^a-z0-9_]+", "_", location).strip("_")
    return f"resumes_n_{location}"



# def create_resume(db: Session, ResumeN_data: schemas.ResumeCreate):
#     location = ResumeN_data.location or "unknown"
#     partition_name = safe_partition_name(location)
    
#     # --- STEP 1: PRE-CREATE PARTITION (Separate Connection) ---
#     try:
#         # Using engine.connect() creates a separate transaction that 
#         # finishes before the main INSERT starts.
#         with engine.connect() as conn:
#             conn.execute(text(f"""
#                 DO $$ 
#                 BEGIN 
#                     IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = '{partition_name}') THEN
#                         EXECUTE 'CREATE TABLE {partition_name} PARTITION OF resumes_n FOR VALUES IN (' || quote_literal('{location}') || ')';
#                     END IF;
#                 END $$;
#             """))
#             conn.commit() 
#     except Exception as e:
#         # We don't raise error here; if this fails, the record will land in 'resumes_n_default'
#         print(f"Partition Check Note: {e}")

#     # --- STEP 2: GENERATE EMBEDDING ---
#     embedding = generate_embedding(ResumeN_data.search_text)

#     # --- STEP 3: DATA INSERTION (Main Session) ---
#     new_resume = models.ResumeN(
#         original_filename=ResumeN_data.original_filename,
#         file_path=ResumeN_data.file_path,
#         file_type=ResumeN_data.file_type,
#         file_hash=ResumeN_data.file_hash,
#         name=ResumeN_data.name,
#         email=ResumeN_data.email,
#         mobile_number=ResumeN_data.mobile_number,
#         location=location,
#         employee_name=ResumeN_data.employee_name,
#         parsed_data=ResumeN_data.parsed_data,
#         search_text=ResumeN_data.search_text,
#         resume_text=ResumeN_data.search_text,
#         embedding=embedding,
#         is_edited=False,
#         parsing_quality=ResumeN_data.parsing_quality or "unknown",
#         extraction_method=ResumeN_data.extraction_method,
#         version=1,
#         is_latest=True,
#         archived=False
#     )

#     try:
#         db.add(new_resume)
#         db.commit()
#         db.refresh(new_resume)
#         return new_resume
#     except Exception as e:
#         db.rollback() # CRITICAL: Reset session state for the next file in bulk upload
#         raise e
    
def create_resume(db: Session, resume_data: schemas.ResumeCreate):
    location = resume_data.location or "unknown"
    partition_name = safe_partition_name(location)
    
    # --- STEP 1: FIX DEADLOCK (Use existing session) ---
    try:
        # We check/create partition using the 'db' session we already have
        db.execute(text(f"""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = '{partition_name}') THEN
                    EXECUTE 'CREATE TABLE {partition_name} PARTITION OF resumes_n 
                             FOR VALUES IN (''' || '{location}' || ''')';
                END IF;
            END $$;
        """))
        db.flush() 
    except Exception as e:
        print(f"⚠️ Partition check error (ignoring): {e}")

    # --- STEP 2: GENERATE EMBEDDING ---
    # This uses your SentenceTransformer model
    try:
        embedding = generate_embedding(resume_data.search_text)
    except Exception as e:
        print(f"⚠️ Embedding failed: {e}")
        embedding = [0.0] * 384  # Fallback to zero vector

    # --- STEP 3: CREATE THE RECORD ---
    new_resume = models.ResumeN(
        original_filename=resume_data.original_filename,
        file_path=resume_data.file_path,
        file_type=resume_data.file_type,
        file_hash=resume_data.file_hash,
        name=resume_data.name,
        email=resume_data.email,
        mobile_number=resume_data.mobile_number,
        location=location,
        employee_name=resume_data.employee_name,
        parsed_data=resume_data.parsed_data,
        search_text=resume_data.search_text,
        resume_text=resume_data.search_text,  # Mapping search_text to resume_text
        embedding=embedding,
        linkedin_url=resume_data.linkedin_url,
        github_url=resume_data.github_url,
        personal_details=json.dumps(resume_data.personal_details) if resume_data.personal_details else "{}",
        is_edited=False,
        parsing_quality=resume_data.parsing_quality or "unknown",
        extraction_method=resume_data.extraction_method,
        version=1,
        is_latest=True,
        archived=False
    )

    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)
    
    print(f"✅ SUCCESS: Resume saved with ID {new_resume.id}")
    return new_resume

# def safe_partition_name(location: str) -> str:
#     location = (location or "unknown").lower()
#     # Replace non-alphanumeric characters with underscores
#     location = re.sub(r"[^a-z0-9_]+", "_", location).strip("_")
#     return f"resumes_n_{location}"

# def create_resume(db: Session, ResumeN_data: schemas.ResumeCreate):
#     """Creates a new ResumeN entry by ensuring the partition exists first."""
    
#     location = ResumeN_data.location or "unknown"
#     partition_name = safe_partition_name(location)
    
#     # 1. Ensure the partition exists using a SEPARATE connection
#     # We use engine.connect() instead of db.connection() to avoid transaction conflicts
#     try:
#         with engine.connect() as conn:
#             # We wrap it in a transaction block that commits immediately
#             conn.execute(text(f"""
#                 DO $$ 
#                 BEGIN 
#                     IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = '{partition_name}') THEN
#                         EXECUTE 'CREATE TABLE {partition_name} PARTITION OF resumes_n FOR VALUES IN (' || quote_literal('{location}') || ')';
#                     END IF;
#                 END $$;
#             """))
#             conn.commit() 
#     except Exception as e:
#         # Log it but don't crash; if it fails, the trigger or DEFAULT partition might handle it
#         print(f"Partition Check Note: {e}")

#     # 2. Generate Embedding
#     embedding = generate_embedding(ResumeN_data.search_text)
#     if embedding is None:
#         raise ValueError("Embedding generation failed")

#     # 3. Create the Model Instance
#     new_ResumeN = models.ResumeN(
#         original_filename=ResumeN_data.original_filename,
#         file_path=ResumeN_data.file_path,
#         file_type=ResumeN_data.file_type,
#         file_hash=ResumeN_data.file_hash,
#         name=ResumeN_data.name,
#         email=ResumeN_data.email,
#         mobile_number=ResumeN_data.mobile_number,
#         location=location,
#         employee_name=ResumeN_data.employee_name,
#         parsed_data=ResumeN_data.parsed_data,
#         search_text=ResumeN_data.search_text,
#         resume_text=ResumeN_data.search_text,
#         embedding=embedding,
#         is_edited=False,
#         parsing_quality=ResumeN_data.parsing_quality or "unknown",
#         extraction_method=ResumeN_data.extraction_method,
#         version=1,
#         is_latest=True,
#         archived=False
#     )

#     # 4. Save to Database (Main Transaction)
#     try:
#         db.add(new_ResumeN)
#         db.commit()
#         db.refresh(new_ResumeN)
#         return new_ResumeN
#     except Exception as e:
#         db.rollback() # Crucial: Clean up the session if the insert fails
#         raise e

def replace_resume_version(db: Session, old_ResumeN_id: int, old_location: str, new_ResumeN_data: schemas.ResumeCreate, file_hash: str) -> models.ResumeN:
    """Archives the old version and inserts a new one as latest."""
    old_ResumeN = db.query(models.ResumeN).filter(
        models.ResumeN.id == old_ResumeN_id, 
        models.ResumeN.location == old_location
    ).first()
    
    if old_ResumeN:
        old_ResumeN.is_latest = False
        old_ResumeN.archived = True
        db.commit()
        
        # Increment version based on existing records for this email
        max_v = db.query(func.max(models.ResumeN.version)).filter(models.ResumeN.email == old_ResumeN.email).scalar() or 1
        
        # Create new ResumeN with incremented version
        new_ResumeN = models.ResumeN(
            **new_ResumeN_data.dict(),
            version=max_v + 1,
            is_latest=True,
            archived=False,
            previous_version_id=old_ResumeN_id,
            file_hash=file_hash,
        )
        # db.commit()
        try:
            db.add(new_ResumeN)
            db.commit()
            db.refresh(new_ResumeN)
        except:
            db.rollback()
            raise
        # return new_ResumeN

def keep_both_versions(db: Session, old_ResumeN_id: int, old_location: str, new_ResumeN_data: schemas.ResumeCreate, file_hash: str) -> models.ResumeN:
    """Marks old version as not latest but keeps it unarchived, then adds new version."""
    old_ResumeN = db.query(models.ResumeN).filter(
        models.ResumeN.id == old_ResumeN_id, 
        models.ResumeN.location == old_location
    ).first()
    
    if old_ResumeN:
        old_ResumeN.is_latest = False
        db.commit()
        max_version = db.query(func.max(models.ResumeN.version)).filter(
            models.ResumeN.email == old_ResumeN.email
        ).scalar() or 1
        
        # Create new resume
        new_resume = models.ResumeN(
            **new_ResumeN_data.dict(),
            version=max_version + 1,
            is_latest=True,
            archived=False,
            previous_version_id=old_ResumeN_id,
            file_hash=file_hash,
        )
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        return new_resume
    
    return None

def get_resume_versions(db: Session, email: str) -> List[models.ResumeN]:
    """Retrieves all historical versions of a ResumeN by email."""
    return db.query(models.ResumeN).filter(models.ResumeN.email == email).order_by(models.ResumeN.version.desc()).all()

def check_duplicate_resume(db: Session, file_hash: str, email: str = None):
    """
    Checks if a resume already exists based on file hash or email.
    """
    # 1. Check if the exact same file exists
    hash_exists = db.query(models.ResumeN).filter(models.ResumeN.file_hash == file_hash).first()
    if hash_exists:
        return True
    
    # 2. Check if a resume with this email already exists (if email was parsed)
    if email:
        email_exists = db.query(models.ResumeN).filter(models.ResumeN.email == email).first()
        if email_exists:
            return True
            
    return False

# ======================================================
# READ & UTILITIES
# ======================================================

# def get_resume(db: Session, ResumeN_id: int, location: str) -> Optional[models.ResumeN]:
#     """Reads a specific ResumeN. Location is required for partition routing."""
#     return db.query(models.ResumeN).filter(models.ResumeN.id == ResumeN_id, models.ResumeN.location == location).first()

def get_resume(db: Session, ResumeN_id: int, location: Optional[str] = None) -> Optional[models.ResumeN]:
    query = db.query(models.ResumeN).filter(models.ResumeN.id == ResumeN_id)
    if location:
        query = query.filter(models.ResumeN.location == location)
    return query.first()

def get_resumes(db: Session, skip: int = 0, limit: int = 100) -> List[models.ResumeN]:
    """Lists ResumeNs across all partitions."""
    return db.query(models.ResumeN).filter(models.ResumeN.is_latest == True).offset(skip).limit(limit).all()

def get_resumes_count(db: Session) -> int:
    """Counts latest ResumeNs across all partitions."""
    return db.query(models.ResumeN).filter(models.ResumeN.is_latest == True).count()

def update_resume(db: Session, ResumeN_id: int, location: str, ResumeN_update: schemas.ResumeUpdate) -> Optional[models.ResumeN]:
    """Updates ResumeN metadata and marks as edited."""
    db_ResumeN = get_resume(db, ResumeN_id, location)
    if not db_ResumeN:
        return None
    for field, value in ResumeN_update.dict(exclude_unset=True).items():
        setattr(db_ResumeN, field, value)
    db_ResumeN.is_edited = True
    db.commit()
    db.refresh(db_ResumeN)
    return db_ResumeN

def delete_resume(db: Session, ResumeN_id: int, location: str) -> bool:
    """Deletes a ResumeN from its specific partition."""
    db_ResumeN = get_resume(db, ResumeN_id, location)
    if not db_ResumeN:
        return False
    db.delete(db_ResumeN)
    db.commit()
    return True

# ============================================================
# ResumeN VERSION MANAGEMENT
# ============================================================

def check_resume_version(
    db: Session,
    email: Optional[str],
    phone: Optional[str],
    file_hash: str,
) -> Dict:
    """
    Smart duplicate/version detection.
    
    Returns one of:
    - {"status": "new"}                    → Brand new candidate
    - {"status": "exact_duplicate", ...}   → Same file uploaded again
    - {"status": "new_version", ...}       → Same person, updated ResumeN
    """
    
    # ── CHECK 1: EXACT SAME FILE (hash match) ─────────────────
    existing_hash = db.query(models.ResumeN).filter(
        models.ResumeN.file_hash == file_hash
    ).first()
    
    if existing_hash:
        return {
            "status": "exact_duplicate",
            "message": f"This exact file was already uploaded on {existing_hash.upload_timestamp.strftime('%b %d, %Y')}",
            "existing_ResumeN": {
                "id": existing_hash.id,
                "name": existing_hash.name,
                "email": existing_hash.email,
                "uploaded_at": existing_hash.upload_timestamp.isoformat() if existing_hash.upload_timestamp else None,
                "filename": existing_hash.original_filename,
            }
        }
    
    # ── CHECK 2: SAME PERSON (email or phone match) ───────────
    existing_person = None
    
    if email:
        existing_person = db.query(models.ResumeN).filter(
            models.ResumeN.email == email,
            models.ResumeN.is_latest == True,
            models.ResumeN.archived == False,
        ).first()
    
    if not existing_person and phone:
        existing_person = db.query(models.ResumeN).filter(
            models.ResumeN.mobile_number == phone,
            models.ResumeN.is_latest == True,
            models.ResumeN.archived == False,
        ).first()
    
    if existing_person:
        # Count how many versions exist
        version_count = db.query(models.ResumeN).filter(
            models.ResumeN.email == email
        ).count()
        
        return {
            "status": "new_version",
            "message": f"A ResumeN for {existing_person.name} already exists (uploaded {existing_person.upload_timestamp.strftime('%b %d, %Y') if existing_person.upload_timestamp else 'previously'})",
            "existing_ResumeN": {
                "id": existing_person.id,
                "name": existing_person.name,
                "email": existing_person.email,
                "uploaded_at": existing_person.upload_timestamp.isoformat() if existing_person.upload_timestamp else None,
                "filename": existing_person.original_filename,
                "version": existing_person.version or 1,
                "total_versions": version_count,
            }
        }
    
    # ── CHECK 3: BRAND NEW ────────────────────────────────────
    return {"status": "new"}


# ======================================================
# SEARCH FUNCTIONS
# ======================================================

def search_resumes(db: Session, query: str, skip: int = 0, limit: int = 100) -> List[models.ResumeN]:
    """Fast keyword-only search using the generated TSVector column."""
    return db.query(models.ResumeN).filter(
        text("tsv_content @@ plainto_tsquery('english', :q)"),
        models.ResumeN.is_latest == True
    ).params(q=query).offset(skip).limit(limit).all()

def search_resumes_with_filters(
    db: Session,
    query: Optional[str] = None,
    location: Optional[str] = None,
    skills: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ResumeN]:
    """Search using keywords, specific locations, and skills using TSVector indexing."""
    db_query = db.query(models.ResumeN).filter(models.ResumeN.is_latest == True)

    if query:
        db_query = db_query.filter(text("tsv_content @@ plainto_tsquery('english', :q)")).params(q=query)
    
    if location:
        db_query = db_query.filter(models.ResumeN.location.ilike(f"%{location}%"))
        
    if skills:
        # Formats skills for a strict AND search in TSVector
        formatted_skills = " & ".join([s.strip() for s in skills.split(',') if s.strip()])
        db_query = db_query.filter(text("tsv_content @@ to_tsquery('english', :s)")).params(s=formatted_skills)

    return db_query.offset(skip).limit(limit).all()

def comprehensive_search(
    db: Session,
    role: Optional[str] = None,
    skills: Optional[str] = None,
    location: Optional[str] = None,
    min_experience: Optional[int] = None,
    max_experience: Optional[int] = None,
    education: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Dict]:
    """Advanced search with relevance scoring and match details."""
    query = db.query(models.ResumeN).filter(
        models.ResumeN.archived == False,
        models.ResumeN.is_latest == True
    )

    if role or skills:
        combined = f"{role or ''} {skills or ''}".strip().replace(",", " ")
        query = query.filter(text("tsv_content @@ plainto_tsquery('english', :terms)")).params(terms=combined)

    if location:
        query = query.filter(text("tsv_content @@ plainto_tsquery('english', :loc)")).params(loc=location)

    # Scoring logic
    all_ResumeNs = query.all()
    scored_ResumeNs = []
    for ResumeN in all_ResumeNs:
        score_data = _calculate_relevance_score(ResumeN, role, skills, location, min_experience, max_experience, education)
        # changes done
        scored_ResumeNs.append({"resume": ResumeN, "score": score_data, "match_details": score_data})

    # scored_ResumeNs.sort(key=lambda x: x["score"], reverse=True)
    scored_ResumeNs.sort(key=lambda x: x["score"]["total"], reverse=True)
    return scored_ResumeNs[skip:skip + limit]

def _calculate_relevance_score(
    ResumeN: models.ResumeN,
    role: Optional[str],
    skills: Optional[str],
    location: Optional[str],
    min_experience: Optional[int],
    max_experience: Optional[int],
    education: Optional[str],
) -> Dict:
    """
    Calculate relevance score for a ResumeN.
    
    Scoring weights:
    - Skills match: 40 points (8 per skill, max 5 skills)
    - Role match:   25 points
    - Location:     20 points
    - Experience:   10 points
    - Education:     5 points
    """
    
    search_text = (ResumeN.search_text or "").lower()
    details = {
        "skills_matched": [],
        "skills_missing": [],
        "role_match": False,
        "location_match": False,
        "experience_match": False,
        "education_match": False,
    }
    total_score = 0
    
    # ── SKILLS SCORING (40 pts max) ───────────────────────────
    skills_score = 0
    if skills:
        skill_list = [s.strip().lower() for s in skills.split(',')]
        matched = []
        missing = []
        
        for skill in skill_list:
            if skill in search_text:
                matched.append(skill)
                skills_score += min(8, 40 // len(skill_list))
            else:
                missing.append(skill)
        
        details["skills_matched"] = matched
        details["skills_missing"] = missing
        details["skills_score"] = min(skills_score, 40)
        total_score += min(skills_score, 40)
    
    # ── ROLE SCORING (25 pts) ─────────────────────────────────
    if role:
        role_terms = [r.strip().lower() for r in role.split(',')]
        role_found = any(term in search_text for term in role_terms)
        
        if role_found:
            details["role_match"] = True
            details["role_score"] = 25
            total_score += 25
        else:
            details["role_score"] = 0
    
    # ── LOCATION SCORING (20 pts) ─────────────────────────────
    if location:
        location_lower = location.lower()
        ResumeN_location = (ResumeN.location or "").lower()
        
        if location_lower in ResumeN_location or location_lower in search_text:
            details["location_match"] = True
            details["location_score"] = 20
            total_score += 20
        else:
            details["location_score"] = 0
    
    # ── EXPERIENCE SCORING (10 pts) ───────────────────────────
    if min_experience is not None:
        exp_found = False
        for yr in range(min_experience, (max_experience or min_experience + 5) + 1):
            patterns = [f"{yr} year", f"{yr}+ year", f"{yr}yrs", f"{yr} yrs"]
            if any(p in search_text for p in patterns):
                exp_found = True
                break
        
        if exp_found:
            details["experience_match"] = True
            details["experience_score"] = 10
            total_score += 10
        else:
            details["experience_score"] = 0
    
    # ── EDUCATION SCORING (5 pts) ─────────────────────────────
    if education:
        edu_terms = [e.strip().lower() for e in education.split(',')]
        edu_found = any(term in search_text for term in edu_terms)
        
        if edu_found:
            details["education_match"] = True
            details["education_score"] = 5
            total_score += 5
        else:
            details["education_score"] = 0
    
    return {
        "total": total_score,
        "details": details,
        "match_percentage": min(round((total_score / 100) * 100), 100)
    }

# def semantic_vector_search(
#     db: Session, 
#     search_query: str, 
#     limit: int = 10
# ) -> List[Dict]:
#     """
#     Performs a semantic search using pgvector and returns the mathematical accuracy score.
#     """
#     # 1. Convert the recruiter's text query into a vector array
#     query_embedding = generate_embedding(search_query)
    
#     # 2. Calculate Cosine Similarity. 
#     # pgvector uses `<=>` for Cosine Distance (cosine_distance in SQLAlchemy). 
#     # Similarity = 1 - Distance. Multiply by 100 for a percentage score.
#     similarity_expr = (1 - models.ResumeN.embedding.cosine_distance(query_embedding)) * 100

#     # 3. Execute the search, ordering by the closest vectors
#     results = db.query(
#         models.ResumeN,
#         similarity_expr.label("similarity_score")
#     ).filter(
#         models.ResumeN.is_latest == True,
#         models.ResumeN.archived == False
#     ).order_by(
#         models.ResumeN.embedding.cosine_distance(query_embedding)
#     ).limit(limit).all()

#     # 4. Format the output so the frontend can display the exact accuracy
#     scored_results = []
#     for resume, score in results:
#         scored_results.append({
#             "resume_id": resume.id,
#             "candidate_name": resume.name,
#             "location": resume.location,
#             "ai_accuracy_score": round(score, 2) # Round to 2 decimals
#         })

#     return scored_results



def semantic_vector_search(
    db: Session, 
    search_query: str,
    limit: int = 10
) -> List[Dict]:
    """
    Single Search Bar Approach: 
    1. Uses FTS to filter by keywords across the ENTIRE candidate profile.
    2. Ranks the remaining candidates using AI semantic similarity.
    """
    # 1. Generate the semantic vector for the AI ranking
    # clean_query = search_query.strip().lower()
    clean_query = search_query.strip().lower().replace(",", " ")
    
    # 2. Generate the AI vector using the perfectly clean string
    query_embedding = generate_embedding(clean_query)
    # query_embedding = generate_embedding(search_query)
    similarity_expr = (1 - models.ResumeN.embedding.cosine_distance(query_embedding)) * 100

    # 2. Start the base query
    base_query = db.query(
        models.ResumeN,
        similarity_expr.label("similarity_score")
    ).filter(
        models.ResumeN.is_latest == True,
        models.ResumeN.archived == False
    )

    # 3. THE UNIFIED KEYWORD FILTER
    # websearch_to_tsquery scans the tsv_content (which holds all resume text, location, etc.)
    # It automatically ignores English stop words (in, for, the) and supports exact-match quotes.
    base_query = base_query.filter(
        text("tsv_content @@ websearch_to_tsquery('english', :q)")
    ).params(q=clean_query)

    # 4. Rank the filtered results mathematically
    results = base_query.order_by(
        models.ResumeN.embedding.cosine_distance(query_embedding)
    ).limit(limit).all()

    # 5. Format output
    scored_results = []
    for resume, score in results:
        scored_results.append({
            "resume_id": resume.id,
            "candidate_name": resume.name,
            "location": resume.location,
            "file_type": resume.file_type, # Added so you can verify the file type!
            "ai_accuracy_score": round(score, 2) 
        })

    return scored_results

def benchmark_vector_recall(
    db: Session, 
    search_query: str, 
    k: int = 10
) -> Dict:
    """
    Developer Utility: Calculates the true Recall by comparing IVFFlat (ANN) 
    against an Exact flat mathematical scan (k-NN).
    *Updated to mirror the Unified Hybrid Search pre-filtering.*
    """
    # clean_query = search_query.strip().lower()
    clean_query = search_query.strip().lower().replace(",", " ")
    
    # 2. Generate the AI vector using the perfectly clean string
    query_embedding = generate_embedding(clean_query)
    # query_embedding = generate_embedding(search_query)
    
    # --- Establish the Base Filtered Query ---
    # We must filter the data exactly like the recruiter search does
    # so we are comparing apples-to-apples in our benchmark.
    base_query = db.query(models.ResumeN.id).filter(
        models.ResumeN.is_latest == True,
        models.ResumeN.archived == False,
        text("tsv_content @@ websearch_to_tsquery('english', :q)")
    ).params(q=clean_query)

    # --- STEP A: Exact k-NN Search ---
    # Disable index usage in Postgres for this transaction to force a flat scan
    db.execute(text("SET LOCAL enable_indexscan = off;"))
    db.execute(text("SET LOCAL enable_bitmapscan = off;"))
    
    exact_results = base_query.order_by(
        models.ResumeN.embedding.cosine_distance(query_embedding)
    ).limit(k).all()
    # exact_ids = {res[0] for res in exact_results}
    # FIX: Use LIST COMPREHENSION (square brackets) to keep the strict AI order
    exact_list = [res[0] for res in exact_results]
    exact_set = set(exact_list) # Only used for the math below
    
    # --- STEP B: Approximate (ANN) Search ---
    # Re-enable indexes to use the IVFFlat pgvector index
    db.execute(text("SET LOCAL enable_indexscan = on;"))
    db.execute(text("SET LOCAL enable_bitmapscan = on;"))
    
    ann_results = base_query.order_by(
        models.ResumeN.embedding.cosine_distance(query_embedding)
    ).limit(k).all()
    # ann_ids = {res[0] for res in ann_results}
    # FIX: Use LIST COMPREHENSION (square brackets) to keep the strict AI order
    ann_list = [res[0] for res in ann_results]
    ann_set = set(ann_list) # Only used for the math below
    
    # --- STEP C: Calculate Recall ---
    matches = exact_set.intersection(ann_set)
    
    # Safety check: If the keyword filter returned fewer than K results, 
    # we adjust our math so recall isn't falsely deflated.
    actual_k = len(exact_list) 
    recall_percentage = (len(matches) / actual_k) * 100 if actual_k > 0 else 0.0
    
    return {
        "search_query": search_query,
        "k_requested": k,
        "actual_filtered_pool_size": actual_k,
        "exact_ids": exact_list,
        "ivfflat_ann_ids": ann_list,
        "true_recall_percentage": recall_percentage,
        "developer_note": f"The IVFFlat index successfully retrieved {len(matches)} out of the absolute true top {actual_k} closest vectors."
    }

# def benchmark_vector_recall(
#     db: Session, 
#     search_query: str, 
#     k: int = 10
# ) -> Dict:
#     """
#     Developer Utility: Calculates the true Recall by comparing IVFFlat (ANN) 
#     against an Exact flat mathematical scan (k-NN).
#     """
#     query_embedding = generate_embedding(search_query)
    
#     # --- STEP A: Exact k-NN Search ---
#     # Disable index usage in Postgres for this transaction to force a flat scan
#     db.execute(text("SET LOCAL enable_indexscan = off;"))
#     db.execute(text("SET LOCAL enable_bitmapscan = off;"))
    
#     exact_results = db.query(models.ResumeN.id).order_by(
#         models.ResumeN.embedding.cosine_distance(query_embedding)
#     ).limit(k).all()
#     exact_ids = {res[0] for res in exact_results}
    
#     # --- STEP B: Approximate (ANN) Search ---
#     # Re-enable indexes to use the IVFFlat pgvector index
#     db.execute(text("SET LOCAL enable_indexscan = on;"))
#     db.execute(text("SET LOCAL enable_bitmapscan = on;"))
    
#     ann_results = db.query(models.ResumeN.id).order_by(
#         models.ResumeN.embedding.cosine_distance(query_embedding)
#     ).limit(k).all()
#     ann_ids = {res[0] for res in ann_results}
    
#     # --- STEP C: Calculate Recall ---
#     matches = exact_ids.intersection(ann_ids)
#     recall_percentage = (len(matches) / k) * 100 if k > 0 else 0.0
    
#     return {
#         "search_query": search_query,
#         "k_requested": k,
#         "exact_ids": list(exact_ids),
#         "ivfflat_ann_ids": list(ann_ids),
#         "true_recall_percentage": recall_percentage,
#         "developer_note": f"The IVFFlat index successfully retrieved {len(matches)} out of the absolute true top {k} closest vectors. If recall is low, consider increasing 'ivfflat.probes' during querying or recreating the index with more 'lists'."
#     }