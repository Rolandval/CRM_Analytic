"""mood fields TEXT, quality scores VARCHAR(30)

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-03-19

Changes:
  - call_ai_analytics.clients_mood:      VARCHAR(50)  → TEXT
  - call_ai_analytics.operators_mood:    VARCHAR(50)  → TEXT
  - call_ai_analytics.customer_satisfaction: VARCHAR(50) → TEXT
  - call_ai_analytics.problem_solving_efficiency: VARCHAR(20) → VARCHAR(30)
  - call_ai_analytics.ability_to_adapt:  VARCHAR(20)  → VARCHAR(30)
  - call_ai_analytics.involvement:       VARCHAR(20)  → VARCHAR(30)
  - call_ai_analytics.problem_identification: VARCHAR(20) → VARCHAR(30)
  - call_ai_analytics.clarity_of_communication: VARCHAR(20) → VARCHAR(30)
  - call_ai_analytics.empathy:           VARCHAR(20)  → VARCHAR(30)
  - call_ai_analytics.operator_professionalism: VARCHAR(20) → VARCHAR(30)

Reason: Unitalk voice analytics returns full-sentence descriptions for mood fields,
not short labels. Quality scores are numeric strings (e.g. "7.4462") — VARCHAR(30)
is sufficient but VARCHAR(20) was too short for edge cases.
"""
from alembic import op
import sqlalchemy as sa


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None

TABLE = "call_ai_analytics"


def upgrade() -> None:
    # ── Mood fields: VARCHAR(50) → TEXT ───────────────────────────────────────
    for col in ("clients_mood", "operators_mood", "customer_satisfaction"):
        op.alter_column(
            TABLE,
            col,
            existing_type=sa.String(50),
            type_=sa.Text(),
            existing_nullable=True,
        )

    # ── Quality scores: VARCHAR(20) → VARCHAR(30) ─────────────────────────────
    for col in (
        "problem_solving_efficiency",
        "ability_to_adapt",
        "involvement",
        "problem_identification",
        "clarity_of_communication",
        "empathy",
        "operator_professionalism",
    ):
        op.alter_column(
            TABLE,
            col,
            existing_type=sa.String(20),
            type_=sa.String(30),
            existing_nullable=True,
        )


def downgrade() -> None:
    for col in ("clients_mood", "operators_mood", "customer_satisfaction"):
        op.alter_column(
            TABLE,
            col,
            existing_type=sa.Text(),
            type_=sa.String(50),
            existing_nullable=True,
        )

    for col in (
        "problem_solving_efficiency",
        "ability_to_adapt",
        "involvement",
        "problem_identification",
        "clarity_of_communication",
        "empathy",
        "operator_professionalism",
    ):
        op.alter_column(
            TABLE,
            col,
            existing_type=sa.String(30),
            type_=sa.String(20),
            existing_nullable=True,
        )
