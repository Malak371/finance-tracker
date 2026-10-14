STATEMENT = (
    b"Date,Description,Amount\n"
    b"2026-01-02,Coffee Shop,-3.50\n"
    b"2026-01-02,Coffee Shop,-3.50\n"
    b"2026-01-05,Grocery Mart,-54.20\n"
    b"2026-01-31,Salary,2500.00\n"
)


def parse(client, headers, content=STATEMENT, filename="statement.csv"):
    return client.post("/imports/parse", files={"file": (filename, content, "text/csv")}, headers=headers)


def preview(client, headers, parsed):
    mapping = {k: v for k, v in parsed["suggested_mapping"].items() if k != "date_format_options"}
    return client.post("/imports/preview", json={"mapping": mapping, "rows": parsed["rows"]}, headers=headers)


def to_commit(rows, category="Food"):
    return {
        "transactions": [
            {"date": r["date"], "amount": r["amount"], "description": r["description"], "category": category}
            for r in rows
        ]
    }


def test_full_import_flow_and_reimport_is_flagged(client, alice):
    parsed = parse(client, alice).json()
    assert parsed["headers"] == ["Date", "Description", "Amount"]

    first = preview(client, alice, parsed).json()
    assert [t["description"] for t in first["transactions"]] == ["Coffee Shop", "Coffee Shop", "Grocery Mart"]
    assert all(not t["duplicate"] for t in first["transactions"])
    assert first["transactions"][0]["category"] == "Uncategorized"
    assert first["skipped"] == [{"row": 4, "reason": "Money in (income or refund), not an expense"}]

    committed = client.post("/imports/commit", json=to_commit(first["transactions"]), headers=alice)
    assert committed.json() == {"imported": 3}
    assert len(client.get("/expenses", headers=alice).json()) == 3

    second = preview(client, alice, parsed).json()
    assert [t["duplicate"] for t in second["transactions"]] == [True, True, True]


def test_category_column_from_file_reuses_existing_casing(client, alice):
    client.post("/expenses", json={"amount": 1, "category": "Groceries", "date": "2026-01-01"}, headers=alice)
    parsed = parse(client, alice, b"Date,Description,Amount,Category\n2026-01-05,Mart,-5,groceries\n").json()
    row = preview(client, alice, parsed).json()["transactions"][0]
    assert (row["category"], row["category_source"]) == ("Groceries", "file")


def test_duplicates_only_consider_the_users_own_data(client, alice, bob):
    parsed = parse(client, alice).json()
    rows = preview(client, alice, parsed).json()["transactions"]
    client.post("/imports/commit", json=to_commit(rows), headers=alice)

    bobs_preview = preview(client, bob, parse(client, bob).json()).json()
    assert not any(t["duplicate"] for t in bobs_preview["transactions"])


def test_rejects_bad_files_with_clear_messages(client, alice):
    response = parse(client, alice, b"")
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "The file is empty."

    too_big = parse(client, alice, b"a,b\n" + b"1,2\n" * 600_000)
    assert too_big.status_code == 413


def test_rejects_mapping_to_missing_column(client, alice):
    parsed = parse(client, alice).json()
    mapping = {"date_column": 0, "description_column": 1, "amount_column": 9, "date_format": "%Y-%m-%d"}
    response = client.post(
        "/imports/preview", json={"mapping": mapping, "rows": parsed["rows"]}, headers=alice
    )
    assert response.status_code == 400
    assert "doesn't exist" in response.json()["error"]["message"]


def test_commit_validates_every_row(client, alice):
    bad = {"transactions": [{"date": "2026-01-01", "amount": -1, "category": "Food"}]}
    response = client.post("/imports/commit", json=bad, headers=alice)
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "transactions.0.amount"
    assert client.get("/expenses", headers=alice).json() == []
