"""Privacy and authentication tests ensuring private home addresses are never leaked."""

from __future__ import annotations

import json
import logging
from datetime import datetime

import handler
from config import PHT
from conftest import STAFF_KEY, make_event


def test_public_slots_endpoint_never_leaks_addresses_or_pii(ddb_client):
    morning = datetime(2026, 11, 23, 8, 10, tzinfo=PHT)
    secret_address = "Blk 99 Lot 12 Secret Subdivision Street"
    secret_phone = "09179998888"

    create_resp = handler.handle_request(
        make_event(
            "POST",
            "/orders",
            body={
                "date": "2026-11-23",
                "slot_id": "08:00-10:00",
                "customer_name": "Maria Santos",
                "address": secret_address,
                "phone": secret_phone,
                "quantity": 3,
                "notes": "Private gate code 4321",
            },
        ),
        now=morning,
        dynamodb_client=ddb_client,
    )
    assert create_resp["statusCode"] == 201

    slots_resp = handler.handle_request(
        make_event("GET", "/slots", query={"date": "2026-11-23"}),
        now=morning,
        dynamodb_client=ddb_client,
    )
    assert slots_resp["statusCode"] == 200
    raw_body = slots_resp["body"]

    assert secret_address not in raw_body
    assert secret_phone not in raw_body
    assert "Maria Santos" not in raw_body
    assert "4321" not in raw_body
    for slot in json.loads(raw_body)["slots"]:
        assert not ({"address", "phone", "customer_name", "notes"} & set(slot.keys()))


def test_rider_endpoints_require_valid_staff_api_key(ddb_client):
    morning = datetime(2026, 11, 23, 8, 10, tzinfo=PHT)

    # Missing key -> 401
    r1 = handler.handle_request(
        make_event("GET", "/rider/orders", query={"date": "2026-11-23", "slot": "08:00-10:00"}),
        now=morning,
        dynamodb_client=ddb_client,
    )
    assert r1["statusCode"] == 401

    # Wrong key -> 401
    r2 = handler.handle_request(
        make_event(
            "GET",
            "/rider/orders",
            query={"date": "2026-11-23", "slot": "08:00-10:00"},
            headers={"X-Staff-Api-Key": "wrong-key"},
        ),
        now=morning,
        dynamodb_client=ddb_client,
    )
    assert r2["statusCode"] == 401

    # Deliver without key -> 401
    r3 = handler.handle_request(
        make_event("PATCH", "/slots/2026-11-23/08:00-10:00/orders/order-12345678/deliver"),
        now=morning,
        dynamodb_client=ddb_client,
    )
    assert r3["statusCode"] == 401

    # Valid key (case-insensitive header) -> 200
    r4 = handler.handle_request(
        make_event(
            "GET",
            "/rider/orders",
            query={"date": "2026-11-23", "slot": "08:00-10:00"},
            headers={"x-staff-api-key": STAFF_KEY},
        ),
        now=morning,
        dynamodb_client=ddb_client,
    )
    assert r4["statusCode"] == 200


def test_lambda_logs_never_contain_home_addresses(ddb_client, caplog):
    morning = datetime(2026, 11, 23, 8, 10, tzinfo=PHT)
    secret_address = "Blk 77 Lot 88 Confidential Ave"

    with caplog.at_level(logging.INFO, logger="aquadash"):
        resp = handler.handle_request(
            make_event(
                "POST",
                "/orders",
                body={
                    "date": "2026-11-23",
                    "slot_id": "08:00-10:00",
                    "customer_name": "Juan Dela Cruz",
                    "address": secret_address,
                    "phone": "09171234567",
                    "quantity": 1,
                },
            ),
            now=morning,
            dynamodb_client=ddb_client,
        )
    assert resp["statusCode"] == 201
    all_logs = "\n".join(rec.getMessage() for rec in caplog.records)
    assert secret_address not in all_logs
    assert "09171234567" not in all_logs
    assert "Juan Dela Cruz" not in all_logs
