from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Budget 
from schemas import BudgetCreate, BudgetOut
from .auth import get_current_user
from fastapi import HTTPException

router = APIRouter(prefix="/budgets", tags=["budgets"])

@router.post("/", response_model=BudgetOut)
def create_budget(budget: BudgetCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    existing = db.query(Budget).filter(Budget.user_id == user.id, Budget.category == budget.category).first()
    if existing:
        raise HTTPException(status_code=400, detail="Budget category already exists")
    db_budget = Budget(user_id=user.id, category=budget.category, amount=budget.amount)
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.get("/", response_model=list[BudgetOut])
def get_budgets(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Budget).filter(Budget.user_id == user.id).all()

@router.put("/{budget_id}", response_model=BudgetOut)
def update_budget(budget_id: int, budget: BudgetCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user.id).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Check for duplicate category if changed
    if db_budget.category != budget.category:
        existing = db.query(Budget).filter(Budget.user_id == user.id, Budget.category == budget.category).first()
        if existing:
            raise HTTPException(status_code=400, detail="Budget category already exists")
    
    db_budget.category = budget.category
    db_budget.amount = budget.amount
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.delete("/{budget_id}", status_code=204)
def delete_budget(budget_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user.id).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(db_budget)
    db.commit()
    return
