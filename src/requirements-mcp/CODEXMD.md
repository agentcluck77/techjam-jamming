# Requirements MCP - Claude Code Documentation

## Project Structure

This is a FastMCP server for PRD semantic search. The system stores PRD documents in PostgreSQL, chunks them into user-story-sized segments, and enables semantic search using ChromaDB vector embeddings.

## Simple Design Philosophy

**Core Function**: Store PRDs ��' Chunk into user-story sizes ��' Return similar text chunks

The system focuses on:
- Simple PRD storage in PostgreSQL 
- Chunking text into segments similar to average user stories (~50 tokens/200 characters)
- Fast semantic search returning actual PRD text chunks
- No complex analysis - just similarity matching

## Data Structure Design

### PRD Storage Structure

Simple hierarchical structure:

```
Products
�"o�"?�"? TikTok Mobile App
�"'   �"o�"?�"? PRD_v2.1_privacy.pdf
�"'   �"o�"?�"? PRD_v2.1_features.pdf  
�"'   �""�"?�"? PRD_v2.2_beta.pdf
�"o�"?�"? TikTok Creator Studio
�"'   �""�"?�"? PRD_v1.5_ai_tools.pdf
�""�"?�"? TikTok Ads Platform
    �""�"?�"? PRD_v3.0_targeting.pdf
```

### Database Tables

#### 1. `pdfs` - Simple Document Storage
```sql
pdfs (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255),
    file_data BYTEA,                  -- PDF binary data
    uploaded_at TIMESTAMP,
    processed BOOLEAN,
    document_type VARCHAR(50),        -- 'prd', 'legal'
    metadata JSONB,                   -- Simple metadata
    text_content TEXT                 -- Extracted text
)
```

#### 2. `processing_log` - Processing Status
```sql
processing_log (
    id SERIAL PRIMARY KEY,
    pdf_id INTEGER ��' pdfs(id),
    status VARCHAR(20),               -- 'processing', 'completed', 'failed'
    error_message TEXT,
    processed_at TIMESTAMP,
    chunks_created INTEGER
)
```

## Why This Simple Structure?

### 1. **Minimal Complexity**
- Just store documents and process them
- No complex versioning or workflow management
- Focus on the core: text similarity search

### 2. **User-Story Sized Chunks**
- Documents are chunked into ~50 token segments
- Similar to typical user story length
- Better semantic matching for PRD content
- Natural text boundaries (sentences, bullet points)

### 3. **Fast Retrieval**
- ChromaDB vector search for semantic similarity
- PostgreSQL for document storage and metadata
- Simple query: "Find text similar to this input"
- Returns actual PRD text chunks with metadata

## Example Usage Patterns

### Upload a New PRD Version
```json
{
  "product": "TikTok Mobile App",
  "config_name": "v2.3-ai-features",
  "version": "2.3.0",
  "status": "draft",
  "documents": [
    "PRD_v2.3_ai_recommendations.pdf",
    "PRD_v2.3_content_generation.pdf"
  ]
}
```

### Query PRD History
```sql
-- Get all versions of TikTok Mobile App PRDs
SELECT p.product_name, c.config_name, c.version, c.status, d.file_name
FROM products p
JOIN prd_configs c ON p.id = c.product_id  
JOIN documents d ON c.id = d.prd_config_id
WHERE p.product_name = 'TikTok Mobile App'
ORDER BY c.created_at DESC;
```

### Compliance Analysis Workflow
1. Upload PRD documents to a config
2. Process documents to generate embeddings
3. Run compliance check against legal corpus
4. Store analysis results with risk score
5. Route to legal team for review if high risk

## Development Notes

### Running Commands
```bash
# Start all services
docker-compose up -d

# Process new documents
docker-compose exec mcp-server python -m src.scripts.process_pdfs

# Run compliance analysis
python example_usage.py
```

### Key Files
- `src/mcp_server/main.py` - FastMCP server with tools
- `src/scripts/process_pdfs.py` - PDF processing pipeline
- `scripts/init.sql` - Database schema
- `docker-compose.yml` - Service orchestration

### MCP Tools
1. **upload_prd** - Upload PRD with config info
2. **create_product** - Create new product entry
3. **create_prd_config** - Create new version config
4. **semantic_search** - Search documents by similarity
5. **legal_compliance_check** - Analyze PRD vs legal requirements
6. **get_prd_history** - Get version history for products

## Future Enhancements

1. **Automated Risk Scoring** - ML model for compliance risk assessment
2. **Change Detection** - Diff analysis between PRD versions  
3. **Legal Update Alerts** - Notify when new laws affect existing PRDs
4. **Approval Workflows** - Integration with review/approval systems
5. **API Rate Limiting** - Production security features

