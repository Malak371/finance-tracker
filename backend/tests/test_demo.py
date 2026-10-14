from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select, update

from app import models
from app.demo import generate_expenses
from app.routes.auth import MAX_DEMO_USERS


def start_demo(client):
    response = client.post("/auth/demo")
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.parametrize(
    "today", [date(2026, 3, 1), date(2026, 2, 28), date(2026, 10, 14), date(2027, 1, 31)]
)
def test_generated_history_is_a_year_long_and_never_in_the_future(today):
    expenses = generate_expenses(today)
    assert max(e.date for e in expenses) <= today
    assert min(e.date for e in expenses) <= today - timedelta(days=360)
    assert all(e.amount > 0 for e in expenses)
    assert any(e.date.month == today.month and e.date.year == today.year for e in expenses)


def test_demo_account_is_seeded_and_shows_every_feature(client):
    headers = start_demo(client)
    me = client.get("/auth/me", headers=headers).json()
    assert me["is_demo"] is True

    assert len(client.get("/expenses", headers=headers).json()) > 300
    assert len(client.get("/rules", headers=headers).json()) == 3

    statuses = {b["category"]: b["status"] for b in client.get("/budgets/status", headers=headers).json()}
    assert statuses["Dining"] == "warning"
    assert statuses["Shopping"] == "over"

    recurring = client.get("/insights/recurring", headers=headers).json()["charges"]
    by_merchant = {c["merchant"]: c for c in recurring}
    assert by_merchant["NETFLIX.COM"]["previous_amount"] == 15.49
    assert by_merchant["MAPLE STREET APARTMENTS RENT"]["active"]
    assert not by_merchant["HULU 877-8244858"]["active"]

    trends = client.get("/dashboard/trends", headers=headers).json()
    assert all(month["total"] > 0 for month in trends)


def test_each_demo_visitor_gets_a_private_copy(client):
    first, second = start_demo(client), start_demo(client)
    expense_id = client.get("/expenses", headers=first).json()[0]["id"]
    client.delete(f"/expenses/{expense_id}", headers=first)
    assert client.delete(f"/expenses/{expense_id}", headers=second).status_code == 404
    assert (
        len(client.get("/expenses", headers=second).json())
        == len(client.get("/expenses", headers=first).json()) + 1
    )


def test_expired_and_surplus_demo_accounts_are_removed(client, db, alice):
    start_demo(client)
    db.execute(
        update(models.User)
        .where(models.User.is_demo)
        .values(created_at=datetime.now(UTC) - timedelta(days=2))
    )
    db.commit()

    start_demo(client)
    demo_users = db.scalars(select(models.User).where(models.User.is_demo)).all()
    assert len(demo_users) == 1
    assert db.scalar(select(models.User).where(models.User.email == "alice@example.com")) is not None
    assert MAX_DEMO_USERS >= 10


def test_demo_creation_is_rate_limited(client):
    for _ in range(5):
        start_demo(client)
    response = client.post("/auth/demo")
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "too_many_requests"


def test_sample_statement_round_trip_flags_duplicates(client):
    headers = start_demo(client)
    sample = client.get("/imports/sample", headers=headers)
    assert sample.headers["content-type"].startswith("text/csv")

    parsed = client.post(
        "/imports/parse", files={"file": ("sample.csv", sample.content, "text/csv")}, headers=headers
    ).json()
    mapping = {k: v for k, v in parsed["suggested_mapping"].items() if k != "date_format_options"}
    preview = client.post(
        "/imports/preview", json={"mapping": mapping, "rows": parsed["rows"]}, headers=headers
    ).json()

    assert sum(t["duplicate"] for t in preview["transactions"]) == 4
    sources = {t["description"]: t["category_source"] for t in preview["transactions"]}
    assert sources["TRADER JOE'S #552"] == "rule"
    assert sources["STARBUCKS #2087"] in ("history", "model")
    assert sources["ZEN FLOW YOGA STUDIO"] == "none"
    assert [s["reason"] for s in preview["skipped"]] == ["Money in (income or refund), not an expense"]


def test_demo_accounts_cannot_log_in_with_a_password(client, db):
    start_demo(client)
    email = db.scalar(select(models.User.email).where(models.User.is_demo))
    for password in ("!", "", "anything-at-all"):
        response = client.post("/auth/login", data={"username": email, "password": password})
        assert response.status_code in (401, 422)
