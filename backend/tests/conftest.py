"""Shared pytest fixtures for AquaDash Lambda backend tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import boto3
import pytest
from moto import mock_aws

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

TABLE_NAME = "umak-elec3-bcsad-g02-orders"
STAFF_KEY = "test-staff-secret-key-999"


@pytest.fixture
def ddb_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TABLE_NAME", TABLE_NAME)
    monkeypatch.setenv("STAFF_API_KEY", STAFF_KEY)
    monkeypatch.setenv("ALLOWED_ORIGIN", "http://umak-elec3-bcsad-g02-frontend.s3-website-ap-southeast-1.amazonaws.com")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")

    with mock_aws():
        client = boto3.client("dynamodb", region_name="ap-southeast-1")
        client.create_table(
            TableName=TABLE_NAME,
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
        )
        yield client


def make_event(
    method: str,
    path: str,
    *,
    query: dict[str, str] | None = None,
    body: dict[str, Any] | str | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    encoded_body = ""
    if isinstance(body, dict):
        encoded_body = json.dumps(body)
    elif isinstance(body, str):
        encoded_body = body

    return {
        "version": "2.0",
        "rawPath": path,
        "queryStringParameters": query,
        "headers": headers or {},
        "requestContext": {
            "stage": "$default",
            "http": {"method": method, "path": path},
        },
        "body": encoded_body,
        "isBase64Encoded": False,
    }
