#!/bin/bash
set -euo pipefail

# ==============================================================================
# AquaDash EC2 Launch Template User Data (Amazon Linux 2023, t3.micro)
# Group: bcsad-g02 | Subnet: umak-elec3-final-bcsad-02-public (10.2.2.0/24)
#
# BEFORE PASTING INTO AWS LAUNCH TEMPLATE USER DATA:
# Replace the 5 values below with your real API Gateway Invoke URL and secrets.
# ==============================================================================
REPO_URL="https://github.com/justinecasiano/AquaDash.git"
API_BASE_URL="https://YOUR_API_ID.execute-api.ap-southeast-1.amazonaws.com"
STAFF_API_KEY="CHANGE_ME_MATCH_LAMBDA_STAFF_API_KEY"
FLASK_SECRET_KEY="CHANGE_ME_LONG_RANDOM_SECRET"
RIDER_PASSWORD="CHANGE_ME_RIDER_PASSWORD"
OWNER_PASSWORD="CHANGE_ME_OWNER_PASSWORD"

APP_DIR="/opt/aquadash"

# 1. Install system packages
dnf install -y git python3 python3-pip nginx

# 2. Clone public AquaDash repository
rm -rf "$APP_DIR"
git clone --depth 1 "$REPO_URL" "$APP_DIR"

# 3. Create Python virtual environment and install Flask + Gunicorn dependencies
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/rider-dashboard/requirements.txt"

# 4. Write protected runtime .env file
cat > "$APP_DIR/rider-dashboard/.env" <<EOF
API_BASE_URL=${API_BASE_URL}
STAFF_API_KEY=${STAFF_API_KEY}
FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
RIDER_PASSWORD=${RIDER_PASSWORD}
OWNER_PASSWORD=${OWNER_PASSWORD}
EOF

chown -R ec2-user:ec2-user "$APP_DIR"
chmod 600 "$APP_DIR/rider-dashboard/.env"

# 5. Create systemd service so Gunicorn starts automatically on every EC2 start
cat > /etc/systemd/system/aquadash-rider.service <<EOF
[Unit]
Description=AquaDash Rider and Owner Dashboard (Gunicorn)
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=${APP_DIR}/rider-dashboard
EnvironmentFile=${APP_DIR}/rider-dashboard/.env
ExecStart=${APP_DIR}/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 --timeout 30 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now aquadash-rider

# 6. Configure Nginx reverse proxy on port 80 -> Gunicorn 127.0.0.1:8000
cat > /etc/nginx/nginx.conf <<'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /run/nginx.pid;

events {
    worker_connections 256;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;

    server {
        listen 80 default_server;
        server_name _;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

nginx -t
systemctl enable --now nginx
