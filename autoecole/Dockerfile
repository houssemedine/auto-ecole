# Dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# dépendances système minimales (facultatif pour SQLite)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installer les deps Python
COPY requirements.txt .
RUN pip install --upgrade pip wheel && pip install -r requirements.txt

# Copier le code (pour la prod, on montera un volume en dev)
COPY . .

EXPOSE 8000

# Commande par défaut (peut être surchargée par docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
