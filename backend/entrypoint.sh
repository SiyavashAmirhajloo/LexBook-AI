#!/usr/bin/env bash
set -euo pipefail

echo "Running database migrations..."
# `python -m` so the venv-resolved interpreter runs the right module
# regardless of which user (root or app) is invoking the script.
python -m alembic upgrade head

echo "Starting application..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers