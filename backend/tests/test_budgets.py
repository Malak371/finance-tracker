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
