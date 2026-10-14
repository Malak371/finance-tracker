import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import delete, select

from app import demo, models, schemas, security
from app.config import get_settings
from app.deps import DB, CurrentUser
from app.ratelimit import SlidingWindowLimiter

router = APIRouter(prefix="/auth", tags=["auth"])

# Verified against when the email is unknown, so both failure paths cost one bcrypt check
# and response timing doesn't reveal which emails are registered.
_DUMMY_HASH = security.hash_password("timing-equaliser")

# Brute-force protection. Failed logins are limited per email (so rotating IPs doesn't help an
# attacker) and per IP (so spraying many emails from one address doesn't either).
FAILED_LOGIN_WINDOW = 15 * 60
failed_logins_by_email = SlidingWindowLimiter(limit=10, window=FAILED_LOGIN_WINDOW)
failed_logins_by_ip = SlidingWindowLimiter(limit=30, window=FAILED_LOGIN_WINDOW)
signup_limiter = SlidingWindowLimiter(limit=10, window=3600)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _too_many(limiter: SlidingWindowLimiter, key: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=429, detail=message, headers={"Retry-After": str(limiter.retry_after(key))}
    )


@router.post("/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: schemas.UserCreate, request: Request, db: DB):
    ip = client_ip(request)
    if not signup_limiter.allow(ip):
        raise _too_many(signup_limiter, ip, "Too many sign-ups from this network. Please try again later.")
    if db.scalar(select(models.User).where(models.User.email == payload.email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = models.User(email=payload.email, hashed_password=security.hash_password(payload.password))
    db.add(user)
    db.commit()
    return user


@router.post("/login", response_model=schemas.Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request, db: DB):
    email = form.username.strip().lower()
    ip = client_ip(request)
    message = "Too many failed attempts. Please wait a few minutes and try again."
    if failed_logins_by_email.is_limited(email):
        raise _too_many(failed_logins_by_email, email, message)
    if failed_logins_by_ip.is_limited(ip):
        raise _too_many(failed_logins_by_ip, ip, message)

    user = db.scalar(select(models.User).where(models.User.email == email))
    password_ok = security.verify_password(form.password, user.hashed_password if user else _DUMMY_HASH)
    if user is None or not password_ok:
        failed_logins_by_email.record(email)
        failed_logins_by_ip.record(ip)
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    failed_logins_by_email.clear(email)
    return {"access_token": security.create_access_token(user.id)}


@router.get("/me", response_model=schemas.UserOut)
def me(user: CurrentUser):
    return user


DEMO_TTL = timedelta(hours=24)
MAX_DEMO_USERS = 100
demo_limiter = SlidingWindowLimiter(limit=get_settings().demo_accounts_per_hour, window=3600)


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
    cannot log in with a password and are deleted after 24 hours.
    """
    ip = client_ip(request)
    if not demo_limiter.allow(ip):
        raise _too_many(demo_limiter, ip, "Too many demo accounts. Please try again later.")

    _remove_old_demo_users(db)
    user = models.User(
        email=f"demo-{secrets.token_hex(6)}@demo.invalid",
        # Demo accounts are entered only through this endpoint; skip bcrypt, which takes
        # seconds on a small free-tier CPU, for a password nobody could use anyway.
        hashed_password=security.UNUSABLE_PASSWORD,
        is_demo=True,
    )
    db.add(user)
    db.flush()
    demo.seed_demo_account(db, user)
    db.commit()
    return {"access_token": security.create_access_token(user.id)}
