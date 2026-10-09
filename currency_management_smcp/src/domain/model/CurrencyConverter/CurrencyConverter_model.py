
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class CurrencyconverterResponse(BaseModel):
    success: bool
    amount: Decimal = Field(gt=0)
    from_currency: str
    converted_amount: Decimal
    to_currency: str
    exchange_rate: Decimal = Field(gt=0)
    rate_date: date
