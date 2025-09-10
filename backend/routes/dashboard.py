from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import schemas, crud, database
from .auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary", response_model=schemas.DashboardSummary)
def summary(db: Session = Depends(database.get_db), user = Depends(get_current_user)):
    return crud.get_dashboard_summary(db, user.id)