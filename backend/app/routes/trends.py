from datetime import date, timedelta

from fastapi import APIRouter
from sqlalchemy import func, select

from app import models
from app.deps import DB, CurrentUser

router = APIRouter(prefix="/expenses/trends", tags=["trends"])


def _daily_totals(db: DB, user: models.User, start: date, category: str | None) -> list[dict]:
    query = (
        select(models.Expense.date, func.sum(models.Expense.amount))
        .where(models.Expense.user_id == user.id, models.Expense.date >= start)
        .group_by(models.Expense.date)
        .order_by(models.Expense.date)
    )
    if category:
        query = query.where(models.Expense.category == category)
    return [{"date": day.isoformat(), "total": float(total)} for day, total in db.execute(query)]


@router.get("/weekly")
def weekly_trends(db: DB, user: CurrentUser, category: str | None = None):
    today = date.today()
    return _daily_totals(db, user, today - timedelta(days=today.weekday()), category)


@router.get("/monthly")
def monthly_trends(db: DB, user: CurrentUser, category: str | None = None):
    return _daily_totals(db, user, date.today().replace(day=1), category)
