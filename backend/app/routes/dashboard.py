from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import func, select

from app import models, schemas
from app.deps import DB, CurrentUser

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=schemas.DashboardSummary)
def summary(db: DB, user: CurrentUser):
    rows = db.execute(
        select(models.Expense.category, func.sum(models.Expense.amount))
        .where(models.Expense.user_id == user.id)
        .group_by(models.Expense.category)
    ).all()
    breakdown = dict(rows)
    return {"total_spent": sum(breakdown.values(), Decimal(0)), "breakdown": breakdown}
