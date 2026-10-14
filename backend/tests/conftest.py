"""Test setup.

Tests run against a real PostgreSQL database (TEST_DATABASE_URL) so that Numeric
columns, constraints and cascades behave exactly as in production. The schema is
built by running the Alembic migrations, which also tests the migrations themselves.
"""

import os

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/finance_tracker_test"
)
# Must be set before the app is imported, since settings are read at import time.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET"] = "test-secret-that-is-at-least-32-characters-long"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
os.environ["BCRYPT_ROUNDS"] = "4"

from collections.abc import Callable, Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from alembic import command  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables() -> Iterator[None]:
    yield
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
def reset_rate_limits() -> None:
    from app.routes.auth import demo_limiter

    demo_limiter.reset()


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def make_user(client: TestClient) -> Callable[..., dict[str, str]]:
    """Create a user and return Authorization headers for them."""

    def _make_user(email: str = "alice@example.com", password: str = "correct-horse-1") -> dict[str, str]:
        assert client.post("/auth/signup", json={"email": email, "password": password}).status_code == 201
        response = client.post("/auth/login", data={"username": email, "password": password})
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _make_user


@pytest.fixture
def alice(make_user) -> dict[str, str]:
    return make_user("alice@example.com")


@pytest.fixture
def bob(make_user) -> dict[str, str]:
    return make_user("bob@example.com")
