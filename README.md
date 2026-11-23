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

---

## Manual AWS Management Console Deployment (`ap-southeast-1`)

> Make sure the AWS Console top-right region is **Singapore (`ap-southeast-1`)** and that every EC2 resource (Security Group, Key Pair, Launch Template, Instances, Volumes) carries the tag `team = bcsad-g02`.

### 1. DynamoDB Table (`umak-elec3-bcsad-g02-orders`)
1. **DynamoDB → Tables → Create table**
2. Table name: `umak-elec3-bcsad-g02-orders` | Partition key: `PK` (`String`) | Sort key: `SK` (`String`)
3. **Customize settings → Capacity mode: On-demand** (leave secondary indexes empty, default encryption on) → **Create table**.

### 2. Lambda Function (`umak-elec3-bcsad-g02-orders-api`)
1. Package zip locally:
   ```powershell
   .\scripts\build-lambda.ps1
   ```
2. **Lambda → Functions → Create function → Author from scratch**
   - Name: `umak-elec3-bcsad-g02-orders-api` | Runtime: `Python 3.12` | Architecture: `x86_64`
   - Execution role: **Use an existing role** → `umak-elec3-bcsad-g02-lambda-role`
3. **Code → Upload from → .zip file** → upload `dist\lambda-deploy.zip`. Verify **Handler** is `handler.lambda_handler`.
4. **Configuration → General configuration**: Memory `128 MB`, Timeout `10 sec`.
5. **Configuration → Environment variables**:
   - `TABLE_NAME` = `umak-elec3-bcsad-g02-orders`
   - `STAFF_API_KEY` = *(strong random secret — keep for EC2!)*
   - `ALLOWED_ORIGIN` = `*` *(lock to your S3 website origin after Step 4)*
6. **Test tab**: paste `deploy/lambda-test-event.json` and run → expect `statusCode: 200`.
7. **CloudWatch → Log groups → `/aws/lambda/umak-elec3-bcsad-g02-orders-api`** → **Edit retention setting** → **1 week (7 days)**.

### 3. Pre-Made API Gateway (`umak-elec3-bcsad-g02-api`)
1. **API Gateway → APIs → `umak-elec3-bcsad-g02-api`**
2. **Develop → Routes → Create** these 5 routes:
   - `GET /slots`
   - `POST /orders`
   - `GET /rider/orders`
   - `PATCH /slots/{date}/{slotId}/orders/{orderId}/deliver`
   - `OPTIONS /{proxy+}`
3. **Develop → Integrations**: attach `umak-elec3-bcsad-g02-orders-api` (Lambda, Payload `2.0`, grant invoke permission checked) to all 5 routes. Leave API Gateway's CORS page unconfigured (Lambda handles CORS).
4. **Deploy → Stages**: confirm `$default` has auto-deploy enabled and copy the **Invoke URL**.

### 4. S3 Static Website (`umak-elec3-bcsad-g02-frontend`)
1. Build frontend with your Invoke URL:
   ```powershell
   .\scripts\build-frontend.ps1 -ApiUrl "https://<YOUR_API_ID>.execute-api.ap-southeast-1.amazonaws.com"
   ```
2. **S3 → Create bucket**: Name `umak-elec3-bcsad-g02-frontend`, Region `ap-southeast-1`, ACLs disabled, **uncheck** *"Block all public access"* and re-check **only** the first two ACL boxes (leaving the two bucket-policy boxes unchecked), acknowledge warning, keep Versioning disabled → **Create bucket**.
3. **Properties → Static website hosting → Enable**: Index `index.html`, Error `index.html`. Copy the **Bucket website endpoint**.
4. **Permissions → Bucket policy**: paste `deploy/s3-bucket-policy.json` → **Save**.
5. **Objects → Upload**: upload the contents inside `frontend\dist\` (`index.html` at bucket root + `assets/` folder).
6. Update Lambda `ALLOWED_ORIGIN` to your exact S3 Bucket website endpoint (`http://umak-elec3-bcsad-g02-frontend.s3-website-ap-southeast-1.amazonaws.com`).

### 5. EC2 Rider & Owner Dashboard (`t3.micro` in `umak-elec3-final-bcsad-02-public`)
1. **Security Group (`umak-elec3-bcsad-g02-rider-sg`)**:
   - VPC: `umak-elec3-final-bcsad` (`10.2.0.0/16`)
   - Inbound: `HTTP (80)` from `0.0.0.0/0` (+ optional `SSH (22)` from `My IP` only)
   - Tag: `team = bcsad-g02`
2. **Launch Template (`umak-elec3-bcsad-g02-rider-lt`)**:
   - **Template tag:** `team = bcsad-g02`
   - **AMI:** Amazon Linux 2023 (`x86_64`) | **Instance type:** `t3.micro`
   - **Advanced network configuration → Add network interface:** Auto-assign public IP = `Enable`, Subnet = `umak-elec3-final-bcsad-02-public` (`10.2.2.0/24`), Security group = `umak-elec3-bcsad-g02-rider-sg`, Delete on termination = `Yes`
   - **Storage:** Root volume `8 GiB` `gp3`, Delete on termination = `Yes`
   - **Resource tags:** `team = bcsad-g02` and `Name = umak-elec3-bcsad-g02-rider` on both **Instances** and **Volumes**
   - **Advanced details:** IAM instance profile = `umak-elec3-bcsad-g02-ec2-role`, Credit specification = `Standard`, Detailed monitoring = `Disable`, User data = `deploy/user_data.sh` (with your real `API_BASE_URL` and secrets filled in)
3. **Launch 1 instance** from the template, wait ~2–3 minutes, then open `http://<PUBLIC_IP>/health` and `http://<PUBLIC_IP>/login`.

---

## Cost-Saving & Presentation Night Runbook
- **After every session:** Stop `umak-elec3-bcsad-g02-rider` in the EC2 Console (drops EC2 compute and Public IPv4 charges to `$0/hr`).
- **15 minutes before defense:** Start the EC2 instance in the Console, wait ~1 minute, and copy the **new Public IPv4 address** (`systemd` starts Gunicorn + Nginx automatically; S3 and API Gateway URLs do not change).
