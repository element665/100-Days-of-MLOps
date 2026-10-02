Prompt

The xFusionCorp Industries ML platform team operates a shell-based Docker CI pipeline for the fraud-detection Flask service. In this process, tests are executed, the image is built, a short git SHA is applied as the tag, and the tagged image is subsequently pushed to the local private registry. However, the pre-staged `build.sh` located at `/root/code/ci/` does not currently execute cleanly from start to finish. Your objective is to rectify the configuration so that `./build.sh` completes its execution without errors and that the registry catalog displays `ml-ci-app`tagged with the current git short SHA.

  

1. The Docker daemon is already running and a `registry:2` container named `local-registry` is already up on host port `5555`.
    
2. The repository layout under `/root/code/ci/`:
    
    - `app/app.py` – Flask service exposing `/health`+ `/predict` on port 8086. Correct.
    - `app/test_app.py` – Three pytest cases covering `/health`, the fraud-flag flow, and the pass-through flow. Correct.
    - `app/Dockerfile` – `python:3.11-slim`, installs flask, COPYs `app.py`, exposes 8086, runs the Flask app. Correct.
    - `app/.git/` – A local git repository initialised at startup with a single "Initial CI baseline" commit. Correct.
    - `build.sh` – Executable shell script with four stages (test → build → tag → push). Needs attention.
3. The end state must include:
    
    - `./build.sh` runs end-to-end without non-zero exit.
    - `docker images ml-ci-app:latest` lists the locally-built image.
    - `curl http://localhost:5555/v2/_catalog` lists `ml-ci-app` in the `repositories` array.
    - `curl http://localhost:5555/v2/ml-ci-app/tags/list` lists the current `git -C app rev-parse --short HEAD` value in the `tags`array.

> Run `./build.sh` against the scaffold as-is; each re-run surfaces the next blocker. All fixes live inside `build.sh`.

---

Solution

build.sh (Original)

```shell
#!/bin/bash
# Shell-based CI pipeline for the ml-ci-app image.
#
# Stages: test -> build -> tag (git SHA) -> push to local registry.
# Run from /root/code/ci/.
set -euo pipefail

cd "$(dirname "$0")"

IMAGE="ml-ci-app"
REGISTRY="localhost:5000"

# --- Stage 1: test
echo "[ci] stage 1/4 — running tests"
python3 -m pytest app/tests/

# --- Stage 2: build
echo "[ci] stage 2/4 — building image"
docker build -t "$IMAGE:latest" app/

# --- Stage 3: tag with short git SHA
echo "[ci] stage 3/4 — tagging"
SHA=$(git -C app rev-parse --short HEAD)
TAGGED="$REGISTRY/$IMAGE:$GIT_SHA"
docker tag "$IMAGE:latest" "$TAGGED"

# --- Stage 4: push
echo "[ci] stage 4/4 — pushing"
docker push "$TAGGED"

echo "[ci] complete: $TAGGED"
```

Run script against scaffold as-is per instructions

```shell
./build.sh
```

Output

```shell
[ci] stage 1/4 — running tests
==================== test session starts ====================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
rootdir: /root/code/ci
plugins: hydra-core-1.3.7, testinfra-10.2.2, Faker-40.40.0, typeguard-4.6.0, platformdirs-4.12.2, anyio-4.15.1
collected 0 items                                           

=================== no tests ran in 0.00s ===================
ERROR: file or directory not found: app/tests/
```

Script points to incorrect test path in stage 1 (app/tests/ -> app/test_app.py)

```shell
# --- Stage 1: test
echo "[ci] stage 1/4 — running tests"
python3 -m pytest app/test_app.py
```

Output

