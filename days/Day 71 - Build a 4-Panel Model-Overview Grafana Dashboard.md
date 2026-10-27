Prompt

The xFusionCorp Industries ML platform team requires the creation of a **model-overview dashboard** in Grafana. This dashboard should display the following metrics side-by-side: request rate, p95 inference latency, current prediction accuracy, and Evidently-computed per-feature drift. This setup will facilitate a quick assessment of the model's health by the on-call engineer.

The existing monitoring stack includes the following components: an **Evidently drift scorer** that recalculates per-feature drift (PSI) against a reference window every 15 seconds; a Flask metric-emitter that republishes these scores alongside its serving signals; Prometheus, which is actively scraping data; and Grafana, which has the Prometheus datasource pre-provisioned.

Your task is to construct a **4-panel Grafana dashboard**that integrates multiple visualization types effectively.

  

The Grafana UI is running on port `3000`. The **Grafana** button opens the login page. Admin credentials: `admin` / `grafana2026`. The **Prometheus** datasource is pre-provisioned.

The dashboard must contain one panel for each of the four signals below, and mix at least three distinct visualization types across them:

- **Request rate** – built from the `flask_http_request_total` counter (labels `version`, `endpoint`, `method`).
- **p95 inference latency** – built from the `model_inference_duration_seconds` histogram (its `_bucket` series carry the `le` label).
- **Prediction accuracy** – the `prediction_accuracy`gauge.
- **Drift by column** – the `data_drift_score` gauge, one series per `column` label. This is the Evidently signal: each value is the PSI the drift scorer computed for that feature in the latest window.

The same drift data is also visible from Evidently's side for cross-checking: the **Evidently UI** button (port `8000`) opens the `fraud-detector drift monitoring` project, whose **Dashboard**tab plots the drifted-columns share and per-column PSI over time (a new scoring run lands roughly every minute) and whose **Reports** tab lists the underlying runs. Nothing to configure there—it's the same drift data, seen from Evidently's side.

The end state must include:

- `GET /api/search?type=dash-db` returns at least one user-created dashboard.
- The dashboard carries 4 or more non-row panels.
- The panel targets collectively reference `flask_http_request_total`, `model_inference_duration_seconds_bucket`, `prediction_accuracy`, and `data_drift_score`.
- The panels use at least 3 distinct visualization types (e.g. `timeseries`, `stat`, `bargauge`).
- The Evidently UI's project keeps accumulating scoring runs (pre-wired—nothing to change).

---

Solution

Login to Grafana UI

![screenshot](<../screenshots/Screenshot Day 71 Grafana UI login.png>)

Navigate to Dashboard page

![screenshot](<../screenshots/Screenshot Day 71 Dashboard page.png>)

Create new dashboard

![screenshot](<../screenshots/Screenshot Day 71 create new dashboard.png>)

Add new panel Request Rate to dashboard

![screenshot](<../screenshots/Screenshot Day 71 create request rate panel.png>)

Configure Request Rate panel using following query

```
rate(flask_http_request_total{version="v1", endpoint="/predict", method="POST"}[5m])
```

![screenshot](<../screenshots/Screenshot Day 71 config request rate panel.png>)

Add new panel p95 Inference Latency to dashboard

![screenshot](<../screenshots/Screenshot Day 71 create p95 panel.png>)

Configure p95 Inference Latency panel using following query

```
histogram_quantile(
  0.95,
  sum by (le) (
    rate(model_inference_duration_seconds_bucket[5m])
  )
)
```

![screenshot](<../screenshots/Screenshot Day 71 config p95 panel.png>)

Add new panel Prediction Accuracy to dashboard

![screenshot](<../screenshots/Screenshot Day 71 create prediction accuracy panel.png>)

Configure Prediction Accuracy panel as Stat using following query 

```
prediction_accuracy
```

![screenshot](<../screenshots/Screenshot Day 71 config prediction accuracy panel.png>)

Add new panel Data Drift Score (PSI) to dashboard

![screenshot](<../screenshots/Screenshot Day 71 create data drift panel.png>)

Configure Data Drift Score (PSI) panel as Gauge using following query 

```
data_drift_score
```

![screenshot](<../screenshots/Screenshot Day 71 config data drift panel.png>)

Final Dashboard

![screenshot](<../screenshots/Screenshot Day 71 final dashboard.png>)

---

### Verification

Confirm Dashboard exists 

```shell
curl -s -u admin:grafana2026 'http://localhost:3000/api/search?type=dash-db'
```

Output

```shell
[{"id":2822113451945984,"uid":"admhswc","orgId":1,"title":"Fraud-detection Model","uri":"db/fraud-detection-model","url":"/d/admhswc/fraud-detection-model","slug":"","type":"dash-db","tags":[],"isStarred":false,"sortMeta":0,"isDeleted":false}]
```

Confirm 4 panels

```shell
curl -s -u admin:grafana2026 'http://localhost:3000/api/dashboards/uid/admhswc'
```

Output

