from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import schemas, crud, database, models
from .auth import get_current_user
from fastapi.responses import StreamingResponse
from io import StringIO
import csv
from fastapi import HTTPException

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.post("/", response_model=schemas.ExpenseOut)
def add_expense(expense: schemas.ExpenseCreate, db: Session = Depends(database.get_db), user=Depends(get_current_user)):
    return crud.create_expense(db, user.id, expense)

@router.get("/", response_model=list[schemas.ExpenseOut])
def list_expenses(category: str = None, db: Session = Depends(database.get_db), user=Depends(get_current_user)):
    return crud.get_expenses(db, user.id, category)

@router.put("/{expense_id}", response_model=schemas.ExpenseOut)
def update_expense(expense_id: int, expense: schemas.ExpenseCreate, db: Session = Depends(database.get_db), user=Depends(get_current_user)):
    # Fix: use models.Expense instead of crud.Expense
    db_exp = db.query(models.Expense).filter(models.Expense.id == expense_id, models.Expense.user_id == user.id).first()
    if not db_exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db_exp.category = expense.category
    db_exp.amount = expense.amount
    db_exp.date = expense.date
    db_exp.description = expense.description
    db.commit()
    db.refresh(db_exp)
    return db_exp

@router.delete("/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(database.get_db), user=Depends(get_current_user)):
    # Fix: use models.Expense
    db_exp = db.query(models.Expense).filter(models.Expense.id == expense_id, models.Expense.user_id == user.id).first()
    if not db_exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(db_exp)
    db.commit()
    return


@router.get("/export")
def export_expenses(db: Session = Depends(database.get_db), user=Depends(get_current_user)):
    expenses = crud.get_expenses(db, user.id)
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Category", "Amount", "Description"])
    for e in expenses:
        writer.writerow([e.date, e.category, e.amount, e.description])
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"}
    )