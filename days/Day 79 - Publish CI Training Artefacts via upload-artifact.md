Prompt

The xFusionCorp Industries ML platform team's Continuous Integration (CI) system currently trains the model and generates a confusion matrix in PNG format. However, these artifacts are discarded when the runner tears down the workspace, preventing reviewers on a Pull Request (PR) from accessing them. A teammate has submitted a PR titled **Publish Training Artifacts from CI** in the `fraud-detector` repository. Your task is to integrate `actions/upload-artifact`into the existing `report` job, ensuring that `metrics.json` and `confusion_matrix.png` are available as a downloadable zip file on the run page.

  

The Gitea UI is running on port `3000` (the **Gitea** button opens the login page). Admin credentials: `gitea-admin` / `gitea2026`. The repo lives at `http://localhost:3000/gitea-admin/fraud-detector` and a working clone is at `/root/code/fraud-detector`, already checked out on branch `add-artifact-upload`. The PR is pre-opened.

The current `report` job in `.gitea/workflows/ci.yml` already installs `numpy scikit-learn joblib matplotlib`, runs `python3 -m src.train` (writes `artifacts/model.joblib` and `artifacts/metrics.json`), runs `python3 -m src.plot` (writes `artifacts/confusion_matrix.png`), and ends with `ls -la artifacts/` — but the produced files are discarded when the run finishes. The job needs a final step that uploads the `artifacts/` directory as a named artefact (`model-report`) using `actions/upload-artifact`. Use `@v3` — Gitea's runner rejects `@v4`.

The end state must include:

- The `report` job contains a step that uses `actions/upload-artifact@*` with a non-empty `path`and the artefact name `model-report`.
- The run-level artefact download at `/gitea-admin/fraud-detector/actions/runs/<id>/artifacts/model-report`returns a zip containing both `metrics.json` and `confusion_matrix.png` by basename.
- The PR head commit's combined status is `success`.

> Artefacts are CI's answer to the question 'what did that run actually produce?'. A green check-mark tells you the code compiled; an uploaded artefact tells you what shipped out the other end. For ML runs, this is where the metrics JSON, the confusion matrix plot, and the pickled model live before anyone promotes them to a registry.

---

Solution

.gitea/workflows/ci.yml

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install ruff
        run: pip install --break-system-packages ruff
      - name: Run ruff
        run: ruff check src tests

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install pytest + runtime deps
        run: pip install --break-system-packages pytest pandas numpy scikit-learn joblib
      - name: Run all tests
        run: python3 -m pytest tests -v

  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install report deps
        run: pip install --break-system-packages numpy scikit-learn joblib matplotlib
      - name: Train
        run: python3 -m src.train
      - name: Plot confusion matrix
        run: python3 -m src.plot
      - name: List produced artefacts
        run: ls -la artifacts/
```



```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install ruff
        run: pip install --break-system-packages ruff
      - name: Run ruff
        run: ruff check src tests

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install pytest + runtime deps
        run: pip install --break-system-packages pytest pandas numpy scikit-learn joblib
      - name: Run all tests
        run: python3 -m pytest tests -v

  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install report deps
        run: pip install --break-system-packages numpy scikit-learn joblib matplotlib
      - name: Train
        run: python3 -m src.train
      - name: Plot confusion matrix
        run: python3 -m src.plot
      - name: List produced artefacts
        run: ls -la artifacts/
      - uses: actions/upload-artifact@v3
        with:
          name: model-report
          path: |
            artifacts/metrics.json
            artifacts/confusion_matrix.png
```

Stage changes

```shell
cd fraud-detector/
git add .gitea/workflows/ci.yml
```

Commit changes

```shell
git commit -m "ci: add artifact upload step to workflow"
```

Output

```shell
[add-artifact-upload 3f96f07] ci: add artifact upload step to workflow
 1 file changed, 7 insertions(+), 1 deletion(-)
```

Push changes

```shell
git push origin add-artifact-upload
```

Output

```shell
Enumerating objects: 9, done.
Counting objects: 100% (9/9), done.
Delta compression using up to 16 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (5/5), 525 bytes | 525.00 KiB/s, done.
Total 5 (delta 2), reused 0 (delta 0), pack-reused 0
remote: 
remote: Visit the existing pull request:
remote:   http://localhost:3000/gitea-admin/fraud-detector/pulls/1
remote: 
remote: . Processing 1 references
remote: Processed 1 references in total
To http://localhost:3000/gitea-admin/fraud-detector.git
   2ee778f..3f96f07  add-artifact-upload -> add-artifact-upload
```


Login to Gitea UI

![screenshot](<../screenshots/Screenshot Day 79 Gitea UI login.png>)

Navigate to the 'fraud-detector' repo

![screenshot](<../screenshots/Screenshot Day 79 select repo.png>)

Select the 'Pull Requests' menu

![screenshot](<../screenshots/Screenshot Day 79 select PR tab.png>)

Select 'Publish training artefacts from CI' 

![screenshot](<../screenshots/Screenshot Day 79 select PR.png>)

View PR details

![screenshot](<../screenshots/Screenshot Day 79 PR details.png>)

Select 'CI / report' details

![screenshot](<../screenshots/Screenshot Day 79 CI report details.png>)

the 'report' step shows 2 files uploaded and 'model-report' under Artifacts

![screenshot](<../screenshots/Screenshot Day 79 completed action.png>)

Create merge commit

![screenshot](<../screenshots/Screenshot Day 79 merge commit.png>)

Pull request successfully merged and closed

![screenshot](<../screenshots/Screenshot Day 79 merged and closed.png>)

