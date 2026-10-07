import os

import joblib
import numpy as np

from pymongo import MongoClient
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


# =====================================================
# CONFIG
# =====================================================

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://sentinelAdmin:password@mongo:27017/?authSource=admin"
)

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "/app/model/isolation_forest.joblib"
)


# =====================================================
# CONNEXION MONGODB
# =====================================================

print("======================================")
print(" SENTINEL-X - ENTRAINEMENT IA")
print("======================================")

print()
print("[AI] Connexion a MongoDB...")


client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client["sentinel"]
telemetry = db["telemetry"]


# =====================================================
# CHARGEMENT DES DONNEES NORMALES
# =====================================================

documents = list(
    telemetry.find(
        {
            "level": 0
        }
    )
)

print(
    f"[AI] Mesures normales trouvees : "
    f"{len(documents)}"
)


if len(documents) < 50:

    raise RuntimeError(
        "Pas assez de donnees normales "
        "pour entrainer le modele."
    )


# =====================================================
# FEATURES
# =====================================================

features = []

for doc in documents:

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

    features.append(
        [
            temperature,
            humidity,
            gas,
            gas_delta,
            pir,
            camera
        ]
    )


X = np.array(
    features,
    dtype=float
)


print(
    "[AI] Dimensions dataset :",
    X.shape
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
                n_estimators=200,
                contamination=0.05,
                random_state=42
            )
        )
    ]
)


# =====================================================
# ENTRAINEMENT
# =====================================================

print()
print("[AI] Entrainement en cours...")

model.fit(X)

print("[AI] Entrainement termine.")


# =====================================================
# SAUVEGARDE
# =====================================================

joblib.dump(
    model,
    MODEL_PATH
)

print()
print(
    "[AI] Modele sauvegarde :",
    MODEL_PATH
)

print()
print("======================================")
print(" ENTRAINEMENT TERMINE")
print("======================================")