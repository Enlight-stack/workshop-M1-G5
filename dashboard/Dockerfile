# ==========================================
# BUILD REACT
# ==========================================

FROM node:22-alpine AS frontend

WORKDIR /frontend

COPY package.json .

RUN npm install

COPY index.html .
COPY vite.config.js .
COPY src ./src

RUN npm run build


# ==========================================
# SERVEUR DASHBOARD
# ==========================================

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    -r requirements.txt

COPY app.py .

COPY --from=frontend \
    /frontend/dist \
    ./dist

RUN useradd -m appuser

USER appuser

EXPOSE 3000

CMD ["gunicorn", "-b", "0.0.0.0:3000", "app:app"]