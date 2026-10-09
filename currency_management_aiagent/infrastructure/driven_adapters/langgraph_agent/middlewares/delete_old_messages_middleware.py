from typing import Any
from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain.messages import HumanMessage, RemoveMessage
from langgraph.runtime import Runtime
from infrastructure.driven_adapters.langgraph_agent.models import ContextSchema


class DeleteOldMessagesMiddleware(AgentMiddleware[AgentState, ContextSchema]):
    """Middleware to delete old messages maintaining message group integrity.

    Ensures that related messages (user, assistant, tool) are kept together
    and never orphaned when removing old messages from conversation history.
    """

    def __init__(self, max_messages_to_keep: int) -> None:
        self.max_messages_to_keep = max_messages_to_keep

    def _group_messages_by_conversation_turn(self,
                                             messages: list) -> list[list]:
        """Group messages into complete conversation turns.

        A turn consists of:
        - user message
        - one or more assistant messages (may have tool_calls)
        - one or more tool messages (if assistant made tool_calls)
        - final assistant message (response after tools)
        """
        groups = []
        current_group = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                if current_group:
                    groups.append(current_group)
                current_group = [msg]
            else:
                current_group.append(msg)
        if current_group:
            groups.append(current_group)
        return groups

    def _select_groups_to_keep(self, groups: list[list]) -> list[list]:
        """Select most recent groups that fit within max_messages limit."""
        if not groups:
            return []
        groups_to_keep = []
        message_count = 0
        for group in reversed(groups):
            group_size = len(group)
            if message_count + group_size <= self.max_messages_to_keep:
                groups_to_keep.insert(0, group)
                message_count += group_size
            else:
                break
        return groups_to_keep

    async def aafter_agent(
        self,
        state: AgentState,
        runtime: Runtime[ContextSchema]
    ) -> dict[str, Any] | None:
        """Remove old message groups to keep conversation manageable."""
        messages = state["messages"]
        if len(messages) <= self.max_messages_to_keep:
            return None
        groups = self._group_messages_by_conversation_turn(messages)
        groups_to_keep = self._select_groups_to_keep(groups)
        messages_to_keep_ids = {msg.id for group in groups_to_keep
                                for msg in group if msg.id is not None}
        messages_to_remove = [
            RemoveMessage(id=msg.id)
            for msg in messages
            if msg.id is not None and msg.id not in messages_to_keep_ids
        ]
        return {"messages": messages_to_remove} if messages_to_remove else None
