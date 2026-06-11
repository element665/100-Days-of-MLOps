Prompt

The xFusionCorp Industries ML team wants to replace the manual `log_param` / `log_metric` boilerplate in their training scripts with MLflow's autologging feature, so every training run captures its constructor parameters, training metrics, and model artefact automatically. A training scaffold has been pre-staged at `/root/code/autolog_experiment.py`—it configures MLflow, fits a small synthetic sklearn model, and prints a confirmation message. Two `# TODO` blocks remain empty. Your task is to complete them so the end state below holds.

  

1. The MLflow tracking server is already running on port `5000`. The **MLflow UI** button at the top of the lab can be opened to view the dashboard; only the `Default`experiment is present on first load.
    
2. Open `/root/code/autolog_experiment.py` in the VS Code editor and complete the two TODO blocks—both are one-line additions—so that, after the script is executed, the following end state holds:
    
    - An experiment named `autolog-demo` exists on the MLflow server.
    - At least one run exists in the `autolog-demo`experiment.
    - The run's **Parameters** panel lists every sklearn constructor parameter that the `LogisticRegression` in the scaffold implicitly carries (for example `C`, `max_iter`, `solver`, `tol`, `penalty`) – Not only the three explicit keyword arguments the scaffold passes.
    - The **Artifacts** panel on the run contains a model directory with an `MLmodel` descriptor and a pickled estimator.
3. Once the TODOs are in place, execute the script:
    

```
   python3 /root/code/autolog_experiment.py
```

Confirm the result in the **MLflow UI**.

> No real dataset is loaded by the scaffold—the training step is a deterministic toy that gives MLflow a `.fit()` call to observe. The focus of the lab is autolog configuration, not model quality.

---

Solution

autolog_experiment.py (original)

```python
"""
MLflow autologging — two TODO blocks activate MLflow's automatic
capture of parameters, metrics, and the trained model for the
`model.fit(...)` call below.

The dataset and the model here are synthetic. A LogisticRegression
fitted on a deterministic four-row XOR-like array stands in for a
real training step so that autologging has a valid sklearn fit()
call to instrument. No real ML workflow takes place; the focus of
the lab is autolog configuration, not model quality.

Both TODO blocks must be completed BEFORE `model.fit(...)` runs —
autolog hooks sklearn at call time, and the active experiment
scopes where the autologged run lands.
"""
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.linear_model import LogisticRegression

mlflow.set_tracking_uri("http://localhost:5000")


# TODO 1: enable autologging for the sklearn flavour so that the
# subsequent model.fit(...) call records parameters, metrics, and
# the trained model on the active experiment automatically.


# TODO 2: set the active experiment to "autolog-demo" so the
# autologged run lands in that experiment rather than the Default one.
model.fit(...)

# Synthetic four-row XOR-like array. Not a real ML dataset — just
# a deterministic toy to give sklearn.fit() something to execute.
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([0, 0, 1, 1])

model = LogisticRegression(C=1.0, max_iter=100, random_state=42)
model.fit(X, y)

print("Autolog run complete — check the MLflow UI")

```

(updated)

```python
"""
MLflow autologging — two TODO blocks activate MLflow's automatic
capture of parameters, metrics, and the trained model for the
`model.fit(...)` call below.

The dataset and the model here are synthetic. A LogisticRegression
fitted on a deterministic four-row XOR-like array stands in for a
real training step so that autologging has a valid sklearn fit()
call to instrument. No real ML workflow takes place; the focus of
the lab is autolog configuration, not model quality.

Both TODO blocks must be completed BEFORE `model.fit(...)` runs —
autolog hooks sklearn at call time, and the active experiment
scopes where the autologged run lands.
"""
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.linear_model import LogisticRegression

mlflow.set_tracking_uri("http://localhost:5000")


# TODO 1: enable autologging for the sklearn flavour so that the
# subsequent model.fit(...) call records parameters, metrics, and
# the trained model on the active experiment automatically.
mlflow.sklearn.autolog()

# TODO 2: set the active experiment to "autolog-demo" so the
# autologged run lands in that experiment rather than the Default one.
mlflow.set_experiment("autolog-demo")

# Synthetic four-row XOR-like array. Not a real ML dataset — just
# a deterministic toy to give sklearn.fit() something to execute.
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([0, 0, 1, 1])

model = LogisticRegression(C=1.0, max_iter=100, random_state=42)
model.fit(X, y)

print("Autolog run complete — check the MLflow UI")

```

Navigate to working directory

```shell
cd /root/code/
```

Execute script

```shell
python3 /root/code/autolog_experiment.py
```

Output

```shell
2026/06/11 13:22:27 INFO mlflow.tracking.fluent: Experiment with name 'autolog-demo' does not exist. Creating a new experiment.
2026/06/11 13:22:27 INFO mlflow.utils.autologging_utils: Created MLflow autologging run with ID 'c86b40485734431bb1a6d32e284f3ea3', which will track hyperparameters, performance metrics, model artifacts, and lineage information for the current sklearn workflow
2026/06/11 13:22:27 WARNING mlflow.sklearn: Saving scikit-learn models in the pickle or cloudpickle format requires exercising caution because these formats rely on Python's object serialization mechanism, which can execute arbitrary code during deserialization. The recommended safe alternative is the 'skops' format. For more information, see: https://scikit-learn.org/stable/model_persistence.html
🏃 View run amazing-slug-414 at: http://localhost:5000/#/experiments/1/runs/c86b40485734431bb1a6d32e284f3ea3
🧪 View experiment at: http://localhost:5000/#/experiments/1
Autolog run complete — check the MLflow UI
```

Verify in MLflow UI

Training runs dashboard

![Dashboard](<../screenshots/Screenshot Day 24 Training runs dash.png>)

Training run details

![Details](<../screenshots/Screenshot Day 24 Run details.png>)
