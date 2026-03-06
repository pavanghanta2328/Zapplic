import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import text

def migrate_database():
    """
    Migrate database to new schema with JSONB support.
    WARNING: This will drop existing data!
    """
    
    print("⚠️  WARNING: This will delete all existing resume data!")
    confirm = input("Type 'YES' to continue: ")
    
    if confirm != "YES":
        print("Migration cancelled.")
        return
    
    with engine.connect() as conn:
        try:
            print("\n🔄 Starting migration...")
            
            # Drop existing table
            print("Dropping old 'resumes' table...")
            conn.execute(text("DROP TABLE IF EXISTS resumes CASCADE;"))
            conn.commit()
            print("✅ Old table dropped")
            
            # Create new table with JSONB
            print("Creating new 'resumes' table with JSONB support...")
            conn.execute(text("""
                CREATE TABLE resumes (
                    id SERIAL PRIMARY KEY,
                    
                    -- File information
                    original_filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_type VARCHAR(10) NOT NULL,
                    
                    -- Key searchable fields
                    name VARCHAR(255),
                    email VARCHAR(255),
                    mobile_number VARCHAR(50),
                    location VARCHAR(255),
                    
                    -- Complete parsed data as JSON
                    parsed_data JSONB,
                    
                    -- Search-optimized text
                    search_text TEXT,
                    
                    -- Metadata
                    is_edited BOOLEAN DEFAULT FALSE,
                    parsing_quality VARCHAR(20) DEFAULT 'unknown',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE
                );
            """))
            conn.commit()
            print("✅ New table created")
            
            # Create indexes
            print("Creating indexes...")
            
            conn.execute(text("CREATE INDEX idx_resumes_id ON resumes(id);"))
            conn.execute(text("CREATE INDEX idx_resumes_name ON resumes(name);"))
            conn.execute(text("CREATE INDEX idx_resumes_email ON resumes(email);"))
            conn.execute(text("CREATE INDEX idx_resumes_location ON resumes(location);"))
            
            # GIN index for JSONB search
            conn.execute(text("CREATE INDEX idx_resumes_parsed_data_gin ON resumes USING gin(parsed_data);"))
            
            # Full-text search index
            conn.execute(text("""
                CREATE INDEX idx_resumes_search_text_gin 
                ON resumes USING gin(to_tsvector('english', COALESCE(search_text, '')));
            """))
            
            conn.commit()
            print("✅ Indexes created")
            
            print("\n🎉 Migration completed successfully!")
            print("\nNew schema supports:")
            print("  ✅ Complete resume data in JSONB format")
            print("  ✅ Fast search with indexes")
            print("  ✅ Flexible structure for any resume format")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate_database()