import os
import hmac
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from pymongo import MongoClient, DESCENDING


# =====================================================
# APP
# =====================================================

app = Flask(__name__)


# =====================================================
# MONGODB
# =====================================================

client = MongoClient(
    os.environ["MONGO_URI"],
    serverSelectionTimeoutMS=3000
)

db = client["sentinel"]

alerts = db["alerts"]
telemetry = db["telemetry"]
ai_results = db["ai_results"]


# =====================================================
# CONFIG
# =====================================================

API_KEY = os.environ.get(
    "API_KEY",
    ""
)

VALID_STATUS = {
    "ok",
    "warning",
    "critical"
}


# =====================================================
# AUTH
# =====================================================

def authorized():

    sent = request.headers.get(
        "X-API-Key",
        ""
    )

    return (
        bool(API_KEY)
        and hmac.compare_digest(
            sent,
            API_KEY
        )
    )


# =====================================================
# HEALTH
# =====================================================

@app.get("/health")
def health():

    return jsonify(
        status="up"
    )


# =====================================================
# TELEMETRY - GET
# =====================================================

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


        if d.get("received_at"):

            d["received_at"] = (
                d["received_at"]
                .isoformat()
            )


        docs.append(
            d
        )


    return jsonify(
        docs
    )


# =====================================================
# TELEMETRY - POST
# =====================================================

@app.post("/api/v1/telemetry")
def create_telemetry():

    if not authorized():

        return jsonify(
            error="unauthorized"
        ), 401


    data = request.get_json(
        silent=True
    )


    if not isinstance(
        data,
        dict
    ):

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
        "level"
    ]


    missing = [

        field

        for field
        in required_fields

        if field
        not in data
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


        if level not in [
            0,
            1,
            2
        ]:

            return jsonify(
                error="level must be 0, 1 or 2"
            ), 400


        doc = {

            "device_id":
                str(
                    data["device_id"]
                ),

            "temperature":
                float(
                    data["temp"]
                ),

            "humidity":
                float(
                    data["hum"]
                ),

            "gas":
                int(
                    data["gaz"]
                ),

            "gas_baseline":
                int(
                    data["gaz_base"]
                ),

            "pir":
                bool(
                    data["pir"]
                ),

            "camera":
                bool(
                    data["cam"]
                ),

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
        id=str(
            result.inserted_id
        )
    ), 201


# =====================================================
# ALERTS - POST
# =====================================================

@app.post("/api/v1/alerts")
def create_alert():

    if not authorized():

        return jsonify(
            error="unauthorized"
        ), 401


    data = request.get_json(
        silent=True
    )


    if (
        not isinstance(
            data,
            dict
        )
        or "sensor"
        not in data
        or "value"
        not in data
    ):

        return jsonify(
            error="'sensor' and 'value' are required"
        ), 400


    status = data.get(
        "status",
        "ok"
    )


    if status not in VALID_STATUS:

        return jsonify(
            error="status must be ok, warning or critical"
        ), 400


    doc = {

        "device_id":
            str(
                data.get(
                    "device_id",
                    "unknown"
                )
            ),

        "sensor":
            str(
                data["sensor"]
            ),

        "value":
            data["value"],

        "unit":
            str(
                data.get(
                    "unit",
                    ""
                )
            ),

        "status":
            status,

        "received_at":
            datetime.now(
                timezone.utc
            )
    }


    result = alerts.insert_one(
        doc
    )


    return jsonify(
        status="received",
        id=str(
            result.inserted_id
        )
    ), 201


# =====================================================
# ALERTS - GET
# =====================================================

@app.get("/api/v1/alerts")
def list_alerts():

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
        alerts
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


        if d.get("received_at"):

            d["received_at"] = (
                d["received_at"]
                .isoformat()
            )


        docs.append(
            d
        )


    return jsonify(
        docs
    )


# =====================================================
# AI RESULTS - GET
# =====================================================

@app.get("/api/v1/ai-results")
def list_ai_results():

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
        ai_results
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


        if d.get("received_at"):

            d["received_at"] = (
                d["received_at"]
                .isoformat()
            )


        docs.append(
            d
        )


    return jsonify(
        docs
    )


# =====================================================
# STATUS GLOBAL - GET
# =====================================================

@app.get("/api/v1/status")
def system_status():

    if not authorized():

        return jsonify(
            error="unauthorized"
        ), 401


    latest_telemetry = telemetry.find_one(
        sort=[
            (
                "received_at",
                DESCENDING
            )
        ]
    )


    latest_ai = ai_results.find_one(
        sort=[
            (
                "received_at",
                DESCENDING
            )
        ]
    )


    if latest_telemetry is None:

        return jsonify(
            status="no_data"
        ), 404


    latest_telemetry["_id"] = str(
        latest_telemetry["_id"]
    )


    if latest_telemetry.get(
        "received_at"
    ):

        latest_telemetry[
            "received_at"
        ] = (

            latest_telemetry[
                "received_at"
            ]
            .isoformat()
        )


    if latest_ai:

        latest_ai["_id"] = str(
            latest_ai["_id"]
        )


        if latest_ai.get(
            "received_at"
        ):

            latest_ai[
                "received_at"
            ] = (

                latest_ai[
                    "received_at"
                ]
                .isoformat()
            )


    return jsonify(

        telemetry=
            latest_telemetry,

        ai=
            latest_ai
    )