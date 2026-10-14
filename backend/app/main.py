from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, expenses, dashboard, budgets, trends
from app.config import get_settings


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)
app.include_router(budgets.router)
app.include_router(trends.router)

@app.get("/")
def read_root():
    return {"message": "Finance Tracker API running"}