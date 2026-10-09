from collections.abc import Awaitable, Callable
from langchain.agents.middleware import AgentState, hook_config
from langchain.agents.middleware.types import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from infrastructure.driven_adapters.langgraph_agent.models import ContextSchema


class ToolEarlyExitMiddleware(AgentMiddleware[AgentState, ContextSchema]):
    """Middleware to handle early exit based on tool call results."""

    def __init__(self, early_exit_tools, success_keywords) -> None:
        self.early_exit_tools = early_exit_tools
        self.success_keywords = success_keywords

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage]],
    ) -> ToolMessage:
        result = await handler(request)
        if result.name in self.early_exit_tools:
            output = str(result.content).lower()
            if any(keyword in output for keyword in self.success_keywords):
                result.additional_kwargs["early_exit"] = True
        return result

    @hook_config(can_jump_to=["end"])
    async def abefore_model(self,
                            state: AgentState,
                            runtime: Runtime) -> dict | None:
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        if isinstance(last_message, ToolMessage):
            if last_message.additional_kwargs.get("early_exit"):
                return {"jump_to": "end"}
        return None
