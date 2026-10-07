import os
import time

from collections import (
    defaultdict,
    deque
)

from datetime import (
    datetime,
    timezone
)

import joblib
import numpy as np

from bson import ObjectId
from pymongo import MongoClient


# =====================================================
# CONFIGURATION
# =====================================================

MONGO_URI = os.getenv(
    "MONGO_URI"
)

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "/app/model/isolation_forest.joblib"
)


if not MONGO_URI:

    raise RuntimeError(
        "MONGO_URI est manquant."
    )


# =====================================================
# PARAMETRES
# =====================================================

# Moyenne glissante MQ-2
GAS_WINDOW_SIZE = 5


# Forte hausse nécessaire avant que le gaz
# influence réellement l'Isolation Forest.
GAS_DELTA_THRESHOLD = 700.0

GAS_RATIO_THRESHOLD = 1.35


# Nombre d'anomalies consécutives avant
# ACTIVITE SUSPECTE.
ANOMALY_CONFIRMATION_COUNT = 2


# =====================================================
# ETAT PAR DEVICE
# =====================================================

gas_history = defaultdict(

    lambda: deque(
        maxlen=GAS_WINDOW_SIZE
    )

)


anomaly_streak = defaultdict(
    int
)


# =====================================================
# MODELE
# =====================================================

while True:

    try:

        model = joblib.load(
            MODEL_PATH
        )


        print(
            "[AI] Modele charge.",
            flush=True
        )


        break

    except Exception as error:

        print(
            "[AI] Impossible de charger le modele : "
            f"{error}",
            flush=True
        )


        time.sleep(
            5
        )


# =====================================================
# MONGODB
# =====================================================

while True:

    try:

        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )


        client.admin.command(
            "ping"
        )


        print(
            "[AI] MongoDB connecte.",
            flush=True
        )


        break

    except Exception as error:

        print(
            "[AI] MongoDB indisponible : "
            f"{error}",
            flush=True
        )


        time.sleep(
            5
        )


db = client[
    "sentinel"
]

telemetry = db[
    "telemetry"
]

ai_results = db[
    "ai_results"
]


# =====================================================
# HELPERS
# =====================================================

def safe_float(
    value,
    default=0.0
):

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return default


def safe_bool(
    value
):

    return bool(
        value
    )


def normalize_gas_for_ai(
    gas_value,
    gas_baseline
):

    if gas_baseline <= 0:

        return (
            None,
            None,
            False
        )


    gas_delta = (
        gas_value -
        gas_baseline
    )


    gas_ratio = (
        gas_value /
        gas_baseline
    )


    significant_gas_rise = (

        gas_delta >=
        GAS_DELTA_THRESHOLD

        or

        gas_ratio >=
        GAS_RATIO_THRESHOLD

    )


    # -------------------------------------------------
    # Fluctuation classique MQ-2
    # -------------------------------------------------

    if not significant_gas_rise:

        return (
            0.0,
            1.0,
            False
        )


    # -------------------------------------------------
    # Forte hausse réelle
    # -------------------------------------------------

    return (
        gas_delta,
        gas_ratio,
        True
    )


# =====================================================
# REPRISE APRES REDEMARRAGE
# =====================================================

last_processed_id = None


last_result = ai_results.find_one(

    sort=[
        (
            "_id",
            -1
        )
    ]

)


if last_result:

    telemetry_id = last_result.get(
        "telemetry_id"
    )


    if telemetry_id:

        try:

            last_processed_id = ObjectId(
                telemetry_id
            )


            print(
                "[AI] Reprise apres telemetry : "
                f"{last_processed_id}",
                flush=True
            )


        except Exception:

            last_processed_id = None


# =====================================================
# PREMIER DEMARRAGE
# =====================================================

if last_processed_id is None:

    latest_telemetry = telemetry.find_one(

        sort=[
            (
                "_id",
                -1
            )
        ]

    )


    if latest_telemetry:

        last_processed_id = (
            latest_telemetry[
                "_id"
            ]
        )


        print(
            "[AI] Demarrage apres telemetry existante : "
            f"{last_processed_id}",
            flush=True
        )


# =====================================================
# ANALYSE
# =====================================================

