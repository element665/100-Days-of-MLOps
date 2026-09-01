"""Stage 2 — Optuna tuning across two model families.

Runs `N_TRIALS` Optuna trials, each sampling a model family
(RandomForest or GradientBoosting) plus its hyperparameters.
Every trial fits the estimator under 3-fold stratified CV on the
training CSV and logs one MLflow run tagged with the candidate
family, the sampled hyperparameters, and the mean F1 score.
The fitted estimator is also logged as an MLflow model artefact so
the register stage can reference it by URI.
"""
import mlflow
import mlflow.sklearn
import optuna
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

TRACKING_URI = "http://localhost:5000"
EXPERIMENT = "fraud-detection-tuning"
TRAIN_CSV = "/root/code/fraud-detection/data/train.csv"

N_TRIALS = 10
SEED = 42


def _build(trial):
    model_type = trial.suggest_categorical(
        "model_type", ["RandomForest", "GradientBoosting"]
    )
    n_estimators = trial.suggest_int("n_estimators", 50, 200)
    max_depth = trial.suggest_int("max_depth", 3, 10)

    if model_type == "RandomForest":
        model = RandomForestClassifier(
            n_estimators=n_estimators, max_depth=max_depth, random_state=SEED,
        )
    else:
        model = GradientBoostingClassifier(
            n_estimators=n_estimators, max_depth=max_depth, random_state=SEED,
        )
    return model_type, model, {
        "n_estimators": n_estimators,
        "max_depth": max_depth,
    }


def _objective(trial, X, y):
    model_type, model, params = _build(trial)
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    scores = []
    for tr, te in cv.split(X, y):
        model.fit(X.iloc[tr], y.iloc[tr])
        scores.append(f1_score(y.iloc[te], model.predict(X.iloc[te])))
    mean_f1 = float(sum(scores) / len(scores))

    model.fit(X, y)
    with mlflow.start_run(run_name=f"trial-{trial.number}"):
        mlflow.set_tag("model_type", model_type)
        mlflow.log_params(params)
        mlflow.log_metric("f1_score", mean_f1)
        mlflow.sklearn.log_model(model, name="model")

    return mean_f1


def main():
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)

    df = pd.read_csv(TRAIN_CSV)
    X = df.drop(columns=["is_fraud"])
    y = df["is_fraud"]

    sampler = optuna.samplers.TPESampler(seed=SEED)
    study = optuna.create_study(
        direction="maximize", study_name=EXPERIMENT, sampler=sampler,
    )
    study.optimize(lambda t: _objective(t, X, y), n_trials=N_TRIALS)

    print(
        f"[tune] {N_TRIALS} trials complete. "
        f"best_value={study.best_value:.4f}  best_params={study.best_params}"
    )


if __name__ == "__main__":
    main()