from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional, List

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
class UserOut(BaseModel):
    id: int
    email: EmailStr
    class Config:
        orm_mode = True
        
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class ExpenseCreate(BaseModel):
    amount: float
    category: str
    date: date
    description: Optional[str] = None
    
class ExpenseOut(BaseModel):
    id: int
    amount: float
    category: str 
    date: date
    description: Optional[str] 
    class Config:
        orm_mode = True

class DashboardSummary(BaseModel):
    total_spent: float
    breakdown: dict
