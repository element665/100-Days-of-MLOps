Prompt

The xFusionCorp Industries ML platform team has developed a comprehensive fraud-detection training pipeline that includes data validation, Optuna tuning across two model families, model selection against a release threshold, Model Registry registration with a release-lane alias, and a consolidated training report. All of these components are integrated behind a single `make train-pipeline` command. Currently, the pre-staged system does not function end-to-end, as each invocation of `make train-pipeline` reveals a wiring issue, and two stages contain unfinished TODO items. To prepare for the release checklist, you must address the necessary updates in the `Makefile`, `src/select_model.py`, `src/register.py`, and `src/report.py`. Your objective is to resolve the wiring issues and complete the two TODO blocks, ensuring that `make train-pipeline` executes successfully from start to finish, the MLflow Model Registry contains a `fraud-detector` version under the `staging` alias, and `reports/training_report.json` compiles all upstream artifacts.

  

1. The MLflow tracking server is already running on port `5000`. The **MLflow UI** button at the top of the lab can be opened to confirm—the dashboard loads with an empty `fraud-detection-tuning` experiment.
    
2. The project layout under `/root/code/fraud-detection/`:
    
    - `data/train.csv` – The 200-row synthetic binary-classification dataset the rest of the Training section uses.
    - `src/validate_data.py` – Schema + null-check gate. Writes `reports/validation_status.json`. Correct.
    - `src/tune.py` – Runs 10 Optuna trials across RandomForest and GradientBoosting, each logged as an MLflow run tagged with `model_type` + `params.{n_estimators,max_depth}` + `metrics.f1_score` + the fitted model artefact. Correct.
    - `src/select_model.py` – Picks the winning run by the training metric and writes `reports/selection.json`. Has a wiring bug.
    - `src/register.py` – Registers the selected run's model as `fraud-detector`; the release-lane alias assignment is left as a `# TODO`.
    - `src/report.py` – Aggregates every upstream artefact into `reports/training_report.json`; the report assembly is left as a `# TODO`.
    - `Makefile` – `train-pipeline` target runs the five stages in order. Has a wiring bug.
3. The end state must include:
    
    - `make train-pipeline` completes without non-zero exit.
    - The `fraud-detection-tuning` MLflow experiment carries at least five trial runs, each with `metrics.f1_score`.
    - `reports/selection.json`, `reports/validation_status.json`, and `reports/training_report.json` are all present. The training report carries `best_model`, `best_params`, `metrics`, `total_trials`, and `validation_status` keys; `validation_status`is `"ok"` and `total_trials` is an integer ≥ 5.
    - The MLflow Model Registry (**MLflow UI** → **Models**) shows a `fraud-detector` registered model with at least one version. That version carries the `staging` alias and no `production`alias.

> Run `make train-pipeline` once against the scaffold as-is — the first wiring bug surfaces immediately, and each re-run reveals the next. The two `# TODO` blocks (the registry alias and the report assembly) do not crash the pipeline; they are caught by the release checklist, so complete them before expecting a clean pass.

---

Solution

**Provided Files

[validate_data.py](<../assets/Day 40 - validate_data.py>)

[tune.py](<../assets/Day 40 - tune.py>)

Makefile (Original)

```shell
.PHONY: train-pipeline clean

# xFusionCorp Industries — Fraud Detection Training Pipeline.
# Usage: make train-pipeline

train-pipeline:
	python3 src/validate_data.py
	python3 src/select_model.py
	python3 src/tune.py
	python3 src/register.py
	python3 src/report.py

clean:
	rm -rf models/ reports/
```

select_model.py (Original)

