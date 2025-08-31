# MCP Integration Guide
## TikTok Geo-Regulation AI System - Legal Semantic Search MCPs

---

## 1. Overview

The MCP team will develop **5 semantic search services** that provide legal context retrieval for each jurisdiction. These services will be called by our **Lawyer Agent** to find relevant legal information from the jurisdiction's legal corpus before making compliance decisions.

**Architecture Flow:**
```
JSON Refactorer → Lawyer Agent → [MCP Search Services] → Lawyer Agent → Final Decision
```

### 1.1 Required MCPs (Semantic Search Services)
1. **Utah Search MCP** - Utah Social Media Regulation Act corpus
2. **EU Search MCP** - EU Digital Services Act corpus  
3. **California Search MCP** - COPPA/CCPA legal corpus
4. **Florida Search MCP** - Florida Online Protections corpus
5. **Brazil Search MCP** - LGPD & Data Localization corpus

---

## 2. Required API Endpoints

### 2.1 Semantic Search Endpoint (CRITICAL)

**Every MCP must expose this exact endpoint:**

```http
POST /api/v1/search
Content-Type: application/json
```

**Request Payload:**
```json
{
  "query": "real-time commerce streaming with payment processing affecting minors",
  "feature_context": {
    "feature_category": "Commerce",
    "risk_indicators": ["payment_processing", "user_generated_content", "minor_access"],
    "geographic_scope": ["United States"]
  },
  "max_results": 5,
  "similarity_threshold": 0.7
}
```

**Required Response Format:**
```json
{
  "jurisdiction": "Utah",
  "results": [
    {
      "chunk_id": "utah_doc_001_chunk_042",
      "source_document": "Utah Social Media Regulation Act",
      "content": "Social media companies must implement age verification systems for users under 18 and obtain parental consent for data collection. This requirement applies to all platforms with more than 100,000 users in Utah.",
      "relevance_score": 0.92,
      "metadata": {
        "document_type": "legislation",
        "chunk_index": 42,
        "character_start": 15420,
        "character_end": 15680
      }
    },
    {
      "chunk_id": "utah_doc_003_chunk_018",
      "source_document": "Utah Minor Protection Online Act",
      "content": "Online platforms facilitating commerce must implement curfew restrictions preventing access by minors between 10:30 PM and 6:30 AM local time.",
      "relevance_score": 0.87,
      "metadata": {
        "document_type": "legislation",
        "chunk_index": 18,
        "character_start": 8920,
        "character_end": 9150
      }
    }
  ],
  "total_results": 2,
  "search_time": 0.34
}
```

### 2.2 Health Check Endpoint (REQUIRED)

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "jurisdiction": "Utah", 
  "version": "1.0.0",
  "timestamp": "2025-08-27T12:34:56Z",
  "corpus_stats": {
    "total_documents": 1247,
    "total_embeddings": 15890,
    "last_updated": "2025-08-27T10:00:00Z"
  },
  "dependencies": {
    "chroma_db": "healthy"
  }
}
```

---

## 3. Integration Architecture

### 3.1 How Our Lawyer Agent Uses Your Services

**The integration flow:**

```python
# Our Lawyer Agent calls your MCP search services
async def analyze_feature_with_legal_context(self, feature_context):
    # Step 1: Create search query from feature context
    search_query = self.generate_search_query(feature_context)
    
    # Step 2: Search all jurisdiction MCPs in parallel
    search_tasks = [
        self.search_legal_corpus(jurisdiction, search_query, feature_context)
        for jurisdiction in ['utah', 'eu', 'california', 'florida', 'brazil']
    ]
    legal_contexts = await asyncio.gather(*search_tasks)
    
    # Step 3: Use retrieved legal context to make compliance decisions
    compliance_decision = await self.make_compliance_decision(
        feature_context, legal_contexts
    )
    
    return compliance_decision
```

### 3.2 Service Discovery

**Your services will be called at these URLs:**

```yaml
# Add to docker-compose.yml
services:
  utah-search-mcp:
    image: tiktok-mcps/utah-search:latest
    ports:
      - "8010:8000"
    environment:
      - CHROMA_HOST=chroma
      - CHROMA_PORT=8000
    
  eu-search-mcp:
    image: tiktok-mcps/eu-search:latest  
    ports:
      - "8011:8000"
      
  california-search-mcp:
    image: tiktok-mcps/california-search:latest
    ports:
      - "8012:8000"
      
  florida-search-mcp:
    image: tiktok-mcps/florida-search:latest
    ports:
      - "8013:8000"
      
  brazil-search-mcp:
    image: tiktok-mcps/brazil-search:latest
    ports:
      - "8014:8000"
