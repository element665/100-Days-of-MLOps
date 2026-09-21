Prompt

The xFusionCorp Industries ML platform team has extended the `fraud_schema` suite to include a second batch—`data/transactions_drifted.csv`, which consists of a week's worth of real production data. The `drift_check` checkpoint executes the existing suite against this file and fails on its initial run. Your objective is to utilize Data Docs to identify which expectation failed and the reason for the failure, modify the offending bound in the fix-script, re-run the checkpoint, and verify that Data Docs reflects a successful outcome.

  

Data Docs is available from the **Data Docs** button (port `8081`). The landing page lists two past validation runs under `fraud_schema`:

- **`default`** – green (against the clean `transactions.csv`).
- **`drift_check`** – **red** (against the drifted file).

To see the failure, re-run the checkpoint and read its output:

```
python3 /root/code/dataquality/fix_drift.py
```

The red `drift_check` run on Data Docs is the debug surface: it names the failing expectation and shows the observed batch values.

`/root/code/dataquality/fix_drift.py` already contains all four expectations. Adjusting the offending expectation so it admits the observed values—rather than deleting any expectation—and re-running the script re-persists the suite and re-executes the `drift_check` checkpoint, turning the most recent `drift_check` run green.

The end state must include:

- The `drift_check` checkpoint is still present in `gx/checkpoints/`.
- `gx/expectations/fraud_schema.json` still has all four core expectation types (the fix is a widening, not a deletion).
- The most recent validation JSON under `gx/uncommitted/validations/` for checkpoint `drift_check` reports `success: true`.

> The failing-validation page is the core debug surface for data-quality incidents: it tells you WHICH expectation failed, WHAT was observed, and by how much. A real team uses that same signal to decide whether the data genuinely drifted (update the rule) or whether the data is broken (fix upstream). Either way, the read-the-evidence step comes first.

---

Solution

fix_drift.py (Original)

```python
"""Re-author the fraud_schema suite and re-run the drift_check checkpoint.

Startup has populated the ``fraud_schema`` suite with its baseline four
expectations and generated ``data/transactions_drifted.csv`` -- a week
of production rows. The ``drift_check`` checkpoint runs this suite
against the drifted file and currently FAILS on its first run.

Use Data Docs (the red ``drift_check`` run) to identify which
expectation failed and what the batch actually contains, then adjust
that expectation below so the checkpoint passes. Do not delete
expectations -- the fix is a widening.

Re-run after editing:
    python3 /root/code/dataquality/fix_drift.py
"""
from __future__ import annotations

import great_expectations as gx
import great_expectations.expectations as ge

PROJECT_ROOT = "/root/code/dataquality"   # GE creates <root>/gx/ as home
SUITE_NAME = "fraud_schema"
CHECKPOINT_NAME = "drift_check"


def main() -> None:
    context = gx.get_context(mode="file", project_root_dir=PROJECT_ROOT)

    # Self-healing: if the startup scaffold skipped the suite for any
    # reason, add_or_update still returns a fresh empty one.
    suite = context.suites.add_or_update(
        gx.ExpectationSuite(name=SUITE_NAME),
    )
    suite.expectations = []  # re-author cleanly each run

    # One of the four expectations below rejects the drifted batch. The
    # red drift_check run on Data Docs shows which expectation failed
    # and the observed values -- adjust that expectation's bound so the
    # batch passes (a widening with a little headroom, not a deletion).
    suite.add_expectation(
        ge.ExpectTableColumnsToMatchSet(
            column_set=["amount", "hour", "num_tx_past_day", "is_fraud"],
        )
    )

    suite.add_expectation(
        ge.ExpectColumnValuesToBeBetween(column="amount", min_value=0)
    )

    suite.add_expectation(
        ge.ExpectColumnValuesToBeBetween(
            column="hour", min_value=0, max_value=23,
        )
    )
    suite.add_expectation(
        ge.ExpectColumnValuesToBeInSet(column="is_fraud", value_set=[0, 1])
    )

    context.suites.add_or_update(suite)
    print(f"Persisted {len(suite.expectations)} expectations to `{SUITE_NAME}`")

    checkpoint = context.checkpoints.get(name=CHECKPOINT_NAME)
    result = checkpoint.run()
    print(f"Checkpoint `{CHECKPOINT_NAME}` result: success={result.success}")


if __name__ == "__main__":
    main()
```

Great Expectations starting point

![screenshot](<../screenshots/Screenshot Day 47 Great Expectations Start.png>)


Re-run checkpoint to see failure as instructed

```shell
python3 /root/code/dataquality/fix_drift.py
```

Output

```shell
Persisted 4 expectations to `fraud_schema`
Calculating Metrics: 100%|█| 27/27 [00:00<00:00, 9506.10it/s
Checkpoint `drift_check` result: success=False
```

Great Expectations updated with failed validation

![screenshot](<../screenshots/Screenshot Day 47 Great Expectations failed check.png>)


- Correct the script to include the negative integers
	Change amount from min_value=0
		ge.ExpectColumnValuesToBeBetween(column="amount", min_value=0)
	To min_value=-500 (or any value below -347.22 with requested headroom)
	ge.ExpectColumnValuesToBeBetween(column="amount", min_value=-500)


