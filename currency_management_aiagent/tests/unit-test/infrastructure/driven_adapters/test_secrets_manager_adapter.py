import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.driven_adapters.secrets_manager.secrets_manager_adapter import SecretsManagerAdapter


@pytest.fixture
def adapter():
    return SecretsManagerAdapter(aws_config={"region_name": "us-east-1"})


def test_empty_cache(adapter):
    assert adapter._cache_secrets == {}


@pytest.mark.asyncio
async def test_cache_hit(adapter):
    adapter._cache_secrets["k"] = {"v": 1}
    assert (await adapter.get_secret("k")) == {"v": 1}


@pytest.mark.asyncio
async def test_cache_bypass(adapter):
    adapter._cache_secrets["k"] = {"v": 1}
    with pytest.raises(Exception):
        await adapter.get_secret("k", use_cache=False)


@pytest.mark.asyncio
async def test_fetches_from_aws(adapter):
    mock_client = AsyncMock()
    mock_client.get_secret_value = AsyncMock(return_value={
        "SecretString": json.dumps({"api_key": "sk-test"})
    })
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch.object(adapter._session, "create_client", return_value=mock_client):
        result = await adapter.get_secret("my-secret", use_cache=False)
    assert result == {"api_key": "sk-test"}
    assert adapter._cache_secrets["my-secret"] == {"api_key": "sk-test"}


@pytest.mark.asyncio
async def test_raises_on_missing_secret_string(adapter):
    mock_client = AsyncMock()
    mock_client.get_secret_value = AsyncMock(return_value={})
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch.object(adapter._session, "create_client", return_value=mock_client):
        with pytest.raises(ValueError, match="SecretString not found"):
            await adapter.get_secret("no-string", use_cache=False)
