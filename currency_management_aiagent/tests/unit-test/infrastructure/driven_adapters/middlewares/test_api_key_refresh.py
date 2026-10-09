import pytest
from unittest.mock import AsyncMock, MagicMock
from openai import AuthenticationError
from infrastructure.driven_adapters.langgraph_agent.middlewares.api_key_refresh_middleware import (
    ApiKeyRefreshMiddleware,
)


def test_stores_auth():
    auth = MagicMock()
    assert ApiKeyRefreshMiddleware(auth).llm_auth is auth


@pytest.mark.asyncio
async def test_success_no_refresh():
    auth = MagicMock()
    auth.refresh_api_key = AsyncMock()
    mw = ApiKeyRefreshMiddleware(auth)
    handler = AsyncMock(return_value="ok")
    request = MagicMock()

    result = await mw.awrap_model_call(request, handler)
    assert result == "ok"
    auth.refresh_api_key.assert_not_awaited()


@pytest.mark.asyncio
async def test_auth_error_triggers_refresh():
    auth = MagicMock()
    auth.refresh_api_key = AsyncMock()
    mw = ApiKeyRefreshMiddleware(auth)

    call_count = 0
    async def handler_with_retry(req):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise AuthenticationError(
                message="invalid key",
                response=MagicMock(status_code=401),
                body=None,
            )
        return "ok after refresh"

    request = MagicMock()
    result = await mw.awrap_model_call(request, handler_with_retry)
    assert result == "ok after refresh"
    auth.refresh_api_key.assert_awaited_once()
