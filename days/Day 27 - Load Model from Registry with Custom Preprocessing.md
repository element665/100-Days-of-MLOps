Prompt

The xFusionCorp Industries deployment team needs a batch-prediction wrapper around the registered `fraud-detector` champion model, complete with custom preprocessing, before the model is exposed to downstream services. The wrapper class is pre-written. Your task is to complete the MLflow-side plumbing that loads the champion and runs the batch.

  

1. The MLflow tracking server is already running on port `5000`. The **MLflow UI** button at the top of the lab can be opened to view the dashboard; the **Models** tab shows `fraud-detector` registered with a `champion`alias on version 1.
    
2. Open `/root/code/predict_with_preprocessing.py` in the VS Code editor. The `ScaledPredictor` class (a pyfunc wrapper that applies per-column mean/std scaling inside its `.predict()` method) and the `MODEL_URI` / `INPUT_CSV` / `OUTPUT_CSV` constants at the top of the file are already written and must NOT be modified. Two `# TODO` blocks remain:
    
    - **TODO 1:** Load the `champion` version of `fraud-detector` from MLflow's Model Registry into a variable named `inner_model`. `MODEL_URI` is already set to `models:/fraud-detector@champion`.
    - **TODO 2:** Run the batch prediction over the pre-staged inputs, attach the predictions as a new `prediction` column on the `inputs` DataFrame, and write the result to `OUTPUT_CSV`(`/root/code/predictions.csv`) with `index=False`.
3. After both TODOs are completed, run the script once:
    

```
   python3 /root/code/predict_with_preprocessing.py
```

The end state must include:

- A file at `/root/code/predictions.csv` with a header row.
- A `prediction` column in that CSV.
- The number of prediction rows equal to the number of input rows in `/root/code/data/inputs.csv` (ten).

---

Solution

predict_with_preprocessing.py (provided)

```python
"""
MLflow model serving — two TODO blocks wire a pyfunc wrapper with
custom preprocessing around the registered champion model and run a
batch prediction on the pre-staged synthetic input file.

The `ScaledPredictor` class (including the mean/std scaling logic
in `.predict()`) is already written — the lab exercises the serving
plumbing (loading the registry champion by alias, wiring it into
the pyfunc wrapper, producing a predictions CSV), not preprocessing
theory.

The input file at /root/code/data/inputs.csv is a deterministic
synthetic 10-row numeric batch. No real ML workflow; the prediction
values carry no meaning beyond "the pyfunc ran end to end".
"""
import numpy as np
import pandas as pd
import mlflow
import mlflow.pyfunc

MODEL_URI = "models:/fraud-detector@champion"
INPUT_CSV = "/root/code/data/inputs.csv"
OUTPUT_CSV = "/root/code/predictions.csv"


class ScaledPredictor(mlflow.pyfunc.PythonModel):
    """Wrap any sklearn / pyfunc model with per-column mean/std scaling
    applied to the input before the underlying model is called.
    Pre-written; no edits are required inside this class."""

    def __init__(self, inner_model, mean, std):
        self.model = inner_model
        self.mean = mean
        self.std = std

    def predict(self, context, model_input, params=None):
        X = np.asarray(model_input, dtype=float)
        scaled = (X - self.mean) / self.std
        return self.model.predict(scaled)


mlflow.set_tracking_uri("http://localhost:5000")

# TODO 1: load the champion version of the `fraud-detector` registered
# model from MLflow and bind the loaded model to `inner_model`. Use
# `mlflow.pyfunc.load_model(uri)` with `uri = MODEL_URI`.


# Compute per-column mean and std from the pre-staged inputs, then
# build the pyfunc wrapper around `inner_model`.
inputs = pd.read_csv(INPUT_CSV)
mean = inputs.values.mean(axis=0)
std = inputs.values.std(axis=0)
std[std == 0] = 1.0  # guard against division by zero on constant columns

predictor = ScaledPredictor(inner_model, mean, std)


# TODO 2: run `predictor.predict(None, inputs.values)` to produce the
# batch prediction, attach the result as a new `prediction` column on
# `inputs`, and write the resulting DataFrame to `OUTPUT_CSV` with
# `index=False`.


```

predict_with_preprocessing.py (updated)

```python
"""
MLflow model serving — two TODO blocks wire a pyfunc wrapper with
custom preprocessing around the registered champion model and run a
batch prediction on the pre-staged synthetic input file.

The `ScaledPredictor` class (including the mean/std scaling logic
in `.predict()`) is already written — the lab exercises the serving
plumbing (loading the registry champion by alias, wiring it into
the pyfunc wrapper, producing a predictions CSV), not preprocessing
theory.

The input file at /root/code/data/inputs.csv is a deterministic
synthetic 10-row numeric batch. No real ML workflow; the prediction
values carry no meaning beyond "the pyfunc ran end to end".
"""
import numpy as np
import pandas as pd
import mlflow
import mlflow.pyfunc

MODEL_URI = "models:/fraud-detector@champion"
INPUT_CSV = "/root/code/data/inputs.csv"
OUTPUT_CSV = "/root/code/predictions.csv"


class ScaledPredictor(mlflow.pyfunc.PythonModel):
    """Wrap any sklearn / pyfunc model with per-column mean/std scaling
    applied to the input before the underlying model is called.
    Pre-written; no edits are required inside this class."""

    def __init__(self, inner_model, mean, std):
        self.model = inner_model
        self.mean = mean
        self.std = std

    def predict(self, context, model_input, params=None):
        X = np.asarray(model_input, dtype=float)
        scaled = (X - self.mean) / self.std
        return self.model.predict(scaled)


mlflow.set_tracking_uri("http://localhost:5000")

# TODO 1: load the champion version of the `fraud-detector` registered
# model from MLflow and bind the loaded model to `inner_model`. Use
# `mlflow.pyfunc.load_model(uri)` with `uri = MODEL_URI`.
inner_model=mlflow.pyfunc.load_model(MODEL_URI)

# Compute per-column mean and std from the pre-staged inputs, then
# build the pyfunc wrapper around `inner_model`.
inputs = pd.read_csv(INPUT_CSV)
mean = inputs.values.mean(axis=0)
std = inputs.values.std(axis=0)
std[std == 0] = 1.0  # guard against division by zero on constant columns

predictor = ScaledPredictor(inner_model, mean, std)


# TODO 2: run `predictor.predict(None, inputs.values)` to produce the
# batch prediction, attach the result as a new `prediction` column on
# `inputs`, and write the resulting DataFrame to `OUTPUT_CSV` with
# `index=False`.
predictions = predictor.predict(None, inputs.values)
inputs["prediction"] = predictions
inputs.to_csv(OUTPUT_CSV, index=False)

```

Run the script

```shell
python3 /root/code/predict_with_preprocessing.py
```

Verify 'predictions.csv' file

![Screenshot](<../screenshots/Screenshot Day 27.png>)