```

### 3.3 Our Integration Code

**We call your search services like this:**

```python
MCP_SEARCH_SERVICES = {
    'utah': {'url': 'http://utah-search-mcp:8000', 'timeout': 10, 'retries': 2},
    'eu': {'url': 'http://eu-search-mcp:8000', 'timeout': 10, 'retries': 2},
    'california': {'url': 'http://california-search-mcp:8000', 'timeout': 10, 'retries': 2},
    'florida': {'url': 'http://florida-search-mcp:8000', 'timeout': 10, 'retries': 2},
    'brazil': {'url': 'http://brazil-search-mcp:8000', 'timeout': 10, 'retries': 2}
}

# Parallel legal corpus search across all jurisdictions
async def search_all_jurisdictions(search_query, feature_context):
    tasks = [
        call_search_service(service['url'], search_query, feature_context)
        for service in MCP_SEARCH_SERVICES.values()
    ]
    search_results = await asyncio.gather(*tasks, return_exceptions=True)
    return search_results
```

---

## 4. Field Specifications

### 4.1 Search Request Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `query` | string | ✅ | Natural language search query | "real-time commerce streaming with payment processing affecting minors" |
| `feature_context.feature_category` | string | ❌ | Feature classification for filtering | "Commerce", "Social", "Content" |
| `feature_context.risk_indicators` | array[string] | ❌ | Potential compliance triggers | ["payment_processing", "minor_access"] |
| `feature_context.geographic_scope` | array[string] | ❌ | Geographic context for filtering | ["United States", "European Union"] |
| `max_results` | integer | ❌ | Maximum results to return (default: 5) | 5 |
| `similarity_threshold` | float | ❌ | Minimum similarity score (default: 0.6) | 0.7 |

### 4.2 Search Response Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `jurisdiction` | string | ✅ | Jurisdiction name ("Utah", "EU", "California", "Florida", "Brazil") |
| `results` | array[object] | ✅ | Array of relevant text chunks |
| `results[].chunk_id` | string | ✅ | Unique identifier for the text chunk |
| `results[].source_document` | string | ✅ | Name of the source legal document |
| `results[].content` | string | ✅ | Text content of the chunk (max 1000 chars) |
| `results[].relevance_score` | float | ✅ | Vector similarity score (0.0-1.0) |
| `results[].metadata` | object | ✅ | Chunk positioning and document info |
| `total_results` | integer | ✅ | Total number of results found |
| `search_time` | float | ✅ | Time taken for search in seconds |

---

## 5. Legal Corpus Requirements

### 5.1 Utah Search MCP - Social Media Regulation Act

### 5.2 EU Search MCP - Digital Services Act

### 5.3 California Search MCP - COPPA/CCPA

### 5.4 Florida Search MCP - Online Protections for Minors

### 5.5 Brazil Search MCP - LGPD & Data Localization

---

## 6. Performance Requirements

### 6.1 Search Performance Targets

| Metric | Target | Maximum | Penalty |
|--------|--------|---------|---------|
| Search Response | <1s | 10s (hard timeout) | Request fails |
| Health Check | <100ms | 5s | Service marked unhealthy |
| Concurrent Searches | 10+ | - | Must handle parallel requests |

### 6.2 Search Quality Requirements

- **Relevance**: Top 3 results should have >0.7 similarity score for valid queries
- **Coverage**: Should return results for 90%+ of feature-related queries
- **Accuracy**: Legal content should be current and correctly attributed
- **Completeness**: Include full regulatory context, not just excerpts

---

## 7. ChromaDB Integration

### 7.1 Shared ChromaDB Service

We'll provide a shared ChromaDB instance:

```yaml
chroma:
  image: chromadb/chroma:latest
  ports:
    - "8001:8000" 
  volumes:
    - chroma_data:/chroma/chroma
  environment:
    - CHROMA_SERVER_HOST=0.0.0.0
    - CHROMA_SERVER_HTTP_PORT=8000
