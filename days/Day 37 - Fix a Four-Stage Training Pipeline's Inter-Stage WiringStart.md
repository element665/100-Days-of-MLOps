Prompt

The xFusionCorp Industries ML platform team operates a fraud-detection training process structured as a four-stage pipeline: preprocess, featurize, train, and evaluate. This pipeline is managed by a single Python script that consolidates the entire run into one MLflow execution. However, two critical issues need to be addressed.

First, the stage chain is incorrectly configured, resulting in two stages reading from the incorrect upstream source. As a consequence, the preprocess and featurize stages do not successfully transmit their outputs to the model, despite the pipeline indicating a successful run.

Second, the orchestrator currently fails to log the run; neither the pipeline's configuration nor its final metrics are recorded in MLflow.

Your task is to identify and rectify the miswiring in the stage chain and to enhance the orchestrator, ensuring that a single MLflow run accurately captures the parameters of the pipeline and its evaluation metrics.

  

1. The MLflow tracking server is already running on port `5000`. The **MLflow UI** button at the top of the lab can be opened to confirm—the dashboard loads with an empty `training-pipeline` experiment.
    
2. The project layout under `/root/code/fraud-detection/`:
    
    - `data/raw/train.csv` – The same 200-row synthetic binary-classification dataset the rest of the Training section uses (imbalanced roughly 70 / 30).
    - `configs/pipeline_config.yaml` – Declares the data paths, model hyperparameters, output paths, and MLflow settings every stage consumes. Correct and must remain intact.
    - `src/preprocess.py`, `src/featurize.py`, `src/train.py`, `src/evaluate.py` – The four pipeline stages. `preprocess.py` drops negligible-amount rows (`amount < 50`) and duplicates before writing the processed CSV. The four stages are wired through the config's `data:` paths.
    - `run_pipeline.py` – The orchestrator that executes the four stages in order under a single MLflow run. The stage-execution loop and fail-fast handling are wired; two tracking steps (logging the config parameters and the final metrics) are marked `TODO` for you to complete.
3. Run the orchestrator once against the scaffold as-is—`python run_pipeline.py`—then inspect the row counts of the intermediate CSVs under `data/` to see where the stage chain diverges (the pipeline reports success even though outputs do not flow through).
    
4. The end state must include:
    
    - The row count of `data/features/features.csv`equals the row count of `data/processed/train_clean.csv` and is strictly less than the 200-row raw CSV.
    - The training stage consumes the feature matrix — the engineered `amount_log` column produced by featurize is present in the training data (and in the persisted held-out set), not the pre-featurize processed data.
    - `models/model.pkl` and `reports/evaluation.json` are written and the report carries `accuracy`, `f1`, and `roc_auc` as numeric values.
    - Exactly one MLflow run exists in the `training-pipeline` experiment, carrying `params.model_type`, `params.n_estimators`, `params.max_depth`, and the three evaluation metrics.

---

**Original Lab Files**

[run_pipeline.py](<../assets/Day 37 - run_pipeline.py>)

[pipeline_config.yaml](<../assets/Day 37 - pipeline_config.yaml>)

[preprocess.py](<../assets/Day 37 - preprocess.py>)

[featurize.py](<../assets/Day 37 - featurize.py>)

[train.py](<../assets/Day 37 - train.py>)

[evaluate.py](<../assets/Day 37 - evaluate.py>)

---

Solution

Run orchestrator script once as-is per instructions

```shell
python run_pipeline.py
```

Output

```shell
[pipeline] running src/preprocess.py ...
[preprocess] raw_rows=200 -> processed_rows=192  (8 dropped)
[pipeline] running src/featurize.py ...
[featurize] input=data/raw/train.csv  rows=200  columns=5
[pipeline] running src/train.py ...
[train] rows=192  model_saved=models/model.pkl
[pipeline] running src/evaluate.py ...
[evaluate] metrics={'accuracy': 0.62069, 'f1': 0.421053, 'roc_auc': 0.559028}  report_saved=reports/evaluation.json
[pipeline] completed.
🏃 View run full-pipeline at: http://localhost:5000/#/experiments/1/runs/ea9c9e4774324c798c04e0e4037c2464
🧪 View experiment at: http://localhost:5000/#/experiments/1
```

- Fix wiring on pipeline stages

