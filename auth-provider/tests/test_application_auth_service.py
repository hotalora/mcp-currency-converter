from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from auth_service.application.auth_service import AuthService
from auth_service.domain.entities import AuthToken, User
from auth_service.domain.errors import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
)


class InMemoryUsers:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    def get_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    def add(self, user: User) -> User:
        persisted_user = replace(user, id=len(self.users) + 1)
        self.users[persisted_user.email] = persisted_user
        return persisted_user


class InMemoryTokens:
    def __init__(self) -> None:
        self.tokens: dict[str, AuthToken] = {}

    def add(self, token: AuthToken) -> None:
        self.tokens[token.jti] = token

    def get_by_jti(self, jti: str) -> AuthToken | None:
        return self.tokens.get(jti)

    def revoke(self, jti: str, revoked_at: datetime) -> None:
        token = self.tokens[jti]
        self.tokens[jti] = replace(token, revoked_at=revoked_at)


class FakePasswordHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == self.hash(password)


class FakeTokenCodec:
    def __init__(self) -> None:
        self._claims: dict[str, dict[str, object]] = {}

    def create_claims(
        self,
        user: User,
        token_type: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> dict[str, int | str]:
        jti = f"token-{len(self._claims) + 1}"
        return {
            "sub": str(user.id),
            "email": user.email,
            "type": token_type,
            "jti": jti,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

    def encode(self, claims: dict[str, int | str]) -> str:
        encoded = f"encoded-{claims['jti']}"
        self._claims[encoded] = claims
        return encoded

    def decode(self, encoded_token: str) -> dict[str, object]:
        try:
            return self._claims[encoded_token]
        except KeyError as error:
            raise InvalidTokenError from error


class MutableClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 1, 1, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def auth_service():
    clock = MutableClock()
    users = InMemoryUsers()
    tokens = InMemoryTokens()
    codec = FakeTokenCodec()
    service = AuthService(
        users=users,
        tokens=tokens,
        password_hasher=FakePasswordHasher(),
        token_codec=codec,
        token_expiration_seconds=3600,
        clock=clock,
    )
    return service, users, tokens, clock


def test_register_normalizes_email_and_rejects_duplicate(auth_service):
    service, users, _, _ = auth_service

    user = service.register(" Person@Example.com ", "a-strong-password")

    assert user.email == "person@example.com"
    assert user.password_hash == "hashed:a-strong-password"
    assert users.get_by_email(user.email) == user
    with pytest.raises(EmailAlreadyRegisteredError):
        service.register("PERSON@example.com", "another-password")


def test_login_rejects_invalid_password(auth_service):
    service, _, _, _ = auth_service
    service.register("person@example.com", "a-strong-password")

    with pytest.raises(InvalidCredentialsError):
        service.login("person@example.com", "wrong-password")


def test_access_token_expires_at_exact_database_expiration(auth_service):
    service, _, tokens, clock = auth_service
    service.register("person@example.com", "a-strong-password")
    pair = service.login("person@example.com", "a-strong-password")
    access_token = str(pair["access_token"])
    issued_token = next(
        token for token in tokens.tokens.values() if token.token_type == "access"
    )
    clock.now = issued_token.expires_at - timedelta(microseconds=1)

    assert service.validate_access_token(access_token).email == "person@example.com"

    clock.now = issued_token.expires_at
    with pytest.raises(InvalidTokenError):
        service.validate_access_token(access_token)


def test_refresh_revokes_previous_refresh_token(auth_service):
    service, _, _, _ = auth_service
    service.register("person@example.com", "a-strong-password")
    original_pair = service.login("person@example.com", "a-strong-password")

    new_pair = service.refresh(str(original_pair["refresh_token"]))

    assert new_pair["refresh_token"] != original_pair["refresh_token"]
    with pytest.raises(InvalidTokenError):
        service.refresh(str(original_pair["refresh_token"]))