```shell
{"meta":{"type":"db","canSave":true,"canEdit":true,"canAdmin":true,"canStar":true,"canDelete":true,"slug":"fraud-detection-model","url":"/d/admhswc/fraud-detection-model","expires":"0001-01-01T00:00:00Z","created":"2026-10-27T09:18:54Z","updated":"2026-10-27T09:45:24Z","updatedBy":"admin","createdBy":"admin","version":7,"hasAcl":false,"isFolder":false,"apiVersion":"v0alpha1","folderId":0,"folderUid":"","folderTitle":"General","folderUrl":"","provisioned":false,"provisionedExternalId":"","annotationsPermissions":{"dashboard":{"canAdd":true,"canEdit":true,"canDelete":true}}},"dashboard":{"annotations":{"list":[{"builtIn":1,"datasource":{"type":"grafana","uid":"-- Grafana --"},"enable":true,"hide":true,"iconColor":"rgba(0, 211, 255, 1)","name":"Annotations \u0026 Alerts","type":"dashboard"}]},"editable":true,"fiscalYearStartMonth":0,"graphTooltip":0,"id":2822113451945984,"liveNow":false,"panels":[{"datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},"fieldConfig":{"defaults":{"color":{"mode":"palette-classic"},"custom":{"axisBorderShow":false,"axisCenteredZero":false,"axisColorMode":"text","axisLabel":"","axisPlacement":"auto","barAlignment":0,"barWidthFactor":0.6,"drawStyle":"line","fillOpacity":0,"gradientMode":"none","hideFrom":{"legend":false,"tooltip":false,"viz":false},"insertNulls":false,"lineInterpolation":"linear","lineWidth":1,"pointSize":5,"scaleDistribution":{"type":"linear"},"showPoints":"auto","showValues":false,"spanNulls":false,"stacking":{"group":"A","mode":"none"},"thresholdsStyle":{"mode":"off"}},"thresholds":{"mode":"absolute","steps":[{"color":"green","value":0},{"color":"red","value":80}]}}},"gridPos":{"h":8,"w":12,"x":0,"y":0},"id":1,"options":{"annotations":{"clustering":-1,"multiLane":false},"legend":{"calcs":[],"displayMode":"list","enableFacetedFilter":false,"overflow":"ellipsis","placement":"bottom","showLegend":true},"tooltip":{"hideZeros":false,"mode":"single","sort":"none"}},"pluginVersion":"13.1.0","targets":[{"datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},"editorMode":"code","expr":"rate(flask_http_request_total{version=\"v1\", endpoint=\"/predict\", method=\"POST\"}[5m])","legendFormat":"__auto","range":true,"refId":"A"}],"title":"Request Rate","type":"timeseries"},{"datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},"fieldConfig":{"defaults":{"color":{"mode":"palette-classic"},"custom":{"axisBorderShow":false,"axisCenteredZero":false,"axisColorMode":"text","axisLabel":"","axisPlacement":"auto","barAlignment":0,"barWidthFactor":0.6,"drawStyle":"line","fillOpacity":0,"gradientMode":"none","hideFrom":{"legend":false,"tooltip":false,"viz":false},"insertNulls":false,"lineInterpolation":"linear","lineWidth":1,"pointSize":5,"scaleDistribution":{"type":"linear"},"showPoints":"auto","showValues":false,"spanNulls":false,"stacking":{"group":"A","mode":"none"},"thresholdsStyle":{"mode":"off"}},"thresholds":{"mode":"absolute","steps":[{"color":"green","value":0},{"color":"red","value":80}]}}},"gridPos":{"h":8,"w":12,"x":12,"y":0},"id":2,"options":{"annotations":{"clustering":-1,"multiLane":false},"legend":{"calcs":[],"displayMode":"list","enableFacetedFilter":false,"overflow":"ellipsis","placement":"bottom","showLegend":true},"tooltip":{"hideZeros":false,"mode":"single","sort":"none"}},"pluginVersion":"13.1.0","targets":[{"datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},"editorMode":"code","expr":"histogram_quantile(\n  0.95,\n  sum by (le) (\n    rate(model_inference_duration_seconds_bucket[5m])\n  )\n)","legendFormat":"__auto","range":true,"refId":"A"}],"title":"p95 Inference Latency","type":"timeseries"},{"datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},"fieldConfig":{"defaults":{"color":{"mode":"thresholds"},"thresholds":{"mode":"absolute","steps":[{"color":"green","value":0},{"color":"red","value":80}]}}},"gridPos":{"h":8,"w":12,"x":0,"y":8},"id":3,"options":{"colorMode":"value","graphMode":"area","justifyMode":"auto","orientation":"auto","percentChangeColorMode":"standard","reduceOptions":{"calcs":["lastNotNull"],"fields":"","values":false},"showPercentChange":false,"textMode":"auto","wideLayout":true},"pluginVersion":"13.1.0","targets":[{"datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},"editorMode":"code","expr":"prediction_accuracy","legendFormat":"__auto","range":true,"refId":"A"}],"title":"Prediction Accuracy","type":"stat"},{"datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},"fieldConfig":{"defaults":{"color":{"mode":"continuous-GrYlRd"},"thresholds":{"mode":"percentage","steps":[{"color":"green","value":0},{"color":"orange","value":60},{"color":"red","value":80}]}}},"gridPos":{"h":8,"w":12,"x":12,"y":8},"id":4,"options":{"displayMode":"lcd","legend":{"calcs":[],"displayMode":"list","overflow":"ellipsis","placement":"bottom","showLegend":false},"maxVizHeight":300,"minVizHeight":16,"minVizWidth":8,"namePlacement":"auto","orientation":"horizontal","reduceOptions":{"calcs":["lastNotNull"],"fields":"","values":false},"showUnfilled":true,"sizing":"auto","valueMode":"text"},"pluginVersion":"13.1.0","targets":[{"datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},"editorMode":"code","expr":"data_drift_score","instant":false,"legendFormat":"__auto","range":true,"refId":"A"}],"title":"Data Drift Score (PSI)","type":"bargauge"}],"preload":false,"refresh":"","schemaVersion":42,"time":{"from":"now-1h","to":"now"},"timepicker":{"refresh_intervals":["5s","10s","30s","1m","5m","15m","30m","1h","2h","1d"]},"timezone":"browser","title":"Fraud-detection Model","uid":"admhswc","version":7}}
```

Confirm Evidently UI's project keeps accumulating scoring runs

![screenshot](<../screenshots/Screenshot Day 71 Evidently UI.png>)

