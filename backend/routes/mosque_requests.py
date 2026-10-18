import os

import requests as http_requests
from flask import Blueprint, current_app, jsonify, request

mosque_requests_bp = Blueprint("mosque_requests", __name__)

WEBHOOK_TIMEOUT = 8
MAX_MOSQUE_NAME_LEN = 200
MAX_ADDITIONAL_INFO_LEN = 2000


@mosque_requests_bp.route("/mosque-request", methods=["POST"])
def submit_mosque_request():
    webhook_url = os.environ.get("GSHEET_WEBHOOK_URL")
    if not webhook_url:
        current_app.logger.error("GSHEET_WEBHOOK_URL is not configured")
        return jsonify({"error": "submissions are not configured"}), 503

    data = request.get_json(silent=True) or {}
    mosque_name = (data.get("mosque_name") or "").strip()
    additional_info = (data.get("additional_info") or "").strip()

    if not mosque_name:
        return jsonify({"error": "mosque_name is required"}), 400
    if len(mosque_name) > MAX_MOSQUE_NAME_LEN or len(additional_info) > MAX_ADDITIONAL_INFO_LEN:
        return jsonify({"error": "field too long"}), 400

    payload = {
        "mosque_name": mosque_name,
        "additional_info": additional_info,
        "submitter_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
    }

    try:
        r = http_requests.post(webhook_url, json=payload, timeout=WEBHOOK_TIMEOUT)
        r.raise_for_status()
    except Exception:
        current_app.logger.exception("Sheet webhook failed")
        return jsonify({"error": "submission failed"}), 502

    return jsonify({"ok": True}), 201
