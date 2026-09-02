FROM python:3.12-slim

# Réglages Python en conteneur
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dépendances système (psycopg a besoin de libpq)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python (couche mise en cache tant que requirements ne change pas)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Code applicatif
COPY . .

EXPOSE 8000

# En dev, la commande est surchargée par docker-compose (runserver).
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