```python
"""Stage 3 — Model selection.

Reads every run in the `fraud-detection-tuning` experiment, picks
the best candidate by the training metric, validates it against the
release threshold, and persists the selection to
`reports/selection.json` for the register stage.
"""
import json
import os
import sys

import mlflow

TRACKING_URI = "http://localhost:5000"
EXPERIMENT = "fraud-detection-tuning"
REPORTS_DIR = "/root/code/fraud-detection/reports"
SELECTION_JSON = os.path.join(REPORTS_DIR, "selection.json")

RELEASE_THRESHOLD = 0.4


def main():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = mlflow.MlflowClient()
    exp = client.get_experiment_by_name(EXPERIMENT)
    if exp is None:
        sys.exit(f"[select] experiment {EXPERIMENT!r} not found.")

    runs = mlflow.search_runs(
        experiment_ids=[exp.experiment_id],
        order_by=["metrics.accuracy DESC"],
        max_results=200,
    )
    if runs.empty:
        sys.exit(
            f"[select] no runs in experiment {EXPERIMENT!r} — the tune "
            "stage has not produced any candidates yet."
        )

    best = runs.iloc[0]
    score = float(best["metrics.accuracy"])
    if score < RELEASE_THRESHOLD:
        sys.exit(
            f"[select] best candidate ({score:.4f}) is below the "
            f"release threshold ({RELEASE_THRESHOLD})."
        )

    selection = {
        "run_id": best["run_id"],
        "model_type": best.get("tags.model_type", ""),
        "f1_score": score,
    }
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(SELECTION_JSON, "w") as f:
        json.dump(selection, f, indent=2)
    print(f"[select] {selection}")


if __name__ == "__main__":
    main()
```

register.py (Original)

```python
"""Stage 4 — Register the selected model.

Reads the selection written by the previous stage, registers the
selected run's model as `fraud-detector` in the MLflow Model
Registry, and assigns the release-lane alias so the serving layer
can fetch the right version by name.
"""
import json
import os
import sys

import mlflow
from mlflow.tracking import MlflowClient

TRACKING_URI = "http://localhost:5000"
REPORTS_DIR = "/root/code/fraud-detection/reports"
SELECTION_JSON = os.path.join(REPORTS_DIR, "selection.json")

REGISTERED_MODEL_NAME = "fraud-detector"
# The release-lane alias the serving layer resolves by name. Per the
# release checklist, models promoted by this pipeline go to "staging".
RELEASE_ALIAS = "staging"


def main():
    if not os.path.exists(SELECTION_JSON):
        sys.exit(
            f"[register] {SELECTION_JSON} missing — the select stage "
            "has not produced a selection yet."
        )
    with open(SELECTION_JSON) as f:
        selection = json.load(f)

    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()

    model_uri = f"runs:/{selection['run_id']}/model"
    version = mlflow.register_model(model_uri, REGISTERED_MODEL_NAME)

    # TODO: assign the release-lane alias so the serving layer can fetch
    # this version by name. Point RELEASE_ALIAS at the just-registered
    # version using client.set_registered_model_alias(name, alias,
    # version) — pass REGISTERED_MODEL_NAME, RELEASE_ALIAS, and
    # version.version.

    print(
        f"[register] {REGISTERED_MODEL_NAME} v{version.version} "
        f"registered (assign the {RELEASE_ALIAS!r} alias in the TODO)"
    )


if __name__ == "__main__":
    main()
```

report.py (Original)

```python
"""Stage 5 — Training report.

Aggregates every upstream stage's output into a single JSON report
at `reports/training_report.json`. Reads:
  - `reports/validation_status.json` produced by the validate stage.
  - `reports/selection.json` produced by the select stage.
  - the MLflow experiment's run count for the total trials figure.
"""
import json
import os

import mlflow

TRACKING_URI = "http://localhost:5000"
EXPERIMENT = "fraud-detection-tuning"
REPORTS_DIR = "/root/code/fraud-detection/reports"

VALIDATION_JSON = os.path.join(REPORTS_DIR, "validation_status.json")
SELECTION_JSON = os.path.join(REPORTS_DIR, "selection.json")
TRAINING_REPORT_JSON = os.path.join(REPORTS_DIR, "training_report.json")


def main():
    with open(VALIDATION_JSON) as f:
        validation = json.load(f)
    with open(SELECTION_JSON) as f:
        selection = json.load(f)

    mlflow.set_tracking_uri(TRACKING_URI)
    client = mlflow.MlflowClient()
    exp = client.get_experiment_by_name(EXPERIMENT)
    runs = mlflow.search_runs([exp.experiment_id], max_results=500) if exp else []
    total_trials = int(len(runs)) if hasattr(runs, "__len__") else 0

    run_id = selection["run_id"]
    client = mlflow.MlflowClient()
    run = client.get_run(run_id)
    best_params = {k: v for k, v in run.data.params.items()}
    best_metrics = {k: float(v) for k, v in run.data.metrics.items()}

    # TODO: assemble the consolidated training report from the upstream
    # artefacts gathered above. Build a dict with exactly these five keys
    # and bind it to `report`:
    #   "best_model"        -> selection's model_type (selection["model_type"])
    #   "best_params"       -> best_params
    #   "metrics"           -> best_metrics
    #   "total_trials"      -> total_trials
    #   "validation_status" -> validation's status (validation["status"])
    report = {}

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(TRAINING_REPORT_JSON, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[report] {TRAINING_REPORT_JSON}")


if __name__ == "__main__":
    main()
```

