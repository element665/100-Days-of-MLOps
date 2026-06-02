Prompt

Complete the xFusionCorp Industries fraud-detection production DVC pipeline. Three stages are already wired in `dvc.yaml`, two remain, and the pipeline must finish as a reproducible, SeaweedFS-backed, v1.0-tagged release.

  

1. A project exists at `/root/code/ml-pipeline/` with Git and DVC initialised. The `params.yaml` is in place and the `.dvc/config` is pre-configured to push to the SeaweedFS bucket `dvc-storage` at `http://localhost:8333`.
    
2. The `ingest`, `validate`, and `preprocess` stages are already declared in `dvc.yaml`, but one of them contains an incorrect output path that prevents `dvc repro` from completing. Find and fix it.
    
3. The remaining two stages need to be added:
    
    - `train` – Depends on the preprocessed dataset and `scripts/train.py`; reads `n_estimators`, `max_depth`, `test_size`, and `random_seed` from `params.yaml`; outputs `models/model.pkl` and `data/processed/test_split.csv`; declares `metrics.json` as a DVC metric with `cache: false`.
    - `evaluate` – Depends on `models/model.pkl`, `data/processed/test_split.csv`, and `scripts/evaluate.py`; outputs `reports/evaluation.json` declared with `cache: false`.
4. The two scripts you need are pre-staged at `/root/code/ml-pipeline/scripts-staging/train.py`and `scripts-staging/evaluate.py`. Copy them into `scripts/` before adding the stages.
    
5. Run the full pipeline with `dvc repro`, push the cache to the SeaweedFS remote with `dvc push`, and tag the current state as `v1.0`.
    
6. Commit every change to Git so the release is fully captured.
    

> Open the **SeaweedFS Filer** button at the top of the lab and navigate to `/buckets/dvc-storage/` to confirm that the bucket holds the pushed artefacts under the `files/md5/...` layout.

---

Solution

dvc.yaml (Original)

```yaml
stages:
  ingest:
    cmd: python scripts/ingest.py
    deps:
      - scripts/ingest.py
      - data/raw/data.csv

  validate:
    cmd: python scripts/validate.py
    deps:
      - data/raw/data.csv
      - scripts/validate.py
    outs:
      - reports/validation.json:
          cache: false

  preprocess:
    cmd: python scripts/preprocess.py
    deps:
      - data/raw/data.csv
      - scripts/preprocess.py
    outs:
      - data/processed/cleaned.csv

```

params.yaml (Original)

```yaml
test_size: 0.2
random_seed: 42
n_estimators: 100
max_depth: 5

```

.dvc/config (Original)

```
[core]
    remote = s3

['remote "s3"']
    url = s3://dvc-storage
    endpointurl = http://localhost:8333
    access_key_id = weedadmin
    secret_access_key = weedadmin123

```

dvc.yaml (Updated)

- preprocess outs 'cleaned.csv -> clean.csv'
- add train and evaluate stages

```yaml
stages:
  ingest:
    cmd: python scripts/ingest.py
    deps:
      - scripts/ingest.py
      - data/raw/data.csv

  validate:
    cmd: python scripts/validate.py
    deps:
      - data/raw/data.csv
      - scripts/validate.py
    outs:
      - reports/validation.json:
          cache: false

  preprocess:
    cmd: python scripts/preprocess.py
    deps:
      - data/raw/data.csv
      - scripts/preprocess.py
    outs:
      - data/processed/clean.csv

  train:
    cmd: python scripts/train.py
    deps:
      - data/processed/clean.csv
      - scripts/train.py
    params:
      - n_estimators
      - max_depth
      - test_size
      - random_seed
    outs:
      - models/model.pkl
      - data/processed/test_split.csv
    metrics:
      - metrics.json:
          cache: false
  evaluate:
    cmd: python scripts/evaluate.py
    deps:
      - models/model.pkl
      - data/processed/test_split.csv
      - scripts/evaluate.py
    outs:
      - reports/evaluation.json:
          cache: false

```

Navigate to working directory

```shell
cd /root/code/ml-pipeline/
```

Run dvc repro to check to error message

```shell
dvc repro
```

Output

```shell
ERROR: failed to reproduce 'preprocess': output 'data/processed/cleaned.csv' does not exist
```

- Update dvc.yaml with correction and new stages

Copy pre-staged scripts into correct directory

```shell
cp scripts-staging/{train.py,evaluate.py} scripts/
```

Run full pipeline

```shell
dvc repro
```

Pipeline completed successfully

Now push to SeaweedFS

```shell
dvc push
```

Push successful

Add dvc.lock file to git

```shell
git add dvc.lock
```

Stage and commit changes

```shell
git add .
git commit -m "Complete fraud detection pipeline release"
```

Tag current state

```shell
git tag v1.0
```

Screenshot Verification

![Screenshot](<../screenshots/Screenshot Day 19.png>)