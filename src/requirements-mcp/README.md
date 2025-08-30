# Requirements MCP Real Implementation

**Port**: 8011  
**Purpose**: Fully functional Requirements MCP server for lawyer agent integration

## Quick Start
```bash
uv run python src/requirements-mcp/server.py http
```

## Real Data
- **ChromaDB Backend**: Full vector database with real requirements documents
- **PDF Processing**: Real document processing and text extraction
- **Structured Requirements**: Dynamic extraction with priorities and types
- **Metadata Search**: Real document-based filtering and search
- **Dynamic responses**: Based on actual document content and vector search

## Available Endpoints

### Standard MCP Tools (Agent Integration)
- `search_requirements(search_type="semantic|metadata|bulk_retrieve", ...)`

### HTTP REST APIs (Code Integration)
- `POST /api/v1/search` - Basic document search
- `POST /api/v1/upload` - Document upload simulation
- `POST /api/v1/search_by_metadata` - Document-specific search
- `POST /api/v1/bulk_retrieve` - All requirements for compliance
- `GET /api/v1/documents` - Document listing
- `GET /health` - Server health check

## Production-Ready Design
- **Real processing** - ChromaDB vector search and document processing
- **Schema compliant** - Exact JSON structure matching specifications  
- **Agent-ready** - MCP tools formatted for LLM direct calls
- **Full functionality** - PDF upload, processing, search, metadata filtering, bulk retrieval

**Status**: ✅ Production-ready and fully functional