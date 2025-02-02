
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class PurchaseCreateMinimal(BaseModel):
	""" A data type for creating a purchase """
	user_id: int
	price: Decimal
	receipt_lottery_number: str
	purchase_time: datetime

class PurchaseCreate(BaseModel):
	""" A data type for creating a purchase """
	user_id: int
	items: str
	price: Decimal
	currency: str
	location: str
	payment_method: str
	receipt_lottery_number: str
	purchase_time: datetime
