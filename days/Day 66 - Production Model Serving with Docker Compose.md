Prompt

The xFusionCorp Industries ML platform team operates a fraud-detection model in production, supported by a comprehensive observability stack. This stack includes a Flask API with Prometheus instrumentation, Redis for per-IP rate limiting, nginx as the public reverse proxy, Prometheus for metrics collection, and Grafana for dashboarding. Currently, the pre-staged stack located at `/root/code/serving/production/` does not reach a clean end state. Your objective is to correct the wiring, bring the stack online, and create a Grafana dashboard that visualizes the model API's request rate.

  

The Docker daemon is already running. Every image the compose stack references is being pre-pulled in the background at startup, so `docker compose up -d` returns in seconds. The Grafana admin password is `grafana2026`.

Bring the stack up and observe where it falls short: `cd /root/code/serving/production && docker compose up -d && docker compose ps` shows the container states, and `docker compose logs` surfaces the wiring faults behind any container that does not settle.

The project layout under `/root/code/serving/production/`:

- `app/app.py` – Flask API with `/health`, `/predict`(Redis-backed per-IP rate limit), and `/metrics` (once the exporter is wired). Needs attention.
- `app/Dockerfile` – `python:3.11-slim` + flask + redis + prometheus-flask-exporter + joblib + sklearn. Correct.
- `model.pkl` – Trained at startup on the shared synthetic fraud dataset.
- `docker-compose.yml` – Defines `model-api`, `redis`, `nginx` (publishes 8085), `prometheus` (publishes 9090), `grafana` (publishes 3000, admin password `grafana2026`), and a `traffic-generator` sidecar (continuously POSTs to `/predict` so Grafana has live request-rate data to plot). Correct.
- `prometheus.yml` – Scrape config for the `model-api`job. Needs attention.
- `nginx.conf` – Reverse-proxy config with an `upstream model_backend` block + `location /` forwarding every request. Needs attention.
- `grafana/provisioning/datasources/prometheus.yml` – Pre-provisions a `Prometheus` datasource pointing at `http://prometheus:9090`, so the Grafana task focuses on dashboard creation.

The Grafana UI button opens the console once the stack is up; the dashboard should carry at least one panel that queries the Prometheus datasource.

The end state must include:

- All six containers (`model-api`, `prod-redis`, `prod-nginx`, `prod-prometheus`, `prod-grafana`, `prod-traffic`) are reported running by `docker inspect`.
- `curl -s http://localhost:5000/metrics` returns a Prometheus exposition-format body (HTTP 200).
- `curl -X POST http://localhost:8085/predict -d '{...}'` through nginx returns a JSON `is_fraud`response.
- `curl http://localhost:9090/api/v1/targets` reports the `model-api` job's health as `up`.
- `curl -u admin:grafana2026 http://localhost:3000/api/datasources` lists a `Prometheus` datasource.
- `curl -u admin:grafana2026 http://localhost:3000/api/search?type=dash-db`returns at least one user-created dashboard, and that dashboard's JSON carries at least one panel.

> The Flask app listens on container port `5000`. The prometheus-flask-exporter publishes standard HTTP request counters that a Grafana panel can query to plot the API's request rate.

---

Solution

docker-compose.yml

```yaml
services:
  model-api:
    build: ./app
    container_name: model-api
    ports:
      - "5000:5000"
    volumes:
      - ./model.pkl:/app/model.pkl:ro
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 5s

  redis:
    image: redis:7-alpine
    container_name: prod-redis
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: prod-nginx
    ports:
      - "8085:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - model-api
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:v3.13.0
    container_name: prod-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    depends_on:
      - model-api
    restart: unless-stopped

  grafana:
    image: grafana/grafana:13.1.0
    container_name: prod-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=grafana2026
      - GF_AUTH_ANONYMOUS_ENABLED=false
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - prometheus
    restart: unless-stopped

  traffic-generator:
    image: curlimages/curl:8.10.1
    container_name: prod-traffic
    depends_on:
      - nginx
    entrypoint:
      - /bin/sh
      - -c
      - |
        sleep 5
        while true; do
          curl -s -X POST -H 'Content-Type: application/json' \
            -d '{"amount":500,"hour":12,"num_tx_past_day":2}' \
            http://nginx:80/predict > /dev/null
          sleep 0.5
        done
    restart: unless-stopped
```

