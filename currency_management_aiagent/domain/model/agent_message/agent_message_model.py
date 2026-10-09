from dataclasses import dataclass
from typing import Any, Dict, Optional, Union


@dataclass
class TextMessage:
    """Model for a text message."""
    content: str
    type: str = "text"


MessageType = Union[TextMessage]


@dataclass
class AgentRequest:
    """Request model for agent processing."""
    conversation_id: str
    user_message: str
    metadata: Dict[str, Any]
    user_id: Optional[str] = None


@dataclass
class AgentResponse:
    """Response model from agent processing."""
    conversation_id: str
    agent_response: list[MessageType]
    status: str
    metadata: Dict[str, Any]
    error_message: Optional[str] = None
