""" Functions for working with timezones """
from typing import List
from zoneinfo import ZoneInfo

from app.purchases.purchase_model import DBPurchase

def adjust_purchase_dates_for_local_time(
    purchases: List[DBPurchase],
    user_timezone: str
    ) -> List[DBPurchase]:
    """ 
    Adjust purchase times to user's local timezone
    
    """
    timezone = ZoneInfo(user_timezone)
    for purchase in purchases:
        purchase.purchase_time = purchase.purchase_time.astimezone(timezone)
    
    return purchases 