Run `make train-pipeline` once against the scaffold as-is per instructions

```shell
make train-pipeline
```

Output

```shell
python3 src/validate_data.py
[validate] {'status': 'ok', 'rows': 200, 'columns': ['amount', 'hour', 'num_tx_past_day', 'is_fraud']}
python3 src/select_model.py
[select] no runs in experiment 'fraud-detection-tuning' — the tune stage has not produced any candidates yet.
make: *** [Makefile:8: train-pipeline] Error 1
```

- First error shows Makefile is wired out of order

Makefile corrected order

```shell
train-pipeline:
	python3 src/validate_data.py (1st)
	python3 src/tune.py          (2nd)
	python3 src/select_model.py  (3rd)
	python3 src/register.py      (4th)
	python3 src/report.py        (5th)
```

Run Makefile again to see new output

```shell
make train-pipeline
```

Output

```shell
python3 src/validate_data.py
[validate] {'status': 'ok', 'rows': 200, 'columns': ['amount', 'hour', 'num_tx_past_day', 'is_fraud']}
python3 src/tune.py
[I 2026-09-01 08:45:22,617] A new study created in memory with name: fraud-detection-tuning
2026/09/01 08:45:36 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-0 at: http://localhost:5000/#/experiments/1/runs/4a160b797077442bac57231e0c14d2fa
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:45:36,557] Trial 0 finished with value: 0.36132756132756133 and parameters: {'model_type': 'GradientBoosting', 'n_estimators': 160, 'max_depth': 7}. Best is trial 0 with value: 0.36132756132756133.
2026/09/01 08:45:44 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-1 at: http://localhost:5000/#/experiments/1/runs/0c6d5e77c5e041c2a2ec412fef345b5b
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:45:44,205] Trial 1 finished with value: 0.43796296296296294 and parameters: {'model_type': 'RandomForest', 'n_estimators': 58, 'max_depth': 9}. Best is trial 1 with value: 0.43796296296296294.
2026/09/01 08:45:52 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-2 at: http://localhost:5000/#/experiments/1/runs/669484a80e2042189a8c5f6bb7817f64
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:45:52,275] Trial 2 finished with value: 0.34562289562289567 and parameters: {'model_type': 'GradientBoosting', 'n_estimators': 53, 'max_depth': 10}. Best is trial 1 with value: 0.43796296296296294.
2026/09/01 08:45:59 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-3 at: http://localhost:5000/#/experiments/1/runs/306a04dea42c4055bc8abdc38d36df75
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:45:59,905] Trial 3 finished with value: 0.41497637666992504 and parameters: {'model_type': 'RandomForest', 'n_estimators': 77, 'max_depth': 4}. Best is trial 1 with value: 0.43796296296296294.
2026/09/01 08:46:07 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-4 at: http://localhost:5000/#/experiments/1/runs/030cfd17269a4e0aa5ec675a57bdcb9b
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:46:07,951] Trial 4 finished with value: 0.42015098722415795 and parameters: {'model_type': 'GradientBoosting', 'n_estimators': 115, 'max_depth': 5}. Best is trial 1 with value: 0.43796296296296294.
2026/09/01 08:46:15 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-5 at: http://localhost:5000/#/experiments/1/runs/011555529d404bc6ac3f69e532638d88
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:46:15,970] Trial 5 finished with value: 0.4653417818740399 and parameters: {'model_type': 'RandomForest', 'n_estimators': 94, 'max_depth': 5}. Best is trial 5 with value: 0.4653417818740399.
2026/09/01 08:46:23 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-6 at: http://localhost:5000/#/experiments/1/runs/8b18a3f1d0bd40ab9fac24e6f018b4c6
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:46:24,011] Trial 6 finished with value: 0.3728682170542636 and parameters: {'model_type': 'GradientBoosting', 'n_estimators': 80, 'max_depth': 7}. Best is trial 5 with value: 0.4653417818740399.
2026/09/01 08:46:32 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-7 at: http://localhost:5000/#/experiments/1/runs/6b7648d51321482183555d11ddc28dde
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:46:32,349] Trial 7 finished with value: 0.432449494949495 and parameters: {'model_type': 'RandomForest', 'n_estimators': 141, 'max_depth': 4}. Best is trial 5 with value: 0.4653417818740399.
2026/09/01 08:46:41 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-8 at: http://localhost:5000/#/experiments/1/runs/2e68741016ac47d194060ce1ded4961e
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:46:41,410] Trial 8 finished with value: 0.33145407564012214 and parameters: {'model_type': 'GradientBoosting', 'n_estimators': 195, 'max_depth': 9}. Best is trial 5 with value: 0.4653417818740399.
2026/09/01 08:46:49 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-9 at: http://localhost:5000/#/experiments/1/runs/a3516f07e8e241758e2e9fc6386603ec
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:46:49,571] Trial 9 finished with value: 0.444990444990445 and parameters: {'model_type': 'RandomForest', 'n_estimators': 153, 'max_depth': 6}. Best is trial 5 with value: 0.4653417818740399.
[tune] 10 trials complete. best_value=0.4653  best_params={'model_type': 'RandomForest', 'n_estimators': 94, 'max_depth': 5}
python3 src/select_model.py
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/dist-packages/pandas/core/indexes/base.py", line 3812, in get_loc
    return self._engine.get_loc(casted_key)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "pandas/_libs/index.pyx", line 167, in pandas._libs.index.IndexEngine.get_loc
  File "pandas/_libs/index.pyx", line 196, in pandas._libs.index.IndexEngine.get_loc
  File "pandas/_libs/hashtable_class_helper.pxi", line 7088, in pandas._libs.hashtable.PyObjectHashTable.get_item
  File "pandas/_libs/hashtable_class_helper.pxi", line 7096, in pandas._libs.hashtable.PyObjectHashTable.get_item
KeyError: 'metrics.accuracy'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/root/code/fraud-detection/src/select_model.py", line 60, in <module>
    main()
  File "/root/code/fraud-detection/src/select_model.py", line 41, in main
    score = float(best["metrics.accuracy"])
                  ~~~~^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/pandas/core/series.py", line 1133, in __getitem__
    return self._get_value(key)
           ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/pandas/core/series.py", line 1249, in _get_value
    loc = self.index.get_loc(label)
          ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/pandas/core/indexes/base.py", line 3819, in get_loc
    raise KeyError(key) from err
KeyError: 'metrics.accuracy'
make: *** [Makefile:9: train-pipeline] Error 1
```

