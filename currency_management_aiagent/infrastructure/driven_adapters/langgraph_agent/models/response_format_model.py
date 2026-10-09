from pydantic import BaseModel
from domain.model.agent_message.agent_message_model import MessageType


class ResponseFormat(BaseModel):
    """Schema for response format to the agent."""
    messages: list[MessageType]