Prompt

The xFusionCorp Industries ML platform team requires data-schema contracts for every batch that feeds the fraud-detector model. It is essential to identify malformed rows upstream of the training process, rather than three hours later in production. A Great Expectations project has already been initialized at `/root/code/dataquality/gx/`, featuring a pandas data source that reads from `data/transactions.csv`, an empty `fraud_schema`suite, and a `default` checkpoint configured to publish results to Data Docs with each run. Your task is to populate the suite with four expectations and execute the checkpoint to ensure that Data Docs reflects a green status for these expectations.

  

The platform's **data contract** for a transactions batch is:

- **Schema** — every batch must carry exactly these columns: `amount`, `hour`, `num_tx_past_day`, `is_fraud`.
- **`amount`** — a transaction amount; it is never negative.
- **`hour`** — the hour-of-day the transaction occurred.
- **`is_fraud`** — a binary label.

`/root/code/dataquality/author_expectations.py` carries four numbered TODOs, each naming the Great Expectations class that encodes one contract rule (imports for `great_expectations as gx` and `great_expectations.expectations as ge` are already in place):

- **TODO 1:** `ExpectTableColumnsToMatchSet` — the required column set.
- **TODO 2:** `ExpectColumnValuesToBeBetween` on `amount`.
- **TODO 3:** `ExpectColumnValuesToBeBetween` on `hour`.
- **TODO 4:** `ExpectColumnValuesToBeInSet` on `is_fraud`.

Running the script persists the suite to disk (`gx/expectations/fraud_schema.json`) and executes the `default` checkpoint, which validates `transactions.csv`against the suite and refreshes the Data Docs site. Data Docs is available from the **Data Docs** button at the top of the lab (port `8081`), where each `fraud_schema` run renders with a green or red pill per expectation.

The end state must include:

- `gx/expectations/fraud_schema.json` has all four expectations by type (`expect_table_columns_to_match_set`, two `expect_column_values_to_be_between` entries – One per column — and `expect_column_values_to_be_in_set`).
- Each expectation's kwargs encode the data contract above.
- The most recent validation JSON under `gx/uncommitted/validations/` has `success: true`.
- The Data Docs index page served on `:8081`references `fraud_schema`.

> Great Expectations treats data quality as code—expectation suites are versioned artefacts in the same repo as the model that consumes the data, run by the same CI that runs pytest. A run's result JSON is machine-readable (a downstream CI-gate lab consumes it), and Data Docs is the human-readable rendering of the same content. This task lays the ground for both.

---

Solution

author_expectations.py (Original)

```python
"""Author the fraud_schema expectation suite and run the default checkpoint.

Startup has already initialised the Great Expectations project,
registered a pandas data source over ``data/transactions.csv``,
created an empty ``fraud_schema`` suite, and wired it into a
``default`` checkpoint that refreshes Data Docs on every run. The
only missing piece is the expectations themselves -- add them in
the TODO block below, then execute the file.
"""
from __future__ import annotations

import great_expectations as gx
import great_expectations.expectations as ge

PROJECT_ROOT = "/root/code/dataquality"   # GE creates <root>/gx/ as home
SUITE_NAME = "fraud_schema"
CHECKPOINT_NAME = "default"


def main() -> None:
    context = gx.get_context(mode="file", project_root_dir=PROJECT_ROOT)

    # Self-healing: if the startup scaffold skipped the suite for any
    # reason, add_or_update still returns a fresh empty one.
    suite = context.suites.add_or_update(
        gx.ExpectationSuite(name=SUITE_NAME),
    )
    suite.expectations = []  # start clean on every authoring pass

    # ------------------------------------------------------------------
    # Encode the platform's data contract as four expectations. Each
    # TODO names the Great Expectations class to use; supply the
    # keyword arguments that express the rule, and register each one
    # with suite.add_expectation(...).
    #
    # TODO 1: Schema -- every batch must carry exactly these columns:
    #         amount, hour, num_tx_past_day, is_fraud.
    #         Use ge.ExpectTableColumnsToMatchSet (column_set=...).
    #
    # TODO 2: `amount` is a transaction amount and is never negative.
    #         Use ge.ExpectColumnValuesToBeBetween on column "amount".
    #
    # TODO 3: `hour` is the hour-of-day the transaction occurred.
    #         Use ge.ExpectColumnValuesToBeBetween on column "hour".
    #
    # TODO 4: `is_fraud` is a binary label.
    #         Use ge.ExpectColumnValuesToBeInSet on column "is_fraud".
    # ------------------------------------------------------------------

    # (expectations go here)

    context.suites.add_or_update(suite)
    print(f"Persisted {len(suite.expectations)} expectations to `{SUITE_NAME}`")

    checkpoint = context.checkpoints.get(name=CHECKPOINT_NAME)
    result = checkpoint.run()
    print(f"Checkpoint `{CHECKPOINT_NAME}` result: success={result.success}")


if __name__ == "__main__":
    main()
```

