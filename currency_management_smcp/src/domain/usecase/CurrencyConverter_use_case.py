
import logging
from decimal import Decimal
from src.domain.model.CurrencyConverter.gateways.CurrencyConverter_adapter import CurrencyconverterAdapter
from src.domain.model.CurrencyConverter.CurrencyConverter_model import CurrencyconverterResponse
from src.domain.model.errors.CurrencyConverter_error import CurrencyconverterError

logger = logging.getLogger(__name__)

class CurrencyconverterUseCase:
    """Caso de uso para orquestar la operación 'CurrencyConverter'."""

    def __init__(self, CurrencyConverter_adapter: CurrencyconverterAdapter):
        self._CurrencyConverter_adapter = CurrencyConverter_adapter

    async def execute(
        self,
        amount: Decimal,
        currency_from: str,
        currency_to: str,
    ) -> CurrencyconverterResponse:
        """Ejecuta la lógica de negocio para 'CurrencyConverter'."""
        logger.info(f"Ejecutando caso de uso 'CurrencyConverter'...")
        try:
            result = await self._CurrencyConverter_adapter.CurrencyConverter(
                amount=amount,
                currency_from=currency_from,
                currency_to=currency_to,
            )
            logger.info(f"Caso de uso 'CurrencyConverter' ejecutado exitosamente.")
            return result
        except CurrencyconverterError as e:
             logger.error(f"Error de dominio en 'CurrencyConverter': {e}", exc_info=True)
             raise
        except Exception as e:
            logger.error(f"Error inesperado en CurrencyconverterUseCase ejecutando 'CurrencyConverter': {e}", exc_info=True)
            raise CurrencyconverterError(f"Fallo inesperado al ejecutar 'CurrencyConverter': {str(e)}") from e
