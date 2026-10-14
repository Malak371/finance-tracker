"""Shared request dependencies.

Data isolation rule: every query for user-owned rows goes through `CurrentUser`
and filters on `user_id`. `get_owned_or_404` is the only way routes load a single
row by id, so another user's id is indistinguishable from one that doesn't exist.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, security
from app.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

DB = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> models.User:
    user_id = security.decode_access_token(token)
    user = db.get(models.User, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[models.User, Depends(get_current_user)]


def get_owned_or_404[OwnedModel: (models.Expense, models.Budget)](
    db: Session, model: type[OwnedModel], row_id: int, user: models.User
) -> OwnedModel:
    row = db.scalar(select(model).where(model.id == row_id, model.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return row


def canonical_category(db: Session, user: models.User, name: str) -> str:
    """Reuse the casing of a category the user already has ("food" -> "Food")."""
    for model in (models.Expense, models.Budget):
        existing = db.scalar(
            select(model.category)
            .where(model.user_id == user.id, func.lower(model.category) == name.lower())
            .limit(1)
        )
        if existing:
            return existing
    return name
