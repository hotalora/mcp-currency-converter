from dataclasses import dataclass
from datetime import datetime
from typing import Literal


TokenType = Literal["access", "refresh"]


@dataclass(frozen=True)
class User:
    id: int | None
    email: str
    password_hash: str
    created_at: datetime


@dataclass(frozen=True)
class AuthToken:
    jti: str
    user_id: int
    token_type: TokenType
    expires_at: datetime
    revoked_at: datetime | None = None
