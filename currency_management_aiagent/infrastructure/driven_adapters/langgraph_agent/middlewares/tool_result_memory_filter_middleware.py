import logging
from typing import Any
from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain_core.messages import (AIMessage,
                                     HumanMessage,
                                     RemoveMessage,
                                     ToolMessage)
from langgraph.config import get_config
from langgraph.runtime import Runtime
from infrastructure.driven_adapters.langgraph_agent import (
    ContextSchema,
)

logger = logging.getLogger(__name__)


class ToolResultMemoryFilterMiddleware(
    AgentMiddleware[AgentState, ContextSchema]
):
    """Removes intermediate tool messages from last completed turn."""

    def __init__(self, tool_names: list[str] | None = None) -> None:
        """Initialize middleware with optional tool name filter.

        Args:
            tool_names: List of tool names to filter. If None or
                empty, filters all tools.
        """
        self.tool_names: list[str] = tool_names or []

    def _should_filter_tool(self, tool_name: str) -> bool:
        """Check if this tool should be filtered.

        Filters all tools when tool_names is empty;
        otherwise only listed tools.
        """
        return not self.tool_names or tool_name in self.tool_names

    def _find_last_group(self, messages: list) -> list:
        """Find the last message group.

        Iterates backwards to find the last HumanMessage,
        then returns slice from that point forward.

        Args:
            messages: List of all messages

        Returns:
            List of messages in the last group
        """
        last_human_idx = None
        for i, msg in enumerate(reversed(messages)):
            if isinstance(msg, HumanMessage):
                last_human_idx = len(messages) - 1 - i
                break
        if last_human_idx is None:
            return messages
        return messages[last_human_idx:]

    def _should_remove_ai_message(self, msg: AIMessage) -> bool:
        """Check if an AIMessage with tool_calls should be removed."""
        if msg.id is None:
            return False
        return any(
            self._should_filter_tool(
                tc.get("name", "") if isinstance(tc, dict) else tc.name
            )
            for tc in msg.tool_calls
        )

    def _should_remove_tool_message(self, msg: ToolMessage) -> bool:
        """Check if a ToolMessage should be removed."""
        if msg.id is None:
            return False
        tool_name = msg.name or ""
        return self._should_filter_tool(tool_name)

    def _get_messages_to_remove(self, group: list) -> list[RemoveMessage]:
        """Identify tool messages to remove from a group."""
        to_remove: list[RemoveMessage] = []
        for msg in group:
            if isinstance(msg, AIMessage) and msg.tool_calls:
                if self._should_remove_ai_message(msg):
                    to_remove.append(RemoveMessage(id=msg.id))
            elif isinstance(msg, ToolMessage):
                if self._should_remove_tool_message(msg):
                    to_remove.append(RemoveMessage(id=msg.id))
        return to_remove

    async def aafter_agent(
        self,
        state: AgentState,
        runtime: Runtime[ContextSchema]
    ) -> dict[str, Any] | None:
        """Filter tool messages from the last completed turn."""
        messages = state["messages"]
        if not messages:
            return None

        last_group = self._find_last_group(messages)
        to_remove = self._get_messages_to_remove(last_group)

        if not to_remove:
            return None

        try:
            config = get_config()
            thread_id = config.get("configurable", {}).get(
                "thread_id", "unknown"
            )
        except RuntimeError:
            thread_id = "unknown"

        logger.debug("ToolResultMemoryFilterMiddleware: "
                     "removing %d messages from thread %s",
                     len(to_remove),
                     thread_id)

        return {"messages": to_remove}