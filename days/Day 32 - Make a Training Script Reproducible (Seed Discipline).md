Prompt

The xFusionCorp Industries ML platform team's audit pipeline relies on run-to-run reproducibility, meaning that identical code and data must yield identical metrics. Currently, the fraud-detection trainer located at `/root/code/fraud-detection/src/models/train.py` does not uphold this guarantee, as consecutive runs on the same dataset produce varying accuracy and F1 values. Your objective is to modify the trainer to ensure it is deterministic, enabling the successful execution of the `check_determinism.sh` probe.

  

1. The MLflow tracking server is already running on port `5000`. The **MLflow UI** button at the top of the lab can be opened to confirm—the dashboard loads with an empty `fraud-detection-repro` experiment.
    
2. The project layout under `/root/code/fraud-detection/`:
    
    - `data/train.csv` – A pre-generated 200-row synthetic binary classification dataset. The same file is read by both runs.
    - `src/models/train.py` – The trainer (non-deterministic on purpose). This is the only file that needs to change.
    - `check_determinism.sh` – Executable probe that runs the trainer three times, writes `reports/metrics_run_1.json`, `reports/metrics_run_2.json`, and `reports/metrics_run_3.json`, and `diff`s each adjacent pair. Exits `0` only when all three JSON files are byte-identical.
    - `models/` – Where each run persists its serialised model.
    - `reports/` – Where each run writes its metrics JSON.
3. Run `./check_determinism.sh` against the scaffold as-is to see it fail and diff the runs that diverge.
    
4. The end state must include:
    
    - `check_determinism.sh` exits with status `0`.
    - At least two runs exist in the `fraud-detection-repro` experiment, named `repro-run-1` and `repro-run-2`, with identical `metrics.accuracy` and `metrics.f1_score`values (to at least six decimal places).
    - All three probe runs produce byte-identical metrics JSON files at `reports/metrics_run_1.json`, `reports/metrics_run_2.json`, and `reports/metrics_run_3.json` – Covering `accuracy`, `f1_score`, and the model's `feature_importances`.

> Only `train.py` needs to change. The probe, the dataset, and the MLflow wiring are all correct and must not be modified.

---

Solution

Verify MLflow UI shows empty fraud-detection-repro experiment

![Starting State](<../screenshots/Screenshot Day 32 start.png>)

train.py (original)

```python
"""Training script for the fraud-detection model.

This scaffold is deliberately non-deterministic — running it twice
produces different metrics on the same input data. A reproducibility
fix is required so downstream tooling (checksum-based caching,
experiment comparison, audit trails) can rely on run-to-run
stability.

Every non-reproducibility concern is already handled here — data
loading, split, training, MLflow logging, model persistence, and
metrics serialisation. Edit this file to add the seed discipline
that makes the run reproducible; do not change anything else.
"""
import os
import json
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

TRAIN_CSV = "/root/code/fraud-detection/data/train.csv"
MODEL_PATH = "/root/code/fraud-detection/models/model.pkl"
METRICS_OUT = os.environ.get(
    "METRICS_OUT", "/root/code/fraud-detection/reports/last_metrics.json"
)
RUN_NAME = os.environ.get("MLFLOW_RUN_NAME", "repro-run")


def main():
    df = pd.read_csv(TRAIN_CSV)
    X = df.drop(columns=["is_fraud"])
    y = df["is_fraud"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y
    )

    model = RandomForestClassifier(n_estimators=100, max_depth=5)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    metrics = {
        "accuracy": round(accuracy_score(y_test, preds), 6),
        "f1_score": round(f1_score(y_test, preds), 6),
    }

    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("fraud-detection-repro")
    with mlflow.start_run(run_name=RUN_NAME):
        mlflow.log_params({"n_estimators": 100, "max_depth": 5})
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        mlflow.sklearn.log_model(model, name="model")

    # Probe payload is a superset of `metrics` plus feature_importances.
    # The list lives here — not in `metrics` — because MLflow's
    # log_metric only accepts scalars. feature_importances_ is an
    # average over 100 trees' bootstrap + feature-subset randomness;
    # two unseeded runs can coincidentally produce the same accuracy
    # / f1 bucket on a 40-row stratified test set, but their importance
    # triplets essentially never match, so the probe's byte-diff can
    # distinguish a real deterministic run from a lucky collision.
    probe_payload = {
        **metrics,
        "feature_importances": model.feature_importances_.tolist(),
    }
    os.makedirs(os.path.dirname(METRICS_OUT), exist_ok=True)
    with open(METRICS_OUT, "w") as f:
        json.dump(probe_payload, f, indent=2, sort_keys=True)

    print(f"{RUN_NAME}: accuracy={metrics['accuracy']}, f1_score={metrics['f1_score']}")


if __name__ == "__main__":
    main()
```

