"""Input validation and sanitization helpers for AquaDash orders."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any

from config import (
    MAX_QUANTITY,
    MIN_QUANTITY,
    SLOT_MAP,
    is_past_date,
    is_slot_closed,
    parse_date_str,
)

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PHONE_PATTERN = re.compile(r"^[0-9+\-\s()]{7,20}$")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class ValidationError(Exception):
    def __init__(self, message: str, code: str = "VALIDATION_ERROR", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def validate_date_str(date_str: Any) -> str:
    if not isinstance(date_str, str) or not DATE_PATTERN.match(date_str.strip()):
        raise ValidationError("Invalid date format. Expected YYYY-MM-DD.", code="INVALID_DATE")
    cleaned = date_str.strip()
    try:
        parse_date_str(cleaned)
    except ValueError as exc:
        raise ValidationError("Invalid calendar date.", code="INVALID_DATE") from exc
    return cleaned


def validate_slot_id(slot_id: Any) -> str:
    if not isinstance(slot_id, str) or slot_id.strip() not in SLOT_MAP:
        raise ValidationError("Invalid delivery time slot.", code="INVALID_SLOT")
    return slot_id.strip()


def validate_order_id(order_id: Any) -> str:
    if not isinstance(order_id, str) or not REQUEST_ID_PATTERN.match(order_id.strip()):
        raise ValidationError("Invalid order ID.", code="INVALID_ORDER_ID")
    return order_id.strip()


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())


def validate_order_payload(body: Any, now: datetime | None = None) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object.")

    date_str = validate_date_str(body.get("date"))
    if is_past_date(date_str, now=now):
        raise ValidationError(
            "Cannot place an order for a past date.",
            code="PAST_DATE",
            status_code=400,
        )

    slot_id = validate_slot_id(body.get("slot_id"))
    if is_slot_closed(date_str, slot_id, now=now):
        raise ValidationError(
            "This delivery time slot has already closed. Please choose another slot.",
            code="SLOT_CLOSED",
            status_code=409,
        )

    customer_name = _clean_text(body.get("customer_name"))
    if len(customer_name) < 2 or len(customer_name) > 100:
        raise ValidationError("Customer name must be between 2 and 100 characters.")

    address = _clean_text(body.get("address"))
    if len(address) < 5 or len(address) > 300:
        raise ValidationError("Home address must be between 5 and 300 characters.")

    phone = _clean_text(body.get("phone"))
    if not PHONE_PATTERN.match(phone):
        raise ValidationError("Please enter a valid contact number (7-20 digits).")

    raw_qty = body.get("quantity")
    if isinstance(raw_qty, bool) or not isinstance(raw_qty, int):
        raise ValidationError(f"Quantity must be a whole number between {MIN_QUANTITY} and {MAX_QUANTITY}.")
    if raw_qty < MIN_QUANTITY or raw_qty > MAX_QUANTITY:
        raise ValidationError(f"Quantity must be between {MIN_QUANTITY} and {MAX_QUANTITY} containers.")

    notes = _clean_text(body.get("notes", ""))
    if len(notes) > 250:
        raise ValidationError("Delivery notes must be 250 characters or fewer.")

    raw_req_id = body.get("client_request_id")
    if raw_req_id is None or raw_req_id == "":
        order_id = uuid.uuid4().hex[:16]
    else:
        if not isinstance(raw_req_id, str) or not REQUEST_ID_PATTERN.match(raw_req_id.strip()):
            raise ValidationError("Invalid client_request_id format.", code="INVALID_REQUEST_ID")
        order_id = raw_req_id.strip()

    return {
        "order_id": order_id,
        "date": date_str,
        "slot_id": slot_id,
        "customer_name": customer_name,
        "address": address,
        "phone": phone,
        "quantity": raw_qty,
        "notes": notes,
    }
