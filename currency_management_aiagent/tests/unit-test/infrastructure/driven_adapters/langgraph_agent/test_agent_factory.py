import inspect
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from domain.model.error import AgentInitializationError
from infrastructure.driven_adapters.langgraph_agent.operations.agent_factory import AgentFactory

HAS_CHECKPOINTER = 'checkpointer' in inspect.signature(AgentFactory.__init__).parameters

def _make_factory(**overrides):
    llm_auth = MagicMock()
    llm_auth.get_api_key = AsyncMock(return_value="sk-test")
    kwargs = dict(
        llm_config={"model_name": "gpt-4o-mini", "temperature": 0.7, "timeout": 30,
                     "timezone": "UTC", "early_exit_tools": [], "success_keywords": [],
                     "memory_excluded_tools": [], "max_messages_to_keep": 20,
                     "message_retention_minutes": 600, "base_url": ""},
        llm_auth=llm_auth,
        mcp_connections=[],
        agent_instructions="You are helpful.",
    )
    if HAS_CHECKPOINTER:
        cp = MagicMock()
        cp.get_checkpointer = AsyncMock(return_value=MagicMock())
        kwargs["checkpointer"] = cp
    kwargs.update(overrides)
    return AgentFactory(**kwargs)

@pytest.fixture
def factory():
    return _make_factory()


@pytest.mark.asyncio
async def test_initialize_no_mcp(factory):
    with patch("infrastructure.driven_adapters.langgraph_agent.operations.agent_factory.ChatOpenAI"), \
         patch("infrastructure.driven_adapters.langgraph_agent.operations.agent_factory.create_agent") as mock_create:
        mock_create.return_value = MagicMock()
        agent = await factory.initialize_agent()
        assert agent is not None
        mock_create.assert_called_once()
        assert "response_format" not in mock_create.call_args.kwargs
        factory.llm_auth.get_api_key.assert_awaited_once()


@pytest.mark.asyncio
async def test_initialize_with_mcp():
    f = _make_factory(
        mcp_connections=[{"name": "test_mcp", "endpoint": "http://localhost:3000"}],
    )
    with patch("infrastructure.driven_adapters.langgraph_agent.operations.agent_factory.ChatOpenAI"), \
         patch("infrastructure.driven_adapters.langgraph_agent.operations.agent_factory.create_agent") as mock_create, \
         patch("infrastructure.driven_adapters.langgraph_agent.operations.agent_factory.MultiServerMCPClient") as MockMCP:
        mock_client = AsyncMock()
        mock_client.get_tools = AsyncMock(return_value=[])
        MockMCP.return_value = mock_client
        mock_create.return_value = MagicMock()

        agent = await f.initialize_agent()
        assert agent is not None
        mock_client.get_tools.assert_awaited_once()


@pytest.mark.asyncio
async def test_initialize_error_raises(factory):
    with patch("infrastructure.driven_adapters.langgraph_agent.operations.agent_factory.ChatOpenAI",
               side_effect=Exception("LLM init failed")):
        with pytest.raises(AgentInitializationError, match="Failed to initialize"):
            await factory.initialize_agent()


@pytest.mark.asyncio
async def test_get_tools_empty_connections(factory):
    tools = await factory._get_tools()
    assert tools == []


@pytest.mark.asyncio
async def test_get_tools_exception_group():
    f = _make_factory(
        mcp_connections=[{"name": "bad", "endpoint": "http://fail"}],
    )
    with patch("infrastructure.driven_adapters.langgraph_agent.operations.agent_factory.MultiServerMCPClient") as MockMCP:
        mock_client = AsyncMock()
        mock_client.get_tools = AsyncMock(
            side_effect=ExceptionGroup("mcp errors", [ConnectionError("fail")])
        )
        MockMCP.return_value = mock_client
        with pytest.raises(AgentInitializationError):
            await f._get_tools()


@pytest.mark.asyncio
async def test_get_tools_generic_exception_raises():
    f = _make_factory(
        mcp_connections=[{"name": "bad", "endpoint": "http://fail"}],
    )
    with patch("infrastructure.driven_adapters.langgraph_agent.operations.agent_factory.MultiServerMCPClient") as MockMCP:
        mock_client = AsyncMock()
        mock_client.get_tools = AsyncMock(side_effect=RuntimeError("timeout"))
        MockMCP.return_value = mock_client
        with pytest.raises(AgentInitializationError):
            await f._get_tools()
