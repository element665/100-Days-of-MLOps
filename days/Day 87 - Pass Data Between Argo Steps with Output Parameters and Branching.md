Prompt

The xFusionCorp Industries ML platform team requires a reusable training pipeline that promotes a model to the registry only when it passes a configurable quality gate. This pipeline should utilize the same WorkflowTemplate with differing `min_score` values for each run. Currently, a `train-and-maybe-register`WorkflowTemplate is available on disk; however, it is not yet functional. The `evaluate` step computes a synthetic score of `0.75` but does not publish it, and the `register` step lacks a quality gate, causing it to execute unconditionally. Your task is to complete the template by publishing the score as an **output parameter** and implementing a **`when:`** expression to gate the `register` step, ensuring that it compares the score to `min_score`. Once you have applied these changes, submit the workflow twice from the Argo UI to demonstrate the functionality of the gate: first with a threshold that prevents `register` from executing, and then with a threshold that allows it to execute.

  

The scaffolded template is at `/root/code/argo/train-and-maybe-register.yaml`. It is NOT applied yet — the Argo UI's **Workflow Templates** list (port `5000`) stays empty until the template is applied to the `argo` namespace as a cluster resource.

Two `TODO`-marked pieces are missing from the YAML:

- **TODO 1 — `evaluate` template:** the script writes a synthetic score to `/tmp/score.txt`, but the template does not yet expose that value to the rest of the workflow as an output parameter.
- **TODO 2 — `register` step in `main`:** the register step currently runs unconditionally, rather than only when the score clears the `min_score` threshold.

With the template applied and appearing in the UI, submitting it twice demonstrates the gate: a run with `min_score` above the evaluate score (e.g. `0.99`) reaches `Succeeded` with the `register` node **Skipped** (the `when:` evaluated false), while a run with `min_score` below the score (e.g. `0.5`) has `register`**Succeeded**.

The end state must include:

- `GET /api/v1/workflow-templates/argo/train-and-maybe-register` returns the template, whose `evaluate`template emits a `score` output parameter and whose `register` step carries a `when:` gate referencing both the evaluate score and `min_score`.
- At least two workflows exist whose `spec.workflowTemplateRef.name == train-and-maybe-register`.
- One with `min_score > 0.75` has its `register` node `Skipped`/`Omitted`; another with `min_score <= 0.75`has `register` `Succeeded`.

> This is the canonical CI/CT gate: every commit runs train + evaluate, but only commits that clear the configurable threshold promote the model. Passing the score between steps as an output parameter—and gating promotion with `when:`—is what lets one template serve dev (`min_score=0.5`), staging (`0.75`), and prod (`0.9`) without a single rewrite.

---

Solution

train-and-maybe-register.yaml (Original)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: train-and-maybe-register
  namespace: argo
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: min_score
        value: "0.80"
  templates:
    - name: main
      steps:
        - - name: train
            template: train
        - - name: evaluate
            template: evaluate
        - - name: register
            template: register
            # TODO 2: Gate this step so register runs ONLY when the
            # evaluate score clears the min_score threshold. Add a
            # `when:` expression comparing the `score` output parameter
            # emitted by the evaluate step (TODO 1) against
            # workflow.parameters.min_score. Without it, register runs
            # unconditionally regardless of min_score.
    - name: train
      container:
        image: alpine:3.19
        command: [sh, -c]
        args: ["echo '[train] fitting model' && sleep 2"]
    - name: evaluate
      script:
        image: alpine:3.19
        command: [sh]
        source: |
          # Deterministic score -- MLOps-not-ML. Teaching point is the
          # parameter plumbing, not the score itself.
          echo "0.75" > /tmp/score.txt
          echo "[evaluate] score=0.75"
      # TODO 1: Publish the score this step wrote to /tmp/score.txt as an
      # output parameter named `score`, so the register step's `when:`
      # (TODO 2) can read it as steps.evaluate.outputs.parameters.score.
      # Add an `outputs.parameters` entry with `valueFrom.path`.
    - name: register
      container:
        image: alpine:3.19
        command: [sh, -c]
        args: ["echo '[register] promoting model to registry'"]

```

train-and-maybe-register.yaml (Updated)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: train-and-maybe-register
  namespace: argo
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: min_score
        value: "0.80"
  templates:
    - name: main
      steps:
        - - name: train
            template: train
        - - name: evaluate
            template: evaluate
        - - name: register
            template: register
            when: "{{=asFloat(steps.evaluate.outputs.parameters.score) > asFloat(workflow.parameters.min_score)}}"
    - name: train
      container:
        image: alpine:3.19
        command: [sh, -c]
        args: ["echo '[train] fitting model' && sleep 2"]
    - name: evaluate
      script:
        image: alpine:3.19
        command: [sh]
        source: |
          # Deterministic score -- MLOps-not-ML. Teaching point is the
          # parameter plumbing, not the score itself.
          echo "0.75" > /tmp/score.txt
          echo "[evaluate] score=0.75"
      outputs:
        parameters:
          - name: score
            valueFrom:
              path: /tmp/score.txt 
    - name: register
      container:
        image: alpine:3.19
        command: [sh, -c]
        args: ["echo '[register] promoting model to registry'"]
```

