FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data

WORKDIR /app

# Installer les dépendances système nécessaires pour GeoPandas et pyogrio
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY . .

# Run pipeline
RUN python run_pipeline.py

# Créer le répertoire de données
RUN mkdir -p /data

EXPOSE 8000

CMD [ "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]