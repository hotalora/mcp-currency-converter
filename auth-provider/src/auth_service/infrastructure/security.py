from datetime import datetime
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from auth_service.domain.entities import TokenType, User
from auth_service.domain.errors import InvalidTokenError


class PasswordHasher:
    def __init__(self) -> None:
        self._hasher = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return self._hasher.verify(password, password_hash)


class TokenCodec:
    def __init__(self, secret_key: str) -> None:
        self._secret_key = secret_key

    def create_claims(
        self,
        user: User,
        token_type: TokenType,
        issued_at: datetime,
        expires_at: datetime,
    ) -> dict[str, int | str]:
        if user.id is None:
            raise ValueError("A persisted user is required to issue a token.")
        return {
            "sub": str(user.id),
            "email": user.email,
            "type": token_type,
            "jti": str(uuid4()),
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

    def encode(self, claims: dict[str, int | str]) -> str:
        return jwt.encode(claims, self._secret_key, algorithm="HS256")

    def decode(self, encoded_token: str) -> dict[str, object]:
        try:
            return jwt.decode(
                encoded_token,
                self._secret_key,
                algorithms=["HS256"],
                options={"require": ["exp", "iat", "sub", "jti", "type", "email"]},
            )
        except jwt.InvalidTokenError as error:
            raise InvalidTokenError from error
