Prompt

The xFusionCorp Industries ML platform team is currently enhancing the `fraud-detector` continuous integration (CI) process. The existing `main.yml` file contains three similar inline jobs that have been duplicated, requiring the same changes to be implemented for each on every pull request (PR). A team member has already separated the `lint`, `test`, and `report` stages into distinct files located in the `.gitea/workflows/` directory—each configured to declare `on: workflow_call`—and has opened a PR that modifies one job (`lint`) to call the reusable workflow. Your task is to complete this refactor by converting the two remaining inline jobs in `main.yml` into `uses:` calls, thereby enabling the main run to expand into three nested `workflow_call`executions.

  

The Gitea UI is on port `3000` (**Gitea** button). Admin credentials: `gitea-admin` / `gitea2026`. The repo is at `http://localhost:3000/gitea-admin/fraud-detector` and a working clone is at `/root/code/fraud-detector`, already checked out on branch `add-reusable-workflows`. The PR is pre-opened.

Four workflow files ship in `.gitea/workflows/`. `lint.yml`, `test.yml`, and `report.yml` are reusable callees, each triggered by `on: workflow_call`. `main.yml` is the caller: `jobs.lint` already calls `./.gitea/workflows/lint.yml` via `uses:` (the example wiring), while `jobs.test` and `jobs.report` are still inline `runs-on` + `steps` jobs that duplicate logic already parked in the callee files. Those two inline job bodies need to become single `uses:` lines mirroring the `lint` job — a job cannot declare both `uses:`and `steps:`, so the inline blocks are removed entirely.

The end state must include:

- `lint.yml`, `test.yml`, and `report.yml` each declare `on: workflow_call` on the PR head branch.
- `main.yml` defines jobs `lint`, `test`, and `report`, each with a `uses:` key pointing at the matching `./.gitea/workflows/<name>.yml`.
- No job in `main.yml` mixes `uses:` with `steps:`(illegal in Actions YAML).
- The PR head commit's combined status reaches `success`.

> Reusable workflows turn a monolithic `main.yml` into a small graph of composable pieces. Each callee becomes the canonical definition for its concern (lint / test / report); any number of callers can consume it. When you later add a `release.yml` workflow for tagged pushes, it can reuse the same `test.yml` callee—no more copy-paste sync issues across files.

---
### Provided files

[.gitea/workflows/lint.yml](<../assets/Day 82 - lint.yml>)

[.gitea/workflows/test.yml](<../assets/Day 82 - test.yml>)

[.gitea/workflows/report.yml](<../assets/Day 82 - report.yml>)

---
### Solution

main.yml (Original)

```yaml
name: Main

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

# The `lint` job is the example wiring -- it calls the reusable
# lint.yml via `uses:`. The `test` and `report` jobs below duplicate
# the logic already parked in test.yml and report.yml. Convert both
# of them to `uses:` calls in the same shape as `lint`.

jobs:
  lint:
    uses: ./.gitea/workflows/lint.yml

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install pytest + runtime deps
        run: pip install --break-system-packages pytest pandas numpy scikit-learn joblib
      - name: Run pytest
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
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: model-report
          path: artifacts/
```

main.yml (Updated)

```yaml
name: Main

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint:
    uses: ./.gitea/workflows/lint.yml

  test:
    uses: ./.gitea/workflows/test.yml

  report:
    uses: ./.gitea/workflows/report.yml
```

Stage changes

```shell
cd /root/code/fraud-detector
git add .gitea/workflows/main.yml
```

Commit changes

```shell
git commit -m "ci: implement reusable workflows"
```

Output

```shell
[add-reusable-workflows c80c098] ci: implement reusable workflows
 1 file changed, 2 insertions(+), 26 deletions(-)
```

Push changes

```shell
git push origin add-reusable-workflows
```

Output

```shell
Enumerating objects: 9, done.
Counting objects: 100% (9/9), done.
Delta compression using up to 16 threads
Compressing objects: 100% (4/4), done.
Writing objects: 100% (5/5), 464 bytes | 464.00 KiB/s, done.
Total 5 (delta 3), reused 0 (delta 0), pack-reused 0
remote: 
remote: Visit the existing pull request:
remote:   http://localhost:3000/gitea-admin/fraud-detector/pulls/1
remote: 
remote: . Processing 1 references
remote: Processed 1 references in total
To http://localhost:3000/gitea-admin/fraud-detector.git
   521d74a..c80c098  add-reusable-workflows -> add-reusable-workflows
```

Login to Gitea UI

![screenshot](<../screenshots/Screenshot Day 82 Gitea UI.png>)

Navigate to 'fraud-detector' repo

![screenshot](<../screenshots/Screenshot Day 82 select repo.png>)

Select 'Pull Requests' from menu

![screenshot](<../screenshots/Screenshot Day 82 select PR.png>)

Select latest PR 'Refactor main workflow to use workflow_call'

![screenshot](<../screenshots/Screenshot Day 82 latest PR.png>)

All checks were successful

![screenshot](<../screenshots/Screenshot Day 82 checks successful.png>)

Create merge commit

![screenshot](<../screenshots/Screenshot Day 82 create merge.png>)

Pull request successfully merged and closed

![screenshot](<../screenshots/Screenshot Day 82 PR merged and closed.png>)

---
### Verification

Confirm latest pull request

```shell
TOKEN=$(cat /root/.gitea/token)

curl -s -H "Authorization: token $TOKEN" \
  'http://localhost:3000/api/v1/repos/gitea-admin/fraud-detector/pulls?state=all&sort=newest' | jq '.[] | {"PR Name": .title, "SHA": .head.sha}'
```

Output

```shell
{
  "PR Name": "Refactor main workflow to use workflow_call",
  "SHA": "c80c0984bf04a6508c8629e4278b63ecb38032bf"
}
```

Confirm pull request merged successfully

```shell
curl -s -H "Authorization: token $TOKEN"   "http://localhost:3000/api/v1/repos/gitea-admin/fraud-detector/commits/c80c0984bf04a6508c8629e4278b63ecb38032bf/status" | jq '{"Status": .state}'
```

Output

```shell
{
  "Status": "success"
}
```
