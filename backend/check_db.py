import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USERNAME")
DB_PASS = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_DATABASE")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

try:
    columns = [col['name'] for col in inspector.get_columns('users')]
    print(f"Columns in 'users' table: {columns}")
    
    if 'status' in columns:
        print("✅ SUCCESS: 'status' column exists.")
    else:
        print("❌ FAILURE: 'status' column is MISSING.")
except Exception as e:
    print(f"Error: {e}")
