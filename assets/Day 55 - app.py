"""Minimal Flask ML API with a health endpoint for container
liveness probing and a dummy predict endpoint for smoke tests."""
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/predict", methods=["POST"])
def predict():
    payload = request.get_json() or {}
    amount = float(payload.get("amount", 0.0))
    # Minimal rule-based stub — high-value + late-night transactions
    # are flagged as fraud. Keeps the serving surface realistic
    # without pulling in sklearn at runtime.
    hour = int(payload.get("hour", 12))
    is_fraud = int(amount > 500 and (hour >= 22 or hour <= 4))
    return jsonify({"is_fraud": is_fraud}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8085)