import pytest


def add(client, headers, **overrides):
    payload = {"amount": "12.50", "category": "Food", "date": "2026-01-15", "description": "Lunch"}
    payload.update(overrides)
    return client.post("/expenses", json=payload, headers=headers)


def test_create_list_update_delete(client, alice):
    created = add(client, alice)
    assert created.status_code == 201
    expense = created.json()
    assert expense["amount"] == 12.5

    assert [e["id"] for e in client.get("/expenses", headers=alice).json()] == [expense["id"]]

    updated = client.put(
        f"/expenses/{expense['id']}",
        json={"amount": 20, "category": "Transport", "date": "2026-01-16"},
        headers=alice,
    )
    assert updated.status_code == 200
    assert updated.json()["category"] == "Transport"
    assert updated.json()["description"] is None

    assert client.delete(f"/expenses/{expense['id']}", headers=alice).status_code == 204
    assert client.get("/expenses", headers=alice).json() == []


def test_list_filters_and_ordering(client, alice):
    add(client, alice, date="2026-01-01", category="Food")
    add(client, alice, date="2026-02-01", category="Rent")
    add(client, alice, date="2026-03-01", category="Food")

    food = client.get("/expenses", params={"category": "Food"}, headers=alice).json()
    assert [e["date"] for e in food] == ["2026-03-01", "2026-01-01"]

    feb = client.get("/expenses", params={"start": "2026-02-01", "end": "2026-02-28"}, headers=alice).json()
    assert [e["category"] for e in feb] == ["Rent"]


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"amount": 0}, "amount"),
        ({"amount": -5}, "amount"),
        ({"amount": "1.234"}, "amount"),
        ({"category": "   "}, "category"),
        ({"category": "x" * 51}, "category"),
        ({"date": "1999-12-31"}, "date"),
        ({"date": "not-a-date"}, "date"),
        ({"description": "x" * 256}, "description"),
    ],
)
def test_invalid_expenses_rejected(client, alice, overrides, field):
    response = add(client, alice, **overrides)
    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "validation_error"
    assert [d["field"] for d in body["details"]] == [field]


def test_category_reuses_existing_casing(client, alice):
    add(client, alice, category="Food")
    assert add(client, alice, category="  food ").json()["category"] == "Food"


def test_money_is_summed_exactly(client, alice):
    for amount in ("0.10", "0.20", "0.30"):
        add(client, alice, amount=amount)
    summary = client.get("/dashboard/summary", params={"month": "2026-01"}, headers=alice).json()
    assert summary["total_spent"] == 0.6
    assert summary["by_category"] == [{"category": "Food", "total": 0.6, "count": 3}]


def test_export_csv(client, alice):
    add(client, alice, amount="9.90", description="Coffee, beans")
    response = client.get("/expenses/export", headers=alice)
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text.splitlines() == [
        "Date,Category,Amount,Description",
        '2026-01-15,Food,9.90,"Coffee, beans"',
    ]


def test_missing_expense_returns_consistent_404(client, alice):
    response = client.delete("/expenses/12345", headers=alice)
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Expense not found"}}
