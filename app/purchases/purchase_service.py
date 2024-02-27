from typing import List
from decimal import Decimal

from app.purchases.purchase_model import DBPurchase

def calculate_day_total_spent(purchases: List[DBPurchase]) -> Decimal:
	return sum([purchase.price for purchase in purchases])