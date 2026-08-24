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

        mlflow.log_artifact(config["output"]["model_path"])
        print("[pipeline] completed.")


if __name__ == "__main__":
    main()