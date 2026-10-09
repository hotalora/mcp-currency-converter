from abc import ABC, abstractmethod
from typing import Dict, Any
from domain.model.agent_message.agent_message_model import MessageType


class AgentGateway(ABC):
    """Abstract gateway for AI agent operations."""

    @abstractmethod
    async def process_message(self,
                              user_message: str,
                              metadata: Dict[str, Any]) -> list[MessageType]:
        """Process a user message through the AI agent.

        Args:
            user_message: The user's input message.
            metadata: Metadata for the conversation.

        Returns:
            List of MessageType with the agent's response.
        """
