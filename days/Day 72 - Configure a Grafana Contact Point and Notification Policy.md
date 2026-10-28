Prompt

The xFusionCorp Industries ML platform team requires that high-severity model alerts trigger notifications to the on-call channel via webhook. Currently, the existing alert rules are effective only if an individual is paged when alerts are activated. The monitoring stack is operational, and an in-stack `webhook-sink` service (container `webhook-sink`) is available at `http://webhook-sink:5000/hook`. Additionally, Grafana has the Prometheus datasource already configured. Your objective is to set up Grafana alerting so that any alert with the label `severity=high` is directed to the specified webhook endpoint.

  

The Grafana UI is running on port `3000`. The **Grafana** button opens the login page. Admin credentials: `admin` / `grafana2026`. The webhook sink is reachable from Grafana at `http://webhook-sink:5000/hook`.

The end state must include:

- `GET /api/v1/provisioning/contact-points` returns at least one contact point of type `webhook` whose `settings.url` references `webhook-sink`.
- `GET /api/v1/provisioning/policies` returns a notification-policy tree containing a route whose `receiver` matches that contact point and whose matchers include `severity = high`.

> Contact points answer the question 'where does a notification go?'—an endpoint (webhook, email, Slack). Notification policies answer 'which alerts go to which contact point?'—by label-matching the alert. Both pieces must be in place before any alert rule actually pages a human.

---

### Solution

Login to Grafana UI

![screenshot](<../screenshots/Screenshot Day 72 Grafana UI login.png>)

Navigate to the Alerting page and select 'Manage contact points'

![screenshot](<../screenshots/Screenshot Day 72 Grafana alerting page.png>)

Create 'New contact point'

![screenshot](<../screenshots/Screenshot Day 72 Grafana new contact point.png>)

Configure and save contact point

![screenshot](<../screenshots/Screenshot Day 72 Grafana config contact point.png>)

Contact point is now saved but shows 'Unused'

![screenshot](<../screenshots/Screenshot Day 72 Grafana saved contact point.png>)

Navigate to 'Notification policies' page and 'Add route' to Default policy

![screenshot](<../screenshots/Screenshot Day 72 Grafana notification policies.png>)

Configure new route

![screenshot](<../screenshots/Screenshot Day 72 Grafana add route.png>)

Save new route

![screenshot](<../screenshots/Screenshot Day 72 Grafana notification policy saved.png>)

Contact point now shows that it is used by a notification policy

![screenshot](<../screenshots/Screenshot Day 72 Grafana contact point used.png>)

---
### Verification

Confirm at least one contact point exists

```shell
curl -s -u admin:grafana2026 'http://localhost:3000/api/v1/provisioning/contact-points'
```

Output

```shell
[{"uid":"fg2kw8rf12qkgd","name":"high-severity-webhook","type":"webhook","settings":{"url":"http://webhook-sink:5000/hook"},"disableResolveMessage":false}]
```

Confirm a notification policy matches the contact point

```shell
curl -s -u admin:grafana2026 'http://localhost:3000/api/v1/provisioning/policies'
```

Output

```shell
{"receiver":"empty","group_by":["grafana_folder","alertname"],"routes":[{"receiver":"high-severity-webhook","object_matchers":[["severity","=","high"]]}]}
```

