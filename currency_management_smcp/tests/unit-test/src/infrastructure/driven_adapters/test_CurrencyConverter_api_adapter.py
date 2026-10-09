from datetime import date
from decimal import Decimal

import httpx
import pytest

from src.domain.model.errors.CurrencyConverter_error import CurrencyconverterError
from src.infrastructure.driven_adapters.frankfurter_adapter import (
    FrankfurterCurrencyRateAdapter,
)


@pytest.mark.asyncio
async def test_conversion_uses_frankfurter_rate_and_date():
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v2/rate/USD/EUR"
        return httpx.Response(
            200,
            json={
                "base": "USD",
                "quote": "EUR",
                "rate": 0.9234,
                "date": "2026-10-07",
            },
        )

    adapter = FrankfurterCurrencyRateAdapter(
        base_url="https://api.frankfurter.dev/v2",
        transport=httpx.MockTransport(respond),
    )

    result = await adapter.CurrencyConverter(
        amount=Decimal("10"),
        currency_from="usd",
        currency_to="eur",
    )

    assert result.amount == Decimal("10")
    assert result.from_currency == "USD"
    assert result.converted_amount == Decimal("9.2340")
    assert result.to_currency == "EUR"
    assert result.exchange_rate == Decimal("0.9234")
    assert result.rate_date == date(2026, 10, 7)


@pytest.mark.asyncio
async def test_conversion_reports_unsupported_currency_pair():
    adapter = FrankfurterCurrencyRateAdapter(
        base_url="https://api.frankfurter.dev/v2",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(404, json={"message": "not found"})
        ),
    )

    with pytest.raises(CurrencyconverterError, match="no tiene una tasa"):
        await adapter.CurrencyConverter(
            amount=Decimal("10"),
            currency_from="USD",
            currency_to="ZZZ",
        )


@pytest.mark.asyncio
async def test_conversion_rejects_invalid_amount_and_currency():
    adapter = FrankfurterCurrencyRateAdapter(
        base_url="https://api.frankfurter.dev/v2",
        transport=httpx.MockTransport(
            lambda request: pytest.fail("Invalid input must not call Frankfurter")
        ),
    )

    with pytest.raises(CurrencyconverterError, match="monto"):
        await adapter.CurrencyConverter(
            amount=Decimal("0"),
            currency_from="USD",
            currency_to="EUR",
        )

    with pytest.raises(CurrencyconverterError, match="codigo"):
        await adapter.CurrencyConverter(
            amount=Decimal("10"),
            currency_from="US",
            currency_to="EUR",
        )
