from collections.abc import Awaitable, Callable
from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelCallResult,
    ModelRequest,
    ModelResponse,
)
from openai import AuthenticationError
from infrastructure.driven_adapters.langgraph_agent.models import ContextSchema
from infrastructure.driven_adapters.llm_auth.llm_auth_adapter import (
    LlmAuthAdapter
)


class ApiKeyRefreshMiddleware(AgentMiddleware[AgentState, ContextSchema]):
    """Middleware to refresh API key on authentication errors."""

    def __init__(self, llm_auth: LlmAuthAdapter) -> None:
        self.llm_auth = llm_auth

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        """Middleware to refresh API key on authentication errors."""
        try:
            return await handler(request)
        except AuthenticationError:
            await self.llm_auth.refresh_api_key()
            return await handler(request)
