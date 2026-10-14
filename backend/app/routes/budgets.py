from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app import models, schemas
from app.deps import DB, CurrentUser, canonical_category, get_owned_or_404
from app.months import add_months, parse_month

router = APIRouter(prefix="/budgets", tags=["budgets"])

WARNING_THRESHOLD = 80  # percent of the monthly limit


def budget_state(spent: Decimal, limit: Decimal) -> tuple[float, str]:
    percent = float(spent / limit * 100)
    if percent > 100:
        return percent, "over"
    if percent >= WARNING_THRESHOLD:
        return percent, "warning"
    return percent, "ok"


def projected_spend(spent: Decimal, month_start: date, today: date) -> Decimal | None:
    """Month-end spend if the current daily pace continues; None for months not in progress."""
    if (month_start.year, month_start.month) != (today.year, today.month):
        return None
    days_in_month = (add_months(month_start, 1) - month_start).days
    return (spent / today.day * days_in_month).quantize(Decimal("0.01"))


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


@router.get("/status", response_model=list[schemas.BudgetStatus])
def budget_status(db: DB, user: CurrentUser, month: str | None = None):
    """Each budget's progress for a month (default: current), most used first."""
    start = parse_month(month)
    spent_by_category = dict(
        db.execute(
            select(func.lower(models.Expense.category), func.sum(models.Expense.amount))
            .where(
                models.Expense.user_id == user.id,
                models.Expense.date >= start,
                models.Expense.date < add_months(start, 1),
            )
            .group_by(func.lower(models.Expense.category))
        ).all()
    )
    today = date.today()
    statuses = []
    for budget in db.scalars(select(models.Budget).where(models.Budget.user_id == user.id)):
        spent = spent_by_category.get(budget.category.lower(), Decimal(0))
        percent, state = budget_state(spent, budget.amount)
        statuses.append(
            {
                "id": budget.id,
                "category": budget.category,
                "amount": budget.amount,
                "spent": spent,
                "remaining": budget.amount - spent,
                "percent": round(percent, 1),
                "status": state,
                "projected": projected_spend(spent, start, today),
            }
        )
    return sorted(statuses, key=lambda s: (-s["percent"], s["category"].lower()))


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
