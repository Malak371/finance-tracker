from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app import models, schemas
from app.deps import DB, CurrentUser, canonical_category, get_owned_or_404

router = APIRouter(prefix="/budgets", tags=["budgets"])


def _ensure_unique_category(db: DB, user: models.User, category: str, exclude_id: int | None = None) -> None:
    query = select(models.Budget.id).where(
        models.Budget.user_id == user.id, func.lower(models.Budget.category) == category.lower()
    )
    if exclude_id is not None:
        query = query.where(models.Budget.id != exclude_id)
    if db.scalar(query) is not None:
        raise HTTPException(status_code=409, detail=f"You already have a budget for {category}")


@router.get("", response_model=list[schemas.BudgetOut])
def list_budgets(db: DB, user: CurrentUser):
    return db.scalars(
        select(models.Budget).where(models.Budget.user_id == user.id).order_by(models.Budget.category)
    ).all()


@router.post("", response_model=schemas.BudgetOut, status_code=status.HTTP_201_CREATED)
def create_budget(payload: schemas.BudgetIn, db: DB, user: CurrentUser):
    category = canonical_category(db, user, payload.category)
    _ensure_unique_category(db, user, category)
    budget = models.Budget(user_id=user.id, category=category, amount=payload.amount)
    db.add(budget)
    db.commit()
    return budget


@router.put("/{budget_id}", response_model=schemas.BudgetOut)
def update_budget(budget_id: int, payload: schemas.BudgetIn, db: DB, user: CurrentUser):
    budget = get_owned_or_404(db, models.Budget, budget_id, user)
    category = canonical_category(db, user, payload.category)
    _ensure_unique_category(db, user, category, exclude_id=budget.id)
    budget.category = category
    budget.amount = payload.amount
    db.commit()
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: int, db: DB, user: CurrentUser):
    db.delete(get_owned_or_404(db, models.Budget, budget_id, user))
    db.commit()
