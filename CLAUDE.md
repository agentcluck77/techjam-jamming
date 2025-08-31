# CLAUDE.md

This file provides guidance to Claude Code when working in this TikTok Geo-Regulation AI System repository.

## Project Overview

**TikTok Geo-Regulation AI System** - An automated legal compliance analysis system for TikTok features across global jurisdictions using multi-agent architecture. Built for TikTok TechJam 2025 hackathon (72 hours).

### Core Objective
Transform legal compliance detection from manual analysis into an automated, traceable, and auditable process that identifies regulatory requirements and compliance gaps for TikTok features and legal documents.

## Team Structure & Roles

### **Team Lead & System Integrator**: Aloysius
**Responsibilities**:
- ✅ Overall system integration and orchestration (COMPLETED)
- ✅ Lawyer Agent implementation and workflows (COMPLETED)
- ✅ UI/UX development - Next.js Professional Frontend (COMPLETED)
- ✅ Database schema and Docker deployment (COMPLETED)
- ✅ Inter-team coordination and API specifications (COMPLETED)
- ✅ LLM Intelligence Enhancement - eliminated hardcoded parsing (COMPLETED)

### **MCP Implementation Status**: ✅ COMPLETED
**Legal MCP**: Lucas & Vivian (Port 8010) - ✅ IMPLEMENTED
- Legal document processing and vector storage
- Semantic search and similarity detection
- Past law iteration management
- ChromaDB integration for legal documents
- **Status**: Fully functional development MCP with real endpoints

**Requirements MCP**: Tingli & JunHao (Port 8011) - ✅ IMPLEMENTED
- Requirements document processing (PDFs)
- Requirements extraction and structured analysis
- Metadata-based document filtering
- ChromaDB integration for requirements
- **Status**: Fully functional development MCP with real endpoints

## Architecture Overview

### **Current System Architecture (Aloysius - COMPLETED)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Next.js UI ✅  │ <->│  Lawyer Agent ✅│ <->│  FastAPI API ✅ │
│  (Frontend)     │    │  (Core Logic)   │    │   (Backend)     │
│  Professional   │    │  LLM Enhanced   │    │  Full Endpoints │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
         ┌───────▼───────┐ ┌───▼────┐ ┌──────▼──────┐
         │  Legal MCP ✅  │ │  Req   │ │ Knowledge   │
         │  (Functional) │ │ MCP ✅  │ │   Base ✅   │
         │   Port 8010   │ │ 8011   │ │             │
         └───────────────┘ └────────┘ └─────────────┘
```

**Note**: Legal MCP and Requirements MCP are now fully implemented and functional. System uses real MCPs with actual ChromaDB backend, HTTP APIs, and MCP tool interfaces. All document processing, vector search, and similarity detection are fully operational.

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

### **📄 Complete PDF Analysis Workflow (PRODUCTION READY)**

The system provides a comprehensive end-to-end PDF analysis workflow with autonomous agent processing and human-in-the-loop approval:

#### **Step 1: Document Upload & Processing**
```
1. User uploads PDF via drag-and-drop interface (DocumentUpload.tsx)
2. File processed and stored with unique document ID
3. Auto-analysis triggers (triggerAutoAnalysisFromUpload)
4. Legal chat session created with autonomous agent
```

#### **Step 2: Autonomous Agent Analysis**
```
5. Lawyer Agent (src/core/agents/lawyer_agent.py) activated
6. Agent decides to extract requirements using MCP search
7. LLM selects appropriate MCP tool (requirements_mcp)
8. HITL approval prompt generated and displayed in UI
```

#### **Step 3: Human-in-the-Loop (HITL) Approval**
```
9. HITL prompt appears in sidebar: "I want to search requirements_mcp for: 'document_id:xxx...' Should I proceed?"
10. User clicks "Approve" or "Skip"
11. If approved: Agent executes MCP search
12. If skipped: Agent continues without MCP data
```

#### **Step 4: Requirements Extraction**
```
13. Requirements MCP (Port 8011) processes PDF document
14. Extracts functional requirements, API specs, data handling
15. Returns structured requirements data to agent
```

#### **Step 5: Legal Compliance Analysis**
```
16. Agent analyzes extracted requirements against global regulations
17. Identifies compliance gaps (GDPR, CCPA, employment law, etc.)
18. Generates comprehensive compliance report with:
    - Executive summary with risk levels
    - Detailed compliance gaps
    - Regulatory requirements
    - Actionable recommendations
    - Cost estimates and timelines
