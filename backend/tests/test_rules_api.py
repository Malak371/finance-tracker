def add_expense(client, headers, description, category="Uncategorized", **extra):
    payload = {"amount": 10, "category": category, "date": "2026-01-10", "description": description, **extra}
    return client.post("/expenses", json=payload, headers=headers).json()


def import_rows(client, headers, rows):
    """Import (description, category, source) rows through the import commit endpoint."""
    transactions = [
        {"amount": 10, "date": "2026-01-10", "description": d, "category": c, "category_source": s}
        for d, c, s in rows
    ]
    assert (
        client.post("/imports/commit", json={"transactions": transactions}, headers=headers).status_code
        == 201
    )


def preview_one(client, headers, description):
    rows = [["2026-02-01", description, "-5.00"]]
    mapping = {"date_column": 0, "description_column": 1, "amount_column": 2, "date_format": "%Y-%m-%d"}
    response = client.post("/imports/preview", json={"mapping": mapping, "rows": rows}, headers=headers)
    return response.json()["transactions"][0]


def test_rule_crud_normalises_keywords(client, alice):
    created = client.post(
        "/rules", json={"keyword": "  TESCO*Stores ", "category": "Groceries"}, headers=alice
    )
    assert created.status_code == 201
    rule = created.json()
    assert (rule["keyword"], rule["applied"]) == ("tesco stores", 0)

    duplicate = client.post("/rules", json={"keyword": "tesco stores", "category": "Food"}, headers=alice)
    assert duplicate.status_code == 409

    updated = client.put(
        f"/rules/{rule['id']}", json={"keyword": "tesco", "category": "Groceries"}, headers=alice
    )
    assert updated.json()["keyword"] == "tesco"
    assert client.delete(f"/rules/{rule['id']}", headers=alice).status_code == 204
    assert client.get("/rules", headers=alice).json() == []


def test_invalid_keyword_rejected(client, alice):
    response = client.post("/rules", json={"keyword": " *! ", "category": "X"}, headers=alice)
    assert response.status_code == 422


def test_rule_applies_to_auto_categorised_but_not_user_labelled_expenses(client, alice):
    import_rows(
        client,
        alice,
        [
            ("NETFLIX.COM", "Uncategorized", "none"),
            ("Netflix gift", "Gifts", "manual"),
            ("NETFLIX 2", "Subscriptions", "default"),
        ],
    )
    created = client.post(
        "/rules",
        json={"keyword": "netflix", "category": "Streaming", "apply_to_existing": True},
        headers=alice,
    ).json()
    assert created["applied"] == 2
    by_description = {e["description"]: e for e in client.get("/expenses", headers=alice).json()}
    assert by_description["NETFLIX.COM"]["category"] == "Streaming"
    assert by_description["NETFLIX.COM"]["category_source"] == "rule"
    assert by_description["Netflix gift"]["category"] == "Gifts"


def test_preview_uses_user_rule(client, alice):
    client.post("/rules", json={"keyword": "corner shop", "category": "Snacks"}, headers=alice)
    row = preview_one(client, alice, "CORNER SHOP LONDON")
    assert (row["category"], row["category_source"]) == ("Snacks", "rule")


def test_classifier_learns_from_corrections(client, alice):
    # Default keywords would file Amazon under Shopping.
    assert preview_one(client, alice, "AMZN Mktp books")["category"] == "Shopping"

    # The user imports Amazon purchases and corrects them to Books, and has other labelled data.
    import_rows(client, alice, [("AMZN Mktp books order", "Shopping", "default")] * 6)
    for expense in client.get("/expenses", headers=alice).json():
        client.put(
            f"/expenses/{expense['id']}",
            json={
                "amount": 10,
                "category": "Books",
                "date": "2026-01-10",
                "description": expense["description"],
            },
            headers=alice,
        )
    import_rows(client, alice, [("Local Grocer", "Groceries", "manual")] * 6)

    row = preview_one(client, alice, "AMZN Mktp books")
    assert (row["category"], row["category_source"]) == ("Books", "model")
    assert row["confidence"] >= 0.7


def test_auto_categorised_imports_are_not_used_as_training_data(client, alice):
    # Rows the user accepted without changing keep their auto source and don't train the model.
    import_rows(client, alice, [("Mystery Vendor", "Guess", "model")] * 12)
    assert preview_one(client, alice, "Mystery Vendor")["category_source"] == "none"


def test_rules_are_private(client, alice, bob):
    rule = client.post("/rules", json={"keyword": "secret", "category": "X"}, headers=alice).json()
    assert client.get("/rules", headers=bob).json() == []
    assert client.delete(f"/rules/{rule['id']}", headers=bob).status_code == 404
    assert preview_one(client, bob, "SECRET THING")["category_source"] == "none"


def test_defaults_are_listed(client, alice):
    defaults = client.get("/rules/defaults", headers=alice).json()
    assert {"keyword": "netflix", "category": "Subscriptions"} in defaults
