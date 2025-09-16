from fastapi import FastAPI
import models, database
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, expenses, dashboard

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # allow POST, GET, OPTIONS, etc
    allow_headers=["*"],  # allow Authorization, Content-Type, etc
)

app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)

@app.get("/")
def read_root():
    return {"message": "Finance Tracker API running"}