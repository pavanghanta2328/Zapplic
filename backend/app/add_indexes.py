import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine

def add_search_indexes():
    """Add indexes to improve search performance"""
    
    with engine.connect() as conn:
        print("Adding indexes for better search performance...")
        
        try:
            # GIN indexes for full-text search on text fields
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_resumes_skills_gin 
                ON resumes USING gin(to_tsvector('english', COALESCE(skills, '')));
            """)
            print("✅ Added index on skills")
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_resumes_experience_gin 
                ON resumes USING gin(to_tsvector('english', COALESCE(experience, '')));
            """)
            print("✅ Added index on experience")
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_resumes_education_gin 
                ON resumes USING gin(to_tsvector('english', COALESCE(education, '')));
            """)
            print("✅ Added index on education")
            
            # Regular indexes for exact match fields
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_resumes_name 
                ON resumes(name);
            """)
            print("✅ Added index on name")
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_resumes_email 
                ON resumes(email);
            """)
            print("✅ Added index on email")
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_resumes_location 
                ON resumes(location);
            """)
            print("✅ Added index on location")
            
            conn.commit()
            print("\n🎉 All indexes created successfully!")
            print("Search performance is now optimized for thousands of resumes.")
            
        except Exception as e:
            print(f"Error creating indexes: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_search_indexes()