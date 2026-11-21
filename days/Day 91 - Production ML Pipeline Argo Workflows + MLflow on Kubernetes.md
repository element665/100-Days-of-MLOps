Prompt

The xFusionCorp Industries ML platform team is cutting the first production release of the fraud-detector pipeline. A `WorkflowTemplate` named `fraud-training-pipeline` trains a model and registers it in MLflow; a `CronWorkflow` named `fraud-retraining` re-runs the template every minute. Argo and an in-cluster MLflow are running, but the release is broken on three fronts. Your capstone task is to fix all three bugs entirely through the Argo UI and confirm that a new version of `fraud-detector` appears on the MLflow Models page.

  

Two surfaces are exposed: the **Argo UI** (port `5000`) — Workflows list, Workflow Templates, and Cron Workflows — and the **MLflow UI** (port `5001`), whose Models page is empty since no version of `fraud-detector` has been registered yet.

Three independent wiring issues sit between the run logs, the `fraud-training-pipeline` WorkflowTemplate spec, and the `fraud-retraining` CronWorkflow spec. They surface progressively: the first submission of the template is rejected outright with a parameter-resolution error (a bad output-parameter reference); once that is fixed a node fails at runtime, visible in its logs; and the Cron Workflows page reveals what `fraud-retraining` is failing to do over the last few minutes. Each fix is a single value change made through the Argo UI's YAML editors (the template's or the cron's **Edit** view).

With all three fixed, a fresh submission of `fraud-training-pipeline` should run green end-to-end, `fraud-retraining`should spawn a green child workflow within a minute, and the MLflow Models page should show one or more versions of `fraud-detector`.

The end state must include:

- A manual submission of the `fraud-training-pipeline`template runs end-to-end to `Succeeded` (`train` and `register` both green on the DAG).
- `GET /api/2.0/mlflow/registered-models/get?name=fraud-detector` returns at least one version (tests poll up to 300 s).
- The `fraud-retraining` CronWorkflow spawns at least one **child Workflow** that completes successfully — the Cron Workflows page shows it in the resource's Workflows panel (tests look for the owner label `workflows.argoproj.io/cron-workflow=fraud-retraining`).

> Production orchestration breaks across boundaries — a typo or a stale reference can survive a reviewer's read of any single resource. The capstone is reading them as symptoms on a running system, fixing them in place, and confirming the full pipe is back to passing.

---

Solution

Check Workflow Template `fraud-training-pipeline` Manifest

![screenshot](<../screenshots/Screenshot Day 91 Argo workflow template manifest.png>)

Error from Argo trying to submit template as workflow confirms `run_id` was incorrectly referenced as `runid` 

```shell
 {"code":3,"message":"templates.main.steps failed to resolve {{steps.train.outputs.parameters.runid}}"}: templates.main.steps failed to resolve {{steps.train.outputs.parameters.runid}}
```

{{steps.train.outputs.parameters.runid}} --> {{steps.train.outputs.parameters.run_id}}

Updated block in Workflow Template `fraud-training-pipeline` Manifest

```yaml
spec:
  templates:
    - name: main
      inputs: {}
      outputs: {}
      metadata: {}
      steps:
        - - name: train
            template: train
            arguments: {}
        - - name: register
            template: register
            arguments:
              parameters:
                - name: run_id
                  value: "{{steps.train.outputs.parameters.run_id}}"
```

Try submitting the Workflow Template manually to check success

![screenshot](<../screenshots/Screenshot Day 91 failed workflow run.png>)

Workflow failed; inspect workflow logs to diagnose issue.

```
  File "/usr/local/lib/python3.11/site-packages/urllib3/connection.py", line 246, in _new_conn
    raise NameResolutionError(self.host, self, e) from e
urllib3.exceptions.NameResolutionError: HTTPConnection(host='mlflow.default.svc.cluster.local', port=5000): Failed to resolve 'mlflow.default.svc.cluster.local' ([Errno -2] Name or service not known)
The above exception was the direct cause of the following exception:
```

Workflow log shows that MLflow service is being referenced on the `default` namespace in the cluster. Inspect the cluster with kubectl

Confirm the cluster's layout

Check what services are running in `default` namespace

```shell
kubectl get service
```

Output

```shell
NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   10m
```

Check what namespaces are being used

```shell
kubectl get namespaces
```

Output

```shell
NAME                 STATUS   AGE
argo                 Active   9m49s
default              Active   10m
kube-node-lease      Active   10m
kube-public          Active   10m
kube-system          Active   10m
local-path-storage   Active   10m
mlflow               Active   9m3s
```

Confirm MLflow is running in `mlflow` namespace

```shell
kubectl get service -n mlflow
```

Output

