Prompt

The xFusionCorp Industries ML platform team requires the `fraud-detector` model to undergo retraining on a fixed schedule without manual intervention. A CronWorkflow scaffold is available at `/root/code/argo/fraud-retraining.yaml`, but it is incomplete; it currently lacks a `schedules` cron expression and the retraining step is only a placeholder. Your objective is to complete the CronWorkflow by adding the appropriate schedule and defining the retraining step. Once completed, apply the CronWorkflow to the `argo` namespace and verify in the Argo UI that it activates and initiates retraining runs as scheduled.

  

The scaffold is at `/root/code/argo/fraud-retraining.yaml`. It is NOT applied yet — the Argo UI's **Cron Workflows** page (port `5000`) stays empty until the CronWorkflow is applied to the `argo` namespace.

Two `TODO`-marked pieces are missing from the YAML:

- **TODO 1 — schedule:** the `schedules:` list with its cron expression is absent, so the cron has no cadence to fire on. It needs to fire frequently enough that a run appears within the grading window (a minute or so).
- **TODO 2 — retraining step:** the step is only a stub. It should run a stand-in retraining command that exits 0 — an `echo` is enough, since this section teaches orchestration, not model quality.

With the CronWorkflow applied, the **Cron Workflows** page should show `fraud-retraining` active (no Suspended badge) with a `nextScheduledTime` ≤ 60 s out, and within one schedule tick a child Workflow should appear under it and run to **Succeeded**.

The end state must include:

- `GET /api/v1/cron-workflows/argo/fraud-retraining`returns the cron with a non-empty `schedules` and `spec.suspend` not `true`.
- At least one Workflow labelled `workflows.argoproj.io/cron-workflow=fraud-retraining` (the owner-label Argo adds to every cron-spawned run) reaches `Succeeded`. Tests poll up to 240 s.

> A CronWorkflow is Argo's scheduled-run primitive: `schedules` is the cron cadence and `workflowSpec` is the Workflow it fires each tick. This is how retraining runs on autopilot—no human clicking Submit—with `concurrencyPolicy: Forbid` ensuring a slow run never overlaps the next tick.

---

Solution

/root/code/argo/fraud-retraining.yaml (Original)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: fraud-retraining
  namespace: argo
spec:
  # TODO 1: Schedule the retraining run. Add a `schedules:` list with a
  # cron expression that fires every minute ("* * * * *") so
  # fraud-detector retrains on a fixed cadence.
  timezone: "Etc/UTC"
  concurrencyPolicy: Forbid
  startingDeadlineSeconds: 60
  successfulJobsHistoryLimit: 4
  failedJobsHistoryLimit: 2
  workflowSpec:
    entrypoint: main
    templates:
      - name: main
        container:
          image: alpine:3.19
          command: [sh, -c]
          args:
            # TODO 2: Author the retraining step this cron runs each
            # tick. Echo a marker containing "retrain" and a UTC
            # timestamp, then exit 0.
            - |
              echo "TODO 2: author the retraining step"
              exit 1

```

/root/code/argo/fraud-retraining.yaml (Updated)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: fraud-retraining
  namespace: argo
spec:
  schedules:
    - "* * * * *"
  timezone: "Etc/UTC"
  concurrencyPolicy: Forbid
  startingDeadlineSeconds: 60
  successfulJobsHistoryLimit: 4
  failedJobsHistoryLimit: 2
  workflowSpec:
    entrypoint: main
    templates:
      - name: main
        container:
          image: alpine:3.19
          command: [sh, -c]
          args:
            - |
              echo "retrain $(date -u +%FT%TZ)"
              exit 0
```

Apply updated scaffold

```shell
kubectl apply -f /root/code/argo/fraud-retraining.yaml -n argo
```

---
### Verification

Confirm API returns the cron with a non-empty `schedules` and `spec.suspend` not `true`

```shell
curl -s http://localhost:5000/api/v1/cron-workflows/argo/fraud-retraining | jq '.spec | {
  "schedules": .schedules,
  "suspend": (.suspend // false)
}'
```

Output

```json
{
  "schedules": [
    "* * * * *"
  ],
  "suspend": false
}
```

Confirm at least one Workflow labelled workflows.argoproj.io/cron-workflow=fraud-retraining (the owner-label Argo adds to every cron-spawned run) reaches Succeeded

```shell
curl -s http://localhost:5000/api/v1/workflows/argo | jq '.items[] | select(.metadata.labels["workflows.argoproj.io/cron-workflow"] == "fraud-retraining") | {name: .metadata.name, labels: .metadata.labels, phase: .status.phase}'
```

Output

```json
{
  "name": "fraud-retraining-1795171620",
  "labels": {
    "workflows.argoproj.io/completed": "true",
    "workflows.argoproj.io/cron-workflow": "fraud-retraining",
    "workflows.argoproj.io/phase": "Succeeded"
  },
  "phase": "Succeeded"
}
{
  "name": "fraud-retraining-1795171560",
  "labels": {
    "workflows.argoproj.io/completed": "true",
    "workflows.argoproj.io/cron-workflow": "fraud-retraining",
    "workflows.argoproj.io/phase": "Succeeded"
  },
  "phase": "Succeeded"
}
```

Argo UI Workflows

![screenshot](<../screenshots/Screenshot Day 90 Argo UI Workflows.png>)

Argo UI Cron Workflows

![screenshot](<../screenshots/Screenshot Day 90 Argo UI Cron Workflows.png>)