```shell
[ci] stage 1/4 — running tests
==================== test session starts ====================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
rootdir: /root/code/ci
plugins: hydra-core-1.3.7, Faker-40.40.0, testinfra-10.2.2, typeguard-4.6.0, platformdirs-4.12.2, anyio-4.15.1
collected 3 items                                           

app/test_app.py ...                                   [100%]

===================== 3 passed in 0.14s =====================
[ci] stage 2/4 — building image
[+] Building 13.6s (9/9) FINISHED                                                          docker:default
 => [internal] load build definition from Dockerfile                                                 0.1s
 => => transferring dockerfile: 181B                                                                 0.0s
 => [internal] load metadata for docker.io/library/python:3.11-slim                                  1.2s
 => [internal] load .dockerignore                                                                    0.1s
 => => transferring context: 2B                                                                      0.0s
 => [internal] load build context                                                                    0.1s
 => => transferring context: 732B                                                                    0.0s
 => [1/4] FROM docker.io/library/python:3.11-slim@sha256:bab1b7ef4b450c81002278d035eff85ebe394ae94d  3.8s
 => => resolve docker.io/library/python:3.11-slim@sha256:bab1b7ef4b450c81002278d035eff85ebe394ae94d  0.0s
 => => sha256:48355dfcbf9e05ad2daf9d9506583bdb41b02ff7d67a5f2b239217e09320604c 250B / 250B           0.1s
 => => sha256:295f1967d0454b54c78432d56f412a274da4b46e92cdf5679aea04fbd47b9c36 14.46MB / 14.46MB     0.4s
 => => sha256:f64163c1b799b4915c58c0439006ebe6e393a8c346d2393f08fa0ca74e306f6e 4.27MB / 4.27MB       0.4s
 => => sha256:6b37362b3da78869050b894b799ad4df04f1f3b52774087db0d81151570244c8 29.83MB / 29.83MB     1.0s
 => => extracting sha256:6b37362b3da78869050b894b799ad4df04f1f3b52774087db0d81151570244c8            0.6s
 => => extracting sha256:f64163c1b799b4915c58c0439006ebe6e393a8c346d2393f08fa0ca74e306f6e            0.9s
 => => extracting sha256:295f1967d0454b54c78432d56f412a274da4b46e92cdf5679aea04fbd47b9c36            0.9s
 => => extracting sha256:48355dfcbf9e05ad2daf9d9506583bdb41b02ff7d67a5f2b239217e09320604c            0.1s
 => [2/4] WORKDIR /app                                                                               0.1s
 => [3/4] RUN pip install --no-cache-dir flask                                                       3.5s
 => [4/4] COPY app.py /app/app.py                                                                    0.1s
 => exporting to image                                                                               4.5s
 => => exporting layers                                                                              0.5s
 => => exporting manifest sha256:afc29d4e912acafb0f90b609384742edb853fdffa250fbcde6c85b40341a0465    0.0s
 => => exporting config sha256:b6604cd2437b9c90a5c4bf1fa626fdd804b171ace2187edfe266cd32a54c57e8      0.0s
 => => exporting attestation manifest sha256:5bfbedd59dec61ca6057cb23b7d3a2c9fea858d129b2aa01892e1b  0.0s
 => => exporting manifest list sha256:4efd48de80e1e47a7052cf7f834af220841460d9cd4b0833e6681347013e3  0.0s
 => => naming to docker.io/library/ml-ci-app:latest                                                  0.0s
 => => unpacking to docker.io/library/ml-ci-app:latest                                               3.9s
[ci] stage 3/4 — tagging
./build.sh: line 24: GIT_SHA: unbound variable
```

SHA variable is incorrectly referenced in Stage 3 (GIT_SHA -> SHA)

```shell
# --- Stage 3: tag with short git SHA
echo "[ci] stage 3/4 — tagging"
SHA=$(git -C app rev-parse --short HEAD)
TAGGED="$REGISTRY/$IMAGE:$SHA"
docker tag "$IMAGE:latest" "$TAGGED"
```

Output

```shell
...SAME AS PREVIOUS
[ci] stage 3/4 — tagging
[ci] stage 4/4 — pushing
The push refers to repository [localhost:5000/ml-ci-app]
f64163c1b799: Waiting 
44136fa355b3: Waiting 
6b37362b3da7: Waiting 
0c4755f9880a: Waiting 
failed to do request: Head "https://localhost:5000/v2/ml-ci-app/blobs/sha256:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a": dial tcp [::1]:5000: connect: connection refused
```

REGISTRY has incorrect port mapped (5000 -> 5555)

```shell
REGISTRY="localhost:5555"
```

Output

