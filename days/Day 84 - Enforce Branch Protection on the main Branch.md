Prompt

The xFusionCorp Industries ML platform team is in the process of promoting the `fraud-detector` repository to production governance. A recent incident, in which an administrator force-merged a red pull request, resulted in a one-hour disruption of the `main` branch. This incident highlighted two critical gaps: the Continuous Integration (CI) pipeline only performs linting and does not execute the test suite, and there are no restrictions in place to require contributors to wait for CI checks before merging. Your capstone task is to address both issues. First, enhance the CI pipeline to ensure that it executes the repository's test suite as a `test` check in addition to the existing `lint` check. Next, configure Gitea branch protection rules on the `main` branch to mandate that all future changes must be made through a pull request. This pull request must show successful completion of both the `lint` and `test` checks, as well as receive at least one approving review.

  

The Gitea UI is on port `3000` (**Gitea** button). Admin credentials: `gitea-admin` / `gitea2026`. The repo is at `http://localhost:3000/gitea-admin/fraud-detector`, with a working clone at `/root/code/fraud-detector` (on `main`).

The work has two parts. First, `.gitea/workflows/ci.yml`defines only a `lint` job while the `test` job is left as a `# TODO`; a `test` job that installs the test deps and runs the repo's suite needs to be added and run on `main` at least once, since a status check can only be required once it exists as a context. Second, the `main` branch needs a branch-protection rule (under the repo's **Settings → Branches**) that blocks direct pushes so every change arrives through a PR, requires both the `lint` and `test` status checks, and requires at least `1`approving review.

The end state must include:

- `.gitea/workflows/ci.yml` on `main` defines a `test`job that runs pytest, alongside `lint`.
- `GET /api/v1/repos/gitea-admin/fraud-detector/branch_protections` returns a rule for `main`with `enable_status_check: true` and `status_check_contexts` including both a `lint` and a `test` entry.
- `required_approvals` is at least `1`.
- Direct push is blocked — either `enable_push: false`, or `enable_push_whitelist: true` with every allow-list empty.

> Branch protection is the guardrail production governance depends on: required status checks stop the 'reviewer overrides red CI' pattern, required reviews stop the 'admin merges pre-review on a Friday afternoon' incident, and blocking direct pushes means the only path onto `main` is a reviewed, green pull request—so every change is auditable, revertable, and release-taggable. And you can only require a check that exists, which is why you build the `test` job before you lock the branch behind it.

---

Solution

ci.yml

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

  # TODO: add a `test` job so the pipeline runs the repo's test suite,
  #       not just lint. Branch protection can only require a status
  #       check that actually exists, so `test` must be a real, run-once
  #       job before you can require it on `main`. The job should:
  #         runs-on: ubuntu-latest
  #         - uses: actions/checkout@v4
  #         - install pytest + runtime deps:
  #             pip install --break-system-packages pytest pandas numpy scikit-learn joblib
  #         - run the suite:
  #             python3 -m pytest tests -v
```

ci.yml (Updated)

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
      - name: Run the suite
        run: python3 -m pytest tests -v
```

Stage changes

```shell
cd /root/code/fraud-detector
git add .gitea/workflows/ci.yml
```

Commit changes

```shell
git commit -m "ci: add test job to pipeline"
```

Output

```shell
[main 32936a8] ci: add test job to pipeline
 1 file changed, 8 insertions(+), 10 deletions(-)
```

Push changes

```shell
git push origin main
```

Output

```shell
Enumerating objects: 9, done.
Counting objects: 100% (9/9), done.
Delta compression using up to 16 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (5/5), 481 bytes | 481.00 KiB/s, done.
Total 5 (delta 2), reused 0 (delta 0), pack-reused 0
remote: . Processing 1 references
remote: Processed 1 references in total
To http://localhost:3000/gitea-admin/fraud-detector.git
   d09a6c2..32936a8  main -> main
```

Login to Gitea UI

![screenshot](<../screenshots/Screenshot Day 84 Gitea login.png>)

Navigate to 'fraud-detector' repo

![screenshot](<../screenshots/Screenshot Day 84 select repo.png>)

Select 'Actions' to confirm workflow completed successfully

![screenshot](<../screenshots/Screenshot Day 84 select Actions.png>)

View details of latest run 'ci: add test job to pipeline'

![screenshot](<../screenshots/Screenshot Day 84 run details.png>)

Confirm test job completed all tests successfully

![screenshot](<../screenshots/Screenshot Day 84 test job.png>)

Select 'Settings' for the repo

![screenshot](<../screenshots/Screenshot Day 84 repo settings.png>)

Navigate to 'Branches' in the left menu and click 'Add New Rule' button on the right

![screenshot](<../screenshots/Screenshot Day 84 branches settings.png>)

Configure new rule with the following and save

- Protected Branch Name Pattern: main
- Whitelist Restricted Push: Selected
- Whitelisted users for pushing: leave empty
- Required approvals: 1
- Enable Status Check: Checked
- Status check patterns: 
```
CI / lint *
CI / test *
```
- 'Status checks found in the last week for this repository' should show both CI / lint (push) and CI / test (push) as matched

![screenshot](<../screenshots/Screenshot Day 84 config rule 1.png>)

![screenshot](<../screenshots/Screenshot Day 84 config rule 2.png>)

![screenshot](<../screenshots/Screenshot Day 84 config rule 3.png>)

![screenshot](<../screenshots/Screenshot Day 84 config rule 4.png>)

Confirm 'Branch protection for rule "main" has been updated.'

![screenshot](<../screenshots/Screenshot Day 84 branch protection rule updated.png>)

---

Verification

```shell
TOKEN=$(cat /root/.gitea/token)

curl -s -H "Authorization: token $TOKEN" \
  'http://localhost:3000/api/v1/repos/gitea-admin/fraud-detector/branch_protections' | \
  jq '.[] | {"Branch": .branch_name, "Enable Status Check": .enable_status_check, "Status Check Contexts": .status_check_contexts, "Required Approvals": .required_approvals, "Enable Push Whitelist": .enable_push_whitelist, "Allow User List": .push_whitelist_usernames, "Allow Team List": .push_whitelist_teams}'
```

Output

```JSON
{
  "Branch": "main",
  "Enable Status Check": true,
  "Status Check Contexts": [
    "CI / lint *",
    "CI / test *"
  ],
  "Required Approvals": 1,
  "Enable Push Whitelist": true,
  "Allow User List": [],
  "Allow Team List": []
}
```

