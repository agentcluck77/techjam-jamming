# CLAUDE.md

This file provides guidance to Claude Code when working in this TikTok Geo-Regulation AI System repository.

## Project Overview

**TikTok Geo-Regulation AI System** - An automated legal compliance analysis system for TikTok features across global jurisdictions using multi-agent architecture. Built for TikTok TechJam 2025 hackathon (72 hours).

### Core Objective
Transform legal compliance detection from manual analysis into an automated, traceable, and auditable process that identifies regulatory requirements and compliance gaps for TikTok features and legal documents.

## Team Structure & Roles

### **Team Lead & System Integrator**: Aloysius
**Responsibilities**:
- Overall system integration and orchestration
- Lawyer Agent implementation and workflows
- UI/UX development with Streamlit
- Database schema and Docker deployment
- Inter-team coordination and API specifications

### **MCP Teams** (4 teammates):
**Legal MCP Team**: Lucas & Vivian (Port 8010)
- Legal document processing and vector storage
- Semantic search and similarity detection
- Past law iteration management
- ChromaDB integration for legal documents

**Requirements MCP Team**: Tingli & JunHao (Port 8011)
- Requirements document processing (PDFs)
- Requirements extraction and structured analysis
- Metadata-based document filtering
- ChromaDB integration for requirements

## Architecture Overview

### **System Integration (Aloysius's Scope)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │ <->│  Lawyer Agent   │ <->│   FastAPI API   │
│   (Frontend)    │    │  (Core Logic)   │    │   (Backend)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
         ┌───────▼───────┐ ┌───▼────┐ ┌──────▼──────┐
         │  Legal MCP    │ │  Req   │ │ Knowledge   │
         │ (Lucas/Vivian)│ │  MCP   │ │    Base     │
         │   Port 8010   │ │(T&J)   │ │             │
         └───────────────┘ │ 8011   │ └─────────────┘
                           └────────┘
```

### **Three Core Workflows**

#### **Workflow 1: Legal Document → Requirements Compliance**
```
User uploads legal document → Legal MCP processes → Lawyer Agent extracts topics 
→ Search Requirements MCP for matches → Generate compliance report
```

#### **Workflow 2: Past Law Iteration Detection**
```
Legal document upload → Legal MCP similarity search → LLM assessment 
→ User prompt (delete/keep) → Update Legal MCP database
```

#### **Workflow 3: Requirements Document → Legal Compliance**
```
User uploads requirements PDF → Requirements MCP processes → Lawyer Agent extracts requirements 
→ Search Legal MCP for regulations → Generate compliance status
```

## Directory Structure

```
techjam-jamming/
├── src/
│   ├── lawyer_agent/           # Core lawyer agent logic (Aloysius)
│   │   ├── workflows/          # TRD workflow implementations
│   │   ├── knowledge_base.py   # User-editable knowledge system
│   │   └── compliance.py       # Compliance assessment logic
│   ├── ui/                     # Streamlit interface (Aloysius)
│   │   ├── pages/             # New document upload pages
│   │   └── components/        # Reusable UI components
│   ├── api/                   # FastAPI endpoints (Aloysius)
│   ├── legal-mcp/            # Legal MCP service (Lucas & Vivian)
│   │   ├── legal-endpoints.md # API specification
│   │   └── server.py          # MCP implementation
│   └── requirements-mcp/      # Requirements MCP service (Tingli & JunHao)
│       ├── requirements-endpoints.md # API specification
│       └── server.py          # MCP implementation
├── docs/
│   ├── TRD-lawyer.md         # Technical requirements (complete)
│   └── system-integration.md # Integration documentation
├── docker-compose.yml        # Service orchestration
├── requirements.txt          # Python dependencies
└── README.md
```

## Implementation Status

### **✅ Completed (Aloysius)**:
- TRD specification and workflow design
- MCP interface specifications (hybrid MCP/HTTP)
- System architecture documentation

### **🚧 In Progress**:
**Aloysius**:
- [ ] Lawyer Agent TRD workflow implementation
- [ ] Streamlit document upload pages
- [ ] Knowledge base text editor
- [ ] User interaction dialogs (HITL)

**MCP Teams**:
- [ ] Legal MCP: ChromaDB + MCP server + HTTP endpoints
- [ ] Requirements MCP: PDF processing + ChromaDB + MCP server

## Key Integration Interfaces

### **Legal MCP Interface (Port 8010)**
**MCP Tools** (for LLM direct calls):
```python
# Unified search tool
search_documents(search_type="semantic|similarity", query="...", document_content="...")
# Document deletion
delete_document(document_id="...", confirm_deletion=True)
```

**HTTP REST API** (for code integration):
```
POST /api/v1/upload          # Document upload
GET  /health                 # Health check
```

### **Requirements MCP Interface (Port 8011)**
**MCP Tools** (for LLM direct calls):
```python
# Unified search tool
search_requirements(search_type="semantic|metadata|bulk_retrieve", query="...", document_id="...")
```

**HTTP REST API** (for code integration):
```
POST /api/v1/upload          # Document upload  
GET  /api/v1/documents       # Document management
GET  /health                 # Health check
```

## Development Guidelines

### **Code Organization Principles**
- **Aloysius**: Focus on system integration, UI/UX, and workflow orchestration
- **MCP Teams**: Focus on specialized document processing and vector operations
- **Clean Interfaces**: Well-defined API contracts between components
- **Mock-First**: Implement with mock MCPs, then integrate real MCPs

### **Communication Patterns**
- **LLM <-> MCP**: Direct MCP tool calls for search operations
- **Code <-> MCP**: HTTP REST APIs for document uploads and management
- **User <-> System**: Streamlit dialogs for human-in-the-loop decisions

### **Technology Stack**
- **Backend**: Python 3.11+, FastAPI, Pydantic models
- **Frontend**: Streamlit with custom components
- **LLMs**: Claude Sonnet 4 (primary), GPT-4 (fallback)
- **Database**: PostgreSQL (audit logs), ChromaDB (vector storage)
- **Deployment**: Docker, docker-compose

## Critical Success Factors

### **Hackathon Constraints (72 hours)**
- **Parallel Development**: MCP teams work independently with clear API contracts
- **Mock-First Development**: Aloysius implements with mocks, integrates real MCPs later
- **MVP Focus**: Core workflows over polish
- **Demo-Ready**: Working end-to-end system by deadline

### **Technical Requirements**
- **Performance**: Document processing <30 seconds
- **Accuracy**: Realistic compliance assessment
- **User Experience**: Intuitive document upload and results display
- **Integration**: Seamless MCP communication via standardized interfaces

## Quick Commands

### **Development Setup**
```bash
# Environment setup
cp .env.template .env
# Edit .env with API keys (Claude, OpenAI)