Run the check script to see failure (as stated in directions)

```shell
./check_determinism.sh
```

Output

```shell
FAIL: the three runs did not produce byte-identical metrics.
```

MLflow UI should now show the 3 runs

![Failed Run](<../screenshots/Screenshot Day 32 failed run.png>)

Need to supply a fixed random_state to both stochastic operations.

train.py (Updated)

```python
"""Training script for the fraud-detection model.

This scaffold is deliberately non-deterministic — running it twice
produces different metrics on the same input data. A reproducibility
fix is required so downstream tooling (checksum-based caching,
experiment comparison, audit trails) can rely on run-to-run
stability.

Every non-reproducibility concern is already handled here — data
loading, split, training, MLflow logging, model persistence, and
metrics serialisation. Edit this file to add the seed discipline
that makes the run reproducible; do not change anything else.
"""
import os
import json
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

TRAIN_CSV = "/root/code/fraud-detection/data/train.csv"
MODEL_PATH = "/root/code/fraud-detection/models/model.pkl"
METRICS_OUT = os.environ.get(
    "METRICS_OUT", "/root/code/fraud-detection/reports/last_metrics.json"
)
RUN_NAME = os.environ.get("MLFLOW_RUN_NAME", "repro-run")


def main():
    df = pd.read_csv(TRAIN_CSV)
    X = df.drop(columns=["is_fraud"])
    y = df["is_fraud"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    metrics = {
        "accuracy": round(accuracy_score(y_test, preds), 6),
        "f1_score": round(f1_score(y_test, preds), 6),
    }

    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("fraud-detection-repro")
    with mlflow.start_run(run_name=RUN_NAME):
        mlflow.log_params({"n_estimators": 100, "max_depth": 5})
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        mlflow.sklearn.log_model(model, name="model")

    # Probe payload is a superset of `metrics` plus feature_importances.
    # The list lives here — not in `metrics` — because MLflow's
    # log_metric only accepts scalars. feature_importances_ is an
    # average over 100 trees' bootstrap + feature-subset randomness;
    # two unseeded runs can coincidentally produce the same accuracy
    # / f1 bucket on a 40-row stratified test set, but their importance
    # triplets essentially never match, so the probe's byte-diff can
    # distinguish a real deterministic run from a lucky collision.
    probe_payload = {
        **metrics,
        "feature_importances": model.feature_importances_.tolist(),
    }
    os.makedirs(os.path.dirname(METRICS_OUT), exist_ok=True)
    with open(METRICS_OUT, "w") as f:
        json.dump(probe_payload, f, indent=2, sort_keys=True)

    print(f"{RUN_NAME}: accuracy={metrics['accuracy']}, f1_score={metrics['f1_score']}")


if __name__ == "__main__":
    main()
```

Now run the check script again

```shell
./check_determinism.sh
```

Output

```shell
OK: all three runs produced byte-identical metrics.
```

Check exit code

```shell
$?
```

Output

```shell
0
```

Final state should show two of each run.

![Final State](<../screenshots/Screenshot Day 32 final.png>)
