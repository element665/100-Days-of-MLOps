Prompt

The xFusionCorp Industries ML platform team requires that pull requests for the `fraud-detector` repository automatically run linting and testing processes prior to the review stage. A local Gitea server is currently operational with the `fraud-detector` repository pre-pushed on the `main` branch. Additionally, a self-hosted Actions runner has been registered and is awaiting jobs. Your objective is to complete the integration of the CI workflow template, which is located at `.gitea/workflows/ci.yml.template` on the `main` branch, within a feature branch. Once completed, open a pull request, monitor the Checks tab for successful approvals, and subsequently merge the pull request into the `main` branch.

  

The Gitea UI is running on port `3000` (the **Gitea** button opens the login page). Admin credentials: `gitea-admin` / `gitea2026`. The repo is at `http://localhost:3000/gitea-admin/fraud-detector`, with a working clone at `/root/code/fraud-detector` (on `main`).

The scaffold under `/root/code/fraud-detector/` lints clean and has passing tests: `src/train.py` (a deterministic synthetic training script), `tests/test_train.py` (three passing unit tests), `pyproject.toml` (Ruff + pytest config), and `.gitea/workflows/ci.yml.template` — a pre-written CI workflow with the `on:` triggers and `lint` + `test` job skeletons already wired, plus `# TODO:` markers on the two `run:` lines that need filling in. Ruff and pytest are both installed on the host. Gitea Actions only schedules `*.yml` / `*.yaml` files, so the `.template` suffix keeps the file inert until it is renamed to `ci.yml`.

The end state must include:

- A workflow file `.gitea/workflows/ci.yml` on branch `add-ci` that parses as YAML and declares both a `lint`and a `test` job.
- One pull request in the repo targeting `main`, with `add-ci` as its head branch.
- That PR's head commit reports combined status `success` on `GET /api/v1/repos/gitea-admin/fraud-detector/commits/{sha}/status`.
- The PR is merged into `main` (`merged: true` on the pulls API).

> Gitea Actions uses the same YAML syntax as GitHub Actions, so the workflow you ship here is also the kind of file you would drop into any `github.com` repo. Real CI engineers rarely author these from scratch — they inherit a template and edit the two or three lines that are project-specific, which is exactly what the `.template` scaffold mirrors.

---

Solution

.gitea/workflows/ci.yml.template (Original)

```yaml
# Gitea Actions CI workflow for the fraud-detector repo.
#
# Rename this file to `ci.yml`, fill in the two TODO `run:` lines,
# and commit + push on your feature branch. Gitea Actions only
# schedules workflow files named `.yml` or `.yaml`, so the
# `.template` suffix keeps this scaffold inert until it's renamed.
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
        run: # TODO: lint `src` and `tests` with ruff

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install pytest
        run: pip install --break-system-packages pytest
      - name: Run pytest
        run: # TODO: run pytest on the tests/ directory with verbose output
```

.gitea/workflows/ci.yml

```yaml
# Gitea Actions CI workflow for the fraud-detector repo.
#
# Rename this file to `ci.yml`, fill in the two TODO `run:` lines,
# and commit + push on your feature branch. Gitea Actions only
# schedules workflow files named `.yml` or `.yaml`, so the
# `.template` suffix keeps this scaffold inert until it's renamed.
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
        run: ruff check src/ tests/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install pytest
        run: pip install --break-system-packages pytest
      - name: Run pytest
        run: pytest -v tests/
```

Create new branch

```shell
git checkout -b add-ci
```

Output

```shell
Switched to a new branch 'add-ci'
```

Stage changes

```shell
git add .gitea/workflows/ci.yml
```

Commit changes

```shell
git commit -m "Add lint and test jobs to CI pipeline"
```

Output

```shell
[add-ci ee3fab3] Add lint and test jobs to CI pipeline
 1 file changed, 32 insertions(+)
 create mode 100644 .gitea/workflows/ci.yml
```

Push changes

```shell
git push -u origin add-ci
```

Output

```shell
Enumerating objects: 8, done.
Counting objects: 100% (8/8), done.
Delta compression using up to 16 threads
Compressing objects: 100% (4/4), done.
Writing objects: 100% (5/5), 808 bytes | 808.00 KiB/s, done.
Total 5 (delta 1), reused 0 (delta 0), pack-reused 0
remote: 
remote: Create a new pull request for 'add-ci':
remote:   http://localhost:3000/gitea-admin/fraud-detector/compare/main...add-ci
remote: 
remote: . Processing 1 references
remote: Processed 1 references in total
To http://localhost:3000/gitea-admin/fraud-detector.git
 * [new branch]      add-ci -> add-ci
branch 'add-ci' set up to track 'origin/add-ci'.
```

Login to Gitea UI

![screenshot](<../screenshots/Screenshot Day 76 Gitea login.png>)

Navigate to 'fraud-detector' repo

![screenshot](<../screenshots/Screenshot Day 76 select repo.png>)

Select 'New Pull Request'

![screenshot](<../screenshots/Screenshot Day 76 select new PR.png>)

Merge and pull branches are correct so select 'New Pull Request'

![screenshot](<../screenshots/Screenshot Day 76 confirm branches.png>)

Write a description for the PR

![screenshot](<../screenshots/Screenshot Day 76 PR description.png>)

Wait to merge until checks have completed

![screenshot](<../screenshots/Screenshot Day 76 merge wait.png>)

'lint' job has completed successfully

![screenshot](<../screenshots/Screenshot Day 76 lint job.png>)

'test' job has completed successfully

![screenshot](<../screenshots/Screenshot Day 76 test job.png>)

Now create merge commit

![screenshot](<../screenshots/Screenshot Day 76 create merge commit.png>)

![screenshot](<../screenshots/Screenshot Day 76 create merge commit 2.png>)

Pull request successfully merged and closed

![screenshot](<../screenshots/Screenshot Day 76 merged and closed.png>)

---
### Verification

Confirm CI status

```shell
curl -s http://localhost:3000/api/v1/repos/gitea-admin/fraud-detector/commits/ee3fab3629/status \
  | jq '{
      state,
      sha,
      total_count,
      checks: [.statuses[] | {
        context,
        status,
        description
      }]
    }'
```

Output

```shell
{
  "state": "success",
  "sha": "ee3fab36292dcd09b3ffb62bd2c686c9b53700fc",
  "total_count": 2,
  "checks": [
    {
      "context": "CI / lint (pull_request)",
      "status": "success",
      "description": "Successful in 11s"
    },
    {
      "context": "CI / test (pull_request)",
      "status": "success",
      "description": "Successful in 12s"
    }
  ]
}
```

Confirm PR status

```shell
curl -s http://localhost:3000/api/v1/repos/gitea-admin/fraud-detector/pulls | jq '.[] | {
  number,
  title,
  state,
  merged,
  head: .head.ref,
  base: .base.ref
}'
```

Ouput

```shell
{
  "number": 1,
  "title": "Add lint and test jobs to CI pipeline",
  "state": "closed",
  "merged": true,
  "head": "add-ci",
  "base": "main"
}
```