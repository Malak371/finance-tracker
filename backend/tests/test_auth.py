from datetime import UTC, datetime, timedelta

import jwt

from app.config import get_settings


def test_signup_and_login(client):
    response = client.post("/auth/signup", json={"email": "New@Example.com", "password": "long-enough-1"})
    assert response.status_code == 201
    assert response.json()["email"] == "new@example.com"

    login = client.post("/auth/login", data={"username": "new@example.com", "password": "long-enough-1"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "new@example.com"


def test_password_is_hashed_with_bcrypt(client, db):
    from app.models import User

    client.post("/auth/signup", json={"email": "a@example.com", "password": "long-enough-1"})
    stored = db.query(User).one().hashed_password
    assert stored.startswith("$2b$")
    assert "long-enough-1" not in stored


def test_duplicate_email_rejected_case_insensitively(client, alice):
    response = client.post("/auth/signup", json={"email": "ALICE@example.com", "password": "long-enough-1"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_weak_password_rejected(client):
    response = client.post("/auth/signup", json={"email": "a@example.com", "password": "short"})
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "password"


def test_wrong_password_and_unknown_email_look_the_same(client, alice):
    wrong_password = client.post(
        "/auth/login", data={"username": "alice@example.com", "password": "nope-nope"}
    )
    unknown_email = client.post("/auth/login", data={"username": "who@example.com", "password": "nope-nope"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def _token(**claims) -> str:
    settings = get_settings()
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def test_expired_token_rejected(client, alice):
    expired = _token(sub="1", exp=datetime.now(UTC) - timedelta(minutes=1))
    response = client.get("/expenses", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_token_signed_with_another_secret_rejected(client, alice):
    claims = {"sub": "1", "exp": datetime.now(UTC) + timedelta(hours=1)}
    forged = jwt.encode(claims, "an-attacker-guessed-secret-of-32-plus-chars", algorithm="HS256")
    assert client.get("/expenses", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_token_without_subject_rejected(client, alice):
    token = _token(exp=datetime.now(UTC) + timedelta(hours=1))
    assert client.get("/expenses", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_expiry_matches_settings(client, alice):
    token = alice["Authorization"].removeprefix("Bearer ")
    claims = jwt.decode(token, options={"verify_signature": False})
    lifetime = timedelta(seconds=claims["exp"] - claims["iat"])
    assert lifetime == timedelta(minutes=get_settings().access_token_expire_minutes)
