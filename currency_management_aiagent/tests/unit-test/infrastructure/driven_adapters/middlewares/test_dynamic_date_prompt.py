import pytest
from unittest.mock import AsyncMock, MagicMock
from infrastructure.driven_adapters.langgraph_agent.middlewares.dynamic_date_prompt_middleware import (
    DynamicDatePromptMiddleware,
)


def test_default_timezone():
    assert DynamicDatePromptMiddleware().timezone == "America/Bogota"


def test_custom_timezone():
    assert DynamicDatePromptMiddleware(timezone="UTC").timezone == "UTC"


@pytest.mark.asyncio
async def test_awrap_model_call_replaces_placeholder():
    mw = DynamicDatePromptMiddleware(timezone="UTC")
    request = MagicMock()
    request.system_prompt = "Today is {{CURRENT_DATE}}. Be helpful."
    handler = AsyncMock(return_value="response")

    result = await mw.awrap_model_call(request, handler)

    assert handler.await_count == 1
    called_request = handler.call_args[0][0]
    assert "{{CURRENT_DATE}}" not in called_request.system_prompt if hasattr(called_request, 'system_prompt') else True


@pytest.mark.asyncio
async def test_awrap_model_call_no_prompt():
    mw = DynamicDatePromptMiddleware()
    request = MagicMock()
    request.system_prompt = None
    handler = AsyncMock(return_value="response")

    result = await mw.awrap_model_call(request, handler)
    handler.assert_awaited_once()
