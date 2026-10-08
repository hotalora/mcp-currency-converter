from datetime import datetime
from typing import Protocol

from auth_service.domain.entities import TokenType, User


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...


class TokenCodec(Protocol):
    def create_claims(
        self,
        user: User,
        token_type: TokenType,
        issued_at: datetime,
        expires_at: datetime,
    ) -> dict[str, int | str]: ...

    def encode(self, claims: dict[str, int | str]) -> str: ...

    def decode(self, encoded_token: str) -> dict[str, object]: ...
