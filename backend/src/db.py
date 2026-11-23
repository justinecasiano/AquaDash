"""DynamoDB single-table data layer with atomic 15-order slot enforcement."""

from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Any

import boto3
from botocore.exceptions import ClientError

from config import MAX_ORDERS_PER_SLOT, SLOT_MAP, TIME_SLOTS, is_slot_closed, now_pht


class SlotFullError(Exception):
    pass


class DuplicateOrderError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class TransactionConflictError(Exception):
    pass


def get_dynamodb_client():
    return boto3.client("dynamodb")


def make_slot_pk(date_str: str, slot_id: str) -> str:
    return f"SLOT#{date_str}#{slot_id}"


def make_order_sk(order_id: str) -> str:
    return f"ORDER#{order_id}"


def _str_attr(item: dict[str, Any], key: str, default: str = "") -> str:
    val = item.get(key)
    return val["S"] if val and "S" in val else default


def _int_attr(item: dict[str, Any], key: str, default: int = 0) -> int:
    val = item.get(key)
    return int(val["N"]) if val and "N" in val else default


def _build_slot_summary(
    date_str: str,
    slot_cfg: dict[str, Any],
    meta_item: dict[str, Any] | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    slot_id = slot_cfg["slot_id"]
    booked_count = _int_attr(meta_item, "booked_count", 0) if meta_item else 0
    delivered_count = _int_attr(meta_item, "delivered_count", 0) if meta_item else 0
    total_containers = _int_attr(meta_item, "total_containers", 0) if meta_item else 0

    remaining = max(0, MAX_ORDERS_PER_SLOT - booked_count)
    pending_count = max(0, booked_count - delivered_count)
    is_full = booked_count >= MAX_ORDERS_PER_SLOT
    closed = is_slot_closed(date_str, slot_id, now=now)

    if booked_count > 0 and delivered_count >= booked_count and (closed or is_full):
        status = "COMPLETED"
    elif closed:
        status = "CLOSED"
    elif is_full:
        status = "FULL"
    else:
        status = "OPEN"

    return {
        "date": date_str,
        "slot_id": slot_id,
        "label": slot_cfg["label"],
        "capacity": MAX_ORDERS_PER_SLOT,
        "booked_count": booked_count,
        "delivered_count": delivered_count,
        "pending_count": pending_count,
        "remaining": remaining,
        "total_containers": total_containers,
        "is_full": is_full,
        "is_closed": closed,
        "status": status,
    }


def get_slots_summary(
    table_name: str,
    date_str: str,
    now: datetime | None = None,
    client: Any = None,
) -> list[dict[str, Any]]:
    """Fetch slot capacity counts using BatchGetItem strictly on META keys (zero PII)."""
    ddb = client or get_dynamodb_client()
    keys = [{"PK": {"S": make_slot_pk(date_str, s["slot_id"])}, "SK": {"S": "META"}} for s in TIME_SLOTS]

    meta_by_pk: dict[str, dict[str, Any]] = {}
    pending_keys: list[dict[str, Any]] = keys

    for _ in range(5):
        if not pending_keys:
            break
        response = ddb.batch_get_item(RequestItems={table_name: {"Keys": pending_keys}})
        for item in response.get("Responses", {}).get(table_name, []):
            meta_by_pk[_str_attr(item, "PK")] = item
        pending_keys = response.get("UnprocessedKeys", {}).get(table_name, {}).get("Keys", [])

    summaries = []
    for slot_cfg in TIME_SLOTS:
        pk = make_slot_pk(date_str, slot_cfg["slot_id"])
        summaries.append(_build_slot_summary(date_str, slot_cfg, meta_by_pk.get(pk), now=now))
    return summaries


def create_order_atomic(
    table_name: str,
    order_data: dict[str, Any],
    now: datetime | None = None,
    client: Any = None,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Atomically increment slot META counter (< 15) and insert ORDER item."""
    ddb = client or get_dynamodb_client()
    date_str = order_data["date"]
    slot_id = order_data["slot_id"]
    order_id = order_data["order_id"]
    pk = make_slot_pk(date_str, slot_id)
    sk = make_order_sk(order_id)
    created_at = now_pht(now).isoformat()

    transact_items = [
        {
            "Update": {
                "TableName": table_name,
                "Key": {"PK": {"S": pk}, "SK": {"S": "META"}},
                "UpdateExpression": (
                    "SET booked_count = if_not_exists(booked_count, :zero) + :one, "
                    "delivered_count = if_not_exists(delivered_count, :zero), "
                    "total_containers = if_not_exists(total_containers, :zero) + :qty, "
                    "#d = :date, slot_id = :slot_id, #cap = :cap"
                ),
                "ConditionExpression": "attribute_not_exists(booked_count) OR booked_count < :cap",
                "ExpressionAttributeNames": {"#d": "date", "#cap": "capacity"},
                "ExpressionAttributeValues": {
                    ":zero": {"N": "0"},
                    ":one": {"N": "1"},
                    ":qty": {"N": str(order_data["quantity"])},
                    ":cap": {"N": str(MAX_ORDERS_PER_SLOT)},
                    ":date": {"S": date_str},
                    ":slot_id": {"S": slot_id},
                },
            }
        },
        {
            "Put": {
                "TableName": table_name,
                "Item": {
                    "PK": {"S": pk},
                    "SK": {"S": sk},
                    "order_id": {"S": order_id},
                    "date": {"S": date_str},
                    "slot_id": {"S": slot_id},
                    "customer_name": {"S": order_data["customer_name"]},
                    "address": {"S": order_data["address"]},
                    "phone": {"S": order_data["phone"]},
                    "quantity": {"N": str(order_data["quantity"])},
                    "notes": {"S": order_data["notes"]},
                    "status": {"S": "PENDING"},
                    "created_at": {"S": created_at},
                },
                "ConditionExpression": "attribute_not_exists(PK)",
            }
        },
    ]

    for attempt in range(max_retries):
        try:
            ddb.transact_write_items(TransactItems=transact_items)
            return {
                "order_id": order_id,
                "date": date_str,
                "slot_id": slot_id,
                "slot_label": SLOT_MAP[slot_id]["label"],
                "customer_name": order_data["customer_name"],
                "quantity": order_data["quantity"],
                "status": "PENDING",
                "created_at": created_at,
            }
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code != "TransactionCanceledException":
                raise

            reasons = exc.response.get("CancellationReasons", [])
            reason_codes = [r.get("Code", "") for r in reasons]

            if "TransactionConflict" in reason_codes:
                if attempt < max_retries - 1:
                    time.sleep(0.02 * (attempt + 1) + random.uniform(0, 0.03))
                    continue
                raise TransactionConflictError("High booking contention, please retry.") from exc

            # Check duplicate order before slot-full so retrying the 15th order reports DUPLICATE_ORDER
            if len(reasons) > 1 and reasons[1].get("Code") == "ConditionalCheckFailed":
                raise DuplicateOrderError("This order request was already submitted.") from exc

            if len(reasons) > 0 and reasons[0].get("Code") == "ConditionalCheckFailed":
                raise SlotFullError("This time slot is full (15/15 orders).") from exc

            raise

    raise TransactionConflictError("High booking contention, please retry.")


def get_rider_orders(
    table_name: str,
    date_str: str,
    slot_id: str,
    now: datetime | None = None,
    client: Any = None,
) -> dict[str, Any]:
    """Fetch all orders (including private home addresses) for a specific slot."""
    ddb = client or get_dynamodb_client()
    pk = make_slot_pk(date_str, slot_id)

    meta_resp = ddb.get_item(TableName=table_name, Key={"PK": {"S": pk}, "SK": {"S": "META"}})
    slot_summary = _build_slot_summary(date_str, SLOT_MAP[slot_id], meta_resp.get("Item"), now=now)

    raw_items: list[dict[str, Any]] = []
    query_kwargs: dict[str, Any] = {
        "TableName": table_name,
        "KeyConditionExpression": "PK = :pk AND begins_with(SK, :prefix)",
        "ExpressionAttributeValues": {
            ":pk": {"S": pk},
            ":prefix": {"S": "ORDER#"},
        },
    }

    while True:
        resp = ddb.query(**query_kwargs)
        raw_items.extend(resp.get("Items", []))
        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break
        query_kwargs["ExclusiveStartKey"] = last_key

    orders = [
        {
            "order_id": _str_attr(item, "order_id"),
            "date": _str_attr(item, "date"),
            "slot_id": _str_attr(item, "slot_id"),
            "customer_name": _str_attr(item, "customer_name"),
            "address": _str_attr(item, "address"),
            "phone": _str_attr(item, "phone"),
            "quantity": _int_attr(item, "quantity", 1),
            "notes": _str_attr(item, "notes"),
            "status": _str_attr(item, "status", "PENDING"),
            "created_at": _str_attr(item, "created_at"),
            "delivered_at": _str_attr(item, "delivered_at") or None,
        }
        for item in raw_items
    ]
    orders.sort(key=lambda o: o["created_at"])

    return {
        "date": date_str,
        "slot": slot_summary,
        "orders": orders,
    }


def mark_order_delivered(
    table_name: str,
    date_str: str,
    slot_id: str,
    order_id: str,
    now: datetime | None = None,
    client: Any = None,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Atomically transition an order from PENDING to DELIVERED and increment delivered_count."""
    ddb = client or get_dynamodb_client()
    pk = make_slot_pk(date_str, slot_id)
    sk = make_order_sk(order_id)
    delivered_at = now_pht(now).isoformat()

    transact_items = [
        {
            "Update": {
                "TableName": table_name,
                "Key": {"PK": {"S": pk}, "SK": {"S": sk}},
                "UpdateExpression": "SET #s = :delivered, delivered_at = :now",
                "ConditionExpression": "attribute_exists(PK) AND #s = :pending",
                "ExpressionAttributeNames": {"#s": "status"},
                "ExpressionAttributeValues": {
                    ":delivered": {"S": "DELIVERED"},
                    ":pending": {"S": "PENDING"},
                    ":now": {"S": delivered_at},
                },
            }
        },
        {
            "Update": {
                "TableName": table_name,
                "Key": {"PK": {"S": pk}, "SK": {"S": "META"}},
                "UpdateExpression": "SET delivered_count = if_not_exists(delivered_count, :zero) + :one",
                "ExpressionAttributeValues": {
                    ":zero": {"N": "0"},
                    ":one": {"N": "1"},
                },
            }
        },
    ]

    for attempt in range(max_retries):
        try:
            ddb.transact_write_items(TransactItems=transact_items)
            return {
                "order_id": order_id,
                "date": date_str,
                "slot_id": slot_id,
                "status": "DELIVERED",
                "delivered_at": delivered_at,
                "already_delivered": False,
            }
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code != "TransactionCanceledException":
                raise

            reasons = exc.response.get("CancellationReasons", [])
            reason_codes = [r.get("Code", "") for r in reasons]

            if "TransactionConflict" in reason_codes:
                if attempt < max_retries - 1:
                    time.sleep(0.02 * (attempt + 1) + random.uniform(0, 0.03))
                    continue
                raise TransactionConflictError("Temporary write conflict, please retry.") from exc

            existing = ddb.get_item(TableName=table_name, Key={"PK": {"S": pk}, "SK": {"S": sk}}).get("Item")
            if not existing:
                raise OrderNotFoundError("Order not found.") from exc

            if _str_attr(existing, "status") == "DELIVERED":
                return {
                    "order_id": order_id,
                    "date": date_str,
                    "slot_id": slot_id,
                    "status": "DELIVERED",
                    "delivered_at": _str_attr(existing, "delivered_at") or None,
                    "already_delivered": True,
                }

            raise

    raise TransactionConflictError("Temporary write conflict, please retry.")
