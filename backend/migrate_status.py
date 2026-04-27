import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USERNAME")
DB_PASS = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_DATABASE")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Checking for existing 'status' column in 'users' table...")
        # Check if the column exists
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='status'")).fetchone()
        
        if not res:
            print("Adding 'status' column to 'users' table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE'"))
            # Update current users to 'ACTIVE' by default so they can log in
            conn.execute(text("UPDATE users SET status = 'ACTIVE' WHERE status IS NULL"))
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column 'status' already exists.")
            
        print("Ensuring all users have at least 'ACTIVE' status...")
        conn.execute(text("UPDATE users SET status = 'ACTIVE' WHERE status IS NULL"))
        conn.commit()
        print("Migration complete.")
except Exception as e:
    print(f"Error: {e}")
