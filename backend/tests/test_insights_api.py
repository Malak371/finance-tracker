from datetime import date, timedelta


def test_recurring_endpoint_finds_subscriptions_and_totals_active_ones(client, alice, bob):
    today = date.today()
    for months_ago in range(4, 0, -1):
        day = (today - timedelta(days=30 * months_ago)).isoformat()
        for description, amount in (("NETFLIX.COM", "15.49"), ("PureGym", "34.99")):
            payload = {"amount": amount, "category": "Subs", "date": day, "description": description}
            assert client.post("/expenses", json=payload, headers=alice).status_code == 201
    client.post(
        "/expenses",
        json={"amount": 80, "category": "Food", "date": today.isoformat(), "description": "Grocer"},
        headers=alice,
    )

    summary = client.get("/insights/recurring", headers=alice).json()
    assert [c["merchant"] for c in summary["charges"]] == ["PureGym", "NETFLIX.COM"]
    assert summary["monthly_total"] == 50.48

    assert client.get("/insights/recurring", headers=bob).json() == {"monthly_total": 0, "charges": []}
