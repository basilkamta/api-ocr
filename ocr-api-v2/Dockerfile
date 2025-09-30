FROM python:3.10-slim

RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installation des dépendances Python



# Copie de l'application
COPY app/ ./app/
COPY .env* ./
RUN --mount=type=cache,target=/root/.cache/pip \
pip install -r ./app/requirements/base.txt

RUN --mount=type=cache,target=/root/.cache/pip \
pip install -r ./app/requirements/common.txt

# Création des répertoires
RUN mkdir -p /tmp/uploads

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]