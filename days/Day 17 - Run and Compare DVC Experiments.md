Prompt

The xFusionCorp Industries data science team compares multiple training runs with different hyperparameters using DVC experiments. Run three experiments that vary the `n_estimators`hyperparameter, identify the best-performing one, and promote it to the tracked workspace.


1. A project exists at `/root/code/fraud-detection/` with a parameterised DVC pipeline already in place. `params.yaml` contains `n_estimators: 100` and the baseline pipeline has been run once.
    
2. Run three DVC experiments, each with a different value for `n_estimators` across a reasonable range (for example `50`, `200`, and `500`). Each experiment should produce a fresh `metrics.json`.
    
3. Compare the experiments and choose the one whose `f1_score` is the highest.
    
4. Apply the chosen experiment to the workspace so its `n_estimators`, `metrics.json`, and `models/model.pkl`become the tracked state.
    

> The DVC extension's **EXPERIMENTS** section under the DVC view lists every experiment alongside its parameters and metrics, supports running fresh experiments through the `+` action, and applies a selected experiment to the workspace from the right-click menu—every operation in this lab can be performed either through the extension UI or with the equivalent `dvc exp` commands.

---

Solution

dvc.yaml (provided)

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
    params:
      - n_estimators
    outs:
      - models/model.pkl
    metrics:
      - metrics.json:
          cache: false

```

params.yaml (provided)

```yaml
n_estimators: 100

```

Navigate to working directory

```shell
cd /root/code/fraud-detection
```

Run first experiment

```shell
dvc exp run --set-param n_estimators=50
```

Run second experiment

```shell
dvc exp run --set-param n_estimators=200
```

Run third experiment

```shell
dvc exp run --set-param n_estimators=500
```

Check the experiments results

```shell
dvc exp show
```

Output

```shell
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  Experiment                 Created    accuracy   f1_score   n_estimators   data/processed/clean_transactions.csv   data/processed/train.csv           data/raw/transactions.csv          src/data/process_data.py           src/data/split_data.py             src/models/train.py               
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  workspace                  -              0.85       0.83   500            16ee9b988c5a51591382422b56e11960        142467e5074926d5eb5e7154aa456c25   262600809db02a8f3b97351c93c27784   20dd83528aa4f1c811acc1999f29b6e0   a8a5e02e0ea8627d58fa9454aa11e2e6   dbf36dea4d172da6c087a24fbadd5ba7  
  main                       04:33 AM          !          !   100            -                                       -                                  -                                  -                                  -                                  -                                 
  ├── 6bbaf98 [pseud-tiff]   04:46 AM       0.85       0.83   500            16ee9b988c5a51591382422b56e11960        142467e5074926d5eb5e7154aa456c25   262600809db02a8f3b97351c93c27784   20dd83528aa4f1c811acc1999f29b6e0   a8a5e02e0ea8627d58fa9454aa11e2e6   dbf36dea4d172da6c087a24fbadd5ba7  
  ├── e520bc9 [rummy-lahs]   04:46 AM       0.94       0.92   200            16ee9b988c5a51591382422b56e11960        142467e5074926d5eb5e7154aa456c25   262600809db02a8f3b97351c93c27784   20dd83528aa4f1c811acc1999f29b6e0   a8a5e02e0ea8627d58fa9454aa11e2e6   dbf36dea4d172da6c087a24fbadd5ba7  
  └── 145f7f5 [gamey-furl]   04:45 AM     0.9175     0.8975   50             16ee9b988c5a51591382422b56e11960        142467e5074926d5eb5e7154aa456c25   262600809db02a8f3b97351c93c27784   20dd83528aa4f1c811acc1999f29b6e0   a8a5e02e0ea8627d58fa9454aa11e2e6   dbf36dea4d172da6c087a24fbadd5ba7  
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
```

Apply winning experiment

```shell
dvc exp apply e520bc9
```

Output

```shell
Building workspace index                                                                                                 |3.00 [00:00,  825entry/s]
Comparing indexes                                                                                                       |8.00 [00:00, 4.35kentry/s]
Applying changes                                                                                                         |4.00 [00:00, 1.76kfile/s]
Changes for experiment 'e520bc9' have been applied to your current workspace.
```

Verify dvc apply

```shell
cat params.yaml
```

Output

```shell
n_estimators: 200
```

Verify dvc metrics

```shell
dvc metrics show
```

Output

```shell
Path          accuracy    f1_score
metrics.json  0.94        0.92
```

Screenshot of verification

![Screenshot](<../screenshots/Screenshot Day 17.png>)