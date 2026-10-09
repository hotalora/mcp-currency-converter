import pytest
from unittest.mock import AsyncMock, MagicMock
from infrastructure.driven_adapters.langgraph_agent.middlewares.tool_modify_args_middleware import (
    ToolModifyArgsMiddleware,
)
from infrastructure.driven_adapters.langgraph_agent.models import ContextSchema


def test_instantiation():
    assert ToolModifyArgsMiddleware() is not None


@pytest.mark.asyncio
async def test_bypass_when_tool_is_none():
    mw = ToolModifyArgsMiddleware()
    request = MagicMock()
    request.tool = None
    handler = AsyncMock(return_value="result")

    result = await mw.awrap_tool_call(request, handler)
    assert result == "result"


@pytest.mark.asyncio
async def test_bypass_when_args_schema_is_none():
    mw = ToolModifyArgsMiddleware()
    request = MagicMock()
    request.tool.args_schema = None
    handler = AsyncMock(return_value="result")

    result = await mw.awrap_tool_call(request, handler)
    assert result == "result"


@pytest.mark.asyncio
async def test_bypass_when_args_schema_is_dict():
    mw = ToolModifyArgsMiddleware()
    request = MagicMock()
    request.tool.args_schema = {"type": "object"}
    handler = AsyncMock(return_value="result")

    result = await mw.awrap_tool_call(request, handler)
    assert result == "result"


@pytest.mark.asyncio
async def test_bypass_when_context_not_schema():
    mw = ToolModifyArgsMiddleware()
    request = MagicMock()
    request.tool.args_schema = MagicMock()
    request.tool.args_schema.model_fields = {"userIdentifier": MagicMock()}
    request.runtime.context = "not a ContextSchema"
    handler = AsyncMock(return_value="result")

    result = await mw.awrap_tool_call(request, handler)
    assert result == "result"


@pytest.mark.asyncio
async def test_injects_context_fields():
    mw = ToolModifyArgsMiddleware()
    request = MagicMock()
    schema = MagicMock()
    schema.model_fields = {"userIdentifier": MagicMock(), "query": MagicMock()}
    request.tool.args_schema = schema
    request.tool.args_schema.model_fields = schema.model_fields
    context = ContextSchema(userIdentifier="user1", applicationIdentifier="app1")
    request.runtime.context = context
    request.tool_call = {"args": {"query": "search"}}
    handler = AsyncMock(return_value="injected")

    result = await mw.awrap_tool_call(request, handler)
    assert result == "injected"
    assert request.tool_call["args"]["userIdentifier"] == "user1"
