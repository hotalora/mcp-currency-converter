import logging
from domain.model.error import AgentInitializationError
from domain.model.agent_message import AgentRequest, AgentResponse
from domain.model.agent_message.gateways import AgentGateway

logger = logging.getLogger(__name__)


class ProcessAgentMessageUseCase:
    """Use case for processing messages through the AI agent."""

    def __init__(self, agent_gateway: AgentGateway):
        self.agent_gateway = agent_gateway

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Execute the use case to process a user message.

        Args:
            request: Agent request containing user message and metadata.

        Returns:
            AgentResponse with the agent's response or error information.
        """
        try:
            logger.info("Processing message for conversation: %s",
                        request.conversation_id)
            agent_response = await self.agent_gateway.process_message(
                user_message=request.user_message,
                metadata=request.metadata
            )
            logger.info("Successfully processed message for conversation: %s",
                        request.conversation_id)
            return AgentResponse(
                conversation_id=request.conversation_id,
                agent_response=agent_response,
                status="success",
                error_message=None,
                metadata=request.metadata,
            )
        except AgentInitializationError as e:
            logger.error("Error processing message for conversation %s: %s",
                         request.conversation_id, str(e))
            return AgentResponse(
                conversation_id=request.conversation_id,
                agent_response=[],
                status="error",
                error_message=str(e),
                metadata=request.metadata,
            )