```

### 7.2 Collection Naming Convention

Use these collection names for consistency:

```python
COLLECTIONS = {
    'utah': 'utah_legal_corpus',
    'eu': 'eu_dsa_corpus', 
    'california': 'california_coppa_corpus',
    'florida': 'florida_minor_protection_corpus',
    'brazil': 'brazil_lgpd_corpus'
}
```

### 7.3 Document Indexing Strategy

**Simple chunking approach for RAG-only system:**
```python
# Chunk legal documents by fixed size with overlap
def chunk_document(document_text, document_name, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(document_text):
        end = start + chunk_size
        chunk_text = document_text[start:end]
        
        chunk = {
            "id": f"{document_name.lower().replace(' ', '_')}_chunk_{chunk_index:03d}",
            "content": chunk_text,
            "metadata": {
                "source_document": document_name,
                "document_type": "legislation",
                "chunk_index": chunk_index,
                "character_start": start,
                "character_end": min(end, len(document_text))
            }
        }
        chunks.append(chunk)
        
        start += (chunk_size - overlap)
        chunk_index += 1
    
    return chunks

# Index all documents
for document_file in legal_documents:
    document_text = read_file(document_file)
    document_name = extract_document_name(document_file)
    chunks = chunk_document(document_text, document_name)
    
    for chunk in chunks:
        collection.add(chunk)
```

---

## 8. Testing Integration

### 8.1 Test Search Queries

**Test with these queries to validate search quality:**

```json
// High-risk commerce query
{
  "query": "real-time shopping with payment processing affecting minors under 18",
  "feature_context": {
    "feature_category": "Commerce",
    "risk_indicators": ["payment_processing", "minor_access"]
  }
}

// Content moderation query  
{
  "query": "user generated content moderation and harmful content detection",
  "feature_context": {
    "feature_category": "Content",
    "risk_indicators": ["user_generated_content", "content_moderation"]
  }
}

// Data privacy query
{
  "query": "personal data collection and cross-border data transfer",
  "feature_context": {
    "feature_category": "Data Processing",
    "risk_indicators": ["data_collection", "international_transfer"]
  }
}
```

### 8.2 Expected Search Results

**Utah MCP should return for commerce query:**
- Text chunks containing age verification requirements
- Text chunks about parental consent for payment processing  
- Text chunks about minor curfew restrictions for commerce features
- All with relevance scores >0.7 and proper chunk metadata

**EU MCP should return for content query:**
- Text chunks containing content moderation requirements
- Text chunks about risk assessment procedures for UGC platforms
- Text chunks about transparency reporting obligations
- All with proper chunk IDs and source document references

---

## 9. Error Handling

### 9.1 Error Response Format

When search fails, return HTTP 500 with:

```json
{
  "error": {
    "code": "SEARCH_FAILED",
    "message": "ChromaDB collection query timeout",
    "jurisdiction": "Utah",
    "timestamp": "2025-08-27T12:34:56Z",
    "retry_after": 5
  }
}
```

### 9.2 Fallback Strategies

1. **ChromaDB Unavailable**: Return cached/recent search results
2. **Query Too Complex**: Simplify query and retry with lower threshold
3. **No Results Found**: Return empty results with explanation
4. **Timeout**: Return partial results with warning
5. **Invalid Input**: Return HTTP 400 with validation details

---

## 10. Deployment Integration

### 10.1 Docker Requirements

Your search services must be containerizable:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install FastMCP and ChromaDB dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy legal corpus data and search service code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s \
  CMD curl -f http://localhost:8000/health || exit 1

# Start search service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 10.2 Expected Environment Variables

```bash
# ChromaDB connection
CHROMA_HOST=chroma
CHROMA_PORT=8000

# Service configuration
JURISDICTION=Utah  # Unique per service
LOG_LEVEL=INFO
SERVICE_VERSION=1.0.0

# Search optimization
MAX_SEARCH_RESULTS=10
DEFAULT_SIMILARITY_THRESHOLD=0.6
SEARCH_TIMEOUT_SECONDS=10
```

---

## 11. Integration Timeline

### 11.1 Development Phases

- **Phase 1**: ChromaDB collections created, basic search endpoint responding
- **Phase 2**: Full legal corpus indexed, search quality validated
- **Phase 3**: Performance optimization complete, error handling implemented
- **Phase 4**: Integration testing with our Lawyer Agent complete

### 11.2 Integration Checklist

- [ ] All 5 search services build and start successfully
- [ ] POST `/api/v1/search` endpoint responds with correct format
- [ ] GET `/health` endpoint returns service status
- [ ] ChromaDB collections populated with legal corpus
- [ ] Search quality meets relevance thresholds (>0.7 for top results)
- [ ] Performance targets met (<10s response time)
- [ ] Error handling graceful and informative

