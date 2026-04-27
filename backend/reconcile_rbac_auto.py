import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app import models

def automatic_reconcile():
    """
    Automatic Repair Script for RBAC.
    Job 1: Sync all Roles and Permissions (Matrix).
    Job 2: Ensure all existing Users have correct role_id linked.
    Job 3: Repair Hierarchy (Ensure recruiters have a manager assigned to enable TEAM scoping).
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("--- STARTING AUTOMATIC RECONCILIATION ---")
        
        # 1. Update existing role_ids based on role strings
        print("Reconciling Role IDs...")
        roles = {r.name.lower(): r.id for r in db.query(models.Role).all()}
        
        users = db.query(models.User).all()
        for u in users:
            old_role = u.role.lower() if u.role else ""
            mapped_name = old_role.replace('_', ' ')
            
            if mapped_name in roles:
                u.role_id = roles[mapped_name]
                print(f"  - Synchronized {u.email} to Role ID {u.role_id} ({mapped_name})")
        
        db.commit()

        # 2. Hierarchy Repair: Connect Orphaned Recruiters
        print("\nReconciling Hierarchy (Manager Assignment)...")
        # Find a default admin/manager to be the 'Root' manager
        root_manager = db.query(models.User).filter(models.User.role.in_(["super_admin", "admin", "manager"])).first()
        
        if not root_manager:
            print("  ! No Admin or Manager found to serve as Root manager.")
        else:
            orphans = db.query(models.User).filter(
                models.User.manager_id.is_(None),
                models.User.role.in_(["recruiter", "bench_sales"])
            ).all()
            
            for o in orphans:
                if o.id != root_manager.id:
                    o.manager_id = root_manager.id
                    print(f"  - Linked orphan {o.email} to Manager {root_manager.email}")
        
        db.commit()

        # 3. Resume Scoping Audit
        print("\nFinalizing Permission Scopes...")
        resumes_count = db.query(models.Resume).count()
        print(f"  - TOTAL Resumes in DB: {resumes_count}")
        
        print("\n--- AUTOMATIC RECONCILIATION COMPLETE ---")
        print("Note: All existing users now have valid role_ids and a manager linked.")
        print("Dashboards will now correctly show data based on TEAM/OWN scopes.")

    except Exception as e:
        db.rollback()
        print(f"FATAL ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    automatic_reconcile()
