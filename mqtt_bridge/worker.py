import json
import os
import ssl
import time

import paho.mqtt.client as mqtt
import requests


# =====================================================
# CONFIG MQTT
# =====================================================

MQTT_HOST = os.getenv(
    "MQTT_HOST",
    "test.mosquitto.org"
)

MQTT_PORT = int(
    os.getenv(
        "MQTT_PORT",
        "8883"
    )
)

MQTT_TOPIC = os.getenv(
    "MQTT_TOPIC",
    "sentinel-x-g5-2026/sensors"
)

MQTT_CLIENT_ID = os.getenv(
    "MQTT_CLIENT_ID",
    "sentinel-x-backend-bridge"
)

MQTT_CA_CERT = os.getenv(
    "MQTT_CA_CERT",
    "/app/mosquitto.org.crt"
)


# =====================================================
# CONFIG API
# =====================================================

API_URL = os.getenv(
    "API_URL",
    "http://api:5000/api/v1/telemetry"
)

API_KEY = os.getenv(
    "API_KEY",
    ""
)


# =====================================================
# ENVOI VERS API
# =====================================================

def send_to_api(data):

    try:

        response = requests.post(
            API_URL,
            json=data,
            headers={
                "X-API-Key": API_KEY
            },
            timeout=5
        )

        print(
            f"[API] {response.status_code} "
            f"{response.text}",
            flush=True
        )

    except requests.RequestException as error:

        print(
            "[API] Erreur :",
            error,
            flush=True
        )


# =====================================================
# MQTT CONNECT
# =====================================================

def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties
):

    print(
        f"[MQTT] Connexion TLS établie avec "
        f"{MQTT_HOST}:{MQTT_PORT}",
        flush=True
    )

    print(
        "[MQTT] Code connexion :",
        reason_code,
        flush=True
    )

    if reason_code == 0:

        client.subscribe(
            MQTT_TOPIC
        )

        print(
            "[MQTT] Abonné au topic :",
            MQTT_TOPIC,
            flush=True
        )

    else:

        print(
            "[MQTT] Connexion MQTT refusée.",
            flush=True
        )


# =====================================================
# MQTT MESSAGE
# =====================================================

def on_message(
    client,
    userdata,
    message
):

    try:

        payload = (
            message
            .payload
            .decode("utf-8")
        )

        print(
            "[MQTT] Message reçu :",
            flush=True
        )

        print(
            payload,
            flush=True
        )

        data = json.loads(
            payload
        )


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


        for field in required_fields:

            if field not in data:

                print(
                    f"[MQTT] Champ manquant : {field}",
                    flush=True
                )

                return


        send_to_api(
            data
        )

    except json.JSONDecodeError:

        print(
            "[MQTT] JSON invalide.",
            flush=True
        )

    except Exception as error:

        print(
            "[MQTT] Erreur :",
            error,
            flush=True
        )


# =====================================================
# CLIENT MQTT
# =====================================================

client = mqtt.Client(
    callback_api_version=
        mqtt.CallbackAPIVersion.VERSION2,

    client_id=
        MQTT_CLIENT_ID
)

client.on_connect = on_connect
client.on_message = on_message


# =====================================================
# TLS
# =====================================================

print(
    "[MQTT] Chargement du certificat CA :",
    MQTT_CA_CERT,
    flush=True
)

client.tls_set(
    ca_certs=MQTT_CA_CERT,
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLS_CLIENT
)

client.tls_insecure_set(
    False
)


# =====================================================
# CONNEXION
# =====================================================

while True:

    try:

        print(
            f"[MQTT] Connexion sécurisée à "
            f"{MQTT_HOST}:{MQTT_PORT}...",
            flush=True
        )

        client.connect(
            MQTT_HOST,
            MQTT_PORT,
            60
        )

        break

    except Exception as error:

        print(
            "[MQTT] Broker indisponible :",
            error,
            flush=True
        )

        print(
            "[MQTT] Nouvelle tentative "
            "dans 5 secondes...",
            flush=True
        )

        time.sleep(
            5
        )


# =====================================================
# BOUCLE
# =====================================================

client.loop_forever()