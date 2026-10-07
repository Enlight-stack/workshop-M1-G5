import os

import joblib
import numpy as np

from pymongo import MongoClient
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


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


# =====================================================
# VERIFICATIONS
# =====================================================

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI est manquant."
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

client.admin.command("ping")

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
# CREATION DES FEATURES
# =====================================================

features = []

ignored_documents = 0

for doc in documents:

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

        # Evite une division par zero
        if gas_baseline <= 0:
            ignored_documents += 1
            continue

        gas_delta = (
            gas - gas_baseline
        )

        gas_ratio = (
            gas / gas_baseline
        )

        features.append(
            [
                temperature,
                humidity,
                gas_delta,
                gas_ratio,
                pir,
                camera
            ]
        )

    except (
        KeyError,
        TypeError,
        ValueError
    ):
        ignored_documents += 1


# =====================================================
# DATASET NUMPY
# =====================================================

X = np.array(
    features,
    dtype=float
)

print(
    "[AI] Dimensions dataset :",
    X.shape
)

print(
    "[AI] Documents ignores :",
    ignored_documents
)

if len(X) < 50:
    raise RuntimeError(
        "Pas assez de donnees exploitables "
        "apres nettoyage."
    )


# =====================================================
# INFORMATIONS DATASET
# =====================================================

print()
print("[AI] Features utilisees :")
print("     1. temperature")
print("     2. humidity")
print("     3. gas_delta")
print("     4. gas_ratio")
print("     5. pir")
print("     6. camera")

print()

print(
    "[AI] Gas delta moyen :",
    round(
        float(
            np.mean(
                X[:, 2]
            )
        ),
        2
    )
)

print(
    "[AI] Gas ratio moyen :",
    round(
        float(
            np.mean(
                X[:, 3]
            )
        ),
        4
    )
)


# =====================================================
# PIPELINE IA
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

                # Le modele apprend uniquement
                # sur les situations normales.
                # On reste prudent sur le taux
                # d'anomalies internes attendu.
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

print()
print("[AI] Entrainement en cours...")

model.fit(
    X
)

print(
    "[AI] Entrainement termine."
)


# =====================================================
# EVALUATION SUR DATASET D'ENTRAINEMENT
# =====================================================

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

print()
print(
    "[AI] Normaux sur dataset :",
    normal_count
)

print(
    "[AI] Anomalies internes :",
    anomaly_count
)


# =====================================================
# SAUVEGARDE
# =====================================================

os.makedirs(
    os.path.dirname(
        MODEL_PATH
    ),
    exist_ok=True
)

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