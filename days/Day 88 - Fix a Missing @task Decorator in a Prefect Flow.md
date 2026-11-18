Prompt

The xFusionCorp Industries ML platform team is piloting Prefect 3.x as a second orchestrator alongside Argo Workflows. A teammate wired up a `fraud-pipeline` deployment with three steps—`prep`, `train`, `evaluate`—but on every run the Prefect Flow Run graph only shows two tracked nodes (`prep` and `train`); `evaluate` is missing. Your task is to fix the flow source, redeploy, trigger a new run from the Deployments page, and confirm the 3-node DAG.

  

The **Prefect UI** button at the top of the lab opens the UI on port `5000`. Its **Deployments** page lists `fraud-pipeline`. Trigger a **Quick Run** and open the resulting Flow Run: its DAG renders only two nodes, and comparing that graph against the flow source is where the gap shows up.

The flow source is at `/root/code/prefect/fraud_pipeline.py`; the `evaluate` function runs as part of the flow but does not surface in the run graph the way the other two functions do. A shipped Makefile in that directory wraps the kill + restart cycle needed for the serve loop to pick up the new source (`/var/log/prefect-serve.log` confirms the new process is up).

After redeploying and triggering a fresh **Quick Run**, the Flow Run's DAG should render three nodes — `prep → train → evaluate` — each reaching Completed.

The end state must include:

- Prefect's `/api/deployments/name/fraud-pipeline/fraud-pipeline` returns the deployment.
- At least one **Completed** flow run under that deployment has three task runs whose names are exactly `prep`, `train`, and `evaluate` — Prefect's run graph now records `evaluate` alongside the other two.

> Prefect's flow-run graph is built from the task-run records its orchestrator emits during execution. A function that runs as part of the flow but is not registered as a task disappears from the run graph entirely — it executes, but the orchestrator has no record of it.

---

Solution

/root/code/prefect/fraud_pipeline.py (Original)

```python
"""Prefect 3.x flow for the fraud-detection pipeline.

Structure: prep -> train -> evaluate. Each step is a `@task`-decorated
function -- or should be. Inspect the evaluate node on the Prefect UI's
Flow Run graph to see whether it is being tracked.
"""
from __future__ import annotations

from prefect import flow, task


@task(name="prep")
def prep() -> dict:
    print("[prep] preparing training data")
    return {"rows": 100, "path": "/tmp/train.csv"}


@task(name="train")
def train(data: dict) -> str:
    print(f"[train] fitting model on {data['rows']} rows from {data['path']}")
    return "model-v1"


def evaluate(model: str) -> float:
    print(f"[evaluate] scoring model {model}")
    return 0.75


@flow(name="fraud-pipeline")
def fraud_pipeline() -> float:
    data = prep()
    model = train(data)
    score = evaluate(model)
    print(f"[flow] final score={score}")
    return score


if __name__ == "__main__":
    # `.serve()` registers a deployment named `fraud-pipeline` and
    # blocks as a worker loop, picking up Quick Run triggers from the
    # Prefect UI.
    fraud_pipeline.serve(name="fraud-pipeline", tags=["lab"])
```

Open Prefect UI

![screenshot](<../screenshots/Screenshot Day 88 Prefect UI.png>)

Select 'Deployments' from left menu

![screenshot](<../screenshots/Screenshot Day 88 select Deployments.png>)

Select the three vertical dots on the right side of the 'fraud-pipeline' Deployment and select 'Quick Run' from the drop-down menu

![screenshot](<../screenshots/Screenshot Day 88 select quick run.png>)

View 'Quick Run' details

![screenshot](<../screenshots/Screenshot Day 88 quick run 1.png>)

The run shows only 'prep' and 'train' tasks have completed; 'evaluate' is missing

Add '@task' -decorated function to 'evaluate' block

```python
@task(name="evaluate")
def evaluate(model: str) -> float:
    print(f"[evaluate] scoring model {model}")
    return 0.75
```

/root/code/prefect/fraud_pipeline.py (Updated)

```python
"""Prefect 3.x flow for the fraud-detection pipeline.

Structure: prep -> train -> evaluate. Each step is a `@task`-decorated
function -- or should be. Inspect the evaluate node on the Prefect UI's
Flow Run graph to see whether it is being tracked.
"""
from __future__ import annotations

from prefect import flow, task


@task(name="prep")
def prep() -> dict:
    print("[prep] preparing training data")
    return {"rows": 100, "path": "/tmp/train.csv"}


@task(name="train")
def train(data: dict) -> str:
    print(f"[train] fitting model on {data['rows']} rows from {data['path']}")
    return "model-v1"


@task(name="evaluate")
def evaluate(model: str) -> float:
    print(f"[evaluate] scoring model {model}")
    return 0.75


@flow(name="fraud-pipeline")
def fraud_pipeline() -> float:
    data = prep()
    model = train(data)
    score = evaluate(model)
    print(f"[flow] final score={score}")
    return score


if __name__ == "__main__":
    # `.serve()` registers a deployment named `fraud-pipeline` and
    # blocks as a worker loop, picking up Quick Run triggers from the
    # Prefect UI.
    fraud_pipeline.serve(name="fraud-pipeline", tags=["lab"])
```

Run Makefile to redeploy

```shell
cd /root/code/prefect
make redeploy
```

Output

```shell
Redeployed fraud-pipeline. Check /var/log/prefect-serve.log
```

Trigger new 'Quick Run' after redeploying

![screenshot](<../screenshots/Screenshot Day 88 select quick run.png>)

New run shows all three nodes 'prep' → 'train' → 'evaluate'

![screenshot](<../screenshots/Screenshot Day 88 all three nodes.png>)

---

Confirm API returns deployment

```shell
curl -s http://localhost:5000/api/deployments/name/fraud-pipeline/fraud-pipeline | jq '{"Name": .name, "Status": .status}'
```

Output

```json
{
  "Name": "fraud-pipeline",
  "Status": "READY"
}
```

Capture latest flow run id

```shell
flow_run_id=$(curl -s -X POST \
  'http://localhost:5000/api/flow_runs/filter' \
  -H 'Content-Type: application/json' \
  -d '{
    "sort": "START_TIME_DESC",
    "limit": 1,
    "offset": 0
  }' | jq -r '.[0].id')
```

Confirm at least one Completed flow run under deployment

```shell
curl -s "http://localhost:5000/api/flow_runs/$flow_run_id" | jq '.state_name'
```

Output

```json
"Completed"
```

Confirm task run names are `prep`, `train`, and `evaluate`

```shell
curl -s -X POST \
  'http://localhost:5000/api/task_runs/filter' \
  -H 'Content-Type: application/json' \
  -d "{
    \"task_runs\": {
      \"flow_run_id\": {
        \"any_\": [\"$flow_run_id\"]
      }
    }
  }" |
  jq '[.[].name] | sort'
```

Output

```json
[
  "evaluate-1ea",
  "prep-0a5",
  "train-c21"
]
```