Apply the template

```shell
kubectl apply -n argo -f /root/code/argo/train-and-maybe-register.yaml
```

Output

```shell
workflowtemplate.argoproj.io/train-and-maybe-register created
```

Open Argo UI

![screenshot](<../screenshots/Screenshot Day 87 Argo UI.png>)

Select Workflow Templates from left menu

![screenshot](<../screenshots/Screenshot Day 87 workflow templates.png>)

Select the now available template 'train-and-maybe-register'

![screenshot](<../screenshots/Screenshot Day 87 select template.png>)

Click the '+SUBMIT' button on the top left

![screenshot](<../screenshots/Screenshot Day 87 +submit.png>)

Use the 'Parameters min_score' of '0.99' as requested

![screenshot](<../screenshots/Screenshot Day 87 min_score 99.png>)

Workflow has completed and skipped 'register' step as expected

![screenshot](<../screenshots/Screenshot Day 87 skipped register.png>)

Use the template to submit a new workflow with '0.50' for 'Parameters min_score'

![screenshot](<../screenshots/Screenshot Day 87 min_score 50.png>)

Workflow has completed successfully and 'register' step ran

![screenshot](<../screenshots/Screenshot Day 87 register succeeded.png>)

---
### Verification

The end state must include:

- `GET /api/v1/workflow-templates/argo/train-and-maybe-register` returns the template, whose `evaluate`template emits a `score` output parameter and whose `register` step carries a `when:` gate referencing both the evaluate score and `min_score`.
- At least two workflows exist whose `spec.workflowTemplateRef.name == train-and-maybe-register`.
- One with `min_score > 0.75` has its `register` node `Skipped`/`Omitted`; another with `min_score <= 0.75`has `register` `Succeeded`.

Confirm 'evaluate' template emits a 'score' output parameter
 
```shell
curl -s http://localhost:5000/api/v1/workflow-templates/argo/train-and-maybe-register | jq '.spec.templates[2] | {"name": .name}, {"output parameters": .outputs.parameters[]}'
```

Output

```JSON
{
  "name": "evaluate"
}
{
  "output parameters": {
    "name": "score",
    "valueFrom": {
      "path": "/tmp/score.txt"
    }
  }
}
```

Confirm 'register' step carries a 'when:' gate

```shell
curl -s http://localhost:5000/api/v1/workflow-templates/argo/train-and-maybe-register | jq '.spec.templates[0].steps[2]'
```

Output

```shell
[
  {
    "name": "register",
    "template": "register",
    "arguments": {},
    "when": "{{=asFloat(steps.evaluate.outputs.parameters.score) > asFloat(workflow.parameters.min_score)}}"
  }
]
```

Confirm 1st workflow uses train-and-maybe-register

```shell
curl -s http://localhost:5000/api/v1/workflows/argo | jq '.items[0].metadata | {"workflow 1": .name, "workflowTemplate": .labels."workflows.argoproj.io/workflow-template"}'
```

Output

```shell
{
  "workflow 1": "train-and-maybe-register-khjwl",
  "workflowTemplate": "train-and-maybe-register"
}
```

Confirm 2nd workflow uses train-and-maybe-register

```shell
curl -s http://localhost:5000/api/v1/workflows/argo | jq '.items[1].metadata | {"workflow 2": .name, "workflowTemplate": .labels."workflows.argoproj.io/workflow-template"}'
```

Output

```shell
{
  "workflow 2": "train-and-maybe-register-kdpnw",
  "workflowTemplate": "train-and-maybe-register"
}
```

Confirm scores used in workflows

```shell
curl -s http://localhost:5000/api/v1/workflows/argo | jq '.items[].spec'
```

Output

```shell
{
  "entrypoint": "main",
  "arguments": {
    "parameters": [
      {
        "name": "min_score",
        "value": "0.50"
      }
    ]
  },
  "workflowTemplateRef": {
    "name": "train-and-maybe-register"
  }
}
{
  "entrypoint": "main",
  "arguments": {
    "parameters": [
      {
        "name": "min_score",
        "value": "0.99"
      }
    ]
  },
  "workflowTemplateRef": {
    "name": "train-and-maybe-register"
  }
}
```

Confirm a 'skipped' and 'succeeded' register phase

```shell
curl -s http://localhost:5000/api/v1/workflows/argo \
  | python3 -c "
import json, sys
body = json.load(sys.stdin)
for w in body.get('items', []):
    spec = w.get('spec', {})
    ref = spec.get('workflowTemplateRef', {})
    if ref.get('name') != 'train-and-maybe-register':
        continue
    args = spec.get('arguments', {}).get('parameters', [])
    ms = next((p['value'] for p in args if p['name'] == 'min_score'), '?')
    # Find the register node phase.
    reg_phase = '?'
    for n in (w.get('status') or {}).get('nodes', {}).values():
        nm = n.get('displayName') or n.get('name') or ''
        if nm.endswith('.register') or nm == 'register':
            reg_phase = n.get('phase'); break
    print(f\"min_score={ms:4s}  register.phase={reg_phase}\")
"
```

Output

```shell
min_score=0.50  register.phase=Succeeded
min_score=0.99  register.phase=Skipped
```


