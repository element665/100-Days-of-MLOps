Prompt

The xFusionCorp Industries ML platform team monitors the rolling prediction accuracy of the fraud-detection model using a Grafana dashboard. The monitoring stack is operational, with the Flask metric-emitter exposing `prediction_accuracy` as a gauge. Prometheus is configured to scrape this metric, and the Prometheus datasource is already pre-provisioned in Grafana. Your objective is to create a Grafana dashboard featuring a time-series panel that visualizes `prediction_accuracy` over time.

  

The Grafana UI is running on port `3000`. The **Grafana** button opens the login page. Admin credentials: `admin` / `grafana2026`. The **Prometheus** datasource is already wired (pre-provisioned at startup—no datasource form to fill).

Available metrics on the `Prometheus` datasource include:

- `prediction_accuracy` – The gauge for this task.
- `flask_http_request_total{version, endpoint, method}` – Counter.
- `data_drift_score{column}` – Per-column drift gauge.
- `model_inference_duration_seconds` – Latency histogram.

The end state must include:

- Grafana's **Data sources** list shows a provisioned **Prometheus** datasource (pre-staged).
- `GET /api/search?type=dash-db` returns at least one user-created dashboard.
- That dashboard carries at least one panel whose `type`is `timeseries`.
- At least one panel across your dashboards has a Prometheus query that references `prediction_accuracy`.

---

Solution

Login to Grafana UI

![screenshot](<../screenshots/Screenshot Day 68 Grafana UI login.png>)

Select Dashboards from side menu

![screenshot](<../screenshots/Screenshot Day 68 select dashboard.png>)

Create dashboard

![screenshot](<../screenshots/Screenshot Day 68 create dashboard.png>)

Add panel to dashboard

![screenshot](<../screenshots/Screenshot Day 68 add panel.png>)

Configure visualization as time series

![screenshot](<../screenshots/Screenshot Day 68 config visual.png>)

Select prediction_accuracy as Metric

![screenshot](<../screenshots/Screenshot Day 68 config metric.png>)

Save panel and dashboard

![screenshot](<../screenshots/Screenshot Day 68 save panel and dash.png>)

Final dashboard

![screenshot](<../screenshots/Screenshot Day 68 final dash.png>)


### Verification

Confirm dashboard exists

```shell
curl -s -u admin:grafana2026 "http://localhost:3000/api/search?type=dash-db"
```

Output

```shell
[{"id":1738662057193472,"uid":"adz8l8b","orgId":1,"title":"Fraud Detection Model Monitoring","uri":"db/fraud-detection-model-monitoring","url":"/d/adz8l8b/fraud-detection-model-monitoring","slug":"","type":"dash-db","tags":[],"isStarred":false,"sortMeta":0,"isDeleted":false}]
```

Capture UID for further checks

```shell
DS_UID=$(curl -s -u admin:grafana2026 "http://localhost:3000/api/search?type=dash-db" | jq -r '.[].uid')
```

Confirm panel uses prediction_accuracy and is type timeseries

```shell
curl -s -u admin:grafana2026 "http://localhost:3000/api/dashboards/uid/$DS_UID" | grep -oE '"type":"timeseries"|"expr":"[^"]*"'
```

Output

```shell
"expr":"prediction_accuracy"
"type":"timeseries"
```
