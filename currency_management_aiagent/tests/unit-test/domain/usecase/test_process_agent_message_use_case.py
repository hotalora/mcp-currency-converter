import pytest
from unittest.mock import AsyncMock
from domain.usecase.process_agent_message_use_case import ProcessAgentMessageUseCase
from domain.model.agent_message import AgentRequest, TextMessage
from domain.model.error import AgentInitializationError


@pytest.fixture
def gateway():
    return AsyncMock()


@pytest.fixture
def use_case(gateway):
    return ProcessAgentMessageUseCase(agent_gateway=gateway)


@pytest.fixture
def request_obj():
    return AgentRequest(
        conversation_id="conv-1", user_message="hola",
        metadata={"UserIdentifier": "u1", "ApplicationIdentifier": "app1"},
    )


@pytest.mark.asyncio
async def test_success(use_case, gateway, request_obj):
    gateway.process_message.return_value = [TextMessage(content="respuesta")]
    result = await use_case.execute(request_obj)
    assert result.status == "success"
    assert result.conversation_id == "conv-1"
    assert len(result.agent_response) == 1
    assert result.agent_response[0].content == "respuesta"
    gateway.process_message.assert_awaited_once_with(
        user_message="hola",
        metadata=request_obj.metadata,
    )


@pytest.mark.asyncio
async def test_agent_initialization_error(use_case, gateway, request_obj):
    gateway.process_message.side_effect = AgentInitializationError("agent fail")
    result = await use_case.execute(request_obj)
    assert result.status == "error"
    assert "agent fail" in result.error_message
    assert result.agent_response == []


@pytest.mark.asyncio
async def test_preserves_metadata(use_case, gateway, request_obj):
    gateway.process_message.return_value = [TextMessage(content="ok")]
    result = await use_case.execute(request_obj)
    assert result.metadata == request_obj.metadata


@pytest.mark.asyncio
async def test_preserves_conversation_id_on_error(use_case, gateway, request_obj):
    gateway.process_message.side_effect = AgentInitializationError("fail")
    result = await use_case.execute(request_obj)
    assert result.conversation_id == "conv-1"
