import os

import requests
from flask import (
    Flask,
    jsonify,
    request,
    send_from_directory
)


app = Flask(
    __name__,
    static_folder="dist",
    static_url_path=""
)


API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://api:5000"
)

API_KEY = os.getenv(
    "API_KEY",
    ""
)


def api_get(path):

    try:

        response = requests.get(
            f"{API_BASE_URL}{path}",
            headers={
                "X-API-Key": API_KEY
            },
            timeout=5
        )

        return (
            response.json(),
            response.status_code
        )

    except requests.RequestException as error:

        return (
            {
                "error":
                    "API Sentinel-X indisponible",

                "details":
                    str(error)
            },
            503
        )


@app.get("/api/status")
def status():

    data, code = api_get(
        "/api/v1/status"
    )

    return jsonify(
        data
    ), code


@app.get("/api/telemetry")
def telemetry():

    limit = max(
        1,
        min(
            request.args.get(
                "limit",
                default=30,
                type=int
            ),
            200
        )
    )

    data, code = api_get(
        f"/api/v1/telemetry?limit={limit}"
    )

    return jsonify(
        data
    ), code


@app.get("/api/ai-results")
def ai_results():

    limit = max(
        1,
        min(
            request.args.get(
                "limit",
                default=30,
                type=int
            ),
            200
        )
    )

    data, code = api_get(
        f"/api/v1/ai-results?limit={limit}"
    )

    return jsonify(
        data
    ), code


@app.get("/health")
def health():

    return jsonify(
        status="up"
    )


@app.route("/")
@app.route("/<path:path>")
def react_app(path=""):

    if path:

        file_path = os.path.join(
            app.static_folder,
            path
        )

        if os.path.exists(
            file_path
        ):

            return send_from_directory(
                app.static_folder,
                path
            )

    return send_from_directory(
        app.static_folder,
        "index.html"
    )