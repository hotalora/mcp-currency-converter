import pytest
from unittest.mock import AsyncMock, MagicMock
from infrastructure.driven_adapters.llm_auth.llm_auth_adapter import LlmAuthAdapter


@pytest.fixture
def secrets_manager():
    sm = MagicMock()
    sm.get_secret = AsyncMock(return_value={"api_key": "sk-test-123"})
    return sm


@pytest.fixture
def adapter(secrets_manager):
    return LlmAuthAdapter(
        llm_config={"secret_name": "my-secret", "secret_field": "api_key"},
        secrets_manager=secrets_manager,
    )


@pytest.mark.asyncio
async def test_get_api_key(adapter, secrets_manager):
    key = await adapter.get_api_key()
    assert key == "sk-test-123"
    secrets_manager.get_secret.assert_awaited_once_with("my-secret", use_cache=False)


@pytest.mark.asyncio
async def test_caches_api_key(adapter, secrets_manager):
    await adapter.get_api_key()
    await adapter.get_api_key()
    assert secrets_manager.get_secret.await_count == 1


@pytest.mark.asyncio
async def test_refresh_api_key(adapter, secrets_manager):
    await adapter.get_api_key()
    secrets_manager.get_secret.return_value = {"api_key": "sk-refreshed"}
    await adapter.refresh_api_key()
    assert adapter._cached_api_key == "sk-refreshed"
    assert secrets_manager.get_secret.await_count == 2


@pytest.mark.asyncio
async def test_returns_not_found_when_field_missing(secrets_manager):
    secrets_manager.get_secret = AsyncMock(return_value={"other_field": "val"})
    adapter = LlmAuthAdapter(
        llm_config={"secret_name": "s", "secret_field": "api_key"},
        secrets_manager=secrets_manager,
    )
    key = await adapter.retrieve_llm_api_key()
    assert key == "NOT_FOUND"


@pytest.mark.asyncio
async def test_concurrent_get_api_key(adapter, secrets_manager):
    """Double-checked locking: only one call to secrets even under concurrency."""
    import asyncio
    results = await asyncio.gather(adapter.get_api_key(), adapter.get_api_key())
    assert all(r == "sk-test-123" for r in results)
    assert secrets_manager.get_secret.await_count == 1
