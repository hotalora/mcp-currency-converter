import logging
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from domain.model.error import AgentInitializationError
from infrastructure.driven_adapters.llm_auth.llm_auth_adapter import (
    LlmAuthAdapter
)
# --- BEGIN VALKEY_AGENT_IMPORT ---
from infrastructure.driven_adapters.checkpointer.checkpointer_repository import (
    CheckpointerRepository
)
# --- END VALKEY_AGENT_IMPORT ---
from infrastructure.driven_adapters.langgraph_agent.models import ContextSchema
from infrastructure.driven_adapters.langgraph_agent.helpers import (
    create_injected_tool
)
from infrastructure.driven_adapters.langgraph_agent.middlewares import (
    ToolModifyArgsMiddleware,
    DeleteOldMessagesMiddleware,
    ToolResultMemoryFilterMiddleware,
    ApiKeyRefreshMiddleware,
    ToolEarlyExitMiddleware,
    DynamicDatePromptMiddleware,
)

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating LangGraph agents with full middleware stack."""

    def __init__(self,
                 llm_config: dict,
                 llm_auth: LlmAuthAdapter,
                 # --- BEGIN VALKEY_AGENT_PARAM ---
                 checkpointer: CheckpointerRepository,
                 # --- END VALKEY_AGENT_PARAM ---
                 mcp_connections: list,
                 agent_instructions: str):
        self.llm_config = llm_config
        self.llm_auth = llm_auth
        # --- BEGIN VALKEY_AGENT_ATTR ---
        self.checkpointer = checkpointer
        # --- END VALKEY_AGENT_ATTR ---
        self.mcp_connections = mcp_connections
        self.agent_instructions = agent_instructions

    async def initialize_agent(self, mcp_headers: dict[str, str] | None = None):
        """Initialize the LangGraph agent with middlewares."""
        try:
            tools = await self._get_tools(mcp_headers)
            api_key = await self.llm_auth.get_api_key()
            llm = ChatOpenAI(
                model=self.llm_config.get("model_name", "gpt-4o-mini"),
                temperature=self.llm_config.get("temperature", 0.7),
                api_key=api_key,
                base_url=self.llm_config.get("base_url", ""),
                timeout=self.llm_config.get("timeout", 30),
            )

            dynamic_date_prompt_middleware = DynamicDatePromptMiddleware(
                timezone=self.llm_config.get("timezone", "America/Bogota")
            )
            tool_early_exit_middleware = ToolEarlyExitMiddleware(
                self.llm_config.get("early_exit_tools", []),
                self.llm_config.get("success_keywords", []),
            )
            tool_result_mem_filter_middleware = ToolResultMemoryFilterMiddleware(
                self.llm_config.get("memory_excluded_tools", [])
            )
            api_key_refresh_middleware = ApiKeyRefreshMiddleware(self.llm_auth)
            delete_old_messages_middleware = DeleteOldMessagesMiddleware(
                max_messages_to_keep=self.llm_config.get(
                    "max_messages_to_keep", 20
                )
            )

            # --- BEGIN VALKEY_AGENT_CHECKPOINTER ---
            checkpointer = None
            if self.checkpointer is not None:
                ttl = self.llm_config.get("message_retention_minutes", 600)
                checkpointer = await self.checkpointer.get_checkpointer(ttl=ttl)
            # --- END VALKEY_AGENT_CHECKPOINTER ---

            agent = create_agent(
                model=llm,
                tools=tools,
                system_prompt=self.agent_instructions,
                middleware=[
                    dynamic_date_prompt_middleware,
                    ToolModifyArgsMiddleware(),
                    tool_early_exit_middleware,
                    api_key_refresh_middleware,
                    tool_result_mem_filter_middleware,
                    delete_old_messages_middleware,
                ],
                context_schema=ContextSchema,
                # --- BEGIN VALKEY_AGENT_KWARG ---
                checkpointer=checkpointer,
                # --- END VALKEY_AGENT_KWARG ---
            )
            logger.info("Agent initialized successfully")
            return agent

        except Exception as e:
            logger.error("Error initializing agent: %s", e)
            raise AgentInitializationError(
                f"Failed to initialize agent: {e}"
            ) from e

    async def _get_tools(
        self,
        mcp_headers: dict[str, str] | None = None,
    ) -> list:
        """Get tools from configured MCP servers."""
        if not self.mcp_connections:
            logger.warning("No MCP connections configured.")
            return []
        try:
            mcp_config = {}
            for conn in self.mcp_connections:
                name = conn.get("name", "unknown")
                endpoint = conn.get("endpoint", "")
                mcp_config[name] = {
                    "transport": "streamable_http",
                    "url": endpoint,
                    "headers": mcp_headers or {},
                }

            client = MultiServerMCPClient(mcp_config)
            tools = await client.get_tools()

            context_fields = set(ContextSchema.model_fields.keys())
            wrapped_tools = [
                create_injected_tool(tool, context_fields) for tool in tools
            ]
            logger.info("Fetched %d tools from MCP servers", len(wrapped_tools))
            return wrapped_tools

        except ExceptionGroup as eg:
            for exc in eg.exceptions:
                if isinstance(exc, ExceptionGroup):
                    for inner_exc in exc.exceptions:
                        logger.error("MCP Inner Exception: %s", inner_exc)
                    continue
                logger.error("MCP Error Fetching Tools: %s", exc)
            raise AgentInitializationError(
                "Failed to initialize agent tools"
            ) from eg
        except Exception as e:
            logger.error("Error fetching MCP tools: %s", e)
            raise AgentInitializationError(
                "Failed to retrieve tools from configured MCP servers."
            ) from e