featurize.py correct input_path "raw_path" -> "processed_path"

Corrected line in featurize.py 

```python
input_path = config["data"]["processed_path"]
```

train.py correct features_path "processed_path" -> "features_path"

Corrected line in train.py

```python
features_path = config["data"]["features_path"]
```

featurize.py (Updated)

```python
"""Stage 2 — Featurize.

Reads the upstream stage's output, engineers one derived column
(`amount_log = log1p(amount)`), and writes the feature matrix to
`data/features/features.csv` for the training stage to consume.

Feature engineering, column preservation, and on-disk layout are all
in place. Like every stage in the pipeline, this one must read its
immediate predecessor's output so the stage-chain invariant holds —
the row count out of this stage should match the row count the
preprocess stage produced.
"""
import os

import numpy as np
import pandas as pd
import yaml

os.chdir("/root/code/fraud-detection")

with open("configs/pipeline_config.yaml") as f:
    config = yaml.safe_load(f)

input_path = config["data"]["processed_path"]
features_path = config["data"]["features_path"]

df = pd.read_csv(input_path)
df["amount_log"] = np.log1p(df["amount"])

os.makedirs(os.path.dirname(features_path), exist_ok=True)
df.to_csv(features_path, index=False)

print(
    f"[featurize] input={input_path}  rows={len(df)}  "
    f"columns={len(df.columns)}"
)
```

train.py (Updated)

```python
"""Stage 3 — Train.

Reads the feature matrix produced by the featurize stage, splits out
a stratified held-out test set (persisted to `data/features/test_set.csv`
so the evaluation stage scores on the same rows), fits a RandomForest
per the config, and writes the pickled model to `models/model.pkl`.

Like every stage in the pipeline, this one must read its immediate
predecessor's output — the engineered feature matrix — so the model is
trained on the featurized data, with the engineered columns present.
"""
import os

import joblib
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

os.chdir("/root/code/fraud-detection")

with open("configs/pipeline_config.yaml") as f:
    config = yaml.safe_load(f)

features_path = config["data"]["features_path"]
target = config["data"]["target_column"]
test_size = config["data"]["test_size"]
seed = config["data"]["random_state"]
model_path = config["output"]["model_path"]

df = pd.read_csv(features_path)
X = df.drop(columns=[target])
y = df[target]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=test_size, stratify=y, random_state=seed,
)

test_set_path = "data/features/test_set.csv"
X_test_df = X_test.copy()
X_test_df[target] = y_test
X_test_df.to_csv(test_set_path, index=False)

model = RandomForestClassifier(
    n_estimators=config["model"]["n_estimators"],
    max_depth=config["model"]["max_depth"],
    random_state=config["model"]["random_state"],
)
model.fit(X_train, y_train)

os.makedirs(os.path.dirname(model_path), exist_ok=True)
joblib.dump(model, model_path)

print(f"[train] rows={len(df)}  model_saved={model_path}")
```

- Complete both TODO sections on orchestrator script

run_pipeline.py (Final)

```python
"""Orchestrator — runs all four pipeline stages in order under a
single MLflow run, so one run captures the whole pipeline: its
configuration going in and its evaluation metrics coming out. This
imperative, MLflow-wrapped runner is what turns four independent
scripts into one tracked experiment.

The stage-execution loop and fail-fast handling are already wired.
Two tracking steps are left for you to complete — TODO 1 (log the
configuration as run parameters) and TODO 2 (log the final metrics).
Fails fast on the first non-zero stage exit.
"""
import json
import os
import subprocess
import sys

import mlflow
import yaml

os.chdir("/root/code/fraud-detection")

with open("configs/pipeline_config.yaml") as f:
    config = yaml.safe_load(f)

mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
mlflow.set_experiment(config["mlflow"]["experiment_name"])

STAGES = ["preprocess.py", "featurize.py", "train.py", "evaluate.py"]


def main():
    with mlflow.start_run(run_name="full-pipeline"):
        # TODO 1: capture the pipeline's configuration on this MLflow run so
        # the parameters live in the same run as the results. Log
        # config["model"]["type"] as the param "model_type",
        # config["model"]["n_estimators"] as "n_estimators", and
        # config["model"]["max_depth"] as "max_depth".
        
        mlflow.log_params({
            "model_type": config["model"]["type"],
            "n_estimators": config["model"]["n_estimators"],
            "max_depth": config["model"]["max_depth"],
        })

        for stage in STAGES:
            print(f"[pipeline] running src/{stage} ...")
            result = subprocess.run(
                [sys.executable, f"src/{stage}"],
                capture_output=True, text=True,
            )
            sys.stdout.write(result.stdout)
            if result.returncode != 0:
                sys.stderr.write(result.stderr)
                raise SystemExit(f"[pipeline] stage failed: {stage}")

        # TODO 2: the evaluate stage wrote its metrics to
        # config["output"]["report_path"] as a flat JSON dict. Read that file
        # and log every metric onto THIS run with mlflow.log_metric, so the
        # pipeline's final results are captured in the same run as its params.
        
        with open(config["output"]["report_path"]) as f:
	        metrics = json.load(f)
        
        for name, value in metrics.items():
	        mlflow.log_metric(name, value)

        mlflow.log_artifact(config["output"]["model_path"])
        print("[pipeline] completed.")


if __name__ == "__main__":
    main()
```

