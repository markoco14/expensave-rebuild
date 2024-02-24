
from decimal import Decimal
from pydantic import BaseModel




class PurchaseCreate(BaseModel):
	""" A data type for creating a purchase """
	items: str
	price: Decimal
	currency: str
	location: str