def analyze(
    document
):

    telemetry_id = str(
        document[
            "_id"
        ]
    )


    # =================================================
    # ANTI-DOUBLON
    # =================================================

    existing = ai_results.find_one(
        {
            "telemetry_id":
                telemetry_id
        }
    )


    if existing:

        return


    # =================================================
    # DONNEES
    # =================================================

    device_id = document.get(
        "device_id",
        "unknown"
    )


    temperature = safe_float(
        document.get(
            "temperature"
        )
    )


    humidity = safe_float(
        document.get(
            "humidity"
        )
    )


    gas_raw = safe_float(
        document.get(
            "gas"
        )
    )


    gas_baseline = safe_float(
        document.get(
            "gas_baseline"
        )
    )


    pir = safe_bool(
        document.get(
            "pir"
        )
    )


    camera = safe_bool(
        document.get(
            "camera"
        )
    )


    rule_level = int(
        document.get(
            "level",
            0
        )
    )


    if gas_baseline <= 0:

        print(
            "[AI] Baseline gaz invalide : "
            f"{telemetry_id}",
            flush=True
        )

        return


    # =================================================
    # MOYENNE GLISSANTE DU GAZ
    # =================================================

    gas_history[
        device_id
    ].append(
        gas_raw
    )


    gas_smoothed = (

        sum(
            gas_history[
                device_id
            ]
        )

        /

        len(
            gas_history[
                device_id
            ]
        )

    )


    # =================================================
    # DELTA REEL
    # =================================================

    raw_gas_delta = (
        gas_smoothed -
        gas_baseline
    )


    raw_gas_ratio = (
        gas_smoothed /
        gas_baseline
    )


    # =================================================
    # GAZ POUR IA
    # =================================================

    (
        gas_delta_ai,
        gas_ratio_ai,
        gas_significant

    ) = normalize_gas_for_ai(

        gas_smoothed,
        gas_baseline

    )


    # =================================================
    # FEATURES
    # =================================================

    features = np.array(
        [
            [
                temperature,
                humidity,

                gas_delta_ai,
                gas_ratio_ai,

                int(
                    pir
                ),

                int(
                    camera
                )
            ]
        ],
        dtype=float
    )


    # =================================================
    # ISOLATION FOREST
    # =================================================

    prediction = model.predict(
        features
    )[0]


    anomaly_score = float(

        model.decision_function(
            features
        )[0]

    )


    model_anomaly = (
        prediction == -1
    )


    # =================================================
    # CONFIRMATION TEMPORELLE
    # =================================================

    if model_anomaly:

        anomaly_streak[
            device_id
        ] += 1

    else:

        anomaly_streak[
            device_id
        ] = 0


    confirmed_anomaly = (

        anomaly_streak[
            device_id
        ]

        >=

        ANOMALY_CONFIRMATION_COUNT

    )


    # =================================================
    # RESULTAT
    # =================================================

    result = {

        "telemetry_id":
            telemetry_id,

        "device_id":
            device_id,

        "temperature":
            temperature,

        "humidity":
            humidity,

        # ---------------------------------------------
        # Donnée capteur réelle
        # ---------------------------------------------

        "gas":
            gas_raw,

        "gas_smoothed":
            round(
                gas_smoothed,
                2
            ),

        "gas_baseline":
            gas_baseline,

        # ---------------------------------------------
        # Variation réelle
        # ---------------------------------------------

        "gas_delta":
            round(
                raw_gas_delta,
                2
            ),

        "gas_ratio":
            round(
                raw_gas_ratio,
                6
            ),

        # ---------------------------------------------
        # Gaz transmis au modèle
        # ---------------------------------------------

        "gas_delta_ai":
            round(
                gas_delta_ai,
                2
            ),

        "gas_ratio_ai":
            round(
                gas_ratio_ai,
                6
            ),

        "gas_significant":
            bool(
                gas_significant
            ),

        # ---------------------------------------------
        # Autres signaux
        # ---------------------------------------------

        "pir":
            pir,

        "camera":
            camera,

        "rule_level":
            rule_level,

        # ---------------------------------------------
        # IA
        # ---------------------------------------------

        "anomaly_score":
            anomaly_score,

        "model_anomaly":
            bool(
                model_anomaly
            ),

        "anomaly_streak":
            anomaly_streak[
                device_id
            ],

        "is_anomaly":
            bool(
                confirmed_anomaly
            ),

        # ---------------------------------------------
        # Dates
        # ---------------------------------------------

        "received_at":
            document.get(
                "received_at",
                datetime.now(
                    timezone.utc
                )
            ),

        "analyzed_at":
            datetime.now(
                timezone.utc
            )

    }


    ai_results.insert_one(
        result
    )


    # =================================================
    # LOG
    # =================================================

    state = (

        "ACTIVITE SUSPECTE"

        if confirmed_anomaly

        else "NORMAL"

    )


    gas_state = (

        "IMPORTANT"

        if gas_significant

        else "IGNORE"

    )


    print(
        (
            f"[AI] {device_id} | "

            f"temp={temperature:.1f} | "

            f"hum={humidity:.1f} | "

            f"gas_raw={gas_raw:.0f} | "

            f"gas_avg={gas_smoothed:.1f} | "

            f"delta={raw_gas_delta:.1f} | "

            f"ratio={raw_gas_ratio:.3f} | "

            f"gas_ai={gas_state} | "

            f"model_anomaly={model_anomaly} | "

            f"streak={anomaly_streak[device_id]} | "

            f"etat={state}"
        ),
        flush=True
    )


# =====================================================
# BOUCLE PRINCIPALE
# =====================================================

print(
    "[AI] Surveillance active.",
    flush=True
)


while True:

    try:

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
                .find(
                    query
                )
                .sort(
                    "_id",
                    1
                )

        )


        for document in new_documents:

            try:

                analyze(
                    document
                )


            except Exception as error:

                print(
                    "[AI] Erreur analyse telemetry "
                    f"{document.get('_id')} : "
                    f"{error}",
                    flush=True
                )


            finally:

                last_processed_id = (
                    document[
                        "_id"
                    ]
                )


        time.sleep(
            0.5
        )


    except Exception as error:

        print(
            "[AI] Erreur boucle principale : "
            f"{error}",
            flush=True
        )


        time.sleep(
            2
        )