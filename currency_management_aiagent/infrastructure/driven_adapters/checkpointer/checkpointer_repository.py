import logging
from langgraph.checkpoint.redis import AsyncShallowRedisSaver
from infrastructure.driven_adapters.cache_repository.cache_repository import (
    CacheRepository
)

logger = logging.getLogger(__name__)


class CheckpointerRepository:
    """Repository for managing Redis checkpointers with TTL.

    Maintains a single Redis connection but creates checkpointers
    with configurable TTL per agent.
    """

    def __init__(self, cache_repository: CacheRepository):
        self.cache_repository = cache_repository

    async def get_checkpointer(self, ttl: int = 600) -> AsyncShallowRedisSaver:
        """Get a Redis checkpointer with specific TTL.

        Args:
            ttl: Time-to-live in seconds for checkpoint entries.

        Returns:
            AsyncShallowRedisSaver instance.
        """
        redis = await self.cache_repository.get_client()
        return AsyncShallowRedisSaver(
            redis_client=redis,
            ttl={"default_ttl": ttl, "refresh_on_read": True}
        )
