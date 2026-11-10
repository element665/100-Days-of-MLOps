Prompt

The xFusionCorp Industries ML platform team requires that every pull request (PR) in the `fraud-detector`repository logs a training run to MLflow and registers the resulting model version. However, they prefer not to include the tracking URL or an API token in plaintext within the workflow file. Gitea and a local MLflow 3.x server are currently operational, and a teammate has initiated a PR titled **Register trained model on every push**. Currently, the first run fails because the `register` job is attempting to access `MLFLOW_TRACKING_URI` and `MLFLOW_TOKEN` from the environment, but these variables are not populated. Your task is to provision these two values as repository secrets and integrate them into the workflow to ensure the run succeeds.

  

The Gitea UI is on port `3000` (**Gitea** button); admin credentials `gitea-admin` / `gitea2026`. The MLflow UI is on port `5000`(**MLflow UI** button). The repo is at `http://localhost:3000/gitea-admin/fraud-detector` and a working clone is at `/root/code/fraud-detector`, already checked out on branch `add-registry-push`. The PR is pre-opened.

The shipped `.gitea/workflows/ci.yml` declares a `register`job that runs `python3 -m src.register`. `src/register.py`reads `MLFLOW_TRACKING_URI` and `MLFLOW_TOKEN` from `os.environ` and exits non-zero if either is missing, so on the first run the job fails with that error. Two pieces are needed: the repository secrets `MLFLOW_TRACKING_URI` (value `http://localhost:5000`) and `MLFLOW_TOKEN` (any non-empty string, e.g. `fraud-detector-ci-token` — the lab's MLflow does not enforce auth, but the script refuses to run without the value so a missing secret surfaces as a clear failure), created under the repo's **Settings → Actions → Secrets**; and the workflow wiring that exports each secret into the `register` job's environment under the same name.

The end state must include:

- `GET /api/v1/repos/gitea-admin/fraud-detector/actions/secrets` lists both `MLFLOW_TRACKING_URI` and `MLFLOW_TOKEN`.
- The `register` job in the workflow references each secret via `${{ secrets.<NAME> }}` inside an `env:`block (job-level or step-level).
- The PR head commit's combined status is `success`.
- MLflow's registered-model endpoint reports `fraud-detector` with at least one version.

> Repository secrets are the CI version of an environment-specific config file. The YAML stays identical between dev, staging, and prod; only the secret values change. This is also the pattern you extend when you add a PyPI token, an S3 access key, or a Kubernetes kubeconfig to a workflow—never paste the value into the committed file.

---

Solution

Login to Gitea UI

![screenshot](<../screenshots/Screenshot Day 80 Gitea UI login.png>)

Navigate to 'fraud-detector' repo

![screenshot](<../screenshots/Screenshot Day 80 select repo.png>)

Go to the repo's setting

![screenshot](<../screenshots/Screenshot Day 80 repo settings.png>)

Select 'Actions' -> 'Secrets' from the left menu

![screenshot](<../screenshots/Screenshot Day 80 secrets menu.png>)

Add secret

![screenshot](<../screenshots/Screenshot Day 80 add secret.png>)

Configure MLflow tracking URI secret

![screenshot](<../screenshots/Screenshot Day 80 configure secret 1.png>)

Add next secret

![screenshot](<../screenshots/Screenshot Day 80 add secret 2.png>)

Configure MLFLOW_TOKEN secret

![screenshot](<../screenshots/Screenshot Day 80 config secret 2.png>)

Confirm both secrets exist

![screenshot](<../screenshots/Screenshot Day 80 confirm secrets.png>)


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

  register:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install registration deps
        run: pip install --break-system-packages mlflow numpy scikit-learn joblib pandas
      - name: Train and register
        run: python3 -m src.register
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
    steps:
      - uses: actions/checkout@v4
      - name: Install pytest + runtime deps
        run: pip install --break-system-packages pytest pandas numpy scikit-learn joblib
      - name: Run all tests
        run: python3 -m pytest tests -v

  register:
    runs-on: ubuntu-latest
    env:
      MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
      MLFLOW_TOKEN: ${{ secrets.MLFLOW_TOKEN }}
    steps:
      - uses: actions/checkout@v4
      - name: Install registration deps
        run: pip install --break-system-packages mlflow numpy scikit-learn joblib pandas
      - name: Train and register
        run: python3 -m src.register
```

Stage changes

```shell
cd fraud-detector/
git add .gitea/workflows/ci.yml
```

Commit changes

```shell
git commit -m "ci: add MLflow secrets to workflow"
```

Output

```shell
[add-registry-push ebf8899] ci: add MLflow secrets to workflow
 1 file changed, 4 insertions(+)
```

Push changes

```shell
git push origin add-registry-push
```

Output

```shell
Enumerating objects: 9, done.
Counting objects: 100% (9/9), done.
Delta compression using up to 16 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (5/5), 530 bytes | 530.00 KiB/s, done.
Total 5 (delta 2), reused 0 (delta 0), pack-reused 0
remote: 
remote: Visit the existing pull request:
remote:   http://localhost:3000/gitea-admin/fraud-detector/pulls/1
remote: 
remote: . Processing 1 references
remote: Processed 1 references in total
To http://localhost:3000/gitea-admin/fraud-detector.git
   93d84ac..ebf8899  add-registry-push -> add-registry-push
```

Go back to Gitea UI 'fraud-detector' repo to Pull Requests
Select 'Register trained model on every push'

![screenshot](<../screenshots/Screenshot Day 80 PR page.png>)

Create merge commit

![screenshot](<../screenshots/Screenshot Day 80 create merge commit.png>)

Pull request successfully merged and closed

![screenshot](<../screenshots/Screenshot Day 80 merged and closed.png>)

MLflow UI 

![screenshot](<../screenshots/Screenshot Day 80 MLflow UI.png>)

### Verification

Confirm the secrets at Gitea api endpoint

```shell
curl -s -u gitea-admin:gitea2026 -H "Accept: application/json" "http://localhost:3000/api/v1/repos/gitea-admin/fraud-detector/actions/
secrets" | jq
```

Output

```shell
[
  {
    "name": "MLFLOW_TRACKING_URI",
    "created_at": "2026-11-10T09:07:54-05:00"
  },
  {
    "name": "MLFLOW_TOKEN",
    "created_at": "2026-11-10T09:08:27-05:00"
  }
]
```

Confirm the registered model at the MLflow api endpoint

```shell
curl -s "http://localhost:5000/api/2.0/mlflow/registered-models/get?name=fraud-detector" | jq '.registered_model.latest_versions[] | {Name: .name, Version: .version, Status: .status}'
```

Output

```shell
{
  "Name": "fraud-detector",
  "Version": "1",
  "Status": "READY"
}
```

