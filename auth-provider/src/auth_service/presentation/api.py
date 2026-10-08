from collections.abc import Generator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from auth_service.application.auth_service import AuthService
from auth_service.config import Settings
from auth_service.domain.errors import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from auth_service.infrastructure.database import Base, create_session_factory, get_session
from auth_service.infrastructure import models as _models
from auth_service.infrastructure.repositories import (
    SqlAlchemyTokenRepository,
    SqlAlchemyUserRepository,
)
from auth_service.infrastructure.security import PasswordHasher, TokenCodec
from auth_service.presentation.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    ValidationResponse,
)

bearer_scheme = HTTPBearer(auto_error=False)


def create_app(settings: Settings | None = None) -> FastAPI:
    configuration = settings or Settings.from_environment()
    configuration.validate()
    session_factory = create_session_factory(configuration.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        Base.metadata.create_all(bind=session_factory.kw["bind"])
        yield

    app = FastAPI(title="Authentication Service", version="0.1.0", lifespan=lifespan)
    app.state.session_factory = session_factory
    app.state.settings = configuration

    def session_dependency() -> Generator[Session, None, None]:
        yield from get_session(app.state.session_factory)

    def service_dependency(
        session: Session = Depends(session_dependency),
    ) -> AuthService:
        return AuthService(
            users=SqlAlchemyUserRepository(session),
            tokens=SqlAlchemyTokenRepository(session),
            password_hasher=PasswordHasher(),
            token_codec=TokenCodec(configuration.secret_key),
            token_expiration_seconds=configuration.token_expiration_seconds,
        )

    @app.post(
        "/auth/register",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def register(
        body: RegisterRequest, service: AuthService = Depends(service_dependency)
    ) -> UserResponse:
        try:
            user = service.register(str(body.email), body.password)
        except EmailAlreadyRegisteredError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered.",
            ) from error
        return UserResponse(
            id=user.id, email=user.email, created_at=user.created_at
        )

    @app.post("/auth/login", response_model=TokenResponse)
    def login(
        body: LoginRequest, service: AuthService = Depends(service_dependency)
    ) -> dict[str, object]:
        try:
            return service.login(str(body.email), body.password)
        except InvalidCredentialsError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error

    @app.get("/auth/validate", response_model=ValidationResponse)
    def validate_token(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        service: AuthService = Depends(service_dependency),
    ) -> ValidationResponse:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            user = service.validate_access_token(credentials.credentials)
        except InvalidTokenError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        return ValidationResponse(
            valid=True,
            user=UserResponse(id=user.id, email=user.email, created_at=user.created_at),
        )

    @app.post("/auth/refresh", response_model=TokenResponse)
    def refresh(
        body: RefreshRequest, service: AuthService = Depends(service_dependency)
    ) -> dict[str, object]:
        try:
            return service.refresh(body.refresh_token)
        except InvalidTokenError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error

    return app
