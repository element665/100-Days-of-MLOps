Prompt

The xFusionCorp Industries ML platform team stages a materialisation script (`materialize.sh`) under `/root/code/fraud-detection/feature_repo/` so the batch job that populates the Feast online store is always repeatable. The registry has already been applied against a correct `features.py`, but running the script writes zero rows into the online sqlite store. Your task is to correct `materialize.sh` so `./materialize.sh` populates the online store, then author `fetch_features.py` to read the features back via `store.get_online_features()` and confirm a non-null `amount` for a known customer.

  

1. The Feast UI is already running on port `8888`. The **Feast UI** button at the top of the lab can be opened to confirm—the dashboard loads the `fraud_detection`project, the `customer` entity, and the `customer_transaction_features` feature view. Materialisation status is not visible in the UI; the online store is inspected from the terminal.
    
2. The repository layout under `/root/code/fraud-detection/feature_repo/`:
    
    - `feature_store.yaml` – Local provider, sqlite online store at `data/online_store.db`. Correct.
    - `features.py` – Declares the `customer` entity (`join_keys=["customer_id"]`) and the `customer_transaction_features` view over the transactions source. Correct.
    - `data/transactions.parquet` – 200-row synthetic source, event timestamps from `2024-01-01` onward.
    - `data/registry.db` – Already written by `feast apply` at startup.
    - `materialize.sh` – Single-purpose shell script that calls `feast materialize-incremental "$END_DATE"`.
    - `fetch_features.py` – Reads features back from the online store; the `store.get_online_features(...)` call is left as a `# TODO`.
3. The end state must include:
    
    - `materialize.sh`'s end date is an ISO-8601 date on or after `2024-01-01`, and `data/online_store.db` is populated (on-disk size comfortably larger than the bare sqlite header, ≥ 4 KB).
    - `fetch_features.py` calls `store.get_online_features(features=["customer_transaction_features:amount", …], entity_rows=[{"customer_id": i}, …])`and writes `online_features.json`.
    - `online_features.json` carries at least one non-null `amount` value for a customer id present in the source.

> `feast materialize-incremental` takes a single ISO-8601 end date and uses the feature view's TTL to pick the start watermark on the first run. Run `./materialize.sh` and read its output — the summary line reports how many rows were written into the online store, which is where the zero shows up.

---

Provided Files

[feature_store.yaml](<../assets/Day 43 - feature_store.yaml>)
[feature.py](<../assets/Day 43 - features.py>)

---

Solution

fetch_features.py (Original)

```python
"""Read materialized features back from the Feast online store.

Materialisation only matters because downstream services then *read*
features for a live entity key. After `./materialize.sh` populates the
online store, this script fetches `customer_transaction_features` for a
few customers and writes the result to `online_features.json`.

Run from /root/code/fraud-detection/feature_repo/ AFTER materialize.sh.
"""
import json

from feast import FeatureStore

store = FeatureStore(repo_path=".")

# TODO: fetch the online features for customers 1 through 5 and bind the
# response dict to `result`. Call store.get_online_features(...) with:
#   features=[
#       "customer_transaction_features:amount",
#       "customer_transaction_features:hour",
#       "customer_transaction_features:num_tx_past_day",
#   ]
#   entity_rows=[{"customer_id": i} for i in range(1, 6)]
# then call .to_dict() on the response.
result = {}

with open("online_features.json", "w") as f:
    json.dump(result, f, indent=2, default=str)
print("wrote online_features.json:", result)
```

Update TODO section

```python
# TODO: fetch the online features for customers 1 through 5 and bind the
# response dict to `result`. Call store.get_online_features(...) with:
#   features=[
#       "customer_transaction_features:amount",
#       "customer_transaction_features:hour",
#       "customer_transaction_features:num_tx_past_day",
#   ]
#   entity_rows=[{"customer_id": i} for i in range(1, 6)]
# then call .to_dict() on the response.
result = store.get_online_features(
    features=[
        "customer_transaction_features:amount",
        "customer_transaction_features:hour",
        "customer_transaction_features:num_tx_past_day",
    ],
    entity_rows=[{"customer_id": i} for i in range(1, 6)],
).to_dict() 
```

materialize.sh (original)

```shell
#!/bin/bash
# Materialize the fraud-detection feature views into the online
# store. Feast's materialize-incremental command writes every
# event whose timestamp is between the view's last-materialized
# watermark (or the TTL-based fallback) and the given end date.
#
# Run from /root/code/fraud-detection/feature_repo/.
set -euo pipefail

cd "$(dirname "$0")"

END_DATE="1970-12-31T00:00:00"

feast materialize-incremental "$END_DATE"
```

Update END_DATE for materialize.sh

```shell
END_DATE="2024-01-31T00:00:00"
```

Run materialize script

```shell
./materialize.sh
```

Output

```shell
Materializing 1 feature views to 2024-01-31 00:00:00+00:00 into the sqlite online store.

customer_transaction_features from 2016-09-06 15:37:02+00:00 to 2024-01-31 00:00:00+00:00:
```

Run corrected fetch_features script

```shell
python fetch_features.py
```

Output

```shell
wrote online_features.json: {'customer_id': [1, 2, 3, 4, 5], 'amount': [822.4299926757812, 802.9400024414062, 214.6199951171875, 222.44000244140625, 868.530029296875], 'hour': [2, 19, 4, 1, 0], 'num_tx_past_day': [1, 0, 2, 2, 5]}
```

**Verification

confirm data/online_store.db is populated

```
ls -lh data/online_store.db
```

Output

```shell
-rw-r--r-- 1 root root 16K Sep  4 11:37 data/online_store.db
```

Check that script wrote to online_features.json

```shell
cat online_features.json
```

Output

```json
{
  "customer_id": [
    1,
    2,
    3,
    4,
    5
  ],
  "amount": [
    822.4299926757812,
    802.9400024414062,
    214.6199951171875,
    222.44000244140625,
    868.530029296875
  ],
  "hour": [
    2,
    19,
    4,
    1,
    0
  ],
  "num_tx_past_day": [
    1,
    0,
    2,
    2,
    5
  ]
}
```
