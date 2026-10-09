from typing import Literal, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request model for the /chat endpoint."""
    message: str
    conversation_id: Optional[str] = "default"


class ChatMessageResponse(BaseModel):
    """Plain-text message returned by the agent."""

    type: Literal["text"]
    content: str


class ChatResponse(BaseModel):
    """Stable response schema for the /chat endpoint."""

    conversation_id: str
    messages: list[ChatMessageResponse]
