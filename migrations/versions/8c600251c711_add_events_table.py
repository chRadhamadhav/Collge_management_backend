"""Add events table

Revision ID: 8c600251c711
Revises: 9e96477cb2d4
Create Date: 2026-03-05 17:47:05.347870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c600251c711'
down_revision: Union[str, None] = '9e96477cb2d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use postgresql ENUM creation safety
    from sqlalchemy.dialects.postgresql import ENUM
    event_type_enum = ENUM('Academic', 'Extracurricular', 'Holiday', 'Deadline', 'Admin', name='eventtype', create_type=False)
    event_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('event_time', sa.Time(), nullable=True),
        sa.Column('event_type', event_type_enum, nullable=False, server_default='Academic'),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('events')
    # Optionally drop the enum, but safer to keep it or drop if needed
    from sqlalchemy.dialects.postgresql import ENUM
    event_type_enum = ENUM('Academic', 'Extracurricular', 'Holiday', 'Deadline', 'Admin', name='eventtype', create_type=False)
    event_type_enum.drop(op.get_bind(), checkfirst=True)
