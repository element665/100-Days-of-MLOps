"""Trivial training stub for the `fraud-detector:v1` registry-push
lab. Fits a tiny RandomForest inline so the built image carries a
ready-to-run `/app/model.pkl` artefact."""
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

X = np.array([
    [25.0, 8, 1],
    [1250.0, 22, 4],
    [45.0, 12, 2],
    [890.0, 2, 3],
    [3200.0, 23, 5],
])
y = np.array([0, 1, 0, 0, 1])

model = RandomForestClassifier(n_estimators=5, random_state=42)
model.fit(X, y)

joblib.dump(model, "/app/model.pkl")
print("Model saved to /app/model.pkl")