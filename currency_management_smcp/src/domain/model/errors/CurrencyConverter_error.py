
class CurrencyconverterError(Exception):
    """Excepción personalizada para errores relacionados con 'CurrencyConverter'."""
    def __init__(self, message: str = "Ocurrió un error durante la operación 'CurrencyConverter'"):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message
