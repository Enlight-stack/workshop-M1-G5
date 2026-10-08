import hashlib
import hmac
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
    "vigil-x-g5-backend-bridge"
)

MQTT_CA_CERT = os.getenv(
    "MQTT_CA_CERT",
    "/app/mosquitto.org.crt"
)


# =====================================================
# CONFIG SECURITE HMAC
# =====================================================

HMAC_SECRET = os.getenv(
    "HMAC_SECRET",
    ""
)

HMAC_MAX_AGE_SECONDS = int(
    os.getenv(
        "HMAC_MAX_AGE_SECONDS",
        "30"
    )
)


if not HMAC_SECRET:
    raise RuntimeError(
        "HMAC_SECRET absent. "
        "Le bridge refuse de démarrer sans secret HMAC."
    )


# =====================================================
# PROTECTION ANTI-REJEU
# =====================================================

# On mémorise temporairement les signatures déjà reçues.
#
# Format :
#
# {
#     "signature": timestamp
# }

seen_signatures = {}


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
# CONSTRUCTION DU MESSAGE SIGNE
# =====================================================

def build_signing_string(data):
    """
    Construit exactement la chaîne utilisée
    pour calculer la signature HMAC.

    Cette même structure devra être utilisée
    côté ESP32 / Wokwi.
    """

    return (
        f"{data['device_id']}|"
        f"{float(data['temp']):.1f}|"
        f"{float(data['hum']):.1f}|"
        f"{int(data['gaz'])}|"
        f"{int(data['gaz_base'])}|"
        f"{int(data['pir'])}|"
        f"{int(data['cam'])}|"
        f"{int(data['level'])}|"
        f"{int(data['timestamp'])}"
    )


# =====================================================
# CALCUL HMAC SHA-256
# =====================================================

def calculate_hmac(data):
    """
    Calcule la signature attendue du message.
    """

    signing_string = build_signing_string(
        data
    )

    signature = hmac.new(
        HMAC_SECRET.encode("utf-8"),
        signing_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return signature


# =====================================================
# NETTOYAGE DES SIGNATURES ANCIENNES
# =====================================================

def cleanup_seen_signatures():
    """
    Supprime les signatures trop anciennes
    de la mémoire du bridge.
    """

    now = int(
        time.time()
    )

    expired_signatures = []

    for signature, timestamp in seen_signatures.items():

        if (
            now - timestamp >
            HMAC_MAX_AGE_SECONDS
        ):
            expired_signatures.append(
                signature
            )


    for signature in expired_signatures:

        del seen_signatures[
            signature
        ]


# =====================================================
# VERIFICATION SECURITE
# =====================================================

def verify_security(data):
    """
    Vérifie :

    1. présence timestamp
    2. présence signature
    3. fraîcheur du timestamp
    4. validité HMAC
    5. absence de replay
    """

    # =================================================
    # CHAMPS DE SECURITE
    # =================================================

    required_security_fields = [
        "timestamp",
        "signature"
    ]


    for field in required_security_fields:

        if field not in data:

            print(
                f"[SECURITY] Champ absent : {field}",
                flush=True
            )

            return False


    # =================================================
    # TIMESTAMP
    # =================================================

    try:

        timestamp = int(
            data["timestamp"]
        )

    except (
        ValueError,
        TypeError
    ):

        print(
            "[SECURITY] Timestamp invalide.",
            flush=True
        )

        return False


    now = int(
        time.time()
    )

    age = abs(
        now - timestamp
    )


    if (
        age >
        HMAC_MAX_AGE_SECONDS
    ):

        print(
            "[SECURITY] Message trop ancien "
            "ou timestamp futur. Rejet.",
            flush=True
        )

        print(
            f"[SECURITY] Age du message : {age}s",
            flush=True
        )

        return False


    # =================================================
    # SIGNATURE RECUE
    # =================================================

    received_signature = str(
        data["signature"]
    )


    # =================================================
    # SIGNATURE ATTENDUE
    # =================================================

    try:

        expected_signature = calculate_hmac(
            data
        )

    except Exception as error:

        print(
            "[SECURITY] Erreur calcul HMAC :",
            error,
            flush=True
        )

        return False


    # =================================================
    # COMPARAISON SECURISEE
    # =================================================

    if not hmac.compare_digest(
        received_signature,
        expected_signature
    ):

        print(
            "[SECURITY] Signature HMAC invalide.",
            flush=True
        )

        print(
            "[SECURITY] Message rejeté.",
            flush=True
        )

        return False


    # =================================================
    # PROTECTION ANTI-REPLAY
    # =================================================

    cleanup_seen_signatures()


    if (
        received_signature
        in seen_signatures
    ):

        print(
            "[SECURITY] Replay détecté.",
            flush=True
        )

        print(
            "[SECURITY] Cette signature a "
            "déjà été utilisée.",
            flush=True
        )

        return False


    # =================================================
    # MEMORISATION DE LA SIGNATURE
    # =================================================

    seen_signatures[
        received_signature
    ] = timestamp


    print(
        "[SECURITY] Signature HMAC valide.",
        flush=True
    )

    print(
        "[SECURITY] Timestamp valide.",
        flush=True
    )

    print(
        "[SECURITY] Anti-replay valide.",
        flush=True
    )

    return True


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

        # =============================================
        # DECODAGE
        # =============================================

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


        # =============================================
        # JSON
        # =============================================

        data = json.loads(
            payload
        )


        # =============================================
        # VERIFICATION CHAMPS
        # =============================================

        required_fields = [
            "device_id",
            "temp",
            "hum",
            "gaz",
            "gaz_base",
            "pir",
            "cam",
            "level",
            "timestamp",
            "signature"
        ]


        for field in required_fields:

            if field not in data:

                print(
                    f"[MQTT] Champ manquant : {field}",
                    flush=True
                )

                print(
                    "[SECURITY] Message ignoré.",
                    flush=True
                )

                return


        # =============================================
        # VERIFICATION HMAC + TIMESTAMP + REPLAY
        # =============================================

        if not verify_security(
            data
        ):

            print(
                "[SECURITY] Message MQTT ignoré.",
                flush=True
            )

            return


        # =============================================
        # CREATION TELEMETRIE
        # =============================================

        # On retire volontairement la signature
        # et le timestamp avant d'envoyer à l'API.
        #
        # L'API continue donc de recevoir
        # exactement le même format qu'avant.

        telemetry = {

            "device_id":
                data["device_id"],

            "temp":
                data["temp"],

            "hum":
                data["hum"],

            "gaz":
                data["gaz"],

            "gaz_base":
                data["gaz_base"],

            "pir":
                data["pir"],

            "cam":
                data["cam"],

            "level":
                data["level"]

        }


        # =============================================
        # ENVOI API
        # =============================================

        send_to_api(
            telemetry
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

    ca_certs=
        MQTT_CA_CERT,

    cert_reqs=
        ssl.CERT_REQUIRED,

    tls_version=
        ssl.PROTOCOL_TLS_CLIENT

)


client.tls_insecure_set(
    False
)


# =====================================================
# CONNEXION MQTT
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
# BOUCLE MQTT
# =====================================================

client.loop_forever()