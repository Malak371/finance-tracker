from fastapi import APIRouter
from sqlalchemy import select, union

from app import models
from app.deps import DB, CurrentUser

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[str])
def list_categories(db: DB, user: CurrentUser):
    """Every category name the user has used on an expense or a budget, alphabetically."""
    names = union(
        select(models.Expense.category).where(models.Expense.user_id == user.id),
        select(models.Budget.category).where(models.Budget.user_id == user.id),
    )
    return sorted(db.scalars(names), key=str.lower)
