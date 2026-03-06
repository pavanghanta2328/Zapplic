"""Add recruiter tracking to resumes (uploaded_by_recruiter_id)

Revision ID: add_recruiter_tracking_to_resumes
Revises: addempname20260217, add_employee_name_to_resumes
Create Date: 2026-02-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_recruiter_tracking_to_resumes'
down_revision = ('addempname20260217', 'add_employee_name_to_resumes')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add foreign key column to track which recruiter uploaded the resume
    op.add_column('resumes', sa.Column('uploaded_by_recruiter_id', sa.Integer(), nullable=True))
    op.create_index('ix_resumes_uploaded_by_recruiter_id', 'resumes', ['uploaded_by_recruiter_id'])
    op.create_foreign_key(
        'fk_resumes_recruiter',
        'resumes',
        'recruiters',
        ['uploaded_by_recruiter_id'],
        ['id']
    )


def downgrade() -> None:
    # Remove the foreign key and column if downgrading
    op.drop_constraint('fk_resumes_recruiter', 'resumes', type_='foreignkey')
    op.drop_index('ix_resumes_uploaded_by_recruiter_id', 'resumes')
    op.drop_column('resumes', 'uploaded_by_recruiter_id')