Second error shows issue with select_model.py using 'metrics.accuracy' instead of 'metrics.f1_score'

select_model.py updates

```python
    runs = mlflow.search_runs(
        experiment_ids=[exp.experiment_id],
        order_by=["metrics.f1_score DESC"],
        max_results=200,
    )

    score = float(best["metrics.f1_score"])
```

Run Makefile again to see new output

```shell
make train-pipeline
```

Output

```shell
python3 src/validate_data.py
[validate] {'status': 'ok', 'rows': 200, 'columns': ['amount', 'hour', 'num_tx_past_day', 'is_fraud']}
python3 src/tune.py
[I 2026-09-01 08:49:06,199] A new study created in memory with name: fraud-detection-tuning
2026/09/01 08:49:19 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-0 at: http://localhost:5000/#/experiments/1/runs/81ab0ca219ed434a93d2c462879f0b9d
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:49:19,834] Trial 0 finished with value: 0.36132756132756133 and parameters: {'model_type': 'GradientBoosting', 'n_estimators': 160, 'max_depth': 7}. Best is trial 0 with value: 0.36132756132756133.
2026/09/01 08:49:27 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-1 at: http://localhost:5000/#/experiments/1/runs/d598ce9cc9194c8d99260e37c9902b0a
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:49:27,367] Trial 1 finished with value: 0.43796296296296294 and parameters: {'model_type': 'RandomForest', 'n_estimators': 58, 'max_depth': 9}. Best is trial 1 with value: 0.43796296296296294.
2026/09/01 08:49:34 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-2 at: http://localhost:5000/#/experiments/1/runs/b564b6fe346a4356bd8541643d40e27f
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:49:35,041] Trial 2 finished with value: 0.34562289562289567 and parameters: {'model_type': 'GradientBoosting', 'n_estimators': 53, 'max_depth': 10}. Best is trial 1 with value: 0.43796296296296294.
2026/09/01 08:49:42 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-3 at: http://localhost:5000/#/experiments/1/runs/9363d9081d0d4e54a765600b983c38f6
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:49:42,598] Trial 3 finished with value: 0.41497637666992504 and parameters: {'model_type': 'RandomForest', 'n_estimators': 77, 'max_depth': 4}. Best is trial 1 with value: 0.43796296296296294.
2026/09/01 08:49:50 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-4 at: http://localhost:5000/#/experiments/1/runs/2a962df6f1f24020a13f6d1c856336e7
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:49:50,218] Trial 4 finished with value: 0.42015098722415795 and parameters: {'model_type': 'GradientBoosting', 'n_estimators': 115, 'max_depth': 5}. Best is trial 1 with value: 0.43796296296296294.
2026/09/01 08:49:57 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-5 at: http://localhost:5000/#/experiments/1/runs/ea72dbf4b78a4a918d04800aa558d395
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:49:58,027] Trial 5 finished with value: 0.4653417818740399 and parameters: {'model_type': 'RandomForest', 'n_estimators': 94, 'max_depth': 5}. Best is trial 5 with value: 0.4653417818740399.
2026/09/01 08:50:05 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-6 at: http://localhost:5000/#/experiments/1/runs/43b7937de91e4dbaad3e486171988ed5
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:50:05,679] Trial 6 finished with value: 0.3728682170542636 and parameters: {'model_type': 'GradientBoosting', 'n_estimators': 80, 'max_depth': 7}. Best is trial 5 with value: 0.4653417818740399.
2026/09/01 08:50:13 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-7 at: http://localhost:5000/#/experiments/1/runs/ab564199916b494aba958ccb3138fa89
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:50:13,816] Trial 7 finished with value: 0.432449494949495 and parameters: {'model_type': 'RandomForest', 'n_estimators': 141, 'max_depth': 4}. Best is trial 5 with value: 0.4653417818740399.
2026/09/01 08:50:22 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-8 at: http://localhost:5000/#/experiments/1/runs/53b2e46e499c40229479fd7eb99969c7
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:50:22,914] Trial 8 finished with value: 0.33145407564012214 and parameters: {'model_type': 'GradientBoosting', 'n_estimators': 195, 'max_depth': 9}. Best is trial 5 with value: 0.4653417818740399.
2026/09/01 08:50:30 WARNING mlflow.utils.requirements_utils: Found torch version (2.12.1+cpu) contains a local version label (+cpu). MLflow logged a pip requirement for this package as 'torch==2.12.1' without the local version label to make it installable from PyPI. To specify pip requirements containing local version labels, please use `conda_env` or `pip_requirements`.
🏃 View run trial-9 at: http://localhost:5000/#/experiments/1/runs/b38532ee936e4ebb88b988b3810a1d35
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-09-01 08:50:31,031] Trial 9 finished with value: 0.444990444990445 and parameters: {'model_type': 'RandomForest', 'n_estimators': 153, 'max_depth': 6}. Best is trial 5 with value: 0.4653417818740399.
[tune] 10 trials complete. best_value=0.4653  best_params={'model_type': 'RandomForest', 'n_estimators': 94, 'max_depth': 5}
python3 src/select_model.py
[select] {'run_id': 'ea72dbf4b78a4a918d04800aa558d395', 'model_type': 'RandomForest', 'f1_score': 0.4653417818740399}
python3 src/register.py
Successfully registered model 'fraud-detector'.
2026/09/01 08:50:35 WARNING mlflow.tracking._model_registry.fluent: Run with id ea72dbf4b78a4a918d04800aa558d395 has no artifacts at artifact path 'model', registering model based on models:/m-ff6d2becc1ac4976bc5f392ff710f626 instead
2026/09/01 08:50:35 INFO mlflow.store.model_registry.abstract_store: Waiting up to 300 seconds for model version to finish creation. Model name: fraud-detector, version 1
Created version '1' of model 'fraud-detector'.
[register] fraud-detector v1 registered (assign the 'staging' alias in the TODO)
python3 src/report.py
[report] /root/code/fraud-detection/reports/training_report.json
```

