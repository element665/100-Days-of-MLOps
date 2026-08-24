"""Stage 2 — Featurize.

Reads the upstream stage's output, engineers one derived column
(`amount_log = log1p(amount)`), and writes the feature matrix to
`data/features/features.csv` for the training stage to consume.

Feature engineering, column preservation, and on-disk layout are all
in place. Like every stage in the pipeline, this one must read its
immediate predecessor's output so the stage-chain invariant holds —
the row count out of this stage should match the row count the
preprocess stage produced.
"""
import os

import numpy as np
import pandas as pd
import yaml

os.chdir("/root/code/fraud-detection")

with open("configs/pipeline_config.yaml") as f:
    config = yaml.safe_load(f)

input_path = config["data"]["raw_path"]
features_path = config["data"]["features_path"]

df = pd.read_csv(input_path)
df["amount_log"] = np.log1p(df["amount"])

os.makedirs(os.path.dirname(features_path), exist_ok=True)
df.to_csv(features_path, index=False)

print(
    f"[featurize] input={input_path}  rows={len(df)}  "
    f"columns={len(df.columns)}"
)