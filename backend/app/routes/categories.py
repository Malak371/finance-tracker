from fastapi import APIRouter
from sqlalchemy import func, select

from app import models
from app.deps import DB, CurrentUser

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[str])
def list_categories(db: DB, user: CurrentUser):
    """Every category name the user has used, in order of first use.

    The order is stable as new categories are added, which lets the frontend give each
    category a fixed colour.
    """
    first_used = db.execute(
        select(models.Expense.category, func.min(models.Expense.created_at), func.min(models.Expense.id))
        .where(models.Expense.user_id == user.id)
        .group_by(models.Expense.category)
        .order_by(func.min(models.Expense.created_at), func.min(models.Expense.id))
    ).all()
    budget_only = db.scalars(
        select(models.Budget.category).where(models.Budget.user_id == user.id).order_by(models.Budget.id)
    ).all()

    names: dict[str, str] = {}
    for name in [row[0] for row in first_used] + list(budget_only):
        names.setdefault(name.lower(), name)
    return list(names.values())
