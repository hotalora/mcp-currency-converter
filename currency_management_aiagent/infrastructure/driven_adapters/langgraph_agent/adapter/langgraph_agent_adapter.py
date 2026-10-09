import logging
from typing import Any, Dict
from langchain_core.messages import ToolMessage
from domain.model.agent_message.gateways import AgentGateway
from domain.model.agent_message import MessageType, TextMessage
from infrastructure.driven_adapters.langgraph_agent.models import ContextSchema
from infrastructure.driven_adapters.langgraph_agent.operations.agent_factory import (
    AgentFactory
)

logger = logging.getLogger(__name__)


class LangGraphAgentAdapter(AgentGateway):
    """Adapter for LangGraph agent integration."""

    def __init__(self, agent_factory: AgentFactory):
        self.agent_factory = agent_factory
        self.agent = None

    async def initialize(self):
        """Initialize the agent using the factory."""
        self.agent = await self.agent_factory.initialize_agent()
        logger.info("LangGraph agent adapter initialized")

    async def process_message(self,
                              user_message: str,
                              metadata: Dict[str, Any]) -> list[MessageType]:
        """Process a user message through the AI agent."""
        user_identifier = metadata.get("UserIdentifier", "unknown_user")
        app_id = metadata.get("ApplicationIdentifier", "default")

        try:
            context = ContextSchema(
                applicationIdentifier=app_id,
                userIdentifier=user_identifier,
            )
            thread_id = f"{app_id}#{user_identifier}"

            logger.info("Processing message for conversation %s: %s",
                        user_identifier,
                        user_message[:50] + "..."
                        if len(user_message) > 50 else user_message)

            access_token = metadata.get("Authorization")
            agent = self.agent
            if access_token:
                agent = await self.agent_factory.initialize_agent(
                    mcp_headers={"Authorization": access_token}
                )
            elif agent is None:
                raise RuntimeError("Agent not initialized. Call initialize() first.")
            if agent is None:
                raise RuntimeError("Agent not initialized.")

            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": user_message}]},
                {"configurable": {"thread_id": thread_id}},
                context=context,
            )

            response = self._generate_response(result)
            logger.info("Agent response for conversation %s: %s",
                        user_identifier,
                        str(response)[:50] + "..."
                        if len(str(response)) > 50 else str(response))
            return response

        except BaseException as e:
            if isinstance(e, BaseExceptionGroup):
                logger.error(
                    "ExceptionGroup error for conversation %s. "
                    "Sub-exceptions: %d",
                    user_identifier,
                    len(e.exceptions),
                )
                for idx, sub_exc in enumerate(e.exceptions):
                    logger.error("Sub-exception [%d]: %s - %s",
                                 idx + 1,
                                 type(sub_exc).__name__,
                                 str(sub_exc))
            else:
                logger.error("Error processing message for %s: %s",
                             user_identifier, str(e))
            raise

    @staticmethod
    def _generate_response(result) -> list[MessageType]:
        """Return the final assistant response as plain text."""
        last_message = result["messages"][-1]
        if isinstance(last_message, ToolMessage):
            return []
        return [TextMessage(content=last_message.content)]
