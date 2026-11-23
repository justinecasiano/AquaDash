"""Local development server wrapping the real Lambda handler with an in-memory Moto DynamoDB table."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import Flask, Response, request
from moto import mock_aws

# Allow importing backend/src modules the exact same way AWS Lambda imports them
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import boto3  # noqa: E402
import handler  # noqa: E402

TABLE_NAME = os.environ.setdefault("TABLE_NAME", "umak-elec3-bcsad-g02-orders")
os.environ.setdefault("STAFF_API_KEY", "dev-staff-key-123")
os.environ.setdefault("ALLOWED_ORIGIN", "*")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-southeast-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")

app = Flask(__name__)


def _create_local_table() -> None:
    ddb = boto3.client("dynamodb", region_name="ap-southeast-1")
    existing = ddb.list_tables().get("TableNames", [])
    if TABLE_NAME not in existing:
        ddb.create_table(
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


@app.route("/", defaults={"subpath": ""}, methods=["GET", "POST", "PATCH", "OPTIONS"])
@app.route("/<path:subpath>", methods=["GET", "POST", "PATCH", "OPTIONS"])
def proxy_to_lambda(subpath: str) -> Response:
    event = {
        "version": "2.0",
        "rawPath": f"/{subpath}" if subpath else "/",
        "queryStringParameters": dict(request.args) if request.args else None,
        "headers": {k.lower(): v for k, v in request.headers.items()},
        "requestContext": {
            "stage": "$default",
            "http": {
                "method": request.method,
                "path": f"/{subpath}" if subpath else "/",
            },
        },
        "body": request.get_data(as_text=True),
        "isBase64Encoded": False,
    }
    result = handler.lambda_handler(event, None)
    return Response(
        response=result.get("body", ""),
        status=result.get("statusCode", 200),
        headers=result.get("headers", {}),
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    with mock_aws():
        _create_local_table()
        print(f"AquaDash local Lambda API running on http://127.0.0.1:{port}")
        print(f"Table: {TABLE_NAME} | Staff Key: {os.environ['STAFF_API_KEY']}")
        app.run(host="127.0.0.1", port=port, debug=False)
