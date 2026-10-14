"""Baseline: the schema previously created by Base.metadata.create_all

Existing databases created before Alembic was introduced already have these
tables; mark them as migrated with `alembic stamp 0001` and then upgrade.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_expenses_id", "expenses", ["id"])

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
    )
    op.create_index("ix_budgets_id", "budgets", ["id"])
    op.create_index("ix_budgets_category", "budgets", ["category"])


def downgrade() -> None:
    op.drop_table("budgets")
    op.drop_table("expenses")
    op.drop_table("users")
