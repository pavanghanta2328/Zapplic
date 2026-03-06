#!/usr/bin/env python3
"""Add uploaded_by_recruiter_id column directly to database"""

from app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='resumes' AND column_name='uploaded_by_recruiter_id'
        """))
        
        if not result.fetchone():
            print('Adding uploaded_by_recruiter_id column...')
            
            # Add column
            conn.execute(text('''
                ALTER TABLE resumes ADD COLUMN uploaded_by_recruiter_id INTEGER
            '''))
            print('  ✓ Column added')
            
            # Create index
            conn.execute(text('''
                CREATE INDEX ix_resumes_uploaded_by_recruiter_id ON resumes(uploaded_by_recruiter_id)
            '''))
            print('  ✓ Index created')
            
            # Add foreign key
            conn.execute(text('''
                ALTER TABLE resumes ADD CONSTRAINT fk_resumes_recruiter 
                FOREIGN KEY (uploaded_by_recruiter_id) REFERENCES recruiters(id)
            '''))
            print('  ✓ Foreign key added')
            
            conn.commit()
            print('\n✅ Column added successfully!')
        else:
            print('✅ Column already exists')
            
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
