Prompt

After training a model, the xFusionCorp Industries ML team wants DVC to surface metrics through `dvc metrics show` and the DVC extension's METRICS view. The fraud-detection pipeline already trains a model and writes a `metrics.json`, but DVC does not recognise the file as a metric. Wire it in correctly.
  

1. A project exists at `/root/code/fraud-detection/` with a three-stage DVC pipeline (`process_data`, `split_data`, `train`). The `train` stage runs `src/models/train.py`, which writes the model to `models/model.pkl` and metrics to `metrics.json`. Do not modify the Python files.
    
2. The `train` stage in `dvc.yaml` must declare `metrics.json` as a DVC metric output, not as a regular file output. The metric must be declared with `cache: false` so the JSON lives in Git for diff history rather than in the DVC cache.
    
3. Re-run the pipeline with `dvc repro` so the metric registration takes effect.
    
4. After your changes, `dvc metrics show` must report the `accuracy` and `f1_score` values from `metrics.json`.
    

> The DVC extension's **METRICS** section under the DVC view will surface the same values directly in the editor once the metric is registered.

---

Solution

dvc.yaml

```yaml
stages:
  process_data:
    cmd: python src/data/process_data.py
    deps:
      - data/raw/transactions.csv
      - src/data/process_data.py
    outs:
      - data/processed/clean_transactions.csv

  split_data:
    cmd: python src/data/split_data.py
    deps:
      - data/processed/clean_transactions.csv
      - src/data/split_data.py
    outs:
      - data/processed/train.csv
      - data/processed/test.csv

  train:
    cmd: python src/models/train.py
    deps:
      - data/processed/train.csv
      - src/models/train.py
    outs:
      - models/model.pkl
      - metrics.json

```

Updated dvc.yaml

Changes:

- move metrics.json from outs: -> metrics:
- declare cache: false under metrics

```yaml
stages:
  process_data:
    cmd: python src/data/process_data.py
    deps:
      - data/raw/transactions.csv
      - src/data/process_data.py
    outs:
      - data/processed/clean_transactions.csv

  split_data:
    cmd: python src/data/split_data.py
    deps:
      - data/processed/clean_transactions.csv
      - src/data/split_data.py
    outs:
      - data/processed/train.csv
      - data/processed/test.csv

  train:
    cmd: python src/models/train.py
    deps:
      - data/processed/train.csv
      - src/models/train.py
    outs:
      - models/model.pkl
    metrics:
      - metrics.json:
          cache: false

```

Navigate to project

```shell
cd /root/code/fraud-detection/
```

Re-run pipeline

```shell
dvc repro
```

Output

```shell
Running stage 'process_data':                                                       
> python src/data/process_data.py
Generating lock file 'dvc.lock'                                                     
Updating lock file 'dvc.lock'

Running stage 'split_data':                                                         
> python src/data/split_data.py
Updating lock file 'dvc.lock'                                                       

Running stage 'train':                                                              
> python src/models/train.py
Metrics: {'accuracy': 1.0, 'f1_score': 1.0}
Updating lock file 'dvc.lock'                                                       

To track the changes with git, run:

        git add models/.gitignore dvc.lock data/processed/.gitignore

To enable auto staging, run:

        dvc config core.autostage true
Use `dvc push` to send your updates to remote storage.
```

Run dvc metrics show

```shell
dvc metrics show
```

Output

```shell
Path          accuracy    f1_score
metrics.json  1.0         1.0
```

![Verify Screenshot](<../screenshots/Screenshot Day 16.png>)