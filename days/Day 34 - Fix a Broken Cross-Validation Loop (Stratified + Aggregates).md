Prompt

The xFusionCorp Industries ML platform team is evaluating fraud-detection candidates using k-fold cross-validation. It is essential that each fold is tracked in MLflow, ensuring that they remain independently visible and comparable, rather than being aggregated into a single score. A cross-validation scaffold is available at `/root/code/fraud-detection/src/models/cross_validate.py`. Within this scaffold, the fold loop, the stratified splitter, and the aggregate report are already properly configured; however, the computation of per-fold metrics is incomplete, and each fold has not yet been logged as its own MLflow run. Your task is to complete the per-fold metrics and log each fold as a nested MLflow run under a single parent run.

  

1. The MLflow tracking server is already running on port `5000`. The **MLflow UI** button at the top of the lab can be opened to confirm—the dashboard loads with an empty `fraud-detection-cv` experiment.
    
2. The project layout under `/root/code/fraud-detection/`:
    
    - `data/train.csv` – A pre-generated 200-row synthetic binary-classification dataset with an imbalanced class split (roughly 70 / 30). Do not regenerate it.
    - `src/models/cross_validate.py` – The cross-validation scaffold. Fold iteration, the `StratifiedKFold` splitter (which preserves the class ratio across folds), the mean/std aggregate report, JSON persistence, and artefact logging are already wired; the per-fold metric computation and the nested MLflow run per fold need to be authored.
    - `reports/` – Where the cross-validation report must land.
