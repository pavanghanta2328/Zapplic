from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func, Computed, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
from .database import Base

# ======================================================
# PARTITIONED RESUME MODEL
# ======================================================
class ResumeN(Base):
    """
    Partitioned Resume Model (resumes_n)
    Partitioned by: LIST (location)
    """
    __tablename__ = "resumes_n"

    # In PostgreSQL partitioning, the partition key (location) must be part of the primary key.
    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(Text, primary_key=True, nullable=False)

    # File information
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_hash = Column(String(64), nullable=False) 

    # Searchable fields
    name = Column(String(255), index=True)
    email = Column(String(255), index=True)
    mobile_number = Column(String(50))
    employee_name = Column(String(255), index=True,nullable=True)

    # Content & Vectors
    parsed_data = Column(JSONB, nullable=True)
    search_text = Column(Text, nullable=True)
    resume_text = Column(Text, nullable=True)
    embedding = Column(Vector(384), nullable=True)

    # Metadata
    is_edited = Column(Boolean, default=False)
    parsing_quality = Column(String(20), default="unknown")
    extraction_method = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    upload_timestamp = Column(DateTime, server_default=func.now())
    
    # Version Management
    version = Column(Integer, default=1, nullable=False)
    is_latest = Column(Boolean, default=True, nullable=False)
    archived = Column(Boolean, default=False, nullable=False)
    previous_version_id = Column(Integer, nullable=True)
    
    #Personal & social details
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    personal_details = Column(JSONB, nullable=True)

    # Generated Full-Text Search Column
    tsv_content = Column(
        TSVECTOR, 
        Computed("to_tsvector('english', COALESCE(search_text, ''))", persisted=True)
    )

    __table_args__ = (
        Index("idx_resn_parsed_gin", "parsed_data", postgresql_using="gin"),
        Index("idx_resn_tsv_gin", "tsv_content", postgresql_using="gin"),
        Index("idx_resn_email", "email"),
        Index("idx_resn_name", "name"),
        Index("idx_resn_hash", "file_hash"),
        Index("idx_resn_vec", "embedding", 
              postgresql_using="ivfflat", 
              postgresql_with={"lists": "100"},
              postgresql_ops={"embedding": "vector_cosine_ops"}),
        {
            "postgresql_partition_by": "LIST (location)",
        }
    )

    def __repr__(self):
        return f"<ResumeN {self.email or self.name}>"


# ======================================================
# RECRUITER MODEL
# ======================================================
class Recruiter(Base):
    __tablename__ = "recruiters"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    experience = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="recruiter")
    auth_provider = Column(String, default="email")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    refresh_tokens = relationship("RefreshToken", back_populates="user")


# ======================================================
# AUTHENTICATION TOKENS
# ======================================================
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("recruiters.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_revoked = Column(Boolean, default=False)

    user = relationship("Recruiter", back_populates="refresh_tokens")