Prompt

The xFusionCorp Industries data science team needs a standardised Python environment for their new ML project. Set up a virtual environment with the required ML libraries on the `controlplane` host.

1. Create a Python virtual environment named `ml-env`under `/root/code/` using `python3 -m venv`.
    
2. Activate the environment and install the following packages: `numpy`, `pandas`, `scikit-learn`, and `matplotlib`.
    
3. Generate a `requirements.txt` file using `pip freeze`and save it at `/root/code/requirements.txt`.

---

Solution

Create virtual environment

```shell
python3 -m venv ml-env
```

Navigate to new dir

```shell
cd ml-env/
```

Activate virt env

```shell
source bin/activate
```

Install required packages in virt env

```shell
python3 -m pip install numpy pandas scikit-learn matplotlib
```

Navigate to /root/code

```shell
cd /root/code
```

Create requirements.txt

```shell
touch requirements.txt
```

Freeze packages

```shell
pip freeze > requirements.txt
```

