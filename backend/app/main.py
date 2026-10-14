from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.errors import register_error_handlers
from app.routes import auth, budgets, categories, dashboard, expenses

app = FastAPI(title="Finance Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
register_error_handlers(app)

app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)
app.include_router(budgets.router)
app.include_router(categories.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
