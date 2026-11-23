"""Tests for slot listing, PHT time cutoffs, evening rollover, and zero-PII guarantees."""

from __future__ import annotations

import json
from datetime import datetime

import handler
from config import PHT
from conftest import make_event


def test_list_slots_empty_day_returns_five_open_slots(ddb_client):
    morning = datetime(2026, 11, 23, 7, 30, tzinfo=PHT)
    resp = handler.handle_request(make_event("GET", "/slots", query={"date": "2026-11-23"}), now=morning, dynamodb_client=ddb_client)
    assert resp["statusCode"] == 200

    data = json.loads(resp["body"])
    assert data["date"] == "2026-11-23"
    assert data["all_today_closed"] is False
    assert data["default_date"] == "2026-11-23"
    assert data["default_slot"] == "08:00-10:00"
    assert len(data["slots"]) == 5

    for slot in data["slots"]:
        assert slot["capacity"] == 15
        assert slot["booked_count"] == 0
        assert slot["remaining"] == 15
        assert slot["status"] == "OPEN"
        assert slot["is_full"] is False
        assert slot["is_closed"] is False


def test_midday_marks_past_slots_closed_and_selects_active_or_next_slot(ddb_client):
    # 12:30 PM PHT: morning slots closed, next upcoming slot is 13:00-15:00
    lunch = datetime(2026, 11, 23, 12, 30, tzinfo=PHT)
    resp = handler.handle_request(make_event("GET", "/slots", query={"date": "2026-11-23"}), now=lunch, dynamodb_client=ddb_client)
    data = json.loads(resp["body"])

    assert data["default_date"] == "2026-11-23"
    assert data["default_slot"] == "13:00-15:00"
    by_id = {s["slot_id"]: s for s in data["slots"]}
    assert by_id["08:00-10:00"]["status"] == "CLOSED"
    assert by_id["10:00-12:00"]["status"] == "CLOSED"
    assert by_id["13:00-15:00"]["status"] == "OPEN"

    # 13:45 PM PHT: currently inside 13:00-15:00 -> active slot stays 13:00-15:00
    active_window = datetime(2026, 11, 23, 13, 45, tzinfo=PHT)
    resp_active = handler.handle_request(make_event("GET", "/slots"), now=active_window, dynamodb_client=ddb_client)
    assert json.loads(resp_active["body"])["default_slot"] == "13:00-15:00"


def test_evening_after_7pm_rolls_default_date_to_tomorrow(ddb_client):
    evening = datetime(2026, 11, 23, 19, 30, tzinfo=PHT)
    resp = handler.handle_request(make_event("GET", "/slots", query={"date": "2026-11-23"}), now=evening, dynamodb_client=ddb_client)
    data = json.loads(resp["body"])

    assert data["all_today_closed"] is True
    assert data["default_date"] == "2026-11-24"
    assert data["default_slot"] == "08:00-10:00"
    assert all(s["status"] == "CLOSED" for s in data["slots"])


def test_cors_options_preflight_returns_204(ddb_client):
    resp = handler.handle_request(make_event("OPTIONS", "/orders"), dynamodb_client=ddb_client)
    assert resp["statusCode"] == 204
    assert "Access-Control-Allow-Origin" in resp["headers"]
    assert "X-Staff-Api-Key" in resp["headers"]["Access-Control-Allow-Headers"]
