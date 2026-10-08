from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth_service.domain.entities import AuthToken, TokenType, User
from auth_service.domain.errors import EmailAlreadyRegisteredError
from auth_service.infrastructure.models import TokenModel, UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_email(self, email: str) -> User | None:
        model = self._session.scalar(
            select(UserModel).where(UserModel.email == email)
        )
        return self._to_entity(model) if model is not None else None

    def add(self, user: User) -> User:
        model = UserModel(
            email=user.email,
            password_hash=user.password_hash,
            created_at=user.created_at,
        )
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            raise EmailAlreadyRegisteredError from error
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            created_at=_as_utc(model.created_at),
        )


class SqlAlchemyTokenRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, token: AuthToken) -> None:
        self._session.add(
            TokenModel(
                jti=token.jti,
                user_id=token.user_id,
                token_type=token.token_type,
                expires_at=token.expires_at,
                revoked_at=token.revoked_at,
            )
        )
        self._session.flush()

    def get_by_jti(self, jti: str) -> AuthToken | None:
        model = self._session.get(TokenModel, jti)
        if model is None:
            return None
        if model.token_type == "access":
            token_type: TokenType = "access"
        elif model.token_type == "refresh":
            token_type = "refresh"
        else:
            raise ValueError("Unsupported token type stored in the database.")
        return AuthToken(
            jti=model.jti,
            user_id=model.user_id,
            token_type=token_type,
            expires_at=_as_utc(model.expires_at),
            revoked_at=(
                _as_utc(model.revoked_at) if model.revoked_at is not None else None
            ),
        )

    def revoke(self, jti: str, revoked_at: datetime) -> None:
        self._session.execute(
            update(TokenModel)
            .where(TokenModel.jti == jti, TokenModel.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
        )


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value
