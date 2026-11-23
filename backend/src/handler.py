"""AWS Lambda entrypoint for AquaDash HTTP API (API Gateway payload format 2.0)."""

from __future__ import annotations

import base64
import hmac
import json
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import unquote

from config import (
    all_slots_closed_for_date,
    default_active_date_and_slot,
    get_allowed_origin,
    get_staff_api_key,
    get_table_name,
    today_pht_str,
)
from db import (
    DuplicateOrderError,
    OrderNotFoundError,
    SlotFullError,
    TransactionConflictError,
    create_order_atomic,
    get_rider_orders,
    get_slots_summary,
    mark_order_delivered,
)
from validators import (
    ValidationError,
    validate_date_str,
    validate_order_id,
    validate_order_payload,
    validate_slot_id,
)

logger = logging.getLogger("aquadash")
logger.setLevel(logging.INFO)

DELIVER_PATH_PATTERN = re.compile(
    r"^/slots/(?P<date>[^/]+)/(?P<slot_id>[^/]+)/orders/(?P<order_id>[^/]+)/deliver$"
)

PII_KEYS = {"address", "phone", "customer_name", "notes"}


def _log_event(action: str, **fields: Any) -> None:
    """Emit structured log lines with PII fields strictly stripped."""
    safe_fields = {k: v for k, v in fields.items() if k not in PII_KEYS}
    logger.info(json.dumps({"action": action, **safe_fields}))


def _cors_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": get_allowed_origin(),
        "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Staff-Api-Key",
    }


def _response(status_code: int, body: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": "" if body is None else json.dumps(body),
    }


def _error_response(status_code: int, code: str, message: str) -> dict[str, Any]:
    return _response(status_code, {"error": code, "message": message})


def _get_header(headers: dict[str, Any] | None, target: str) -> str:
    if not headers:
        return ""
    target_lower = target.lower()
    for key, value in headers.items():
        if key.lower() == target_lower and isinstance(value, str):
            return value
    return ""


def _is_authorized_staff(headers: dict[str, Any] | None) -> bool:
    expected = get_staff_api_key()
    provided = _get_header(headers, "X-Staff-Api-Key")
    if not expected or not provided:
        return False
    return hmac.compare_digest(provided, expected)


def _normalize_path(event: dict[str, Any]) -> str:
    raw_path = event.get("rawPath") or event.get("path") or "/"
    stage = event.get("requestContext", {}).get("stage")
    if stage and stage != "$default" and raw_path.startswith(f"/{stage}/"):
        raw_path = raw_path[len(stage) + 1 :]
    if len(raw_path) > 1 and raw_path.endswith("/"):
        raw_path = raw_path.rstrip("/")
    return raw_path


def _parse_json_body(event: dict[str, Any]) -> dict[str, Any]:
    raw_body = event.get("body")
    if raw_body is None or raw_body == "":
        raise ValidationError("Request body is required.")
    if event.get("isBase64Encoded"):
        raw_body = base64.b64decode(raw_body).decode("utf-8")
    try:
        parsed = json.loads(raw_body)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValidationError("Request body must be valid JSON.", code="INVALID_JSON") from exc
    if not isinstance(parsed, dict):
        raise ValidationError("Request body must be a JSON object.", code="INVALID_JSON")
    return parsed


def handle_request(
    event: dict[str, Any],
    now: datetime | None = None,
    dynamodb_client: Any = None,
) -> dict[str, Any]:
    method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or ""
    ).upper()
    path = _normalize_path(event)
    query = event.get("queryStringParameters") or {}
    headers = event.get("headers") or {}
    table_name = get_table_name()

    if method == "OPTIONS":
        return _response(204)

    try:
        # Public: GET /slots?date=YYYY-MM-DD (aggregate slot counts only, zero PII)
        if method == "GET" and path == "/slots":
            today_str = today_pht_str(now)
            default_date, default_slot = default_active_date_and_slot(now)
            raw_date = query.get("date")
            date_str = validate_date_str(raw_date) if raw_date else today_str
            slots = get_slots_summary(table_name, date_str, now=now, client=dynamodb_client)
            _log_event("list_slots", date=date_str, slot_count=len(slots))
            return _response(
                200,
                {
                    "date": date_str,
                    "today": today_str,
                    "default_date": default_date,
                    "default_slot": default_slot,
                    "all_today_closed": all_slots_closed_for_date(today_str, now=now),
                    "slots": slots,
                },
            )

        # Public: POST /orders (atomic <= 15 orders enforcement)
        if method == "POST" and path == "/orders":
            body = _parse_json_body(event)
            order_data = validate_order_payload(body, now=now)
            receipt = create_order_atomic(table_name, order_data, now=now, client=dynamodb_client)
            _log_event(
                "create_order",
                order_id=receipt["order_id"],
                date=receipt["date"],
                slot_id=receipt["slot_id"],
                quantity=receipt["quantity"],
                status=receipt["status"],
            )
            return _response(201, {"order": receipt})

        # Staff-only: GET /rider/orders?date=YYYY-MM-DD&slot=08:00-10:00
        if method == "GET" and path == "/rider/orders":
            if not _is_authorized_staff(headers):
                _log_event("unauthorized_rider_read")
                return _error_response(401, "UNAUTHORIZED", "Valid staff API key is required.")

            default_date, default_slot = default_active_date_and_slot(now)
            date_str = validate_date_str(query.get("date")) if query.get("date") else default_date
            slot_id = validate_slot_id(query.get("slot")) if query.get("slot") else default_slot
            result = get_rider_orders(table_name, date_str, slot_id, now=now, client=dynamodb_client)
            _log_event(
                "rider_list_orders",
                date=date_str,
                slot_id=slot_id,
                order_count=len(result["orders"]),
            )
            return _response(200, result)

        # Staff-only: PATCH /slots/{date}/{slotId}/orders/{orderId}/deliver
        deliver_match = DELIVER_PATH_PATTERN.match(path)
        if method == "PATCH" and deliver_match:
            if not _is_authorized_staff(headers):
                _log_event("unauthorized_deliver")
                return _error_response(401, "UNAUTHORIZED", "Valid staff API key is required.")

            date_str = validate_date_str(unquote(deliver_match.group("date")))
            slot_id = validate_slot_id(unquote(deliver_match.group("slot_id")))
            order_id = validate_order_id(unquote(deliver_match.group("order_id")))
            result = mark_order_delivered(
                table_name,
                date_str,
                slot_id,
                order_id,
                now=now,
                client=dynamodb_client,
            )
            _log_event(
                "mark_delivered",
                order_id=order_id,
                date=date_str,
                slot_id=slot_id,
                already_delivered=result["already_delivered"],
            )
            return _response(200, result)

        return _error_response(404, "NOT_FOUND", f"Route not found: {method} {path}")

    except ValidationError as exc:
        return _error_response(exc.status_code, exc.code, exc.message)
    except SlotFullError as exc:
        return _error_response(409, "SLOT_FULL", str(exc))
    except DuplicateOrderError as exc:
        return _error_response(409, "DUPLICATE_ORDER", str(exc))
    except OrderNotFoundError as exc:
        return _error_response(404, "ORDER_NOT_FOUND", str(exc))
    except TransactionConflictError as exc:
        return _error_response(503, "RETRY_CONFLICT", str(exc))
    except Exception:
        logger.exception("Unhandled error while processing request")
        return _error_response(500, "INTERNAL_ERROR", "An unexpected server error occurred.")


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    return handle_request(event)
