# Requirements MCP Required Endpoints

**Team**: Tingli & JunHao  
**Port**: 8011  
**Purpose**: Requirements document search and management for lawyer agent workflows

---

## Required Endpoints for Lawyer Agent Integration

### 1. Document Search (Core Functionality)
```
POST /api/v1/search
```
**Purpose**: Search requirements documents (PRDs, specs, user stories) with metadata filtering  
**Request**:
```json
{
    "query": "live shopping payment processing",
    "doc_types": ["prd", "technical", "feature", "user_story"],  // optional filter
    "document_id": "req_doc_12345",  // optional: search only specific document
    "max_results": 5
}
```
**Response**:
```json
{
    "results": [
        {
            "chunk_id": "req_001",
            "content": "Live shopping feature must include payment processing, age verification for purchases...",
            "source_document": "E-commerce Integration Requirements v2.1",
            "relevance_score": 0.9,
            "document_type": "PRD",
            "metadata": {
                "version": "2.1",
                "team": "Commerce Platform",
                "last_updated": "2025-01-15T10:00:00Z",
                "document_id": "req_doc_12345"
            }
        }
    ],
    "total_results": 1,
    "search_time": 0.2
}
```

### 2. Document Upload & Processing (NEW - Required for Workflow 3)
```
POST /api/v1/upload
```
**Purpose**: Upload and process PDF requirements documents  
**Request**: `multipart/form-data`
```
file: [PDF file]
metadata: {
    "document_type": "prd",
    "team": "Commerce Platform", 
    "version": "1.0",
    "uploaded_by": "user123"
}
```
**Response**:
```json
{
    "success": true,
    "document_id": "req_doc_67890",
    "message": "Document uploaded and processed successfully",
    "processing_details": {
        "pages_processed": 15,
        "chunks_created": 23,
        "processing_time": 8.5
    }
}
```
**Error Response**:
```json
{
    "success": false,
    "error": "File format not supported or processing failed",
    "error_code": "UPLOAD_FAILED",
    "details": "PDF could not be parsed"
}
```

### 3. Metadata-Based Document Search (NEW - Required for Workflow 3)
```
POST /api/v1/search_by_metadata
```
**Purpose**: Search only within a specific newly uploaded document using metadata  
**Request**:
```json
{
    "document_id": "req_doc_67890",
    "query": "payment processing requirements",
    "extract_requirements": true  // extract structured requirements from chunks
}
```
**Response**:
```json
{
    "document_id": "req_doc_67890",
    "document_title": "Live Shopping Platform Requirements",
    "extracted_requirements": [
        {
            "requirement_id": "req_67890_001",
            "requirement_text": "Payment processing must support multiple currencies",
            "requirement_type": "functional",
            "priority": "high",
            "chunk_source": "Section 3.2 - Payment Integration"
        },
        {
            "requirement_id": "req_67890_002", 
            "requirement_text": "Age verification required for purchases under 18",
            "requirement_type": "compliance",
            "priority": "critical",
            "chunk_source": "Section 4.1 - User Safety"
        }
    ],
    "total_requirements": 12,
    "extraction_time": 1.2
}
```

### 4. Bulk Requirements Retrieval (NEW - Required for Workflow 1)
```
POST /api/v1/bulk_retrieve
```
**Purpose**: Retrieve ALL requirements documents for compliance checking against new legal documents  
**Request**:
```json
{
    "doc_types": ["prd", "technical", "feature", "user_story"],  // optional filter
    "include_content": true,  // include full content vs just metadata
    "limit": 100,
    "format": "structured"  // return requirements in structured format
}
```
**Response**:
```json
{
    "requirements": [
        {
            "requirement_id": "req_001",
            "requirement_text": "User data must be retained for maximum 180 days",
            "document_title": "Data Retention Policy PRD",
            "document_type": "prd",
            "requirement_type": "compliance",
            "priority": "critical",
            "team": "Privacy Team",
            "last_updated": "2025-01-10T10:00:00Z"
        },
        {
            "requirement_id": "req_002",
            "requirement_text": "Content moderation response time must be within 48 hours",
            "document_title": "Content Safety Technical Spec",
            "document_type": "technical",
            "requirement_type": "operational",
            "priority": "high",
            "team": "Safety Team", 
            "last_updated": "2025-01-12T10:00:00Z"
        }
    ],
    "total_requirements": 47,
    "retrieval_time": 1.5
}
```

