# TikTok Geo-Regulation AI System

An AI-powered legal compliance analysis system that automatically identifies regulatory requirements and compliance gaps for TikTok features across global jurisdictions.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- At least one API key: Google AI, Anthropic Claude, or OpenAI

### 1. Setup
```bash
git clone <repository> && cd techjam-jamming
cp .env.template .env
# Edit .env and add your API key (any one works)
```

### 2. Run
```bash
docker-compose up -d
```

### 3. Access
- **Frontend**: http://localhost:3000 (Modern React UI)
- **API**: http://localhost:8000 (Backend API)
- **API Docs**: http://localhost:8000/docs (Swagger)

## How It Works

1. **Upload** a requirements document or describe a TikTok feature
2. **AI Analysis** automatically extracts key requirements and identifies regulatory concerns
3. **Legal Search** finds relevant laws across 5 major jurisdictions (US, EU, California, Florida, Brazil)  
4. **Compliance Report** shows gaps, risks, and actionable recommendations

## Key Features

- **Smart Document Processing**: PDF upload with automatic feature extraction
- **Multi-Jurisdiction Analysis**: Covers major global privacy and social media regulations
- **Real-Time Analysis**: Watch the AI reasoning process in real-time
- **Human-in-the-Loop**: Approve or modify AI decisions during analysis
- **Professional Reports**: Detailed compliance analysis with implementation guidance

## Architecture

- **Frontend**: Next.js with professional UI components
- **Backend**: FastAPI with multi-LLM support (Google AI, Claude, GPT)
- **Legal Search**: PostgreSQL with semantic vector search
- **Requirements Search**: ChromaDB for document processing
- **Deployment**: Docker containerization for easy setup

## Example Use Cases

- Analyze new TikTok features for GDPR compliance
- Check live shopping features against minor protection laws
- Evaluate data collection practices across jurisdictions
- Generate compliance reports for product launches

## Development

### Local Development
```bash
# Start infrastructure
docker-compose up -d postgres legal-mcp requirements-mcp

# Run services locally
cd frontend && npm run dev          # Port 3000
uv run python -m src.main          # Port 8000
```

### Testing
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Test feature analysis
curl -X POST http://localhost:8000/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{"name": "Live Shopping", "description": "Real-time shopping with payment processing"}'
```

## Tech Stack

- **Frontend**: Next.js, TypeScript, Tailwind CSS
- **Backend**: Python, FastAPI, PostgreSQL
- **AI**: Google Gemini, Claude, GPT-4 (with fallbacks)
- **Search**: Vector similarity search with pgvector
- **Deployment**: Docker, Docker Compose

## Troubleshooting

**Common Issues:**
- **API Key**: Add any valid API key to `.env` (Google AI has free tier)
- **Services Down**: Run `docker-compose restart` to restart all services
- **Port Conflicts**: Change ports in `docker-compose.yml` if needed

**Health Check:**
```bash
curl http://localhost:8000/api/v1/health    # Backend
curl http://localhost:8010/health           # Legal service
curl http://localhost:8011/health           # Requirements service
```

---

Built for TikTok TechJam 2025 - Automated legal compliance through AI-powered document analysis.