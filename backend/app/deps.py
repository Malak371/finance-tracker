"""Shared request dependencies.

Data isolation rule: every query for user-owned rows goes through `CurrentUser`
and filters on `user_id`. `get_owned_or_404` is the only way routes load a single
row by id, so another user's id is indistinguishable from one that doesn't exist.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, select, union
from sqlalchemy.orm import Session

from app import categorization, models, security
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


def get_owned_or_404[OwnedModel: (models.Expense, models.Budget, models.CategoryRule)](
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


class CategoryLookup:
    """Batch version of canonical_category: loads the user's category names once."""

    def __init__(self, db: Session, user: models.User):
        names = db.scalars(
            union(
                select(models.Expense.category).where(models.Expense.user_id == user.id),
                select(models.Budget.category).where(models.Budget.user_id == user.id),
            )
        )
        self._by_lower = {name.lower(): name for name in names}

    def canonical(self, name: str) -> str:
        # New names are remembered too, so "food" and "Food" in one import end up the same.
        return self._by_lower.setdefault(name.lower(), name)


def load_categorizer(db: Session, user: models.User) -> categorization.Categorizer:
    rules = db.execute(
        select(models.CategoryRule.keyword, models.CategoryRule.category).where(
            models.CategoryRule.user_id == user.id
        )
    ).all()
    training = db.execute(
        select(models.Expense.description, models.Expense.category).where(
            models.Expense.user_id == user.id,
            models.Expense.description.is_not(None),
            models.Expense.category_source.in_(categorization.USER_LABELLED_SOURCES),
            models.Expense.category != categorization.UNCATEGORIZED,
        )
    ).all()
    return categorization.Categorizer(dict(rules), training)
