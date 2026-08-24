"""Stage 1 — Preprocess.

Reads raw transactions from `data/raw/train.csv`, drops the rows that
a production pipeline would reject (negligible-amount transactions
below $50 and any duplicates), and writes the cleaned dataset to
`data/processed/train_clean.csv`.

The row-count contract is load-bearing for the rest of the pipeline:
  raw_rows - dropped_rows = processed_rows  (≈192 rows, not 200).
If a later stage reads the raw file instead of this stage's output,
the row count in `data/features/features.csv` will not match and
the pipeline invariant is broken.
"""
import os

import pandas as pd
import yaml

os.chdir("/root/code/fraud-detection")

with open("configs/pipeline_config.yaml") as f:
    config = yaml.safe_load(f)

raw_path = config["data"]["raw_path"]
processed_path = config["data"]["processed_path"]

df = pd.read_csv(raw_path)
before = len(df)

df = df[df["amount"] >= 50].copy()
df = df.drop_duplicates().reset_index(drop=True)

os.makedirs(os.path.dirname(processed_path), exist_ok=True)
df.to_csv(processed_path, index=False)

print(
    f"[preprocess] raw_rows={before} -> processed_rows={len(df)}  "
    f"({before - len(df)} dropped)"
)