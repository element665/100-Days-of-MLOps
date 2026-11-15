Prompt

The xFusionCorp Industries ML platform team has established a new Kubernetes cluster for pipeline orchestration. Argo Workflows v4.0.4 is currently operational in the `argo` namespace, with both the `workflow-controller` and `argo-server` Deployments marked as Available. Additionally, the Argo web UI is accessible via port-forwarding in the lab. Your task is to create your first Argo `Workflow` and submit it using the Argo UI's **+ Submit New Workflow** form. This should be a single-step container that simulates a training step and achieves a status of `Succeeded` in the Workflows list.

  

The **Argo UI** button at the top of the lab opens the Workflows page on port `5000`. The UI has no auth (quick-start install) and the Workflows list is empty on first open; new workflows are authored through its **+ Submit New Workflow** form, whose in-browser YAML editor is the canonical authoring surface for this section.

The workflow to author is a `kind: Workflow` in namespace `argo` that declares a `spec.entrypoint` pointing at a template under `spec.templates`. That template runs a single `container` whose `command`/`args` stand in for a training step — an `echo` is fine, since this section teaches orchestration, not model quality. Once submitted, the single node should progress `Pending` → `Running` → `Succeeded`.

The end state must include:

- `GET http://localhost:5000/` returns `200` (Argo UI reachable).
- `workflow-controller` and `argo-server` Deployments in namespace `argo` are `Available`.
- At least one `Workflow` exists in namespace `argo`, and the most recent one is genuinely authored: it declares `spec.entrypoint` and a template whose `container`runs a `command`/`args`.
- That most recent workflow reaches `status.phase == Succeeded` (tests wait up to 180 s for a terminal phase).

> Argo's **+ Submit New Workflow** flow is how every future lab in this section starts. The UI's YAML editor is the canonical authoring surface—not `kubectl apply -f file.yaml` from a terminal. Authoring the Workflow spec by hand here—`entrypoint`, `templates`, `container`—is the foundation every WorkflowTemplate, CronWorkflow, and parameterised pipeline in the coming labs builds on.

---

Solution

Open Argo UI and select 'SUBMIT NEW WORKFLOW' in the top left

![screenshot](<../screenshots/Screenshot Day 85 Argo UI.png>)

Select 'Edit using full workflow options' 

![screenshot](<../screenshots/Screenshot Day 85 edit full workflow.png>)

The new workflow loads with an example template 

![screenshot](<../screenshots/Screenshot Day 85 example template.png>)

Replace example template with requirements from lab and use the '+ CREATE' button at the top to create

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: train-
  namespace: argo
spec:
  entrypoint: train
  templates:
    - name: train
      container:
        image: alpine:3.20
        command: [echo]
        args: ["fraud-detector: training step complete"]
```

![screenshot](<../screenshots/Screenshot Day 85 config workflow.png>)

Confirm workflow completes successfully

![screenshot](<../screenshots/Screenshot Day 85 confirm workflow 1.png>)

![screenshot](<../screenshots/Screenshot Day 85 confirm workflow 2.png>)

---
### Verification

Confirm Argo UI is reachable

```shell
curl -si http://localhost:5000 | grep 200
```

Output

```shell
HTTP/1.1 200 OK
```

Confirm deployments in namespace 'argo' are available

```shell
kubectl -n argo get deploy
```

Output

```shell
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
argo-server           1/1     1            1           41m
workflow-controller   1/1     1            1           41m
```

Confirm

```shell
curl -s http://localhost:5000/api/v1/workflows/argo | jq '.items[].metadata | {"Name": .name, "Namespace": .namespace}'
```

Output

```shell
{
  "Name": "train-nhbms",
  "Namespace": "argo"
}
```
