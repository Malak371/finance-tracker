import csv
from datetime import date
from io import StringIO

from fastapi import APIRouter, Response, status
from sqlalchemy import select

from app import models, schemas
from app.deps import DB, CurrentUser, canonical_category, get_owned_or_404

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _user_expenses(user: models.User, category: str | None, start: date | None, end: date | None):
    query = select(models.Expense).where(models.Expense.user_id == user.id)
    if category:
        query = query.where(models.Expense.category == category)
    if start:
        query = query.where(models.Expense.date >= start)
    if end:
        query = query.where(models.Expense.date <= end)
    return query.order_by(models.Expense.date.desc(), models.Expense.id.desc())


@router.get("", response_model=list[schemas.ExpenseOut])
def list_expenses(
    db: DB,
    user: CurrentUser,
    category: str | None = None,
    start: date | None = None,
    end: date | None = None,
):
    return db.scalars(_user_expenses(user, category, start, end)).all()


@router.post("", response_model=schemas.ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(payload: schemas.ExpenseIn, db: DB, user: CurrentUser):
    data = payload.model_dump()
    data["category"] = canonical_category(db, user, payload.category)
    expense = models.Expense(**data, user_id=user.id)
    db.add(expense)
    db.commit()
    return expense


@router.get("/export")
def export_expenses(db: DB, user: CurrentUser):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Category", "Amount", "Description"])
    for e in db.scalars(_user_expenses(user, None, None, None)):
        writer.writerow([e.date.isoformat(), e.category, f"{e.amount:.2f}", e.description or ""])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"},
    )


@router.put("/{expense_id}", response_model=schemas.ExpenseOut)
def update_expense(expense_id: int, payload: schemas.ExpenseIn, db: DB, user: CurrentUser):
    expense = get_owned_or_404(db, models.Expense, expense_id, user)
    category = canonical_category(db, user, payload.category)
    if category != expense.category:
        # A changed category is a correction the classifier should learn from.
        expense.category_source = "manual"
    expense.amount = payload.amount
    expense.category = category
    expense.date = payload.date
    expense.description = payload.description
    db.commit()
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: DB, user: CurrentUser):
    db.delete(get_owned_or_404(db, models.Expense, expense_id, user))
    db.commit()
