"""Config-driven training script.

Every parameter comes from `/root/code/fraud-detection/configs/train_config.yaml`.
No values are hardcoded. The scaffold is authoritative — the lab's
fix belongs in the YAML config, not in this file.

The estimator is resolved through a small registry of supported
classes; unknown class names fail fast with a clear diagnostic so the
config bug surfaces before a confusing sklearn error.
"""
import os
import sys
import yaml
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

CONFIG_PATH = "/root/code/fraud-detection/configs/train_config.yaml"

ESTIMATOR_REGISTRY = {
    "RandomForestClassifier": RandomForestClassifier,
    "GradientBoostingClassifier": GradientBoostingClassifier,
    "LogisticRegression": LogisticRegression,
}


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    config = load_config(CONFIG_PATH)

    estimator_name = config["model"]["type"]
    if estimator_name not in ESTIMATOR_REGISTRY:
        print(
            f"ERROR: unknown estimator type {estimator_name!r}. "
            f"Supported: {sorted(ESTIMATOR_REGISTRY)}"
        )
        sys.exit(1)
    estimator_cls = ESTIMATOR_REGISTRY[estimator_name]

    train_path = config["data"]["train_path"]
    target_column = config["data"]["target_column"]
    model_path = config["output"]["model_path"]

    df = pd.read_csv(train_path)
    if target_column not in df.columns:
        print(
            f"ERROR: target column {target_column!r} not found in {train_path}. "
            f"Available columns: {list(df.columns)}"
        )
        sys.exit(2)

    X = df.drop(columns=[target_column])
    y = df[target_column]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    estimator_kwargs = {k: v for k, v in config["model"].items() if k != "type"}
    model = estimator_cls(**estimator_kwargs)

    mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
    mlflow.set_experiment(config["mlflow"]["experiment_name"])

    with mlflow.start_run():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        accuracy = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds)

        mlflow.log_param("model_type", estimator_name)
        mlflow.log_params(estimator_kwargs)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)

        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(model, model_path)
        mlflow.sklearn.log_model(model, name="model")

        print(f"accuracy={accuracy:.4f}, f1_score={f1:.4f}")
        print(f"model saved to {model_path}")


if __name__ == "__main__":
    main()