- Delete the original requested run to ensure only one run exists in MLflow UI

![Screenshot Delete Run](<../screenshots/Screenshot Day 37 delete run.png>)

Run the final run_pipeline.py with corrected stages

```shell
python run_pipeline.py
```

Output

```shell
[pipeline] running src/preprocess.py ...
[preprocess] raw_rows=200 -> processed_rows=192  (8 dropped)
[pipeline] running src/featurize.py ...
[featurize] input=data/processed/train_clean.csv  rows=192  columns=5
[pipeline] running src/train.py ...
[train] rows=192  model_saved=models/model.pkl
[pipeline] running src/evaluate.py ...
[evaluate] metrics={'accuracy': 0.637931, 'f1': 0.461538, 'roc_auc': 0.595139}  report_saved=reports/evaluation.json
[pipeline] completed.
🏃 View run full-pipeline at: http://localhost:5000/#/experiments/1/runs/f841d9691a174dc3822b27df2b41925b
🧪 View experiment at: http://localhost:5000/#/experiments/1
```

**MLflow UI Verification**

Confirm exactly one run exists in MLflow UI

![Screenshot Runs](<../screenshots/Screenshot Day 37 runs.png>)

Confirm run includes three evaluation metrics required ("model_type", "n_estimators", "max_depth" )

![Screenshot Run Details](<../screenshots/Screenshot Day 37 run details.png>)

**Additional Verification**

Check feature matrix for "amount_log" column

```shell
head -n 2 data/features/features.csv
```

Output

```shell
amount,hour,num_tx_past_day,is_fraud,amount_log
380.79,23,3,0,5.944870719225222
```

Check row numbers match and under 200 rows in processed and original files

```shell
wc -l data/processed/train_clean.csv data/features/features.csv
```

Output

```shell
 193 data/processed/train_clean.csv
 193 data/features/features.csv
 386 total
```

---

***Failed 1st Attempt

Lab Failure Report:

```
featurize.py is not reading from `config["data"]["processed_path"]`. As wired, the stage consumes the raw CSV and the preprocess stage's output is ignored. for full solution please refer to https://github.com/kodekloudhub/100-days-of-mlops-solutions
```

### Lesson Learned

My first attempt focused too narrowly on the two `TODO` sections in
`run_pipeline.py`. I correctly left `pipeline_config.yaml` unchanged because
the lab explicitly stated that it was correct and must remain intact.

The mistake was assuming that the TODOs represented the complete set of
required code changes. The lab also instructed me to run the pipeline as-is
and inspect the intermediate outputs to identify where the stage chain
diverged.

The row counts revealed that `featurize.py` was reading the raw dataset
instead of the output from `preprocess.py`. Inspecting the stage scripts then
revealed a second wiring problem: `train.py` was reading the processed data
instead of the feature matrix produced by `featurize.py`.

The key lesson is that when debugging a multi-stage pipeline, don't assume
that the explicitly marked TODOs are the only problems to solve. Use the
pipeline's observed behavior and its stated invariants to trace the complete
data flow through each stage.

For this pipeline, the expected contract is:

raw → preprocess → processed → featurize → features → train → model → evaluate

Each stage should consume the output of its immediate predecessor, while
the configuration remains the source of truth for the paths.