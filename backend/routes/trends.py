from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import get_db
import models
from sqlalchemy import func

router = APIRouter(prefix="/expenses/trends", tags=["Trends"])

def get_start_dates(period: str):
    today = datetime.today()
    if period == "weekly":
        start = today - timedelta(days=today.weekday())
    elif period == "monthly":
        start = today.replace(day=1)
    else:
        start = today
    return start

@router.get("/weekly")
def weekly_trends(category: str | None = Query(None), db: Session = Depends(get_db)):
    start = get_start_dates("weekly")
    query = db.query(
        func.date(models.Expense.date).label("date"),
        func.sum(models.Expense.amount).label("total")
    ).filter(models.Expense.date >= start)
    
    if category:
        query = query.filter(models.Expense.category == category)
        
    results = query.group_by(func.date(models.Expense.date)).order_by(func.date(models.Expense.date)).all()
    return [{"date": str(r.date), "total": float(r.total)} for r in results]

@router.get("/monthly")
def weekly_trends(category: str | None = Query(None), db: Session = Depends(get_db)):
    start = get_start_dates("monthly")
    query = db.query(
        func.date(models.Expense.date).label("date"),
        func.sum(models.Expense.amount).label("total")
    ).filter(models.Expense.date >= start)
    
    if category:
        query = query.filter(models.Expense.category == category)
        
    results = query.group_by(func.date(models.Expense.date)).order_by(func.date(models.Expense.date)).all()
    return [{"date": str(r.date), "total": float(r.total)} for r in results]