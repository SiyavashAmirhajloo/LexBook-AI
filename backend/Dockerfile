# syntax=docker/dockerfile:1
FROM python:3.13-slim
WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy only backend contents here (context already at repo root)
COPY backend/pyproject.toml ./
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini
COPY backend/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

RUN pip install --upgrade pip && pip install . && pip install asyncpg

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]