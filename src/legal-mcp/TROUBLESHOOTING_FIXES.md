# Legal MCP Container Troubleshooting Fixes

## 🔧 Issues Found & Fixes Applied:

### Issue 1: ✅ FIXED - Wrong Command Path in Docker
**Problem**: Container was looking for `/app/src/legal-mcp/run_server.py` but file doesn't exist
**Solution**: Updated docker-compose.yml command to use `src/legal-mcp/server.py http`

```yaml
# BEFORE (broken):
command: uv run python src/legal-mcp/run_server.py http --host 0.0.0.0 --port 8010

# AFTER (fixed):
command: uv run python src/legal-mcp/server.py http
```

### Issue 2: ✅ FIXED - Missing PyMuPDF Dependency  
**Problem**: PDF processing failed due to missing PyMuPDF (fitz module)
**Solution**: Added PyMuPDF to pyproject.toml dependencies

```toml
# Added to pyproject.toml:
"PyMuPDF>=1.23.0",
"pgvector>=0.2.0", 
"numpy>=1.24.0",
```

### Issue 3: ✅ FIXED - Sentence Transformer Model Path Issue
**Problem**: Model loading failed due to path being None
**Solution**: Updated server.py to create cache directory and specify path

```python
# BEFORE (broken):
model = SentenceTransformer('all-MiniLM-L6-v2')

# AFTER (fixed):
cache_dir = os.path.join(os.getcwd(), '.sentence_transformers_cache')
os.makedirs(cache_dir, exist_ok=True)
model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=cache_dir)
```

## 🚀 Next Steps to Complete Fix:

### Step 1: Rebuild Container
```bash
cd /path/to/your/project
docker-compose build legal-mcp
```

### Step 2: Start Legal MCP
```bash
docker-compose up -d legal-mcp
```

### Step 3: Test Legal MCP
```bash
# Health check
curl http://localhost:8010/health

# Semantic search test
curl -X POST http://localhost:8010/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"search_type": "semantic", "query": "data protection", "max_results": 5}'
```

### Step 4: Verify Integration
```bash
# Test main system can reach Legal MCP
curl -X POST http://localhost:8000/api/legal-chat-stream \
  -H "Content-Type: application/json" \
  -d '{"message": "What are GDPR requirements?", "chat_id": "test"}'
```

## 📋 Expected Results After Fix:

### ✅ Container Should Start Successfully
- Legal MCP container running on port 8010
- Health endpoint returns `{"status": "healthy"}`
- No more file not found errors

### ✅ Dependencies Should Load
- PyMuPDF (fitz) loads successfully
- Sentence transformer model downloads and caches
- PostgreSQL connection established

### ✅ API Endpoints Should Work
- `/health` - Returns healthy status
- `/api/v1/search` - Semantic search functionality
- `/api/v1/regions` - Available jurisdictions
- `/api/v1/upload` - PDF document upload

### ✅ Integration Should Function
- Main system can call Legal MCP
- Lawyer agent can use real semantic search
- HITL prompts work with real Legal MCP data

## 🔍 Debugging Commands if Issues Persist:

```bash
# Check container logs
docker logs techjam-jamming-legal-mcp-1

# Check container files 
docker exec -it techjam-jamming-legal-mcp-1 ls -la /app/src/legal-mcp/

# Test dependencies inside container
docker exec -it techjam-jamming-legal-mcp-1 uv run python -c "import fitz; print('PyMuPDF OK')"

# Check model download
docker exec -it techjam-jamming-legal-mcp-1 uv run python -c "from sentence_transformers import SentenceTransformer; print('Models OK')"
```

## 📊 Status Summary:

| Issue | Status | Fix Applied |
|-------|--------|-------------|
| Wrong command path | ✅ Fixed | Updated docker-compose.yml |
| PyMuPDF missing | ✅ Fixed | Added to pyproject.toml |
| Model path issue | ✅ Fixed | Updated server.py with cache dir |
| Container won't start | 🔄 Ready to test | All fixes applied |

**Next Action**: Rebuild and restart the container to test all fixes together.