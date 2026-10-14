from datetime import date
from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import func, select

from app import models, schemas
from app.deps import DB, CurrentUser
from app.months import add_months, month_label, parse_month

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def month_total(db: DB, user: models.User, start: date) -> Decimal:
    total = db.scalar(
        select(func.sum(models.Expense.amount)).where(
            models.Expense.user_id == user.id,
            models.Expense.date >= start,
            models.Expense.date < add_months(start, 1),
        )
    )
    return total or Decimal(0)


@router.get("/summary", response_model=schemas.DashboardSummary)
def summary(db: DB, user: CurrentUser, month: str | None = None):
    """Spending for one month (default: the current month), by category, compared with the month before."""
    start = parse_month(month)
    rows = db.execute(
        select(models.Expense.category, func.sum(models.Expense.amount), func.count())
        .where(
            models.Expense.user_id == user.id,
            models.Expense.date >= start,
            models.Expense.date < add_months(start, 1),
        )
        .group_by(models.Expense.category)
        .order_by(func.sum(models.Expense.amount).desc(), models.Expense.category)
    ).all()
    return {
        "month": month_label(start),
        "total_spent": sum((total for _, total, _ in rows), Decimal(0)),
        "previous_month_total": month_total(db, user, add_months(start, -1)),
        "transaction_count": sum(count for _, _, count in rows),
        "by_category": [{"category": c, "total": t, "count": n} for c, t, n in rows],
    }
