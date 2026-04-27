import sys
import os
from sqlalchemy import text

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine

def add_columns():
    with engine.connect() as conn:
        print("Adding manager_id to users...")
        try:
            # Check if column exists first
            res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='manager_id'"))
            if not res.fetchone():
                conn.execute(text("ALTER TABLE users ADD COLUMN manager_id INTEGER REFERENCES users(id)"))
                conn.commit()
                print("Done!")
            else:
                print("manager_id already exists.")
        except Exception as e:
            print(f"Error adding manager_id: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_columns()
