from pydantic import BaseModel


class ContextSchema(BaseModel):
    """Schema for context-based tool parameters."""
    userIdentifier: str
    applicationIdentifier: str
