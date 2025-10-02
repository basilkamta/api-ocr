FROM python:3.10-slim

# Installation des dépendances système
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libgl1 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie des requirements
COPY app/requirements/ ./app/requirements/

# Installation des dépendances Python de base
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r ./app/requirements/base.txt

# Installation des dépendances communes (images, PDF)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r ./app/requirements/common.txt

# Installation PaddleOCR
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r ./app/requirements/paddle.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r ./app/requirements/kraken.txt

# Copie de l'application
COPY app/ ./app/
COPY .env* ./

# Création des répertoires
RUN mkdir -p /tmp/uploads /app/logs /app/models

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]