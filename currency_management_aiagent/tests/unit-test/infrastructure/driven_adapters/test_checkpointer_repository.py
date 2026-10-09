# --- BEGIN VALKEY_TEST ---
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.driven_adapters.checkpointer.checkpointer_repository import CheckpointerRepository


def test_init():
    assert CheckpointerRepository(cache_repository=MagicMock()).cache_repository is not None


@pytest.mark.asyncio
async def test_get_checkpointer():
    mock_cache = MagicMock()
    mock_redis = AsyncMock()
    mock_cache.get_client = AsyncMock(return_value=mock_redis)
    repo = CheckpointerRepository(cache_repository=mock_cache)

    with patch("infrastructure.driven_adapters.checkpointer.checkpointer_repository.AsyncShallowRedisSaver") as MockSaver:
        mock_saver = MagicMock()
        MockSaver.return_value = mock_saver
        result = await repo.get_checkpointer(ttl=300)
        assert result is mock_saver
        MockSaver.assert_called_once()


@pytest.mark.asyncio
async def test_get_checkpointer_default_ttl():
    mock_cache = MagicMock()
    mock_cache.get_client = AsyncMock(return_value=AsyncMock())
    repo = CheckpointerRepository(cache_repository=mock_cache)

    with patch("infrastructure.driven_adapters.checkpointer.checkpointer_repository.AsyncShallowRedisSaver") as MockSaver:
        MockSaver.return_value = MagicMock()
        await repo.get_checkpointer()
        call_kwargs = MockSaver.call_args[1]
        assert call_kwargs["ttl"]["default_ttl"] == 600
# --- END VALKEY_TEST ---
