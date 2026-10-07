import os
from pathlib import Path

import joblib
import numpy as np

from pymongo import MongoClient

from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


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
# PARAMETRES GAZ
# =====================================================

# Le gaz n'est réellement utilisé par l'IA
# que lorsqu'il dépasse fortement sa baseline.

GAS_DELTA_THRESHOLD = 700.0

GAS_RATIO_THRESHOLD = 1.35


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


print(
    "[TRAIN] MongoDB connecte.",
    flush=True
)


db = client[
    "sentinel"
]

telemetry = db[
    "telemetry"
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
    # Variation normale :
    # gaz neutralisé pour le modèle.
    # -------------------------------------------------

    if not significant_gas_rise:

        return (
            0.0,
            1.0,
            False
        )


    # -------------------------------------------------
    # Forte hausse :
    # le modèle voit réellement le gaz.
    # -------------------------------------------------

    return (
        gas_delta,
        gas_ratio,
        True
    )


# =====================================================
# RECUPERATION DES DONNEES NORMALES
# =====================================================

documents = list(

    telemetry.find(
        {
            "level": 0
        }
    )

)


print(
    f"[TRAIN] Mesures normales trouvees : {len(documents)}",
    flush=True
)


features = []

ignored_documents = 0

gas_significant_count = 0


# =====================================================
# PREPARATION DATASET
# =====================================================

for document in documents:

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


    gas = safe_float(
        document.get(
            "gas"
        )
    )


    gas_baseline = safe_float(
        document.get(
            "gas_baseline"
        )
    )


    if gas_baseline <= 0:

        ignored_documents += 1

        continue


    gas_delta_ai, gas_ratio_ai, significant = (
        normalize_gas_for_ai(
            gas,
            gas_baseline
        )
    )


    if significant:

        gas_significant_count += 1


    pir = int(
        bool(
            document.get(
                "pir",
                False
            )
        )
    )


    camera = int(
        bool(
            document.get(
                "camera",
                False
            )
        )
    )


    features.append(
        [
            temperature,
            humidity,
            gas_delta_ai,
            gas_ratio_ai,
            pir,
            camera
        ]
    )


# =====================================================
# VALIDATION
# =====================================================

if len(
    features
) < 50:

    raise RuntimeError(
        "Pas assez de mesures normales pour entrainer le modele."
    )


X = np.array(
    features,
    dtype=float
)


print(
    f"[TRAIN] Dimensions dataset : {X.shape}",
    flush=True
)


print(
    f"[TRAIN] Documents ignores : {ignored_documents}",
    flush=True
)


print(
    "[TRAIN] Fortes variations gaz dans dataset normal : "
    f"{gas_significant_count}",
    flush=True
)


# =====================================================
# PIPELINE
# =====================================================

model = Pipeline(
    [
        (
            "scaler",
            StandardScaler()
        ),

        (
            "isolation_forest",

            IsolationForest(
                n_estimators=300,
                contamination=0.03,
                random_state=42,
                n_jobs=-1
            )
        )
    ]
)


# =====================================================
# ENTRAINEMENT
# =====================================================

model.fit(
    X
)


predictions = model.predict(
    X
)


normal_count = int(
    np.sum(
        predictions == 1
    )
)


anomaly_count = int(
    np.sum(
        predictions == -1
    )
)


print(
    "[TRAIN] Entrainement termine.",
    flush=True
)


print(
    f"[TRAIN] Normaux sur dataset : {normal_count}",
    flush=True
)


print(
    f"[TRAIN] Anomalies internes : {anomaly_count}",
    flush=True
)


# =====================================================
# SAUVEGARDE
# =====================================================

model_path = Path(
    MODEL_PATH
)


model_path.parent.mkdir(
    parents=True,
    exist_ok=True
)


joblib.dump(
    model,
    model_path
)


print(
    f"[TRAIN] Modele sauvegarde : {MODEL_PATH}",
    flush=True
)