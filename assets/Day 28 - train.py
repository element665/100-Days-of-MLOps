"""Trainer entry point for the MLflow Project.

A DummyClassifier stands in for a real training step. The script
exists only to exercise the MLflow Project configuration — it
accepts the four argparse parameters declared by MLproject, logs
them, advertises a pair of synthetic metrics, and logs the fitted
estimator. No real ML workflow takes place (§2.5).
"""
import argparse
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.dummy import DummyClassifier


def _parse_args():
    # allow_abbrev=False prevents argparse from silently resolving
    # prefixes like --n_est to --n_estimators. Without this, the
    # MLproject typo the lab is designed around would never fire.
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--n_estimators", type=int, default=100)
    parser.add_argument("--max_depth", type=int, default=5)
    parser.add_argument("--test_size", type=float, default=0.2)
    parser.add_argument("--random_seed", type=int, default=42)
    return parser.parse_args()


def main():
    args = _parse_args()

    # Deterministic synthetic "fit" — DummyClassifier performs no learning.
    X = np.array([[0.0, 0.0], [1.0, 1.0]])
    y = np.array([0, 1])
    model = DummyClassifier(strategy="most_frequent").fit(X, y)

    with mlflow.start_run():
        mlflow.log_param("n_estimators", args.n_estimators)
        mlflow.log_param("max_depth", args.max_depth)
        mlflow.log_param("test_size", args.test_size)
        mlflow.log_param("random_seed", args.random_seed)

        # Synthetic metrics advertised for the lab — the values bear no
        # relation to any real evaluation.
        mlflow.log_metric("accuracy", 0.87)
        mlflow.log_metric("f1_score", 0.86)

        mlflow.sklearn.log_model(model, name="model")

        print(
            f"trainer finished: n_estimators={args.n_estimators}, "
            f"max_depth={args.max_depth}"
        )


if __name__ == "__main__":
    main()