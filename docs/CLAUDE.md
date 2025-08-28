# CLAUDE.md

This file provides guidance to Claude Code when working in this TikTok Geo-Regulation AI System repository.

## Project Overview

**TikTok Geo-Regulation AI System** - An automated compliance analysis system for TikTok features across global jurisdictions using multi-agent LLM architecture. Built for TikTok TechJam 2025 competition (72-hour hackathon).

### Core Objective
Transform regulatory detection from manual guesswork into an automated, traceable, and auditable process that identifies geo-specific compliance requirements for TikTok features.

## Architecture Components

### Multi-Agent System
- **LangGraph Orchestrator**: Central workflow management with real-time visualization
- **JSON Refactorer Agent**: TikTok jargon expansion and context enrichment
- **Lawyer Agent**: Legal analysis coordination and decision synthesis
- **Jurisdiction MCPs**: 5 specialized compliance agents (Utah, EU, California, Florida, Brazil)

### Technology Stack
- **Backend**: Python 3.11, FastAPI, LangGraph, LangChain
- **LLMs**: Claude Sonnet 4 (primary), GPT-4 (fallback), Google Gemini (optional)
- **Database**: PostgreSQL (persistent), Redis (cache)
- **Frontend**: Streamlit with custom components
- **Deployment**: Docker, docker-compose
- **Monitoring**: Custom metrics, health checks

### Key Services
- **FastAPI Backend**: REST API with health checks (`localhost:8000`)
- **Streamlit Frontend**: Demo interface (`localhost:8501`)
- **PostgreSQL**: Analysis storage and audit trails
- **Redis**: Caching layer for performance optimization

## Team Structure & Development Phases

### Phase 1: Backbone Implementation (Complete ✅)
**Lead**: Aloysius (Hours 0-8)
- Complete end-to-end workflow with mock MCPs
- Basic UI and API endpoints functional
- Database schema and Docker deployment ready

### Phase 2A: Performance & Scale Enhancement
**Team Member 1** (Hours 8-24)
- Replace mock MCPs with real HTTP client integration
- Implement Redis caching layer
- Add parallel MCP execution optimization
- Performance monitoring and metrics collection

### Phase 2B: User Experience & Polish  
**Team Member 2** (Hours 8-24)
- CSV batch processing with progress tracking
- Real-time workflow visualization
- Enhanced UI with interactive charts
- Metrics dashboard implementation

## Directory Structure

```
src/
├── core/
│   ├── workflow.py              # LangGraph orchestration
│   └── agents/
│       ├── json_refactorer.py   # Terminology expansion
│       ├── lawyer_agent.py      # Decision synthesis
│       └── mock_mcps.py         # Mock jurisdiction responses
├── services/                    # Team Member 1 - create these
│   ├── mcp_client.py           # Real HTTP client for MCPs
│   ├── cache_manager.py        # Redis caching
│   ├── llm_router.py           # Enhanced LLM service
│   └── metrics.py              # Performance monitoring
├── ui/
│   ├── app.py                  # Main Streamlit interface
│   └── components/             # Team Member 2 - create these
│       ├── batch_processor.py  # CSV batch processing
│       ├── workflow_viz.py     # Real-time visualization
│       └── enhanced_results.py # Interactive results
└── api/
    └── endpoints/              # FastAPI route handlers
```

## Key Integration Points

### MCP Integration (Team Member 1)
MCPs are implemented as separate HTTP services with standardized endpoints:

```python
# Expected MCP endpoint format
POST /api/v1/analyze
{
    "feature_context": {
        "expanded_description": "string",
        "geographic_implications": ["string"],
        "feature_category": "string"
    }
}

# Service discovery configuration
MCP_SERVICES = {
    'utah': {'url': 'http://utah-mcp:8000', 'timeout': 30},
    'eu': {'url': 'http://eu-mcp:8000', 'timeout': 30},
    # ... other jurisdictions
}
```

### Feature Flags
```bash
# .env configuration
ENABLE_CACHING=true
ENABLE_REAL_MCPS=true
ENABLE_BATCH_PROCESSING=true
ENABLE_WORKFLOW_VIZ=true
```

## Development Guidelines

