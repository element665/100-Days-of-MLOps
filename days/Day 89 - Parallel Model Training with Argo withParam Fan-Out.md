Prompt

The xFusionCorp Industries ML platform team aims to train multiple model variants simultaneously and select the best performing model. The `train-parallel-variants` WorkflowTemplate has been created but is incomplete: the `train-variant` and `pick-best` step templates are defined, yet the `main` template lacks its `withParam` fan-out and the `pick-best` fan-in step. Your task is to complete both components: fan out the `train-variant` step over the `estimators_list`parameter using `withParam`, and incorporate the `pick-best` reducer as a second step. After applying the template, submit it twice through the Argo UI: first, with a deliberately faulty entry (ensuring one branch fails), and then with a valid list (confirming both the fan-out and reducer complete successfully).

  

The scaffolded template is at `/root/code/argo/train-parallel-variants.yaml`. It is NOT applied yet — the Argo UI's **Workflow Templates** list (port `5000`) stays empty until the template is applied to the `argo` namespace. The `train-variant` template validates its `n_estimators` input as a positive integer and exits 1 otherwise.

Two `TODO`-marked pieces are missing from the `main`template:

- **TODO 1 — fan-out:** the `train` step runs only once instead of fanning out over the `estimators_list`parameter, so it never becomes the N parallel pods the sweep needs.
- **TODO 2 — fan-in:** the reducer step group that runs after the parallel branches finish is absent, so nothing picks the best result once the variants complete.

With the template applied and appearing in the UI, submitting it twice demonstrates the fan-out and its failure mode: an `estimators_list` with one obviously-bad entry alongside valid positive integers red-lights the bad branch while the others go green, never reaches `pick-best`, and finishes `Failed`; a clean list of three valid positive integers turns every `train-variant`branch green, runs `pick-best`, and finishes `Succeeded`.

The end state must include:

- `GET /api/v1/workflow-templates/argo/train-parallel-variants` returns the template, whose `main`step fans out over `estimators_list` with `withParam`and includes a `pick-best` fan-in step.
- At least two workflows exist with `spec.workflowTemplateRef.name == train-parallel-variants`.
- The most recent workflow's `status.phase == Succeeded`, with ≥3 `train-variant` Pod nodes all `Succeeded` plus one `pick-best` node Succeeded.

> `withParam` is Argo's fan-out primitive—one step definition, N parallel pods, one template per input value. Because every item runs independently, one bad value does not stop the others; it only blocks the fan-in reducer (`pick-best`) from receiving a complete set. That isolation is both the pattern's value (a 99-of-100 sweep still gives you 99 models) and its failure mode (one bad row in the input list red-lights the release).

---

Solution

train-parallel-variants.yaml (Original)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: train-parallel-variants
  namespace: argo
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: estimators_list
        value: '["10","50","100"]'
  templates:
    - name: main
      steps:
        # TODO 1: Fan out `train-variant` over the estimators_list
        # parameter. On this step add `withParam:` referencing
        # workflow.parameters.estimators_list, and pass each list item to
        # the template as its n_estimators input via arguments.parameters
        # (value "{{item}}"). Without withParam this runs a single
        # train-variant with no input and fails the required-parameter
        # check.
        - - name: train
            template: train-variant
        # TODO 2: Add the fan-in reducer as a SECOND step group so it runs
        # after the parallel fan-out completes -- a step named `pick-best`
        # that calls the `pick-best` template below.
    - name: train-variant
      inputs:
        parameters:
          - name: n_estimators
      script:
        image: alpine:3.19
        command: [sh]
        source: |
          N='{{inputs.parameters.n_estimators}}'
          case "$N" in
            ''|*[!0-9]*)
              echo "[train] ERROR: n_estimators must be a positive integer, got: $N"
              exit 1
              ;;
          esac
          echo "[train] fitting with n_estimators=$N"
          sleep 2
          echo "model-n$N"
    - name: pick-best
      container:
        image: alpine:3.19
        command: [sh, -c]
        args: ["echo '[pick_best] selected: model-n100'"]

```

Modify the `main` template to complete both TODO sections

```yaml
    - name: main
      steps:
        - - name: train
            template: train-variant
            arguments:
              parameters:
              - name: n_estimators
                value: "{{item}}"
            withParam: "{{workflow.parameters.estimators_list}}"
        - - name: pick-best
            template: pick-best
```

train-parallel-variants.yaml (Updated)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: train-parallel-variants
  namespace: argo
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: estimators_list
        value: '["10","50","100"]'
  templates:
    - name: main
      steps:
        - - name: train
            template: train-variant
            arguments:
              parameters:
              - name: n_estimators
                value: "{{item}}"
            withParam: "{{workflow.parameters.estimators_list}}"
        - - name: pick-best
            template: pick-best
    - name: train-variant
      inputs:
        parameters:
          - name: n_estimators
      script:
        image: alpine:3.19
        command: [sh]
        source: |
          N='{{inputs.parameters.n_estimators}}'
          case "$N" in
            ''|*[!0-9]*)
              echo "[train] ERROR: n_estimators must be a positive integer, got: $N"
              exit 1
              ;;
          esac
          echo "[train] fitting with n_estimators=$N"
          sleep 2
          echo "model-n$N"
    - name: pick-best
      container:
        image: alpine:3.19
        command: [sh, -c]
        args: ["echo '[pick_best] selected: model-n100'"]
```