```shell
[ci] stage 1/4 — running tests
========================================== test session starts ===========================================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
rootdir: /root/code/ci
plugins: hydra-core-1.3.7, Faker-40.40.0, testinfra-10.2.2, typeguard-4.6.0, platformdirs-4.12.2, anyio-4.15.1
collected 3 items                                                                                        

app/test_app.py ...                                                                                [100%]

=========================================== 3 passed in 0.07s ============================================
[ci] stage 2/4 — building image
[+] Building 0.7s (9/9) FINISHED                                                           docker:default
 => [internal] load build definition from Dockerfile                                                 0.0s
 => => transferring dockerfile: 181B                                                                 0.0s
 => [internal] load metadata for docker.io/library/python:3.11-slim                                  0.5s
 => [internal] load .dockerignore                                                                    0.0s
 => => transferring context: 2B                                                                      0.0s
 => [1/4] FROM docker.io/library/python:3.11-slim@sha256:bab1b7ef4b450c81002278d035eff85ebe394ae94d  0.0s
 => => resolve docker.io/library/python:3.11-slim@sha256:bab1b7ef4b450c81002278d035eff85ebe394ae94d  0.0s
 => [internal] load build context                                                                    0.0s
 => => transferring context: 28B                                                                     0.0s
 => CACHED [2/4] WORKDIR /app                                                                        0.0s
 => CACHED [3/4] RUN pip install --no-cache-dir flask                                                0.0s
 => CACHED [4/4] COPY app.py /app/app.py                                                             0.0s
 => exporting to image                                                                               0.1s
 => => exporting layers                                                                              0.0s
 => => exporting manifest sha256:afc29d4e912acafb0f90b609384742edb853fdffa250fbcde6c85b40341a0465    0.0s
 => => exporting config sha256:b6604cd2437b9c90a5c4bf1fa626fdd804b171ace2187edfe266cd32a54c57e8      0.0s
 => => exporting attestation manifest sha256:ecd0d75c02790319f64bd9e3ae37a934fad0ec07c758ec72d3fcb8  0.0s
 => => exporting manifest list sha256:494fd7a8e54b2d1e776db71fb619cdcab53b60ca4cc2ea40d93443d9179ff  0.0s
 => => naming to docker.io/library/ml-ci-app:latest                                                  0.0s
 => => unpacking to docker.io/library/ml-ci-app:latest                                               0.0s
[ci] stage 3/4 — tagging
[ci] stage 4/4 — pushing
The push refers to repository [localhost:5555/ml-ci-app]
f64163c1b799: Pushed 
e39b9be7b679: Pushed 
44136fa355b3: Pushed 
6b37362b3da7: Pushed 
31c6791c6a3d: Pushed 
295f1967d045: Pushed 
48355dfcbf9e: Pushed 
05c717662ad5: Pushed 
9ae33e072d5b: Pushed 
be76f77: digest: sha256:494fd7a8e54b2d1e776db71fb619cdcab53b60ca4cc2ea40d93443d9179ff105 size: 856
[ci] complete: localhost:5555/ml-ci-app:be76f77
```

build.sh (Final)

```shell
#!/bin/bash
# Shell-based CI pipeline for the ml-ci-app image.
#
# Stages: test -> build -> tag (git SHA) -> push to local registry.
# Run from /root/code/ci/.
set -euo pipefail

cd "$(dirname "$0")"

IMAGE="ml-ci-app"
REGISTRY="localhost:5555"

# --- Stage 1: test
echo "[ci] stage 1/4 — running tests"
python3 -m pytest app/test_app.py

# --- Stage 2: build
echo "[ci] stage 2/4 — building image"
docker build -t "$IMAGE:latest" app/

# --- Stage 3: tag with short git SHA
echo "[ci] stage 3/4 — tagging"
SHA=$(git -C app rev-parse --short HEAD)
TAGGED="$REGISTRY/$IMAGE:$SHA"
docker tag "$IMAGE:latest" "$TAGGED"

# --- Stage 4: push
echo "[ci] stage 4/4 — pushing"
docker push "$TAGGED"

echo "[ci] complete: $TAGGED"
```

### Verification

Exit code for script

```shell
echo $?
```

Output

```shell
0
```

Image is listed locally

```shell
docker images ml-ci-app:latest
```

Output

```shell
IMAGE              ID             DISK USAGE   CONTENT SIZE   EXTRA
ml-ci-app:latest   494fd7a8e54b        223MB         54.3MB        
```

Confirm 'ml-ci-app' exists in 'repositories'

```shell
curl http://localhost:5555/v2/_catalog
```

Output

```JSON
{"repositories":["ml-ci-app"]}
```

Confirm registry image is tagged with the Git-SHA value

```shell
curl http://localhost:5555/v2/ml-ci-app/tags/list
```

Output

```JSON
{"name":"ml-ci-app","tags":["be76f77"]}
```