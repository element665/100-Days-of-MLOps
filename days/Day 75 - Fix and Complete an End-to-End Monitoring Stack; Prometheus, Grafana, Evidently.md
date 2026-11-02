Prompt

The xFusionCorp Industries ML platform team attempted to implement a complete end-to-end monitoring stack for the fraud-detection model. This stack includes an **Evidently** drift scorer connected to a Flask metric-emitter, which is then scraped by **Prometheus** and visualized using **Grafana**. However, the monitoring flow is currently non-functional. Grafana displays empty panels, Prometheus indicates that the `metric-emitter` is DOWN on the `Targets` page, and attempts to access the emitter's `/metrics` endpoint result in a 404 error. The Evidently scorer itself is operational, as evidenced by the presence of drift scores in the hand-off file; however, all downstream components are failing, preventing any signals from reaching the dashboard. Within the stack's configuration, there are three wiring issues that need to be addressed. Your primary objective is to identify and resolve all three issues, and subsequently, to construct a tagged **monitoring overview** dashboard in Grafana.

  

The stack is at `/root/code/monitoring/` with three services defined in `docker-compose.yml`, plus the host-side Evidently scorer:

- `metric-emitter` – Flask exporter (Python source bind-mounted). Republishes the Evidently drift scores as `data_drift_score{column}` / `evidently_drift_share`next to its own serving signals.
- `mon-prometheus` – Port `9090`.
- `mon-grafana` – Port `3000`, admin / `grafana2026`. The Prometheus datasource is provisioned on boot.
- Evidently drift scorer – host process (`drift/drift_scorer.py`), rescores per-feature PSI every 15 s into `drift/drift_scores.json` and publishes a run to the **Evidently UI** (port `8000`) every ~minute. **Healthy—not part of the bug hunt.** The Evidently UI button -> `fraud-detector drift monitoring` -> **Dashboard** tab confirms drift data is flowing at the source; everything downstream of it is what's broken.

**Three integration bugs** must be diagnosed and fixed — each lives in exactly one configuration file under `/root/code/monitoring/`. The symptoms:

- `metric-emitter`'s `/metrics` endpoint returns `404`.
    
- Prometheus's **Targets** page lists `metric-emitter` as `DOWN`.
    
- Grafana renders empty panels even when Prometheus has fresh samples.
    
    Start from the emitter itself — `curl -i http://localhost:5000/metrics` shows the 404, and `docker compose ps` from `/root/code/monitoring/`shows what is running. The affected services must be reloaded for the fixed configs to take effect.
    

**A tagged monitoring-overview dashboard** must also be built in Grafana (port `3000`, the **Grafana** button, admin / `grafana2026`): three panels covering request rate, p95 inference latency, and prediction accuracy (or similar signals from the shared metric-emitter, e.g. the Evidently-computed `data_drift_score`), saved with a title and at least one **tag**(e.g. `mlops` or `monitoring`) so the ops team can find it from the Dashboards search.

The end state must include:

- `curl -sf http://localhost:5000/metrics` returns HTTP 200.
- Prometheus `GET /api/v1/targets` lists the `metric-emitter` job with `health: "up"`.
- Grafana `GET /api/datasources` shows the Prometheus datasource URL ending in `:9090`.
- One user-created dashboard has 3 or more panels and at least one tag.
- The Evidently UI's project keeps accumulating scoring runs (pre-wired—nothing to change).

> A monitoring stack is only as useful as its weakest link. Evidently can score drift perfectly and still page nobody: each of these three bugs is silent on its own—none of them crashes a container—but together they cost you every metric Grafana would otherwise surface. The capstone is reading failure symptoms back to their config file, not retyping Python.

---

Solution

/root/code/monitoring/grafana/provisioning/datasources/prometheus.yml references incorrect port (9091 -> 9090)

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

/root/code/monitoring/prometheus.yml references incorrect metric-emitter port (8000 -> 5000)

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

Correct metric-emitter '/metrics' endpoint in /root/code/monitoring/app/metric-emitter.py

```python
# orignal line @app.route("/prom-metrics")
@app.route("/metrics")
```

Rebuild stack to apply updates

```shell
cd /root/code/monitoring
docker compose down
docker compose up -d
```

Grafana steps

- Login to Grafana UI (admin/grafana2026)

- Create new dashboard (ex: ML Ops Fraud-detection Model)

- Add 3 panels (ex: Data Drift Score, Prediction Accuracy, Status)

- Configure 3 panels 

- Tag dashboard (ex: monitoring)

- Save dashboard

### Verification

Confirm '/metrics' endpoint now shows HTTP/1.1 200 OK

```shell
curl -i http://localhost:5000/metrics | grep 200
```

Output

```shell
HTTP/1.1 200 OK
```

Confirm Prometheus lists metric-emitter with health: "up"

```shell
curl -sf http://localhost:9090/api/v1/targets | jq '.data.activeTargets[0].health'
```

Output

```shell
"up"
```

Confirm Grafana shows the Prometheus datasource

```shell
curl -s -u admin:grafana2026 'http://localhost:3000/api/datasources' | jq -r '.[0].url'
```

Output

```shell
http://prometheus:9090
```

Grafana has at least one dashboard with one tag

```shell
curl -s -u admin:grafana2026 'http://localhost:3000/api/search?type=dash-db'
```

Output

```shell
[{"id":593436330786816,"uid":"adf9hsq","orgId":1,"title":"ML Ops Fraud-detection Model","uri":"db/ml-ops-fraud-detection-model","url":"/d/adf9hsq/ml-ops-fraud-detection-model","slug":"","type":"dash-db","tags":["monitoring"],"isStarred":false,"sortMeta":0,"isDeleted":false}]
```

Grafana has at least three panels

```
curl -s -u admin:grafana2026 'http://localhost:3000/api/dashboards/uid/adf9hsq' | jq '.dashboard.panels[] | {id, title, type}'
```

Output

```shell
{
  "id": 3,
  "title": "Status",
  "type": "stat"
}
{
  "id": 2,
  "title": "Prediction Accuracy",
  "type": "timeseries"
}
{
  "id": 1,
  "title": "Data Drift",
  "type": "timeseries"
}
```

### Screenshots

Evidently UI's project keeps accumulating scoring runs

![screenshot](<../screenshots/Screenshot Day 75 Evidently UI.png>)

Prometheus UI shows target heath for metric-emitter as UP

![screenshot](<../screenshots/Screenshot Day 75 Prometheus UI.png>)

Grafana UI final dashboard

![screenshot](<../screenshots/Screenshot Day 75 Grafana UI.png>)
