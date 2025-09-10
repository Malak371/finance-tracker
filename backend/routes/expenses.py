from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import schemas, crud, database
from .auth import get_current_user

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.post("/", response_model=schemas.ExpenseOut)
def add_expense(expense: schemas.ExpenseCreate, db: Session = Depends(database.get_db), user=Depends(get_current_user)):
    return crud.create_expense(db, user.id, expense)

@router.get("/", response_model=list[schemas.ExpenseOut])
def list_expenses(category: str = None, db: Session = Depends(database.get_db), user=Depends(get_current_user)):
    return crud.get_expenses(db, user.id, category)