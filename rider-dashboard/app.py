"""AquaDash EC2 Rider & Owner Dashboard (Flask + Jinja2 + Gunicorn)."""

from __future__ import annotations

import hmac
import os
from functools import wraps
from typing import Any, Callable

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from api_client import ApiClientError, AquaDashApiClient

load_dotenv()


def create_app(api_client: AquaDashApiClient | None = None) -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-flask-secret-change-me")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    client = api_client or AquaDashApiClient(
        base_url=os.environ.get("API_BASE_URL", "http://127.0.0.1:5001"),
        staff_api_key=os.environ.get("STAFF_API_KEY", "dev-staff-key-123"),
    )
    app.config["API_CLIENT"] = client

    def get_client() -> AquaDashApiClient:
        return app.config["API_CLIENT"]

    def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if not session.get("role"):
                return redirect(url_for("login", next=request.full_path.rstrip("?")))
            return view(*args, **kwargs)

        return wrapped

    def role_required(*allowed_roles: str) -> Callable[..., Any]:
        def decorator(view: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(view)
            def wrapped(*args: Any, **kwargs: Any) -> Any:
                role = session.get("role")
                if not role:
                    return redirect(url_for("login", next=request.full_path.rstrip("?")))
                if role not in allowed_roles:
                    return ("Forbidden: insufficient role permissions.", 403)
                return view(*args, **kwargs)

            return wrapped

        return decorator

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.get("/")
    def index():
        role = session.get("role")
        if role == "owner":
            return redirect(url_for("owner_dashboard"))
        if role == "rider":
            return redirect(url_for("rider_dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            role = (request.form.get("role") or "rider").strip().lower()
            password = request.form.get("password") or ""

            rider_pw = os.environ.get("RIDER_PASSWORD", "rider123")
            owner_pw = os.environ.get("OWNER_PASSWORD", "owner123")

            if role == "rider" and rider_pw and hmac.compare_digest(password, rider_pw):
                session.clear()
                session["role"] = "rider"
                flash("Signed in as Delivery Rider.", "success")
                return redirect(url_for("rider_dashboard"))

            if role == "owner" and owner_pw and hmac.compare_digest(password, owner_pw):
                session.clear()
                session["role"] = "owner"
                flash("Signed in as Station Owner.", "success")
                return redirect(url_for("owner_dashboard"))

            flash("Invalid role or password. Please try again.", "error")
            return render_template("login.html", selected_role=role), 401

        return render_template("login.html", selected_role="rider")

    @app.post("/logout")
    def logout():
        session.clear()
        flash("You have been signed out.", "info")
        return redirect(url_for("login"))

    @app.get("/rider")
    @login_required
    def rider_dashboard():
        req_date = (request.args.get("date") or "").strip()
        req_slot = (request.args.get("slot") or "").strip()

        error_message = ""
        slots_data: dict[str, Any] = {}
        orders_data: dict[str, Any] = {"orders": [], "slot": None}

        try:
            # Determine default active/next PHT slot if user didn't pick one explicitly
            initial_slots = get_client().get_slots(req_date or None)
            selected_date = req_date or initial_slots.get("default_date") or initial_slots.get("date")
            selected_slot = req_slot or initial_slots.get("default_slot") or "08:00-10:00"

            if selected_date != initial_slots.get("date"):
                slots_data = get_client().get_slots(selected_date)
            else:
                slots_data = initial_slots

            orders_data = get_client().get_rider_orders(selected_date, selected_slot)
        except ApiClientError as exc:
            error_message = exc.message
            selected_date = req_date
            selected_slot = req_slot

        return render_template(
            "rider.html",
            role=session.get("role"),
            selected_date=selected_date,
            selected_slot=selected_slot,
            today=slots_data.get("today", ""),
            all_today_closed=slots_data.get("all_today_closed", False),
            slots=slots_data.get("slots", []),
            slot_info=orders_data.get("slot"),
            orders=orders_data.get("orders", []),
            error_message=error_message,
        )

    @app.post("/rider/deliver")
    @role_required("rider")
    def mark_delivered():
        date_str = (request.form.get("date") or "").strip()
        slot_id = (request.form.get("slot_id") or "").strip()
        order_id = (request.form.get("order_id") or "").strip()

        if not (date_str and slot_id and order_id):
            flash("Missing order details for delivery update.", "error")
            return redirect(url_for("rider_dashboard"))

        try:
            result = get_client().mark_delivered(date_str, slot_id, order_id)
            if result.get("already_delivered"):
                flash(f"Order {order_id} was already marked delivered.", "info")
            else:
                flash(f"Order {order_id} marked as DELIVERED.", "success")
        except ApiClientError as exc:
            flash(exc.message, "error")

        return redirect(url_for("rider_dashboard", date=date_str, slot=slot_id))

    @app.get("/owner")
    @role_required("owner")
    def owner_dashboard():
        req_date = (request.args.get("date") or "").strip()
        error_message = ""
        slots: list[dict[str, Any]] = []
        selected_date = req_date

        try:
            initial = get_client().get_slots(req_date or None)
            selected_date = req_date or initial.get("default_date") or initial.get("date")
            if selected_date != initial.get("date"):
                data = get_client().get_slots(selected_date)
            else:
                data = initial
            slots = data.get("slots", [])
        except ApiClientError as exc:
            error_message = exc.message

        total_capacity = sum(s["capacity"] for s in slots)
        total_booked = sum(s["booked_count"] for s in slots)
        total_delivered = sum(s["delivered_count"] for s in slots)
        total_pending = sum(s["pending_count"] for s in slots)
        total_containers = sum(s["total_containers"] for s in slots)
        utilization_pct = round((total_booked / total_capacity) * 100) if total_capacity else 0
        completion_pct = round((total_delivered / total_booked) * 100) if total_booked else 0

        return render_template(
            "owner.html",
            role=session.get("role"),
            selected_date=selected_date,
            slots=slots,
            totals={
                "capacity": total_capacity,
                "booked": total_booked,
                "delivered": total_delivered,
                "pending": total_pending,
                "containers": total_containers,
                "utilization_pct": utilization_pct,
                "completion_pct": completion_pct,
            },
            error_message=error_message,
        )

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
