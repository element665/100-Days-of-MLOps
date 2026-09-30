FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir scikit-learn numpy joblib

COPY train.py /app/train.py
RUN python3 /app/train.py

CMD ["python3", "-c", "import joblib; m = joblib.load('/app/model.pkl'); print('Model loaded:', type(m).__name__)"]