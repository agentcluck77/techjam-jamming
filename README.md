# TikTok Geo-Regulation AI System - Team Handover

**Phase 1 Complete ✅ | Ready for Integration 🚀**

Multi-agent AI system for TikTok compliance analysis across global jurisdictions.

---

## 🚀 Quick Start

```bash
# 1. Setup environment
git clone <repository> && cd techjam-jamming
cp .env.template .env

# 2. Add API key to .env (any one works)
# GOOGLE_API_KEY=your_key  # FREE tier available
# ANTHROPIC_API_KEY=your_key
# OPENAI_API_KEY=your_key

# 3. Start system
docker-compose up -d

# 4. Access
# - UI: http://localhost:8501
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
```

---

## 👥 Team Assignments

### 🔍 **MCP Team** (Lucas & JH) - CRITICAL PATH
**Deliverable**: 5 Legal Search Services

#### Your Files
```
src/mcp/                       # YOUR DOMAIN
├── utah-search-mcp/           # Utah Social Media Act
├── eu-search-mcp/             # EU DSA + GDPR  
├── california-search-mcp/     # COPPA/CCPA
├── florida-search-mcp/        # Minor Protection Act
├── brazil-search-mcp/         # LGPD + Data Localization
└── shared-chroma/             # ChromaDB setup

docker-compose.yml             # Add MCP services (lines 68-94)
```

#### Required API
```bash
POST /api/v1/search           # Semantic search endpoint
GET /health                   # Health check

# Ports: 8010-8014 (Utah, EU, CA, FL, Brazil)
# Full specs: docs/MCP.md
```

---

### ⚡ **Team Member 1** - MCP Integration
**What & Why**: Replace mock MCP services with real HTTP clients.

**Deliverable**: Real MCP client + system monitoring

#### Your Files  
```
src/services/                  # YOUR DOMAIN
├── mcp_client.py             # HTTP client for MCP services
├── llm_router.py             # Enhanced LLM fallback chains
└── metrics.py                # Performance monitoring

# MODIFY ONLY THESE LINES:
src/core/workflow.py          # Lines 393-404 (MCP injection)
src/core/agents/lawyer_agent.py # Lines 21-24 (MCP dependency)
src/main.py                   # Lines 34-40, 79-91, 265-275 (health/metrics)
```

#### Tasks
- Replace `src/core/agents/mock_mcps.py` with real HTTP calls
- Add performance monitoring and metrics collection
- Enable flag: `ENABLE_REAL_MCPS=true`

#### Search for: `# TODO: Team Member 1`

---

### ⚡ **Team Member 2** - UI & Batch Processing  
**What & Why**: Transform basic UI into a production-ready platform. Currently users can only analyze one feature at a time.

**Business Impact**:
- **Productivity**: Batch processing lets users analyze 50+ features from CSV instead of one-by-one
- **Insights**: Workflow visualization shows users exactly how their features get analyzed
- **User Experience**: Interactive dashboards make the system feel professional vs prototype

**Deliverable**: Enhanced UI + CSV batch processing

#### Your Files
```
src/ui/components/            # YOUR DOMAIN
├── batch_processor.py        # CSV upload interface
├── workflow_viz.py           # Real-time visualization
├── metrics_dashboard.py      # Performance dashboard
└── enhanced_results.py       # Interactive results

src/api/endpoints/            # YOUR DOMAIN
└── batch.py                  # Batch processing API

# MODIFY ONLY THESE LINES:
src/ui/app.py                 # Lines 60-74, 385-472 (new components)
src/main.py                   # Lines 213-243 (batch endpoints)
```

#### Tasks
- CSV batch upload with background processing
- Real-time workflow visualization 
- Interactive performance dashboard
- Enhanced UI with charts and progress tracking
- Enable flags: `ENABLE_BATCH_PROCESSING=true`, `ENABLE_WORKFLOW_VIZ=true`

