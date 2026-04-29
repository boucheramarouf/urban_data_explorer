# ──────────────────────────────────────────────────────────────
# Stage 1 : Base (utilisé par API et Airflow)
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data

WORKDIR /app

# Installer les dépendances système nécessaires pour GeoPandas, pyogrio, et Airflow
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libspatialindex-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY . .

# Créer le répertoire de données
RUN mkdir -p /data

# ──────────────────────────────────────────────────────────────
# Stage 2 : API
# ──────────────────────────────────────────────────────────────
FROM base as api

# Run pipeline
RUN python run_pipeline.py

EXPOSE 8000

CMD [ "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ──────────────────────────────────────────────────────────────
# Stage 3 : Airflow
# ──────────────────────────────────────────────────────────────
FROM base as airflow

# Installer les dépendances Airflow supplémentaires
RUN pip install --no-cache-dir \
    apache-airflow==2.8.0 \
    apache-airflow-providers-postgres==5.11.0 \
    apache-airflow-providers-redis==3.2.0 \
    apache-airflow-providers-celery==3.5.0 \
    psycopg2-binary>=2.9.0 \
    redis>=4.5.0 \
    celery>=5.3.0

ENV AIRFLOW_HOME=/app

CMD [ "airflow", "webserver" ]