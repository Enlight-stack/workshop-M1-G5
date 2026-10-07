import os
import hmac
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from pymongo import MongoClient, DESCENDING

app = Flask(__name__)

client = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=3000)
alerts = client["sentinel"]["alerts"]
telemetry = client["sentinel"]["telemetry"]

API_KEY = os.environ.get("API_KEY", "")
VALID_STATUS = {"ok", "warning", "critical"}


def authorized():
    sent = request.headers.get("X-API-Key", "")
    return bool(API_KEY) and hmac.compare_digest(sent, API_KEY)


@app.get("/health")
def health():
    return jsonify(status="up")

@app.get("/api/v1/telemetry")
def list_telemetry():

    if not authorized():
        return jsonify(
            error="unauthorized"
        ), 401

    limit = max(
        1,
        min(
            request.args.get(
                "limit",
                default=50,
                type=int
            ),
            200
        )
    )

    docs = []

    for d in (
        telemetry
        .find()
        .sort(
            "received_at",
            DESCENDING
        )
        .limit(limit)
    ):

        d["_id"] = str(
            d["_id"]
        )

        d["received_at"] = (
            d["received_at"]
            .isoformat()
        )

        docs.append(d)

    return jsonify(
        docs
    )

@app.post("/api/v1/alerts")
def create_alert():
    if not authorized():
        return jsonify(error="unauthorized"), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "sensor" not in data or "value" not in data:
        return jsonify(error="'sensor' and 'value' are required"), 400

    status = data.get("status", "ok")
    if status not in VALID_STATUS:
        return jsonify(error="status must be ok, warning or critical"), 400

    doc = {
        "device_id": str(data.get("device_id", "unknown")),
        "sensor": str(data["sensor"]),
        "value": data["value"],
        "unit": str(data.get("unit", "")),
        "status": status,
        "received_at": datetime.now(timezone.utc),
    }
    result = alerts.insert_one(doc)
    return jsonify(status="received", id=str(result.inserted_id)), 201


@app.get("/api/v1/alerts")
def list_alerts():
    if not authorized():
        return jsonify(error="unauthorized"), 401

    limit = max(1, min(request.args.get("limit", default=50, type=int), 200))
    docs = []
    for d in alerts.find().sort("received_at", DESCENDING).limit(limit):
        d["_id"] = str(d["_id"])
        d["received_at"] = d["received_at"].isoformat()
        docs.append(d)
    return jsonify(docs)
@app.post("/api/v1/telemetry")


def create_telemetry():

    if not authorized():
        return jsonify(error="unauthorized"), 401

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):
        return jsonify(
            error="invalid JSON"
        ), 400

    required_fields = [
        "device_id",
        "temp",
        "hum",
        "gaz",
        "gaz_base",
        "pir",
        "cam",
        "level",
    ]

    missing = [
        field
        for field in required_fields
        if field not in data
    ]

    if missing:

        return jsonify(
            error="missing fields",
            fields=missing
        ), 400

    try:

        level = int(
            data["level"]
        )

        if level not in [0, 1, 2]:

            return jsonify(
                error="level must be 0, 1 or 2"
            ), 400

        doc = {

            "device_id":
                str(data["device_id"]),

            "temperature":
                float(data["temp"]),

            "humidity":
                float(data["hum"]),

            "gas":
                int(data["gaz"]),

            "gas_baseline":
                int(data["gaz_base"]),

            "pir":
                bool(data["pir"]),

            "camera":
                bool(data["cam"]),

            "level":
                level,

            "received_at":
                datetime.now(
                    timezone.utc
                )
        }

    except (
        TypeError,
        ValueError
    ):

        return jsonify(
            error="invalid sensor values"
        ), 400


    result = telemetry.insert_one(
        doc
    )

    return jsonify(
        status="stored",
        id=str(result.inserted_id)
    ), 201
    
    