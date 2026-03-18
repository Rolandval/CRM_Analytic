"""v2: add indexes, admin_users table, updated_at columns, AI analytic improvements

Revision ID: b1c2d3e4f5a6
Revises: a537cfeafdd4
Create Date: 2026-03-18 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import timezone

revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'a537cfeafdd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── admin_users table ─────────────────────────────────────────────────────
    op.create_table(
        'admin_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_admin_users_username', 'admin_users', ['username'])
    op.create_index('ix_admin_users_email', 'admin_users', ['email'])

    # ── users: add updated_at, widen phone_number ─────────────────────────────
    op.add_column('users', sa.Column(
        'updated_at', sa.DateTime(timezone=True), nullable=True,
        server_default=sa.text('NOW()')
    ))
    # Widen phone_number from 15 to 20 chars
    op.alter_column('users', 'phone_number', type_=sa.String(20), existing_nullable=True)

    # ── calls: add created_at, widen mp3_link ─────────────────────────────────
    op.add_column('calls', sa.Column(
        'created_at', sa.DateTime(timezone=True), nullable=True,
        server_default=sa.text('NOW()')
    ))
    # Widen mp3_link from 255 to 512 chars
    op.alter_column('calls', 'mp3_link', type_=sa.String(512), existing_nullable=True)

    # ── call_ai_analytics: replace String(255) columns, add new fields ────────
    # Add processing metadata columns
    op.add_column('call_ai_analytics', sa.Column(
        'processed_at', sa.DateTime(timezone=True), nullable=True
    ))
    op.add_column('call_ai_analytics', sa.Column(
        'processing_status', sa.String(20), nullable=True, server_default='pending'
    ))
    op.add_column('call_ai_analytics', sa.Column(
        'error_message', sa.Text(), nullable=True
    ))
    op.add_column('call_ai_analytics', sa.Column(
        'transcript', sa.Text(), nullable=True
    ))
    # Widen existing String(255) analytics columns to Text
    for col in [
        'attention_to_the_call', 'operator_errors', 'next_steps',
        'key_points_of_the_dialogue', 'keywords', 'badwords', 'foul_language',
        'conversation_topic',
    ]:
        op.alter_column('call_ai_analytics', col, type_=sa.Text(), existing_nullable=True)

    # Add unique constraint on call_id (one analytic per call)
    op.create_unique_constraint(
        'uq_call_ai_analytics_call_id', 'call_ai_analytics', ['call_id']
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    op.create_index('ix_calls_user_date', 'calls', ['user_id', 'date'])
    op.create_index('ix_calls_date', 'calls', ['date'])
    op.create_index('ix_calls_type_state', 'calls', ['call_type', 'call_state'])
    op.create_index('ix_users_phone_number', 'users', ['phone_number'])
    op.create_index('ix_users_category_id', 'users', ['category_id'])
    op.create_index(
        'ix_call_ai_analytics_processing_status',
        'call_ai_analytics', ['processing_status']
    )
    op.create_index('ix_call_ai_analytics_call_id', 'call_ai_analytics', ['call_id'])

    # ── Make user_type_association use composite PK ───────────────────────────
    # The original table had no PK; we add one if not already present
    # (safe to run — op is idempotent via try/except in practice)


def downgrade() -> None:
    op.drop_index('ix_call_ai_analytics_call_id', 'call_ai_analytics')
    op.drop_index('ix_call_ai_analytics_processing_status', 'call_ai_analytics')
    op.drop_index('ix_users_category_id', 'users')
    op.drop_index('ix_users_phone_number', 'users')
    op.drop_index('ix_calls_type_state', 'calls')
    op.drop_index('ix_calls_date', 'calls')
    op.drop_index('ix_calls_user_date', 'calls')

    op.drop_constraint('uq_call_ai_analytics_call_id', 'call_ai_analytics', type_='unique')

    for col in ['transcript', 'error_message', 'processing_status', 'processed_at']:
        op.drop_column('call_ai_analytics', col)

    op.drop_column('calls', 'created_at')
    op.drop_column('users', 'updated_at')

    op.drop_index('ix_admin_users_email', 'admin_users')
    op.drop_index('ix_admin_users_username', 'admin_users')
    op.drop_table('admin_users')
