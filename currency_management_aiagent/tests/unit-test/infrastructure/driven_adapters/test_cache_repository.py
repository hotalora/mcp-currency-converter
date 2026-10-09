# --- BEGIN VALKEY_TEST ---
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.driven_adapters.cache_repository.cache_repository import CacheRepository


@pytest.fixture
def sm():
    m = MagicMock()
    m.get_secret = AsyncMock(return_value={"password": "pass123", "username": "user1"})
    return m


@pytest.fixture
def repo(sm):
    return CacheRepository(
        redis_config={"host": "localhost", "port": 6379, "db": 0,
                       "ssl": False, "secret_name": "redis-secret"},
        secrets_manager=sm,
    )


def test_init(repo):
    assert repo.redis is None
    assert repo.secret_name == "redis-secret"


@pytest.mark.asyncio
async def test_get_client_before_init_raises(repo):
    with pytest.raises(RuntimeError, match="Failed to initialize"):
        await repo.get_client()


@pytest.mark.asyncio
async def test_initialize_success(repo, sm):
    with patch("infrastructure.driven_adapters.cache_repository.cache_repository.AsyncRedis") as MockRedis:
        mock_instance = AsyncMock()
        mock_instance.ping = AsyncMock()
        MockRedis.return_value = mock_instance

        await repo.initialize()

        sm.get_secret.assert_awaited_once()
        mock_instance.ping.assert_awaited_once()
        assert repo.redis is not None


@pytest.mark.asyncio
async def test_get_client_after_init(repo, sm):
    with patch("infrastructure.driven_adapters.cache_repository.cache_repository.AsyncRedis") as MockRedis:
        mock_instance = AsyncMock()
        mock_instance.ping = AsyncMock()
        MockRedis.return_value = mock_instance

        await repo.initialize()
        client = await repo.get_client()
        assert client is mock_instance
# --- END VALKEY_TEST ---
