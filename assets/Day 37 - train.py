"""Stage 3 — Train.

Reads the feature matrix produced by the featurize stage, splits out
a stratified held-out test set (persisted to `data/features/test_set.csv`
so the evaluation stage scores on the same rows), fits a RandomForest
per the config, and writes the pickled model to `models/model.pkl`.

Like every stage in the pipeline, this one must read its immediate
predecessor's output — the engineered feature matrix — so the model is
trained on the featurized data, with the engineered columns present.
"""
import os

import joblib
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

os.chdir("/root/code/fraud-detection")

with open("configs/pipeline_config.yaml") as f:
    config = yaml.safe_load(f)

features_path = config["data"]["processed_path"]
target = config["data"]["target_column"]
test_size = config["data"]["test_size"]
seed = config["data"]["random_state"]
model_path = config["output"]["model_path"]

df = pd.read_csv(features_path)
X = df.drop(columns=[target])
y = df[target]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=test_size, stratify=y, random_state=seed,
)

test_set_path = "data/features/test_set.csv"
X_test_df = X_test.copy()
X_test_df[target] = y_test
X_test_df.to_csv(test_set_path, index=False)

model = RandomForestClassifier(
    n_estimators=config["model"]["n_estimators"],
    max_depth=config["model"]["max_depth"],
    random_state=config["model"]["random_state"],
)
model.fit(X_train, y_train)

os.makedirs(os.path.dirname(model_path), exist_ok=True)
joblib.dump(model, model_path)

print(f"[train] rows={len(df)}  model_saved={model_path}")