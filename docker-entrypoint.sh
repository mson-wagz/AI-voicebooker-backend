#!/bin/sh
set -e

echo "Running database migrations..."
/app/.venv/bin/prisma migrate deploy

echo "Starting server..."
exec /app/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
