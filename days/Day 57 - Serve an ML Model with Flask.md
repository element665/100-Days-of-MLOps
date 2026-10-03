Prompt

The xFusionCorp Industries ML platform team serves the fraud-detection model over HTTP with a Flask app so downstream services can score transactions synchronously. A draft `app.py` at `/root/code/serving/` loads the pre-trained model and declares `/health` + `/predict`, but the server binds to the wrong port and the `/predict` handler is left unimplemented. Your task is to author the `/predict`handler and bind the server to the exposed port, start the server, and confirm two distinct payloads produce two distinct responses.

  

Flask is installed at startup (it is not part of the lab image by default).

The project layout under `/root/code/serving/`:

- `model.pkl` – Deterministic RandomForest trained at startup on the shared `amount / hour / num_tx_past_day → is_fraud` synthetic set. Correct and must remain intact.
- `train.csv` – The 10-row training source used to fit `model.pkl`.
- `app.py` – Flask app loading `model.pkl` and declaring `GET /health` + `POST /predict`. The `/predict` handler body is left as a `TODO` to author, and the `app.run(...)`bind port needs attention.

The end state must include:

- `curl http://localhost:8085/health` returns `{"status":"ok"}` with HTTP 200.
- `curl -X POST http://localhost:8085/predict -H 'Content-Type: application/json' -d '{"amount":3200,"hour":23,"num_tx_past_day":5}'`returns a JSON body with an `is_fraud` key.
- The same POST with a low-amount daytime payload (e.g. `{"amount":25.5,"hour":10,"num_tx_past_day":1}`) returns a different `is_fraud` value – Confirming the endpoint actually reads the posted body rather than falling back to zeros.

> The lab's port forwarding targets `8085`; the running server must bind there to be reachable.

---

Solution

app.py (Original)

```python
"""Flask fraud-detection prediction API.

Loads the pre-trained RandomForest at `/root/code/serving/model.pkl`
and exposes `/health` + `/predict` over HTTP.
"""
import joblib
import numpy as np
from flask import Flask, jsonify, request

MODEL_PATH = "/root/code/serving/model.pkl"
MODEL = joblib.load(MODEL_PATH)

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/predict", methods=["POST"])
def predict():
    # TODO: author the prediction handler so a POSTed JSON body is
    #       scored by the model:
    #         1. read the JSON body from the request
    #         2. build a feature row [[amount, hour, num_tx_past_day]]
    #            (a numpy array) from the posted values
    #         3. score it with MODEL.predict(...) and cast to int
    #         4. return {"is_fraud": <int>} as JSON with HTTP 200
    return jsonify({"error": "predict not implemented"}), 501


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

***TODO:***
- Read the JSON body
- Build feature row
- Make prediction
- Return JSON response
- app should run on port '8085' not '5000'

Updates to app.py

```python
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    features = np.array([[
        data["amount"],
        data["hour"],
        data["num_tx_past_day"]
    ]])

    prediction = int(MODEL.predict(features)[0])

    return jsonify({"is_fraud": prediction}), 200
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8085)
```

Run updated script

```shell
python3 app.py
```

Output

```shell
* Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8085
 * Running on http://10.244.247.242:8085
Press CTRL+C to quit
```

### Verification

Verify end state in new terminal window

Confirm Flask app is healthy

```shell
curl http://localhost:8085/health
```

Output

```shell
{"status":"ok"}
```

Confirm POST returns 'is_fraud'

```shell
curl -X POST http://localhost:8085/predict -H 'Content-Type: application/json' -d '{"amount":3200,"hour":23,"num_tx_past_day":5}'
```

Output

```shell
{"is_fraud":1}
```

Confirm POST returns different value

```shell
curl -X POST http://localhost:8085/predict -H 'Content-Type: application/json' -d '{"amount":25.5,"hour":10,"num_tx_past_day":1}'
```

Output

```shell
{"is_fraud":0}
```

Flask app Outputs

```shell
127.0.0.1 - - [03/Oct/2026 11:23:42] "GET /health HTTP/1.1" 200 -
127.0.0.1 - - [03/Oct/2026 11:24:26] "POST /predict HTTP/1.1" 200 -
127.0.0.1 - - [03/Oct/2026 11:25:33] "POST /predict HTTP/1.1" 200 -
```

---

app.py (Final)

```python
"""Flask fraud-detection prediction API.

Loads the pre-trained RandomForest at `/root/code/serving/model.pkl`
and exposes `/health` + `/predict` over HTTP.
"""
import joblib
import numpy as np
from flask import Flask, jsonify, request

MODEL_PATH = "/root/code/serving/model.pkl"
MODEL = joblib.load(MODEL_PATH)

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    features = np.array([[
        data["amount"],
        data["hour"],
        data["num_tx_past_day"]
    ]])

    prediction = int(MODEL.predict(features)[0])

    return jsonify({"is_fraud": prediction}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8085)
```
