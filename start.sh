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

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
while ! nc -z redis 6379 2>/dev/null; do
  sleep 1
done
echo "✅ Redis is ready"

# Setup database
echo "🗄️ Setting up database..."
uv run python scripts/setup_db.py

# Start FastAPI backend in background
echo "🔧 Starting FastAPI backend..."
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
FASTAPI_PID=$!

# Give FastAPI time to start
sleep 5

# Start Streamlit frontend
echo "🎨 Starting Streamlit frontend..."
uv run streamlit run src/ui/app.py --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!

# Wait for both processes
wait $FASTAPI_PID $STREAMLIT_PID