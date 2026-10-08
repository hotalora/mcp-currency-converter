from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import select, update

from auth_service.infrastructure.models import TokenModel


def register(client, email: str = "person@example.com", password: str = "a-strong-password"):
    return client.post(
        "/auth/register", json={"email": email, "password": password}
    )


def test_register_normalizes_email_and_does_not_return_password_hash(client):
    response = register(client, " Person@Example.com ")

    assert response.status_code == 201
    assert response.json()["email"] == "person@example.com"
    assert "password_hash" not in response.json()


def test_register_rejects_duplicate_email_case_insensitively(client):
    assert register(client).status_code == 201

    response = register(client, "PERSON@example.com")

    assert response.status_code == 409


def test_register_validates_email_and_password_boundaries(client):
    short_password = client.post(
        "/auth/register",
        json={"email": "person@example.com", "password": "1234567"},
    )
    maximum_password = client.post(
        "/auth/register",
        json={"email": "boundary@example.com", "password": "x" * 128},
    )
    too_long_password = client.post(
        "/auth/register",
        json={"email": "long@example.com", "password": "x" * 129},
    )
    malformed_email = client.post(
        "/auth/register", json={"email": "not-an-email", "password": "12345678"}
    )

    assert short_password.status_code == 422
    assert maximum_password.status_code == 201
    assert too_long_password.status_code == 422
    assert malformed_email.status_code == 422


def test_login_issues_persisted_one_hour_access_and_refresh_tokens(client):
    register(client)

    response = client.post(
        "/auth/login",
        json={"email": "PERSON@example.com", "password": "a-strong-password"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] == 3600
    persisted_session = client.app.state.session_factory()
    try:
        persisted_tokens = persisted_session.scalars(select(TokenModel)).all()
    finally:
        persisted_session.close()
    assert len(persisted_tokens) == 2
    for token_type in ("access", "refresh"):
        claims = jwt.decode(
            payload[f"{token_type}_token"],
            "test-secret-key-that-is-long-enough-for-tests",
            algorithms=["HS256"],
        )
        assert claims["type"] == token_type
        assert claims["exp"] - claims["iat"] == 3600
        persisted_token = next(
            token for token in persisted_tokens if token.jti == claims["jti"]
        )
        assert persisted_token.user_id == int(claims["sub"])
        stored_expiration = int(
            persisted_token.expires_at.replace(tzinfo=UTC).timestamp()
        )
        assert stored_expiration == claims["exp"]


def test_login_rejects_unknown_user_and_wrong_password(client):
    register(client)

    wrong_password = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "wrong-password"},
    )
    unknown_user = client.post(
        "/auth/login",
        json={"email": "unknown@example.com", "password": "a-strong-password"},
    )

    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_validate_accepts_access_token_and_rejects_missing_or_refresh_token(client):
    register(client)
    tokens = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "a-strong-password"},
    ).json()

    valid = client.get(
        "/auth/validate",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    refresh_as_access = client.get(
        "/auth/validate",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    missing = client.get("/auth/validate")

    assert valid.status_code == 200
    assert valid.json()["valid"] is True
    assert valid.json()["user"]["email"] == "person@example.com"
    assert refresh_as_access.status_code == 401
    assert missing.status_code == 401


def test_refresh_rotates_refresh_token_and_rejects_reuse(client):
    register(client)
    original = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "a-strong-password"},
    ).json()

    refreshed = client.post(
        "/auth/refresh", json={"refresh_token": original["refresh_token"]}
    )
    reused = client.post(
        "/auth/refresh", json={"refresh_token": original["refresh_token"]}
    )

    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != original["refresh_token"]
    assert reused.status_code == 401


def test_refresh_rejects_access_token_and_expired_token(client):
    register(client)
    tokens = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "a-strong-password"},
    ).json()
    expired = jwt.encode(
        {
            "sub": "1",
            "email": "person@example.com",
            "type": "refresh",
            "jti": "expired-token",
            "iat": int((datetime.now(UTC) - timedelta(hours=2)).timestamp()),
            "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp()),
        },
        "test-secret-key-that-is-long-enough-for-tests",
        algorithm="HS256",
    )

    access_token = client.post(
        "/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )
    expired_token = client.post("/auth/refresh", json={"refresh_token": expired})
    malformed_token = client.post(
        "/auth/refresh", json={"refresh_token": "not-a-jwt"}
    )

    assert access_token.status_code == 401
    assert expired_token.status_code == 401
    assert malformed_token.status_code == 401


def test_refresh_rejects_token_with_non_integer_subject(client):
    invalid_subject = jwt.encode(
        {
            "sub": "not-an-id",
            "email": "person@example.com",
            "type": "refresh",
            "jti": "invalid-subject",
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
        },
        "test-secret-key-that-is-long-enough-for-tests",
        algorithm="HS256",
    )

    response = client.post(
        "/auth/refresh", json={"refresh_token": invalid_subject}
    )

    assert response.status_code == 401


def test_access_token_is_rejected_at_persisted_expiration_boundary(client):
    register(client)
    tokens = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "a-strong-password"},
    ).json()
    claims = jwt.decode(
        tokens["access_token"],
        "test-secret-key-that-is-long-enough-for-tests",
        algorithms=["HS256"],
    )
    session = client.app.state.session_factory()
    try:
        session.execute(
            update(TokenModel)
            .where(TokenModel.jti == claims["jti"])
            .values(expires_at=datetime.now(UTC))
        )
        session.commit()
    finally:
        session.close()

    response = client.get(
        "/auth/validate",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 401


def test_refreshed_access_token_is_valid_and_old_refresh_token_is_revoked(client):
    register(client)
    original = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "a-strong-password"},
    ).json()
    refreshed = client.post(
        "/auth/refresh", json={"refresh_token": original["refresh_token"]}
    ).json()

    valid = client.get(
        "/auth/validate",
        headers={"Authorization": f"Bearer {refreshed['access_token']}"},
    )

    assert valid.status_code == 200
    assert client.post(
        "/auth/refresh", json={"refresh_token": original["refresh_token"]}
    ).status_code == 401
