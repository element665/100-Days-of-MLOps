Prompt

The xFusionCorp Industries ML platform team maintains a configuration-driven training pipeline that allows for hyperparameter adjustments without the need to modify Python code. A training scaffold is located at `/root/code/fraud-detection/`, with the trainer already set up. However, the YAML configuration is currently in a broken state, preventing the pipeline from running successfully. Your objective is to rectify the configuration so that one successful training run is recorded on the MLflow tracking server, and the trained model is saved within the project tree.

  

1. The MLflow tracking server is already running on port `5000`. The **MLflow UI** button at the top of the lab can be opened to confirm—the dashboard loads with an empty `fraud-detection` experiment already in place.
    
2. The project layout under `/root/code/fraud-detection/`:
    
    - `data/train.csv` – A pre-generated 200-row synthetic binary classification dataset (columns: `amount`, `hour`, `num_tx_past_day`, `is_fraud`).
    - `src/models/train.py` – The config-driven trainer. This file is correct and must not be modified.
    - `configs/train_config.yaml` – The project's training configuration.
    - `models/` – Where the serialised model must land.
3. Run the trainer once against the scaffold as-is—`python src/models/train.py`—to see how it currently fails.
    
4. The end state must include:
    
    - A successful training run printed to stdout.
    - Exactly one new MLflow run in the `fraud-detection` experiment, with the estimator's hyperparameters logged as run parameters.
    - A serialised model at `/root/code/fraud-detection/models/model.pkl` (absolute path, inside the project tree).

---

Solution

[train.py](<../assets/Day 31 - train.py>) (do not modify for lab)

![Screenshot start](<../screenshots/Screenshot Day 31 start.png>)

train_config.yaml (Original)

```yaml
model:
  type: RandomForest
  n_estimators: 100
  max_depth: 5
  random_state: 42
data:
  train_path: /root/code/fraud-detection/data/train.csv
  target_column: target
output:
  model_path: /root/code/model.pkl
mlflow:
  tracking_uri: http://localhost:5000
  experiment_name: fraud-detection
```

Run trainer to see failure as instructed

```shell
python src/models/train.py
```

Output

```shell
ERROR: unknown estimator type 'RandomForest'. Supported: ['GradientBoostingClassifier', 'LogisticRegression', 'RandomForestClassifier']
```

Update train_config.yaml
- model type should be 'RandomForestClassifier'
- model_path should be '/root/code/fraud-detection/models/model.pkl'

train_config.yaml (Final)

```yaml
model:
  type: RandomForestClassifier
  n_estimators: 100
  max_depth: 5
  random_state: 42
data:
  train_path: /root/code/fraud-detection/data/train.csv
  target_column: is_fraud
output:
  model_path: /root/code/fraud-detection/models/model.pkl
mlflow:
  tracking_uri: http://localhost:5000
  experiment_name: fraud-detection
```

Run trainer again 

```shell
python src/models/train.py
```

Output

```shell
2026/08/05 09:55:55 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
accuracy=0.8000, f1_score=0.8261
model saved to /root/code/fraud-detection/models/model.pkl
🏃 View run carefree-fish-470 at: http://localhost:5000/#/experiments/1/runs/009233da416b43ea82476b08d31a4684
🧪 View experiment at: http://localhost:5000/#/experiments/1
```

![Screenshot verify one run in MLflow UI](<../screenshots/Screenshot Day 31 final.png>)
