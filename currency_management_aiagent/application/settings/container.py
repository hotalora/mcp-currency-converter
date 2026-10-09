from dotenv import load_dotenv
load_dotenv('application/settings/.env')

from dependency_injector import containers, providers

from application.settings.settings import Config
from domain.usecase.process_agent_message_use_case import (
    ProcessAgentMessageUseCase
)
from infrastructure.driven_adapters.secrets_manager.secrets_manager_adapter import (
    SecretsManagerAdapter
)
# --- BEGIN VALKEY_IMPORTS ---
from infrastructure.driven_adapters.cache_repository.cache_repository import (
    CacheRepository
)
from infrastructure.driven_adapters.checkpointer.checkpointer_repository import (
    CheckpointerRepository
)
# --- END VALKEY_IMPORTS ---
from infrastructure.driven_adapters.llm_auth.llm_auth_adapter import (
    LlmAuthAdapter
)
from infrastructure.driven_adapters.langgraph_agent import (
    AgentFactory,
    LangGraphAgentAdapter,
)




class Container(containers.DeclarativeContainer):
    """Dependency injection container."""

    config = providers.Configuration()

    # --- AWS Secrets Manager ---
    secrets_manager_adapter = providers.Singleton(
        SecretsManagerAdapter,
        aws_config=config.aws,
    )

    # --- BEGIN VALKEY_PROVIDERS ---
    # --- Cache (Valkey/Redis) ---
    cache_repository = providers.Singleton(
        CacheRepository,
        redis_config=config.redis,
        secrets_manager=secrets_manager_adapter,
    )

    # --- Checkpointer ---
    checkpointer_repository = providers.Singleton(
        CheckpointerRepository,
        cache_repository=cache_repository,
    )
    # --- END VALKEY_PROVIDERS ---

    # --- LLM Auth ---
    llm_auth_adapter = providers.Singleton(
        LlmAuthAdapter,
        llm_config=config.llm,
        secrets_manager=secrets_manager_adapter,
    )

    # --- Agent Factory ---
    agent_factory = providers.Singleton(
        AgentFactory,
        llm_config=config.llm,
        llm_auth=llm_auth_adapter,
        # --- BEGIN VALKEY_FACTORY_ARG ---
        checkpointer=checkpointer_repository,
        # --- END VALKEY_FACTORY_ARG ---
        mcp_connections=config.mcp_connections,
        agent_instructions=config.agent_instructions,
    )

    # --- LangGraph Agent Adapter ---
    langchain_agent_adapter = providers.Singleton(
        LangGraphAgentAdapter,
        agent_factory=agent_factory,
    )

    # --- Use Case ---
    process_agent_message_use_case = providers.Factory(
        ProcessAgentMessageUseCase,
        agent_gateway=langchain_agent_adapter,
    )

