from collections.abc import Awaitable, Callable
from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from infrastructure.driven_adapters.langgraph_agent.models import ContextSchema


class ToolModifyArgsMiddleware(AgentMiddleware[AgentState, ContextSchema]):
    """Middleware to modify tool call arguments based on context."""

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage]],
    ) -> ToolMessage:
        """Middleware to modify tool call arguments based on context."""
        if (
                request.tool is None
                or request.tool.args_schema is None
                or isinstance(request.tool.args_schema, dict)
                or not isinstance(request.runtime.context, ContextSchema)
                or not isinstance(request.tool.args_schema.model_fields, dict)
        ):
            return await handler(request)
        context = request.runtime.context
        context_dict = context.model_dump()
        args = request.tool_call.get("args", {})
        for key in request.tool.args_schema.model_fields.keys():
            if key in context_dict:
                args[key] = context_dict[key]
        request.tool_call["args"] = args
        return await handler(request)
