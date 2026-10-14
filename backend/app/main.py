import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.errors import register_error_handlers
from app.middleware import register_middleware
from app.routes import auth, budgets, categories, dashboard, expenses, imports, insights, rules

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

app = FastAPI(title="Finance Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "Retry-After"],
)
register_error_handlers(app)
# Registered after CORS so it wraps it: every response, including CORS rejections, gets headers.
register_middleware(app)

app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)
app.include_router(budgets.router)
app.include_router(categories.router)
app.include_router(imports.router)
app.include_router(rules.router)
app.include_router(insights.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
