import sys
import os
from sqlalchemy import text

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine

def add_tables():
    with engine.connect() as conn:
        print("Creating user_permissions table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_permissions (
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
                    scope VARCHAR(20) NOT NULL DEFAULT 'OWN',
                    PRIMARY KEY (user_id, permission_id)
                )
            """))
            conn.commit()
            print("Done!")
        except Exception as e:
            print(f"Error creating user_permissions: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_tables()
