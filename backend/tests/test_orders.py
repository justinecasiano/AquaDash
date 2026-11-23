"""Tests for atomic 15-order slot cap, concurrency, idempotency, time cutoffs, and deliveries."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

import db
import handler
from config import PHT
from conftest import STAFF_KEY, TABLE_NAME, make_event


def _order_payload(
    *,
    date: str = "2026-11-23",
    slot_id: str = "08:00-10:00",
    idx: int = 1,
    quantity: int = 2,
    client_request_id: str | None = None,
) -> dict:
    payload = {
        "date": date,
        "slot_id": slot_id,
        "customer_name": f"Household {idx}",
        "address": f"Blk {idx} Lot 4 Sampaguita St, Phase 1",
        "phone": f"091700000{idx:02d}",
        "quantity": quantity,
        "notes": "Leave by front gate",
    }
    if client_request_id is not None:
        payload["client_request_id"] = client_request_id
    return payload


def test_slot_accepts_15_orders_and_rejects_16th(ddb_client):
    morning = datetime(2026, 11, 23, 8, 15, tzinfo=PHT)

    for i in range(1, 16):
        resp = handler.handle_request(
            make_event("POST", "/orders", body=_order_payload(idx=i, quantity=2)),
            now=morning,
            dynamodb_client=ddb_client,
        )
        assert resp["statusCode"] == 201, f"Order {i} unexpectedly failed: {resp}"

    # 16th order must fail with 409 SLOT_FULL
    resp_16 = handler.handle_request(
        make_event("POST", "/orders", body=_order_payload(idx=16)),
        now=morning,
        dynamodb_client=ddb_client,
    )
    assert resp_16["statusCode"] == 409
    assert json.loads(resp_16["body"])["error"] == "SLOT_FULL"

    # Verify slot summary shows exactly 15 booked, 0 remaining, 30 containers, status FULL
    slots_resp = handler.handle_request(
        make_event("GET", "/slots", query={"date": "2026-11-23"}),
        now=morning,
        dynamodb_client=ddb_client,
    )
    slot = json.loads(slots_resp["body"])["slots"][0]
    assert slot["booked_count"] == 15
    assert slot["remaining"] == 0
    assert slot["total_containers"] == 30
    assert slot["status"] == "FULL"


def test_concurrent_15th_spot_allows_only_one_winner(ddb_client):
    morning = datetime(2026, 11, 23, 8, 15, tzinfo=PHT)

    # Pre-fill 14 orders
    for i in range(1, 15):
        r = handler.handle_request(
            make_event("POST", "/orders", body=_order_payload(idx=i)),
            now=morning,
            dynamodb_client=ddb_client,
        )
        assert r["statusCode"] == 201

    # Fire 6 concurrent attempts for the single remaining 15th spot
    def submit(idx: int) -> int:
        res = handler.handle_request(
            make_event("POST", "/orders", body=_order_payload(idx=idx)),
            now=morning,
            dynamodb_client=ddb_client,
        )
        return res["statusCode"]

    with ThreadPoolExecutor(max_workers=6) as pool:
        statuses = list(pool.map(submit, range(15, 21)))

    assert statuses.count(201) == 1
    assert statuses.count(409) == 5

    # Invariant check: booked_count == actual ORDER# count == 15
    rider_resp = handler.handle_request(
        make_event(
            "GET",
            "/rider/orders",
            query={"date": "2026-11-23", "slot": "08:00-10:00"},
            headers={"X-Staff-Api-Key": STAFF_KEY},
        ),
        now=morning,
        dynamodb_client=ddb_client,
    )
    rider_data = json.loads(rider_resp["body"])
    assert rider_data["slot"]["booked_count"] == 15
    assert len(rider_data["orders"]) == 15


def test_duplicate_client_request_id_does_not_double_book(ddb_client):
    morning = datetime(2026, 11, 23, 8, 10, tzinfo=PHT)
    payload = _order_payload(client_request_id="req-uuid-12345678")

    first = handler.handle_request(make_event("POST", "/orders", body=payload), now=morning, dynamodb_client=ddb_client)
    second = handler.handle_request(make_event("POST", "/orders", body=payload), now=morning, dynamodb_client=ddb_client)

    assert first["statusCode"] == 201
    assert second["statusCode"] == 409
    assert json.loads(second["body"])["error"] == "DUPLICATE_ORDER"

    slots = json.loads(
        handler.handle_request(make_event("GET", "/slots", query={"date": "2026-11-23"}), now=morning, dynamodb_client=ddb_client)["body"]
    )["slots"]
    assert slots[0]["booked_count"] == 1


def test_past_date_and_closed_slot_rejected(ddb_client):
    midday = datetime(2026, 11, 23, 10, 1, tzinfo=PHT)

    past = handler.handle_request(
        make_event("POST", "/orders", body=_order_payload(date="2026-11-22")),
        now=midday,
        dynamodb_client=ddb_client,
    )
    assert past["statusCode"] == 400
    assert json.loads(past["body"])["error"] == "PAST_DATE"

    closed = handler.handle_request(
        make_event("POST", "/orders", body=_order_payload(date="2026-11-23", slot_id="08:00-10:00")),
        now=midday,
        dynamodb_client=ddb_client,
    )
    assert closed["statusCode"] == 409
    assert json.loads(closed["body"])["error"] == "SLOT_CLOSED"


def test_validation_rejects_bad_inputs(ddb_client):
    morning = datetime(2026, 11, 23, 8, 0, tzinfo=PHT)

    for bad_fields in [
        {"quantity": 0},
        {"quantity": 25},
        {"quantity": True},
        {"address": "abc"},
        {"address": "A" * 305},
        {"customer_name": "X"},
        {"phone": "abc"},
        {"slot_id": "23:00-24:00"},
    ]:
        payload = _order_payload()
        payload.update(bad_fields)
        resp = handler.handle_request(make_event("POST", "/orders", body=payload), now=morning, dynamodb_client=ddb_client)
        assert resp["statusCode"] == 400


def test_mark_delivered_idempotent_late_delivery_and_404(ddb_client):
    # Book in last slot (17:00-19:00) at 17:30 PHT
    booking_time = datetime(2026, 11, 23, 17, 30, tzinfo=PHT)
    created = handler.handle_request(
        make_event("POST", "/orders", body=_order_payload(slot_id="17:00-19:00", client_request_id="order-late-0001")),
        now=booking_time,
        dynamodb_client=ddb_client,
    )
    assert created["statusCode"] == 201

    # Rider delivers at 19:15 PHT (after slot is CLOSED for new customer bookings!)
    late_time = datetime(2026, 11, 23, 19, 15, tzinfo=PHT)
    deliver_path = "/slots/2026-11-23/17:00-19:00/orders/order-late-0001/deliver"
    headers = {"X-Staff-Api-Key": STAFF_KEY}

    first_deliver = handler.handle_request(make_event("PATCH", deliver_path, headers=headers), now=late_time, dynamodb_client=ddb_client)
    assert first_deliver["statusCode"] == 200
    assert json.loads(first_deliver["body"])["already_delivered"] is False

    # Repeat click must be idempotent and NOT double-increment delivered_count
    second_deliver = handler.handle_request(make_event("PATCH", deliver_path, headers=headers), now=late_time, dynamodb_client=ddb_client)
    assert second_deliver["statusCode"] == 200
    assert json.loads(second_deliver["body"])["already_delivered"] is True

    # Missing order returns 404
    missing = handler.handle_request(
        make_event("PATCH", "/slots/2026-11-23/17:00-19:00/orders/does-not-exist-99/deliver", headers=headers),
        now=late_time,
        dynamodb_client=ddb_client,
    )
    assert missing["statusCode"] == 404

    # Slot now has booked=1, delivered=1, status=COMPLETED
    slots = json.loads(
        handler.handle_request(make_event("GET", "/slots", query={"date": "2026-11-23"}), now=late_time, dynamodb_client=ddb_client)["body"]
    )["slots"]
    last_slot = [s for s in slots if s["slot_id"] == "17:00-19:00"][0]
    assert last_slot["booked_count"] == 1
    assert last_slot["delivered_count"] == 1
    assert last_slot["pending_count"] == 0
    assert last_slot["status"] == "COMPLETED"


def test_transient_transaction_conflict_retries_and_succeeds():
    """Verify 10x traffic write contention (TransactionConflict) retries instead of failing as SLOT_FULL."""
    mock_ddb = MagicMock()
    conflict_err = ClientError(
        {
            "Error": {"Code": "TransactionCanceledException", "Message": "Transaction cancelled"},
            "CancellationReasons": [{"Code": "TransactionConflict"}, {"Code": "None"}],
        },
        "TransactWriteItems",
    )
    mock_ddb.transact_write_items.side_effect = [conflict_err, {}]

    order = _order_payload(client_request_id="retry-order-0001")
    order["order_id"] = order.pop("client_request_id")
    receipt = db.create_order_atomic(
        TABLE_NAME,
        order,
        now=datetime(2026, 11, 23, 8, 10, tzinfo=PHT),
        client=mock_ddb,
        max_retries=3,
    )

    assert receipt["order_id"] == "retry-order-0001"
    assert mock_ddb.transact_write_items.call_count == 2
