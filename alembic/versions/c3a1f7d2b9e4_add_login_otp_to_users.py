"""add login otp to users

Revision ID: c3a1f7d2b9e4
Revises: b68c9e2953a4
Create Date: 2026-10-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3a1f7d2b9e4'
down_revision: Union[str, None] = 'b68c9e2953a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('otp_code_hash', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('otp_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('otp_attempts', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'otp_attempts')
    op.drop_column('users', 'otp_expires_at')
    op.drop_column('users', 'otp_code_hash')