```

#### **Step 6: Report Delivery**
```
19. Full compliance analysis displayed in real-time
20. Report includes specific regulatory citations
21. Prioritized recommendations with implementation steps
22. Session saved for future reference
```

## Directory Structure (CURRENT STATE)

```
techjam-jamming/
├── src/                        # ✅ COMPLETED Backend
│   ├── core/                   # Core business logic
│   │   ├── agents/            # Lawyer agent & LLM intelligence
│   │   ├── models.py          # Data models
│   │   ├── workflow.py        # Workflow orchestration
│   │   └── llm_service.py     # LLM service with fallbacks
│   ├── api/                   # ✅ FastAPI endpoints (Complete)
│   │   └── endpoints/         # All endpoint implementations
│   ├── legal-mcp/            # ✅ REAL MCP Implementation
│   │   ├── server.py         # FastAPI MCP server
│   │   ├── legal-endpoints.md # API specification
│   │   ├── database.py       # ChromaDB integration
│   │   └── README.md         # Implementation docs
│   ├── requirements-mcp/      # ✅ REAL MCP Implementation
│   │   ├── server.py         # FastAPI MCP server  
│   │   ├── requirements-endpoints.md # API specification
│   │   ├── database.py       # ChromaDB integration
│   │   └── README.md         # Implementation docs
│   ├── services/             # Service layer
│   └── main.py               # ✅ FastAPI application entry
├── frontend/                  # ✅ COMPLETED Next.js Frontend
│   ├── src/
│   │   ├── app/              # Next.js App Router pages
│   │   ├── components/       # Professional UI components
│   │   ├── hooks/            # React hooks for state
│   │   └── lib/              # API client & utilities
│   ├── Dockerfile           # Container configuration
│   └── package.json         # Dependencies
├── archive/                  # Deprecated components
│   └── streamlit_ui/        # ✅ Archived Streamlit UI
├── data/                     # Static data & uploads
├── docs/                     # ✅ Complete documentation
├── scripts/                  # Database setup scripts
├── docker-compose.yml        # ✅ Multi-service orchestration
├── pyproject.toml           # Python project config
└── README.md                # ✅ Complete project documentation
```

## Implementation Status

### **✅ MAJOR COMPLETIONS (Aloysius)**:
- ✅ **Next.js Professional Frontend**: Complete React/Next.js UI with shadcn/ui components
- ✅ **Backend API Implementation**: Comprehensive FastAPI backend with all endpoints
- ✅ **LLM Intelligence Enhancement**: Eliminated hardcoded parsing, full LLM-based processing
- ✅ **Real MCP Integration**: Fully functional Legal and Requirements MCPs with ChromaDB backends
- ✅ **Docker Deployment**: Complete containerization with multi-service orchestration
- ✅ **TRD specification and workflow design**: Complete technical requirements
- ✅ **Streamlit UI Archived**: Legacy UI moved to archive, Next.js is primary frontend
- ✅ **Database Integration**: PostgreSQL setup with health monitoring
- ✅ **Core Workflows**: All three TRD workflows implemented and functional
- ✅ **Autonomous Agent System**: 100% LLM-orchestrated legal compliance chat (Aug 30, 2025)
- ✅ **Cursor-Style Reasoning UI**: Real-time reasoning dropdown with clean UX (Aug 30, 2025)
- ✅ **HITL Integration**: Human-in-the-loop approval system for MCP calls (Aug 30, 2025)
- ✅ **PDF Analysis Workflow**: Complete end-to-end PDF upload → analysis → compliance reporting (Aug 30, 2025)
- ✅ **HITL Prompt Fix**: Fixed missing polling call preventing HITL prompts from appearing (Aug 30, 2025)

### **🏗️ CURRENT STATE**:
**Frontend (Next.js) - PRODUCTION READY**:
- ✅ 5 professional pages with real-time SSE updates
- ✅ HITL sidebar integration (Cursor-style)
- ✅ Document upload/management with progress tracking
- ✅ Zustand state management and TypeScript throughout
- ✅ Docker containerization ready

**Backend (FastAPI) - PRODUCTION READY**:
- ✅ Universal processing endpoint handling all input types
- ✅ Real MCP services for legal/requirements search (fully functional)
- ✅ Database integration and health monitoring
- ✅ LLM service with fallback chain (Gemini/Claude/GPT)
- ✅ Complete API endpoints for frontend integration

### **✅ MCP IMPLEMENTATION COMPLETED**:
**MCP Services**:
- ✅ **Legal MCP**: ChromaDB + MCP server + HTTP endpoints (Port 8010) - FULLY FUNCTIONAL
- ✅ **Requirements MCP**: PDF processing + ChromaDB + MCP server (Port 8011) - FULLY FUNCTIONAL

**Note**: System is fully functional with real MCPs for development and production use.

## 🛠️ **Recent Critical Fixes (Aug 30, 2025)**

### **HITL Prompt Display Issue - RESOLVED** 
**Problem**: HITL approval prompts were not appearing in the frontend despite being correctly generated by the backend.

**Root Cause**: Missing `pollForWorkflowMessages()` call in the auto-analysis trigger function (`triggerAutoChat`).

**Solution Applied**:
```typescript
// Added missing polling call in frontend/src/components/HITLSidebar.tsx:255-258
if (result.workflow_id) {
  setCurrentWorkflowId(result.workflow_id)
  await pollForWorkflowMessages(result.workflow_id)
}
```

**Backend Changes**:
```python
# Fixed prompt filtering logic in src/api/endpoints/legal_chat.py:1288
# Changed from checking 'sent' to 'completed' status
if prompt.get("workflow_id") == workflow_id and not prompt.get("completed", False):
```

**Current Status**: ✅ HITL prompts now display correctly in the UI sidebar

### **Conversation Memory Fix - PENDING**
**Issue**: Agent doesn't retain conversation context between messages.
**Impact**: Each user message starts a fresh conversation instead of continuing the existing one.
**Priority**: Medium - affects user experience but doesn't break core functionality.

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

### **MCP Development Approach**
- **IMPORTANT**: Legal MCP (`src/legal-mcp/`) and Requirements MCP (`src/requirements-mcp/`) are now REAL, functional implementations
- **Treat as Production MCPs**: These are no longer mocks - they have real ChromaDB backends, HTTP APIs, and MCP tool interfaces
- **Full Integration**: The lawyer agent and all workflows use these real MCPs for document processing and search
- **Development Status**: Both MCPs are fully operational and should be treated as production-ready components

### **Code Organization Principles**
- **Aloysius**: Focus on system integration, UI/UX, and workflow orchestration
- **MCP Implementation**: Fully functional specialized document processing and vector operations
- **Clean Interfaces**: Well-defined API contracts between components implemented and operational
- **Production-Ready**: All MCPs are functional with real databases and APIs

### **Communication Patterns**
- **LLM <-> MCP**: Direct MCP tool calls for search operations
- **Code <-> MCP**: HTTP REST APIs for document uploads and management
- **User <-> System**: Streamlit dialogs for human-in-the-loop decisions

### **Technology Stack (CURRENT)**
- **Backend**: Python 3.11+, FastAPI, Pydantic models ✅
- **Frontend**: Next.js 14+ with shadcn/ui (Streamlit archived) ✅
- **LLMs**: Google Gemini (primary), Claude Sonnet 4, GPT-4 (fallbacks) ✅
- **Database**: PostgreSQL (operational), ChromaDB (operational in both MCPs)
- **State Management**: Zustand for React state ✅
- **Deployment**: Docker multi-service orchestration ✅
- **UI Components**: shadcn/ui + Radix UI + Tailwind CSS ✅
- **File Upload**: react-dropzone with progress tracking ✅

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

### **Development Setup (CURRENT)**
```bash
# Environment setup
cp .env.template .env
# Edit .env with API keys (Google/Anthropic/OpenAI)

