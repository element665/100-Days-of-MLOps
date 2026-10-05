Prompt

The xFusionCorp Industries ML platform team processes the overnight batch of transactions using a fraud-detection model. This process is executed with a standalone script that reads from `input.csv`, applies the pre-trained RandomForest model to each row, and generates `predictions.csv`. A scaffold for the script, located at `/root/code/serving/batch_predict.py`, includes the paths for the model, input, and output; however, the scoring flow is currently marked as `TODO`.

Your objective is to implement the batch scoring process within the script. Specifically, you need to ensure that it reads `input.csv`, utilizes the pre-trained model to score each row, and outputs `predictions.csv`, which should include a column for integer `prediction` class labels. After implementing the flow, run the script.

  

The project layout under `/root/code/serving/`:

- `model.pkl` – Deterministic RandomForest trained at startup on the shared `amount / hour / num_tx_past_day → is_fraud` synthetic dataset.
- `input.csv` – The 10-row batch input: three feature columns, no label column.
- `batch_predict.py` – The scorer scaffold. The `MODEL_PATH` / `INPUT_CSV` / `OUTPUT_CSV` constants are set; the scoring flow (load the model, read the input, add an integer `prediction` column via `model.predict(...)`, write the output) is left as a `TODO` to author.

The end state must include:

- `/root/code/serving/predictions.csv` exists.
- The output carries the three input columns plus a `prediction` column.
- Every value in `prediction` is `0` or `1` (integer class label), not a float probability.
- The output row count matches the input row count.

---

Solution

batch_predict.py (Original)

```python
"""Batch scorer for the fraud-detection RandomForest.

Reads `input.csv` (one row per transaction, columns: amount, hour,
num_tx_past_day), runs every row through the pre-trained model, and
writes `predictions.csv` with the original columns plus an integer
`prediction` class-label column.
"""
import joblib
import pandas as pd

MODEL_PATH = "/root/code/serving/model.pkl"
INPUT_CSV = "/root/code/serving/input.csv"
OUTPUT_CSV = "/root/code/serving/predictions.csv"

# TODO: author the batch scoring flow using the paths above:
#   1. load the model from MODEL_PATH (joblib.load)
#   2. read INPUT_CSV into a DataFrame (pd.read_csv)
#   3. select the feature columns: amount, hour, num_tx_past_day
#   4. add a `prediction` column of INTEGER class labels with
#      model.predict(...) — class labels (0/1), NOT the float
#      probabilities that predict_proba(...) would return
#   5. write the DataFrame to OUTPUT_CSV with to_csv(..., index=False)
#   6. print how many rows were written
```

batch_predict.py (Updated)

```python
"""Batch scorer for the fraud-detection RandomForest.

Reads `input.csv` (one row per transaction, columns: amount, hour,
num_tx_past_day), runs every row through the pre-trained model, and
writes `predictions.csv` with the original columns plus an integer
`prediction` class-label column.
"""
import joblib
import pandas as pd

MODEL_PATH = "/root/code/serving/model.pkl"
INPUT_CSV = "/root/code/serving/input.csv"
OUTPUT_CSV = "/root/code/serving/predictions.csv"

# Load the model
model = joblib.load(MODEL_PATH)

# Read the input dataset
df = pd.read_csv(INPUT_CSV)

# Select the model features
features = df[["amount", "hour", "num_tx_past_day"]]

# Generate integer class-label predictions
df["prediction"] = model.predict(features).astype(int)

# Write predictions
df.to_csv(OUTPUT_CSV, index=False)

# Report number of rows written
print(f"Wrote {len(df)} rows to {OUTPUT_CSV}")
```

Run updated script

```shell
python3 /root/code/serving/batch_predict.py
```

Output

```shell
Wrote 10 rows to /root/code/serving/predictions.csv
```

### Verification

Confirm /root/code/serving/predictions.csv 
- exists
- output carries 3 input columns + prediction 
- prediction values are 0 or 1
- output row count matches input row count

```shell
cat /root/code/serving/predictions.csv
```

Output

```shell
amount,hour,num_tx_past_day,prediction
25.5,8,1,0
1250.0,22,4,1
45.0,12,2,0
890.0,2,3,0
3200.0,23,5,1
12.99,9,1,0
567.0,17,2,0
2100.0,1,4,1
33.5,13,2,0
78.0,10,1,0
```

