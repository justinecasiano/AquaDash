# AquaDash — Water Refilling Station Orders (Case 9)

**Course:** ELEC3 — Cloud Computing (Final Exam, Track B)  
**Section / Group:** `IV-BCSAD` · `Group 02` (`bcsad-g02`)  
**AWS Region:** `ap-southeast-1` (Asia Pacific — Singapore)  

AquaDash lets subdivision households order 5-gallon water refills for a delivery time slot, lets the delivery rider view orders for the current/next slot and mark them as delivered, and lets the station owner monitor how full each time slot is.

## Constraints Enforced
- **Max 15 orders per time slot:** Enforced atomically in DynamoDB via `TransactWriteItems` (`booked_count < 15`) with client-side `client_request_id` idempotency and transient `TransactionConflict` retry handling.
- **Private home addresses:**
  - Public `GET /slots` reads only `META` slot counters (`BatchGetItem`) — never touches order items or addresses.
  - Staff routes (`GET /rider/orders`, `PATCH /slots/{date}/{slotId}/orders/{orderId}/deliver`) require server-side `X-Staff-Api-Key`.
  - The EC2 Rider & Owner Dashboard requires session login (`/login`) before displaying any private addresses.
  - Lambda logs strip all PII fields (`address`, `phone`, `customer_name`, `notes`).

## Tech Stack & Repository Layout
- `backend/` — **Python 3.12 AWS Lambda** (`boto3` + DynamoDB single-table design), local Moto dev runner (`local_server.py`), and `pytest` suite.
- `frontend/` — **Vue 3 (Vite) + Tailwind CSS** static website hosted on **Amazon S3** (Household Order Portal + Owner Slot Capacity View).
- `rider-dashboard/` — **Python Flask + Jinja2 + Gunicorn** dashboard hosted on **EC2 `t3.micro`** behind Nginx (Rider Delivery List + Owner Capacity Overview).
- `deploy/` — Ready-to-use AWS Console deployment assets (`user_data.sh`, `s3-bucket-policy.json`, `lambda-test-event.json`).
- `scripts/` — PowerShell packaging helpers (`build-lambda.ps1`, `build-frontend.ps1`).
- `docs/` — Defense least-privilege IAM policy (`iam-least-privilege.json`).

---

## Local Development & Testing

### 1. Set Up Python Virtual Environment & Run Automated Tests
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt requests python-dotenv
.\.venv\Scripts\pytest.exe backend/tests rider-dashboard/tests -v
```

### 2. Run All 3 Tiers Locally (3 Terminals)
- **Terminal 1 — Local Lambda + Moto DynamoDB (`http://127.0.0.1:5001`):**
  ```powershell
  .\.venv\Scripts\python.exe backend/local_server.py
  ```
- **Terminal 2 — Vue 3 S3 Frontend (`http://localhost:5173`):**
  ```powershell
  cd frontend
  npm install
  npm run dev
  ```
- **Terminal 3 — Flask Rider & Owner Dashboard (`http://127.0.0.1:5000`):**
  ```powershell
  .\.venv\Scripts\python.exe rider-dashboard/app.py
  ```
  - Default local credentials (override in `rider-dashboard/.env`):
    - **Rider:** password `rider123`
    - **Owner:** password `owner123`
