import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, engine, get_db
from app import models

# Sync the database (Drop and Create specific tables to ensure sync)
print("Syncing Roles and Permissions tables...")
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS role_permissions CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS permissions CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS roles CASCADE"))
    conn.commit()

Base.metadata.create_all(bind=engine, tables=[
    models.Role.__table__, 
    models.Permission.__table__, 
    models.RolePermission.__table__
])

def seed_rbac():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        # 1. Define Permissions
        permissions_data = [
            ("job:create", "Create Job"),
            ("job:view", "View Job"),
            ("job:update", "Update Job"),
            ("job:delete", "Delete Job"),
            ("job:assign_user", "Assign User to Job"),
            ("submission:create", "Create Submission"),
            ("submission:review", "Review Submission"),
            ("bench:create", "Create Bench Record"),
            ("bench:view", "View Bench Record"),
            ("bench:generate_hotlist", "Generate Hotlist"),
            ("bench:mass_mail", "Mass Mail Bench Candidates"),
            ("candidate:create", "Create Candidate"),
            ("candidate:view", "View Candidate"),
            ("user:invite", "Invite User"),
        ]

        print("Seeding Permissions...")
        permission_map = {}
        for slug, name in permissions_data:
            perm = db.query(models.Permission).filter_by(slug=slug).first()
            if not perm:
                perm = models.Permission(slug=slug, name=name)
                db.add(perm)
                db.flush()
            permission_map[slug] = perm

        # 2. Define Roles
        roles_data = [
            "Super Admin",
            "Admin",
            "Manager",
            "Recruiter",
            "Bench Sales"
        ]

        print("Seeding Roles...")
        role_map = {}
        for name in roles_data:
            role = db.query(models.Role).filter_by(name=name).first()
            if not role:
                role = models.Role(name=name)
                db.add(role)
                db.flush()
            role_map[name] = role

        # 3. Define the Matrix (Permission, Role, Scope)
        # Matrix: { PermissionSlug: { RoleName: Scope } }
        matrix = {
            "job:create": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM", "Recruiter": "OWN"
            },
            "job:view": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM", "Recruiter": "OWN", "Bench Sales": "TEAM"
            },
            "job:update": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM", "Recruiter": "OWN"
            },
            "job:delete": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM"
            },
            "job:assign_user": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM"
            },
            "submission:create": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM", "Recruiter": "OWN", "Bench Sales": "OWN"
            },
            "submission:review": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM"
            },
            "bench:create": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM", "Bench Sales": "OWN"
            },
            "bench:view": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM", "Bench Sales": "OWN"
            },
            "bench:generate_hotlist": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM", "Bench Sales": "OWN"
            },
            "bench:mass_mail": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Bench Sales": "OWN"
            },
            "candidate:create": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM", "Recruiter": "OWN"
            },
            "candidate:view": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM", "Recruiter": "OWN", "Bench Sales": "OWN"
            },
            "user:invite": {
                "Super Admin": "ALL", "Admin": "COMPANY", "Manager": "TEAM"
            }
        }

        print("Linking Roles and Permissions with Scopes...")
        for slug, role_scopes in matrix.items():
            perm = permission_map.get(slug)
            if not perm: continue
            
            for role_name, scope in role_scopes.items():
                role = role_map.get(role_name)
                if not role: continue
                
                # Check if link exists
                rp = db.query(models.RolePermission).filter_by(
                    role_id=role.id, 
                    permission_id=perm.id
                ).first()
                
                if not rp:
                    rp = models.RolePermission(
                        role_id=role.id,
                        permission_id=perm.id,
                        scope=scope
                    )
                    db.add(rp)
                else:
                    rp.scope = scope # Update if already exists

        db.commit()
        print("DONE: RBAC Matrix successfully seeded!")

        # 4. Optional: Assign existing users to their respective role objects
        print("Checking for existing users and assigning role_ids...")
        users = db.query(models.User).all()
        for user in users:
            # Map string role to role object
            role_name_map = {
                "super_admin": "Super Admin",
                "admin": "Admin",
                "manager": "Manager",
                "recruiter": "Recruiter",
                "bench_sales": "Bench Sales"
            }
            mapped_name = role_name_map.get(user.role.lower() if user.role else "")
            if mapped_name and mapped_name in role_map:
                user.role_id = role_map[mapped_name].id
        
        db.commit()
        print("DONE: Users updated with role_id!")

    except Exception as e:
        db.rollback()
        print(f"ERROR seeding RBAC: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_rbac()
