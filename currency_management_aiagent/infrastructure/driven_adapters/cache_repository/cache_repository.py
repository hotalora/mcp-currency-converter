import logging
from redis.asyncio import Redis as AsyncRedis
from infrastructure.driven_adapters.secrets_manager.secrets_manager_adapter import (
    SecretsManagerAdapter
)

logger = logging.getLogger(__name__)


class CacheRepository:
    """Repository for managing Redis/Valkey cache connections."""

    def __init__(self,
                 redis_config: dict,
                 secrets_manager: SecretsManagerAdapter):
        self.secret_name = redis_config.get("secret_name", "unknown")
        self.redis_kwargs = {**redis_config}
        self.secrets_manager = secrets_manager
        self.redis = None

    async def initialize(self):
        """Initialize Redis/Valkey connection with credentials from Secrets Manager."""
        redis_kwargs = self.redis_kwargs.copy()
        credentials_from_secrets = redis_kwargs.pop(
            "credentials_from_secrets",
            True,
        )
        redis_kwargs.pop("secret_name", None)
        if credentials_from_secrets:
            credentials = await self.secrets_manager.get_secret(self.secret_name)
            redis_kwargs["username"] = credentials.get("username")
            redis_kwargs["password"] = credentials.get("password")
        self.redis = AsyncRedis(**redis_kwargs)
        await self.redis.ping()
        logger.info("Redis/Valkey connection established successfully.")

    async def get_client(self) -> AsyncRedis:
        """Get the Redis/Valkey client instance."""
        if not self.redis:
            raise RuntimeError("Failed to initialize Redis/Valkey connection")
        return self.redis