Complete TODO section in register.py 

```python
    # TODO: assign the release-lane alias so the serving layer can fetch
    # this version by name. Point RELEASE_ALIAS at the just-registered
    # version using client.set_registered_model_alias(name, alias,
    # version) — pass REGISTERED_MODEL_NAME, RELEASE_ALIAS, and
    # version.version.

	client.set_registered_model_alias(
		REGISTERED_MODEL_NAME, 
		RELEASE_ALIAS, 
		version.version
	)


    print(
        f"[register] {REGISTERED_MODEL_NAME} v{version.version} "
        f"registered (assign the {RELEASE_ALIAS!r} alias in the TODO)"
    )


if __name__ == "__main__":
    main()
```

Run Makefile again to see new output

```shell
make train-pipeline
```

Output

```shell
[tune] 10 trials complete. best_value=0.4653  best_params={'model_type': 'RandomForest', 'n_estimators': 94, 'max_depth': 5}
python3 src/select_model.py
[select] {'run_id': 'a27ea4d0015348d2b543532b561ab12e', 'model_type': 'RandomForest', 'f1_score': 0.4653417818740399}
python3 src/register.py
Registered model 'fraud-detector' already exists. Creating a new version of this model...
2026/09/01 08:55:23 WARNING mlflow.tracking._model_registry.fluent: Run with id a27ea4d0015348d2b543532b561ab12e has no artifacts at artifact path 'model', registering model based on models:/m-8fb54622d65d4e0babf450ff542e4e3e instead
2026/09/01 08:55:23 INFO mlflow.store.model_registry.abstract_store: Waiting up to 300 seconds for model version to finish creation. Model name: fraud-detector, version 2
Created version '2' of model 'fraud-detector'.
[register] fraud-detector v2 registered (assign the 'staging' alias in the TODO)
python3 src/report.py
[report] /root/code/fraud-detection/reports/training_report.json
```