# Install dependencies
uv sync

# Start core services
docker-compose up -d postgres redis

# Run individual components
uv run python -m src.main                # FastAPI backend
uv run streamlit run src/ui/app.py       # Streamlit frontend
python -m src.legal-mcp.server           # Legal MCP (when ready)
python -m src.requirements-mcp.server    # Requirements MCP (when ready)
```

### **Integration Testing**
```bash
# Test MCP connectivity
curl http://localhost:8010/health        # Legal MCP
curl http://localhost:8011/health        # Requirements MCP

# Test document upload
curl -X POST http://localhost:8010/api/v1/upload -F "file=@test.pdf"

# Test full workflow
uv run python scripts/test_workflows.py

# Test TRD implementation
uv run python test_trd_implementation.py
```

## Key Files for Understanding

### **System Integration (Aloysius)**
1. **src/lawyer_agent/workflows.py** - Core TRD workflow implementations
2. **src/ui/pages/document_upload.py** - New document upload interfaces
3. **src/api/lawyer_endpoints.py** - FastAPI endpoints for workflows
4. **docker-compose.yml** - Service orchestration

### **MCP Integration Points**
1. **src/legal-mcp/legal-endpoints.md** - Legal MCP API specification
2. **src/requirements-mcp/requirements-endpoints.md** - Requirements MCP API specification
3. **docs/TRD-lawyer.md** - Complete technical requirements

## Team Coordination

### **Daily Standups** (Recommended)
- **Progress updates**: What's completed, what's blocked
- **Integration points**: API changes, new dependencies
- **Testing coordination**: End-to-end workflow validation

### **API Contract Changes**
- **Process**: Update .md specification → Notify integration team → Update implementation
- **Backward compatibility**: Maintain existing endpoints during development
- **Version control**: Tag stable API versions for integration

### **Demo Preparation**
- **Aloysius**: End-to-end workflow demo, UI polish
- **MCP Teams**: Performance optimization, error handling
- **Integration**: Joint testing with realistic document sets

---

**Status**: TRD Complete ✅ | Ready for Parallel Implementation 🚀  
**Timeline**: 72-hour hackathon | Focus on core workflows and integration  
**Contact**: Aloysius (System Integration Lead)

*Built for TikTok TechJam 2025 - Automated legal compliance analysis through AI-powered document processing*