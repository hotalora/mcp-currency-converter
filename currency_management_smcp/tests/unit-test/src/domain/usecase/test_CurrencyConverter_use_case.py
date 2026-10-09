
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from src.domain.usecase.CurrencyConverter_use_case import CurrencyconverterUseCase
from src.domain.model.CurrencyConverter.CurrencyConverter_model import CurrencyconverterResponse
from src.domain.model.CurrencyConverter.gateways.CurrencyConverter_adapter import CurrencyconverterAdapter
from src.domain.model.errors.CurrencyConverter_error import CurrencyconverterError

@pytest.fixture
def mock_adapter() -> AsyncMock:
    return AsyncMock(spec=CurrencyconverterAdapter)

@pytest.fixture
def use_case_instance(mock_adapter: AsyncMock) -> CurrencyconverterUseCase:
    return CurrencyconverterUseCase(CurrencyConverter_adapter=mock_adapter)

@pytest.mark.asyncio
async def test_CurrencyConverter_use_case_success(use_case_instance: CurrencyconverterUseCase, mock_adapter: AsyncMock):
    expected_response_data = {
        "success": True,
        "amount": Decimal("10"),
        "from_currency": "USD",
        "converted_amount": Decimal("9"),
        "to_currency": "EUR",
        "exchange_rate": Decimal("0.9"),
        "rate_date": "2026-10-07",
    }
    expected_response_object = CurrencyconverterResponse(**expected_response_data)
    mock_adapter.CurrencyConverter.return_value = expected_response_object

    result = await use_case_instance.execute(
        amount=Decimal("10"),
        currency_from="USD",
        currency_to="EUR",
    )

    assert result == expected_response_object
    mock_adapter.CurrencyConverter.assert_awaited_once_with(
        amount=Decimal("10"),
        currency_from="USD",
        currency_to="EUR",
    )

@pytest.mark.asyncio
async def test_CurrencyConverter_use_case_adapter_error(use_case_instance: CurrencyconverterUseCase, mock_adapter: AsyncMock):
    adapter_error = CurrencyconverterError("Fallo en el adapter")
    mock_adapter.CurrencyConverter.side_effect = adapter_error

    with pytest.raises(CurrencyconverterError) as exc_info:
        await use_case_instance.execute(
            amount=Decimal("10"),
            currency_from="USD",
            currency_to="EUR",
        )
    assert exc_info.value is adapter_error
    mock_adapter.CurrencyConverter.assert_awaited_once_with(
        amount=Decimal("10"),
        currency_from="USD",
        currency_to="EUR",
    )

@pytest.mark.asyncio
async def test_CurrencyConverter_use_case_unexpected_error(use_case_instance: CurrencyconverterUseCase, mock_adapter: AsyncMock):
    unexpected_error = ValueError("Algo salió mal inesperadamente")
    mock_adapter.CurrencyConverter.side_effect = unexpected_error

    with pytest.raises(CurrencyconverterError) as exc_info:
        await use_case_instance.execute(
            amount=Decimal("10"),
            currency_from="USD",
            currency_to="EUR",
        )
    assert "Fallo inesperado" in str(exc_info.value)
    assert exc_info.value.__cause__ is unexpected_error
    mock_adapter.CurrencyConverter.assert_awaited_once_with(
        amount=Decimal("10"),
        currency_from="USD",
        currency_to="EUR",
    )
