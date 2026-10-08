from datetime import UTC, datetime, timedelta
from typing import Callable

from auth_service.application.ports import PasswordHasher, TokenCodec
from auth_service.domain.entities import AuthToken, TokenType, User
from auth_service.domain.errors import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from auth_service.domain.repositories import TokenRepository, UserRepository


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        tokens: TokenRepository,
        password_hasher: PasswordHasher,
        token_codec: TokenCodec,
        token_expiration_seconds: int,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._password_hasher = password_hasher
        self._token_codec = token_codec
        self._token_expiration_seconds = token_expiration_seconds
        self._clock = clock

    def register(self, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        if self._users.get_by_email(normalized_email) is not None:
            raise EmailAlreadyRegisteredError
        user = User(
            id=None,
            email=normalized_email,
            password_hash=self._password_hasher.hash(password),
            created_at=self._clock(),
        )
        return self._users.add(user)

    def login(self, email: str, password: str) -> dict[str, object]:
        user = self._users.get_by_email(email.strip().lower())
        if user is None or not self._password_hasher.verify(
            password, user.password_hash
        ):
            raise InvalidCredentialsError
        return self._issue_pair(user)

    def validate_access_token(self, encoded_token: str) -> User:
        claims, token = self._get_active_token(encoded_token, "access")
        user = self._users.get_by_email(str(claims["email"]))
        if user is None or user.id != token.user_id:
            raise InvalidTokenError
        return user

    def refresh(self, encoded_token: str) -> dict[str, object]:
        claims, token = self._get_active_token(encoded_token, "refresh")
        user = self._users.get_by_email(str(claims["email"]))
        if user is None or user.id != token.user_id:
            raise InvalidTokenError
        self._tokens.revoke(token.jti, self._clock())
        return self._issue_pair(user)

    def _get_active_token(
        self, encoded_token: str, expected_type: TokenType
    ) -> tuple[dict[str, object], AuthToken]:
        claims = self._token_codec.decode(encoded_token)
        if claims.get("type") != expected_type:
            raise InvalidTokenError
        jti = claims.get("jti")
        subject = claims.get("sub")
        email = claims.get("email")
        if not isinstance(jti, str) or not isinstance(subject, str):
            raise InvalidTokenError
        if not isinstance(email, str):
            raise InvalidTokenError
        try:
            user_id = int(subject)
        except ValueError as error:
            raise InvalidTokenError from error
        token = self._tokens.get_by_jti(jti)
        if (
            token is None
            or token.user_id != user_id
            or token.token_type != expected_type
            or token.revoked_at is not None
            or token.expires_at <= self._clock()
        ):
            raise InvalidTokenError
        return claims, token

    def _issue_pair(self, user: User) -> dict[str, object]:
        if user.id is None:
            raise InvalidTokenError
        user_id = user.id
        issued_at = datetime.fromtimestamp(int(self._clock().timestamp()), UTC)
        expiration = issued_at + timedelta(seconds=self._token_expiration_seconds)
        access_token = self._issue_token(user, user_id, "access", issued_at, expiration)
        refresh_token = self._issue_token(user, user_id, "refresh", issued_at, expiration)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self._token_expiration_seconds,
        }

    def _issue_token(
        self,
        user: User,
        user_id: int,
        token_type: TokenType,
        now: datetime,
        expiration: datetime,
    ) -> str:
        claims = self._token_codec.create_claims(user, token_type, now, expiration)
        encoded = self._token_codec.encode(claims)
        self._tokens.add(
            AuthToken(
                jti=str(claims["jti"]),
                user_id=user_id,
                token_type=token_type,
                expires_at=expiration,
            )
        )
        return encoded