3. The end state must include:
    
    - A file at `/root/code/fraud-detection/reports/cv_results.json` (absolute path, inside the project's reports directory).
    - That JSON contains exactly these seven top-level keys: `mean_accuracy`, `std_accuracy`, `mean_f1`, `std_f1`, `mean_roc_auc`, `std_roc_auc`, `folds`. Every `mean_*` and `std_*` value is numeric.
    - The `folds` value is a list of five per-fold dictionaries; each carries the keys `fold`, `accuracy`, `f1`, `roc_auc`.
    - One parent MLflow run named `cv-parent` in the `fraud-detection-cv` experiment, with five **nested** children (`fold-1` through `fold-5`)—each a true nested run under the parent—logging the per-fold metrics.

> `accuracy_score`, `f1_score`, and `roc_auc_score` are already imported at the top of the scaffold—no new imports are required.

---

Solution

cross_validate.py (original)

```python
"""Cross-validation evaluator for the fraud-detection model.

Runs k-fold cross-validation and writes an aggregate report at
`reports/cv_results.json`. The point of this lab is *tracking*: every
fold is recorded as its own nested MLflow run under a single parent so
the folds are independently visible and comparable in the MLflow UI.

Every ML-methodology concern is already wired for you — the stratified
splitter (preserves the class ratio across folds) and the mean/std
aggregate report. What you author is the MLOps tracking: compute each
fold's metrics (TODO 1) and log each fold as a nested run (TODO 2).
"""
import os
import json
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

TRAIN_CSV = "/root/code/fraud-detection/data/train.csv"
REPORTS_DIR = "/root/code/fraud-detection/reports"
CV_RESULTS_JSON = os.path.join(REPORTS_DIR, "cv_results.json")
N_SPLITS = 5
EXPERIMENT_NAME = "fraud-detection-cv"


def main():
    df = pd.read_csv(TRAIN_CSV)
    X = df.drop(columns=["is_fraud"])
    y = df["is_fraud"]

    # StratifiedKFold (not a plain KFold) so every fold preserves the
    # dataset's ~70/30 class ratio — essential on an imbalanced set.
    # Pre-wired: this lab's focus is tracking the folds in MLflow.
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)

    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment(EXPERIMENT_NAME)

    fold_results = []

    with mlflow.start_run(run_name="cv-parent"):
        mlflow.log_param("n_splits", N_SPLITS)
        mlflow.log_param("cv_type", type(cv).__name__)

        for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y), start=1):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            model = RandomForestClassifier(
                n_estimators=100, max_depth=5, random_state=42
            )
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            proba = model.predict_proba(X_test)[:, 1]

            # TODO 1: fill in this fold's metrics on the held-out split,
            # in place, under the keys "accuracy", "f1", and "roc_auc"
            # (round each to 6 dp). Use accuracy_score / f1_score on `preds`
            # and roc_auc_score on `proba` (the class-1 probabilities).
            # `accuracy_score`, `f1_score`, and `roc_auc_score` are imported.
            fold = {
                "fold": fold_idx,
            }

            # TODO 2: track THIS fold as its own MLflow run, nested under the
            # `cv-parent` run above, so each fold is independently visible and
            # comparable in the MLflow UI. Open a nested run named
            # f"fold-{fold_idx}" (pass nested=True to mlflow.start_run) and,
            # inside it, log `fold_idx` as the param "fold" and this fold's
            # "accuracy", "f1", and "roc_auc" (from the `fold` dict) as metrics.

            # Pre-wired — record this fold for the aggregate report below.
            # Leave this line in place.
            fold_results.append(fold)

        acc_vals = [r["accuracy"] for r in fold_results]
        f1_vals = [r["f1"] for r in fold_results]
        auc_vals = [r["roc_auc"] for r in fold_results]

        # Aggregate reports the mean AND standard deviation of each metric —
        # a high std across folds flags an unstable model. Pre-wired.
        aggregate = {
            "mean_accuracy": round(float(np.mean(acc_vals)), 6),
            "std_accuracy": round(float(np.std(acc_vals)), 6),
            "mean_f1": round(float(np.mean(f1_vals)), 6),
            "std_f1": round(float(np.std(f1_vals)), 6),
            "mean_roc_auc": round(float(np.mean(auc_vals)), 6),
            "std_roc_auc": round(float(np.std(auc_vals)), 6),
            "folds": fold_results,
        }

        mlflow.log_metric("mean_accuracy", aggregate["mean_accuracy"])
        mlflow.log_metric("mean_f1", aggregate["mean_f1"])
        mlflow.log_metric("mean_roc_auc", aggregate["mean_roc_auc"])

        os.makedirs(REPORTS_DIR, exist_ok=True)
        with open(CV_RESULTS_JSON, "w") as f:
            json.dump(aggregate, f, indent=2, sort_keys=False)
        mlflow.log_artifact(CV_RESULTS_JSON)

    print(f"aggregate: {aggregate}")
    print(f"report: {CV_RESULTS_JSON}")


if __name__ == "__main__":
    main()
```

TODO 1

```python
fold = {
    "fold": fold_idx,
    "accuracy": round(accuracy_score(y_test, preds), 6),
    "f1": round(f1_score(y_test, preds), 6),
    "roc_auc": round(roc_auc_score(y_test, proba), 6),
}
```

TODO 2

```python
with mlflow.start_run(run_name=f"fold-{fold_idx}", nested=True):
    mlflow.log_param("fold", fold_idx)
    mlflow.log_metric("accuracy", fold["accuracy"])
    mlflow.log_metric("f1", fold["f1"])
    mlflow.log_metric("roc_auc", fold["roc_auc"])
```

Final script

```Python
"""Cross-validation evaluator for the fraud-detection model.

Runs k-fold cross-validation and writes an aggregate report at
`reports/cv_results.json`. The point of this lab is *tracking*: every
fold is recorded as its own nested MLflow run under a single parent so
the folds are independently visible and comparable in the MLflow UI.

Every ML-methodology concern is already wired for you — the stratified
splitter (preserves the class ratio across folds) and the mean/std
aggregate report. What you author is the MLOps tracking: compute each
fold's metrics (TODO 1) and log each fold as a nested run (TODO 2).
"""
import os
import json
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

TRAIN_CSV = "/root/code/fraud-detection/data/train.csv"
REPORTS_DIR = "/root/code/fraud-detection/reports"
CV_RESULTS_JSON = os.path.join(REPORTS_DIR, "cv_results.json")
N_SPLITS = 5
EXPERIMENT_NAME = "fraud-detection-cv"


def main():
    df = pd.read_csv(TRAIN_CSV)
    X = df.drop(columns=["is_fraud"])
    y = df["is_fraud"]

    # StratifiedKFold (not a plain KFold) so every fold preserves the
    # dataset's ~70/30 class ratio — essential on an imbalanced set.
    # Pre-wired: this lab's focus is tracking the folds in MLflow.
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)

    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment(EXPERIMENT_NAME)

    fold_results = []

    with mlflow.start_run(run_name="cv-parent"):
        mlflow.log_param("n_splits", N_SPLITS)
        mlflow.log_param("cv_type", type(cv).__name__)

        for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y), start=1):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            model = RandomForestClassifier(
                n_estimators=100, max_depth=5, random_state=42
            )
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            proba = model.predict_proba(X_test)[:, 1]

            # TODO 1: fill in this fold's metrics on the held-out split,
            # in place, under the keys "accuracy", "f1", and "roc_auc"
            # (round each to 6 dp). Use accuracy_score / f1_score on `preds`
            # and roc_auc_score on `proba` (the class-1 probabilities).
            # `accuracy_score`, `f1_score`, and `roc_auc_score` are imported.
            fold = {
                "fold": fold_idx,
                "accuracy": round(accuracy_score(y_test, preds), 6),
                "f1": round(f1_score(y_test, preds), 6),
                "roc_auc": round(roc_auc_score(y_test, proba), 6)
            }

            # TODO 2: track THIS fold as its own MLflow run, nested under the
            # `cv-parent` run above, so each fold is independently visible and
            # comparable in the MLflow UI. Open a nested run named
            # f"fold-{fold_idx}" (pass nested=True to mlflow.start_run) and,
            # inside it, log `fold_idx` as the param "fold" and this fold's
            # "accuracy", "f1", and "roc_auc" (from the `fold` dict) as metrics.

            with mlflow.start_run(run_name=f"fold-{fold_idx}", nested=True):
                mlflow.log_param("fold", fold_idx)
                mlflow.log_metric("accuracy", fold["accuracy"])
                mlflow.log_metric("f1", fold["f1"])
                mlflow.log_metric("roc_auc", fold["roc_auc"])

            # Pre-wired — record this fold for the aggregate report below.
            # Leave this line in place.
            fold_results.append(fold)

        acc_vals = [r["accuracy"] for r in fold_results]
        f1_vals = [r["f1"] for r in fold_results]
        auc_vals = [r["roc_auc"] for r in fold_results]

        # Aggregate reports the mean AND standard deviation of each metric —
        # a high std across folds flags an unstable model. Pre-wired.
        aggregate = {
            "mean_accuracy": round(float(np.mean(acc_vals)), 6),
            "std_accuracy": round(float(np.std(acc_vals)), 6),
            "mean_f1": round(float(np.mean(f1_vals)), 6),
            "std_f1": round(float(np.std(f1_vals)), 6),
            "mean_roc_auc": round(float(np.mean(auc_vals)), 6),
            "std_roc_auc": round(float(np.std(auc_vals)), 6),
            "folds": fold_results,
        }

        mlflow.log_metric("mean_accuracy", aggregate["mean_accuracy"])
        mlflow.log_metric("mean_f1", aggregate["mean_f1"])
        mlflow.log_metric("mean_roc_auc", aggregate["mean_roc_auc"])

        os.makedirs(REPORTS_DIR, exist_ok=True)
        with open(CV_RESULTS_JSON, "w") as f:
            json.dump(aggregate, f, indent=2, sort_keys=False)
        mlflow.log_artifact(CV_RESULTS_JSON)

    print(f"aggregate: {aggregate}")
    print(f"report: {CV_RESULTS_JSON}")


if __name__ == "__main__":
    main()
```

Execute cross_validate.py

```shell
python /root/code/fraud-detection/src/models/cross_validate.py
```

Output

```shell
🏃 View run fold-1 at: http://localhost:5000/#/experiments/1/runs/94ff0e640b954b08ba40fedcd61ace18
🧪 View experiment at: http://localhost:5000/#/experiments/1
🏃 View run fold-2 at: http://localhost:5000/#/experiments/1/runs/1d0b5d3b979749a88a03a0cf2b2bd4f3
🧪 View experiment at: http://localhost:5000/#/experiments/1
🏃 View run fold-3 at: http://localhost:5000/#/experiments/1/runs/5a2292bb363f44f6be8886852c0b91f6
🧪 View experiment at: http://localhost:5000/#/experiments/1
🏃 View run fold-4 at: http://localhost:5000/#/experiments/1/runs/92e902c2e34a4298a3d8d22ebe7a156f
🧪 View experiment at: http://localhost:5000/#/experiments/1
🏃 View run fold-5 at: http://localhost:5000/#/experiments/1/runs/7235e0441146480f82021bd6fed33c0c
🧪 View experiment at: http://localhost:5000/#/experiments/1
🏃 View run cv-parent at: http://localhost:5000/#/experiments/1/runs/8d3fc04b6198465ebbaeb28656426bdd
🧪 View experiment at: http://localhost:5000/#/experiments/1
aggregate: {'mean_accuracy': 0.71, 'std_accuracy': 0.060415, 'mean_f1': 0.393399, 'std_f1': 0.161452, 'mean_roc_auc': 0.66046, 'std_roc_auc': 0.047093, 'folds': [{'fold': 1, 'accuracy': 0.825, 'f1': 0.695652, 'roc_auc': 0.72619}, {'fold': 2, 'accuracy': 0.65, 'f1': 0.222222, 'roc_auc': 0.651786}, {'fold': 3, 'accuracy': 0.675, 'f1': 0.315789, 'roc_auc': 0.589286}, {'fold': 4, 'accuracy': 0.7, 'f1': 0.4, 'roc_auc': 0.639881}, {'fold': 5, 'accuracy': 0.7, 'f1': 0.333333, 'roc_auc': 0.695157}]}
report: /root/code/fraud-detection/reports/cv_results.json
```

project report for verification

cv_results.json

```json
{
  "mean_accuracy": 0.71,
  "std_accuracy": 0.060415,
  "mean_f1": 0.393399,
  "std_f1": 0.161452,
  "mean_roc_auc": 0.66046,
  "std_roc_auc": 0.047093,
  "folds": [
    {
      "fold": 1,
      "accuracy": 0.825,
      "f1": 0.695652,
      "roc_auc": 0.72619
    },
    {
      "fold": 2,
      "accuracy": 0.65,
      "f1": 0.222222,
      "roc_auc": 0.651786
    },
    {
      "fold": 3,
      "accuracy": 0.675,
      "f1": 0.315789,
      "roc_auc": 0.589286
    },
    {
      "fold": 4,
      "accuracy": 0.7,
      "f1": 0.4,
      "roc_auc": 0.639881
    },
    {
      "fold": 5,
      "accuracy": 0.7,
      "f1": 0.333333,
      "roc_auc": 0.695157
    }
  ]
}
```

MLflow UI should now show the cv-parent with 5 nested runs 

![parent run](<../screenshots/Screenshot Day 34 parent run.png>)

Nested child run (fold-1)

![nested child run](<../screenshots/Screenshot Day 34 nested child run.png>)