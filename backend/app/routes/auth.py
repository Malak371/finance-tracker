import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import delete, select

from app import demo, models, schemas, security
from app.deps import DB, CurrentUser
from app.ratelimit import SlidingWindowLimiter

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


DEMO_TTL = timedelta(hours=24)
MAX_DEMO_USERS = 100
demo_limiter = SlidingWindowLimiter(limit=5, window=3600)


def _remove_old_demo_users(db: DB) -> None:
    """Delete expired demo accounts, and the oldest ones beyond MAX_DEMO_USERS (cascades to their data)."""
    cutoff = datetime.now(UTC) - DEMO_TTL
    db.execute(delete(models.User).where(models.User.is_demo, models.User.created_at < cutoff))
    surplus = db.scalars(
        select(models.User.id)
        .where(models.User.is_demo)
        .order_by(models.User.created_at.desc())
        .offset(MAX_DEMO_USERS - 1)
    ).all()
    if surplus:
        db.execute(delete(models.User).where(models.User.id.in_(surplus)))


@router.post("/demo", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def start_demo(request: Request, db: DB):
    """Create a private, pre-filled demo account and log straight into it.

    Every visitor gets their own copy, so nobody sees anyone else's changes. Demo accounts
    have an unusable random password and are deleted after 24 hours.
    """
    client_ip = request.client.host if request.client else "unknown"
    if not demo_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Too many demo accounts. Please try again later.")

    _remove_old_demo_users(db)
    user = models.User(
        email=f"demo-{secrets.token_hex(6)}@demo.invalid",
        hashed_password=security.hash_password(secrets.token_urlsafe(32)),
        is_demo=True,
    )
    db.add(user)
    db.flush()
    demo.seed_demo_account(db, user)
    db.commit()
    return {"access_token": security.create_access_token(user.id)}
