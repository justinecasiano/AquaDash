"""AquaDash shared configuration and Philippine Time (UTC+8) slot helpers."""

from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta, timezone

PHT = timezone(timedelta(hours=8))

MAX_ORDERS_PER_SLOT = 15
MIN_QUANTITY = 1
MAX_QUANTITY = 20

TIME_SLOTS = [
    {"slot_id": "08:00-10:00", "label": "8:00 AM - 10:00 AM", "start_hour": 8, "end_hour": 10},
    {"slot_id": "10:00-12:00", "label": "10:00 AM - 12:00 PM", "start_hour": 10, "end_hour": 12},
    {"slot_id": "13:00-15:00", "label": "1:00 PM - 3:00 PM", "start_hour": 13, "end_hour": 15},
    {"slot_id": "15:00-17:00", "label": "3:00 PM - 5:00 PM", "start_hour": 15, "end_hour": 17},
    {"slot_id": "17:00-19:00", "label": "5:00 PM - 7:00 PM", "start_hour": 17, "end_hour": 19},
]

SLOT_MAP = {slot["slot_id"]: slot for slot in TIME_SLOTS}


def get_table_name() -> str:
    return os.environ.get("TABLE_NAME", "umak-elec3-bcsad-g02-orders")


def get_staff_api_key() -> str:
    return os.environ.get("STAFF_API_KEY", "")


def get_allowed_origin() -> str:
    return os.environ.get("ALLOWED_ORIGIN", "*")


def now_pht(now: datetime | None = None) -> datetime:
    if now is None:
        return datetime.now(PHT)
    if now.tzinfo is None:
        return now.replace(tzinfo=PHT)
    return now.astimezone(PHT)


def today_pht_str(now: datetime | None = None) -> str:
    return now_pht(now).date().isoformat()


def tomorrow_pht_str(now: datetime | None = None) -> str:
    return (now_pht(now).date() + timedelta(days=1)).isoformat()


def parse_date_str(date_str: str) -> date:
    return date.fromisoformat(date_str)


def is_past_date(date_str: str, now: datetime | None = None) -> bool:
    return parse_date_str(date_str) < now_pht(now).date()


def is_slot_closed(date_str: str, slot_id: str, now: datetime | None = None) -> bool:
    """Return True if the delivery slot window has already ended in PHT."""
    current = now_pht(now)
    target_date = parse_date_str(date_str)
    if target_date < current.date():
        return True
    if target_date > current.date():
        return False

    slot = SLOT_MAP[slot_id]
    slot_end = datetime.combine(target_date, time(hour=slot["end_hour"], minute=0), tzinfo=PHT)
    return current >= slot_end


def all_slots_closed_for_date(date_str: str, now: datetime | None = None) -> bool:
    return all(is_slot_closed(date_str, s["slot_id"], now=now) for s in TIME_SLOTS)


def default_active_date_and_slot(now: datetime | None = None) -> tuple[str, str]:
    """Pick the current active (or next upcoming) PHT slot; roll to tomorrow after 19:00."""
    current = now_pht(now)
    today_str = current.date().isoformat()
    for slot in TIME_SLOTS:
        if not is_slot_closed(today_str, slot["slot_id"], now=current):
            return today_str, slot["slot_id"]
    return tomorrow_pht_str(current), TIME_SLOTS[0]["slot_id"]
