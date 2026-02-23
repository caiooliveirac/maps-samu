FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for PostGIS/psycopg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Seed + migrate on startup, then serve
CMD ["sh", "-c", "python -m app.seed.run && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${BACKEND_WORKERS:-2} --log-level ${LOG_LEVEL:-info}"]

EXPOSE 8000