Complete TODO section in report.py 

```python
    # TODO: assemble the consolidated training report from the upstream
    # artefacts gathered above. Build a dict with exactly these five keys
    # and bind it to `report`:
    #   "best_model"        -> selection's model_type (selection["model_type"])
    #   "best_params"       -> best_params
    #   "metrics"           -> best_metrics
    #   "total_trials"      -> total_trials
    #   "validation_status" -> validation's status (validation["status"])
    report = {
	    "best_model": selection["model_type"],
	    "best_params": best_params,
	    "metrics": best_metrics,
	    "total_trials": total_trials,
	    "validation_status": validation["status"],
    }
    
```

Run Makefile again to see new output

```shell
make train-pipeline
```

Output

```shell
[I 2026-09-01 09:16:18,273] Trial 9 finished with value: 0.444990444990445 and parameters: {'model_type': 'RandomForest', 'n_estimators': 153, 'max_depth': 6}. Best is trial 5 with value: 0.4653417818740399.
[tune] 10 trials complete. best_value=0.4653  best_params={'model_type': 'RandomForest', 'n_estimators': 94, 'max_depth': 5}
python3 src/select_model.py
[select] {'run_id': '97bf03a29dec42f58b582c957e94a57e', 'model_type': 'RandomForest', 'f1_score': 0.4653417818740399}
python3 src/register.py
Registered model 'fraud-detector' already exists. Creating a new version of this model...
2026/09/01 09:16:22 WARNING mlflow.tracking._model_registry.fluent: Run with id 97bf03a29dec42f58b582c957e94a57e has no artifacts at artifact path 'model', registering model based on models:/m-3b04414dcaae4a4cbc19aa78e2719772 instead
2026/09/01 09:16:22 INFO mlflow.store.model_registry.abstract_store: Waiting up to 300 seconds for model version to finish creation. Model name: fraud-detector, version 3
Created version '3' of model 'fraud-detector'.
[register] fraud-detector v3 registered (assign the 'staging' alias in the TODO)
python3 src/report.py
[report] /root/code/fraud-detection/reports/training_report.json
```



