Prompt

The xFusionCorp Industries ML team uses a Makefile to orchestrate common tasks—data processing, training, testing, and cleanup. A draft `Makefile`exists at `/root/code/fraud-detection/Makefile`, but `make all` does not complete successfully. Bring the Makefile in line with the team's standard.

1. Change into `/root/code/fraud-detection/` and run `make all` to observe the current failure.
    
2. The corrected Makefile must declare the following six targets and behaviour:
    
    - `setup` – Creates a virtual environment at `mlops-venv/` and installs dependencies from `requirements.txt`;
    - `data` – Runs `python src/data/process_data.py`;
    - `train` – Runs `python src/models/train.py`;
    - `test` – Runs `pytest tests/`;
    - `clean` – Recursively removes every `__pycache__` directory, removes `.pytest_cache`, and clears the contents of `models/`;
    - `all` – Runs `setup`, `data`, `train`, and `test`in that order.
3. All six target names must be declared as `.PHONY` so that Make never confuses them with files of the same name.
    
4. After your changes, `make all` must complete without error.

Makefile recipes must be indented with a real tab character, not spaces. Make rejects any recipe that is not tab-indented.

---

Solution

Original Makefile (/root/code/fraud-detection/Makefile)

```shell
# fraud-detection Makefile

setup:
	python3 -m venv mlops-venv && mlops-venv/bin/pip install -r requirements.txt

data:
    python src/data/process_data.py

train:
	python src/models/train.py

test:
	pytest tests/

clean:
	rm -rf __pycache__

all: setup train test

```

Makefile issues:

- `data` is indented with spaces instead of a tab
- `all` is missing the `data` target
- `.PHONY` is missing
- `clean` does not fully meet requirements
- `all` should run in the order: `setup → data → train → test`

Corrected Makefile

```shell
# fraud-detection Makefile

.PHONY: setup data train test clean all

setup:
	python3 -m venv mlops-venv && mlops-venv/bin/pip install -r requirements.txt

data:
	python src/data/process_data.py

train:
	python src/models/train.py

test:
	pytest tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf models/*

all: setup data train test
```

Navigate to correct directory

```shell
cd /root/code/fraud-detection
```

Execute Makefile

```shell
make all
```

