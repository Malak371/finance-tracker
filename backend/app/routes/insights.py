from dataclasses import asdict
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import select

from app import insights, models, recurring, schemas
from app.deps import DB, CurrentUser
from app.months import parse_month

router = APIRouter(prefix="/insights", tags=["insights"])

LOOKBACK_DAYS = 18 * 31  # long enough to see a yearly charge repeat


def _load_charges(db: DB, user: models.User, since: date) -> list[recurring.Charge]:
    rows = db.execute(
        select(
            models.Expense.date, models.Expense.amount, models.Expense.description, models.Expense.category
        )
        .where(models.Expense.user_id == user.id, models.Expense.date >= since)
        .order_by(models.Expense.date)
    ).all()
    return [
        recurring.Charge(d, amount, description or category, category)
        for d, amount, description, category in rows
    ]


@router.get("", response_model=list[schemas.InsightOut])
def spending_insights(db: DB, user: CurrentUser, month: str | None = None):
    """Up to six plain-English observations about a month, compared with the user's own history."""
    today = date.today()
    start = parse_month(month)
    charges = _load_charges(db, user, min(start, today) - timedelta(days=LOOKBACK_DAYS))
    detected = recurring.detect_recurring([c for c in charges if c.date <= today], today)
    return [asdict(i) for i in insights.generate_insights(charges, detected, start, today)]


@router.get("/recurring", response_model=schemas.RecurringSummary)
def recurring_charges(db: DB, user: CurrentUser):
    """Subscriptions and other repeating charges detected in the user's history."""
    today = date.today()
    charges = _load_charges(db, user, today - timedelta(days=LOOKBACK_DAYS))
    detected = recurring.detect_recurring(charges, today)
    return {
        "monthly_total": sum((c.monthly_cost for c in detected if c.active), Decimal(0)),
        "charges": [asdict(c) for c in detected],
    }