**Verification

Check 'make train-pipeline' exit code after run

```shell
make train-pipeline
echo $?
```

Output

```shell
0
```

Screenshot of MLflow UI 'fraud-detection-tuning' trial runs

![trial runs](<../screenshots/Screenshot Day 40 runs.png>)

Screenshot of reports/ and training_report.json contents

![reports](<../screenshots/Screenshot Day 40 reports.png>)

Screenshot of MLflow UI registered models

![registered models](<../screenshots/Screenshot Day 40 registered models.png>)


---

Makefile (Final)

```shell
.PHONY: train-pipeline clean

# xFusionCorp Industries — Fraud Detection Training Pipeline.
# Usage: make train-pipeline

train-pipeline:
	python3 src/validate_data.py
	python3 src/tune.py
	python3 src/select_model.py
	python3 src/register.py
	python3 src/report.py

clean:
	rm -rf models/ reports/
```

select_model.py (Final)

```python
"""Stage 3 — Model selection.

Reads every run in the `fraud-detection-tuning` experiment, picks
the best candidate by the training metric, validates it against the
release threshold, and persists the selection to
`reports/selection.json` for the register stage.
"""
import json
import os
import sys

import mlflow

TRACKING_URI = "http://localhost:5000"
EXPERIMENT = "fraud-detection-tuning"
REPORTS_DIR = "/root/code/fraud-detection/reports"
SELECTION_JSON = os.path.join(REPORTS_DIR, "selection.json")

RELEASE_THRESHOLD = 0.4


def main():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = mlflow.MlflowClient()
    exp = client.get_experiment_by_name(EXPERIMENT)
    if exp is None:
        sys.exit(f"[select] experiment {EXPERIMENT!r} not found.")

    runs = mlflow.search_runs(
        experiment_ids=[exp.experiment_id],
        order_by=["metrics.f1_score DESC"],
        max_results=200,
    )
    if runs.empty:
        sys.exit(
            f"[select] no runs in experiment {EXPERIMENT!r} — the tune "
            "stage has not produced any candidates yet."
        )

    best = runs.iloc[0]
    score = float(best["metrics.f1_score"])
    if score < RELEASE_THRESHOLD:
        sys.exit(
            f"[select] best candidate ({score:.4f}) is below the "
            f"release threshold ({RELEASE_THRESHOLD})."
        )

    selection = {
        "run_id": best["run_id"],
        "model_type": best.get("tags.model_type", ""),
        "f1_score": score,
    }
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(SELECTION_JSON, "w") as f:
        json.dump(selection, f, indent=2)
    print(f"[select] {selection}")


if __name__ == "__main__":
    main()
```

register.py (Final)

