Prompt

A colleague has started a new ML project at `/root/code/fraud-detection/`, but the layout does not match the xFusionCorp Industries standard. Bring the project in line with the team's conventions.

  

1. Inspect the existing project at `/root/code/fraud-detection/`.
    
2. The final layout must match the tree below exactly:
    

```
fraud-detection/
├── data/
│   ├── raw/
│   └── processed/
├── models/
├── notebooks/
├── src/
│   ├── data/
│   ├── features/
│   ├── models/
│   └── utils/
├── tests/
├── configs/
├── requirements.txt
└── README.md
```

3. Every subdirectory under `src/` must contain an `__init__.py` file so that Python recognises it as a package.
    
4. `requirements.txt` must list the following dependencies, one per line: `scikit-learn`, `pandas`, `numpy`, and `mlflow`. The canonical PyPI name for the scikit-learn package is `scikit-learn`.
    
5. `README.md` must begin with the heading `# fraud-detection`.
    
6. Review the existing project and correct everything that does not match the requirements above.

---

Solution

Added folders as required for structure

```shell
fraud-detection/
├── data/
│   ├── raw/ # added
│   └── processed/ # added
│
├── tests/ # added
└── configs/ # added
```

Corrected directory names

```shell
├── src/
│   ├── features/ # added s
│   └── utils/ # added s
```

Corrected requirements.txt contents

```shell
scikit-learn # corrected name
pandas
numpy
mlflow # added
```

Corrected README.md first line

```shell
# fraud-detection
```

Ensured add subdirectories under src/ include file

```shell
__init__.py found under all subdirectories
```

