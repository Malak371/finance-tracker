from fastapi import FastAPI
import models, database
from routes import auth, expenses, dashboard

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)

@app.get("/")
def read_root():
    return {"message": "Finance Tracker API running"}