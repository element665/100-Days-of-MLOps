Prompt

The xFusionCorp Industries ML platform team has deployed a fraud-detection model as a Docker image. However, the current runtime image includes all packages required for the training phase and the training source itself, resulting in an unnecessarily large image. Your objective is to refactor the single-stage `Dockerfile` located at `/root/code/ml-serve/`into a multi-stage build. This should comprise a builder stage that trains the model and generates `model.pkl`, followed by a runtime stage that installs only the dependencies necessary for serving and copies the trained model from the builder stage.

  

1. The Docker daemon is already running. `docker version` can be run in a VS Code terminal to confirm.
    
2. The project layout under `/root/code/ml-serve/`:
    
    - `train_model.py` – Fits a 10-tree RandomForest on the shared 10-row synthetic fraud set and writes `/app/model.pkl` via `joblib.dump(...)`. Correct and must remain intact.
    - `serve.py` – Flask app loading the model and exposing `POST /predict` + `GET /health` on port `8080`. Correct and must remain intact.
    - `Dockerfile` – A single-stage build that installs `scikit-learn`, `pandas`, `numpy`, `joblib`, and `flask`, runs the trainer at build time to bake the model in, and serves. The reader rewrites this file.
3. The end state must include:
    
    - The Dockerfile carries at least two `FROM`instructions; the first is given a name (e.g. `AS builder`) so a later stage can reference it.
    - The builder stage produces `/app/model.pkl`(the trained model).
    - The runtime stage contains `/app/model.pkl`(copied out of the builder stage) and `serve.py`.
    - The runtime stage's `pip install` line installs only the four packages `serve.py` needs: `flask`, `joblib`, `numpy`, `scikit-learn`.
    - `docker images ml-serve:v1` lists the built image; `docker run --rm -p 8090:8080 ml-serve:v1` exposes `/health` returning `{"status": "ok"}` on port `8090`.

> Multi-stage builds let you ship runtime images that carry only what the serving app needs — training dependencies and source files stay in the builder stage and are discarded. `docker build -t ml-serve:v1 .`can be re-run as each change lands; Docker re-uses cached layers when only runtime-stage lines change.

---

Solution

Dockerfile (Original)

```yaml
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir scikit-learn pandas numpy joblib flask

COPY train_model.py /app/train_model.py
COPY serve.py /app/serve.py

RUN python3 /app/train_model.py

EXPOSE 8080
CMD ["python3", "/app/serve.py"]
```

Dockerfile (Final)

```yaml
FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir scikit-learn pandas numpy joblib flask

COPY train_model.py /app/train_model.py

RUN python3 /app/train_model.py

FROM python:3.11-slim AS runtime

WORKDIR /app

COPY --from=builder /app/model.pkl /app/model.pkl
COPY serve.py /app/serve.py

RUN pip install --no-cache-dir scikit-learn numpy joblib flask

EXPOSE 8080
CMD ["python3", "/app/serve.py"]
```

Build image

```shell
docker build -t ml-serve:v1 .
```

Output

```shell
[+] Building 34.1s (13/13) FINISHED           docker:default
 => [internal] load build definition from Dockerfile    0.0s
 => => transferring dockerfile: 467B                    0.0s
 => [internal] load metadata for docker.io/library/pyt  1.1s
 => [internal] load .dockerignore                       0.0s
 => => transferring context: 2B                         0.0s
 => [builder 1/5] FROM docker.io/library/python:3.11-s  2.2s
 => => resolve docker.io/library/python:3.11-slim@sha2  0.0s
 => => sha256:0526d5e29bf341cb1941d46a6d4a 249B / 249B  0.1s
 => => sha256:58abdd9670ca8c69d03432 14.45MB / 14.45MB  0.4s
 => => sha256:41e7217c2e506d048f89ca0c 1.29MB / 1.29MB  0.4s
 => => sha256:6b37362b3da78869050b89 29.83MB / 29.83MB  0.6s
 => => extracting sha256:6b37362b3da78869050b894b799ad  0.6s
 => => extracting sha256:41e7217c2e506d048f89ca0c5cfef  0.2s
 => => extracting sha256:58abdd9670ca8c69d03432ce18899  0.6s
 => => extracting sha256:0526d5e29bf341cb1941d46a6d4ab  0.0s
 => [internal] load build context                       0.1s
 => => transferring context: 1.49kB                     0.0s
 => [builder 2/5] WORKDIR /app                          0.0s
 => [builder 3/5] RUN pip install --no-cache-dir scik  11.2s
 => [builder 4/5] COPY train_model.py /app/train_model  0.1s
 => [builder 5/5] RUN python3 /app/train_model.py       1.4s
 => [runtime 3/5] COPY --from=builder /app/model.pkl /  0.1s
 => [runtime 4/5] COPY serve.py /app/serve.py           0.1s
 => [runtime 5/5] RUN pip install --no-cache-dir sciki  8.5s
 => exporting to image                                  9.3s
 => => exporting layers                                 6.1s
 => => exporting manifest sha256:5d104b0c6bbae5c7a0cc8  0.0s
 => => exporting config sha256:2de46aed61e762de4e83c9c  0.0s
 => => exporting attestation manifest sha256:03137109d  0.0s
 => => exporting manifest list sha256:ae7374b9625e2ad8  0.0s
 => => naming to docker.io/library/ml-serve:v1          0.0s
 => => unpacking to docker.io/library/ml-serve:v1       3.0s
```

Confirm image exsits

```shell
docker images ml-serve:v1
```

Output

```shell
IMAGE         ID             DISK USAGE   CONTENT SIZE
ml-serve:v1   945ba2b8eb80        582MB          134MB
```

Run container to test image health

```shell
docker run --rm -p 8090:8080 ml-serve:v1
```

Output

```shell
 * Serving Flask app 'serve'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://172.17.0.2:8080
Press CTRL+C to quit
```

From a new terminal window check the /health of the flask app

```shell
curl http://localhost:8090/health
```

Output

```shell
{"status":"ok"}
```

** Lab requires quitting the Flask app before submitting for check