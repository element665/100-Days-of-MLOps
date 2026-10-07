Prompt

The xFusionCorp Industries ML platform team has deployed the fraud-detection model using BentoML. The model is registered in BentoML's local store and is served over HTTP with the command `bentoml serve`, which automatically generates a Swagger UI at the server's root. Within the scaffold located at `/root/code/serving/service.py`, the modern `@bentoml.service` class API is utilized. This script loads the pre-registered `fraud_detector:latest`model from the store and defines the APIs, although the `POST /predict` handler remains unimplemented. Your objective is to implement the `/predict` handler to score a transaction using the loaded model. Additionally, you need to start the server on port `3000`and verify that it returns predictions.

  

The `fraud_detector` model is registered in BentoML's local store. The BentoML server is NOT pre-started — the **BentoML UI** button opens the Swagger surface once the server is running on port `3000`.

The project layout under `/root/code/serving/`:

- `service.py` – BentoML service (`@bentoml.service`class `FraudService`). The model-store load (`bentoml.models.BentoModel` + `bentoml.sklearn.load_model` in `__init__`) and the `last_predictions` API are wired. The `predict` handler body is left as a `TODO` — it returns an error until authored. The handler takes the `amount`/`hour`/`num_tx_past_day` parameters and returns `{"is_fraud": <int>}`.
- `train.csv` – The 10-row source used at startup to train and register the model with `bentoml.sklearn.save_model("fraud_detector", model)`.

The end state must include:

- `bentoml models list` lists `fraud_detector` in the store.
- `curl http://localhost:3000/` returns HTTP `200` – The Swagger UI is reachable once the server is running.
- `POST /predict` with a valid payload returns `{"is_fraud": 0}` or `{"is_fraud": 1}`.
- Two distinct payloads return different `is_fraud` values – The handler scores the posted features.

> Suggested payloads: `{"amount": 3200, "hour": 23, "num_tx_past_day": 5}` (high-value, late-night—expected to flag fraud); `{"amount": 25.5, "hour": 10, "num_tx_past_day": 1}` (low-value, daytime).

---

Solution

service.py (Original)

```python
"""BentoML service exposing the fraud-detection RandomForest.

Loads `fraud_detector:latest` from the BentoML model store (saved at
startup) and serves it with the modern `@bentoml.service` class API:
  - POST /predict           — score one transaction.
  - POST /last_predictions  — audit log of every POST /predict
                              handled since the server booted.

`bentoml serve service:FraudService` starts the HTTP server on port
3000 and auto-generates a Swagger UI at the server's root — the
primary GUI surface for this lab.
"""
from typing import Any, Dict, List

import bentoml
import numpy as np


@bentoml.service(name="fraud_service")
class FraudService:
    # Declare the model dependency from the store; BentoML resolves it
    # and makes it available for loading.
    bento_model = bentoml.models.BentoModel("fraud_detector:latest")

    def __init__(self) -> None:
        self.model = bentoml.sklearn.load_model(self.bento_model)
        self._history: List[Dict[str, Any]] = []

    @bentoml.api
    def predict(
        self, amount: float, hour: int, num_tx_past_day: int
    ) -> Dict[str, Any]:
        # TODO: author the prediction handler:
        #   1. build a feature row [[amount, hour, num_tx_past_day]] (numpy)
        #   2. score it with self.model.predict(...) and cast to int
        #   3. append the inputs + label to self._history (keys: amount,
        #      hour, num_tx_past_day, is_fraud)
        #   4. return {"is_fraud": <int>}
        return {"error": "predict not implemented"}

    @bentoml.api
    def last_predictions(self) -> Dict[str, Any]:
        return {"count": len(self._history), "predictions": self._history}
```

TODO section

```python
        feature = np.array([[amount, hour, num_tx_past_day]])
        prediction = int(self.model.predict(feature)[0])
        
        self._history.append({
            "amount": amount,
            "hour": hour,
            "num_tx_past_day": num_tx_past_day,
            "is_fraud": prediction,
        })
            
        return {"is_fraud": prediction}
```

service.py (Final)

```python
"""BentoML service exposing the fraud-detection RandomForest.

Loads `fraud_detector:latest` from the BentoML model store (saved at
startup) and serves it with the modern `@bentoml.service` class API:
  - POST /predict           — score one transaction.
  - POST /last_predictions  — audit log of every POST /predict
                              handled since the server booted.

`bentoml serve service:FraudService` starts the HTTP server on port
3000 and auto-generates a Swagger UI at the server's root — the
primary GUI surface for this lab.
"""
from typing import Any, Dict, List

import bentoml
import numpy as np


@bentoml.service(name="fraud_service")
class FraudService:
    # Declare the model dependency from the store; BentoML resolves it
    # and makes it available for loading.
    bento_model = bentoml.models.BentoModel("fraud_detector:latest")

    def __init__(self) -> None:
        self.model = bentoml.sklearn.load_model(self.bento_model)
        self._history: List[Dict[str, Any]] = []

    @bentoml.api
    def predict(
        self, amount: float, hour: int, num_tx_past_day: int
    ) -> Dict[str, Any]:
        feature = np.array([[amount, hour, num_tx_past_day]])
        prediction = int(self.model.predict(feature)[0])
        
        self._history.append({
            "amount": amount,
            "hour": hour,
            "num_tx_past_day": num_tx_past_day,
            "is_fraud": prediction,
        })
            
        return {"is_fraud": prediction}
        return {"error": "predict not implemented"}

    @bentoml.api
    def last_predictions(self) -> Dict[str, Any]:
        return {"count": len(self._history), "predictions": self._history}
```

