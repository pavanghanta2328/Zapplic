"""Add recruiter profile fields (phone, experience, age)

Revision ID: add_recruiter_profile_fields
Revises: def123456789
Create Date: 2026-02-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_recruiter_profile_fields'
down_revision = 'def123456789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to recruiters table
    try:
        op.add_column('recruiters', sa.Column('phone_number', sa.String(), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('recruiters', sa.Column('experience', sa.String(), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('recruiters', sa.Column('age', sa.Integer(), nullable=True))
    except Exception:
        pass


def downgrade() -> None:
    # Remove columns if downgrading
    try:
        op.drop_column('recruiters', 'age')
    except Exception:
        pass
    
    try:
        op.drop_column('recruiters', 'experience')
    except Exception:
        pass
    
    try:
        op.drop_column('recruiters', 'phone_number')
    except Exception:
        pass
