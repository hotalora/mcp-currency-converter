from collections.abc import Awaitable, Callable
from langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
)
from infrastructure.driven_adapters.langgraph_agent import (
    ContextSchema,
    resolve_current_date_placeholder
)


class DynamicDatePromptMiddleware(AgentMiddleware[AgentState, ContextSchema]):
    """Middleware that resolves the CURRENT_DATE placeholder in the prompt."""

    def __init__(self, timezone: str = "America/Bogota") -> None:
        self.timezone = timezone

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        if request.system_prompt:
            resolved = resolve_current_date_placeholder(request.system_prompt,
                                                        self.timezone)
            request = request.override(system_prompt=resolved)
        return await handler(request)