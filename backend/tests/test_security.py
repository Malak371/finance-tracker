from fastapi.testclient import TestClient

from app.main import app


def login(client, email, password):
    return client.post("/auth/login", data={"username": email, "password": password})


def test_security_headers_on_api_responses(client, alice):
    response = client.get("/expenses", headers=alice)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"
    # Errors get them too.
    assert client.get("/expenses").headers["X-Content-Type-Options"] == "nosniff"


def test_interactive_docs_are_not_blocked_by_the_api_csp(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Content-Security-Policy" not in response.headers


def test_request_ids_are_generated_or_propagated(client):
    generated = client.get("/health").headers["X-Request-ID"]
    assert len(generated) == 32

    assert (
        client.get("/health", headers={"X-Request-ID": "proxy-abc-12345"}).headers["X-Request-ID"]
        == "proxy-abc-12345"
    )
    # Anything that doesn't look like an ID (e.g. log injection attempts) is replaced.
    replaced = client.get("/health", headers={"X-Request-ID": "bad id\nINJECTED"}).headers["X-Request-ID"]
    assert replaced != "bad id\nINJECTED"


def test_unexpected_errors_include_the_request_id(alice, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.routes.dashboard.month_total", broken)
    response = TestClient(app, raise_server_exceptions=False).get("/dashboard/summary", headers=alice)

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["message"] == "Something went wrong on our side"
    assert "boom" not in response.text
    assert error["request_id"] == response.headers["X-Request-ID"]


def test_repeated_failed_logins_for_an_account_are_blocked(client, alice):
    for _ in range(10):
        assert login(client, "alice@example.com", "wrong-password").status_code == 401

    blocked = login(client, "alice@example.com", "correct-horse-1")
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "too_many_requests"
    assert 0 < int(blocked.headers["Retry-After"]) <= 15 * 60


def test_a_successful_login_resets_the_failure_count(client, alice):
    for _ in range(9):
        login(client, "alice@example.com", "wrong-password")
    assert login(client, "alice@example.com", "correct-horse-1").status_code == 200
    for _ in range(9):
        assert login(client, "alice@example.com", "wrong-password").status_code == 401


def test_password_spraying_from_one_address_is_blocked(client):
    for i in range(30):
        assert login(client, f"user{i}@example.com", "guess").status_code == 401
    assert login(client, "someone-else@example.com", "guess").status_code == 429


def test_signups_are_rate_limited_per_address(client):
    for i in range(10):
        response = client.post(
            "/auth/signup", json={"email": f"u{i}@example.com", "password": "long-enough-1"}
        )
        assert response.status_code == 201
    response = client.post(
        "/auth/signup", json={"email": "one-more@example.com", "password": "long-enough-1"}
    )
    assert response.status_code == 429
