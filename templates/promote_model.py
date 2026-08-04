import mlflow
from mlflow import MlflowClient

mlflow.set_tracking_uri("http://localhost:5000")

client = MlflowClient()

exp = client.get_experiment_by_name("fraud-detection-v2")

run = client.search_runs(
    [exp.experiment_id],
    order_by=["metrics.f1_score DESC"],
    max_results=1,
)[0]

mv = mlflow.register_model(
    f"runs:/{run.info.run_id}/model",
    "fraud-detector-v2",
)

client.set_registered_model_alias(
    "fraud-detector-v2",
    "champion",
    mv.version,
)