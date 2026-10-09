import pytest
from unittest.mock import AsyncMock, patch
from infrastructure.helpers.check_connectivity import check_connectivity


@pytest.mark.asyncio
async def test_disabled_returns_false():
    result = await check_connectivity(enabled=False)
    assert result is False


@pytest.mark.asyncio
async def test_enabled_connects():
    with patch("infrastructure.helpers.check_connectivity.asyncio.open_connection",
               new_callable=AsyncMock) as mock_conn:
        result = await check_connectivity(host="localhost", port=80, enabled=True)
        assert result is True
        mock_conn.assert_awaited_once_with("localhost", 80)
