def add(client, headers, amount, category, day):
    payload = {"amount": amount, "category": category, "date": day}
    assert client.post("/expenses", json=payload, headers=headers).status_code == 201


def test_summary_for_a_month_compares_with_previous_month(client, alice):
    add(client, alice, 100, "Rent", "2026-02-01")
    add(client, alice, 30, "Food", "2026-03-05")
    add(client, alice, 20, "Food", "2026-03-31")
    add(client, alice, 200, "Rent", "2026-03-01")
    add(client, alice, 999, "Food", "2026-04-01")

    summary = client.get("/dashboard/summary", params={"month": "2026-03"}, headers=alice).json()

    assert summary == {
        "month": "2026-03",
        "total_spent": 250,
        "previous_month_total": 100,
        "transaction_count": 3,
        "by_category": [
            {"category": "Rent", "total": 200, "count": 1},
            {"category": "Food", "total": 50, "count": 2},
        ],
    }


def test_summary_handles_year_boundary(client, alice):
    add(client, alice, 10, "Food", "2025-12-31")
    add(client, alice, 5, "Food", "2026-01-01")
    summary = client.get("/dashboard/summary", params={"month": "2026-01"}, headers=alice).json()
    assert summary["total_spent"] == 5
    assert summary["previous_month_total"] == 10


def test_invalid_month_rejected(client, alice):
    response = client.get("/dashboard/summary", params={"month": "2026-13"}, headers=alice)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
