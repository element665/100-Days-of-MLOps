Prompt

The xFusionCorp Industries ML platform team is currently tuning hyperparameters for fraud detection using Optuna and reviewing the comprehensive search results in the MLflow Compare view. A draft tuner is available at `/root/code/fraud-detection/src/models/tune.py`. However, the current optimization process is functioning incorrectly, causing no trials to be recorded on the tracking server. Your objective is to modify the tuner so that all 20 trials are visible in MLflow, and ensure that the saved best configuration corresponds to the candidate with the highest F1 score.

  

1. The MLflow tracking server is already running on port `5000`. The **MLflow UI** button at the top of the lab can be opened to confirm—the dashboard loads with an empty `hyperopt-tuning` experiment.
    
2. The project layout under `/root/code/fraud-detection/`:
    
    - `data/train.csv` – A 200-row synthetic binary-classification dataset (imbalanced roughly 70 / 30).
    - `src/models/tune.py` – The Optuna tuner scaffold. Fold iteration, metric averaging, Optuna study creation, and YAML persistence are already wired; corrections are required.
    - `configs/` – Where `best_params.yaml` is written after the search completes.
3. Run the tuner once against the scaffold as-is—`python src/models/tune.py`—and check the `hyperopt-tuning`experiment to confirm no trials land on the tracking server.
    
4. The end state must include:
    
    - At least 20 runs exist in the `hyperopt-tuning`experiment on MLflow. Every run carries `params.n_estimators`, `params.max_depth`, and `metrics.f1_score`.
    - A YAML file at `/root/code/fraud-detection/configs/best_params.yaml` with exactly two keys: `n_estimators` (integer in the range `[50, 500]`) and `max_depth` (integer in the range `[3, 20]`).
    - The saved `best_params` corresponds to the highest-F1 trial in the search space.

---

Solution

tune.py (original)

```python
"""Hyperparameter tuner for the fraud-detection RandomForest.

Uses Optuna to sample `n_estimators` and `max_depth` across 20
trials, evaluates each candidate via 3-fold stratified cross-
validation on the synthetic training set, and writes the best
configuration to `configs/best_params.yaml`.

Every trial must land in the MLflow `hyperopt-tuning` experiment
as an independent run so the full search can be inspected in the
Compare view — the per-trial hyperparameters logged as run
parameters and the resulting mean f1 as a run metric named
`f1_score`.

The scaffold below already implements fold iteration, metric
averaging, and the Optuna / YAML wiring. Two corrections remain
before the search produces the configuration the release checklist
requires.
"""
import os
import yaml
import numpy as np
import pandas as pd
import optuna
import mlflow
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

TRAIN_CSV = "/root/code/fraud-detection/data/train.csv"
CONFIGS_DIR = "/root/code/fraud-detection/configs"
BEST_PARAMS_YAML = os.path.join(CONFIGS_DIR, "best_params.yaml")
EXPERIMENT_NAME = "hyperopt-tuning"
N_TRIALS = 20
N_SPLITS = 3

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment(EXPERIMENT_NAME)


def objective(trial, X, y):
    n_estimators = trial.suggest_int("n_estimators", 50, 500)
    max_depth = trial.suggest_int("max_depth", 3, 20)

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42,
    )
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring="f1")
    score = float(np.mean(scores))

    return score


def main():
    df = pd.read_csv(TRAIN_CSV)
    X = df.drop(columns=["is_fraud"])
    y = df["is_fraud"]

    study = optuna.create_study(
        direction="minimize", study_name=EXPERIMENT_NAME
    )
    study.optimize(lambda trial: objective(trial, X, y), n_trials=N_TRIALS)

    os.makedirs(CONFIGS_DIR, exist_ok=True)
    with open(BEST_PARAMS_YAML, "w") as f:
        yaml.safe_dump(study.best_params, f, sort_keys=True)

    print(f"best params: {study.best_params}")
    print(f"best f1: {study.best_value:.6f}")
    print(f"wrote {BEST_PARAMS_YAML}")


if __name__ == "__main__":
    main()
```

