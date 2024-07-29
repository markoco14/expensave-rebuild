""" Functions for working with timezones """
from typing import List
from zoneinfo import ZoneInfo
from datetime import datetime, time, timedelta

from app.purchases.transaction_model import Transaction

# Time/Date related functions


def get_utc_start_of_day(utc_offset: int):
    """ 
    Gets the start of the day in utc
    adjusts for user's timezone
    used for retrieving purchases from the database
    """
    return datetime.combine(
        datetime.now(), time.min) - timedelta(hours=utc_offset)


def get_utc_start_of_current_day(year: int, month: int, day: int, utc_offset: int):
    """ 
    Gets the start of the day in utc
    adjusts for user's timezone
    used for retrieving purchases from the database
    """
    return datetime.combine(
        datetime(year=year, month=month, day=day), time.min) - timedelta(hours=utc_offset)


def get_utc_end_of_day(utc_offset: int):
    """ 
    Gets the end of the day in utc
    adjusts for user's timezone
    used for retrieving purchases from the database
    """
    return datetime.combine(
        datetime.now(), time.max) - timedelta(hours=utc_offset)


def get_utc_end_of_current_day(
    year: int,
    month: int,
    day: int,
    utc_offset: int
):
    """ 
    Gets the start of the day in utc
    adjusts for user's timezone
    used for retrieving purchases from the database
    """
    return datetime.combine(
        datetime(year=year, month=month, day=day), time.max) - timedelta(hours=utc_offset)

# Timezone related functions


def adjust_purchase_dates_for_local_time(
    purchases: List[Transaction],
    user_timezone: str
) -> List[Transaction]:
    """ 
    Adjust purchase times to user's local timezone

    """
    timezone = ZoneInfo(user_timezone)
    for purchase in purchases:
        purchase.purchase_time = purchase.purchase_time.astimezone(timezone)

    return purchases


# format date from datetime object for date input
def format_date_for_date_input(purchase_time: datetime) -> str:
    input_date = (purchase_time +
                        timedelta(hours=8)).strftime("%Y-%m-%d")
    return input_date
