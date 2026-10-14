from dataclasses import asdict
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import select

from app import models, recurring, schemas
from app.deps import DB, CurrentUser

router = APIRouter(prefix="/insights", tags=["insights"])

LOOKBACK_DAYS = 18 * 31  # long enough to see a yearly charge repeat


@router.get("/recurring", response_model=schemas.RecurringSummary)
def recurring_charges(db: DB, user: CurrentUser):
    """Subscriptions and other repeating charges detected in the user's history."""
    today = date.today()
    rows = db.execute(
        select(
            models.Expense.date, models.Expense.amount, models.Expense.description, models.Expense.category
        )
        .where(
            models.Expense.user_id == user.id,
            models.Expense.description.is_not(None),
            models.Expense.date >= today - timedelta(days=LOOKBACK_DAYS),
        )
        .order_by(models.Expense.date)
    ).all()
    charges = recurring.detect_recurring([recurring.Charge(*row) for row in rows], today)
    return {
        "monthly_total": sum((c.monthly_cost for c in charges if c.active), Decimal(0)),
        "charges": [asdict(c) for c in charges],
    }
