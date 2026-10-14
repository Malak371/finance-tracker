"""Categorisation: user keyword rules and where each expense's category came from

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "expenses",
        sa.Column("category_source", sa.String(20), server_default="manual", nullable=False),
    )
    op.create_table(
        "category_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keyword", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "keyword", name="uq_category_rules_user_keyword"),
    )
    op.create_index("ix_category_rules_user_id", "category_rules", ["user_id"])


def downgrade() -> None:
    op.drop_table("category_rules")
    op.drop_column("expenses", "category_source")
