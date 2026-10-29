Prompt

The xFusionCorp Industries ML platform team operates a drift-triggered retraining pipeline. When data drift exceeds the alert threshold, the pipeline automatically retrains the fraud-detection model and registers it as a new version of `fraud-detector`. Currently, there is an incumbent version `1` serving production traffic under the `production` alias, along with a newly retrained challenger version `2`, which has not yet been promoted. It is essential to avoid promoting the retrained model to production without evaluation, as this could result in a subpar model reaching users. Your task is to implement the promotion gate in `promote.py`, ensuring that the challenger is only promoted to `production` if it surpasses the incumbent's performance on the designated evaluation metric. After completing this task, proceed to execute the promotion.

  

The MLflow tracking server is on port `5000`; the **MLflow UI**button opens it. Under **Models → fraud-detector** you can see version `1` (alias `production`, `f1_score` `0.71`) and version `2`(no alias yet, `f1_score` `0.82`).

The project is at `/root/code/monitoring/`:

- `retrain_pipeline.py` – the startup setup that registered v1 and v2. Correct; do not edit.
- `promote.py` – the promotion-gate scaffold. Its `f1_of(version)` helper (reads a version's logged `f1_score`) is wired; the gate logic is a `# TODO` naming the MLflow client calls to use.

The gate must read the version the `production` alias currently points at (the champion) and its `f1_score`, read the challenger's `f1_score` (version `2`), and re-point `production`at the challenger only if the challenger's is strictly greater—otherwise leave the alias unchanged.

The end state must include:

- The `production` alias on `fraud-detector` resolves to version `2` (the challenger).
- The version now serving `production` has a higher `f1_score` than the incumbent v1 — the gate promoted the better model, not a blind version bump.

> MLflow 3.x replaced stage-based promotion (`Staging`/`Production`) with **aliases** — named pointers like `production` that decouple a label from a version, so downstream code loads `models:/fraud-detector@production` and promotion is just re-pointing the alias. A champion/challenger gate is the guardrail: never re-point `production` at a retrained model without first confirming it actually beats what is live.

---

Solution

promote.py (Original)

```python
"""Champion/challenger promotion gate.

A drift-triggered retrain registered a new challenger version of
`fraud-detector` (v2). The incumbent (v1) currently serves production
traffic via the `production` alias. Promoting a retrained model blindly
is how a worse model reaches production -- so gate the promotion on the
candidate's evaluation metric.

Run from /root/code/monitoring/:  python3 promote.py
"""
from mlflow import MlflowClient

TRACKING_URI = "http://localhost:5000"
MODEL = "fraud-detector"
PROD_ALIAS = "production"
CHALLENGER_VERSION = "2"  # the version the drift-triggered retrain registered

client = MlflowClient(tracking_uri=TRACKING_URI)


def f1_of(version: str) -> float:
    """Read the f1_score metric logged on a model version's run."""
    mv = client.get_model_version(MODEL, version)
    return client.get_run(mv.run_id).data.metrics["f1_score"]


def main() -> None:
    # TODO: implement the promotion gate.
    #   1. Find the version the `production` alias currently points at
    #      (client.get_model_version_by_alias(MODEL, PROD_ALIAS)) -- the
    #      champion -- and read its f1 with f1_of(...).
    #   2. Read the challenger's f1: f1_of(CHALLENGER_VERSION).
    #   3. Promote ONLY IF the challenger's f1 is strictly greater than the
    #      champion's: re-point the production alias at the challenger with
    #        client.set_registered_model_alias(MODEL, PROD_ALIAS, CHALLENGER_VERSION)
    #      and print that it was promoted. Otherwise, leave the alias
    #      untouched and print that the challenger was rejected.
    raise SystemExit("promotion gate not implemented")


if __name__ == "__main__":
    main()
```

TODO Section

```python
def main() -> None:
    champion = client.get_model_version_by_alias(MODEL, PROD_ALIAS)
    champion_f1 = f1_of(champion.version)
    challenger_f1 = f1_of(CHALLENGER_VERSION)
    
    if challenger_f1 > champion_f1:
        client.set_registered_model_alias(
            MODEL, 
            PROD_ALIAS, 
            CHALLENGER_VERSION
            )
        print("Challenger model was promoted")
    else:
        print("Challenger model was rejected")
```

Run updated promote script

```shell
cd /root/code/monitoring
python3 promote.py
```

Output

```shell
Challenger model was promoted
```

monitoring.log

```shell
[2026-10-29 13:48:44] Registered fraud-detector (incumbent, f1=0.71)
[2026-10-29 13:48:48] Registered fraud-detector (retrained-challenger, f1=0.82)
[2026-10-29 13:48:48] Set production -> v1 (incumbent). Challenger v2 awaits the promotion gate.
```

---

### Verification

MLflow UI Registered Models shows fraud-detector using Version 2 and carries production alias

![screenshot](<../screenshots/Screenshot Day 73 MLflow UI Registered Models.png>)

MLflow UI shows production model (v2) has a higher f1_score that the incumbent (v1)

![screenshot](<../screenshots/Screenshot Day 73 MLflow Model Metrics.png>)

---
### LAB NOTE

The lab's startup script (retrain_pipeline.py) failed before any model was registered, so fraud-detector did not exist in the registry. The failure was skops.io.exceptions.UntrustedTypesFoundException for sklearn.tree.tree.Tree, raised by mlflow.sklearn.log_model (mlflow 3.16.1, skops 0.16.0, scikit-learn 1.9.1). Restarting the lab reproduced the same failed run.

Workaround: I did not edit retrain_pipeline.py. I ran a copy at /tmp/retrain_seed.py with one added argument to log_model, skops_trusted_types="sklearn.tree.tree.Tree", trusting only that type (the model is trained by the script itself). Note that this means the lab's own startup script was bypassed rather than used.

alteration script used

```shell
cd /root/code/monitoring/
sed 's/^\(\s*\)registered_model_name=REGISTERED_MODEL,/&\n\1skops_trusted_types=["sklearn.tree._tree.Tree"],/' \
  retrain_pipeline.py > /tmp/retrain_seed.py
grep -n -B1 -A1 skops_trusted_types /tmp/retrain_seed.py
python3 /tmp/retrain_seed.py
```

Result: fraud-detector v1 (f1 0.71, alias production) and v2 (f1 0.82) were registered as the lab describes. I then ran promote.py, which re-pointed production at v2 because 0.82 > 0.71.

![screenshot](<../screenshots/Screenshot Day 73 MLflow UI failed run.png>)

---
### Provided Files

retrain_pipeline.py

```python
"""Drift-triggered retrain setup for Day 73.

Runs once at lab startup and leaves the MLflow registry in a
champion/challenger state:

  - `fraud-detector` v1  — the incumbent, currently serving
    (f1_score 0.71), with the `production` alias attached.
  - `fraud-detector` v2  — the challenger the drift-triggered
    retrain just produced (f1_score 0.82), registered but NOT
    promoted.

The reader authors the promotion gate (`promote.py`) that decides
whether v2 should replace v1 as `production`. This script does NOT
promote anything beyond seeding the incumbent alias.
"""
import os
from datetime import datetime

import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow import MlflowClient
from mlflow.models.signature import infer_signature
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier

TRACKING_URI = "http://localhost:5000"
EXPERIMENT = "retraining-monitor"
REGISTERED_MODEL = "fraud-detector"
LOG_PATH = "/root/code/logs/monitoring.log"

# Two candidate models. f1 values are fixed so the registry the reader
# sees is deterministic; the challenger (v2) beats the incumbent (v1).
# Model quality itself is irrelevant here -- the teaching point is the
# promotion gate, so the metrics are synthetic.
CANDIDATES = [
    {"run_name": "incumbent", "f1": 0.71, "drift_share": 0.05},
    {"run_name": "retrained-challenger", "f1": 0.82, "drift_share": 0.48},
]


def log(msg: str) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a") as fh:
        fh.write(line + "\n")


def main() -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)

    X, y = make_classification(
        n_samples=400, n_features=4, n_informative=3, n_redundant=0,
        random_state=42,
    )
    columns = ["amount", "hour", "num_tx_past_day", "category_code"]
    X_df = pd.DataFrame(X, columns=columns)
    y_s = pd.Series(y, name="is_fraud")
    signature = infer_signature(X_df, y_s)

    client = MlflowClient(tracking_uri=TRACKING_URI)

    for cand in CANDIDATES:
        with mlflow.start_run(run_name=cand["run_name"]):
            model = RandomForestClassifier(n_estimators=20, random_state=42)
            model.fit(X_df, y_s)
            mlflow.log_metric("drift_share", cand["drift_share"])
            mlflow.log_metric("f1_score", cand["f1"])
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                signature=signature,
                input_example=X_df.head(2),
                registered_model_name=REGISTERED_MODEL,
            )
        log(f"Registered {REGISTERED_MODEL} ({cand['run_name']}, f1={cand['f1']})")

    # Seed the incumbent: point `production` at v1. The challenger (v2)
    # is left unpromoted -- the reader's gate decides its fate.
    client.set_registered_model_alias(REGISTERED_MODEL, "production", "1")
    log("Set production -> v1 (incumbent). Challenger v2 awaits the promotion gate.")


if __name__ == "__main__":
    main()
```