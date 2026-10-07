import json
import os
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
        "1883"
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
            f"{response.text}"
        )

    except requests.RequestException as error:

        print(
            "[API] Erreur :",
            error
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
        "[MQTT] Connecté au broker."
    )

    print(
        "[MQTT] Topic :",
        MQTT_TOPIC
    )

    client.subscribe(
        MQTT_TOPIC
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

        print()
        print(
            "[MQTT] Message reçu :"
        )

        print(payload)

        data = json.loads(
            payload
        )


        # Vérification minimale

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
                    f"[MQTT] Champ manquant : {field}"
                )

                return


        # Envoi vers Flask

        send_to_api(
            data
        )

    except json.JSONDecodeError:

        print(
            "[MQTT] JSON invalide."
        )

    except Exception as error:

        print(
            "[MQTT] Erreur :",
            error
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
# CONNEXION
# =====================================================

while True:

    try:

        print(
            f"[MQTT] Connexion à "
            f"{MQTT_HOST}:{MQTT_PORT}..."
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
            error
        )

        print(
            "[MQTT] Nouvelle tentative "
            "dans 5 secondes..."
        )

        time.sleep(5)


# =====================================================
# BOUCLE
# =====================================================

client.loop_forever()