Prompt

The xFusionCorp Industries ML platform team is conducting a three-way bake-off among three candidates for fraud detection: RandomForest, GradientBoosting, and LogisticRegression. Each candidate's performance is recorded as an MLflow run in the `bakeoff` experiment. While three accurate trainer scripts are already implemented, the orchestrator located at `/root/code/fraud-detection/src/models/bakeoff.py` incorrectly identifies the winning model and generates an incomplete report. Your objective is to modify the orchestrator to ensure that the model with the highest F1 score is correctly designated as the winner and that the report clearly indicates which model family triumphed.

  

1. The MLflow tracking server is already running on port `5000`. The **MLflow UI** button at the top of the lab can be opened to confirm—the dashboard loads with an empty `bakeoff` experiment.
    
2. The project layout under `/root/code/fraud-detection/`:
    
    - `data/train.csv` – A 200-row synthetic binary-classification dataset (imbalanced roughly 70 / 30).
    - `src/models/train_rf.py`, `src/models/train_gb.py`, `src/models/train_lr.py` – Three independent trainer scripts. Each one fits its named estimator with 3-fold stratified CV and logs one MLflow run tagged `candidate=<model family>` with the mean `f1_score` metric and its hyperparameters. These three files are correct and need no edits.
    - `src/models/bakeoff.py` – The orchestrator. It queries the `bakeoff` experiment with `mlflow.search_runs(...)` and writes `/root/code/fraud-detection/reports/winner.json`. The corrections are confined to this file.
3. Each candidate must be logged before the orchestrator can compare them—run the three trainer scripts to populate the `bakeoff` experiment, then run `python src/models/bakeoff.py` and inspect `reports/winner.json` against the runs in MLflow.
    
4. The end state must include:
    
    - Three runs exist in the `bakeoff` MLflow experiment, one per candidate, each with `tags.candidate`, the candidate's hyperparameters, and `metrics.f1_score`.
    - A JSON file at `/root/code/fraud-detection/reports/winner.json` with exactly three keys: `model_type` (one of `random_forest`, `gradient_boosting`, `logistic_regression`), `run_id`, and `f1_score`.
    - The `model_type`, `run_id`, and `f1_score`stored in `winner.json` correspond to the candidate with the highest `f1_score` in the `bakeoff` experiment.

> The MLflow Compare view—select all three runs in the experiment's run list and click **Compare**—is the fastest way to eyeball which candidate won and spot-check the report.

---

Solution

(Provided Trainer Scripts)

[train_rf.py](<../assets/Day 36 - train_rf.py>)

[train_gb.py](<../assets/Day 36 - train_gb.py>)

[train_lf.py](<../assets/Day 36 - train_lr.py>)

bakeoff.py (Original)

```python
"""Pick the winning candidate from the `bakeoff` MLflow experiment and
persist it at /root/code/fraud-detection/reports/winner.json.

Assumes train_rf.py, train_gb.py, and train_lr.py have each been run
at least once so the experiment contains three candidate runs.

The winner is the run with the highest metrics.f1_score. The saved
report must contain:

    {
      "model_type": "<candidate tag>",
      "run_id":     "<mlflow run id>",
      "f1_score":   <float>
    }
"""
import json
import os

import mlflow

TRACKING_URI = "http://localhost:5000"
EXPERIMENT = "bakeoff"
REPORTS_DIR = "/root/code/fraud-detection/reports"
WINNER_JSON = os.path.join(REPORTS_DIR, "winner.json")


def main():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = mlflow.MlflowClient()
    exp = client.get_experiment_by_name(EXPERIMENT)
    if exp is None:
        raise SystemExit(
            f"Experiment {EXPERIMENT!r} not found. Run the three "
            "trainer scripts first."
        )

    runs = mlflow.search_runs(
        experiment_ids=[exp.experiment_id],
        order_by=["metrics.f1_score ASC"],
        max_results=10,
    )
    if runs.empty:
        raise SystemExit(
            f"No runs found in {EXPERIMENT!r}. Run the three trainer "
            "scripts first."
        )

    winner = runs.iloc[0]
    report = {
        "run_id": winner["run_id"],
        "f1_score": float(winner["metrics.f1_score"]),
    }

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(WINNER_JSON, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Winner written to {WINNER_JSON}: {report}")


if __name__ == "__main__":
    main()
```

