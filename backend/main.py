from fastapi import FastAPI
import models, database
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, expenses, dashboard, budgets, trends

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
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