#### Search for: `# TODO: Team Member 2`

---

## 🏗️ System Architecture

### Current (Phase 1)
```
User Input → Smart Router → AI Agents → Mock MCPs → Results
├── JSON Refactorer (TikTok jargon expansion)
├── Lawyer Agent (compliance analysis) 
└── LLM Enhancement (Gemini/Claude/GPT)
```

### Target (Phase 2)
```  
User Input → Router → AI Agents → Real MCPs → Results
├── Real MCP Services (MCP Team)
├── Batch Processing (Team Member 2)
└── Performance Monitoring (Team Member 1)
```

---

## ✅ Current Features (Working)

- **Universal API**: Single `/api/v1/process` endpoint handles any input
- **Smart Routing**: Auto-detects features vs queries vs PDFs  
- **Dual-Mode Analysis**: Compliance analysis + advisory responses
- **LLM Integration**: Google Gemini with model switching
- **5 Jurisdictions**: Utah, EU, California, Florida, Brazil
- **Docker Deploy**: Single-command setup
- **Modern Stack**: FastAPI + Streamlit + PostgreSQL

---

## 🧪 Testing

```bash
# Feature Analysis
curl -X POST http://localhost:8000/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{"name": "Live Shopping", "description": "Real-time shopping with payment processing"}'

# User Query  
curl -X POST http://localhost:8000/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{"query": "What are Utah age verification requirements?"}'

# Health Check
curl http://localhost:8000/api/v1/health
```

---

## 🚨 Integration Rules

### DO NOT TOUCH
```
src/core/agents/         # AI agent logic (complete)
src/core/models.py       # Data models (complete)  
src/core/llm_service.py  # LLM service (complete)
data/                    # Static data (complete)
docs/                    # Documentation (complete)
```

### SHARED FILES (Coordinate!)
```
docker-compose.yml       # MCP Team + Team Member 1
src/main.py             # Team Member 1 + Team Member 2 (different lines)
.env                    # All teams (different flags)
```

### Communication Protocol
1. **Check line ranges** before modifying shared files
2. **Create your directories** - don't modify others  
3. **Report conflicts** immediately if they occur
4. **Test integration** after each major change

---

## 📋 Success Criteria

### MCP Team
- [ ] 5 MCP services responding on ports 8010-8014
- [ ] ChromaDB integration working
- [ ] Search API returns legal document chunks
- [ ] Health checks passing

### Team Member 1  
- [ ] Mock MCP calls replaced with real HTTP
- [ ] Performance metrics collection working
- [ ] All original features still functional

### Team Member 2
- [ ] CSV batch upload working (50+ features)
- [ ] Real-time workflow visualization
- [ ] Interactive performance dashboard  
- [ ] Enhanced UI with charts and progress
- [ ] All original features preserved

### Competition Ready
- [ ] >90% accuracy on test dataset
- [ ] Sub-3-second response times
- [ ] Demo polished and rehearsed
- [ ] All acceptance criteria met

---

## 🏆 Competitive Advantages

1. **Universal Input Processing** - Handles any input type automatically
2. **Multi-Agent Architecture** - Sophisticated AI orchestration  
3. **Dual-Mode Analysis** - Compliance + advisory in one system
4. **Real MCP Integration** - Authentic legal analysis with real databases
5. **Real-Time Visualization** - Live workflow tracking
6. **Comprehensive Coverage** - 5 jurisdictions with specialized expertise
7. **Production Ready** - Professional deployment and monitoring

---

## 🔍 Troubleshooting

**API Key Issues**: Add any one key to `.env` - system works with Google (free), Anthropic, or OpenAI

**Database Issues**: `docker-compose restart postgres`  

**Import Errors**: Run from project root with `uv run python -m src.main`

**Container Issues**: Force rebuild with `docker-compose build --no-cache`

**Detailed Logs**: `docker-compose logs -f app`

---
