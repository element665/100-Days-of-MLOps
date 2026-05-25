Prompt

The xFusionCorp Industries ML team enforces code quality with `ruff` and `black` on every pull request. The project at `/root/code/fraud-detection/` currently fails both tools. Make it pass them.

1. The project at `/root/code/fraud-detection/` contains a `pyproject.toml` and sample sources under `src/`.
    
2. The corrected project must meet the following requirements:
    
    - `ruff` and `black` are both configured with a line length of `120`.
    - `ruff` lint rule selection includes `E`, `F`, `W`, and `I`, and is declared under `[tool.ruff.lint]` – The schema required by `ruff` 0.1 and later.
    - Running `ruff check src/` from the project directory exits with status `0`.
    - Running `black --check src/` from the project directory exits with status `0`.
3. Review the existing configuration and source files, and correct everything that prevents the two commands above from exiting cleanly.
    

`ruff`, `black`, and `mypy` are already installed.

---

Solution

Original pyproject.toml

```shell
[project]
name = "fraud-detection"
version = "0.1.0"

[tool.ruff]
line-length = 88
select = ["E", "F"]

[tool.black]
line-length = 100

```

Updated pyproject.toml

```shell
[project]
name = "fraud-detection"
version = "0.1.0"

[tool.ruff]
line-length = 120
[tool.ruff.lint]
select = ["E", "F", "W", "I"]

[tool.black]
line-length = 120

```

Execute ruff check

```shell
ruff check src/
```
	output
```shell
I001 [*] Import block is un-sorted or un-formatted
 --> src/data/process_data.py:1:1
  |
1 | / import os
2 | | import pandas as pd
  | |___________________^
  |
help: Organize imports

F401 [*] `os` imported but unused
 --> src/data/process_data.py:1:8
  |
1 | import os
  |        ^^
2 | import pandas as pd
  |
help: Remove unused import: `os`

Found 2 errors.
[*] 2 fixable with the `--fix` option.
```

2 errors found in check

```shell
Found 2 errors.
[*] 2 fixable with the `--fix` option.
```

Run ruff check command with '--fix'

```shell
ruff check src/ --fix
```
	output
```shell
Found 1 error (1 fixed, 0 remaining).
```

Execute ruff check again to verify success

```shell
ruff check src/
```
	output
```shell
All checks passed!
```

Execute black check

```shell
black --check src/
```
	output
```shell
All done! ✨ 🍰 ✨
5 files would be left unchanged.
```

Checks are now both successful