```shell
NAME     TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
mlflow   ClusterIP   10.96.37.117   <none>        5000/TCP   9m24s
```

This confirms the `MLFLOW_TRACKING_URI` is incorrect. 

Update both the `train` and `register` templates in the `fraud-training-pipeline` Workflow Template 

```yaml
        env:
          - name: MLFLOW_TRACKING_URI
            value: http://mlflow.mlflow.svc.cluster.local:5000
```

Submit a new workflow manually to check if all issues are resolved.

![screenshot](<../screenshots/Screenshot Day 91 successful workflow run.png>)

Workflow now completes successfully, but Cron Workflow is not triggering new child workflows

Inspect CronWorkflow Manifest

![screenshot](<../screenshots/Screenshot Day 91 cron workflow manifest.png>)

Cron workflow template ref incorrectly references `training-pipeline` instead of `fraud-training-pipeline`

Update Cron Workflow `fraud-retraining` Manifest

```yaml
  "spec": {
    "workflowSpec": {
      "arguments": {},
      "workflowTemplateRef": {
        "name": "fraud-training-pipeline"
      }
    },
    "concurrencyPolicy": "Forbid",
    "timezone": "Etc/UTC",
    "schedules": [
      "* * * * *"
    ]
  },
  "status": {
    "active": null,
    "lastScheduledTime": null,
    "conditions": null,
    "succeeded": 0,
    "failed": 0,
    "phase": ""
  }
```

Confirm Cron Workflow triggers child workflow after update

![screenshot](<../screenshots/Screenshot Day 91 child workflows.png>)

Confirm MLflow UI registered model with versions

![screenshot](<../screenshots/Screenshot Day 91 MLflow registered model.png>)

![screenshot](<../screenshots/Screenshot Day 91 MLflow model versions.png>)

---
### Verification

Confirm manual workflow succeeded 

```shell
curl -s http://localhost:5000/api/v1/workflows/argo/fraud-training-pipeline-22rdm |
jq '{
    name: .metadata.name,
    phase: .status.phase,
    nodes: [
        .status.nodes[] |
        select(.displayName == "train" or .displayName == "register") |
        {
            name: .displayName,
            phase: .phase
        }
    ]
}'
```

Output

```json
{
  "name": "fraud-training-pipeline-22rdm",
  "phase": "Succeeded",
  "nodes": [
    {
      "name": "train",
      "phase": "Succeeded"
    },
    {
      "name": "register",
      "phase": "Succeeded"
    }
  ]
}
```

Confirm MLflow contains at least one registered model version

```shell
curl -s "http://localhost:5001/api/2.0/mlflow/registered-models/get?name=fraud-detector" |
jq '{
    name: .registered_model.name,
    versions: [
        .registered_model.latest_versions[] |
        {
            version: .version,
            status: .status,
            run_id: .run_id
        }
    ]
}'
```

Output

```json
{
  "name": "fraud-detector",
  "versions": [
    {
      "version": "3",
      "status": "READY",
      "run_id": "3770f47fc6154de0902d64d92ae39e67"
    }
  ]
}
```

Confirm CronWorkflow spawns at least one child Workflow that completes successfully

```shell
curl -s http://localhost:5000/api/v1/workflows/argo |
jq '.items[] |
    select(
        .metadata.labels["workflows.argoproj.io/cron-workflow"]
        == "fraud-retraining"
    ) |
    {
        name: .metadata.name,
        phase: .status.phase,
        startedAt: .status.startedAt,
        finishedAt: .status.finishedAt,
        labels: .metadata.labels
    }'
```

Output

```json
{
  "name": "fraud-retraining-1795261200",
  "phase": "Running",
  "startedAt": "2026-11-21T11:40:00Z",
  "finishedAt": null,
  "labels": {
    "workflows.argoproj.io/completed": "false",
    "workflows.argoproj.io/cron-workflow": "fraud-retraining",
    "workflows.argoproj.io/phase": "Running"
  }
}
{
  "name": "fraud-retraining-1795261080",
  "phase": "Succeeded",
  "startedAt": "2026-11-21T11:38:00Z",
  "finishedAt": "2026-11-21T11:39:42Z",
  "labels": {
    "workflows.argoproj.io/completed": "true",
    "workflows.argoproj.io/cron-workflow": "fraud-retraining",
    "workflows.argoproj.io/phase": "Succeeded"
  }
}
{
  "name": "fraud-retraining-1795260960",
  "phase": "Succeeded",
  "startedAt": "2026-11-21T11:36:00Z",
  "finishedAt": "2026-11-21T11:37:42Z",
  "labels": {
    "workflows.argoproj.io/completed": "true",
    "workflows.argoproj.io/cron-workflow": "fraud-retraining",
    "workflows.argoproj.io/phase": "Succeeded"
  }
}
```
