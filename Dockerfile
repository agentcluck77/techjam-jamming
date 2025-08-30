# Multi-stage Dockerfile for Geo-Regulation AI System  
# Phase 1D: Basic deployment setup with uv

FROM python:3.11-slim as base

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    netcat-traditional \
    libpq-dev \
    && pip install --no-cache-dir uv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files for dependency installation
COPY pyproject.toml .

# Install Python dependencies with uv using pyproject.toml dependencies
RUN uv pip install --system --no-cache \
    "fastapi>=0.100.0" \
    "uvicorn[standard]>=0.20.0" \
    "pydantic>=2.7.4" \
    "python-multipart>=0.0.6" \
    "langgraph>=0.2.0" \
    "langchain>=0.3.0" \
    "langchain-anthropic>=0.2.0" \
    "langchain-openai>=0.2.0" \
    "langchain-google-genai>=2.0.0" \
    "google-generativeai>=0.4.1" \
    "sqlalchemy>=2.0.0" \
    "alembic>=1.12.0" \
    "asyncpg>=0.29.0" \
    "psycopg2-binary>=2.9.0" \
    "redis>=5.0.0" \
    "aioredis>=2.0.0" \
    "aiohttp>=3.9.0" \
    "httpx>=0.25.0" \
    "streamlit>=1.28.0" \
    "plotly>=5.17.0" \
    "pandas>=2.1.0" \
    "python-dotenv>=1.0.0" \
    "pydantic-settings>=2.1.0" \
    "typing-extensions>=4.11.0" \
    "cryptography>=42.0.0" \
    "python-jose[cryptography]>=3.3.0" \
    "prometheus-client>=0.19.0"

# Copy application code
COPY . .

# Create non-root user for security (Debian uses useradd)
RUN useradd -r -s /bin/bash -m -d /home/app app && \
    chown -R app:app /app && \
    chmod +x scripts/setup_db.py && \
    chmod +x start.sh

USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || nc -z localhost 8000 || exit 1

# Expose ports
EXPOSE 8000 8501

# Start script
CMD ["./start.sh"]