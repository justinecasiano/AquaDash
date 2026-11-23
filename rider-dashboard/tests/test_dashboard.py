"""Unit tests for the EC2 Flask Rider & Owner Dashboard."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

DASHBOARD_DIR = Path(__file__).resolve().parent.parent
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from app import create_app  # noqa: E402


def _mock_slots_response():
    return {
        "date": "2026-11-23",
        "today": "2026-11-23",
        "default_date": "2026-11-23",
        "default_slot": "13:00-15:00",
        "all_today_closed": False,
        "slots": [
            {
                "date": "2026-11-23",
                "slot_id": "13:00-15:00",
                "label": "1:00 PM - 3:00 PM",
                "capacity": 15,
                "booked_count": 2,
                "delivered_count": 1,
                "pending_count": 1,
                "remaining": 13,
                "total_containers": 5,
                "is_full": False,
                "is_closed": False,
                "status": "OPEN",
            }
        ],
    }


def _mock_orders_response():
    return {
        "date": "2026-11-23",
        "slot": _mock_slots_response()["slots"][0],
        "orders": [
            {
                "order_id": "ord-11112222",
                "date": "2026-11-23",
                "slot_id": "13:00-15:00",
                "customer_name": "Ana Reyes",
                "address": "Blk 2 Lot 8 <script>alert(1)</script> Rosal St",
                "phone": "09171112222",
                "quantity": 3,
                "notes": "Ring doorbell",
                "status": "PENDING",
                "created_at": "2026-11-23T08:30:00+08:00",
                "delivered_at": None,
            }
        ],
    }


@pytest.fixture
def flask_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RIDER_PASSWORD", "rider-secret")
    monkeypatch.setenv("OWNER_PASSWORD", "owner-secret")
    monkeypatch.setenv("FLASK_SECRET_KEY", "unit-test-secret")

    mock_api = MagicMock()
    mock_api.get_slots.return_value = _mock_slots_response()
    mock_api.get_rider_orders.return_value = _mock_orders_response()
    mock_api.mark_delivered.return_value = {
        "order_id": "ord-11112222",
        "status": "DELIVERED",
        "already_delivered": False,
    }

    app = create_app(api_client=mock_api)
    app.config["TESTING"] = True
    return app.test_client(), mock_api


def test_health_endpoint_ok(flask_client):
    client, _ = flask_client
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_unauthenticated_access_redirects_to_login(flask_client):
    client, _ = flask_client

    r1 = client.get("/rider")
    assert r1.status_code == 302
    assert "/login" in r1.headers["Location"]
    assert b"Rosal St" not in r1.data

    r2 = client.get("/owner")
    assert r2.status_code == 302
    assert "/login" in r2.headers["Location"]


def test_wrong_password_rejected(flask_client):
    client, _ = flask_client
    resp = client.post("/login", data={"role": "rider", "password": "wrong"})
    assert resp.status_code == 401
    assert b"Invalid role or password" in resp.data


def test_rider_login_views_escaped_address_and_marks_delivered(flask_client):
    client, mock_api = flask_client

    login = client.post("/login", data={"role": "rider", "password": "rider-secret"}, follow_redirects=True)
    assert login.status_code == 200
    assert b"Ana Reyes" in login.data
    assert b"Rosal St" in login.data
    # Verify Jinja2 auto-escapes script tags in untrusted address inputs
    assert b"<script>alert(1)</script>" not in login.data
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in login.data

    deliver = client.post(
        "/rider/deliver",
        data={"date": "2026-11-23", "slot_id": "13:00-15:00", "order_id": "ord-11112222"},
        follow_redirects=True,
    )
    assert deliver.status_code == 200
    assert b"marked as DELIVERED" in deliver.data
    mock_api.mark_delivered.assert_called_once_with("2026-11-23", "13:00-15:00", "ord-11112222")


def test_owner_login_views_slot_capacity_and_logout_revokes_access(flask_client):
    client, _ = flask_client

    login = client.post("/login", data={"role": "owner", "password": "owner-secret"}, follow_redirects=True)
    assert login.status_code == 200
    assert b"Owner Slot Fullness Overview" in login.data
    assert b"1:00 PM - 3:00 PM" in login.data

    logout = client.post("/logout", follow_redirects=False)
    assert logout.status_code == 302

    after_logout = client.get("/owner")
    assert after_logout.status_code == 302
    assert "/login" in after_logout.headers["Location"]
