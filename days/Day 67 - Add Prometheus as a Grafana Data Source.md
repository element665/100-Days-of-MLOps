Prompt

The xFusionCorp Industries ML platform team is in the process of implementing Grafana-based monitoring for their fraud-detection model. Although Prometheus and Grafana are already running in Docker, alongside a Flask metric emitter that provides live ML signals, Grafana currently lacks a configured data source, preventing the UI from accessing any metrics.

Your objective is to access the Grafana interface, configure the running Prometheus container as a data source through the Grafana UI, and create an initial dashboard panel that queries a live metric. This will ensure that the connection functions correctly end to end.

  

The Grafana UI is already running on port `3000`. The **Grafana**button at the top of the lab opens the login page. Admin credentials: `admin` / `grafana2026`.

The stack running under `/root/code/monitoring/` (via `docker compose`):

- `metric-emitter` – Flask app exposing `/metrics` with `flask_http_request_total{version}`, `prediction_accuracy`, `data_drift_score{column}`, and `model_inference_duration_seconds` metrics. A background thread nudges the values every 5 seconds so panels built on top see real motion.
- `mon-prometheus` – Prometheus, scraping `metric-emitter:5000` every 5 seconds. Reachable inside the compose network as `http://prometheus:9090`.
- `mon-grafana` – Grafana, no data sources configured.

The end state must include:

- A data source of type `prometheus` exists in Grafana's configuration.
- Its URL is `http://prometheus:9090` (the compose service name – `localhost:9090` does NOT work from inside the Grafana container).
- Grafana's `/api/datasources/uid/<uid>/health` check reports `status: OK`.
- At least one saved dashboard exists carrying a panel whose query targets a metric (a non-empty PromQL expression) — proof the data source actually returns data.

> Grafana and Prometheus share a Docker network. Inside the Grafana container, `localhost` refers to Grafana itself, not to Prometheus.

---
### Provided Files

metric-emitter.py

```python
"""Metric emitter for the Monitoring-section labs.

Exposes a Prometheus `/metrics` endpoint carrying four simulated
ML-serving signals:
  - `flask_http_request_total{version}`     — request counter, labelled by model version.
  - `prediction_accuracy`                   — gauge, random walk around 0.85.
  - `data_drift_score{column}`              — per-feature drift share.
  - `model_inference_duration_seconds`      — latency histogram.

A background thread nudges the gauges and increments the counters
every 5 seconds so Grafana panels built on top of these metrics
see real motion rather than flat lines.
"""
import random
import threading
import time

from flask import Flask, jsonify
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST

app = Flask(__name__)

REGISTRY = CollectorRegistry()

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
    "Population Stability Index (PSI) per feature column.",
    labelnames=["column"],
    registry=REGISTRY,
)

INFERENCE_LATENCY = Histogram(
    "model_inference_duration_seconds",
    "End-to-end inference duration in seconds.",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=REGISTRY,
)


def _nudge_metrics() -> None:
    random.seed(42)
    accuracy = 0.85
    drift = {"amount": 0.10, "hour": 0.12, "num_tx_past_day": 0.08}
    while True:
        # Simulate a handful of requests across two model versions.
        for version in ("v1", "v1", "v1", "v2"):
            REQUEST_TOTAL.labels(version=version, endpoint="/predict", method="POST").inc()
            INFERENCE_LATENCY.observe(random.uniform(0.005, 0.15))

        # Random-walk the accuracy around 0.85, clipped to [0.70, 0.95].
        accuracy = max(0.70, min(0.95, accuracy + random.uniform(-0.02, 0.02)))
        PREDICTION_ACCURACY.set(accuracy)

        # Random-walk each column's drift score.
        for column, base in drift.items():
            drift[column] = max(0.01, min(0.60, drift[column] + random.uniform(-0.02, 0.03)))
            DATA_DRIFT_SCORE.labels(column=column).set(drift[column])

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

prometheus.yml

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

docker-compose.yml

```yaml
services:
  metric-emitter:
    build: ./app
    container_name: metric-emitter

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
    depends_on:
      - prometheus
```

---
### Solution

Login to Grafana UI

![screenshot](<../screenshots/Screenshot Day 67 Grafana UI login.png>)

Add new Data source

![screenshot](<../screenshots/Screenshot Day 67 Add Data source.png>)

Select Prometheus as source

![screenshot](<../screenshots/Screenshot Day 67 select Prometheus data source.png>)

Configure using Prometheus server info

![screenshot](<../screenshots/Screenshot Day 67 configure prometheus source.png>)

Save & test connection when completed

![screenshot](<../screenshots/Screenshot Day 67 Save and test data source.png>)

Create new Dashboard

![screenshot](<../screenshots/Screenshot Day 67 Create Dashboard.png>)

Add panel to new dashboard and select metric for panel

![screenshot](<../screenshots/Screenshot Day 67 add panel to dashboard.png>)

Add a couple of extra panels for good measure and design

![screenshot](<../screenshots/Screenshot Day 67 final dashboard.png>)

---
### Verification

Get uid from Grafana

```shell
DS_UID=$(curl -s -u admin:grafana2026 http://localhost:3000/api/datasources | jq -r '.[].uid')
```

UID

```JSON
bg23s3lzdkhs0c
```

Check Grafana's /health api

```shell
curl -s -u admin:grafana2026 "http://localhost:3000/api/datasources/uid/$DS_UID/health" | jq -c '{status}'
```

Output

```JSON
{"status":"OK"}
```

Confirm data source type and URL

```shell
curl -s -u admin:grafana2026 http://localhost:3000/api/datasources | jq '.[] | {name, type, url}'
```

Output

```JSON
{
  "name": "prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090"
}
```

Confirm saved dashboard

```shell
curl -s -u admin:grafana2026 'http://localhost:3000/api/search?type=dash-db' | jq -r '.[] | "\(.uid)  \(.title)"'
```

Output

```text
ad2cqd9  Fraud-Detection Model
```

PromQL expressions in that dashboard's panels

```shell
curl -s -u admin:grafana2026 http://localhost:3000/api/dashboards/uid/ad2cqd9 | jq '.dashboard.panels[].targets[].expr'
```

Output

```JSON
"data_drift_score"
"prediction_accuracy"
"rate(flask_http_request_total[$__rate_interval])"
"up"
```