nginx.conf

```shell
events {}

http {
    upstream model_backend {
        server model-api:8000;
    }

    server {
        listen 80;

        location / {
            proxy_pass http://model_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

prometheus.yml

```yaml
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: model-api
    static_configs:
      - targets:
          - model-api:8000
```

app.py

```python
"""Production fraud-detection serving API.

Flask app wired with:
  - GET  /health           — liveness check.
  - POST /predict          — score one transaction; Redis-backed
                             per-IP rate limit (100 req / min).
  - GET  /metrics          — Prometheus scrape endpoint, exposed
                             by `prometheus_flask_exporter`.

The observability stack scrapes `/metrics` every 5 seconds; the
container listens on port 5000 inside the Docker network, and
nginx fronts the public 8085 surface.
"""
import joblib
import numpy as np
import redis
from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics

MODEL = joblib.load("/app/model.pkl")
REDIS = redis.Redis(host="redis", port=6379, decode_responses=True)

RATE_LIMIT = 100
RATE_WINDOW_SECONDS = 60

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/predict", methods=["POST"])
def predict():
    ip = request.remote_addr or "unknown"
    key = f"ratelimit:{ip}"
    try:
        count = REDIS.incr(key)
        if count == 1:
            REDIS.expire(key, RATE_WINDOW_SECONDS)
    except redis.RedisError:
        count = 0

    if count > RATE_LIMIT:
        return jsonify({"error": "rate limit exceeded"}), 429

    payload = request.get_json() or {}
    features = np.array([[
        float(payload.get("amount", 0.0)),
        int(payload.get("hour", 0)),
        int(payload.get("num_tx_past_day", 0)),
    ]])
    return jsonify({"is_fraud": int(MODEL.predict(features)[0])}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### Corrections

nginx.conf
	- referencing incorrect model-api port (8000 -> 5000)

prometheus.yml
	- referencing incorrect model-api port (8000 -> 5000)

app.py
	- PrometheusMetrics is imported but not attached to the app.
	- Rate limit is reached since traffic is routed through nginx container IP
	- JSON parsing with fail without 'Content-Type' provide with curl. Setting 'force=True, silent=True' parses the body regardless.

app.py (Updated)

```python
"""Production fraud-detection serving API.

Flask app wired with:
  - GET  /health           — liveness check.
  - POST /predict          — score one transaction; Redis-backed
                             per-IP rate limit (100 req / min).
  - GET  /metrics          — Prometheus scrape endpoint, exposed
                             by `prometheus_flask_exporter`.

The observability stack scrapes `/metrics` every 5 seconds; the
container listens on port 5000 inside the Docker network, and
nginx fronts the public 8085 surface.
"""
import joblib
import numpy as np
import redis
from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics

MODEL = joblib.load("/app/model.pkl")
REDIS = redis.Redis(host="redis", port=6379, decode_responses=True)

RATE_LIMIT = 100
RATE_WINDOW_SECONDS = 60

app = Flask(__name__)
metrics = PrometheusMetrics(app)


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/predict", methods=["POST"])
def predict():
    ip = request.headers.get("X-Real-IP") or request.remote_addr or "unknown"
    key = f"ratelimit:{ip}"
    try:
        count = REDIS.incr(key)
        if count == 1:
            REDIS.expire(key, RATE_WINDOW_SECONDS)
    except redis.RedisError:
        count = 0

    if count > RATE_LIMIT:
        return jsonify({"error": "rate limit exceeded"}), 429

    payload = request.get_json(force=True, silent=True) or {}
    features = np.array([[
        float(payload.get("amount", 0.0)),
        int(payload.get("hour", 0)),
        int(payload.get("num_tx_past_day", 0)),
    ]])
    return jsonify({"is_fraud": int(MODEL.predict(features)[0])}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

Navigate to working directory and start Docker Compose stack

```shell
cd /root/code/serving/production && docker compose up -d && docker compose ps
```

Output

```shell
[+] up 24/26
 ✔ Image curlimages/curl:8.10.1                                 Pulled                                1.8s
 ✔ Image prom/prometheus:v3.13.0                                Pulled                                3.6s
 ⠴ Image grafana/grafana:13.1.0 [⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿] 365.7MB / 374.1MB Pulling                              12.6s
[+] Building 21.0s (11/11) FINISHED                                                                       
 => [internal] load local bake definitions                                                           0.0s
 => => reading from stdin 536B                                                                       0.0s
 => [internal] load build definition from Dockerfile                                                 0.0s
 => => transferring dockerfile: 245B                                                                 0.0s
 => [internal] load metadata for docker.io/library/python:3.11-slim                                  0.0s
 => [internal] load .dockerignore                                                                    0.0s
 => => transferring context: 2B                                                                      0.0s
 => [1/4] FROM docker.io/library/python:3.11-slim@sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d  1.6s
 => => resolve docker.io/library/python:3.11-slim@sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d  0.0s
 => => extracting sha256:f2be67225471500c788ce88c597eb5ea8336e912ad1ca4815650e0281afe2034            0.6s
 => => extracting sha256:90d47cf54851a8d83f33db71f0025a8ba367c12fb24817259dd9736098cb305b            0.2s
 => => extracting sha256:6d9af71a343efe2a00fdfc9507db3bdf3530bf3f8cf2975eb1be235a7eb70128            0.6s
 => => extracting sha256:b0aec4a98ced1e92f1d50c37aa89c78d60e3dc6a52d61f8134afda24b185ad06            0.0s
 => [internal] load build context                                                                    0.0s
 => => transferring context: 1.79kB                                                                  0.0s
 => [2/4] WORKDIR /app                                                                               0.1s
 => [3/4] RUN pip install --no-cache-dir     flask redis prometheus-flask-exporter joblib numpy sci  9.4s
 => [4/4] COPY app.py /app/app.py                                                                    0.1s 
 => exporting to image                                                                               9.6s 
 => => exporting layers                                                                              6.4s 
 => => exporting manifest sha256:8f4a387e9cf9eeec2206bbc418209d7890d7bf91bdcf8cc787ad5bccba8dccf2    0.0s 
 => => exporting config sha256:d273614a669e85865ad05cb8d4ec5674fb626249b53385e8e62a65354ea929bd      0.0s 
 => => exporting attestation manifest sha256:4ff54547e74f8842b81ce99301a3b70aa5bb68a85d77b4bf2f24e3  0.0s 
[+] up 34/34ting manifest list sha256:fe68f4f493f6ae0c53086f31fd1d6f3907febd9bceddc21f998e981541e56  0.0s
 ✔ Image curlimages/curl:8.10.1  Pulled                                                               1.8s
 ✔ Image prom/prometheus:v3.13.0 Pulled                                                               3.6s
 ✔ Image grafana/grafana:13.1.0  Pulled                                                              12.6s
 ✔ Image production-model-api    Built                                                               21.1s
 ✔ Network production_default    Created                                                              0.1s
 ✔ Container prod-redis          Started                                                              0.7s
 ✔ Container model-api           Started                                                              0.9s
 ✔ Container prod-prometheus     Started                                                              1.3s
 ✔ Container prod-nginx          Started                                                              1.7s
 ✔ Container prod-grafana        Started                                                              2.0s
 ✔ Container prod-traffic        Started                                                              2.3s
NAME              IMAGE                     COMMAND                  SERVICE             CREATED         STATUS                           PORTS
model-api         production-model-api      "python3 /app/app.py"    model-api           3 seconds ago   Up 1 second (health: starting)   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp
prod-grafana      grafana/grafana:13.1.0    "/run.sh"                grafana             2 seconds ago   Up Less than a second            0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
prod-nginx        nginx:alpine              "/docker-entrypoint.…"   nginx               2 seconds ago   Up 1 second                      0.0.0.0:8085->80/tcp, [::]:8085->80/tcp
prod-prometheus   prom/prometheus:v3.13.0   "/bin/prometheus --c…"   prometheus          2 seconds ago   Up 1 second                      0.0.0.0:9090->9090/tcp, [::]:9090->9090/tcp
prod-redis        redis:7-alpine            "docker-entrypoint.s…"   redis               3 seconds ago   Up 2 seconds                     6379/tcp
prod-traffic      curlimages/curl:8.10.1    "/bin/sh -c 'sleep 5…"   traffic-generator   2 seconds ago   Up Less than a second 
```

Check model-api logs

```shell
docker compose logs model-api --tail 20
```

Output

```shell
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:09] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:10] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:10] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.4 - - [22/Oct/2026 19:25:10] "GET /metrics HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:11] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:11] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:12] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:12] "POST /predict HTTP/1.1" 200 -
model-api  | 127.0.0.1 - - [22/Oct/2026 19:25:12] "GET /health HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:13] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:13] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:14] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:14] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:15] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.4 - - [22/Oct/2026 19:25:15] "GET /metrics HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:15] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:16] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:16] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:17] "POST /predict HTTP/1.1" 200 -
model-api  | 172.18.0.5 - - [22/Oct/2026 19:25:17] "POST /predict HTTP/1.1" 200 -
```

Check /metrics api

```shell
curl -s http://localhost:5000/metrics | tail
```

Output

```shell
flask_http_request_total{method="GET",status="200"} 21.0
flask_http_request_total{method="POST",status="200"} 338.0
flask_http_request_total{method="POST",status="429"} 54.0
# HELP flask_http_request_created Total number of HTTP requests
# TYPE flask_http_request_created gauge
flask_http_request_created{method="GET",status="200"} 1.792697072634444e+09
flask_http_request_created{method="POST",status="200"} 1.7926970744187264e+09
flask_http_request_created{method="POST",status="429"} 1.7926971254265597e+09
# HELP flask_http_request_exceptions_total Total number of HTTP requests which resulted in an exception
# TYPE flask_http_request_exceptions_total counter
```

Check /predict api

```shell
curl -X POST http://localhost:8085/predict -d '{"amount":500,"hour":12,"num_tx_past_day":2}'
```

Output 

```shell
{"is_fraud":0}
```

Check model-api reports health as up

```shell
curl http://localhost:9090/api/v1/targets | grep -o '"health":"[a-z]*"'
```

Output

```shell
"health":"up"
```

Check Grafana lists Prometheus as datasource

```shell
curl -u admin:grafana2026 http://localhost:3000/api/datasources
```

Output

```shell
[{"id":1,"uid":"PBFA97CFB590B2093","orgId":1,"name":"Prometheus","type":"prometheus","typeName":"Prometheus","typeLogoUrl":"public/plugins/prometheus/img/prometheus_logo.svg","access":"proxy","url":"http://prometheus:9090","user":"","database":"","basicAuth":false,"isDefault":true,"jsonData":{},"readOnly":false}]
```

Confirm at least one user-created dashboard exists with at least one panel

```shell
curl -u admin:grafana2026 http://localhost:3000/api/search?type=dash-db
```

Output

```shell
[{"id":1166738676391936,"uid":"adbnkfc","orgId":1,"title":"Model API Request Rate","uri":"db/model-api-request-rate","url":"/d/adbnkfc/model-api-request-rate","slug":"","type":"dash-db","tags":[],"isStarred":false,"sortMeta":0,"isDeleted":false}]
```

---

Screenshots

Prometheus UI shows health target

![screenshot](<../screenshots/Screenshot Day 66 Prometheus UI.png>)

Grafana UI shows user-created dashboard with at least one panel

![screenshot](<../screenshots/Screenshot Day 66 Grafana UI.png>)