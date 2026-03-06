"""Add employee_name column to resumes table

Revision ID: add_employee_name_to_resumes
Revises: add_recruiter_profile_fields
Create Date: 2026-02-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_employee_name_to_resumes'
down_revision = 'add_recruiter_profile_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add employee_name column to resumes table if it doesn't exist
    try:
        op.add_column('resumes', sa.Column('employee_name', sa.String(255), nullable=True, index=True))
    except Exception:
        # Column might already exist
        pass


def downgrade() -> None:
    # Remove employee_name column
    try:
        op.drop_column('resumes', 'employee_name')
    except Exception:
        pass
