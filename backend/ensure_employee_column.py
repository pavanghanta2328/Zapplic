#!/usr/bin/env python
import sys
import os
from sqlalchemy import text, inspect

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base

def ensure_employee_name_column():
    """Ensure employee_name column exists in resumes table"""
    
    # Get inspector to check existing columns
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('resumes')]
    
    if 'employee_name' not in columns:
        print("❌ employee_name column not found. Adding it now...")
        with engine.connect() as connection:
            connection.execute(text('''
                ALTER TABLE resumes 
                ADD COLUMN employee_name VARCHAR(255) NULL
            '''))
            connection.execute(text('''
                CREATE INDEX idx_resumes_employee_name ON resumes(employee_name)
            '''))
            connection.commit()
        print("✅ employee_name column added successfully!")
    else:
        print("✅ employee_name column already exists!")

if __name__ == "__main__":
    try:
        ensure_employee_name_column()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