# OPTION 1: Full Docker deployment (RECOMMENDED)
docker-compose up -d
# Access: Frontend http://localhost:3000, Backend http://localhost:8000

# OPTION 2: Local development
# Install dependencies
uv sync
cd frontend && npm install

# Start database
docker-compose up -d postgres

# Run services
uv run python -m src.main                # FastAPI backend (port 8000)
cd frontend && npm run dev               # Next.js frontend (port 3000)

# MCP Services (REAL implementations)
python -m src.legal-mcp.server           # Legal MCP (port 8010) - FUNCTIONAL
python -m src.requirements-mcp.server    # Requirements MCP (port 8011) - FUNCTIONAL
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

### **System Integration (Aloysius - COMPLETED)**
1. **src/core/workflow.py** - ✅ Core TRD workflow implementations
2. **frontend/src/app/** - ✅ Next.js professional UI pages
3. **src/api/endpoints/** - ✅ Complete FastAPI endpoint implementations
4. **docker-compose.yml** - ✅ Multi-service orchestration
5. **src/core/agents/lawyer_agent.py** - ✅ Enhanced LLM-based lawyer agent
6. **src/main.py** - ✅ FastAPI application with all routers

### **MCP Integration Points (FUNCTIONAL)**
1. **src/legal-mcp/server.py** - Legal MCP FastAPI server (REAL)
2. **src/requirements-mcp/server.py** - Requirements MCP FastAPI server (REAL)
3. **src/legal-mcp/legal-endpoints.md** - Legal MCP API specification
4. **src/requirements-mcp/requirements-endpoints.md** - Requirements MCP API specification
5. **docs/TRD-lawyer.md** - Complete technical requirements

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

**Status**: Core System Complete ✅ | Demo Ready 🎯 | MCP Integration Complete ✅  
**Timeline**: Full system implementation complete | All MCPs operational and integrated  
**Contact**: Aloysius (System Integration Lead)

## Current Capabilities

### **✅ Fully Operational Systems**
- **End-to-End PDF Analysis**: Complete workflow from PDF upload → requirements extraction → compliance analysis
- **Autonomous Agent Processing**: 100% LLM-orchestrated analysis with intelligent MCP tool selection
- **HITL Approval System**: Human-in-the-loop prompts for MCP operations with real-time UI updates
- **Real MCP Integration**: Functional Legal and Requirements MCPs with ChromaDB backends
- **Professional UI**: Next.js frontend with shadcn/ui, real-time polling, and Cursor-style reasoning
- **Comprehensive Compliance Reports**: Detailed analysis with GDPR/CCPA/regulatory gap identification
- **Docker Deployment**: Multi-service orchestration ready for production

### **📊 Current Performance**
- **Document Processing**: <30 seconds for typical PDF analysis
- **HITL Response Time**: Instant prompt display and approval processing
- **MCP Search Speed**: ~2-5 seconds for semantic document search
- **Report Generation**: Comprehensive compliance reports in 30-60 seconds
- **UI Responsiveness**: Real-time updates with 1-second polling intervals

### **🔧 Known Issues & Limitations**
1. **Conversation Memory**: Agent starts fresh conversations instead of continuing context
2. **File Size Limits**: Large PDFs (>50MB) may timeout during processing
3. **MCP Error Handling**: Limited retry logic for MCP service failures
4. **Multi-Language**: Currently optimized for English legal documents only

### **🎯 Demo-Ready Features**
- ✅ **Live PDF Upload**: Drag-and-drop with progress indicators
- ✅ **Real-Time Analysis**: Visible reasoning steps and MCP operations
- ✅ **Interactive HITL**: User can approve/skip MCP calls with explanations
- ✅ **Comprehensive Reports**: Professional compliance analysis with actionable recommendations
- ✅ **Responsive Design**: Works across desktop and tablet form factors

*Built for TikTok TechJam 2025 - Automated legal compliance analysis through AI-powered document processing*
- do not use emojis, use lucide-react icon library instead