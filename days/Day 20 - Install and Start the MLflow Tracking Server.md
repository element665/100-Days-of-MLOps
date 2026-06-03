Prompt

The xFusionCorp Industries ML team is adopting MLflow for experiment tracking. Your task is to bring up a local MLflow tracking server on the ML pipeline workstation so experiments can be logged from the team's training code.

  

MLflow 3.x is pre-installed on the controlplane. Launch the tracking server in the background so that every end-state requirement below holds.

1. The server is listening on port `5000` and is reachable on all interfaces.
    
2. The backend store is a SQLite database at `/root/code/mlflow-backend/mlflow.db`. The database file must exist after the server has started.
    
3. The artifact root is `/root/code/mlflow-artifacts/`.
    
4. Any parent directories the server needs must be in place before it starts—MLflow will abort if the backend directory is missing.
    
5. The **MLflow UI** button at the top of the lab must open a responsive dashboard in the browser. The button routes through the lab proxy, so the server must accept requests from any origin (`--cors-allowed-origins '*'`) and any host header (`--allowed-hosts '*'`) to avoid proxy-related rejections.
    
6. The server process must persist in the background so it survives terminal closure.
    

> Once the server is running, the `Default` experiment can be viewed from the **MLflow UI** button. The experiment is empty—runs will be logged in subsequent labs.

---

Solution

Create required directories

```shell
mkdir -p /root/code/mlflow-backend
mkdir -p /root/code/mlflow-artifacts
```

Start MLflow server

```shell
nohup mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri sqlite:////root/code/mlflow-backend/mlflow.db \
  --artifacts-destination /root/code/mlflow-artifacts \
  --cors-allowed-origins '*' \
  --allowed-hosts '*' \
  > /tmp/mlflow.log 2>&1 &
```

Verify server is running in background

```shell
ps -ef | grep mlflow
```

Output

```shell
root        5580    2838  0 05:07 pts/6    00:00:02 /usr/bin/python3 /usr/local/bin/mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:////root/code/mlflow-backend/mlflow.db --artifacts-destination /root/code/mlflow-artifacts --cors-allowed-origins * --allowed-hosts *
root        5648    5580  0 05:07 pts/6    00:00:00 /usr/bin/python3 -m uvicorn --log-config /usr/local/lib/python3.12/dist-packages/mlflow/server/uvicorn_log_config.yaml --host 0.0.0.0 --port 5000 --workers 4 mlflow.server.fastapi_app:app
root        5649    5580  0 05:07 pts/6    00:00:01 /usr/bin/python3 -m mlflow.server.jobs._job_runner
root        5849    5649  0 05:07 pts/6    00:00:01 /usr/bin/python3 -m huey.bin.huey_consumer mlflow.server.jobs._huey_consumer.huey_instance -w 5 -q
root        5850    5649  0 05:07 pts/6    00:00:02 /usr/bin/python3 -m huey.bin.huey_consumer mlflow.server.jobs._huey_consumer.huey_instance -w 5 -q
root        5852    5649  0 05:07 pts/6    00:00:02 /usr/bin/python3 -m huey.bin.huey_consumer mlflow.server.jobs._huey_consumer.huey_instance -w 10 -q
root        5853    5649  0 05:07 pts/6    00:00:02 /usr/bin/python3 -m huey.bin.huey_consumer mlflow.server.jobs._huey_consumer.huey_instance -w 2 -q
root        5856    5649  0 05:07 pts/6    00:00:01 /usr/bin/python3 -m huey.bin.huey_consumer mlflow.server.jobs._huey_consumer.huey_instance -w 10 -q
root        5857    5649  0 05:07 pts/6    00:00:02 /usr/bin/python3 -m huey.bin.huey_consumer mlflow.server.jobs._periodic_tasks_consumer.huey_instance -w 5 -q
root        6639    2838  0 05:12 pts/6    00:00:00 grep --color=auto mlflow
```

Verify MLflow dashboard is functioning

```shell
Click MLflow UI button
```

Screenshot for Verification

![Screenshot](<../screenshots/Screenshot Day 20.png>)