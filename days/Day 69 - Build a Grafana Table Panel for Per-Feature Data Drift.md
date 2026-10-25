Prompt

The xFusionCorp Industries ML platform team monitors per-feature data drift for the fraud-detection model using a Grafana table. This table presents one row for each feature and one column for each drift score, allowing reviewers to easily scan the entire feature set. The monitoring stack is operational; the Flask metric-emitter exposes `data_drift_score` as a labeled gauge (with one time-series per feature), Prometheus is actively scraping the data, and Grafana has the Prometheus datasource pre-provisioned. Your objective is to create a Grafana dashboard featuring a **Table** panel that displays the `data_drift_score`values for each column.

  

The Grafana UI is running on port `3000`. The **Grafana** button opens the login page. Admin credentials: `admin` / `grafana2026`. The **Prometheus** datasource is pre-provisioned.

Metrics available on the Prometheus datasource:

- `data_drift_score{column="amount"}`, `data_drift_score{column="hour"}`, `data_drift_score{column="num_tx_past_day"}` – The gauge for this task, one series per feature column.
- `prediction_accuracy`, `flask_http_request_total{version, endpoint, method}`, `model_inference_duration_seconds` – The other signals from the shared metric-emitter.

The end state must include:

- `GET /api/search?type=dash-db` returns at least one user-created dashboard.
- At least one panel across your dashboards has `type: table`.
- At least one of those panel's Prometheus targets references `data_drift_score`.
- Querying `data_drift_score` through Grafana's datasource proxy returns non-empty Prometheus series whose labels include `column` – Confirming the table has per-feature rows to render.

> A per-feature drift view answers 'which input shifted?' at a glance — a Table panel is the natural shape for it, one row per feature carrying that feature's latest drift score.

---

Solution

Login to Grafana UI

![screenshot](<../screenshots/Screenshot Day 69 Login to Grafana UI.png>)

Confirm Prometheus as data source

![screenshot](<../screenshots/Screenshot Day 69 Confirm data source.png>)

Navigate to Dashboard menu

![screenshot](<../screenshots/Screenshot Day 69 dashboard menu.png>)

Create new dashboard

![screenshot](<../screenshots/Screenshot Day 69 new dashboard.png>)

Create new panel

![screenshot](<../screenshots/Screenshot Day 69 create panel.png>)

Configure panel to be Table and use data_drift_score as Metric

![screenshot](<../screenshots/Screenshot Day 69 config metric.png>)

Save panel

![screenshot](<../screenshots/Screenshot Day 69 save panel.png>)

Save Dashboard

![screenshot](<../screenshots/Screenshot Day 69 save dashboard.png>)

Remove unwanted columns to cleanup table(Not required) 

![screenshot](<../screenshots/Screenshot Day 69 organize table.png>)

Final Dashboard

![screenshot](<../screenshots/Screenshot Day 69 final dashboard.png>)

---
### Verification

Confirm Dashboard exists 

```shell
curl -s -u admin:grafana2026 'http://localhost:3000/api/search?type=dash-db'
```

Output

```shell
[{"id":2168665770360832,"uid":"ad29kfv","orgId":1,"title":"xFusionCorp Industries - Fraud-detection Model","uri":"db/xfusioncorp-industries-fraud-detection-model","url":"/d/ad29kfv/xfusioncorp-industries-fraud-detection-model","slug":"","type":"dash-db","tags":[],"isStarred":false,"sortMeta":0,"isDeleted":false}]
```

Confirm Panel is a table and its target uses data_drift_score

```shell
curl -s -u admin:grafana2026 'http://localhost:3000/api/dashboards/uid/ad29kfv' | grep -oE '"type":"table"|"expr":"[^"]*"'
```

Output

```shell
"expr":"data_drift_score"
"type":"table"
```

Confirm datasource proxy returns series with a "column" label

```shell
DS_UID=$(curl -s -u admin:grafana2026 http://localhost:3000/api/datasources | grep -o '"uid":"[^"]*"' | head -1 | cut -d'"' -f4)
curl -s -u admin:grafana2026 \
  "http://localhost:3000/api/datasources/proxy/uid/$DS_UID/api/v1/query?query=data_drift_score"
```

Output

```shell
{"status":"success","data":{"resultType":"vector","result":[{"metric":{"__name__":"data_drift_score","column":"amount","instance":"metric-emitter:5000","job":"metric-emitter"},"value":[1792938254.281,"0.6"]},{"metric":{"__name__":"data_drift_score","column":"hour","instance":"metric-emitter:5000","job":"metric-emitter"},"value":[1792938254.281,"0.5802948319705279"]},{"metric":{"__name__":"data_drift_score","column":"num_tx_past_day","instance":"metric-emitter:5000","job":"metric-emitter"},"value":[1792938254.281,"0.6"]}]}}
```
