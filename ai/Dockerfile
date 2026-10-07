FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY train.py .
COPY detector.py .

RUN mkdir -p /app/model

CMD ["python", "detector.py"]