```python
"""Stage 4 — Register the selected model.

Reads the selection written by the previous stage, registers the
selected run's model as `fraud-detector` in the MLflow Model
Registry, and assigns the release-lane alias so the serving layer
can fetch the right version by name.
"""
import json
import os
import sys

import mlflow
from mlflow.tracking import MlflowClient

TRACKING_URI = "http://localhost:5000"
REPORTS_DIR = "/root/code/fraud-detection/reports"
SELECTION_JSON = os.path.join(REPORTS_DIR, "selection.json")

REGISTERED_MODEL_NAME = "fraud-detector"
# The release-lane alias the serving layer resolves by name. Per the
# release checklist, models promoted by this pipeline go to "staging".
RELEASE_ALIAS = "staging"


def main():
    if not os.path.exists(SELECTION_JSON):
        sys.exit(
            f"[register] {SELECTION_JSON} missing — the select stage "
            "has not produced a selection yet."
        )
    with open(SELECTION_JSON) as f:
        selection = json.load(f)

    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()

    model_uri = f"runs:/{selection['run_id']}/model"
    version = mlflow.register_model(model_uri, REGISTERED_MODEL_NAME)

    # TODO: assign the release-lane alias so the serving layer can fetch
    # this version by name. Point RELEASE_ALIAS at the just-registered
    # version using client.set_registered_model_alias(name, alias,
    # version) — pass REGISTERED_MODEL_NAME, RELEASE_ALIAS, and
    # version.version.

    client.set_registered_model_alias(
        REGISTERED_MODEL_NAME, 
        RELEASE_ALIAS,
        version.version
        )

    print(
        f"[register] {REGISTERED_MODEL_NAME} v{version.version} "
        f"registered (assign the {RELEASE_ALIAS!r} alias in the TODO)"
    )


if __name__ == "__main__":
    main()
```

report.py (Final)

```python
"""Stage 5 — Training report.

Aggregates every upstream stage's output into a single JSON report
at `reports/training_report.json`. Reads:
  - `reports/validation_status.json` produced by the validate stage.
  - `reports/selection.json` produced by the select stage.
  - the MLflow experiment's run count for the total trials figure.
"""
import json
import os

import mlflow

TRACKING_URI = "http://localhost:5000"
EXPERIMENT = "fraud-detection-tuning"
REPORTS_DIR = "/root/code/fraud-detection/reports"

VALIDATION_JSON = os.path.join(REPORTS_DIR, "validation_status.json")
SELECTION_JSON = os.path.join(REPORTS_DIR, "selection.json")
TRAINING_REPORT_JSON = os.path.join(REPORTS_DIR, "training_report.json")


def main():
    with open(VALIDATION_JSON) as f:
        validation = json.load(f)
    with open(SELECTION_JSON) as f:
        selection = json.load(f)

    mlflow.set_tracking_uri(TRACKING_URI)
    client = mlflow.MlflowClient()
    exp = client.get_experiment_by_name(EXPERIMENT)
    runs = mlflow.search_runs([exp.experiment_id], max_results=500) if exp else []
    total_trials = int(len(runs)) if hasattr(runs, "__len__") else 0

    run_id = selection["run_id"]
    client = mlflow.MlflowClient()
    run = client.get_run(run_id)
    best_params = {k: v for k, v in run.data.params.items()}
    best_metrics = {k: float(v) for k, v in run.data.metrics.items()}

    # TODO: assemble the consolidated training report from the upstream
    # artefacts gathered above. Build a dict with exactly these five keys
    # and bind it to `report`:
    #   "best_model"        -> selection's model_type (selection["model_type"])
    #   "best_params"       -> best_params
    #   "metrics"           -> best_metrics
    #   "total_trials"      -> total_trials
    #   "validation_status" -> validation's status (validation["status"])
    report = {
        "best_model": selection["model_type"],
        "best_params": best_params,
        "metrics": best_metrics,
        "total_trials": total_trials,
        "validation_status": validation["status"],
    }


    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(TRAINING_REPORT_JSON, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[report] {TRAINING_REPORT_JSON}")


if __name__ == "__main__":
    main()
```