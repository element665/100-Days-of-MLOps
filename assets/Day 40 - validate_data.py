"""Stage 1 — Data validation.

Loads the raw training CSV, verifies the expected schema and that no
nulls have leaked into the feature columns, and writes the result to
`reports/validation_status.json` as a status gate the rest of the
pipeline reads back.
"""
import json
import os
import sys

import pandas as pd

TRAIN_CSV = "/root/code/fraud-detection/data/train.csv"
REPORTS_DIR = "/root/code/fraud-detection/reports"
STATUS_JSON = os.path.join(REPORTS_DIR, "validation_status.json")

EXPECTED_COLUMNS = ["amount", "hour", "num_tx_past_day", "is_fraud"]


def main():
    df = pd.read_csv(TRAIN_CSV)

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        sys.exit(f"[validate] schema check failed — missing columns: {missing}")

    null_counts = df[EXPECTED_COLUMNS].isna().sum().to_dict()
    if any(v > 0 for v in null_counts.values()):
        sys.exit(f"[validate] null check failed — {null_counts}")

    status = {
        "status": "ok",
        "rows": int(len(df)),
        "columns": EXPECTED_COLUMNS,
    }
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(STATUS_JSON, "w") as f:
        json.dump(status, f, indent=2)
    print(f"[validate] {status}")


if __name__ == "__main__":
    main()