import os
from datetime import date
from decimal import Decimal, InvalidOperation
import re

import httpx

from src.domain.model.CurrencyConverter.CurrencyConverter_model import (
    CurrencyconverterResponse,
)
from src.domain.model.CurrencyConverter.gateways.CurrencyConverter_adapter import (
    CurrencyconverterAdapter,
)
from src.domain.model.errors.CurrencyConverter_error import CurrencyconverterError


class FrankfurterCurrencyRateAdapter(CurrencyconverterAdapter):
    """Retrieve currency rates from Frankfurter and apply the conversion."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = (
            base_url or os.getenv(
                "FRANKFURTER_BASE_URL",
                "https://api.frankfurter.dev/v2",
            )
        ).rstrip("/")
        self._timeout_seconds = timeout_seconds or float(
            os.getenv("FRANKFURTER_TIMEOUT_SECONDS", "10")
        )
        self._transport = transport

    async def CurrencyConverter(
        self,
        amount: Decimal,
        currency_from: str,
        currency_to: str,
    ) -> CurrencyconverterResponse:
        source = self._normalize_currency(currency_from)
        target = self._normalize_currency(currency_to)
        value = self._parse_amount(amount)
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.get(f"{self._base_url}/rate/{source}/{target}")
                if response.status_code == 404:
                    raise CurrencyconverterError(
                        f"Frankfurter no tiene una tasa disponible para {source}/{target}."
                    )
                response.raise_for_status()
                payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object.")
            if payload.get("base") != source or payload.get("quote") != target:
                raise ValueError("Frankfurter returned a different currency pair.")
            rate = Decimal(str(payload["rate"]))
            rate_date = date.fromisoformat(payload["date"])
            if not rate.is_finite() or rate <= 0:
                raise ValueError("Exchange rate must be positive and finite.")
        except CurrencyconverterError:
            raise
        except httpx.HTTPError as error:
            raise CurrencyconverterError(
                "No fue posible consultar las tasas de Frankfurter."
            ) from error
        except (KeyError, TypeError, ValueError, InvalidOperation) as error:
            raise CurrencyconverterError(
                "Frankfurter devolvio una respuesta de tasa invalida."
            ) from error

        return CurrencyconverterResponse(
            success=True,
            amount=value,
            from_currency=source,
            converted_amount=value * rate,
            to_currency=target,
            exchange_rate=rate,
            rate_date=rate_date,
        )

    @staticmethod
    def _normalize_currency(currency: str) -> str:
        normalized = currency.strip().upper()
        if re.fullmatch(r"[A-Z]{3}", normalized, flags=re.ASCII) is None:
            raise CurrencyconverterError(
                "El codigo de cada divisa debe tener tres letras."
            )
        return normalized

    @staticmethod
    def _parse_amount(amount: Decimal) -> Decimal:
        try:
            value = Decimal(str(amount))
        except InvalidOperation as error:
            raise CurrencyconverterError(
                "El monto debe ser un numero positivo y finito."
            ) from error
        if not value.is_finite() or value <= 0:
            raise CurrencyconverterError(
                "El monto debe ser un numero positivo y finito."
            )
        return value
