"""
Script to seed the initial Super Admin account.
"""
import os
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app import models, security, database

# Load .env file
load_dotenv()

def seed_superadmin():
    # Load settings from .env
    email = os.getenv("SUPER_ADMIN_EMAIL")
    password = os.getenv("SUPER_ADMIN_PASSWORD")
    full_name = os.getenv("SUPER_ADMIN_NAME", "System Super Admin")
    
    if not email or not password:
        print("ERROR: SUPER_ADMIN_EMAIL or SUPER_ADMIN_PASSWORD not set in .env")
        return

    db = next(database.get_db())
    
    # Check if exists
    existing = db.query(models.User).filter(models.User.email == email).first()
    
    # Get the Super Admin role object to get the ID
    super_admin_role = db.query(models.Role).filter(models.Role.name == "Super Admin").first()
    if not super_admin_role:
        print("ERROR: 'Super Admin' role not found in database. Run seed_rbac.py first.")
        return

    if existing:
        print(f"User {email} already exists. Updating role_id if necessary.")
        existing.role_id = super_admin_role.id
        existing.role = "super_admin" # Maintain backward compatibility
        db.commit()
        return
    
    # Create Super Admin
    new_user = models.User(
        email=email,
        hashed_password=security.get_password_hash(password),
        full_name=full_name,
        role="super_admin",
        role_id=super_admin_role.id,
        is_active=True,
        status="ACTIVE",
        auth_provider="email"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    print(f"Successfully created Super Admin: {email}")

if __name__ == "__main__":
    seed_rbac_path = os.path.join(os.path.dirname(__file__), "seed_rbac.py")
    # Note: Ensure seed_rbac.py has been run already or is called here
    seed_superadmin()
