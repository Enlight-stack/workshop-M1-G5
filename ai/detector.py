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
# VERIFICATIONS
# =====================================================

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI est manquant."
    )


# =====================================================
# DEMARRAGE
# =====================================================

print("======================================")
print(" SENTINEL-X - DETECTION IA")
print("======================================")
print()


# =====================================================
# ATTENTE DU MODELE
# =====================================================

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
# CONNEXION MONGODB
# =====================================================

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

client.admin.command(
    "ping"
)

db = client["sentinel"]

telemetry = db["telemetry"]
ai_results = db["ai_results"]


print(
    "[AI] MongoDB connecte."
)

print(
    "[AI] Surveillance active."
)


# =====================================================
# MEMOIRE
# =====================================================

last_processed_id = None


# =====================================================
# ANALYSE
# =====================================================

def analyze(doc):

    try:
        temperature = float(
            doc["temperature"]
        )

        humidity = float(
            doc["humidity"]
        )

        gas = float(
            doc["gas"]
        )

        gas_baseline = float(
            doc["gas_baseline"]
        )

        pir = int(
            bool(
                doc.get(
                    "pir",
                    False
                )
            )
        )

        camera = int(
            bool(
                doc.get(
                    "camera",
                    False
                )
            )
        )

    except (
        KeyError,
        TypeError,
        ValueError
    ) as error:

        print(
            "[AI] Telemetrie invalide :",
            error
        )

        return


    if gas_baseline <= 0:

        print(
            "[AI] Baseline gaz invalide."
        )

        return


    # =================================================
    # FEATURES NORMALISEES PAR RAPPORT A LA BASELINE
    # =================================================

    gas_delta = (
        gas - gas_baseline
    )

    gas_ratio = (
        gas / gas_baseline
    )


    X = np.array(
        [
            [
                temperature,
                humidity,
                gas_delta,
                gas_ratio,
                pir,
                camera
            ]
        ],
        dtype=float
    )


    # =================================================
    # PREDICTION
    # =================================================

    prediction = int(
        model.predict(
            X
        )[0]
    )

    decision_score = float(
        model.decision_function(
            X
        )[0]
    )


    # Isolation Forest :
    #
    #  1 = normal
    # -1 = anomalie

    is_anomaly = (
        prediction == -1
    )


    # =================================================
    # RESULTAT
    # =================================================

    result = {

        "telemetry_id":
            str(
                doc["_id"]
            ),

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

        "gas_baseline":
            gas_baseline,

        "gas_delta":
            gas_delta,

        "gas_ratio":
            gas_ratio,

        "pir":
            bool(
                pir
            ),

        "camera":
            bool(
                camera
            ),

        # Niveau calcule par les regles ESP32.
        # Il est conserve uniquement pour comparaison,
        # PAS utilise comme entree IA.
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


    # =================================================
    # STOCKAGE DU RESULTAT IA
    # =================================================

    ai_results.insert_one(
        result
    )


    # =================================================
    # LOGS
    # =================================================

    print()
    print(
        "[AI] Telemetry :",
        str(
            doc["_id"]
        )
    )

    print(
        "[AI] Temp :",
        temperature
    )

    print(
        "[AI] Humidite :",
        humidity
    )

    print(
        "[AI] Gaz :",
        gas
    )

    print(
        "[AI] Baseline gaz :",
        gas_baseline
    )

    print(
        "[AI] Delta gaz :",
        round(
            gas_delta,
            2
        )
    )

    print(
        "[AI] Ratio gaz :",
        round(
            gas_ratio,
            4
        )
    )

    print(
        "[AI] PIR :",
        pir
    )

    print(
        "[AI] Camera :",
        camera
    )

    print(
        "[AI] Niveau regles :",
        doc.get(
            "level"
        )
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
# BOUCLE TEMPS REEL
# =====================================================

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


        if (
            current_id
            != last_processed_id
        ):

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