### 5. Document Management
```
GET /api/v1/documents
```
**Purpose**: List uploaded documents with metadata  
**Response**:
```json
{
    "documents": [
        {
            "document_id": "req_doc_12345",
            "title": "E-commerce Integration Requirements",
            "document_type": "prd",
            "upload_date": "2025-01-15T10:00:00Z",
            "team": "Commerce Platform",
            "version": "2.1",
            "status": "processed",
            "chunks_count": 23
        }
    ],
    "total_documents": 15
}
```

### 6. Health Check
```
GET /health
```
**Response**:
```json
{
    "status": "healthy",
    "service": "requirements-mcp",
    "version": "1.0", 
    "chroma_status": "connected",
    "document_count": 15,
    "timestamp": "2025-08-29T10:00:00Z"
}
```

---

## Implementation Priority

### **Phase 1 (Critical for Lawyer Agent)**:
1. =� **Document Upload & Processing** (needed for Workflow 3)
2. =� **Metadata-Based Search** (search within specific document)
3.  **Basic Document Search** (should be straightforward)

### **Phase 2 (Performance)**:
4. **Bulk Retrieval** (for Workflow 1 - compliance checking)
5. **Document Management** (for UI integration)
6. **Health Check** (for monitoring)

---

## Technical Notes

### PDF Processing
- Extract text from PDF documents
- Create chunks with proper metadata (document_id, page, section)
- Store in ChromaDB with document-specific filtering capability

### Metadata Filtering
- ChromaDB queries must support filtering by `document_id`
- Enable searching within specific documents only
- Support bulk operations across all documents

### Requirements Extraction
- Parse chunks to identify structured requirements
- Extract requirement type (functional, compliance, operational)
- Identify priority levels and responsible teams

### Error Handling
- Handle PDF parsing failures gracefully
- Return meaningful error messages for upload failures
- Support partial results if some documents fail to process

### Performance Targets
- **PDF Upload**: < 10 seconds for documents <50 pages
- **Search**: < 2 seconds response time
- **Bulk Retrieval**: < 5 seconds for 100+ requirements
- **Metadata Search**: < 3 seconds per document

---

## 🔗 Integration with Lawyer Agent

**LLM Workflows** (via Standard MCP):
- Search for relevant requirements documents (semantic search)
- Search within specific uploaded documents (metadata search)
- Retrieve all requirements for compliance checking (bulk retrieve)

**Code Workflows** (via HTTP REST):
- Document upload and processing
- Document management and listing
- System health monitoring

### Lawyer Agent Usage Patterns:

1. **Workflow 1** (Legal Doc → Requirements Compliance):
   - LLM: `search_requirements(search_type="bulk_retrieve")` to get ALL requirements
   - Check each requirement against new legal document

2. **Workflow 3** (Requirements Doc → Legal Compliance):
   - Code: `POST /api/v1/upload` to process new PDF (steps 1-2)
   - LLM: `search_requirements(search_type="metadata", document_id="...")` to extract requirements (steps 3-6)
   - Legal compliance analysis for extracted requirements

3. **General Usage**:
   - LLM: `search_requirements(search_type="semantic", query="...")` for finding relevant requirements during analysis

---

## Workflow 3 Integration Details

**Your Scope (Steps 1-2)**:
1. User uploads PDF � `POST /api/v1/upload`
2. Requirements MCP processes and stores with metadata

**Lawyer Agent Scope (Steps 3-6)**:
3. Lawyer agent calls `POST /api/v1/search_by_metadata` with new document_id
4. Extract requirements from new document
5. For each extracted requirement � search Legal MCP for applicable regulations
6. Generate compliance status with human-in-the-loop

**Key Integration Point**: `document_id` handoff between your processing and lawyer agent analysis

---

## Questions/Issues

If you have questions about these endpoints, PDF processing requirements, or need clarification on the lawyer agent integration, please reach out.

**Contact**: Lawyer Agent Implementation Team