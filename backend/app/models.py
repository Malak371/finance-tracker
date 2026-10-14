from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Money is stored as exact decimals; floats accumulate rounding errors when summed.
Money = Numeric(12, 2)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    expenses: Mapped[list["Expense"]] = relationship(back_populates="owner", passive_deletes=True)
    budgets: Mapped[list["Budget"]] = relationship(back_populates="owner", passive_deletes=True)
    rules: Mapped[list["CategoryRule"]] = relationship(back_populates="owner", passive_deletes=True)


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[Decimal] = mapped_column(Money)
    category: Mapped[str] = mapped_column(String(50))
    date: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    # Where the category came from: "manual" (chosen by the user), "file" (bank export),
    # "rule", "model" or "default" (auto-categorised), or "none" (Uncategorized).
    category_source: Mapped[str] = mapped_column(String(20), server_default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="expenses")


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("user_id", "category", name="uq_budgets_user_category"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(50))
    # Monthly limit for the category.
    amount: Mapped[Decimal] = mapped_column(Money)

    owner: Mapped[User] = relationship(back_populates="budgets")


class CategoryRule(Base):
    """A user's own keyword rule: descriptions containing `keyword` go to `category`."""

    __tablename__ = "category_rules"
    __table_args__ = (UniqueConstraint("user_id", "keyword", name="uq_category_rules_user_keyword"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # Stored normalised (lowercase, single spaces) so matching and uniqueness ignore case.
    keyword: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="rules")