Run tuner as-is per instructions

```shell
python src/models/tune.py
```

Output

```shell
[I 2026-08-18 15:26:09,955] A new study created in memory with name: hyperopt-tuning
[I 2026-08-18 15:26:10,183] Trial 0 finished with value: 0.4535315068830801 and parameters: {'n_estimators': 125, 'max_depth': 15}. Best is trial 0 with value: 0.4535315068830801.
[I 2026-08-18 15:26:10,905] Trial 1 finished with value: 0.4414141414141414 and parameters: {'n_estimators': 381, 'max_depth': 13}. Best is trial 1 with value: 0.4414141414141414.
[I 2026-08-18 15:26:11,577] Trial 2 finished with value: 0.4465943215943216 and parameters: {'n_estimators': 421, 'max_depth': 6}. Best is trial 1 with value: 0.4414141414141414.
[I 2026-08-18 15:26:12,305] Trial 3 finished with value: 0.45444832944832947 and parameters: {'n_estimators': 445, 'max_depth': 7}. Best is trial 1 with value: 0.4414141414141414.
[I 2026-08-18 15:26:12,974] Trial 4 finished with value: 0.4465943215943216 and parameters: {'n_estimators': 414, 'max_depth': 6}. Best is trial 1 with value: 0.4414141414141414.
[I 2026-08-18 15:26:13,461] Trial 5 finished with value: 0.4532722179781003 and parameters: {'n_estimators': 305, 'max_depth': 8}. Best is trial 1 with value: 0.4414141414141414.
[I 2026-08-18 15:26:13,840] Trial 6 finished with value: 0.48328664799253024 and parameters: {'n_estimators': 234, 'max_depth': 8}. Best is trial 1 with value: 0.4414141414141414.
[I 2026-08-18 15:26:14,393] Trial 7 finished with value: 0.4377104377104377 and parameters: {'n_estimators': 322, 'max_depth': 14}. Best is trial 7 with value: 0.4377104377104377.
[I 2026-08-18 15:26:14,482] Trial 8 finished with value: 0.4334150326797386 and parameters: {'n_estimators': 50, 'max_depth': 4}. Best is trial 8 with value: 0.4334150326797386.
[I 2026-08-18 15:26:15,167] Trial 9 finished with value: 0.4453357100415924 and parameters: {'n_estimators': 422, 'max_depth': 13}. Best is trial 8 with value: 0.4334150326797386.
[I 2026-08-18 15:26:15,295] Trial 10 finished with value: 0.45392904216433627 and parameters: {'n_estimators': 72, 'max_depth': 19}. Best is trial 8 with value: 0.4334150326797386.
[I 2026-08-18 15:26:15,626] Trial 11 finished with value: 0.4532722179781003 and parameters: {'n_estimators': 200, 'max_depth': 19}. Best is trial 8 with value: 0.4334150326797386.
[I 2026-08-18 15:26:16,139] Trial 12 finished with value: 0.4017595307917888 and parameters: {'n_estimators': 306, 'max_depth': 4}. Best is trial 12 with value: 0.4017595307917888.
[I 2026-08-18 15:26:16,231] Trial 13 finished with value: 0.43793103448275855 and parameters: {'n_estimators': 50, 'max_depth': 3}. Best is trial 12 with value: 0.4017595307917888.
[I 2026-08-18 15:26:16,996] Trial 14 finished with value: 0.3968253968253968 and parameters: {'n_estimators': 490, 'max_depth': 3}. Best is trial 14 with value: 0.3968253968253968.
[I 2026-08-18 15:26:17,749] Trial 15 finished with value: 0.3968253968253968 and parameters: {'n_estimators': 479, 'max_depth': 3}. Best is trial 14 with value: 0.3968253968253968.
[I 2026-08-18 15:26:18,584] Trial 16 finished with value: 0.44921167903384046 and parameters: {'n_estimators': 500, 'max_depth': 10}. Best is trial 14 with value: 0.3968253968253968.
[I 2026-08-18 15:26:19,367] Trial 17 finished with value: 0.3968253968253968 and parameters: {'n_estimators': 495, 'max_depth': 3}. Best is trial 14 with value: 0.3968253968253968.
[I 2026-08-18 15:26:20,003] Trial 18 finished with value: 0.4039554531490015 and parameters: {'n_estimators': 372, 'max_depth': 5}. Best is trial 14 with value: 0.3968253968253968.
[I 2026-08-18 15:26:20,761] Trial 19 finished with value: 0.4414141414141414 and parameters: {'n_estimators': 461, 'max_depth': 10}. Best is trial 14 with value: 0.3968253968253968.
best params: {'n_estimators': 490, 'max_depth': 3}
best f1: 0.396825
wrote /root/code/fraud-detection/configs/best_params.yaml
```

