Prompt

The xFusionCorp Industries ML platform team runs the `drift_check` Great Expectations checkpoint on the `fraud-detector` repository; however, it is currently not enforced in the continuous integration (CI) process. The `data-quality` workflow installs Great Expectations but does not execute the checkpoint, which means that a pull request that introduces data drift could potentially be merged without any checks. A teammate has already submitted a pull request to integrate the checkpoint into the workflow. Your objective is to configure the checkpoint as a **blocking merge gate**: ensure that the `data-quality` job executes `python3 -m src.gx_run` as a standard (non-`continue-on-error`) step, so that if the checkpoint fails, the job will also fail, thereby preventing the merge.

  

The Gitea UI is on port `3000` (**Gitea** button). Admin credentials: `gitea-admin` / `gitea2026`. The repo is at `http://localhost:3000/gitea-admin/fraud-detector` and a working clone is at `/root/code/fraud-detector`, already checked out on branch `enforce-data-quality-gate`. The PR is pre-opened.

The current `data-quality` job in `.gitea/workflows/data-quality.yml` checks out the repo and installs `great_expectations`, `pandas`, `numpy`—but does not run the checkpoint. `src/gx_run.py` bootstraps the GE project in-workspace, runs the `drift_check` checkpoint against `data/transactions.csv`, and **exits non-zero when the data violates the suite**. A blocking step that invokes `python3 -m src.gx_run`, pushed to the `enforce-data-quality-gate`branch, turns the checkpoint into a real merge gate.

The end state must include:

- The `data-quality` job has a step whose command runs `python3 -m src.gx_run`.
- That step is **blocking**: no `continue-on-error: true`, and no `|| true` / `; true`-style suffix that would swallow a failure.
- The PR head commit's combined status reaches `success` (the current `transactions.csv` is clean, so the gate passes).

> A CI check that runs but is marked `continue-on-error` (or whose command swallows its exit code) is **not** a gate—bad data merges anyway. The gate is only real when a failing checkpoint fails the job. The grader proves this by running the checkpoint against a deliberately bad row and confirming it exits non-zero.

---

Solution

data-quality.yml (Original)

```yaml
name: Data Quality

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  data-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Great Expectations
        run: |
          pip install --break-system-packages \
            great_expectations pandas numpy

      # TODO: add the data-quality GATE step here. Run the drift_check
      #       checkpoint with:  python3 -m src.gx_run
      #   `src/gx_run.py` exits non-zero when the checkpoint fails, so as
      #   an ordinary step its failure fails the job and BLOCKS the merge —
      #   that is the gate. Do NOT add `continue-on-error:` to the step and
      #   do NOT append `|| true` / `; true` to the command: either one lets
      #   a failing checkpoint pass, so bad data would merge anyway.
```

Complete TODO section

```yaml
name: Data Quality

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  data-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Great Expectations
        run: |
          pip install --break-system-packages \
            great_expectations pandas numpy
            
      - name: Data-quality GATE drift_check checkpoint
        run: |
          python3 -m src.gx_run
```

Verify checkpoint succeeds with clean data

```shell
python3 -m src.gx_run
echo $?
```

Output

```shell
Calculating Metrics: 100%|██████████████████████████████████████████| 27/27 [00:00<00:00, 9046.67it/s]
Checkpoint drift_check success=True
0
```

Check current git status of project

```shell
git status
git diff
```

Output

```shell
On branch enforce-data-quality-gate
Your branch is up to date with 'origin/enforce-data-quality-gate'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   .gitea/workflows/data-quality.yml

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        gx/

no changes added to commit (use "git add" and/or "git commit -a")
```

Add and commit the changes

```shell
git add .gitea/workflows/data-quality.yml
git commit -m "Enforce data quality checkpoint in CI"
git push origin enforce-data-quality-gate
```

Output

```shell
[enforce-data-quality-gate 7950ee4] Enforce data quality checkpoint in CI
 1 file changed, 5 insertions(+), 1 deletion(-)
Enumerating objects: 9, done.
Counting objects: 100% (9/9), done.
Delta compression using up to 16 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (5/5), 506 bytes | 506.00 KiB/s, done.
Total 5 (delta 2), reused 0 (delta 0), pack-reused 0
remote: 
remote: Visit the existing pull request:
remote:   http://localhost:3000/gitea-admin/fraud-detector/pulls/1
remote: 
remote: . Processing 1 references
remote: Processed 1 references in total
To http://localhost:3000/gitea-admin/fraud-detector.git
   7854056..7950ee4  enforce-data-quality-gate -> enforce-data-quality-gate
```

Verify 

```shell
git status
git log -1 --oneline
```

Output

```shell
On branch enforce-data-quality-gate
Your branch is up to date with 'origin/enforce-data-quality-gate'.

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        gx/

nothing added to commit but untracked files present (use "git add" to track)
7950ee4 (HEAD -> enforce-data-quality-gate, origin/enforc
e-data-quality-gate) Enforce data quality checkpoint in CI
```

 **Untracked Directory 

After running the checkpoint locally, `src/gx_run.py` created an untracked `gx/` directory while bootstrapping the Great Expectations project.

The `gx/` directory was not part of the requested CI change, so I decided it was best left untracked and was not included in the commit.

---

Verification Screenshots

Gitea UI Dashboard

![screenshot](<../screenshots/Screenshot Day 48 Gitea UI Dashboard.png>)

Gitea UI Pull Requests

![screenshot](<../screenshots/Screenshot Day 48 Gitea UI Pull Requests.png>)

Gitea UI Pull Request Details

![screenshot](<../screenshots/Screenshot Day 48 Gitea UI Pull Request Details.png>)