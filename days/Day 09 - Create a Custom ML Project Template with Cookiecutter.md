Prompt

The xFusionCorp Industries ML platform team maintains a Cookiecutter template that new ML projects are generated from. A draft template exists at `/root/code/mlops-template/`, but it does not render. Correct the template and use it to generate a project.

1. A Cookiecutter template exists at `/root/code/mlops-template/`. `cookiecutter` is installed system-wide.
    
2. The corrected template must satisfy every one of the following:
    
    - **The `cookiecutter.json` declares four variables:**
        - `project_name` (default `my-ml-project`)
        - `author` (default `xFusionCorp`)
        - `python_version` (default `3.11`)
        - `ml_framework` with the choices `sklearn`, `pytorch`, and `tensorflow`
    - **The generated `requirements.txt` logic:**
        - Contains `scikit-learn` when `ml_framework` is `sklearn`
        - Contains `torch` when `ml_framework` is `pytorch`
        - Contains `tensorflow` when `ml_framework` is `tensorflow`
    - **The generated `README.md` content:**
        - Must reference both the `project_name`and the `author` from cookiecutter variables.
    - **The template directory structure `{{cookiecutter.project_name}}/` must contain:**
        - **Files:** `README.md` and `requirements.txt`
        - **Directories:** `data/`, `models/`, `src/`, and `tests/`
3. Review the existing template in the VS Code explorer and correct everything that prevents it from rendering.
    
4. Once the template renders, generate a project at `/root/code/churn-model/`:
    

```
   cookiecutter /root/code/mlops-template/ -o /root/code/ --no-input project_name=churn-model ml_framework=sklearn
```

5. The generated project must contain a `requirements.txt` listing `scikit-learn` and a `README.md` that mentions `xFusionCorp`.

---

Solution

Original cookiecutter.json

```json
{
    "project_name": "my-ml-project",
    "author": "xFusionCorp",
    "python_version": "3.11"
}

```

Original requirements.txt

```
{% if cookiecutter.ml_framework = 'sklearn' %}
scikit-learn
{% elif cookiecutter.ml_framework = 'pytorch' %}
torch
{% elif cookiecutter.ml_framework = 'tensorflow' %}
tensorflow

```

Original README.md

```markdown
# {{cookiecutter.project_name}}

Created by {{ cookiecutter.Author }}.

```

Updated cookiecutter.json

- Add ml_framework to cookiecutter.json

```json
{
    "project_name": "my-ml-project",
    "author": "xFusionCorp",
    "python_version": "3.11",
    "ml_framework": ["sklearn", "pytorch", "tensorflow"]
}

```

Updated requirements.txt

- Update if conditional = -> ==
- Missing `{% endif %}`

```
{% if cookiecutter.ml_framework == 'sklearn' %}
scikit-learn
{% elif cookiecutter.ml_framework == 'pytorch' %}
torch
{% elif cookiecutter.ml_framework == 'tensorflow' %}
tensorflow
{% endif %}

```

 Updated README.md

- Correct author variable .Author -> .author

```markdown
# {{ cookiecutter.project_name }}

Created by {{ cookiecutter.author }}.
```

Template directory structure matches requirements

```shell
├──{{cookiecutter.project_name}}/
│    ├── data/
│    ├── models/
│    ├── src/
│    ├── tests/
│    ├── README.md
│    └── requirements.txt
```

Generate project

```shell
cookiecutter /root/code/mlops-template/ -o /root/code/ --no-input project_name=churn-model ml_framework=sklearn
```

Ensure new project matches template

```shell
├── churn-model/
│    ├── data/
│    ├── models/
│    ├── src/
│    ├── tests/
│    ├── README.md
│    └── requirements.txt
```

Generated project README.md

```markdown
# churn-model

Created by xFusionCorp.
```

Generated project requirements.txt

```
scikit-learn
```

---

Notes

```
* ml_framework must be a JSON array so Cookiecutter treats it as a
  choices variable — a plain string would be used as a literal default
  and the if/elif conditions in requirements.txt would never match
```