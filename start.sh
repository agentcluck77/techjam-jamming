#!/bin/sh
# Start script for Geo-Regulation AI System - Phase 1D
set -e

echo "🚀 Starting TikTok Geo-Regulation AI System..."

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! nc -z postgres 5432 2>/dev/null; do
  sleep 1
done
echo "✅ PostgreSQL is ready"

# Redis not required for current deployment

# Setup database
echo "🗄️ Setting up database..."
uv run python scripts/setup_db.py

# Start FastAPI backend
echo "🔧 Starting FastAPI backend..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000