Confirm 'fraud_detector' model in bentoml

```shell
bentoml models list
```

Output

```shell
Tag                              Module           Size      Creation Time       
 fraud_detector:euhlj2gclw6ngzvw  bentoml.sklearn  8.04 KiB  2026-10-07 10:41:13
```

Start the service

```shell
bentoml serve service:FraudService --port 3000
```

Output

```shell
2026-10-07T10:45:30-0400 [INFO] [cli] Starting production HTTP BentoServer from "service:FraudService" listening on http://localhost:3000 (Press CTRL+C to quit)
2026-10-07T10:45:31-0400 [INFO] [entry_service:fraud_service:1] Service fraud_service initialized
```

Confirm service is running

```shell
curl -i http://localhost:3000/
```

Output

```shell
HTTP/1.1 200 OK
date: Wed, 07 Oct 2026 14:46:27 GMT
content-type: text/html; charset=utf-8
accept-ranges: bytes
content-length: 2945
last-modified: Thu, 01 Oct 2026 03:28:20 GMT
etag: "9942ea71be5d5338fbd54969e265cb02"

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>BentoML Prediction Service</title>
    <!-- Google Tag Manager -->
    <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
    new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
    j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
    'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    })(window,document,'script','dataLayer','GTM-WNPGWRM');</script>
    <!-- End Google Tag Manager -->
    <link rel="stylesheet" type="text/css" href="./static_content/swagger-ui.css" />
    <link rel="stylesheet" type="text/css" href="./static_content/index.css" />
    <link rel="icon" type="image/png" href="./static_content/favicon-light-32x32.png" sizes="32x32" media="(prefers-color-scheme: light)" />
    <link rel="icon" type="image/png" href="./static_content/favicon-dark-32x32.png" sizes="32x32" media="(prefers-color-scheme: dark)" />
  </head>
  <body>
    <!-- Google Tag Manager (noscript) -->
    <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-WNPGWRM"
    height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
    <!-- End Google Tag Manager (noscript) -->
    <div id="swagger-ui"></div>
    <script src="./static_content/swagger-ui-bundle.js" charset="UTF-8"> </script>
    <script src="./static_content/swagger-ui-standalone-preset.js" charset="UTF-8"> </script>
    <script src="./static_content/swagger-initializer.js" charset="UTF-8"> </script>
    <div class="version">
        <div class="version-section"><a href="https://github.com/bentoml/BentoML" class="github-corner" aria-label="Powered by BentoML">
            <svg width="80" height="80" viewBox="0 0 250 250" style="fill:#151513; color:#fff; position: absolute; top: 0; border: 0; right: 0;" aria-hidden="true">
            <path d="M0,0 L115,115 L130,115 L142,142 L250,250 L250,0 Z"></path>
            <path d="M128.3,109.0 C113.8,99.7 119.0,89.6 119.0,89.6 C122.0,82.7 120.5,78.6 120.5,78.6 C119.2,72.0 123.4,76.3 123.4,76.3 C127.3,80.9 125.5,87.3 125.5,87.3 C122.9,97.6 130.6,101.9 134.4,103.2" fill="currentColor" style="transform-origin: 130px 106px;" class="octo-arm"></path>
            <path d="M115.0,115.0 C114.9,115.1 118.7,116.5 119.8,115.4 L133.7,101.6 C136.9,99.2 139.9,98.4 142.2,98.6 C133.8,88.0 127.5,74.4 143.8,58.0 C148.5,53.4 154.0,51.2 159.7,51.0 C160.3,49.4 163.2,43.6 171.4,40.1 C171.4,40.1 176.1,42.5 178.8,56.2 C183.1,58.6 187.2,61.8 190.9,65.4 C194.5,69.0 197.7,73.2 200.1,77.6 C213.8,80.2 216.3,84.9 216.3,84.9 C212.7,93.1 206.9,96.0 205.4,96.6 C205.1,102.4 203.0,107.8 198.3,112.5 C181.9,128.9 168.3,122.5 157.7,114.1 C157.9,116.9 156.7,120.9 152.7,124.9 L141.0,136.5 C139.8,137.7 141.6,141.9 141.8,141.8 Z" fill="currentColor" class="octo-body"></path>
            </svg></a>
        </div>
    </div>
  </body>
</html>
```

### Verification

Swagger UI is reachable

![screenshot](<../screenshots/Screenshot Day 60 Swagger UI.png>)

Swagger UI POST /predict payload 1 (high-value, late-night = expected fraud flag)

![screenshot](<../screenshots/Screenshot Day 60 Swagger UI payload 1.png>)

Swagger UI POST /predict payload 1 (low-value, daytime)

![screenshot](<../screenshots/Screenshot Day 60 Swagger UI payload 2.png>)