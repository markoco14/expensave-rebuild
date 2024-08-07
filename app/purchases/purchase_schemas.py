
from decimal import Decimal
from pydantic import BaseModel




class PurchaseCreate(BaseModel):
	""" A data type for creating a purchase """
	user_id: int
	items: str
	price: Decimal
	currency: str
	location: str
	payment_method: str
