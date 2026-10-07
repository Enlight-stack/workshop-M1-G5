import os
import time

import joblib
import numpy as np

from bson import ObjectId
from pymongo import MongoClient


# =====================================================
# CONFIG
# =====================================================

MONGO_URI = os.getenv("MONGO_URI")

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

while not os.path.exists(MODEL_PATH):

    print("[AI] Modele introuvable.")
    print("[AI] Lance d'abord l'entrainement.")

    time.sleep(5)


# =====================================================
# CHARGEMENT DU MODELE
# =====================================================

model = joblib.load(MODEL_PATH)

print("[AI] Modele charge.")


# =====================================================
# CONNEXION MONGODB
# =====================================================

while True:

    try:

        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        client.admin.command("ping")

        print("[AI] MongoDB connecte.")

        break

    except Exception as error:

        print(
            "[AI] MongoDB indisponible :",
            error
        )

        print(
            "[AI] Nouvelle tentative dans 5 secondes..."
        )

        time.sleep(5)


db = client["sentinel"]

telemetry = db["telemetry"]
ai_results = db["ai_results"]


# =====================================================
# RETROUVER LA DERNIERE TELEMETRIE DEJA ANALYSEE
# =====================================================

last_processed_id = None

last_result = ai_results.find_one(
    sort=[("_id", -1)]
)

if last_result:

    telemetry_id = last_result.get(
        "telemetry_id"
    )

    try:

        last_processed_id = ObjectId(
            telemetry_id
        )

        print(
            "[AI] Reprise apres telemetry :",
            telemetry_id
        )

    except Exception:

        print(
            "[AI] Ancien telemetry_id invalide."
        )

        last_processed_id = None


# =====================================================
# PREMIER DEMARRAGE
# =====================================================

if last_processed_id is None:

    latest_telemetry = telemetry.find_one(
        sort=[("_id", -1)]
    )

    if latest_telemetry:

        last_processed_id = latest_telemetry["_id"]

        print(
            "[AI] Premiere execution."
        )

        print(
            "[AI] Les anciennes telemetries "
            "ne seront pas retraitees."
        )

        print(
            "[AI] Demarrage apres :",
            str(last_processed_id)
        )


print()
print("[AI] Surveillance active.")
print()


# =====================================================
# ANALYSE D'UNE TELEMETRIE
# =====================================================

def analyze(doc):

    telemetry_id = str(
        doc["_id"]
    )

    # -------------------------------------------------
    # EVITER LES DOUBLONS
    # -------------------------------------------------

    existing_result = ai_results.find_one(
        {
            "telemetry_id":
                telemetry_id
        }
    )

    if existing_result:

        print(
            "[AI] Telemetry deja analysee :",
            telemetry_id
        )

        return


    # -------------------------------------------------
    # RECUPERATION DES DONNEES
    # -------------------------------------------------

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
            telemetry_id,
            error
        )

        return


    # -------------------------------------------------
    # VERIFICATION BASELINE GAZ
    # -------------------------------------------------

    if gas_baseline <= 0:

        print(
            "[AI] Baseline gaz invalide :",
            telemetry_id
        )

        return


    # =================================================
    # FEATURES
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
    # PREDICTION IA
    # =================================================

    prediction = int(
        model.predict(X)[0]
    )

    decision_score = float(
        model.decision_function(X)[0]
    )

    is_anomaly = (
        prediction == -1
    )


    # =================================================
    # RESULTAT
    # =================================================

    result = {

        "telemetry_id":
            telemetry_id,

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
            bool(pir),

        "camera":
            bool(camera),

        # Niveau calcule par l'ESP32.
        # Conserve pour comparaison.
        # Il n'est PAS utilise comme feature IA.
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
    # ENREGISTREMENT
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
        telemetry_id
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

        # ---------------------------------------------
        # RECUPERER TOUTES LES NOUVELLES TELEMETRIES
        # ---------------------------------------------

        query = {}

        if last_processed_id is not None:

            query = {
                "_id": {
                    "$gt":
                        last_processed_id
                }
            }


        new_documents = list(
            telemetry
            .find(query)
            .sort("_id", 1)
        )


        # ---------------------------------------------
        # TRAITEMENT DANS L'ORDRE
        # ---------------------------------------------

        for doc in new_documents:

            analyze(doc)

            # Même si la donnée est invalide,
            # on avance pour ne pas bloquer la boucle.
            last_processed_id = (
                doc["_id"]
            )


    except Exception as error:

        print(
            "[AI] Erreur :",
            error
        )


    time.sleep(
        CHECK_INTERVAL
    )