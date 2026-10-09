
import logging
from typing import Dict, Any, Optional, List
from src.domain.model.CurrencyConverter.gateways.CurrencyConverter_adapter import CurrencyconverterAdapter
from src.domain.model.CurrencyConverter.CurrencyConverter_model import CurrencyconverterResponse
from src.domain.model.errors.CurrencyConverter_error import CurrencyconverterError
from src.infrastructure.driven_adapters.api_connect_adapter.adapter.api_connect_adapter import ApiConnectAdapter
from src.infrastructure.driven_adapters.api_connect_adapter.errors import ApiConnectError

class CurrencyconverterApiAdapter(CurrencyconverterAdapter):
    """Implementación del adaptador para 'CurrencyConverter' usando ApiConnectAdapter genérico."""

    def __init__(self, config: Dict[str, Any], api_adapter: ApiConnectAdapter):
        self.endpoint = config.get("CurrencyConverter_endpoint", "")
        if not self.endpoint:
             logging.warning(f"Endpoint para 'CurrencyConverter' no encontrado en la configuración.")
        self.api_adapter = api_adapter
        self.logger = logging.getLogger(__name__)

    async def CurrencyConverter(self, currency_from: str) -> CurrencyconverterResponse:
        """Implementación de 'CurrencyConverter' que consume la API via API Connect."""
        self.logger.info(f"Iniciando llamada a API para 'CurrencyConverter' en endpoint: {self.endpoint}")
        if not self.endpoint:
             raise CurrencyconverterError("Endpoint no configurado para la operación 'CurrencyConverter'.")

        try:
            api_params = { currency_from }
            self.logger.debug(f"Parámetros para GET 'CurrencyConverter': {api_params}")
            result = await self.api_adapter.make_get_request(self.endpoint, params=api_params)

            await self.api_adapter.handle_api_error(result)
            response_data = result.get("body", {}).get("data", None)

            if response_data is None:
                 self.logger.warning(f"Respuesta de API para 'CurrencyConverter' no contenía 'data'. Respuesta recibida: {result.get('body')}")
                 raise CurrencyconverterError(f"Respuesta inesperada de API para 'CurrencyConverter', campo 'data' ausente.")

            try:
                parsed_response = CurrencyconverterResponse(**response_data)
                self.logger.info(f"API call para 'CurrencyConverter' exitosa.")
                return parsed_response
            except Exception as pydantic_error:
                self.logger.error(f"Error al validar respuesta de API para 'CurrencyConverter' con Pydantic: {pydantic_error}", exc_info=True)
                raise CurrencyconverterError(f"Formato de respuesta inválido de API para 'CurrencyConverter'.") from pydantic_error

        except ApiConnectError as e:
            self.logger.error(f"Error de API Connect en 'CurrencyConverter': {e}", exc_info=False)
            raise CurrencyconverterError(f"Fallo la comunicación con API para 'CurrencyConverter': {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Error inesperado en CurrencyconverterApiAdapter (CurrencyConverter): {e}", exc_info=True)
            raise CurrencyconverterError(f"Error inesperado en adaptador para 'CurrencyConverter': {str(e)}") from e