Error 1:

mlflow.search_runs(...) is ordered in ascending order, but winner selects the first run (lowest in current order). Change order to descending.

```python
    runs = mlflow.search_runs(
        experiment_ids=[exp.experiment_id],
        order_by=["metrics.f1_score DESC"],
        max_results=10,
    )
```

Error 2:

model_type is not referenced in the report = {...}

```shell
    report = {
	    "model_type": winner["tags.candidate"],
        "run_id": winner["run_id"],
        "f1_score": float(winner["metrics.f1_score"]),
    }
```

Run three trainer scripts

```shell
python src/models/train_rf.py
python src/models/train_gb.py
python src/models/train_lr.py
```

Output

```shell
random_forest: f1_score=0.4533  run_id=f26ac99295bc47eaa4a38a89c0cb2be4
🏃 View run random_forest at: http://localhost:5000/#/experiments/1/runs/f26ac99295bc47eaa4a38a89c0cb2be4
🧪 View experiment at: http://localhost:5000/#/experiments/1
gradient_boosting: f1_score=0.4076  run_id=5d4598714bdb432988950a06eaa82085
🏃 View run gradient_boosting at: http://localhost:5000/#/experiments/1/runs/5d4598714bdb432988950a06eaa82085
🧪 View experiment at: http://localhost:5000/#/experiments/1
logistic_regression: f1_score=0.5192  run_id=4a0648e95cb449e38c5085bbb77e5a35
🏃 View run logistic_regression at: http://localhost:5000/#/experiments/1/runs/4a0648e95cb449e38c5085bbb77e5a35
🧪 View experiment at: http://localhost:5000/#/experiments/1
```

Run bakeoff script

```shell
python src/models/bakeoff.py
```

Output

```shell
Winner written to /root/code/fraud-detection/reports/winner.json: {'model_type': 'logistic_regression', 'run_id': '4a0648e95cb449e38c5085bbb77e5a35', 'f1_score': 0.519208310283361}
```

winner.json

```json
{
  "model_type": "logistic_regression",
  "run_id": "4a0648e95cb449e38c5085bbb77e5a35",
  "f1_score": 0.519208310283361
}
```

MLflow UI verification 

![MLflow screenshot](<../screenshots/Screenshot Day 36 MLflow UI.png>)


bakeoff.py (Final)

```python
"""Pick the winning candidate from the `bakeoff` MLflow experiment and
persist it at /root/code/fraud-detection/reports/winner.json.

Assumes train_rf.py, train_gb.py, and train_lr.py have each been run
at least once so the experiment contains three candidate runs.

The winner is the run with the highest metrics.f1_score. The saved
report must contain:

    {
      "model_type": "<candidate tag>",
      "run_id":     "<mlflow run id>",
      "f1_score":   <float>
    }
"""
import json
import os

import mlflow

TRACKING_URI = "http://localhost:5000"
EXPERIMENT = "bakeoff"
REPORTS_DIR = "/root/code/fraud-detection/reports"
WINNER_JSON = os.path.join(REPORTS_DIR, "winner.json")


def main():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = mlflow.MlflowClient()
    exp = client.get_experiment_by_name(EXPERIMENT)
    if exp is None:
        raise SystemExit(
            f"Experiment {EXPERIMENT!r} not found. Run the three "
            "trainer scripts first."
        )

    runs = mlflow.search_runs(
        experiment_ids=[exp.experiment_id],
        order_by=["metrics.f1_score DESC"],
        max_results=10,
    )
    if runs.empty:
        raise SystemExit(
            f"No runs found in {EXPERIMENT!r}. Run the three trainer "
            "scripts first."
        )

    winner = runs.iloc[0]
    report = {
        "model_type": winner["tags.candidate"],
        "run_id": winner["run_id"],
        "f1_score": float(winner["metrics.f1_score"]),
    }

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(WINNER_JSON, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Winner written to {WINNER_JSON}: {report}")


if __name__ == "__main__":
    main()
```
