Prompt

The xFusionCorp Industries ML platform team has three distinct test suites within the `fraud-detector`repository: unit tests (`test_train.py`), data quality tests (`test_data_quality.py`), and model contract tests (`test_model_contract.py`). Currently, the continuous integration (CI) pipeline executes all three suites serially within a single `test` job. As the test suites expand, this configuration is becoming a significant bottleneck for every pull request (PR). A teammate has submitted a PR titled **Convert test job to matrix strategy**. Your task is to modify the workflow to enable the `test` job to utilize a Gitea Actions matrix, allowing each test suite to run in its own parallel job.

  

The Gitea UI is running on port `3000` (the **Gitea** button opens the login page). Admin credentials: `gitea-admin` / `gitea2026`. The repo lives at `http://localhost:3000/gitea-admin/fraud-detector` and a working clone is at `/root/code/fraud-detector`, already checked out on branch `add-test-matrix`. The PR is pre-opened.

The current `.gitea/workflows/ci.yml` declares a `test` job that runs all suites serially on a single runner, alongside a `lint`job. Three test files live under `tests/`: `test_train.py`, `test_data_quality.py`, `test_model_contract.py`. The goal is to fan the `test` job out over a `strategy.matrix` so each suite runs in its own parallel cell, while the `lint` job stays unchanged.

The end state must include:

- The `test` job in the workflow declares `strategy.matrix` whose list dimension contains `train`, `data_quality`, and `model_contract`.
- Every matrix value maps to an existing `tests/test_<value>.py` file on the `add-test-matrix`branch.
- The latest run on the PR head commit reports combined status `success`, with at least three `test` status entries (one per matrix cell).

> A matrix strategy is the CI equivalent of a loop variable: one job definition, many parameterised executions. The classical case is a Python-version matrix (3.10 / 3.11 / 3.12), but any axis works—test suites, feature flags, target platforms. The point is to express 'run this N times with N variants' once instead of copying the job body.

---

Solution

.gitea/workflows/ci.yml (Original)

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
```

.gitea/workflows/ci.yml (Updated)

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
      strategy:
        matrix:
          file: [train, data_quality, model_contract]
    steps:
      - uses: actions/checkout@v4
      - name: Install pytest + runtime deps
        run: pip install --break-system-packages pytest pandas numpy scikit-learn joblib
      - name: Run all tests
        run: python3 -m pytest tests/test_${{ matrix.file }}.py -v
```

Navigate to cloned repo directory

```shell
cd /root/code/fraud-detector
```

Check working branch in git

```shell
git status
```

Output

```shell
On branch add-test-matrix
Your branch is up to date with 'origin/add-test-matrix'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   .gitea/workflows/ci.yml

no changes added to commit (use "git add" and/or "git commit -a")
```

Stage and commit changes

```shell
git add .gitea/workflows/ci.yml
git commit -m "Convert test job to matrix strategy"
```

Output

```shell
[add-test-matrix 1e16a6e] Convert test job to matrix strategy
 1 file changed, 4 insertions(+), 1 deletion(-)
```

Push to existing PR branch

```shell
git push origin add-test-matrix
```

Output

```shell
Enumerating objects: 9, done.
Counting objects: 100% (9/9), done.
Delta compression using up to 16 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (5/5), 510 bytes | 510.00 KiB/s, done.
Total 5 (delta 2), reused 0 (delta 0), pack-reused 0
remote: 
remote: Visit the existing pull request:
remote:   http://localhost:3000/gitea-admin/fraud-detector/pulls/1
remote: 
remote: . Processing 1 references
remote: Processed 1 references in total
To http://localhost:3000/gitea-admin/fraud-detector.git
   1f26191..1e16a6e  add-test-matrix -> add-test-matrix
```

Login to Gitea UI

![screenshot](<../screenshots/Screenshot Day 78 Gitea login.png>)

Navigate to the 'fraud-detector' repo

![screenshot](<../screenshots/Screenshot Day 78 select repo.png>)

Select the 'Pull Requests' tab

![screenshot](<../screenshots/Screenshot Day 78 select PR.png>)

Select 'Convert test job to matrix strategy' request

![screenshot](<../screenshots/Screenshot Day 78 select request.png>)

Confirm all checks were successful

![screenshot](<../screenshots/Screenshot Day 78 confirm checks.png>)

Confirm each test used the correct file

![screenshot](<../screenshots/Screenshot Day 78 confirm test 1.png>)

![screenshot](<../screenshots/Screenshot Day 78 confirm test 2.png>)

![screenshot](<../screenshots/Screenshot Day 78 confirm test 3.png>)

Create merge commit

![screenshot](<../screenshots/Screenshot Day 78 create merge.png>)

Confirm 'Pull request successfully merged and closed'

![screenshot](<../screenshots/Screenshot Day 78 PR merged and closed.png>)

