from datetime import datetime
from typing import Protocol

from auth_service.domain.entities import AuthToken, User


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None: ...

    def add(self, user: User) -> User: ...


class TokenRepository(Protocol):
    def add(self, token: AuthToken) -> None: ...

    def get_by_jti(self, jti: str) -> AuthToken | None: ...

    def revoke(self, jti: str, revoked_at: datetime) -> None: ...
