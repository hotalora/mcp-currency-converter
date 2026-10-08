from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./auth.db"
    secret_key: str = "development-only-secret-key-change-before-deployment"
    token_expiration_seconds: int = 3600

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite:///./auth.db"),
            secret_key=os.getenv(
                "AUTH_SECRET_KEY",
                "development-only-secret-key-change-before-deployment",
            ),
        )

    def validate(self) -> None:
        if len(self.secret_key) < 32:
            raise ValueError("AUTH_SECRET_KEY must contain at least 32 characters.")
        if self.token_expiration_seconds <= 0:
            raise ValueError("Token expiration must be a positive number of seconds.")
