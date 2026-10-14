"""Store money as decimals and tighten constraints

- amount columns: double precision -> numeric(12, 2)
- user_id NOT NULL with ON DELETE CASCADE (rows without an owner were unreachable through the API)
- one budget per (user, category)
- bounded string lengths, created_at timestamps, indexes for per-user queries

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

MONEY = sa.Numeric(12, 2)


def upgrade() -> None:
    op.execute("DELETE FROM expenses WHERE user_id IS NULL")
    op.execute("DELETE FROM budgets WHERE user_id IS NULL OR category IS NULL OR amount IS NULL")
    # Keep the lowest id if duplicate budgets for the same category ever slipped in.
    op.execute(
        "DELETE FROM budgets b USING budgets other "
        "WHERE b.user_id = other.user_id AND b.category = other.category AND b.id > other.id"
    )

    # users
    op.drop_index("ix_users_id", table_name="users")
    op.alter_column("users", "email", type_=sa.String(254))
    op.alter_column("users", "hashed_password", type_=sa.String(100))
    op.add_column(
        "users",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # expenses
    op.drop_index("ix_expenses_id", table_name="expenses")
    op.alter_column("expenses", "amount", type_=MONEY, postgresql_using="round(amount::numeric, 2)")
    op.alter_column("expenses", "category", type_=sa.String(50), postgresql_using="left(category, 50)")
    op.alter_column("expenses", "description", type_=sa.String(255), postgresql_using="left(description, 255)")
    op.alter_column("expenses", "user_id", nullable=False)
    op.drop_constraint("expenses_user_id_fkey", "expenses", type_="foreignkey")
    op.create_foreign_key(
        "expenses_user_id_fkey", "expenses", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.add_column(
        "expenses",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_expenses_user_id", "expenses", ["user_id"])
    op.create_index("ix_expenses_date", "expenses", ["date"])

    # budgets
    op.drop_index("ix_budgets_id", table_name="budgets")
    op.drop_index("ix_budgets_category", table_name="budgets")
    op.alter_column("budgets", "amount", type_=MONEY, nullable=False, postgresql_using="round(amount::numeric, 2)")
    op.alter_column(
        "budgets", "category", type_=sa.String(50), nullable=False, postgresql_using="left(category, 50)"
    )
    op.alter_column("budgets", "user_id", nullable=False)
    op.drop_constraint("budgets_user_id_fkey", "budgets", type_="foreignkey")
    op.create_foreign_key("budgets_user_id_fkey", "budgets", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"])
    op.create_unique_constraint("uq_budgets_user_category", "budgets", ["user_id", "category"])


def downgrade() -> None:
    op.drop_constraint("uq_budgets_user_category", "budgets", type_="unique")
    op.drop_index("ix_budgets_user_id", table_name="budgets")
    op.drop_constraint("budgets_user_id_fkey", "budgets", type_="foreignkey")
    op.create_foreign_key("budgets_user_id_fkey", "budgets", "users", ["user_id"], ["id"])
    op.alter_column("budgets", "user_id", nullable=True)
    op.alter_column("budgets", "category", type_=sa.String(), nullable=True)
    op.alter_column("budgets", "amount", type_=sa.Float(), nullable=True)
    op.create_index("ix_budgets_category", "budgets", ["category"])
    op.create_index("ix_budgets_id", "budgets", ["id"])

    op.drop_index("ix_expenses_date", table_name="expenses")
    op.drop_index("ix_expenses_user_id", table_name="expenses")
    op.drop_column("expenses", "created_at")
    op.drop_constraint("expenses_user_id_fkey", "expenses", type_="foreignkey")
    op.create_foreign_key("expenses_user_id_fkey", "expenses", "users", ["user_id"], ["id"])
    op.alter_column("expenses", "user_id", nullable=True)
    op.alter_column("expenses", "description", type_=sa.String())
    op.alter_column("expenses", "category", type_=sa.String())
    op.alter_column("expenses", "amount", type_=sa.Float())
    op.create_index("ix_expenses_id", "expenses", ["id"])

    op.drop_column("users", "created_at")
    op.alter_column("users", "hashed_password", type_=sa.String())
    op.alter_column("users", "email", type_=sa.String())
    op.create_index("ix_users_id", "users", ["id"])
