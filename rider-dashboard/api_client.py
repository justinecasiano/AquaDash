"""Server-side HTTP client for calling AquaDash API Gateway with X-Staff-Api-Key."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests


class ApiClientError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AquaDashApiClient:
    def __init__(self, base_url: str, staff_api_key: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.staff_api_key = staff_api_key
        self.timeout = timeout

    def _staff_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Staff-Api-Key": self.staff_api_key,
        }

    def _handle_response(self, resp: requests.Response) -> dict[str, Any]:
        try:
            payload = resp.json()
        except ValueError:
            payload = {}

        if not resp.ok:
            msg = payload.get("message") or f"Backend API returned HTTP {resp.status_code}."
            raise ApiClientError(msg, status_code=resp.status_code)
        return payload

    def get_slots(self, date_str: str | None = None) -> dict[str, Any]:
        params = {"date": date_str} if date_str else None
        try:
            resp = requests.get(
                f"{self.base_url}/slots",
                params=params,
                headers={"Accept": "application/json"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ApiClientError("Could not reach the AquaDash API server.") from exc
        return self._handle_response(resp)

    def get_rider_orders(self, date_str: str | None = None, slot_id: str | None = None) -> dict[str, Any]:
        params: dict[str, str] = {}
        if date_str:
            params["date"] = date_str
        if slot_id:
            params["slot"] = slot_id
        try:
            resp = requests.get(
                f"{self.base_url}/rider/orders",
                params=params or None,
                headers=self._staff_headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ApiClientError("Could not reach the AquaDash API server.") from exc
        return self._handle_response(resp)

    def mark_delivered(self, date_str: str, slot_id: str, order_id: str) -> dict[str, Any]:
        safe_date = quote(date_str, safe="")
        safe_slot = quote(slot_id, safe="")
        safe_order = quote(order_id, safe="")
        url = f"{self.base_url}/slots/{safe_date}/{safe_slot}/orders/{safe_order}/deliver"
        try:
            resp = requests.patch(
                url,
                headers=self._staff_headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ApiClientError("Could not reach the AquaDash API server.") from exc
        return self._handle_response(resp)
