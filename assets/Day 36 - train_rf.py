"""Train a RandomForest candidate for the bake-off.

Logs a single MLflow run in the `bakeoff` experiment with:
  - tags.candidate = "random_forest"
  - params: n_estimators, max_depth
  - metrics.f1_score (mean of 3-fold CV, stratified, random_state=42)
"""
import mlflow
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

TRACKING_URI = "http://localhost:5000"
EXPERIMENT = "bakeoff"
TRAIN_CSV = "/root/code/fraud-detection/data/train.csv"

CANDIDATE = "random_forest"
PARAMS = {"n_estimators": 200, "max_depth": 8}


def main():
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)

    df = pd.read_csv(TRAIN_CSV)
    X = df.drop(columns=["is_fraud"])
    y = df["is_fraud"]

    model = RandomForestClassifier(random_state=42, **PARAMS)
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    scores = []
    for tr, te in cv.split(X, y):
        model.fit(X.iloc[tr], y.iloc[tr])
        scores.append(f1_score(y.iloc[te], model.predict(X.iloc[te])))
    mean_f1 = float(sum(scores) / len(scores))

    with mlflow.start_run(run_name=CANDIDATE) as run:
        mlflow.set_tag("candidate", CANDIDATE)
        mlflow.log_params(PARAMS)
        mlflow.log_metric("f1_score", mean_f1)
        print(f"{CANDIDATE}: f1_score={mean_f1:.4f}  run_id={run.info.run_id}")


if __name__ == "__main__":
    main()