author_expectations.py (Updated)

```python
"""Author the fraud_schema expectation suite and run the default checkpoint.

Startup has already initialised the Great Expectations project,
registered a pandas data source over ``data/transactions.csv``,
created an empty ``fraud_schema`` suite, and wired it into a
``default`` checkpoint that refreshes Data Docs on every run. The
only missing piece is the expectations themselves -- add them in
the TODO block below, then execute the file.
"""
from __future__ import annotations

import great_expectations as gx
import great_expectations.expectations as ge

PROJECT_ROOT = "/root/code/dataquality"   # GE creates <root>/gx/ as home
SUITE_NAME = "fraud_schema"
CHECKPOINT_NAME = "default"


def main() -> None:
    context = gx.get_context(mode="file", project_root_dir=PROJECT_ROOT)

    # Self-healing: if the startup scaffold skipped the suite for any
    # reason, add_or_update still returns a fresh empty one.
    suite = context.suites.add_or_update(
        gx.ExpectationSuite(name=SUITE_NAME),
    )
    suite.expectations = []  # start clean on every authoring pass

    # ------------------------------------------------------------------
    # Encode the platform's data contract as four expectations. Each
    # TODO names the Great Expectations class to use; supply the
    # keyword arguments that express the rule, and register each one
    # with suite.add_expectation(...).
    #
    # TODO 1: Schema -- every batch must carry exactly these columns:
    #         amount, hour, num_tx_past_day, is_fraud.
    #         Use ge.ExpectTableColumnsToMatchSet (column_set=...).
    #
    # TODO 2: `amount` is a transaction amount and is never negative.
    #         Use ge.ExpectColumnValuesToBeBetween on column "amount".
    #
    # TODO 3: `hour` is the hour-of-day the transaction occurred.
    #         Use ge.ExpectColumnValuesToBeBetween on column "hour".
    #
    # TODO 4: `is_fraud` is a binary label.
    #         Use ge.ExpectColumnValuesToBeInSet on column "is_fraud".
    # ------------------------------------------------------------------

    # (expectations go here)
    
    suite.add_expectation(
	    ge.ExpectTableColumnsToMatchSet(
	        column_set=[
	        "amount",
	        "hour",
	        "num_tx_past_day",
	        "is_fraud"
	        ]
	    )
	)
    
    suite.add_expectation(
	    ge.ExpectColumnValuesToBeBetween(
		    column="amount",
		    min_value=0
		)
	)	
    
    suite.add_expectation(
	    ge.ExpectColumnValuesToBeBetween(
		    column="hour",
		    min_value=0,
		    max_value=23
		)
	)	
    
    suite.add_expectation(
	    ge.ExpectColumnValuesToBeInSet(
		    column="is_fraud",
		    value_set=[0, 1]
		)
    )
    
    context.suites.add_or_update(suite)
    print(f"Persisted {len(suite.expectations)} expectations to `{SUITE_NAME}`")

    checkpoint = context.checkpoints.get(name=CHECKPOINT_NAME)
    result = checkpoint.run()
    print(f"Checkpoint `{CHECKPOINT_NAME}` result: success={result.success}")


if __name__ == "__main__":
    main()
```

Screenshot of Data Doc starting point

![start](<../screenshots/Screenshot Day 46 starting point.png>)

![details](<../screenshots/Screenshot Day 46 start details.png>)

Run updated script

```shell
python /root/code/dataquality/author_expectations.py
```

Output

```shell
Persisted 4 expectations to `fraud_schema`
Calculating Metrics: 100%|█| 27/27 [00:00<00:00, 8924.75it/s
Checkpoint `default` result: success=True
```

Verification updated Data Doc screenshot

![end](<../screenshots/Screenshot Day 46 after script.png>)

![details](<../screenshots/Screenshot Day 46 updated details.png>)