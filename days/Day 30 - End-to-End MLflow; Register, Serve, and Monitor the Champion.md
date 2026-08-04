Prompt

The xFusionCorp Industries MLOps team requires the promotion of the `fraud-detection-v2` candidate from the tracking server to live inference, which includes comprehensive end-to-end monitoring. The supporting infrastructure, encompassing PostgreSQL, SeaweedFS, MLflow tracking server, and three candidate runs, has already been established. Your objective is to complete the remaining lifecycle tasks: model promotion, serving, and health monitoring.

  

1. The infrastructure is fully up: PostgreSQL container `mlflow-db` on port `5432`, SeaweedFS on ports `8333`(S3 API) and `8888` (Filer UI), MLflow tracking server on port `5000` with the PostgreSQL backend and the `mlflow-artifacts` S3 bucket. The `fraud-detection-v2` experiment contains three candidate runs (`baseline`, `improved`, `regression`) with logged `f1_score` metrics. The **MLflow UI** and **SeaweedFS Filer** buttons at the top of the lab can be opened to view each web UI.
    
2. The complete end state requires the following.
    
    - A registered model named **`fraud-detector-v2`** exists in the MLflow Model Registry.
    - A **`champion`** alias on that model points at the version sourced from the `fraud-detection-v2`run with the **highest** `f1_score`.
    - An `mlflow models serve` process listens on port `5001`, serving the champion version (`--env-manager=local` is the supported choice for the lab). Export `MLFLOW_TRACKING_URI=http://localhost:5000`in the serving shell so the `models:/` URI can be resolved against the tracking server. The tracking server proxies the model download from SeaweedFS itself, so no S3 credentials are needed in the serving shell.
    - The served endpoint returns `200` on `GET /health`.
    - A shell script at `/root/code/monitor.sh`exists, is executable, probes the served model's `/health` endpoint once, and exits with status `0` when the endpoint is healthy.
3. The top run can be identified either through the **MLflow UI** Compare view or with a one-off `MlflowClient.search_runs()` call—whichever is preferable. The registration and alias assignment are likewise available from the UI (Models tab) or the SDK.
    

> `mlflow models serve` is long-running; start it in the background, and ensure that the new process is listening on port `5001` before writing the monitoring script.

---

Solution

seed_runs.py (Provided file)

```python
"""Seed the `fraud-detection-v2` experiment with three candidate
runs. Each run logs a DummyClassifier fitted on a two-row
deterministic array and advertises hardcoded synthetic `f1_score`
and `accuracy` metrics.

No real training takes place. The lab is about the full lifecycle
(identify best, register, alias, serve, monitor) — not about model
quality. The synthetic metric values are chosen so that the
`improved` run is unambiguously the top candidate.
"""
import sys
import numpy as np
import mlflow
import mlflow.sklearn
from mlflow import MlflowClient
from sklearn.dummy import DummyClassifier

TRACKING_URI = "http://localhost:5000"
EXPERIMENT_NAME = "fraud-detection-v2"

SEED_RUNS = [
    {
        "name": "baseline",
        "params": {"n_estimators": 100, "max_depth": 5},
        "metrics": {"accuracy": 0.78, "f1_score": 0.80},
    },
    {
        "name": "improved",
        "params": {"n_estimators": 200, "max_depth": 10},
        "metrics": {"accuracy": 0.89, "f1_score": 0.92},
    },
    {
        "name": "regression",
        "params": {"n_estimators": 50, "max_depth": 3},
        "metrics": {"accuracy": 0.73, "f1_score": 0.75},
    },
]


def _dummy_fit():
    X = np.array([[0.0, 0.0], [1.0, 1.0]])
    y = np.array([0, 1])
    return DummyClassifier(strategy="most_frequent").fit(X, y)


def main():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()

    existing = client.get_experiment_by_name(EXPERIMENT_NAME)
    if existing is not None and len(client.search_runs([existing.experiment_id])) >= len(SEED_RUNS):
        # Re-spawn safety: seed already populated.
        sys.exit(0)

    mlflow.set_experiment(EXPERIMENT_NAME)

    for cfg in SEED_RUNS:
        with mlflow.start_run(run_name=cfg["name"]):
            mlflow.log_params(cfg["params"])
            for key, value in cfg["metrics"].items():
                mlflow.log_metric(key, value)
            mlflow.sklearn.log_model(_dummy_fit(), name="model")


if __name__ == "__main__":
    main()
```

Create script to identify and register model

[promote_model.py](../templates/promote_model.py)

```Python
import mlflow
from mlflow import MlflowClient

mlflow.set_tracking_uri("http://localhost:5000")

client = MlflowClient()

exp = client.get_experiment_by_name("fraud-detection-v2")

run = client.search_runs(
    [exp.experiment_id],
    order_by=["metrics.f1_score DESC"],
    max_results=1,
)[0]

mv = mlflow.register_model(
    f"runs:/{run.info.run_id}/model",
    "fraud-detector-v2",
)

client.set_registered_model_alias(
    "fraud-detector-v2",
    "champion",
    mv.version,
)
```

Run promotion script

```shell
python3 promote_model.py
```

Export environment variable

```shell
export MLFLOW_TRACKING_URI=http://localhost:5000
```

Run server

```shell
mlflow models serve \
    -m "models:/fraud-detector-v2@champion" \
    -p 5001 \
    --env-manager=local &
```

Create /root/code/monitor.sh script

```shell
#!/bin/bash
curl -fs http://localhost:5001/health >/dev/null
```

Make script executable

```shell
chmod +x  /root/code/monitor.sh
```

Run script to verify completes successfully

```shell
/root/code/monitor.sh
echo $?
```