Apply updated workflow template

```shell
kubectl apply -f /root/code/argo/train-parallel-variants.yaml -n argo
```

Confirm in Workflow Templates that `train-parallel-variants` now exists

```shell
curl -s http://localhost:5000/api/v1/workflow-templates/argo/train-parallel-variants | jq '.metadata.name'
```

Output

```json
"train-parallel-variants"
```

Open Argo UI

![screenshot](<../screenshots/Screenshot Day 89 Argo UI.png>)

Navigate to Workflow Templates

![screenshot](<../screenshots/Screenshot Day 89 navigate wf templates.png>)

Open `train-parallel-variants`

![screenshot](<../screenshots/Screenshot Day 89 open template.png>)

Click `+ SUBMIT`

![screenshot](<../screenshots/Screenshot Day 89 click submit.png>)

Override `estimators_list` with the values below and submit workflow

```json
["10","50","invalid"]
```

![screenshot](<../screenshots/Screenshot Day 89 override values.png>)

Completed workflow details

![screenshot](<../screenshots/Screenshot Day 89 wf details 1.png>)

Submit new workflow with the default `estimators_list` values and submit workflow

![screenshot](<../screenshots/Screenshot Day 89 default values.png>)

Completed workflow details for second run

![screenshot](<../screenshots/Screenshot Day 89 wf details 2.png>)

---
### Verification

Confirm API returns `main` step fans out over `estimators_list` with `withParam` and includes a `pick-best` fan-in step.

```shell
curl -s http://localhost:5000/api/v1/workflow-templates/argo/train-parallel-variants | jq '
.spec.templates[0] |
{
  name: .name,
  fan_out: .steps[0],
  fan_in: .steps[1]
}'
```

Output

```json
{
  "name": "main",
  "fan_out": [
    {
      "name": "train",
      "template": "train-variant",
      "arguments": {
        "parameters": [
          {
            "name": "n_estimators",
            "value": "{{item}}"
          }
        ]
      },
      "withParam": "{{workflow.parameters.estimators_list}}"
    }
  ],
  "fan_in": [
    {
      "name": "pick-best",
      "template": "pick-best",
      "arguments": {}
    }
  ]
}
```

Confirm two workflows exist with `spec.workflowTemplateRef.name == train-parallel-variants`

```shell
curl -s http://localhost:5000/api/v1/workflows/argo | jq -r '
.items[]
| select(.spec.workflowTemplateRef.name == "train-parallel-variants")
| [.metadata.name, .status.phase, .metadata.creationTimestamp]
| @tsv'
```

Output

```json
train-parallel-variants-tplfg   Succeeded       2026-11-19T17:17:35Z
train-parallel-variants-vjdxp   Failed  2026-11-19T17:15:53Z
```

Confirm most recent workflow's `status.phase == Succeeded`, with ≥3 `train-variant` Pod nodes all `Succeeded` plus one `pick-best` node Succeeded.

```shell
curl -s http://localhost:5000/api/v1/workflows/argo | jq '
(.items | sort_by(.metadata.creationTimestamp) | last) as $wf |
($wf.status.nodes // {} | [.[]]) as $nodes |
{
  workflow: $wf.metadata.name,
  phase: $wf.status.phase,
  train_variant_pods: [
    $nodes[]
    | select(.templateName == "train-variant" and .type == "Pod")
    | {name, phase}
  ],
  train_variant_succeeded_count: [
    $nodes[]
    | select(.templateName == "train-variant" and .type == "Pod" and .phase == "Succeeded")
  ] | length,
  pick_best: [
    $nodes[]
    | select(.templateName == "pick-best")
    | {name, phase}
  ]
}'
```

Output

```json
{
  "workflow": "train-parallel-variants-tplfg",
  "phase": "Succeeded",
  "train_variant_pods": [
    {
      "name": "train-parallel-variants-tplfg[0].train(0:10)",
      "phase": "Succeeded"
    },
    {
      "name": "train-parallel-variants-tplfg[0].train(1:50)",
      "phase": "Succeeded"
    },
    {
      "name": "train-parallel-variants-tplfg[0].train(2:100)",
      "phase": "Succeeded"
    }
  ],
  "train_variant_succeeded_count": 3,
  "pick_best": [
    {
      "name": "train-parallel-variants-tplfg[1].pick-best",
      "phase": "Succeeded"
    }
  ]
}
```
