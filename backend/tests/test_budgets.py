def test_budget_crud(client, alice):
    created = client.post("/budgets", json={"category": "Food", "amount": 300}, headers=alice)
    assert created.status_code == 201
    budget_id = created.json()["id"]

    updated = client.put(f"/budgets/{budget_id}", json={"category": "Food", "amount": 350}, headers=alice)
    assert updated.json()["amount"] == 350

    assert client.delete(f"/budgets/{budget_id}", headers=alice).status_code == 204
    assert client.get("/budgets", headers=alice).json() == []


def test_one_budget_per_category(client, alice):
    client.post("/budgets", json={"category": "Food", "amount": 300}, headers=alice)
    duplicate = client.post("/budgets", json={"category": "FOOD", "amount": 100}, headers=alice)
    assert duplicate.status_code == 409


def test_budget_amount_must_be_positive(client, alice):
    response = client.post("/budgets", json={"category": "Food", "amount": -100}, headers=alice)
    assert response.status_code == 422


def _spend(client, headers, amount, category="Food", day="2026-03-10"):
    client.post("/expenses", json={"amount": amount, "category": category, "date": day}, headers=headers)


def test_budget_status_thresholds(client, alice):
    for category in ("Food", "Fun", "Rent"):
        client.post("/budgets", json={"category": category, "amount": 100}, headers=alice)
    _spend(client, alice, 50, "Food")
    _spend(client, alice, 80, "Fun")
    _spend(client, alice, 100.01, "Rent")
    _spend(client, alice, 999, "Food", day="2026-04-01")  # other month

    statuses = client.get("/budgets/status", params={"month": "2026-03"}, headers=alice).json()

    assert [(s["category"], s["percent"], s["status"]) for s in statuses] == [
        ("Rent", 100.0, "over"),
        ("Fun", 80.0, "warning"),
        ("Food", 50.0, "ok"),
    ]
    assert statuses[0]["remaining"] == -0.01
    assert statuses[0]["projected"] is None


def test_budget_status_matches_categories_case_insensitively(client, alice):
    _spend(client, alice, 30, "groceries")
    client.post("/budgets", json={"category": "Groceries", "amount": 60}, headers=alice)
    status = client.get("/budgets/status", params={"month": "2026-03"}, headers=alice).json()[0]
    assert (status["spent"], status["status"]) == (30, "ok")


def test_projection_for_the_current_month():
    from datetime import date
    from decimal import Decimal

    from app.routes.budgets import projected_spend

    # 100 spent by the 10th of a 30-day month -> 300 at that pace.
    assert projected_spend(Decimal(100), date(2026, 4, 1), date(2026, 4, 10)) == Decimal("300.00")
    assert projected_spend(Decimal(100), date(2026, 3, 1), date(2026, 4, 10)) is None


def test_budget_status_is_private(client, alice, bob):
    client.post("/budgets", json={"category": "Food", "amount": 100}, headers=alice)
    _spend(client, bob, 90, "Food")
    assert client.get("/budgets/status", params={"month": "2026-03"}, headers=bob).json() == []
    assert client.get("/budgets/status", params={"month": "2026-03"}, headers=alice).json()[0]["spent"] == 0