Error 1: 
Output shows the lowest f1 score was listed as best. Instructions state highest score should be best.  (update minimize -> maximize)

```python
    study = optuna.create_study(
        direction="maximize", study_name=EXPERIMENT_NAME
    )
```

Error 2:
MLflow is configured but not set to create run

```python
def objective(trial, X, y):
    n_estimators = trial.suggest_int("n_estimators", 50, 500)
    max_depth = trial.suggest_int("max_depth", 3, 20)

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42,
    )
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring="f1")
    score = float(np.mean(scores))
    
    with mlflow.start_run():
	    mlflow.log_params({
		    "n_estimators": n_estimators,
		    "max_depth": max_depth,
	    })
	    mlflow.log_metric("f1_score", score)

    return score
```

tune.py (final)

```python
"""Hyperparameter tuner for the fraud-detection RandomForest.

Uses Optuna to sample `n_estimators` and `max_depth` across 20
trials, evaluates each candidate via 3-fold stratified cross-
validation on the synthetic training set, and writes the best
configuration to `configs/best_params.yaml`.

Every trial must land in the MLflow `hyperopt-tuning` experiment
as an independent run so the full search can be inspected in the
Compare view — the per-trial hyperparameters logged as run
parameters and the resulting mean f1 as a run metric named
`f1_score`.

The scaffold below already implements fold iteration, metric
averaging, and the Optuna / YAML wiring. Two corrections remain
before the search produces the configuration the release checklist
requires.
"""
import os
import yaml
import numpy as np
import pandas as pd
import optuna
import mlflow
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

TRAIN_CSV = "/root/code/fraud-detection/data/train.csv"
CONFIGS_DIR = "/root/code/fraud-detection/configs"
BEST_PARAMS_YAML = os.path.join(CONFIGS_DIR, "best_params.yaml")
EXPERIMENT_NAME = "hyperopt-tuning"
N_TRIALS = 20
N_SPLITS = 3

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment(EXPERIMENT_NAME)


def objective(trial, X, y):
    n_estimators = trial.suggest_int("n_estimators", 50, 500)
    max_depth = trial.suggest_int("max_depth", 3, 20)

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42,
    )
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring="f1")
    score = float(np.mean(scores))

    with mlflow.start_run():
        mlflow.log_params({
            "n_estimators": n_estimators,
            "max_depth": max_depth,
        })
        mlflow.log_metric("f1_score", score)

    return score


def main():
    df = pd.read_csv(TRAIN_CSV)
    X = df.drop(columns=["is_fraud"])
    y = df["is_fraud"]

    study = optuna.create_study(
        direction="maximize", study_name=EXPERIMENT_NAME
    )
    study.optimize(lambda trial: objective(trial, X, y), n_trials=N_TRIALS)

    os.makedirs(CONFIGS_DIR, exist_ok=True)
    with open(BEST_PARAMS_YAML, "w") as f:
        yaml.safe_dump(study.best_params, f, sort_keys=True)

    print(f"best params: {study.best_params}")
    print(f"best f1: {study.best_value:.6f}")
    print(f"wrote {BEST_PARAMS_YAML}")


if __name__ == "__main__":
    main()
```

