Prompt

The xFusionCorp Industries ML platform team deploys Flask-based inference APIs as Docker images, incorporating Docker-native `HEALTHCHECK` instructions. This allows operators to easily verify the serving status of the process by running `docker inspect --format='{{.State.Health.Status}}'`. However, the draft `Dockerfile` located at `/root/code/ml-health/`currently does not meet these standards; executing `docker inspect --format='{{.State.Health.Status}}' ml-health-api`returns `unhealthy`, and `docker inspect --format '{{.Config.ExposedPorts}}' ml-health:v1` shows no exposed ports. Your task is to rectify the `HEALTHCHECK`target and include the missing `EXPOSE` declaration.

  

1. The Docker daemon is already running. `docker version` can be run in a VS Code terminal to confirm. With the current image built and run as `ml-health-api`, `docker inspect --format='{{.State.Health.Status}}' ml-health-api`reports `unhealthy` and `docker inspect --format '{{.Config.ExposedPorts}}' ml-health:v1` shows no exposed ports.
    
2. The project layout under `/root/code/ml-health/`:
    
    - `app.py` – Flask API serving `GET /health`(returns `{"status": "ok"}` / 200) and `POST /predict` (returns a rule-based fraud flag) on port `8085`. Correct.
    - `Dockerfile` – `python:3.11-slim`, installs flask, copies `app.py`, carries a `HEALTHCHECK` + `CMD`. The corrected image is built as `ml-health:v1`and run as a container named `ml-health-api`with host port `8085` published.
3. The end state must include:
    
    - `docker inspect --format '{{.Config.ExposedPorts}}' ml-health:v1`reports `map[8085/tcp:{}]`.
    - After `docker run`, `docker inspect --format='{{.State.Health.Status}}' ml-health-api` reads `healthy` within ~15 seconds.
    - `curl http://localhost:8085/health` returns `{"status": "ok"}` with HTTP 200.

> `HEALTHCHECK` reruns its `CMD` every `--interval` seconds and flips the state to `unhealthy` after `--retries`consecutive failures. `EXPOSE` does not change networking (that is done by `-p`)—it writes image metadata so `docker inspect` and downstream orchestrators know which port the image intends to serve on.

---

Solution

[app.py](<../assets/Day 55 - app.py>) (Provided)

Dockerfile (Original)

```yaml
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask

COPY app.py /app/app.py

HEALTHCHECK --interval=5s --timeout=3s --start-period=3s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8085/healthz')" || exit 1

CMD ["python3", "/app/app.py"]
```

**Errors**
- HEALTHCHECK references incorrect url (/healthz -> /health)
- EXPOSE declaration for port 8085 is missing

Dockerfile (Updated)

```yaml
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask

COPY app.py /app/app.py

EXPOSE 8085

HEALTHCHECK --interval=5s --timeout=3s --start-period=3s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8085/health')" || exit 1

CMD ["python3", "/app/app.py"]
```

Build docker image

```shell
docker build -t ml-health:v1 .
```

Output

```shell
[+] Building 7.9s (9/9) FINISHED                                                           docker:default
 => [internal] load build definition from Dockerfile                                                 0.0s
 => => transferring dockerfile: 361B                                                                 0.0s
 => [internal] load metadata for docker.io/library/python:3.11-slim                                  1.2s
 => [internal] load .dockerignore                                                                    0.0s
 => => transferring context: 2B                                                                      0.0s
 => [1/4] FROM docker.io/library/python:3.11-slim@sha256:e41613d42d4891e4930f79523f93f81bbc7632584e  2.1s
 => => resolve docker.io/library/python:3.11-slim@sha256:e41613d42d4891e4930f79523f93f81bbc7632584e  0.0s
 => => sha256:0526d5e29bf341cb1941d46a6d4ab64fcde4fca3dc3adccfb4dbf5728b88b61e 249B / 249B           0.1s
 => => sha256:58abdd9670ca8c69d03432ce188995dee67f0979357caf83866fe1ef2ec37138 14.45MB / 14.45MB     0.4s
 => => sha256:41e7217c2e506d048f89ca0c5cfef848c05ef990900627c19f99938c4aae57f8 1.29MB / 1.29MB       0.4s
 => => sha256:6b37362b3da78869050b894b799ad4df04f1f3b52774087db0d81151570244c8 29.83MB / 29.83MB     0.6s
 => => extracting sha256:6b37362b3da78869050b894b799ad4df04f1f3b52774087db0d81151570244c8            0.6s
 => => extracting sha256:41e7217c2e506d048f89ca0c5cfef848c05ef990900627c19f99938c4aae57f8            0.2s
 => => extracting sha256:58abdd9670ca8c69d03432ce188995dee67f0979357caf83866fe1ef2ec37138            0.5s
 => => extracting sha256:0526d5e29bf341cb1941d46a6d4ab64fcde4fca3dc3adccfb4dbf5728b88b61e            0.0s
 => [internal] load build context                                                                    0.0s
 => => transferring context: 849B                                                                    0.0s
 => [2/4] WORKDIR /app                                                                               0.0s
 => [3/4] RUN pip install --no-cache-dir flask                                                       2.2s
 => [4/4] COPY app.py /app/app.py                                                                    0.0s 
 => exporting to image                                                                               2.2s 
 => => exporting layers                                                                              0.4s 
 => => exporting manifest sha256:74a81d7f76954e3a9c0c78e58e0768370cf8f91a3ab2b3130378465350f3a82d    0.0s 
 => => exporting config sha256:1ae46324d64886539cf851532e8cf9783c058d6b27b68a67acc2888c910577c7      0.0s 
 => => exporting attestation manifest sha256:8947c9434970935ad6890543509fef6c05393c617876108b1e0e8c  0.0s 
 => => exporting manifest list sha256:7516c6d11cf9f5995d43be4154c6000de66e9dd2e5410bd0863264d0b867d  0.0s
 => => naming to docker.io/library/ml-health:v1                                                      0.0s
 => => unpacking to docker.io/library/ml-health:v1                                                   1.7s
```

Check the exposed port

```shell
docker inspect --format '{{.Config.ExposedPorts}}' ml-health:v1
```

Output

```shell
map[8085/tcp:{}]
```

Run the container

```shell
docker run -d --name ml-health-api -p 8085:8085 ml-health:v1
```

Output

```shell
b4edeb22f72bf6a0d71fc00627a8b126d51a3cc74031ab1063da460ce66a4688
```

Check health of container

```shell
docker inspect --format='{{.State.Health.Status}}' ml-health-api
```

Output

```shell
healthy
```

Confirm API (included -i to receive HTTP response header)

```shell
curl -i http://localhost:8085/health
```

Output

```shell
HTTP/1.1 200 OK
{"status":"ok"}
```