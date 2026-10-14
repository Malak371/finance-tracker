from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app import models, schemas
from app.deps import DB, CurrentUser
from app.months import add_months, month_label, parse_month

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def month_total(db: DB, user: models.User, start: date, through_day: int | None = None) -> Decimal:
    """Spending in the month starting at `start`, optionally only up to day `through_day`."""
    end = add_months(start, 1)
    if through_day is not None:
        end = min(end, start + timedelta(days=through_day))
    total = db.scalar(
        select(func.sum(models.Expense.amount)).where(
            models.Expense.user_id == user.id,
            models.Expense.date >= start,
            models.Expense.date < end,
        )
    )
    return total or Decimal(0)


@router.get("/summary", response_model=schemas.DashboardSummary)
def summary(db: DB, user: CurrentUser, month: str | None = None):
    """Spending for one month (default: the current month), by category, compared with the month before.

    For the month in progress the comparison is with the same point last month (month to date);
    comparing half a month with a whole one would always look like a saving.
    """
    start = parse_month(month)
    today = date.today()
    in_progress = (start.year, start.month) == (today.year, today.month)
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
        "previous_month_total": month_total(
            db, user, add_months(start, -1), through_day=today.day if in_progress else None
        ),
        "comparison": "month_to_date" if in_progress else "full_month",
        "transaction_count": sum(count for _, _, count in rows),
        "by_category": [{"category": c, "total": t, "count": n} for c, t, n in rows],
    }


@router.get("/trends", response_model=list[schemas.MonthTotal])
def monthly_trends(
    db: DB,
    user: CurrentUser,
    month: str | None = None,
    months: int = Query(default=12, ge=1, le=36),
    category: str | None = None,
):
    """Total spent per month for the `months` months ending with `month`, oldest first.

    Months with no spending are included as zero so the series has no gaps.
    """
    end = parse_month(month)
    start = add_months(end, -(months - 1))
    month_start = func.date_trunc("month", models.Expense.date)
    query = (
        select(month_start, func.sum(models.Expense.amount))
        .where(
            models.Expense.user_id == user.id,
            models.Expense.date >= start,
            models.Expense.date < add_months(end, 1),
        )
        .group_by(month_start)
    )
    if category:
        query = query.where(func.lower(models.Expense.category) == category.lower())
    totals = {month_label(row_month.date()): total for row_month, total in db.execute(query)}
    labels = [month_label(add_months(start, i)) for i in range(months)]
    return [{"month": label, "total": totals.get(label, Decimal(0))} for label in labels]
