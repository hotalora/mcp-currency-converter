import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import ToolMessage
from infrastructure.driven_adapters.langgraph_agent.middlewares.tool_early_exit_middleware import (
    ToolEarlyExitMiddleware,
)


def test_empty_config():
    mw = ToolEarlyExitMiddleware([], [])
    assert mw.early_exit_tools == []


def test_with_tools():
    mw = ToolEarlyExitMiddleware(["sumar"], ["ok"])
    assert "sumar" in mw.early_exit_tools


@pytest.mark.asyncio
async def test_awrap_tool_call_non_exit_tool():
    mw = ToolEarlyExitMiddleware(["sumar"], ["exitoso"])
    result_msg = ToolMessage(content="15", tool_call_id="tc1", name="restar")
    handler = AsyncMock(return_value=result_msg)
    request = MagicMock()

    result = await mw.awrap_tool_call(request, handler)
    assert result.name == "restar"
    assert "early_exit" not in result.additional_kwargs


@pytest.mark.asyncio
async def test_awrap_tool_call_exit_tool_with_keyword():
    mw = ToolEarlyExitMiddleware(["crear_pago"], ["exitoso", "creado"])
    result_msg = ToolMessage(content="Pago creado exitoso", tool_call_id="tc1", name="crear_pago")
    handler = AsyncMock(return_value=result_msg)
    request = MagicMock()

    result = await mw.awrap_tool_call(request, handler)
    assert result.additional_kwargs.get("early_exit") is True


@pytest.mark.asyncio
async def test_awrap_tool_call_exit_tool_no_keyword():
    mw = ToolEarlyExitMiddleware(["crear_pago"], ["exitoso"])
    result_msg = ToolMessage(content="Error en pago", tool_call_id="tc1", name="crear_pago")
    handler = AsyncMock(return_value=result_msg)
    request = MagicMock()

    result = await mw.awrap_tool_call(request, handler)
    assert "early_exit" not in result.additional_kwargs


@pytest.mark.asyncio
async def test_abefore_model_with_early_exit():
    mw = ToolEarlyExitMiddleware([], [])
    tool_msg = ToolMessage(content="ok", tool_call_id="tc1", name="t")
    tool_msg.additional_kwargs["early_exit"] = True
    state = {"messages": [tool_msg]}
    runtime = MagicMock()

    result = await mw.abefore_model(state, runtime)
    assert result == {"jump_to": "end"}


@pytest.mark.asyncio
async def test_abefore_model_no_early_exit():
    mw = ToolEarlyExitMiddleware([], [])
    tool_msg = ToolMessage(content="ok", tool_call_id="tc1", name="t")
    state = {"messages": [tool_msg]}
    runtime = MagicMock()

    result = await mw.abefore_model(state, runtime)
    assert result is None


@pytest.mark.asyncio
async def test_abefore_model_empty_messages():
    mw = ToolEarlyExitMiddleware([], [])
    state = {"messages": []}
    runtime = MagicMock()
    assert await mw.abefore_model(state, runtime) is None
