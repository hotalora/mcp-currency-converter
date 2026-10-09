import logging
import asyncio
from infrastructure.driven_adapters.secrets_manager.secrets_manager_adapter import (
    SecretsManagerAdapter
)

logger = logging.getLogger(__name__)


class LlmAuthAdapter:
    """Adapter for LLM authentication using secrets from AWS."""

    def __init__(self,
                 llm_config: dict,
                 secrets_manager: SecretsManagerAdapter):
        self.secret_name = llm_config.get("secret_name", "unknown")
        self.secret_field = llm_config.get("secret_field", "api_key")
        self.api_key = llm_config.get("api_key", "")
        self.use_secrets = llm_config.get("use_secrets", True)
        self._cached_api_key = None
        self.secrets_manager = secrets_manager
        self._async_lock = asyncio.Lock()

    async def retrieve_llm_api_key(self) -> str:
        """Retrieve the LLM api key from Secrets Manager."""
        if self.api_key:
            return self.api_key
        if not self.use_secrets:
            raise RuntimeError(
                "Configure OPENAI_API_KEY or enable LLM_USE_SECRETS."
            )
        credentials = await self.secrets_manager.get_secret(
            self.secret_name, use_cache=False
        )
        api_key = credentials.get(self.secret_field)
        if not isinstance(api_key, str) or not api_key:
            raise RuntimeError(
                f"LLM secret '{self.secret_name}' has no '{self.secret_field}' value."
            )
        return api_key

    async def get_api_key(self) -> str:
        """Retrieve and cache the LLM api key."""
        if self._cached_api_key:
            return self._cached_api_key
        async with self._async_lock:
            if self._cached_api_key:
                return self._cached_api_key
            self._cached_api_key = await self.retrieve_llm_api_key()
            logger.info("LLM token fetched successfully")
        return self._cached_api_key

    async def refresh_api_key(self) -> None:
        """Refresh the cached LLM api key."""
        async with self._async_lock:
            self._cached_api_key = await self.retrieve_llm_api_key()
            logger.info("LLM api key refreshed successfully")
