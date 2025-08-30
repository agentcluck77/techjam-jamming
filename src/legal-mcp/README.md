# Legal MCP Server

Real implementation of Legal MCP with PostgreSQL + pgvector semantic search for legal documents.

## Features

- **Semantic Search**: PostgreSQL + pgvector for vector similarity search
- **MCP Protocol**: Full MCP server implementation for LLM direct calls
- **HTTP REST API**: FastAPI endpoints for document upload and search
- **Auto-Embeddings**: Automatic vector generation on document insert/update
- **Multi-Region Support**: Search across EU, Utah, California, Florida, Brazil
- **Real-time Processing**: Live document processing and embedding generation

## Quick Start

### 1. Setup Database Schema

```bash
# Set up techjam schema for law documents
cd scripts
python schema_setup.py

# Add pgvector support and vector columns
psql -d postgres -f data/vector_migration.sql
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create `.env` file:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
```

### 4. Start the Server

```bash
# HTTP server mode (recommended for integration)
python run_server.py http

# MCP protocol mode (for direct MCP communication)
python run_server.py mcp

# Generate embeddings for existing documents
python run_server.py embeddings
```

## API Endpoints

### HTTP REST API

- **POST** `/api/v1/upload` - Upload and process PDF documents
- **POST** `/api/v1/search` - Semantic/similarity search across legal documents
- **GET** `/api/v1/regions` - Get available jurisdictions
- **GET** `/api/v1/bulk_retrieve` - Bulk document retrieval
- **GET** `/health` - Health check with database status

### MCP Tools (for LLM calls)

- `search_documents` - Search legal documents with semantic/similarity/text search
- `delete_document` - Delete legal document (with confirmation)

## Document Processing

### Import Legal Documents

```python
from src2.helpers.db.upsert_law_pdf import upsert_law_pdf_by_name

# Process and import PDF with auto-embedding generation
upsert_law_pdf_by_name(
    region="EU",           # Region: EU, Utah, California, Florida, Brazil
    pdf_file_name="EU_DSA.pdf",  # PDF filename in your document directory
    statute="EU_DSA"       # Statute identifier
)
```

### Search Documents

```python
# Semantic search
curl -X POST http://localhost:8010/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_type": "semantic",
    "query": "data protection requirements for minors",
    "jurisdictions": ["EU", "California"],
    "max_results": 10
  }'

# Similarity search
curl -X POST http://localhost:8010/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_type": "similarity",
    "document_content": "Very large online platforms...",
    "max_results": 5
  }'
```

## Database Schema

### Tables (per region)

- `techjam.t_law_{region}_regulations` - Legal regulations with vector embeddings
- `techjam.t_law_{region}_definitions` - Legal definitions with vector embeddings

### Vector Columns

- `embedding vector(384)` - Sentence transformer embeddings (all-MiniLM-L6-v2)
- `embedding_model VARCHAR(100)` - Embedding model used
- `embedding_created_at TIMESTAMPTZ` - When embedding was generated

## Integration with Main System

The Legal MCP integrates with the main system through:

1. **RealMCPClient** (`src/core/agents/real_mcp_client.py`) - MCP tool calls
2. **MCPSearchClient** (`src/services/mcp_client.py`) - HTTP API calls  
3. **LawyerAgent** - Automatic legal document search and analysis

## Development Commands

```bash
# Check setup and dependencies
python run_server.py check

# Run with verbose logging
python run_server.py http --verbose

# Custom host/port
python run_server.py http --host 127.0.0.1 --port 8015

# Generate embeddings for existing documents
python run_server.py embeddings

# Direct database operations
python src2/helpers/lawer_agent/for_lucas.py EU  # Get regulations for EU
python src2/helpers/lawer_agent/for_lucas_2.py EU "EU_DSA"  # Get definitions
```

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Lawyer Agent      │ <- │  Real MCP Client    │ <- │  Legal Chat API     │
│   (Core Logic)      │    │  (Tool Routing)     │    │  (User Interface)   │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                           │
           └─────────────┬─────────────┘
                         │
           ┌─────────────▼─────────────┐
           │    Legal MCP Server       │
           │  (PostgreSQL + pgvector)  │
           └─────────────┬─────────────┘
                         │
           ┌─────────────▼─────────────┐
           │     PostgreSQL DB         │
           │   techjam.t_law_*_*       │
           │   (with vector columns)   │
           └───────────────────────────┘
```

## Status: ✅ Production Ready

- ✅ Real PostgreSQL + pgvector backend
- ✅ Automatic embedding generation
- ✅ MCP protocol + HTTP API
- ✅ Multi-region search support  
- ✅ Integrated with main system
- ✅ Error handling and logging
- ✅ Health monitoringegion] [statute]"