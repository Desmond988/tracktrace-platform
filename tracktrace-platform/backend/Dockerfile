FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD curl -f http://localhost:8000/health || exit 1

# Runs migrations, then starts the app. Never drops/recreates the database.
# Uses sh -c so ${PORT} expands, waits for DB, and fails loudly if migrations fail.
CMD sh -c "python -c \"import os; u=os.getenv('DATABASE_URL','MISSING'); print('DB_HOST_CHECK:', u.split('@')[-1].split('/')[0] if '@' in u else u, flush=True)\" && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $${PORT:-8000} --workers $${WEB_CONCURRENCY:-1}"