### Code Standards
- **Python 3.11+** with type hints
- **Async/await** patterns for performance
- **Pydantic models** for data validation
- **Structured logging** for debugging
- **Error handling** with fallback strategies

### Testing Strategy
- **Unit tests**: Individual agent functionality
- **Integration tests**: End-to-end workflow
- **Performance tests**: Concurrent analysis handling
- **Competition dataset validation**: >85% accuracy target

### TODO Search Patterns
- `# TODO: Team Member 1` - Performance and MCP integration tasks
- `# TODO: Team Member 2` - UI and batch processing tasks
- `# REPLACE:` - Mock implementations to be replaced

## Competition Specifications

### Acceptance Criteria
- **Speed**: Feature analysis <5 seconds, batch (50 features) <5 minutes
- **Accuracy**: >90% precision on competition test dataset
- **Scale**: Handle 100+ features in batch processing
- **Demo Quality**: Visual workflow execution, performance metrics dashboard

### Jurisdiction Coverage
1. **Utah Social Media Regulation Act**: Age verification, curfew restrictions, parental controls
2. **EU Digital Services Act**: Content moderation, transparency reporting, risk assessment
3. **California COPPA**: Child protection, data collection limitations
4. **Florida Online Protections for Minors**: Age-appropriate design, content filtering
5. **Brazil Data Localization**: Data storage requirements, cross-border transfers

### Output Format
```csv
feature_name,compliance_required,risk_level,applicable_jurisdictions,requirements,implementation_steps,confidence_score,reasoning
```

## Quick Commands

### Development Setup
```bash
# Copy environment template
cp .env.template .env
# Edit .env with API keys

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Start services
docker-compose up -d postgres redis
uv run python scripts/setup_db.py
uv run uvicorn src.main:app --reload &
uv run streamlit run src/ui/app.py
```

### Competition Demo
```bash
# Single command deployment
docker-compose up -d

# Health check
curl http://localhost:8000/api/v1/health

# Access demo
open http://localhost:8501
```

### Testing
```bash
# Run tests
uv run pytest tests/

# Code formatting
uv run black src/
uv run isort src/

# Performance testing
uv run python scripts/load_test.py
```

## Competitive Advantages

1. **JSON Refactorer Intelligence**: Unique TikTok terminology expansion capability
2. **Multi-Agent Architecture**: Sophisticated AI orchestration with LangGraph
3. **Visual Workflow**: Real-time execution tracking and performance metrics
4. **Production Ready**: Professional deployment, monitoring, and error handling
5. **Comprehensive Coverage**: 5 jurisdictions with specialized legal expertise

## Security Considerations

- **Input Sanitization**: Remove PII patterns before processing
- **API Key Management**: Secure LLM API key handling
- **Prompt Injection Protection**: Sanitize user inputs to prevent attacks
- **Data Hashing**: Cache-safe hashing without storing original sensitive data

## Integration Requirements

### MCP Team Coordination
- **Framework**: MCPs use FastMCP framework with ChromaDB for vector storage
- **Service Discovery**: HTTP endpoints accessible via Docker network
- **Health Monitoring**: `/health` endpoint for system checks
- **Performance**: <30 second response time per analysis
- **Docker Integration**: Shared ChromaDB instance for all MCPs

### LLM Service Requirements
- **Primary**: Claude Sonnet 4 via Anthropic API
- **Fallback**: GPT-4 via OpenAI API  
- **Optional**: Google Gemini for additional capacity
- **Rate Limiting**: 10 requests per second per model
- **Token Management**: 4000 token limit per request

## Key Files to Understand

1. **src/core/workflow.py**: Main LangGraph orchestration logic
2. **src/core/agents/lawyer_agent.py**: Decision synthesis and MCP coordination
3. **src/ui/app.py**: Primary demo interface
4. **docker-compose.yml**: Service orchestration and deployment
5. **requirements.txt**: Python dependencies and versions

## Success Metrics

- **Technical**: >90% accuracy, <5s response time, >50% cache hit rate
- **Competition**: Top 25% demo quality, advanced technical sophistication
- **Business**: Clear ROI for compliance automation, audit trail capability

---

**Status**: Phase 1 Complete ✅ | Ready for Phase 2 Parallel Development 🚀

*Built for TikTok TechJam 2025 - Automated compliance detection through AI-powered legal expertise*