
from abc import ABC, abstractmethod
from decimal import Decimal
from src.domain.model.CurrencyConverter.CurrencyConverter_model import CurrencyconverterResponse

class CurrencyconverterAdapter(ABC):
    """Gateway abstracto para la operación 'CurrencyConverter'."""

    @abstractmethod
    async def CurrencyConverter(
        self,
        amount: Decimal,
        currency_from: str,
        currency_to: str,
    ) -> CurrencyconverterResponse:
        """Define el contrato para ejecutar la operación 'CurrencyConverter'."""
        raise NotImplementedError
