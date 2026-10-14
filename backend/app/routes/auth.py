from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app import models, schemas, security
from app.deps import DB, CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])

# Verified against when the email is unknown, so both failure paths cost one bcrypt check
# and response timing doesn't reveal which emails are registered.
_DUMMY_HASH = security.hash_password("timing-equaliser")


@router.post("/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: schemas.UserCreate, db: DB):
    if db.scalar(select(models.User).where(models.User.email == payload.email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = models.User(email=payload.email, hashed_password=security.hash_password(payload.password))
    db.add(user)
    db.commit()
    return user


@router.post("/login", response_model=schemas.Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB):
    user = db.scalar(select(models.User).where(models.User.email == form.username.strip().lower()))
    password_ok = security.verify_password(form.password, user.hashed_password if user else _DUMMY_HASH)
    if user is None or not password_ok:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": security.create_access_token(user.id)}


@router.get("/me", response_model=schemas.UserOut)
def me(user: CurrentUser):
    return user
