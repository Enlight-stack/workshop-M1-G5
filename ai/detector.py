import os
import time

import joblib
import numpy as np

from pymongo import MongoClient


# =====================================================
# CONFIG
# =====================================================

MONGO_URI = os.getenv(
    "MONGO_URI"
)

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "/app/model/isolation_forest.joblib"
)

CHECK_INTERVAL = 1


# =====================================================
# ATTENTE DU MODELE
# =====================================================

print("======================================")
print(" SENTINEL-X - DETECTION IA")
print("======================================")

print()

while not os.path.exists(
    MODEL_PATH
):

    print(
        "[AI] Modele introuvable."
    )

    print(
        "[AI] Lance d'abord "
        "l'entrainement."
    )

    time.sleep(5)


# =====================================================
# CHARGEMENT MODELE
# =====================================================

model = joblib.load(
    MODEL_PATH
)

print(
    "[AI] Modele charge."
)


# =====================================================
# MONGODB
# =====================================================

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client["sentinel"]

telemetry = db["telemetry"]
ai_results = db["ai_results"]


# =====================================================
# MEMOIRE
# =====================================================

last_processed_id = None


# =====================================================
# ANALYSE
# =====================================================

def analyze(doc):

    temperature = float(
        doc.get(
            "temperature",
            0
        )
    )

    humidity = float(
        doc.get(
            "humidity",
            0
        )
    )

    gas = float(
        doc.get(
            "gas",
            0
        )
    )

    gas_baseline = float(
        doc.get(
            "gas_baseline",
            0
        )
    )

    gas_delta = (
        gas - gas_baseline
    )

    pir = int(
        doc.get(
            "pir",
            False
        )
    )

    camera = int(
        doc.get(
            "camera",
            False
        )
    )

    X = np.array(
        [
            [
                temperature,
                humidity,
                gas,
                gas_delta,
                pir,
                camera
            ]
        ],
        dtype=float
    )


    prediction = int(
        model.predict(X)[0]
    )

    decision_score = float(
        model.decision_function(X)[0]
    )


    # Isolation Forest :
    #
    #  1  = normal
    # -1  = anomalie

    is_anomaly = (
        prediction == -1
    )


    result = {

        "telemetry_id":
            str(doc["_id"]),

        "device_id":
            doc.get(
                "device_id"
            ),

        "temperature":
            temperature,

        "humidity":
            humidity,

        "gas":
            gas,

        "gas_delta":
            gas_delta,

        "pir":
            bool(pir),

        "camera":
            bool(camera),

        "rule_level":
            doc.get(
                "level"
            ),

        "is_anomaly":
            is_anomaly,

        "anomaly_score":
            decision_score,

        "received_at":
            doc.get(
                "received_at"
            )
    }


    ai_results.insert_one(
        result
    )


    print()
    print(
        "[AI] Telemetry :",
        str(doc["_id"])
    )

    print(
        "[AI] Score :",
        round(
            decision_score,
            4
        )
    )

    if is_anomaly:

        print(
            "[AI] >>> ANOMALIE DETECTEE <<<"
        )

    else:

        print(
            "[AI] Etat normal."
        )


# =====================================================
# BOUCLE
# =====================================================

print(
    "[AI] Surveillance active."
)

while True:

    try:

        latest = telemetry.find_one(
            sort=[
                (
                    "received_at",
                    -1
                )
            ]
        )

        if latest is None:

            time.sleep(
                CHECK_INTERVAL
            )

            continue


        current_id = str(
            latest["_id"]
        )


        if current_id != last_processed_id:

            analyze(
                latest
            )

            last_processed_id = (
                current_id
            )


    except Exception as error:

        print(
            "[AI] Erreur :",
            error
        )


    time.sleep(
        CHECK_INTERVAL
    )