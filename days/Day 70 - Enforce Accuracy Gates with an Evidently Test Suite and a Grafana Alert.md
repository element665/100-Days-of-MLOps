Prompt

The xFusionCorp Industries ML platform team requires the enforcement of quality gates for the fraud-detection model in two key ways: first, by establishing an **Evidently test suite** that can be executed by any CI job against a production batch, and second, by integrating this suite with Grafana to ensure that on-call personnel are notified immediately if live accuracy declines. The monitoring stack is operational, and the test-suite scaffold is already established, including data loading, classification mapping, report execution, and publication to the **Evidently UI**.

Your task consists of two parts: (1) Complete the TODO block of the scaffold with the two specified threshold metrics, execute the test suite, and examine the results in the Evidently UI; (2) Create a Grafana **alert rule** that triggers when `avg_over_time(prediction_accuracy[1m])` falls below `0.80`.

  

**Evidently test suite.**`/root/code/monitoring/tests/test_suite.py` is pre-wired except for the gates themselves; a TODO block marks where two thresholded metrics must be appended to `METRICS`:

- a missing-values gate that fails the suite when the batch carries 10 or more missing values.
    
- an accuracy gate that fails the suite when batch accuracy is 0.80 or lower.
    
    The batch it runs against is `/root/code/monitoring/tests/current.csv`(features + `is_fraud` target + the model's `prediction` column). The batch carries only a few missing values and its accuracy clears 0.80, so both gates should end up `SUCCESS`. A successful run writes `test_results.json` and publishes a snapshot to the Evidently workspace, viewable under the **Evidently UI** button (port `8000`) in the `fraud-detector quality gates` project (**Reports** tab).
    

**Grafana alert rule.** The Grafana UI is running on port `3000`. The **Grafana** button opens the login page. Admin credentials: `admin` / `grafana2026`. The **Prometheus** datasource is pre-provisioned. Metrics available:

- `prediction_accuracy` – The gauge for this task. It drifts in a random walk around 0.85, so `avg_over_time(prediction_accuracy[1m])` is the smoothed signal the alert should watch.
- `data_drift_score{column}`, `evidently_drift_share`– Per-feature PSI and the drifted-columns share, computed by the Evidently drift scorer at `/root/code/monitoring/drift/drift_scorer.py`.
- `flask_http_request_total{version, endpoint, method}`, `model_inference_duration_seconds` – The other signals from the shared metric-emitter.

The alert rule must fire when `avg_over_time(prediction_accuracy[1m])` drops below `0.80`.

The end state must include:

- `/root/code/monitoring/tests/test_results.json`exists and carries at least two Evidently test entries—a missing-values gate and an accuracy gate—all with status `SUCCESS`.
- The Evidently UI's project carries at least one published run (snapshot).
- `GET /api/v1/provisioning/alert-rules` returns a non-empty array.
- At least one rule's PromQL expression references `prediction_accuracy`.
- That rule's threshold evaluator carries `0.80` as a numeric parameter.

> The same `0.80` accuracy gate is enforced at two altitudes: the Evidently test suite fails a CI pipeline _before_ a degraded model ships, and the Grafana alert rule pages on-call _after_ live accuracy slips. Evidently's `include_tests=True` turns each metric into a pass/fail assertion—the same structure a `pytest` run gives you, but over data and model quality—and the Evidently UI is where a reviewer reads those verdicts without touching code.

---

Solution

/root/code/monitoring/tests/test_suite.py (Original)

```python
"""Run the fraud-detector quality gates as an Evidently test suite.

Startup has already seeded the latest production batch at
``tests/current.csv`` (features + the ``is_fraud`` target + the
model's ``prediction`` column), created the Evidently workspace
behind the **Evidently UI** button, and wired this script to publish
every run there. The only missing piece is the two thresholded
metrics that turn the report into a pass/fail gate -- add them in
the TODO block below, then execute the file:

    python3 /root/code/monitoring/tests/test_suite.py
"""
from __future__ import annotations

import json

import pandas as pd
from evidently import Dataset, DataDefinition, Report
from evidently.core.datasets import BinaryClassification
from evidently.metrics import Accuracy, DatasetMissingValueCount
from evidently.tests import gt, lt
from evidently.ui.workspace import Workspace

BATCH_CSV = "/root/code/monitoring/tests/current.csv"
RESULTS_JSON = "/root/code/monitoring/tests/test_results.json"
WORKSPACE_DIR = "/root/code/monitoring/workspace"
PROJECT_NAME = "fraud-detector quality gates"

# ----------------------------------------------------------------------
# TODO 1: Gate data quality -- fail the suite when the batch carries
#         10 or more missing values.
#
#         METRICS.append(DatasetMissingValueCount(tests=[lt(10)]))
#
# TODO 2: Gate model quality -- fail the suite when batch accuracy
#         is 0.80 or lower. Use `Accuracy` with `tests=[gt(0.80)]`,
#         appended the same way.
# ----------------------------------------------------------------------
METRICS = []

# (append the two thresholded metrics here)


def main() -> None:
    if not METRICS:
        print("METRICS is empty -- complete the TODO block first.")
        return

    df = pd.read_csv(BATCH_CSV)
    dd = DataDefinition(
        classification=[
            BinaryClassification(
                target="is_fraud", prediction_labels="prediction"
            )
        ]
    )
    ds = Dataset.from_pandas(df, data_definition=dd)

    # include_tests=True turns every thresholded metric into a
    # pass/fail assertion -- Evidently's "test suite" mode.
    result = Report(metrics=METRICS, include_tests=True).run(current_data=ds)

    d = result.dict()
    with open(RESULTS_JSON, "w") as fh:
        json.dump(d, fh, indent=2, default=str)

    # Publish the run to the workspace behind the Evidently UI button.
    ws = Workspace.create(WORKSPACE_DIR)
    found = ws.search_project(PROJECT_NAME)
    project = found[0] if found else ws.create_project(PROJECT_NAME)
    ws.add_run(project.id, result)

    tests = d.get("tests", [])
    passed = sum(1 for t in tests if t.get("status") == "SUCCESS")
    print(f"Tests: {passed}/{len(tests)} passed -> {RESULTS_JSON}")
    for t in tests:
        status = str(t.get("status", "")).split(".")[-1]
        print(f"  - {t.get('name')}: {status}")
    print("Run published -- refresh the Evidently UI to inspect it.")


if __name__ == "__main__":
    main()
```

TODO Section

```shell
# ----------------------------------------------------------------------
# TODO 1: Gate data quality -- fail the suite when the batch carries
#         10 or more missing values.
#
#         METRICS.append(DatasetMissingValueCount(tests=[lt(10)]))
#
# TODO 2: Gate model quality -- fail the suite when batch accuracy
#         is 0.80 or lower. Use `Accuracy` with `tests=[gt(0.80)]`,
#         appended the same way.
# ----------------------------------------------------------------------
METRICS = []

# (append the two thresholded metrics here)
METRICS.append(DatasetMissingValueCount(tests=[lt(10)]))
METRICS.append(Accuracy(tests=[gt(0.80)]))
```

(Updated)

```python
"""Run the fraud-detector quality gates as an Evidently test suite.

Startup has already seeded the latest production batch at
``tests/current.csv`` (features + the ``is_fraud`` target + the
model's ``prediction`` column), created the Evidently workspace
behind the **Evidently UI** button, and wired this script to publish
every run there. The only missing piece is the two thresholded
metrics that turn the report into a pass/fail gate -- add them in
the TODO block below, then execute the file:

    python3 /root/code/monitoring/tests/test_suite.py
"""
from __future__ import annotations

import json

import pandas as pd
from evidently import Dataset, DataDefinition, Report
from evidently.core.datasets import BinaryClassification
from evidently.metrics import Accuracy, DatasetMissingValueCount
from evidently.tests import gt, lt
from evidently.ui.workspace import Workspace

BATCH_CSV = "/root/code/monitoring/tests/current.csv"
RESULTS_JSON = "/root/code/monitoring/tests/test_results.json"
WORKSPACE_DIR = "/root/code/monitoring/workspace"
PROJECT_NAME = "fraud-detector quality gates"

# ----------------------------------------------------------------------
# TODO 1: Gate data quality -- fail the suite when the batch carries
#         10 or more missing values.
#
#         METRICS.append(DatasetMissingValueCount(tests=[lt(10)]))
#
# TODO 2: Gate model quality -- fail the suite when batch accuracy
#         is 0.80 or lower. Use `Accuracy` with `tests=[gt(0.80)]`,
#         appended the same way.
# ----------------------------------------------------------------------
METRICS = []

METRICS.append(DatasetMissingValueCount(tests=[lt(10)]))
METRICS.append(Accuracy(tests=[gt(0.80)]))


def main() -> None:
    if not METRICS:
        print("METRICS is empty -- complete the TODO block first.")
        return

    df = pd.read_csv(BATCH_CSV)
    dd = DataDefinition(
        classification=[
            BinaryClassification(
                target="is_fraud", prediction_labels="prediction"
            )
        ]
    )
    ds = Dataset.from_pandas(df, data_definition=dd)

    # include_tests=True turns every thresholded metric into a
    # pass/fail assertion -- Evidently's "test suite" mode.
    result = Report(metrics=METRICS, include_tests=True).run(current_data=ds)

    d = result.dict()
    with open(RESULTS_JSON, "w") as fh:
        json.dump(d, fh, indent=2, default=str)

    # Publish the run to the workspace behind the Evidently UI button.
    ws = Workspace.create(WORKSPACE_DIR)
    found = ws.search_project(PROJECT_NAME)
    project = found[0] if found else ws.create_project(PROJECT_NAME)
    ws.add_run(project.id, result)

    tests = d.get("tests", [])
    passed = sum(1 for t in tests if t.get("status") == "SUCCESS")
    print(f"Tests: {passed}/{len(tests)} passed -> {RESULTS_JSON}")
    for t in tests:
        status = str(t.get("status", "")).split(".")[-1]
        print(f"  - {t.get('name')}: {status}")
    print("Run published -- refresh the Evidently UI to inspect it.")


if __name__ == "__main__":
    main()
```

Run the script

```shell
python3 /root/code/monitoring/tests/test_suite.py
```

Output

```shell
Tests: 2/2 passed -> /root/code/monitoring/tests/test_results.json
  - Count and share of missing values in dataset: Less 10.000: SUCCESS
  - Accuracy metric: Greater 0.800: SUCCESS
Run published -- refresh the Evidently UI to inspect it.
```

View JSON output

```shell
cat /root/code/monitoring/tests/test_results.json
```

Output

```JSON
{
  "metrics": [
    {
      "id": "92a195ef8e4593edd8d8a033f62184ca",
      "metric_name": "DatasetMissingValueCount()",
      "config": {
        "type": "evidently:metric_v2:DatasetMissingValueCount",
        "tests": [
          {
            "type": "evidently:test_v2:LessThanMetricTest",
            "is_critical": true,
            "threshold": 10.0
          }
        ]
      },
      "value": {
        "count": 3.0,
        "share": 0.015
      }
    },
    {
      "id": "7a7b0ce567d19ba36db88fd3d6a3f9ca",
      "metric_name": "Accuracy(classification_name=default)",
      "config": {
        "type": "evidently:metric_v2:Accuracy",
        "tests": [
          {
            "type": "evidently:test_v2:GreaterThanMetricTest",
            "is_critical": true,
            "threshold": 0.8
          }
        ],
        "classification_name": "default"
      },
      "value": 0.89
    }
  ],
  "tests": [
    {
      "id": "lt",
      "name": "Count and share of missing values in dataset: Less 10.000",
      "description": "Count and share of missing values in dataset: Actual value 3.000 < 10.000",
      "metric_config": {
        "metric_id": "92a195ef8e4593edd8d8a033f62184ca",
        "params": {
          "type": "evidently:metric_v2:DatasetMissingValueCount",
          "tests": [
            {
              "type": "evidently:test_v2:LessThanMetricTest",
              "is_critical": true,
              "threshold": 10.0
            }
          ]
        }
      },
      "test_config": {
        "type": "evidently:test_v2:LessThanMetricTest",
        "is_critical": true,
        "alias": null,
        "label_filters": null,
        "threshold": 10.0
      },
      "status": "SUCCESS",
      "bound_test": {
        "type": "evidently:bound_test:CountBoundTest",
        "test": {
          "type": "evidently:test_v2:LessThanMetricTest",
          "is_critical": true,
          "alias": null,
          "label_filters": null,
          "threshold": 10.0
        },
        "metric_fingerprint": "92a195ef8e4593edd8d8a033f62184ca",
        "is_count": true
      }
    },
    {
      "id": "gt",
      "name": "Accuracy metric: Greater 0.800",
      "description": "Accuracy metric: Actual value 0.890 >= 0.800",
      "metric_config": {
        "metric_id": "7a7b0ce567d19ba36db88fd3d6a3f9ca",
        "params": {
          "type": "evidently:metric_v2:Accuracy",
          "tests": [
            {
              "type": "evidently:test_v2:GreaterThanMetricTest",
              "is_critical": true,
              "threshold": 0.8
            }
          ],
          "classification_name": "default"
        }
      },
      "test_config": {
        "type": "evidently:test_v2:GreaterThanMetricTest",
        "is_critical": true,
        "alias": null,
        "label_filters": null,
        "threshold": 0.8
      },
      "status": "SUCCESS",
      "bound_test": {
        "type": "evidently:bound_test:SingleValueBoundTest",
        "test": {
          "type": "evidently:test_v2:GreaterThanMetricTest",
          "is_critical": true,
          "alias": null,
          "label_filters": null,
          "threshold": 0.8
        },
        "metric_fingerprint": "7a7b0ce567d19ba36db88fd3d6a3f9ca"
      }
    }
  ]
}
```

Login to Grafana UI

![screenshot](<../screenshots/Screenshot Day 70 Granfa UI login.png>)

Navigate to Alerting -> Alert rules -> New alert rule

![screenshot](<../screenshots/Screenshot Day 70 new alert rule.png>)

Configure New alert rule in Grafana (avg_over_time(prediction_accuracy[1m]))

![screenshot](<../screenshots/Screenshot Day 70 config new alert rule.png>)

Save New alert rule

![screenshot](<../screenshots/Screenshot Day 70 save new alert rule.png>)

Final Grafana Query

![screenshot](<../screenshots/Screenshot Day 70 final query.png>)

Open Evidently UI

![screenshot](<../screenshots/Screenshot Day 70 Evidently UI.png>)

View Report

![screenshot](<../screenshots/Screenshot Day 70 Evidently report metrics.png>)

View Tests in Report

![screenshot](<../screenshots/Screenshot Day 70 Evidently report tests.png>)

---
### Provided Files

/root/code/monitoring/app/metric_emitter.py

```python
"""Metric emitter for the Monitoring-section labs.

Exposes a Prometheus `/metrics` endpoint carrying the ML-serving signals:
  - `flask_http_request_total{version}`     — request counter, labelled by model version.
  - `prediction_accuracy`                   — gauge, random walk around 0.85.
  - `data_drift_score{column}`              — per-feature PSI, computed by the
                                              Evidently drift scorer
                                              (`../drift/drift_scorer.py`) and
                                              read from the bind-mounted
                                              scores file.
  - `evidently_drift_share`                 — share of feature columns Evidently
                                              flags as drifted in the latest window.
  - `model_inference_duration_seconds`      — latency histogram.

A background thread refreshes the gauges and increments the counters
every 5 seconds so Grafana panels built on top of these metrics see
real motion rather than flat lines. Until the Evidently scorer has
produced its first scores file, the drift gauges fall back to a
deterministic random walk so panels never flatline.
"""
import json
import os
import random
import threading
import time

from flask import Flask, jsonify
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST

app = Flask(__name__)

REGISTRY = CollectorRegistry()

DRIFT_SCORES_PATH = os.environ.get("DRIFT_SCORES_PATH", "/drift/drift_scores.json")

REQUEST_TOTAL = Counter(
    "flask_http_request_total",
    "Total HTTP requests handled, labelled by model version.",
    labelnames=["version", "endpoint", "method"],
    registry=REGISTRY,
)

PREDICTION_ACCURACY = Gauge(
    "prediction_accuracy",
    "Rolling prediction accuracy on the shadow eval set.",
    registry=REGISTRY,
)

DATA_DRIFT_SCORE = Gauge(
    "data_drift_score",
    "Population Stability Index (PSI) per feature column, "
    "scored by the Evidently drift scorer.",
    labelnames=["column"],
    registry=REGISTRY,
)

EVIDENTLY_DRIFT_SHARE = Gauge(
    "evidently_drift_share",
    "Share of feature columns Evidently flags as drifted "
    "in the latest scoring window.",
    registry=REGISTRY,
)

INFERENCE_LATENCY = Histogram(
    "model_inference_duration_seconds",
    "End-to-end inference duration in seconds.",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=REGISTRY,
)


def _read_evidently_scores():
    """Latest per-column scores from the Evidently drift scorer.

    Returns ({column: psi}, drift_share), or None while the scorer has
    not produced a readable scores file yet.
    """
    try:
        with open(DRIFT_SCORES_PATH) as fh:
            payload = json.load(fh)
        scores = {
            str(column): float(value)
            for column, value in (payload.get("drift_scores") or {}).items()
        }
        if not scores:
            return None
        return scores, float(payload.get("drift_share", 0.0))
    except (OSError, ValueError):
        return None


def _nudge_metrics() -> None:
    random.seed(42)
    accuracy = 0.85
    fallback_drift = {"amount": 0.10, "hour": 0.12, "num_tx_past_day": 0.08}
    while True:
        # Simulate a handful of requests across two model versions.
        for version in ("v1", "v1", "v1", "v2"):
            REQUEST_TOTAL.labels(version=version, endpoint="/predict", method="POST").inc()
            INFERENCE_LATENCY.observe(random.uniform(0.005, 0.15))

        # Random-walk the accuracy around 0.85, clipped to [0.70, 0.95].
        accuracy = max(0.70, min(0.95, accuracy + random.uniform(-0.02, 0.02)))
        PREDICTION_ACCURACY.set(accuracy)

        # Republish the Evidently-computed drift scores; fall back to a
        # random walk only while the scorer's first file is pending.
        evidently = _read_evidently_scores()
        if evidently is not None:
            scores, drift_share = evidently
            for column, score in scores.items():
                DATA_DRIFT_SCORE.labels(column=column).set(score)
            EVIDENTLY_DRIFT_SHARE.set(drift_share)
        else:
            for column in fallback_drift:
                fallback_drift[column] = max(
                    0.01,
                    min(0.60, fallback_drift[column] + random.uniform(-0.02, 0.03)),
                )
                DATA_DRIFT_SCORE.labels(column=column).set(fallback_drift[column])

        time.sleep(5)


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/metrics")
def metrics():
    return generate_latest(REGISTRY), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    threading.Thread(target=_nudge_metrics, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
```

/root/code/monitoring/app/Dockerfile

```yaml
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask prometheus-client

COPY metric_emitter.py /app/metric_emitter.py

EXPOSE 5000
CMD ["python3", "/app/metric_emitter.py"]
```

/root/code/monitoring/drift/drift_scorer.py

```python
"""Evidently drift scorer for the Monitoring-section labs.

Builds a fixed *reference* window of fraud-transaction features once,
then loops forever. Every cycle it:

1. Synthesizes a fresh *current* window whose distribution slowly walks
   away from (and back toward) the reference — so drift rises and falls
   the way a real production feed would.
2. Scores per-column drift with Evidently (`ValueDrift`, PSI) and the
   dataset-level drifted-columns share (`DriftedColumnsCount`).
3. Atomically rewrites `drift_scores.json` next to this script. The
   metric-emitter container bind-mounts this directory read-only and
   republishes the scores as the `data_drift_score{column}` and
   `evidently_drift_share` Prometheus gauges.
4. Every few cycles, saves the full Evidently report as
   `drift_report.html` so the latest scoring window can be inspected.
5. If `DRIFT_WORKSPACE` is set, also publishes every few cycles' run
   to that Evidently workspace — the project behind the lab's
   Evidently UI button accumulates one report per publish, so the
   UI's Dashboard tab plots drift over time.
"""
import json
import math
import os
import time

import numpy as np
import pandas as pd
from evidently import Dataset, DataDefinition, Report
from evidently.metrics import DriftedColumnsCount, ValueDrift

HERE = os.path.dirname(os.path.abspath(__file__))
SCORES_PATH = os.path.join(HERE, "drift_scores.json")
REPORT_PATH = os.path.join(HERE, "drift_report.html")

COLUMNS = ["amount", "hour", "num_tx_past_day"]
ROWS = 300
CYCLE_SECONDS = 15
REPORT_EVERY_N_CYCLES = 4

# Optional: publish runs to an Evidently workspace (the UI button).
WORKSPACE_DIR = os.environ.get("DRIFT_WORKSPACE", "")
PROJECT_NAME = os.environ.get("DRIFT_PROJECT", "fraud-detector drift monitoring")
PUBLISH_EVERY_N_CYCLES = 4


def _make_window(rng: np.random.Generator, shift: float) -> pd.DataFrame:
    """One window of fraud-transaction features.

    `shift = 0.0` reproduces the reference distribution; larger values
    push every column further away from it.
    """
    amount = rng.normal(120.0 * (1.0 + shift), 40.0, ROWS).clip(min=1.0)

    # A `shift`-sized slice of transactions migrates into late-night hours.
    late_share = min(max(shift, 0.0), 0.9)
    late_mask = rng.random(ROWS) < late_share
    hour = rng.integers(0, 24, ROWS)
    hour[late_mask] = rng.integers(18, 24, int(late_mask.sum()))

    num_tx = rng.poisson(4.0 * (1.0 + shift), ROWS)

    return pd.DataFrame(
        {"amount": amount.round(2), "hour": hour, "num_tx_past_day": num_tx}
    )


def _build_metrics():
    """Per-column PSI metrics + the dataset-level drifted-columns share.

    PSI keeps the published score on the 'higher = more drift' scale the
    labs' Grafana panels describe. If this Evidently build doesn't take
    a `method` kwarg, fall back to the column default — the score stays
    in [0, 1] either way.
    """
    try:
        per_column = [ValueDrift(column=c, method="psi") for c in COLUMNS]
    except TypeError:
        per_column = [ValueDrift(column=c) for c in COLUMNS]
    return per_column + [DriftedColumnsCount()]


def _extract(result_dict: dict):
    """Pull {column: score} + drift share out of `Report(...).run().dict()`."""
    scores: dict = {}
    share = 0.0
    drifted = 0
    for m in result_dict.get("metrics", []) or []:
        name = str(m.get("metric_name") or m.get("metric_id") or "")
        value = m.get("value")
        if name.startswith("ValueDrift(column="):
            column = name[len("ValueDrift(column="):].split(",")[0].rstrip(")")
            try:
                scores[column] = round(float(value), 4)
            except (TypeError, ValueError):
                continue
        elif "DriftedColumnsCount" in name and isinstance(value, dict):
            share = round(float(value.get("share", 0.0)), 4)
            drifted = int(float(value.get("count", 0)))
    return scores, share, drifted


def _write_json_atomic(path: str, payload: dict) -> None:
    """tmp-file + rename so the emitter never reads a half-written JSON."""
    tmp = f"{path}.tmp"
    with open(tmp, "w") as fh:
        json.dump(payload, fh, indent=2)
    os.replace(tmp, path)


def main() -> None:
    rng_ref = np.random.default_rng(42)
    reference = _make_window(rng_ref, shift=0.0)
    ref_ds = Dataset.from_pandas(reference, data_definition=DataDefinition())

    workspace = project = None
    if WORKSPACE_DIR:
        # Lazy import: headless labs never pay for the UI machinery.
        from evidently.ui.workspace import Workspace

        workspace = Workspace.create(WORKSPACE_DIR)
        found = workspace.search_project(PROJECT_NAME)
        project = found[0] if found else workspace.create_project(PROJECT_NAME)

    rng_cur = np.random.default_rng(99)
    cycle = 0
    while True:
        # Drift breathes: a slow sine sweep plus per-cycle noise, so the
        # per-column PSI climbs and recedes over the life of the lab.
        shift = 0.20 + 0.18 * math.sin(2 * math.pi * cycle / 40.0)
        shift += float(rng_cur.uniform(-0.03, 0.03))
        current = _make_window(rng_cur, shift=max(shift, 0.0))
        cur_ds = Dataset.from_pandas(current, data_definition=DataDefinition())

        try:
            result = Report(_build_metrics()).run(
                current_data=cur_ds, reference_data=ref_ds
            )
            scores, share, drifted = _extract(result.dict())
            if scores:
                payload = {
                    "source": "evidently",
                    "method": "psi",
                    "drift_scores": scores,
                    "drift_share": share,
                    "drifted_columns": drifted,
                    "rows_scored": ROWS,
                    "cycle": cycle,
                }
                _write_json_atomic(SCORES_PATH, payload)
            if cycle % REPORT_EVERY_N_CYCLES == 0:
                result.save_html(REPORT_PATH)
            if workspace is not None and cycle % PUBLISH_EVERY_N_CYCLES == 0:
                workspace.add_run(project.id, result)
        except Exception as exc:  # noqa: BLE001 — keep the loop alive
            print(f"[drift-scorer] cycle {cycle} failed: {exc}", flush=True)

        cycle += 1
        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    main()
```

/root/code/monitoring/grafana/alerting/contact-points.yml

```yaml
apiVersion: 1

contactPoints:
  - orgId: 1
    name: default
    receivers:
      - uid: default-email
        type: email
        settings:
          addresses: noreply@example.com
          singleEmail: false
```

/root/code/monitoring/grafana/datasources/prometheus.yml

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

/root/code/monitoring/docker-compose.yml

```yaml
services:
  metric-emitter:
    build: ./app
    container_name: metric-emitter
    volumes:
      # Evidently drift scorer output (host-side loop) — the emitter
      # republishes these scores as Prometheus gauges.
      - ./drift:/drift:ro

  prometheus:
    image: prom/prometheus:v3.13.0
    container_name: mon-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    depends_on:
      - metric-emitter

  grafana:
    image: grafana/grafana:13.1.0
    container_name: mon-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=grafana2026
      - GF_AUTH_ANONYMOUS_ENABLED=false
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - prometheus
```

/root/code/monitoring/prometheus.yml

```yaml
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: metric-emitter
    static_configs:
      - targets:
          - metric-emitter:5000
```