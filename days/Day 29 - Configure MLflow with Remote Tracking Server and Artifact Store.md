Prompt

The xFusionCorp Industries ML platform team has successfully deployed a shared MLflow instance that employs a production-grade tracking store, specifically PostgreSQL, and a production-grade artifact store, SeaweedFS (which is S3-compatible). While the MLflow server is operational and correctly writing metadata to PostgreSQL, a team member has noticed that artifacts are not being stored in the `mlflow-artifacts` bucket within SeaweedFS. This suggests that the connection between MLflow and SeaweedFS is not properly configured.

Your task is to diagnose the issue in the MLflow server's startup configuration, rectify it, and re-run the pre-staged smoke test to ensure that one round trip successfully stores metadata in PostgreSQL **and** the model artifact in SeaweedFS.

  

1. The pre-staged state:
    
    - **PostgreSQL** container `mlflow-db` is running on port `5432` (database `mlflow`, credentials `mlflow` / `mlflow123`).
    - **SeaweedFS** is running on port `8333` (S3 API) / `8888` (Filer UI), credentials `weedadmin` / `weedadmin123`, with a pre-created bucket `mlflow-artifacts`.
    - **MLflow tracking server** is running on port `5000`and was launched by `/root/code/start-mlflow.sh`. Its log is at `/tmp/mlflow.log`.
    - Reference scripts: `/root/code/start-mlflow.sh`(the MLflow startup command), `/root/code/restart-mlflow.sh` (kills the running server and re-launches via `start-mlflow.sh`), and `/root/code/log_test_run.py`(the smoke-test that exercises one full round trip).
2. As pre-staged, the smoke-test in `log_test_run.py`only half-succeeds: the MLflow run appears in the **MLflow UI** (the metadata write to PostgreSQL succeeds), but the model artefact upload step raises an error and the **SeaweedFS Filer** shows `/buckets/mlflow-artifacts/` still empty. Run `python3 /root/code/log_test_run.py` to observe the artefact-upload error directly, and inspect the server log at `/tmp/mlflow.log`. Once the startup configuration in `/root/code/start-mlflow.sh` is corrected, `restart-mlflow.sh` re-launches the server.
    
3. The end state must include:
    
    - The `test-remote` experiment exists on the MLflow server with at least one **successful** run, visible in the **MLflow UI**.
    - The `mlflow-artifacts` bucket on SeaweedFS holds the run's model artefact (`MLmodel` + `model.pkl`), visible in the **SeaweedFS Filer**under `/buckets/mlflow-artifacts/`.
    - The PostgreSQL `mlflow` database holds the MLflow schema (the run's metadata).

> PostgreSQL listens on port `5432` with a binary protocol — it is not reachable from a web browser. Use `docker exec mlflow-db psql -U mlflow -d mlflow` for manual inspection if needed.

---

Solution

*Provided Files (Original)*

start-mlflow.sh

```shell
#!/bin/bash
# Start the MLflow tracking server with the production-style wiring:
# - PostgreSQL backend for run metadata
# - SeaweedFS (S3-compatible) for artefact storage
# - host/CORS flags so the MLflow UI button works through the lab proxy
set -e

export AWS_ACCESS_KEY_ID=weedadmin
export AWS_SECRET_ACCESS_KEY=weedadmin123

exec mlflow server \
  --backend-store-uri postgresql://mlflow:mlflow123@localhost:5432/mlflow \
  --artifacts-destination s3://mlflow-artifacts \
  --host 0.0.0.0 --port 5000 \
  --allowed-hosts '*' --cors-allowed-origins '*'
```

log_test_run.py

```python
"""Log one test run against the remote MLflow setup.

Prerequisites before this script is run:
- The MLflow tracking server is already serving on http://localhost:5000
  with the PostgreSQL backend and the SeaweedFS (S3-compatible) artefact
  store, started with --artifacts-destination s3://mlflow-artifacts.
- Because the server runs in proxied artefact-serving mode, this client
  uploads artefacts *through* the MLflow server (via the mlflow-artifacts:
  proxy URI). The server — not this client — is what writes them to
  SeaweedFS, using its own AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY /
  MLFLOW_S3_ENDPOINT_URL. This client therefore needs only the tracking
  URI set below.

The DummyClassifier and the synthetic metrics values have no meaning
beyond exercising one full metadata-to-artefact round-trip.
"""
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.dummy import DummyClassifier

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("test-remote")

X = np.array([[0.0], [1.0]])
y = np.array([0, 1])
model = DummyClassifier(strategy="most_frequent").fit(X, y)

with mlflow.start_run(run_name="remote-smoke-test"):
    mlflow.log_param("source", "remote-smoke-test")
    mlflow.log_metric("accuracy", 0.87)
    mlflow.log_metric("f1_score", 0.86)
    mlflow.sklearn.log_model(model, name="model")

print("test-remote run logged successfully")

```

Run smoke test to view error.

```shell
python3 /root/code/log_test_run.py
```

Check /tmp/mlflow.log for error.

```shell
tail -n 100 /tmp/mlflow.log | grep -i error
```

Output

```shell
2026/07/30 05:24:25 ERROR mlflow.server: Exception on /api/2.0/mlflow-artifacts/artifacts/1/models/m-6a5a17c02a844d0593298abc837840a3/artifacts/requirements.txt [PUT]
    raise error_class(parsed_response, operation_name)
botocore.exceptions.ClientError: An error occurred (InvalidAccessKeyId) when calling the PutObject operation: The AWS Access Key Id you provided does not exist in our records.
    raise S3UploadFailedError(
boto3.exceptions.S3UploadFailedError: Failed to upload /tmp/tmpy4njcwnj/requirements.txt to mlflow-artifacts/1/models/m-6a5a17c02a844d0593298abc837840a3/artifacts/requirements.txt: An error occurred (InvalidAccessKeyId) when calling the PutObject operation: The AWS Access Key Id you provided does not exist in our records.
2026/07/30 05:24:25 INFO:     127.0.0.1:46314 - "PUT /api/2.0/mlflow-artifacts/artifacts/1/models/m-6a5a17c02a844d0593298abc837840a3/artifacts/requirements.txt HTTP/1.1" 500 Internal Server Error
```

*The script is calling to AWS S3 endpoints instead of localhost

Add correct endpoint for MLFlow in start script

```shell
export MLFLOW_S3_ENDPOINT_URL=http://localhost:8333
```

Try restarting the server using the restart-script

```shell
/root/code/restart-mlflow.sh
```

Check the tmp log for confirmation on restart

```shell
tail -n 30 /tmp/mlflow.log
```

Log shows successful restart. Retry smoke test

```shell
python3 /root/code/log_test_run.py
```

Output shows run was logged successfully

```shell
View experiment at: http://localhost:5000/#/experiments/1
test-remote run logged successfully
```

Confirm success in MLflow UI and SeaweedFS

![MLflow Verify Screenshot](<../screenshots/Screenshot Day 29 MLflow UI.png>)

![SeaweedFS Verify Screenshot](<../screenshots/Screenshot Day 29 SeaweedFS UI.png>)