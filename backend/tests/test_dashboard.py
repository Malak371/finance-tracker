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
        "comparison": "full_month",
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


def test_trends_fill_empty_months_and_filter_by_category(client, alice):
    add(client, alice, 100, "Rent", "2025-12-01")
    add(client, alice, 20, "Food", "2026-01-15")
    add(client, alice, 30, "food", "2026-03-02")
    add(client, alice, 999, "Food", "2026-04-01")  # after the window

    trends = client.get("/dashboard/trends", params={"month": "2026-03", "months": 4}, headers=alice).json()
    assert trends == [
        {"month": "2025-12", "total": 100},
        {"month": "2026-01", "total": 20},
        {"month": "2026-02", "total": 0},
        {"month": "2026-03", "total": 30},
    ]

    food = client.get(
        "/dashboard/trends", params={"month": "2026-03", "months": 4, "category": "FOOD"}, headers=alice
    ).json()
    assert [m["total"] for m in food] == [0, 20, 0, 30]


def test_trends_months_is_bounded(client, alice):
    assert client.get("/dashboard/trends", params={"months": 0}, headers=alice).status_code == 422
    assert client.get("/dashboard/trends", params={"months": 37}, headers=alice).status_code == 422


def test_current_month_is_compared_with_the_same_point_last_month(client, alice):
    from datetime import date, timedelta

    today = date.today()
    last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    add(client, alice, 40, "Food", last_month_start.isoformat())
    # Spending later in last month than today's day-of-month is not part of the comparison.
    late = last_month_start.replace(day=28)
    if late.day > today.day:
        add(client, alice, 500, "Food", late.isoformat())

    summary = client.get("/dashboard/summary", headers=alice).json()
    assert summary["comparison"] == "month_to_date"
    assert summary["previous_month_total"] == 40

    past = client.get("/dashboard/summary", params={"month": "2026-01"}, headers=alice).json()
    assert past["comparison"] == "full_month"
