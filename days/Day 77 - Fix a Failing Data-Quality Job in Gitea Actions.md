Prompt

The xFusionCorp Industries ML platform team requires data-schema tests to be executed as a continuous integration (CI) gate for every pull request, ensuring that poor training data is detected before it affects the model. A team member has submitted a pull request titled **Add data-quality CI gate** in the `fraud-detector`repository; however, the newly added `data-quality`job has failed on its initial execution. Your objective is to examine the failed run log in Gitea Actions, determine the cause of the job failure, rectify the workflow, and push your changes so that the pull request is successful.

  

The Gitea UI is running on port `3000` (the **Gitea** button opens the login page). Admin credentials: `gitea-admin` / `gitea2026`. The repo lives at `http://localhost:3000/gitea-admin/fraud-detector` and a working clone is at `/root/code/fraud-detector`, already checked out on branch `add-data-validation`.

The pre-opened PR's workflow at `.gitea/workflows/ci.yml`declares three jobs: **lint**, **test** (both green), and **data-quality**(meant to run the data-schema tests, currently **red**). Open the failed `data-quality` run from the PR's **Checks** tab to read its log.

The end state must include:

- The `data-quality` job is still declared in the workflow (do not delete the job itself).
- The data-quality job's pytest step references a `.py` file that exists on the `add-data-validation` branch.
- After the latest push, the PR's head commit's combined status reaches `success` (all three jobs green).

> The point of a red CI run is not just the red pill in the PR—it is the log underneath it. A workflow can look fine by static inspection and still fail at runtime.

---

Solution

Login to Gitea UI

![screenshot](<../screenshots/Screenshot Day 77 Gitea Login.png>)

Select the fraud-detector repo

![screenshot](<../screenshots/Screenshot Day 77 select repo.png>)

From the repo select the Pull Request tab

![screenshot](<../screenshots/Screenshot Day 77 select PR tab.png>)

Select the Add data-quality CI gate request

![screenshot](<../screenshots/Screenshot Day 77 select request.png>)

Select the failed CI step 'data-quality' details

![screenshot](<../screenshots/Screenshot Day 77 select failed step.png>)

Inspect where the failure began 'Run data-quality tests'

![screenshot](<../screenshots/Screenshot Day 77 inspect failure.png>)

The error is due to missing file 'tests/test_data_validation.py'

![screenshot](<../screenshots/Screenshot Day 77 error missing file.png>)

Review the Gitea workflow file

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
      - name: Install pytest
        run: pip install --break-system-packages pytest
      - name: Run pytest
        run: python3 -m pytest tests/test_train.py -v

  data-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install pytest + pandas
        run: pip install --break-system-packages pytest pandas
      - name: Run data-quality tests
        run: python3 -m pytest tests/test_data_validation.py -v
```

Update file with correct file name under data-quality block

```shell
- name: Run data-quality tests
  run: python3 -m pytest tests/test_data_quality.py -v
```

Confirm git status and working branch

```shell
cd /root/code/fraud-detector
git status
```

Output

```shell
On branch add-data-validation
Your branch is up to date with 'origin/add-data-validation'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   .gitea/workflows/ci.yml

no changes added to commit (use "git add" and/or "git commit -a")
```

Stage change in git

```shell
git add .gitea/workflows/ci.yml
```

Commit change

```shell
git commit -m "Update CI with correct data-quality test file"
```

Output

```shell
[add-data-validation 2af9755] Update CI with correct data-quality test file
 1 file changed, 1 insertion(+), 1 deletion(-)
```

Push change to trigger Gitea workflow

```shell
git push -u origin add-data-validation
```

Output

```shell
Enumerating objects: 9, done.
Counting objects: 100% (9/9), done.
Delta compression using up to 16 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (5/5), 440 bytes | 440.00 KiB/s, done.
Total 5 (delta 2), reused 0 (delta 0), pack-reused 0
remote: 
remote: Visit the existing pull request:
remote:   http://localhost:3000/gitea-admin/fraud-detector/pulls/1
remote: 
remote: . Processing 1 references
remote: Processed 1 references in total
To http://localhost:3000/gitea-admin/fraud-detector.git
   f12d3e5..2af9755  add-data-validation -> add-data-validation
branch 'add-data-validation' set up to track 'origin/add-data-validation'.
```

Confirm workflow in Gitea UI

![screenshot](<../screenshots/Screenshot Day 77 confirm workflow.png>)

All 3 checks passed (lint, test, and data-quality)

![screenshot](<../screenshots/Screenshot Day 77 checks passed.png>)

Create merge commit

![screenshot](<../screenshots/Screenshot Day 77 create merge commit.png>)

 Pull request successfully merged and closed

![screenshot](<../screenshots/Screenshot Day 77 PR merged and closed.png>)

