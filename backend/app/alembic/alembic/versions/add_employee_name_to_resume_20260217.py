"""add employee_name to resumes

Revision ID: addempname20260217
Revises: def123456789
Create Date: 2026-02-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'addempname20260217'
down_revision: Union[str, Sequence[str], None] = 'def123456789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('resumes', sa.Column('employee_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('resumes', 'employee_name')