Run correct script

```shell
python src/models/tune.py
```

Output

```shell
[I 2026-08-19 05:02:13,264] A new study created in memory with name: hyperopt-tuning
🏃 View run adaptable-stag-696 at: http://localhost:5000/#/experiments/1/runs/24eb084d3d374bb0925b8bc73d617f8c
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:13,566] Trial 0 finished with value: 0.46193097121889687 and parameters: {'n_estimators': 75, 'max_depth': 10}. Best is trial 0 with value: 0.46193097121889687.
🏃 View run marvelous-mole-521 at: http://localhost:5000/#/experiments/1/runs/5209b533686f40bb955346034ff59c87
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:13,927] Trial 1 finished with value: 0.4532722179781003 and parameters: {'n_estimators': 196, 'max_depth': 15}. Best is trial 0 with value: 0.46193097121889687.
🏃 View run nimble-rat-436 at: http://localhost:5000/#/experiments/1/runs/471abf602c53493b82cfdd70a937bf49
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:14,323] Trial 2 finished with value: 0.4465943215943216 and parameters: {'n_estimators': 220, 'max_depth': 7}. Best is trial 0 with value: 0.46193097121889687.
🏃 View run charming-mare-728 at: http://localhost:5000/#/experiments/1/runs/3042940594564560a3ba18b4cea7f9c8
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:15,059] Trial 3 finished with value: 0.4453357100415924 and parameters: {'n_estimators': 434, 'max_depth': 15}. Best is trial 0 with value: 0.46193097121889687.
🏃 View run carefree-dove-684 at: http://localhost:5000/#/experiments/1/runs/fa091228ee6041ef904f538c689fda82
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:15,716] Trial 4 finished with value: 0.4453357100415924 and parameters: {'n_estimators': 379, 'max_depth': 11}. Best is trial 0 with value: 0.46193097121889687.
🏃 View run welcoming-calf-261 at: http://localhost:5000/#/experiments/1/runs/dd0340a5e7514ebc97f8e662f5f179ab
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:16,417] Trial 5 finished with value: 0.3826024426691835 and parameters: {'n_estimators': 411, 'max_depth': 4}. Best is trial 0 with value: 0.46193097121889687.
🏃 View run hilarious-jay-921 at: http://localhost:5000/#/experiments/1/runs/60c4424ca8e94f1ea1a22ed9fc7b8185
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:17,007] Trial 6 finished with value: 0.4414141414141414 and parameters: {'n_estimators': 342, 'max_depth': 11}. Best is trial 0 with value: 0.46193097121889687.
🏃 View run wistful-fox-989 at: http://localhost:5000/#/experiments/1/runs/43a6318d4ee346c891e72dc57c28610d
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:17,653] Trial 7 finished with value: 0.4453357100415924 and parameters: {'n_estimators': 362, 'max_depth': 19}. Best is trial 0 with value: 0.46193097121889687.
🏃 View run polite-tern-122 at: http://localhost:5000/#/experiments/1/runs/d8b483fa72c540999950fd5785b68dde
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:18,064] Trial 8 finished with value: 0.46073871409028727 and parameters: {'n_estimators': 221, 'max_depth': 11}. Best is trial 0 with value: 0.46193097121889687.
🏃 View run luminous-pig-25 at: http://localhost:5000/#/experiments/1/runs/d7d317c81ea3427a88051bf35b62bcf3
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:18,874] Trial 9 finished with value: 0.4115719406041986 and parameters: {'n_estimators': 487, 'max_depth': 5}. Best is trial 0 with value: 0.46193097121889687.
🏃 View run ambitious-snake-697 at: http://localhost:5000/#/experiments/1/runs/1d1596f0d3e7490c913bb3d2a3cb6ef0
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:19,042] Trial 10 finished with value: 0.4461281408649829 and parameters: {'n_estimators': 80, 'max_depth': 20}. Best is trial 0 with value: 0.46193097121889687.
🏃 View run efficient-mole-808 at: http://localhost:5000/#/experiments/1/runs/34608f2d927a4b499169e02044d346d3
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:19,176] Trial 11 finished with value: 0.4155982905982906 and parameters: {'n_estimators': 54, 'max_depth': 10}. Best is trial 0 with value: 0.46193097121889687.
🏃 View run masked-croc-607 at: http://localhost:5000/#/experiments/1/runs/97c8109e9e7641b28b8c604e96e92242
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:19,525] Trial 12 finished with value: 0.4687208216619981 and parameters: {'n_estimators': 177, 'max_depth': 8}. Best is trial 12 with value: 0.4687208216619981.
🏃 View run chill-worm-756 at: http://localhost:5000/#/experiments/1/runs/c325a7d183d74668bc35c7ff431b848b
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:19,778] Trial 13 finished with value: 0.44935064935064933 and parameters: {'n_estimators': 132, 'max_depth': 8}. Best is trial 12 with value: 0.4687208216619981.
🏃 View run able-owl-600 at: http://localhost:5000/#/experiments/1/runs/974a59ca51304e7ba31bd26781b6f55f
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:20,078] Trial 14 finished with value: 0.45661375661375664 and parameters: {'n_estimators': 156, 'max_depth': 14}. Best is trial 12 with value: 0.4687208216619981.
🏃 View run wise-shrimp-882 at: http://localhost:5000/#/experiments/1/runs/95d81b36c1f940ff87720c5d33e1252f
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:20,565] Trial 15 finished with value: 0.43803418803418803 and parameters: {'n_estimators': 276, 'max_depth': 7}. Best is trial 12 with value: 0.4687208216619981.
🏃 View run whimsical-crab-657 at: http://localhost:5000/#/experiments/1/runs/a17ad59cf17247cb89de58ae143131e1
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:20,800] Trial 16 finished with value: 0.4223920236851271 and parameters: {'n_estimators': 129, 'max_depth': 3}. Best is trial 12 with value: 0.4687208216619981.
🏃 View run sassy-yak-396 at: http://localhost:5000/#/experiments/1/runs/736e4090916a47dea31d070ee0198130
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:21,315] Trial 17 finished with value: 0.4575308319928119 and parameters: {'n_estimators': 292, 'max_depth': 9}. Best is trial 12 with value: 0.4687208216619981.
🏃 View run colorful-skink-214 at: http://localhost:5000/#/experiments/1/runs/9dd94910922b41c9ae27faec8ce3572c
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:21,532] Trial 18 finished with value: 0.4490497141659932 and parameters: {'n_estimators': 103, 'max_depth': 13}. Best is trial 12 with value: 0.4687208216619981.
🏃 View run useful-zebra-786 at: http://localhost:5000/#/experiments/1/runs/de9e5beff6e54f44947f2fffb6d0283b
🧪 View experiment at: http://localhost:5000/#/experiments/1
[I 2026-08-19 05:02:21,848] Trial 19 finished with value: 0.44949494949494956 and parameters: {'n_estimators': 168, 'max_depth': 6}. Best is trial 12 with value: 0.4687208216619981.
best params: {'n_estimators': 177, 'max_depth': 8}
best f1: 0.468721
wrote /root/code/fraud-detection/configs/best_params.yaml
```

MLflow UI should now show the 20 runs.

![MLflow Screenshot](<../screenshots/Screenshot Day 35 MLflow runs.png>)

best_params should correspond to highest-F1 trial (Trial 12)

best_params.yaml

```yaml
max_depth: 8
n_estimators: 177

```