fix_drift.py (Updated)

```python
"""Re-author the fraud_schema suite and re-run the drift_check checkpoint.

Startup has populated the ``fraud_schema`` suite with its baseline four
expectations and generated ``data/transactions_drifted.csv`` -- a week
of production rows. The ``drift_check`` checkpoint runs this suite
against the drifted file and currently FAILS on its first run.

Use Data Docs (the red ``drift_check`` run) to identify which
expectation failed and what the batch actually contains, then adjust
that expectation below so the checkpoint passes. Do not delete
expectations -- the fix is a widening.

Re-run after editing:
    python3 /root/code/dataquality/fix_drift.py
"""
from __future__ import annotations

import great_expectations as gx
import great_expectations.expectations as ge

PROJECT_ROOT = "/root/code/dataquality"   # GE creates <root>/gx/ as home
SUITE_NAME = "fraud_schema"
CHECKPOINT_NAME = "drift_check"


def main() -> None:
    context = gx.get_context(mode="file", project_root_dir=PROJECT_ROOT)

    # Self-healing: if the startup scaffold skipped the suite for any
    # reason, add_or_update still returns a fresh empty one.
    suite = context.suites.add_or_update(
        gx.ExpectationSuite(name=SUITE_NAME),
    )
    suite.expectations = []  # re-author cleanly each run

    # One of the four expectations below rejects the drifted batch. The
    # red drift_check run on Data Docs shows which expectation failed
    # and the observed values -- adjust that expectation's bound so the
    # batch passes (a widening with a little headroom, not a deletion).
    suite.add_expectation(
        ge.ExpectTableColumnsToMatchSet(
            column_set=["amount", "hour", "num_tx_past_day", "is_fraud"],
        )
    )

    suite.add_expectation(
        ge.ExpectColumnValuesToBeBetween(column="amount", min_value=-500)
    )

    suite.add_expectation(
        ge.ExpectColumnValuesToBeBetween(
            column="hour", min_value=0, max_value=23,
        )
    )
    suite.add_expectation(
        ge.ExpectColumnValuesToBeInSet(column="is_fraud", value_set=[0, 1])
    )

    context.suites.add_or_update(suite)
    print(f"Persisted {len(suite.expectations)} expectations to `{SUITE_NAME}`")

    checkpoint = context.checkpoints.get(name=CHECKPOINT_NAME)
    result = checkpoint.run()
    print(f"Checkpoint `{CHECKPOINT_NAME}` result: success={result.success}")


if __name__ == "__main__":
    main()
```

Run the corrected script

```shell
python3 /root/code/dataquality/fix_drift.py
```

Output

```shell
Persisted 4 expectations to `fraud_schema`
Calculating Metrics: 100%|█████████████████████████████████████████████| 27/27 [00:00<00:00, 8854.28it/s]
Checkpoint `drift_check` result: success=True
```

Great Expectations successful validation

![screenshot](<../screenshots/Screenshot Day 47 Great Expectations successful validation.png>)

![screenshot](<../screenshots/Screenshot Day 47 Great Expectations validation details.png>)

---

**Verification

- drift_check is still present in gx/checkpoints/

![screenshot](<../screenshots/Screenshot Day 47 drift_check json.png>)

- `gx/expectations/fraud_schema.json` still has all four core expectation types

```json
{
  "expectations": [
    {
      "id": "77d892af-15c9-43cb-b4a6-9e5509e6bfa3",
      "kwargs": {
        "column_set": [
          "amount",
          "hour",
          "num_tx_past_day",
          "is_fraud"
        ]
      },
      "meta": {},
      "severity": "critical",
      "type": "expect_table_columns_to_match_set"
    },
    {
      "id": "802bddb7-0d1b-4391-aa05-389c834e8cb2",
      "kwargs": {
        "column": "amount",
        "min_value": -500.0
      },
      "meta": {},
      "severity": "critical",
      "type": "expect_column_values_to_be_between"
    },
    {
      "id": "848a94c4-3a86-45e6-8ee0-40970b4d51a2",
      "kwargs": {
        "column": "hour",
        "max_value": 23.0,
        "min_value": 0.0
      },
      "meta": {},
      "severity": "critical",
      "type": "expect_column_values_to_be_between"
    },
    {
      "id": "cf2c7bb0-e5ab-4187-8033-d9ddb936ec3b",
      "kwargs": {
        "column": "is_fraud",
        "value_set": [
          0,
          1
        ]
      },
      "meta": {},
      "severity": "critical",
      "type": "expect_column_values_to_be_in_set"
    }
  ],
  "id": "97bbf9a6-2fb5-4fed-a823-b6f35e50d605",
  "meta": {
    "great_expectations_version": "1.18.2"
  },
  "name": "fraud_schema",
  "notes": null
}
```

Confirm 'success: true' in most recent validation

```shell
cat transactions_source-transactions_drifted.json | grep -i success
```

Output

```shell
      "success": true
      "success": true
      "success": true
      "success": true
    "success_percent": 100.0,
    "successful_expectations": 4,
    "unsuccessful_expectations": 0
  "success": true,
```
