# Legal MCP Hybrid Interface

**Team**: Lucas & Vivian  
**Port**: 8010  
**Architecture**: **Hybrid** - Standard MCP Tools + HTTP REST APIs

---

## 🔧 Standard MCP Tools (LLM Direct Integration)

These tools are called directly by the LLM in lawyer agent workflows:

### 1. search_documents
```python
{
    "name": "search_documents",
    "description": "Unified search for legal documents - supports both semantic search and similarity detection",
    "inputSchema": {
        "type": "object",
        "properties": {
            "search_type": {
                "type": "string",
                "enum": ["semantic", "similarity"],
                "description": "Type of search: 'semantic' for query-based search, 'similarity' for document similarity"
            },
            "query": {
                "type": "string",
                "description": "Search query for semantic search (required if search_type='semantic')"
            },
            "document_content": {
                "type": "string", 
                "description": "Document content for similarity search (required if search_type='similarity')"
            },
            "jurisdictions": {
                "type": "array",
                "items": {"enum": ["Utah", "EU", "California", "Florida", "Brazil"]},
                "description": "Optional jurisdiction filtering"
            },
            "similarity_threshold": {
                "type": "number",
                "default": 0.8,
                "description": "Minimum similarity score for similarity search (0-1)"
            },
            "max_results": {
                "type": "integer",
                "default": 10,
                "description": "Maximum number of results to return"
            }
        },
        "required": ["search_type"]
    }
}
```

**Example LLM Call (Semantic Search)**:
```json
{
    "tool": "search_documents",
    "parameters": {
        "search_type": "semantic",
        "query": "age verification requirements for social media",
        "jurisdictions": ["Utah", "California"],
        "max_results": 5
    }
}
```

**Example LLM Call (Similarity Search)**:
```json
{
    "tool": "search_documents", 
    "parameters": {
        "search_type": "similarity",
        "document_content": "EU Digital Services Act Amendment 2025 establishes new content moderation requirements...",
        "similarity_threshold": 0.85,
        "max_results": 5
    }
}
```

**Expected Response (Semantic Search)**:
```json
{
    "search_type": "semantic",
    "results": [
        {
            "chunk_id": "utah_001",
            "content": "Utah Social Media Regulation Act requires age verification...",
            "source_document": "Utah Social Media Act Section 13-2a-3",
            "relevance_score": 0.95,
            "jurisdiction": "Utah"
        }
    ],
    "total_results": 3,
    "search_time": 0.8
}
```

**Expected Response (Similarity Search)**:
```json
{
    "search_type": "similarity",
    "similar_documents": [
        {
            "document_id": "legal_doc_456",
            "title": "EU Digital Services Act 2024",
            "similarity_score": 0.92,
            "preview": "EU Digital Services Act establishes content moderation...",
            "jurisdiction": "EU"
        }
    ],
    "total_found": 1,
    "search_time": 0.5
}
```

### 2. delete_document
```python
{
    "name": "delete_document", 
    "description": "Delete a legal document (for removing past iterations)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "document_id": {
                "type": "string",
                "description": "ID of document to delete"
            },
            "confirm_deletion": {
                "type": "boolean",
                "default": true,
                "description": "Confirmation flag for deletion"
            }
        },
        "required": ["document_id"]
    }
}
```

**Example LLM Call**:
```json
{
    "tool": "delete_document",
    "parameters": {
        "document_id": "legal_doc_456",
        "confirm_deletion": true
    }
}
```

**Expected Response**:
```json
{
    "success": true,
    "document_id": "legal_doc_456",
    "message": "Document successfully deleted from ChromaDB"
}
```

---

## 🌐 HTTP REST APIs (Code-Level Operations)

These endpoints are called by lawyer agent code for bulk operations and management:

### 1. Document Upload
```
POST /api/v1/upload
Content-Type: multipart/form-data
```
**Purpose**: Upload legal documents (PDF/text)  
**Usage**: When users upload new legal documents

### 2. Bulk Document Retrieval
```
POST /api/v1/bulk_retrieve
```
**Purpose**: Retrieve all legal documents for compliance checking  
**Usage**: Workflow 1 - check all requirements against new legal document

**Request**:
```json
{
    "document_type": "all",
    "jurisdictions": ["Utah", "EU", "California", "Florida", "Brazil"],
    "include_content": true,
    "limit": 100
}
```

### 3. Health Check
```
GET /health
```
**Purpose**: Service health monitoring

---

## 🔄 Integration Patterns

### Pattern 1: LLM-Driven Search (Standard MCP)
```python
# In lawyer agent - LLM calls MCP tools directly
prompt = f"Search for legal requirements about {topic}"
# LLM decides to call search_documents tool
# MCP returns results directly to LLM
```

### Pattern 2: Bulk Operations (HTTP REST)
```python
# In lawyer agent code - HTTP calls for bulk operations
async def check_all_requirements_compliance(legal_doc_id):
    # Get all legal documents via HTTP
    documents = await http_client.post("/api/v1/bulk_retrieve", {...})
    # Process each document...
```

### Pattern 3: Document Management (HTTP REST)
```python
# File uploads, bulk operations
await http_client.post("/api/v1/upload", files={"document": pdf_file})
```

---

## 🎯 Implementation Priority

### **Phase 1 (Critical for Lawyer Agent)**:
1. 🚨 **Standard MCP Tools**: search_documents (unified), delete_document
2. 🚨 **HTTP Upload**: Document upload endpoint

### **Phase 2 (Performance)**:
3. **HTTP Bulk**: Bulk retrieval for compliance checking
4. **Health Check**: Monitoring endpoint

---

## 📋 Technical Notes

### MCP Server Setup
- Implement standard MCP server with tool definitions
- ChromaDB integration for vector search
- Handle tool calls with proper JSON responses

### HTTP Server Setup  
- FastAPI or similar for REST endpoints
- File upload handling for PDFs
- Bulk operation optimization

### Shared Components
- Single ChromaDB instance for both MCP and HTTP operations
- Consistent document ID scheme across both interfaces
- Shared metadata structure

---

## 🤝 Integration with Lawyer Agent

**LLM Workflows** (via Standard MCP):
- Search for relevant legal documents (semantic search)
- Find similar documents for past iteration detection (similarity search)
- Delete past iterations when user confirms

**Code Workflows** (via HTTP REST):
- Upload new legal documents
- Bulk retrieve documents for compliance checking
- Document management and monitoring

This hybrid approach gives you the best of both worlds: direct LLM integration where needed, and efficient bulk operations via HTTP.