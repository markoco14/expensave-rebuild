from datetime import datetime, timedelta, timezone
from typing import Tuple
from zoneinfo import ZoneInfo


def get_local_today():
    """
    Returns todays date localized to the user's timezone
    """
    today_utc = datetime.now(timezone.utc)
    return today_utc.astimezone(ZoneInfo("Asia/Taipei"))


def get_today_utc_range(local_today: datetime) -> Tuple[datetime, datetime]:
    """
    Returns a tuple like start_of_period, end_of_period.
    Takes your local range and 
    """
    local_start_of_day = local_today.replace(hour=0, minute=0, second=0)
    utc_start_of_day =  local_start_of_day.astimezone(timezone.utc)

    local_start_of_tomorrow = local_start_of_day + timedelta(days=1)
    utc_start_of_tomorrow =  local_start_of_tomorrow.astimezone(timezone.utc) 

    return utc_start_of_day, utc_start_of_tomorrow