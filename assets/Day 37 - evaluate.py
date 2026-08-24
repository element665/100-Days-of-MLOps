"""Stage 4 — Evaluate.

Loads the model and the held-out test set from the training stage
and writes the evaluation metrics (`accuracy`, `f1`, `roc_auc`) to
`reports/evaluation.json` as a flat numeric dict.
"""
import json
import os

import joblib
import pandas as pd
import yaml
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

os.chdir("/root/code/fraud-detection")

with open("configs/pipeline_config.yaml") as f:
    config = yaml.safe_load(f)

target = config["data"]["target_column"]
model_path = config["output"]["model_path"]
report_path = config["output"]["report_path"]

model = joblib.load(model_path)
test_df = pd.read_csv("data/features/test_set.csv")
X_test = test_df.drop(columns=[target])
y_test = test_df[target]

preds = model.predict(X_test)
proba = model.predict_proba(X_test)[:, 1]

metrics = {
    "accuracy": round(float(accuracy_score(y_test, preds)), 6),
    "f1": round(float(f1_score(y_test, preds, zero_division=0)), 6),
    "roc_auc": round(float(roc_auc_score(y_test, proba)), 6),
}

os.makedirs(os.path.dirname(report_path), exist_ok=True)
with open(report_path, "w") as f:
    json.dump(metrics, f, indent=2)

print(f"[evaluate] metrics={metrics}  report_saved={report_path}")