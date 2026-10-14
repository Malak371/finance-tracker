"""Users must never be able to read or change each other's data."""

import re

import pytest

from app.main import app

PUBLIC_ROUTES = {
    ("POST", "/auth/signup"),
    ("POST", "/auth/login"),
    ("POST", "/auth/demo"),
    ("GET", "/health"),
}


def _protected_routes():
    # The OpenAPI schema lists every API endpoint, so new routes are covered automatically.
    for path, operations in app.openapi()["paths"].items():
        for method in operations:
            if (method.upper(), path) not in PUBLIC_ROUTES:
                yield method.upper(), path


PROTECTED_ROUTES = sorted(_protected_routes())


def test_route_discovery_finds_routes():
    assert len(PROTECTED_ROUTES) >= 10


@pytest.mark.parametrize(("method", "path"), PROTECTED_ROUTES)
def test_every_non_public_route_requires_a_token(client, method, path):
    response = client.request(method, re.sub(r"\{\w+\}", "1", path))
    assert response.status_code == 401, f"{method} {path} is reachable without a token"


@pytest.fixture
def alices_data(client, alice):
    expense = client.post(
        "/expenses",
        json={"amount": 42, "category": "Secret", "date": "2026-01-15", "description": "Alice only"},
        headers=alice,
    ).json()
    budget = client.post("/budgets", json={"category": "Secret", "amount": 100}, headers=alice).json()
    return {"expense": expense, "budget": budget}


def test_lists_and_aggregates_only_show_own_data(client, alices_data, bob):
    assert client.get("/expenses", headers=bob).json() == []
    assert client.get("/budgets", headers=bob).json() == []
    summary = client.get("/dashboard/summary", params={"month": "2026-01"}, headers=bob).json()
    assert summary["total_spent"] == 0
    assert summary["by_category"] == []
    assert client.get("/categories", headers=bob).json() == []
    assert "Alice only" not in client.get("/expenses/export", headers=bob).text


def test_cannot_modify_another_users_rows(client, alice, alices_data, bob):
    expense_id = alices_data["expense"]["id"]
    budget_id = alices_data["budget"]["id"]
    change = {"amount": 1, "category": "Hacked", "date": "2026-01-15"}

    assert client.put(f"/expenses/{expense_id}", json=change, headers=bob).status_code == 404
    assert client.delete(f"/expenses/{expense_id}", headers=bob).status_code == 404
    assert (
        client.put(f"/budgets/{budget_id}", json={"category": "Hacked", "amount": 1}, headers=bob).status_code
        == 404
    )
    assert client.delete(f"/budgets/{budget_id}", headers=bob).status_code == 404

    assert client.get("/expenses", headers=alice).json() == [alices_data["expense"]]
    assert client.get("/budgets", headers=alice).json() == [alices_data["budget"]]
