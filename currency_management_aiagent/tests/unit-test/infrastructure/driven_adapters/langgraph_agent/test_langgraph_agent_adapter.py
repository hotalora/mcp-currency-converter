import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.driven_adapters.langgraph_agent.adapter.langgraph_agent_adapter import (
    LangGraphAgentAdapter,
)
from domain.model.agent_message import TextMessage


@pytest.fixture
def factory():
    f = MagicMock()
    f.initialize_agent = AsyncMock(return_value=MagicMock())
    return f


@pytest.fixture
def adapter(factory):
    return LangGraphAgentAdapter(agent_factory=factory)


@pytest.mark.asyncio
async def test_initialize(adapter, factory):
    await adapter.initialize()
    factory.initialize_agent.assert_awaited_once()
    assert adapter.agent is not None


@pytest.mark.asyncio
async def test_not_initialized_raises():
    a = LangGraphAgentAdapter(agent_factory=MagicMock())
    with pytest.raises(RuntimeError, match="not initialized"):
        await a.process_message(user_message="hi", metadata={})


@pytest.mark.asyncio
async def test_authenticated_request_initializes_agent_with_mcp_token():
    factory = MagicMock()
    agent = AsyncMock()
    message = MagicMock()
    message.content = "converted"
    agent.ainvoke.return_value = {"messages": [message]}
    factory.initialize_agent = AsyncMock(return_value=agent)
    adapter = LangGraphAgentAdapter(agent_factory=factory)

    result = await adapter.process_message(
        user_message="convert 25 USD to EUR",
        metadata={"Authorization": "Bearer test-token"},
    )

    factory.initialize_agent.assert_awaited_once_with(
        mcp_headers={"Authorization": "Bearer test-token"}
    )
    agent.ainvoke.assert_awaited_once()
    assert result[0].content == "converted"


@pytest.mark.asyncio
async def test_process_message_success(adapter, factory):
    mock_agent = AsyncMock()
    mock_msg = MagicMock()
    mock_msg.content = "response text"
    mock_agent.ainvoke.return_value = {"messages": [mock_msg]}
    factory.initialize_agent.return_value = mock_agent
    await adapter.initialize()

    result = await adapter.process_message(
        user_message="hello",
        metadata={"UserIdentifier": "user1", "ApplicationIdentifier": "app1"},
    )
    assert len(result) == 1
    assert isinstance(result[0], TextMessage)
    mock_agent.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_message_uses_thread_id(adapter, factory):
    mock_agent = AsyncMock()
    mock_msg = MagicMock()
    mock_msg.content = "ok"
    mock_agent.ainvoke.return_value = {"messages": [mock_msg]}
    factory.initialize_agent.return_value = mock_agent
    await adapter.initialize()

    await adapter.process_message(
        user_message="hi",
        metadata={"UserIdentifier": "u1", "ApplicationIdentifier": "a1"},
    )
    call_args = mock_agent.ainvoke.call_args
    config = call_args[0][1]
    assert config["configurable"]["thread_id"] == "a1#u1"


@pytest.mark.asyncio
async def test_process_message_default_identifiers(adapter, factory):
    mock_agent = AsyncMock()
    mock_msg = MagicMock()
    mock_msg.content = "ok"
    mock_agent.ainvoke.return_value = {"messages": [mock_msg]}
    factory.initialize_agent.return_value = mock_agent
    await adapter.initialize()

    await adapter.process_message(user_message="hi", metadata={})
    call_args = mock_agent.ainvoke.call_args
    config = call_args[0][1]
    assert config["configurable"]["thread_id"] == "default#unknown_user"


@pytest.mark.asyncio
async def test_process_message_propagates_exception(adapter, factory):
    mock_agent = AsyncMock()
    mock_agent.ainvoke.side_effect = ValueError("LLM error")
    factory.initialize_agent.return_value = mock_agent
    await adapter.initialize()

    with pytest.raises(ValueError, match="LLM error"):
        await adapter.process_message(user_message="hi", metadata={})


@pytest.mark.asyncio
async def test_process_message_exception_group(adapter, factory):
    mock_agent = AsyncMock()
    eg = BaseExceptionGroup("group", [ValueError("sub1"), TypeError("sub2")])
    mock_agent.ainvoke.side_effect = eg
    factory.initialize_agent.return_value = mock_agent
    await adapter.initialize()

    with pytest.raises(BaseExceptionGroup):
        await adapter.process_message(user_message="hi", metadata={})


def test_generate_response_text():
    m = MagicMock(); m.content = "hello"
    r = LangGraphAgentAdapter._generate_response({"messages": [m]})
    assert isinstance(r[0], TextMessage)


def test_generate_response_is_plain_text():
    message = MagicMock()
    message.content = "¡Listo! 25 USD equivalen a 22.31 EUR."
    response = LangGraphAgentAdapter._generate_response({
        "messages": [message],
        "structured_response": MagicMock(),
    })

    assert len(response) == 1
    assert isinstance(response[0], TextMessage)
    assert response[0].content == "¡Listo! 25 USD equivalen a 22.31 EUR."


def test_generate_response_tool_msg():
    from langchain_core.messages import ToolMessage
    r = LangGraphAgentAdapter._generate_response({"messages": [ToolMessage(content="r", tool_call_id="t")]})
    assert r == []
