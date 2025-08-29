# Technical Requirements Document (TRD)
## Geo-Regulation AI System - TikTok TechJam 2025

### Document Information
- **Version**: 1.0
- **Date**: August 27, 2025
- **Competition**: TikTok TechJam 2025 - Problem Statement 3
- **Timeline**: 72-hour implementation (MVP focus with production considerations)

---

## 1. System Overview

### 1.1 Architecture Summary
Multi-agent LLM system using LangGraph orchestration with specialized jurisdiction MCPs, designed for 72-hour MVP delivery while maintaining production-grade patterns.

### 1.2 Core Components
- **LangGraph Orchestrator**: Central workflow management
- **JSON Refactorer Agent**: Context enrichment and jargon expansion
- **Lawyer Agent**: Legal analysis coordination
- **Jurisdiction MCPs**: 5 specialized legal compliance agents
- **FastAPI Backend**: REST API and business logic
- **Streamlit Frontend**: Demo interface and visualization
- **Supporting Services**: Redis cache, PostgreSQL storage, metrics

### 1.3 Technology Constraints
- **Timeline**: 72 hours total development time
- **Team Size**: 3-4 developers maximum
- **Deployment**: Single-machine demo capability required
- **Scalability**: Handle competition dataset (estimated 100+ features)

---

## 2. Component Specifications

### 2.1 LangGraph Orchestrator

#### 2.1.1 Responsibilities
- **Input Type Detection**: Classify incoming requests (PDF documents, direct feature descriptions, user queries)
- **Smart Routing**: Route requests to appropriate workflow paths based on input type and completeness
- **Missing Information Handling**: Prompt user for additional information when state/country/context is missing
- **Workflow State Management**: Manage execution order and state across multiple potential paths
- **Response Aggregation**: Aggregate responses from all agents into appropriate output format
- **Error Recovery**: Handle failures and implement retry logic for incomplete processing
- **Real-time Visualization**: Provide execution tracking across different workflow paths

#### 2.1.2 Technical Requirements
```python
# Enhanced workflow definition with multiple paths
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Optional, Literal

class WorkflowState(TypedDict):
    input_data: dict
    input_type: Optional[Literal["pdf_document", "feature_description", "user_query"]]
    pdf_content: Optional[str]  # Extracted PDF text
    enriched_context: Optional[dict]
    legal_analyses: List[dict]
    final_decision: Optional[dict]
    user_advice: Optional[dict]  # For user query responses
    execution_path: List[str]
    error_state: Optional[str]
    confidence_scores: dict
    missing_info: Optional[List[str]]  # Track missing required information
    retry_count: int

class OrchestratorAgent:
    """Enhanced orchestrator with smart routing capabilities"""
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()  # TODO: Team Member 3 - PDF processing
        self.json_refactorer = JSONRefactorer()
        self.lawyer_agent = LawyerAgent()
    
    def detect_input_type(self, input_data: dict) -> str:
        """Classify input type for appropriate routing"""
        if "pdf_file" in input_data or "document_url" in input_data:
            return "pdf_document"
        elif "query" in input_data or input_data.get("type") == "query":
            return "user_query" 
        elif "feature_name" in input_data and "description" in input_data:
            return "feature_description"
        else:
            return "unknown"
    
    def check_completeness(self, input_data: dict, input_type: str) -> List[str]:
        """Check for missing required information"""
        missing = []
        
        if input_type in ["feature_description", "pdf_document"]:
            if not input_data.get("geographic_context"):
                missing.append("geographic_context")
            # Additional validation logic here
        
        return missing
    
    def route_workflow(self, state: WorkflowState) -> str:
        """Route to appropriate workflow path"""
        input_type = state["input_type"]
        missing_info = state.get("missing_info", [])
        
        if missing_info:
            return "request_additional_info"
        elif input_type == "pdf_document":
            return "pdf_processing_path"
        elif input_type == "user_query":
            return "direct_lawyer_query"
        elif input_type == "feature_description":
            return "standard_analysis_path"
        else:
            return "error_handling"
```

#### 2.1.3 Performance Requirements
- **Execution Time**: Complete workflow in <5 seconds (uncached)
- **Concurrency**: Handle 10 parallel analyses
- **Memory**: <512MB per workflow instance
- **Error Recovery**: 3 retry attempts with exponential backoff

#### 2.1.4 Workflow Architecture

**Multiple Workflow Paths:**
```python
def create_enhanced_workflow():
    workflow = StateGraph(WorkflowState)
    
    # Core routing nodes
    workflow.add_node("input_detector", detect_input_type_node)
    workflow.add_node("completeness_checker", check_completeness_node)  
    workflow.add_node("router", route_request_node)
    
    # Processing paths
    workflow.add_node("pdf_processor", pdf_processing_node)      # TODO: Team Member 3
    workflow.add_node("json_refactorer", json_refactor_node)
    workflow.add_node("lawyer_agent", lawyer_analysis_node)
    workflow.add_node("direct_lawyer", direct_lawyer_query_node)
    
    # Utility nodes
    workflow.add_node("request_info", request_additional_info_node)
    workflow.add_node("format_response", format_response_node)
    
    # Routing logic
    workflow.add_edge(START, "input_detector")
    workflow.add_edge("input_detector", "completeness_checker")
    workflow.add_conditional_edges(
        "completeness_checker",
        route_on_completeness,
        {
            "complete": "router",
            "incomplete": "request_info"
        }
    )
    workflow.add_conditional_edges(
        "router", 
        route_workflow_path,
        {
            "pdf_processing_path": "pdf_processor",
            "standard_analysis_path": "json_refactorer", 
            "direct_lawyer_query": "direct_lawyer",
            "error_handling": "format_response"
        }
    )
    
    # Path connections
    workflow.add_edge("pdf_processor", "json_refactorer")
    workflow.add_edge("json_refactorer", "lawyer_agent")
    workflow.add_edge("lawyer_agent", "format_response")
    workflow.add_edge("direct_lawyer", "format_response")
    workflow.add_edge("request_info", END)  # Return request for more info
    workflow.add_edge("format_response", END)
    
    return workflow.compile()
```

#### 2.1.5 MVP Implementation Priority
- **Phase 1** (Hours 0-6): Basic routing with feature description path
- **Phase 2** (Hours 6-12): Add user query direct routing
- **Phase 3** (Hours 12-18): Completeness validation and retry logic
- **Phase 4** (Hours 18-24): PDF processing integration (Team Member 3)

### 2.2 PDF Processing Agent

#### 2.2.1 Responsibilities
- **PDF Text Extraction**: Extract text content from uploaded PDF documents (PRDs/TRDs)
- **Feature Identification**: Parse extracted text to identify feature descriptions and requirements
- **Document Structure Analysis**: Understand document sections and hierarchy
- **Content Validation**: Verify extraction completeness and quality
- **Format Standardization**: Convert extracted content to standardized format for JSON Refactorer

#### 2.2.2 Technical Specifications
```python
class PDFProcessor:
    """
    TODO: Team Member 3 - PDF Processing Implementation
    Processes PDF documents containing feature requirements and technical specifications
    """
    
    def __init__(self, llm_client: LLMRouter):
        self.llm_client = llm_client
        # TODO: Add PDF processing libraries (PyPDF2, pdfplumber, etc.)
        
    async def process_pdf(self, pdf_data: bytes, filename: str) -> dict:
        """
        Process PDF and extract feature information
        
        Returns:
        {
            "extracted_text": str,
            "identified_features": List[dict],
            "document_metadata": dict,
            "extraction_confidence": float,
            "requires_retry": bool
        }
        """
        # TODO: Implement PDF text extraction
        # TODO: Implement feature identification using LLM
        # TODO: Implement extraction validation
        pass
    
    def extract_text(self, pdf_data: bytes) -> str:
        """Extract raw text from PDF"""
        # TODO: Implement using pdfplumber or similar
        pass
    
    async def identify_features(self, extracted_text: str) -> List[dict]:
        """Use LLM to identify and structure feature descriptions"""
        # TODO: Implement LLM-powered feature extraction
        pass
    
    def validate_extraction(self, features: List[dict]) -> bool:
        """Validate completeness of feature extraction"""
        # TODO: Implement validation logic
        pass
```

#### 2.2.3 MVP Implementation Strategy
- **Hours 0-6**: Placeholder implementation returning mock data
- **Hours 18-24**: **Team Member 3** implements actual PDF processing
- **Integration Points**: 
  - Input: PDF files from API endpoints
  - Output: Structured feature data for JSON Refactorer
  - Error Handling: Invalid PDFs, extraction failures
  - Validation: Completeness checking and retry logic

#### 2.2.4 Technical Requirements
- **Supported Formats**: PDF files up to 10MB
- **Processing Time**: <30 seconds per document
- **Extraction Accuracy**: >85% feature identification rate
- **Integration**: Must output compatible format for JSON Refactorer input

### 2.3 JSON Refactorer Agent

#### 2.3.1 Responsibilities
- **Terminology Expansion**: Expand TikTok-specific jargon and acronyms into legal-friendly language
- **Geographic Context Inference**: Infer geographic implications from implicit references
- **Document Structure Parsing**: Parse and normalize various input document structures
- **Context Enrichment**: Add missing context for comprehensive legal analysis
- **Completeness Validation**: Ensure all critical feature requirements are captured
- **Retry Logic**: Re-process inputs when extraction is incomplete

#### 2.3.2 Enhanced Technical Specifications
```python
class JSONRefactorer:
    """
    Processes raw feature descriptions (from direct input or PDF extraction) 
    into enriched legal context with completeness validation
    """
    
    def __init__(self, llm_client: LLMRouter):
        self.llm_client = llm_client
        self.terminology_db = TerminologyDatabase()
        self.max_retries = 2
    
    async def process(self, raw_input: dict, retry_count: int = 0) -> dict:
        """
        Returns enriched context with:
        - Expanded terminology
        - Geographic implications  
        - Feature categorization
        - Risk indicators
        - Completeness validation
        """
        enriched_context = await self._enrich_context(raw_input)
        
        # Validate completeness
        if not self._is_complete(enriched_context) and retry_count < self.max_retries:
            # Retry with additional prompting
            return await self.process(raw_input, retry_count + 1)
        
        return {
            **enriched_context,
            "processing_complete": self._is_complete(enriched_context),
            "retry_count": retry_count
        }
    
    async def _enrich_context(self, raw_input: dict) -> dict:
        """Core enrichment logic"""
        # TODO: Implement enrichment logic
        pass
    
    def _is_complete(self, enriched_context: dict) -> bool:
        """
        Validate that all important feature requirements are captured
        Original requirement: "if any important feature requirements were removed"
        """
        required_fields = [
            "expanded_description",
            "feature_category", 
            "risk_indicators",
            "geographic_implications"
        ]
        
        for field in required_fields:
            if not enriched_context.get(field):
                return False
                
        # Additional completeness checks
        return len(enriched_context.get("risk_indicators", [])) > 0
```

#### 2.3.3 Data Requirements
- **Terminology Database**: TikTok-specific terms and expansions
- **Geographic Mappings**: Location hints to jurisdiction mappings
- **Feature Categories**: Classification system for legal relevance
- **Completeness Patterns**: Templates for validating complete extractions

#### 2.3.4 MVP Implementation
- **Hours 0-6**: Basic terminology expansion with hardcoded mappings
- **Hours 6-12**: LLM-powered context inference and completeness validation
- **Hours 12-18**: Geographic hint processing and retry logic
- **Hours 18-24**: Advanced validation and edge case handling

### 2.4 Lawyer Agent

#### 2.4.1 Enhanced Responsibilities
- **Feature Analysis Path**: Generate search queries from enriched feature context and analyze compliance
- **Direct Query Path**: Handle user questions and provide legal advice without feature analysis
- **Search Coordination**: Coordinate parallel search across jurisdiction MCP services
- **Legal Analysis**: Analyze legal search results and make compliance decisions for each jurisdiction  
- **Multi-Jurisdiction Synthesis**: Synthesize multi-jurisdiction analysis into unified decision
- **Response Formatting**: Format responses appropriately for compliance tables vs. advisory responses
- **Implementation Guidance**: Generate actionable steps based on applicable regulations

#### 2.4.2 Enhanced Technical Architecture
```python
class LawyerAgent:
    """
    Central coordinator for legal analysis with dual-mode operation:
    1. Feature compliance analysis (with MCP search)
    2. Direct user query responses (advisory mode)
    """
    
    def __init__(self):
        self.mcp_search_client = MCPSearchClient(MCP_SEARCH_SERVICES)
        self.llm_client = LLMRouter()
    
    async def process_request(self, request_data: dict, request_type: str) -> dict:
        """Route to appropriate processing method based on request type"""
        if request_type == "feature_analysis":
            return await self.analyze_feature_compliance(request_data)
        elif request_type == "user_query":
            return await self.handle_user_query(request_data)
        else:
            raise ValueError(f"Unknown request type: {request_type}")
    
    async def handle_user_query(self, query_data: dict) -> dict:
        """
        Handle direct user queries for legal advice
        Original requirement: "if receive user query: output advice"
        """
        user_query = query_data.get("query", "")
        context = query_data.get("context", {})
        
        # Generate advisory response using LLM
        advice_prompt = f"""
        You are a legal compliance expert for TikTok platform regulations.
        
        User Query: {user_query}
        Additional Context: {context}
        
        Provide helpful legal guidance addressing the user's question.
        Focus on practical compliance advice for TikTok features and operations.
        """
        
        advice_response = await self.llm_client.complete(advice_prompt)
        
        return {
            "response_type": "advisory",
            "advice": advice_response["content"],
            "confidence": advice_response.get("confidence", 0.8),
            "sources": ["Legal knowledge base", "Regulatory expertise"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def analyze_feature_compliance(self, enriched_context: dict) -> dict:
        """
        Standard feature compliance analysis path
        Original requirement: "if receive JSON: check compliance for corresponding location"
        """
        # Generate search queries and perform MCP analysis (existing logic)
        return await self.analyze(enriched_context)
    
    def generate_search_query(self, enriched_context: dict) -> str:
        """
        Convert enriched feature context into legal search query
        """
        feature_desc = enriched_context.get("expanded_description", "")
        risk_indicators = enriched_context.get("risk_indicators", [])
        return f"{feature_desc} {' '.join(risk_indicators)}"
    
    async def analyze(self, enriched_context: dict) -> dict:
        """
        Returns unified legal decision with:
        - Compliance requirements per jurisdiction
        - Risk assessment
        - Implementation steps
        - Confidence scoring
        """
        # Step 1: Generate search query
        search_query = self.generate_search_query(enriched_context)
        
        # Step 2: Search all jurisdiction legal corpora in parallel
        search_results = await self.mcp_search_client.search_all_jurisdictions(
            search_query, enriched_context
        )
        
        # Step 3: Analyze each jurisdiction's search results
        jurisdiction_analyses = await self.analyze_jurisdictions(
            enriched_context, search_results
        )
        
        # Step 4: Synthesize into unified decision
        return self.synthesize_decision(jurisdiction_analyses)
    
    async def analyze_jurisdictions(self, enriched_context: dict, search_results: List[dict]) -> List[dict]:
        """
        Analyze compliance for each jurisdiction using search results
        """
        analyses = []
        for search_result in search_results:
            if search_result and "results" in search_result:
                analysis = await self.analyze_single_jurisdiction(
                    enriched_context, search_result
                )
                analyses.append(analysis)
        return analyses
    
    async def analyze_single_jurisdiction(self, enriched_context: dict, search_result: dict) -> dict:
        """
        Perform compliance analysis for single jurisdiction using legal context
        """
        jurisdiction = search_result["jurisdiction"]
        legal_context = "\n".join([
            result["content"] for result in search_result["results"]
        ])
        
        # Use LLM to analyze compliance based on legal context
        analysis_prompt = f"""
        Analyze feature compliance for {jurisdiction} jurisdiction.
        
        Feature Context: {enriched_context}
        
        Relevant Legal Context: {legal_context}
        
        Return structured compliance analysis.
        """
        
        analysis = await self.llm_client.complete(analysis_prompt)
        return {
            "jurisdiction": jurisdiction,
            "legal_context_sources": [r["source_document"] for r in search_result["results"]],
            "compliance_analysis": analysis
        }
```

#### 2.3.3 Decision Logic Requirements
- **Search Query Generation**: Transform feature context into effective legal search queries
- **Legal Context Analysis**: Use LLM to interpret retrieved legal text for compliance implications
- **Multi-Jurisdiction Synthesis**: Aggregate individual jurisdiction analyses into unified decision
- **Risk Scoring**: 1-5 scale based on severity of compliance requirements across jurisdictions
- **Confidence Calculation**: Based on search result relevance and legal context completeness
- **Implementation Guidance**: Actionable steps derived from applicable regulations

#### 2.3.4 Performance Requirements
- **Parallel Search**: All 5 MCP searches execute simultaneously
- **Search Timeout**: 10-second maximum per MCP search
- **Analysis Timeout**: 30-second maximum for LLM-based compliance analysis
- **Fallback Strategy**: Continue with available search results if some MCPs fail
- **Caching**: Store search results and analyses by feature/query hash

### 2.4 Jurisdiction MCPs Integration

#### 2.4.1 MCP Integration Architecture
The jurisdiction MCPs are implemented as **semantic search services** by the MCP team. Our Lawyer Agent integrates with them to retrieve relevant legal context before making compliance decisions. This architecture allows our Lawyer Agent to leverage specialized legal document search capabilities while maintaining full control over compliance analysis.

**Architecture Flow:**
```
JSON Refactorer → Lawyer Agent → [MCP Search Services] → Lawyer Agent → Final Decision
```

#### 2.4.2 Required MCP Search Endpoint

Each jurisdiction MCP must expose the following REST API endpoint for semantic search:

```http
POST /api/v1/search
Content-Type: application/json

Request Body:
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

Response Body:
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
        }
    ],
    "total_results": 2,
    "search_time": 0.34
}
```

#### 2.4.3 MCP Service Discovery

Our system expects the following MCP search services to be available:

```python
MCP_SEARCH_SERVICES = {
    'utah': {
        'url': 'http://utah-search-mcp:8000',
        'timeout': 10,
        'retries': 2
    },
    'eu': {
        'url': 'http://eu-search-mcp:8000', 
        'timeout': 10,
        'retries': 2
    },
    'california': {
        'url': 'http://california-search-mcp:8000',
        'timeout': 10,
        'retries': 2
    },
    'florida': {
        'url': 'http://florida-search-mcp:8000',
        'timeout': 10,
        'retries': 2
    },
    'brazil': {
        'url': 'http://brazil-search-mcp:8000',
        'timeout': 10,
        'retries': 2
    }
}
```

#### 2.4.4 MCP Search Client Implementation

```python
import aiohttp
import asyncio
from typing import Dict, List, Optional

class MCPSearchClient:
    """HTTP client for communicating with jurisdiction MCP search services"""
    
    def __init__(self, service_config: Dict[str, Dict]):
        self.services = service_config
        self.session = None
    
    async def search_legal_corpus(self, 
                                 jurisdiction: str, 
                                 query: str,
                                 feature_context: dict,
                                 max_results: int = 5,
                                 similarity_threshold: float = 0.7) -> Optional[dict]:
        """
        Search legal corpus in specific jurisdiction MCP
        """
        if jurisdiction not in self.services:
            raise ValueError(f"Unknown jurisdiction: {jurisdiction}")
        
        service = self.services[jurisdiction]
        url = f"{service['url']}/api/v1/search"
        
        search_payload = {
            "query": query,
            "feature_context": feature_context,
            "max_results": max_results,
            "similarity_threshold": similarity_threshold
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=search_payload,
                    timeout=aiohttp.ClientTimeout(total=service['timeout'])
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logging.error(f"MCP search {jurisdiction} returned {response.status}")
                        return None
        
        except asyncio.TimeoutError:
            logging.error(f"MCP search {jurisdiction} timeout")
            return None
        except Exception as e:
            logging.error(f"MCP search {jurisdiction} error: {e}")
            return None
    
    async def search_all_jurisdictions(self, 
                                      query: str, 
                                      feature_context: dict) -> List[dict]:
        """
        Execute parallel search across all jurisdiction MCPs
        """
        tasks = [
            self.search_legal_corpus(jurisdiction, query, feature_context)
            for jurisdiction in self.services.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_results = [
            result for result in results 
            if result is not None and not isinstance(result, Exception)
        ]
        
        return valid_results
```

#### 2.4.5 Health Check Requirements

Each MCP service must also expose:

```http
GET /health
Response: 200 OK
{
    "status": "healthy",
    "jurisdiction": "string",
    "version": "string",
    "timestamp": "ISO8601"
}
```

#### 2.4.6 Error Handling Integration

Our system handles MCP search failures gracefully:

- **Timeout**: 10-second maximum per MCP search
- **Retries**: 2 retry attempts with exponential backoff
- **Partial Results**: Continue with available search results from other MCPs
- **Complete Failure**: Use cached legal context or return analysis with lower confidence
- **Search Quality**: Validate relevance scores and filter low-quality results

#### 2.4.7 MCP Team Integration Requirements

The MCP team is using **ChromaDB** for vector storage and **FastMCP** framework. Requirements:

1. **Search Service URLs**: Accessible HTTP endpoints for each jurisdiction search service
2. **Health Monitoring**: `/health` endpoint for system checks
3. **Error Responses**: Structured error messages for debugging
4. **Performance**: <10 second response time per search request
5. **Reliability**: >95% uptime during competition demo
6. **ChromaDB Integration**: Vector embeddings for legal document similarity matching
7. **FastMCP Compliance**: Follow FastMCP service patterns and conventions
8. **Legal Corpus Quality**: High-quality chunking and indexing of legal documents
9. **Search Relevance**: >0.7 similarity score for top results on valid queries

#### 2.4.8 Docker Integration

MCPs using ChromaDB + FastMCP should be deployable alongside our system:

```yaml
# Add to docker-compose.yml
services:
  utah-search-mcp:
    image: tiktok-mcps/utah-search:latest
    ports:
      - "8010:8000"
    environment:
      - LOG_LEVEL=INFO
      - CHROMA_HOST=chroma
      - CHROMA_PORT=8000
      - JURISDICTION=Utah
    depends_on:
      - chroma
  
  eu-search-mcp:
    image: tiktok-mcps/eu-search:latest  
    ports:
      - "8011:8000"
    environment:
      - CHROMA_HOST=chroma
      - CHROMA_PORT=8000
      - JURISDICTION=EU
    depends_on:
      - chroma

  california-search-mcp:
    image: tiktok-mcps/california-search:latest
    ports:
      - "8012:8000"
    environment:
      - CHROMA_HOST=chroma
      - CHROMA_PORT=8000  
      - JURISDICTION=California
    depends_on:
      - chroma

  florida-search-mcp:
    image: tiktok-mcps/florida-search:latest
    ports:
      - "8013:8000"
    environment:
      - CHROMA_HOST=chroma
      - CHROMA_PORT=8000
      - JURISDICTION=Florida
    depends_on:
      - chroma

  brazil-search-mcp:
    image: tiktok-mcps/brazil-search:latest
    ports:
      - "8014:8000"
    environment:
      - CHROMA_HOST=chroma
      - CHROMA_PORT=8000
      - JURISDICTION=Brazil
    depends_on:
      - chroma
    
  # Shared ChromaDB instance for all MCPs
  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000

volumes:
  chroma_data:
```

#### 2.4.9 FastMCP Integration Considerations

Since MCP search services use FastMCP framework, ensure:

1. **Async Support**: FastMCP handles async search operations efficiently
2. **Error Handling**: FastMCP error responses are properly formatted for search failures
3. **Request Validation**: Search request validation follows FastMCP patterns
4. **Performance**: ChromaDB vector searches complete within 10-second timeout
5. **Scaling**: ChromaDB collections properly indexed for fast legal document retrieval
6. **Search Optimization**: Implement query preprocessing and result ranking for legal context

---

## 3. Implementation Strategy - Backbone First Approach

### 3.1 Team Structure & Responsibilities

**Team Composition:**
- **Aloysius (Tech Lead)**: Builds complete backbone system (Hours 0-8)
- **Team Member 1**: Performance & Scale enhancements (Hours 8-24)
- **Team Member 2**: User Experience & Polish (Hours 8-24)
- **Team Member 3**: PDF Processing & Document Analysis (Hours 18-24)
- **MCP Team (3 people)**: Jurisdiction search services (parallel development)

### 3.2 Phase 1: Backbone Development (Aloysius)

#### 3.2.1 Minimal Working System Architecture
```
Input → JSON Refactorer → Mock MCPs → Lawyer Agent → Output
                ↓
        FastAPI Backend → PostgreSQL
                ↓
        Basic Streamlit UI
```

#### 3.2.2 Phase-by-Phase Implementation Plan

**Phase 1A: Foundation Layer**
- [ ] Project setup: directory structure, requirements.txt, .env template
- [ ] Basic LangGraph workflow with sequential execution (no parallel yet)
- [ ] JSON Refactorer with hardcoded terminology dictionary
- [ ] Mock MCP responses (static JSON for each jurisdiction)
- [ ] Core data models and workflow state management

```python
# Minimal LangGraph workflow
def create_backbone_workflow():
    workflow = StateGraph(WorkflowState)
    
    workflow.add_node("json_refactorer", json_refactor_node)
    workflow.add_node("lawyer_agent", lawyer_search_and_analysis_node)
    
    workflow.add_edge(START, "json_refactorer")
    workflow.add_edge("json_refactorer", "lawyer_agent")
    workflow.add_edge("lawyer_agent", END)
    
    return workflow.compile()

# Mock MCP search responses for testing
MOCK_MCP_SEARCH_RESPONSES = {
    "utah": {
        "jurisdiction": "Utah",
        "results": [
            {
                "chunk_id": "utah_doc_001_chunk_042",
                "source_document": "Utah Social Media Regulation Act",
                "content": "Social media companies must implement age verification systems for users under 18 and obtain parental consent for data collection.",
                "relevance_score": 0.92,
                "metadata": {
                    "document_type": "legislation",
                    "chunk_index": 42,
                    "character_start": 15420,
                    "character_end": 15680
                }
            }
        ],
        "total_results": 1,
        "search_time": 0.34
    }
    # ... other jurisdictions
}
```

**Phase 1B: API & Database Layer**
- [ ] FastAPI app with core endpoints: `/analyze-feature`, `/health`
- [ ] PostgreSQL schema: `feature_analyses` table only
- [ ] Basic SQLAlchemy models and database connection
- [ ] Simple error handling and request validation
- [ ] Docker compose for PostgreSQL (no Redis yet)

```python
# Minimal FastAPI setup
@app.post("/api/v1/analyze-feature")
async def analyze_feature(request: FeatureAnalysisRequest):
    # Call LangGraph workflow directly
    result = await workflow.ainvoke({
        "input_data": request.dict(),
        "enriched_context": None,
        "legal_analyses": [],
        "final_decision": None
    })
    
    # Save to database
    analysis = FeatureAnalysis(**result["final_decision"])
    db.add(analysis)
    db.commit()
    
    return result["final_decision"]
```

**Phase 1C: Frontend Layer**
- [ ] Basic Streamlit app with single analysis page
- [ ] Form input: feature name, description, geographic context
- [ ] API integration: call FastAPI backend
- [ ] Results display: compliance status, risk level, requirements
- [ ] No batch processing, no real-time visualization yet

```python
# Minimal Streamlit interface
def main():
    st.title("🎯 TikTok Geo-Regulation AI - MVP")
    
    with st.form("analysis_form"):
        name = st.text_input("Feature Name")
        description = st.text_area("Description")
        geo_context = st.text_input("Geographic Context")
        
        if st.form_submit_button("Analyze"):
            with st.spinner("Analyzing..."):
                result = call_api(name, description, geo_context)
                display_results(result)
```

**Phase 1D: Integration & Handoff Prep**
- [ ] End-to-end testing: form → API → database → results
- [ ] Docker compose with all services
- [ ] Basic error handling and logging
- [ ] **Critical**: Handoff documentation and TODOs
- [ ] Git branches prepared for parallel development

#### 3.2.3 Handoff Deliverables (End of Phase 1)

**Working Demo Capabilities:**
- ✅ Single feature analysis working end-to-end
- ✅ All 5 jurisdictions return mock responses
- ✅ Results saved to database with proper schema
- ✅ Streamlit UI functional for basic testing
- ✅ Docker deployment with `docker-compose up`

**Clear Enhancement Areas Marked:**
```python
# TODO: Team Member 1 - Replace with real MCP search HTTP calls
async def lawyer_search_and_analysis_node(state: WorkflowState):
    # REPLACE: Call actual MCP search services via HTTP
    # This node now handles both search coordination and compliance analysis
    return MOCK_MCP_SEARCH_RESPONSES

# TODO: Team Member 1 - Add Redis caching
async def json_refactor_node(state: WorkflowState):
    # REPLACE: Add caching layer here
    result = await llm_client.complete(prompt)
    return result

# TODO: Team Member 2 - Add batch processing
@app.post("/api/v1/batch-analyze") 
async def batch_analyze():
    # IMPLEMENT: CSV upload and batch processing
    raise NotImplementedError("Team Member 2 - implement batch processing")

# TODO: Team Member 2 - Add workflow visualization  
def render_workflow_diagram():
    # IMPLEMENT: Real-time LangGraph visualization
    raise NotImplementedError("Team Member 2 - implement workflow viz")
```

### 3.3 Phase 2: Parallel Enhancement

#### 3.3.1 Team Member 1: Performance & Scale

**Focus Areas:**
- Replace mock MCP search responses with real HTTP client integration
- Implement Redis caching layer for search results and analyses
- Add parallel MCP search execution to LangGraph workflow
- Performance monitoring and optimization
- Integration with MCP team's search services

**Key Tasks:**
```python
# Replace mock search responses with HTTP calls
class MCPSearchClient:
    async def search_legal_corpus(self, jurisdiction: str, query: str, context: dict):
        async with aiohttp.ClientSession() as session:
            # Real implementation calling MCP search services
            pass

# Add caching throughout the system
class CacheLayer:
    async def get_cached_analysis(self, feature_hash: str):
        # Redis integration
        pass

# Convert workflow to parallel search execution  
def create_parallel_workflow():
    workflow.add_node("lawyer_agent", parallel_search_and_analysis_node)  # All MCP searches at once
    # Update workflow to handle parallel search coordination within lawyer agent
```

#### 3.3.2 Team Member 2: User Experience & Polish

**Focus Areas:**
- CSV batch processing with progress tracking
- Real-time workflow visualization
- Metrics dashboard and system monitoring
- UI polish and error states
- Demo preparation and testing

**Key Tasks:**
```python
# Batch processing implementation
@app.post("/api/v1/batch-analyze")
async def batch_analyze(file: UploadFile):
    # CSV parsing, background job processing
    # Progress tracking with WebSocket updates
    pass

# Workflow visualization
def render_real_time_workflow():
    # LangGraph integration for live execution tracking
    # Dynamic diagram updates during analysis
    pass

# Enhanced UI components
def render_enhanced_results():
    # Interactive charts, jurisdiction breakdowns
    # Export capabilities, historical analysis
    pass
```

#### 3.3.3 Team Member 3: PDF Processing & Document Analysis

**Focus Areas:**
- PDF text extraction and parsing
- LLM-powered feature identification from documents
- Document validation and completeness checking
- Integration with existing JSON Refactorer workflow
- Support for various document formats (PRD, TRD, specifications)

**Key Tasks:**
```python
# PDF Processing Implementation
class PDFProcessor:
    async def process_pdf(self, pdf_data: bytes, filename: str) -> dict:
        # Extract text using pdfplumber/PyPDF2
        # Identify features using LLM
        # Validate extraction completeness
        pass

# Integration with workflow
def pdf_processing_node(state: WorkflowState) -> WorkflowState:
    # Process PDF content
    # Convert to format compatible with JSON Refactorer
    # Handle extraction errors and retries
    pass
```

**Timeline:**
- **Hours 18-20**: PDF extraction library integration
- **Hours 20-22**: LLM feature identification 
- **Hours 22-24**: Integration testing and validation

#### 3.3.4 Aloysius: System Quality & Integration

**Focus Areas:**
- Advanced error handling and retry logic
- Security implementation and validation
- Testing framework and competition dataset validation
- Integration coordination between all team members
- Demo preparation and deployment optimization

**Integration Checkpoints:**
- **Phase 2A**: Merge Team Member 1's caching and MCP integration
- **Phase 2B**: Merge Team Member 2's batch processing and UI enhancements
- **Phase 2C**: Merge Team Member 3's PDF processing capabilities
- **Phase 2D**: Final integration testing and bug fixes

### 3.4 Success Criteria for Each Phase

**Phase 1 Complete (Backbone Ready):**
- [ ] End-to-end demo works reliably
- [ ] All team members can run system locally
- [ ] Clear TODOs marked for enhancement areas
- [ ] Git workflow established for parallel development

**Phase 2A Complete (Performance Integration):**
- [ ] Real MCP search service integration working
- [ ] Caching reduces response time by >50%
- [ ] Parallel search execution implemented
- [ ] No regressions in basic functionality

**Phase 2B Complete (UX Integration):**
- [ ] Batch processing handles 50+ features
- [ ] Workflow visualization updates in real-time  
- [ ] Enhanced UI with metrics dashboard
- [ ] All original functionality preserved

**Phase 2C Complete (Competition Ready):**
- [ ] Competition dataset processing verified
- [ ] Demo rehearsed and polished
- [ ] All acceptance criteria met
- [ ] Deployment automated and documented

---

## 4. API Specifications

### 4.1 FastAPI Backend

#### 4.1.1 Core Endpoints
```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Geo-Regulation AI API", version="1.0.0")

class FeatureAnalysisRequest(BaseModel):
    name: str
    description: str
    geographic_context: Optional[str] = None
    documents: Optional[List[str]] = None
    feature_type: Optional[str] = None

class PDFAnalysisRequest(BaseModel):
    pdf_file: bytes
    filename: str
    geographic_context: Optional[str] = None
    
class UserQueryRequest(BaseModel):
    query: str
    context: Optional[dict] = None

class FeatureAnalysisResponse(BaseModel):
    response_type: Literal["compliance_analysis"] = "compliance_analysis"
    feature_id: str
    compliance_required: bool
    risk_level: int  # 1-5
    applicable_jurisdictions: List[str]
    requirements: List[str]
    implementation_steps: List[str]
    confidence_score: float
    reasoning: str
    analysis_time: float
    
class AdvisoryResponse(BaseModel):
    response_type: Literal["advisory"] = "advisory" 
    advice: str
    confidence: float
    sources: List[str]
    timestamp: str

class AdditionalInfoRequest(BaseModel):
    request_id: str
    missing_fields: List[str]
    message: str

@app.post("/api/v1/analyze-feature", response_model=FeatureAnalysisResponse)
async def analyze_feature(request: FeatureAnalysisRequest):
    """Analyze single feature for geo-compliance requirements"""
    pass

@app.post("/api/v1/analyze-pdf", response_model=FeatureAnalysisResponse) 
async def analyze_pdf(file: UploadFile, geographic_context: Optional[str] = None):
    """Analyze PDF document (PRD/TRD) for compliance requirements"""
    # TODO: Team Member 3 - PDF processing integration
    pass

@app.post("/api/v1/query", response_model=AdvisoryResponse)
async def handle_query(request: UserQueryRequest):
    """Handle direct user queries for legal advice"""
    pass

@app.post("/api/v1/batch-analyze")
async def batch_analyze(background_tasks: BackgroundTasks, file: UploadFile):
    """Process CSV batch of features"""
    pass

@app.get("/api/v1/batch-status/{batch_id}")
async def get_batch_status(batch_id: str):
    """Get status of batch processing job"""
    pass

@app.post("/api/v1/request-info")
async def request_additional_info(request: AdditionalInfoRequest):
    """Request additional information from user when input is incomplete"""
    pass

@app.get("/api/v1/health")
async def health_check():
    """System health and readiness check"""
    pass
```

#### 4.1.2 Error Handling
```python
from enum import Enum

class ErrorCode(Enum):
    INVALID_INPUT = "INVALID_INPUT"
    LLM_SERVICE_ERROR = "LLM_SERVICE_ERROR"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class APIError(BaseModel):
    error_code: ErrorCode
    message: str
    details: Optional[dict] = None
    timestamp: str
```

#### 4.1.3 Performance Requirements
- **Response Time**: <5 seconds for single analysis
- **Throughput**: 10 concurrent requests
- **Batch Size**: Up to 100 features per batch
- **Error Rate**: <5% under normal conditions

### 4.2 WebSocket Interface (Optional for MVP)
```python
@app.websocket("/ws/analysis/{analysis_id}")
async def websocket_analysis_status(websocket: WebSocket, analysis_id: str):
    """Real-time analysis progress updates"""
    # Implementation for live workflow visualization
    pass
```

---

## 5. Database Design

### 5.1 PostgreSQL Schema

#### 5.1.1 Core Tables
```sql
-- Feature analyses storage
CREATE TABLE feature_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_name VARCHAR(255) NOT NULL,
    feature_description TEXT NOT NULL,
    geographic_context TEXT,
    enriched_context JSONB,
    compliance_required BOOLEAN NOT NULL,
    risk_level INTEGER CHECK (risk_level >= 1 AND risk_level <= 5),
    applicable_jurisdictions TEXT[] NOT NULL,
    requirements TEXT[] NOT NULL,
    implementation_steps TEXT[] NOT NULL,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    reasoning TEXT NOT NULL,
    analysis_time FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jurisdiction-specific analysis results
CREATE TABLE jurisdiction_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_analysis_id UUID REFERENCES feature_analyses(id),
    jurisdiction VARCHAR(50) NOT NULL,
    applicable_regulations TEXT[] NOT NULL,
    compliance_required BOOLEAN NOT NULL,
    risk_level INTEGER CHECK (risk_level >= 1 AND risk_level <= 5),
    requirements TEXT[] NOT NULL,
    implementation_steps TEXT[] NOT NULL,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    reasoning TEXT NOT NULL,
    execution_time FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Batch processing jobs
CREATE TABLE batch_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    total_features INTEGER NOT NULL,
    processed_features INTEGER DEFAULT 0,
    failed_features INTEGER DEFAULT 0,
    input_file_path TEXT,
    output_file_path TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System metrics and monitoring
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    tags JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 5.1.2 Indexes for Performance
```sql
CREATE INDEX idx_feature_analyses_created_at ON feature_analyses(created_at);
CREATE INDEX idx_feature_analyses_compliance ON feature_analyses(compliance_required);
CREATE INDEX idx_jurisdiction_analyses_feature_id ON jurisdiction_analyses(feature_analysis_id);
CREATE INDEX idx_jurisdiction_analyses_jurisdiction ON jurisdiction_analyses(jurisdiction);
CREATE INDEX idx_batch_jobs_status ON batch_jobs(status);
CREATE INDEX idx_system_metrics_name_timestamp ON system_metrics(metric_name, timestamp);
```

#### 5.1.3 MVP Database Strategy
- **Hours 0-6**: Basic schema with feature_analyses table
- **Hours 6-12**: Add jurisdiction_analyses for detailed tracking
- **Hours 12-18**: Implement batch_jobs for CSV processing
- **Hours 18-24**: Add system_metrics for performance monitoring

### 5.2 Redis Cache Design

#### 5.2.1 Cache Keys and TTL
```python
CACHE_KEYS = {
    'feature_analysis': 'analysis:{feature_hash}',  # TTL: 1 hour
    'mcp_search_result': 'search:{jurisdiction}:{query_hash}',  # TTL: 30 minutes  
    'llm_response': 'llm:{model}:{prompt_hash}',  # TTL: 24 hours
    'terminology': 'terminology:{version}',  # TTL: 7 days
}

# Feature similarity cache for batch optimization
SIMILARITY_THRESHOLD = 0.85  # Cosine similarity threshold
```

#### 5.2.2 Cache Implementation
```python
import redis
import hashlib
import json
from typing import Optional, Any

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    def generate_feature_hash(self, feature_data: dict) -> str:
        """Generate consistent hash for feature data"""
        normalized = json.dumps(feature_data, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    async def get_cached_analysis(self, feature_hash: str) -> Optional[dict]:
        """Retrieve cached feature analysis"""
        key = f"analysis:{feature_hash}"
        cached = self.redis_client.get(key)
        return json.loads(cached) if cached else None
    
    async def cache_analysis(self, feature_hash: str, result: dict, ttl: int = 3600):
        """Cache feature analysis result"""
        key = f"analysis:{feature_hash}"
        self.redis_client.setex(key, ttl, json.dumps(result))
```

---

## 6. LLM Integration

### 6.1 LLM Router Service

#### 6.1.1 Multi-Model Support
```python
from enum import Enum
import anthropic
import openai
from typing import Optional, Dict, Any

class LLMProvider(Enum):
    CLAUDE_SONNET_4 = "claude-sonnet-4"
    GPT_4 = "gpt-4"

class LLMRouter:
    def __init__(self):
        self.anthropic_client = anthropic.AsyncAnthropic()
        self.openai_client = openai.AsyncOpenAI()
        self.fallback_chain = [
            LLMProvider.CLAUDE_SONNET_4,
            LLMProvider.GPT_4
        ]
    
    async def complete(self, 
                      prompt: str, 
                      model: Optional[LLMProvider] = None,
                      max_tokens: int = 4000,
                      temperature: float = 0.1) -> Dict[str, Any]:
        """
        Execute LLM completion with fallback support
        """
        models_to_try = [model] if model else self.fallback_chain
        
        for model_provider in models_to_try:
            try:
                if model_provider == LLMProvider.CLAUDE_SONNET_4:
                    response = await self.anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=max_tokens,
                        temperature=temperature,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return {
                        "content": response.content[0].text,
                        "model": model_provider.value,
                        "tokens_used": response.usage.total_tokens
                    }
                
                elif model_provider == LLMProvider.GPT_4:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    return {
                        "content": response.choices[0].message.content,
                        "model": model_provider.value,
                        "tokens_used": response.usage.total_tokens
                    }
                    
            except Exception as e:
                logging.warning(f"LLM {model_provider.value} failed: {e}")
                continue
        
        raise Exception("All LLM providers failed")
```

#### 5.1.2 Prompt Templates

```python
class PromptTemplates:
    JSON_REFACTORER = """
    You are a JSON Refactorer specializing in TikTok feature analysis for legal compliance.
    
    Your task is to expand and enrich the following feature description:
    
    Original Input:
    {original_input}
    
    Please provide:
    1. Expanded terminology (convert TikTok jargon to legal-friendly language)
    2. Inferred geographic implications
    3. Feature categorization
    4. Risk indicators
    
    Return enriched context as JSON:
    {{
        "original_feature": "...",
        "expanded_description": "...",
        "geographic_implications": [...],
        "feature_category": "...",
        "risk_indicators": [...],
        "terminology_expansions": {{...}}
    }}
    """
    
    LAWYER_AGENT = """
    You are a specialized legal compliance analyst for TikTok features.
    
    Analyze this enriched feature context for compliance requirements:
    {enriched_context}
    
    Based on the jurisdiction analysis results:
    {jurisdiction_results}
    
    Provide unified legal assessment:
    {{
        "compliance_required": boolean,
        "risk_level": 1-5,
        "applicable_jurisdictions": [...],
        "requirements": [...],
        "implementation_steps": [...],
        "confidence_score": 0.0-1.0,
        "reasoning": "detailed explanation"
    }}
    """
    
    UTAH_MCP = """
    You are a Utah legal expert specializing in the Social Media Regulation Act.
    
    Utah Social Media Regulation Act Requirements:
    - Age verification required for users under 18
    - Curfew restrictions: 10:30 PM - 6:30 AM for minors
    - Parental controls and account access
    - Data collection limitations for minors
    - Addictive design feature restrictions
    
    Analyze this feature for Utah compliance:
    {feature_context}
    
    Return structured analysis:
    {{
        "jurisdiction": "Utah",
        "applicable_regulations": [...],
        "compliance_required": boolean,
        "risk_level": 1-5,
        "requirements": [...],
        "implementation_steps": [...],
        "confidence": 0.0-1.0,
        "reasoning": "detailed explanation"
    }}
    """
```

#### 5.1.3 Performance and Cost Optimization
- **Caching Strategy**: Cache identical prompts for 24 hours
- **Token Limits**: Maximum 4000 tokens per request
- **Rate Limiting**: 10 requests per second per model
- **Cost Tracking**: Monitor token usage across all agents

### 5.2 Structured Output Handling

```python
from pydantic import BaseModel, Field
from typing import List

class JurisdictionAnalysis(BaseModel):
    jurisdiction: str
    applicable_regulations: List[str]
    compliance_required: bool
    risk_level: int = Field(ge=1, le=5)
    requirements: List[str]
    implementation_steps: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class FeatureAnalysisResult(BaseModel):
    feature_id: str
    compliance_required: bool
    risk_level: int = Field(ge=1, le=5)
    applicable_jurisdictions: List[str]
    requirements: List[str]
    implementation_steps: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    jurisdiction_details: List[JurisdictionAnalysis]
    analysis_time: float
```

---

## 6. Frontend Specifications

### 6.1 Streamlit Demo Interface

#### 6.1.1 Application Structure
```python
import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any

def main():
    st.set_page_config(
        page_title="TikTok Geo-Regulation AI",
        page_icon="⚖️",
        layout="wide"
    )
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Single Analysis", "Batch Processing", "System Metrics", "About"]
    )
    
    if page == "Single Analysis":
        render_single_analysis()
    elif page == "Batch Processing":
        render_batch_processing()
    elif page == "System Metrics":
        render_metrics_dashboard()
    elif page == "About":
        render_about_page()

def render_single_analysis():
    """Interactive single feature analysis interface"""
    st.title("🎯 Single Feature Analysis")
    
    # Input form
    with st.form("feature_analysis"):
        col1, col2 = st.columns(2)
        
        with col1:
            feature_name = st.text_input("Feature Name", "Live Shopping")
            feature_description = st.text_area(
                "Feature Description", 
                height=150,
                placeholder="Describe the feature functionality..."
            )
        
        with col2:
            geographic_context = st.text_input(
                "Geographic Context (Optional)",
                placeholder="e.g., Global rollout, US-only, EU-targeted"
            )
            feature_type = st.selectbox(
                "Feature Type",
                ["Content Creation", "Commerce", "Social Features", "Monetization", "Other"]
            )
        
        submit = st.form_submit_button("🔍 Analyze Feature", type="primary")
    
    if submit and feature_name and feature_description:
        analyze_feature_ui(feature_name, feature_description, geographic_context, feature_type)

def analyze_feature_ui(name: str, description: str, geo_context: str, feature_type: str):
    """Execute analysis with real-time progress visualization"""
    
    # Progress containers
    progress_bar = st.progress(0)
    status_container = st.empty()
    workflow_container = st.empty()
    
    # Execute analysis with progress updates
    with st.spinner("Initializing analysis..."):
        try:
            # Call API with streaming updates
            result = call_analysis_api(name, description, geo_context, feature_type)
            
            # Display results
            render_analysis_results(result)
            
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")

def render_analysis_results(result: Dict[str, Any]):
    """Display comprehensive analysis results"""
    
    # Overall assessment
    st.subheader("📊 Overall Assessment")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        compliance_color = "red" if result["compliance_required"] else "green"
        st.metric(
            "Compliance Required", 
            "YES" if result["compliance_required"] else "NO",
            delta=None,
            delta_color=compliance_color
        )
    
    with col2:
        risk_color = "red" if result["risk_level"] >= 4 else "orange" if result["risk_level"] >= 3 else "green"
        st.metric("Risk Level", f"{result['risk_level']}/5")
    
    with col3:
        st.metric("Confidence", f"{result['confidence_score']:.1%}")
    
    with col4:
        st.metric("Analysis Time", f"{result['analysis_time']:.2f}s")
    
    # Jurisdiction breakdown
    if result["compliance_required"]:
        st.subheader("🌍 Jurisdiction Requirements")
        
        for jurisdiction in result["jurisdiction_details"]:
            with st.expander(f"📍 {jurisdiction['jurisdiction']} - Risk Level {jurisdiction['risk_level']}/5"):
                st.write("**Applicable Regulations:**")
                for reg in jurisdiction["applicable_regulations"]:
                    st.write(f"• {reg}")
                
                st.write("**Requirements:**")
                for req in jurisdiction["requirements"]:
                    st.write(f"• {req}")
                
                st.write("**Implementation Steps:**")
                for step in jurisdiction["implementation_steps"]:
                    st.write(f"• {step}")
                
                st.write(f"**Reasoning:** {jurisdiction['reasoning']}")
    
    # Implementation guidance
    if result["implementation_steps"]:
        st.subheader("🛠️ Implementation Guidance")
        for i, step in enumerate(result["implementation_steps"], 1):
            st.write(f"{i}. {step}")
```

#### 6.1.2 Batch Processing Interface
```python
def render_batch_processing():
    """CSV batch upload and processing interface"""
    st.title("📄 Batch Feature Analysis")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload CSV file with feature descriptions",
        type=['csv'],
        help="CSV should contain columns: name, description, geographic_context (optional)"
    )
    
    if uploaded_file:
        # Preview data
        df = pd.read_csv(uploaded_file)
        st.subheader("📋 Data Preview")
        st.dataframe(df.head())
        
        # Validation
        required_columns = ['name', 'description']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {missing_columns}")
        else:
            if st.button("🚀 Process Batch", type="primary"):
                process_batch_ui(df)

def process_batch_ui(df: pd.DataFrame):
    """Execute batch processing with progress tracking"""
    
    # Initialize progress tracking
    total_features = len(df)
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.empty()
    
    # Process batch
    batch_id = submit_batch_job(df)
    
    # Poll for results
    results = []
    while True:
        status = get_batch_status(batch_id)
        
        progress = status['processed_features'] / total_features
        progress_bar.progress(progress)
        
        status_text.text(f"Processing: {status['processed_features']}/{total_features} features")
        
        if status['status'] == 'completed':
            results = get_batch_results(batch_id)
            break
        elif status['status'] == 'failed':
            st.error(f"Batch processing failed: {status['error_message']}")
            return
        
        time.sleep(2)  # Poll every 2 seconds
    
    # Display results
    render_batch_results(results)
```

#### 6.1.3 Real-time Workflow Visualization
```python
import graphviz

def render_workflow_diagram(execution_state: Dict[str, Any]):
    """Generate dynamic workflow diagram based on execution state"""
    
    graph = graphviz.Digraph()
    graph.attr(rankdir='TB', size='10,8')
    
    # Node styling based on execution state
    completed_style = {'style': 'filled', 'fillcolor': 'lightgreen'}
    processing_style = {'style': 'filled', 'fillcolor': 'lightyellow'}
    pending_style = {'style': 'filled', 'fillcolor': 'lightgray'}
    error_style = {'style': 'filled', 'fillcolor': 'lightcoral'}
    
    # Add nodes with dynamic styling
    for node_id, node_state in execution_state.items():
        if node_state['status'] == 'completed':
            graph.node(node_id, node_state['label'], **completed_style)
        elif node_state['status'] == 'processing':
            graph.node(node_id, node_state['label'], **processing_style)
        elif node_state['status'] == 'error':
            graph.node(node_id, node_state['label'], **error_style)
        else:
            graph.node(node_id, node_state['label'], **pending_style)
    
    # Add edges
    for edge in execution_state.get('edges', []):
        graph.edge(edge['from'], edge['to'])
    
    return graph
```

#### 6.1.4 MVP Frontend Timeline
- **Hours 0-6**: Basic single analysis form and results display
- **Hours 6-12**: Add batch processing interface
- **Hours 12-18**: Implement workflow visualization
- **Hours 18-24**: Polish UI and add metrics dashboard

---

## 7. Performance Requirements

### 7.1 Response Time Targets

| Component | Target | Maximum | Measurement |
|-----------|--------|---------|-------------|
| Single Feature Analysis | 3s | 5s | End-to-end API response |
| Batch Processing (50 features) | 3min | 5min | Complete batch job |
| Cache Hit Response | 500ms | 1s | Cached result retrieval |
| UI Page Load | 2s | 3s | Initial Streamlit app load |
| Database Queries | 100ms | 500ms | Individual query execution |

### 7.2 Scalability Requirements

#### 7.2.1 Concurrent Processing
```python
# Configuration for hackathon demo
MAX_CONCURRENT_ANALYSES = 10
MAX_BATCH_SIZE = 100
WORKER_PROCESSES = 4
REDIS_MAX_CONNECTIONS = 20
POSTGRES_MAX_CONNECTIONS = 10
```

#### 7.2.2 Memory Management
```python
# Memory limits per component
MEMORY_LIMITS = {
    'langgraph_workflow': '512MB',
    'llm_client': '256MB', 
    'database_connections': '128MB',
    'redis_cache': '256MB',
    'streamlit_app': '512MB'
}

# Total system memory target: <2GB
```

### 7.3 Monitoring and Metrics

#### 7.3.1 Key Metrics Collection
```python
from dataclasses import dataclass
from typing import Dict, List
import time

@dataclass
class PerformanceMetrics:
    request_id: str
    start_time: float
    end_time: float
    component_timings: Dict[str, float]
    memory_usage: Dict[str, float]
    cache_hits: int
    cache_misses: int
    llm_tokens_used: int
    error_count: int

class MetricsCollector:
    def __init__(self):
        self.metrics_buffer: List[PerformanceMetrics] = []
    
    def record_analysis(self, metrics: PerformanceMetrics):
        self.metrics_buffer.append(metrics)
        
        # Store in database for historical tracking
        self.store_metrics(metrics)
    
    def get_system_health(self) -> Dict[str, Any]:
        return {
            'avg_response_time': self.calculate_avg_response_time(),
            'cache_hit_rate': self.calculate_cache_hit_rate(),
            'error_rate': self.calculate_error_rate(),
            'active_connections': self.get_active_connections(),
            'memory_usage': self.get_memory_usage()
        }
```

#### 7.3.2 MVP Performance Strategy
- **Hours 0-6**: Basic timing measurement and logging
- **Hours 6-12**: Add memory monitoring and cache metrics
- **Hours 12-18**: Implement performance dashboard
- **Hours 18-24**: Optimize bottlenecks and tune performance

---

## 8. Security and Privacy

### 8.1 Data Protection

#### 8.1.1 Input Data Handling
```python
from cryptography.fernet import Fernet
import hashlib

class DataProtection:
    def __init__(self):
        # Generate encryption key for sensitive data
        self.cipher_suite = Fernet(Fernet.generate_key())
    
    def sanitize_input(self, feature_data: dict) -> dict:
        """Remove or mask potentially sensitive information"""
        sanitized = feature_data.copy()
        
        # Remove common PII patterns
        pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{16}\b',             # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email
        ]
        
        for field in ['description', 'documents']:
            if field in sanitized:
                for pattern in pii_patterns:
                    sanitized[field] = re.sub(pattern, '[REDACTED]', sanitized[field])
        
        return sanitized
    
    def hash_for_caching(self, data: dict) -> str:
        """Create cache-safe hash without storing original data"""
        normalized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()
```

#### 8.1.2 API Security
```python
from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Simple API key validation for demo security"""
    # For hackathon: basic API key validation
    # Production: implement proper JWT/OAuth
    if credentials.credentials != os.getenv('API_KEY', 'demo-key-2025'):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# Apply to protected endpoints
@app.post("/api/v1/analyze-feature")
async def analyze_feature(
    request: FeatureAnalysisRequest,
    api_key: str = Depends(verify_api_key)
):
    # Protected endpoint implementation
    pass
```

### 8.2 LLM Security

#### 8.2.1 Prompt Injection Protection
```python
class PromptSanitizer:
    def __init__(self):
        self.blocked_patterns = [
            r'ignore previous instructions',
            r'system prompt',
            r'jailbreak',
            r'DAN mode',
            r'pretend you are'
        ]
    
    def sanitize_user_input(self, user_input: str) -> str:
        """Sanitize user input to prevent prompt injection"""
        sanitized = user_input
        
        for pattern in self.blocked_patterns:
            sanitized = re.sub(pattern, '[BLOCKED]', sanitized, flags=re.IGNORECASE)
        
        # Limit input length
        return sanitized[:5000]
    
    def validate_llm_output(self, output: str) -> bool:
        """Validate LLM output doesn't contain sensitive information"""
        sensitive_patterns = [
            r'API[_\s]?KEY',
            r'SECRET[_\s]?KEY', 
            r'PASSWORD',
            r'TOKEN'
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return False
        
        return True
```

### 8.3 MVP Security Implementation
- **Hours 0-6**: Basic input sanitization and API key validation
- **Hours 6-12**: Add prompt injection protection
- **Hours 12-18**: Implement data hashing for caching
- **Hours 18-24**: Security testing and validation

---

## 9. Testing Strategy

### 9.1 Unit Testing

#### 9.1.1 Agent Testing Framework
```python
import pytest
import asyncio
from unittest.mock import Mock, patch

class TestJSONRefactorer:
    @pytest.fixture
    async def json_refactorer(self):
        mock_llm = Mock()
        return JSONRefactorer(mock_llm)
    
    @pytest.mark.asyncio
    async def test_terminology_expansion(self, json_refactorer):
        """Test TikTok jargon expansion"""
        input_data = {
            "name": "ASL Feature",
            "description": "New jellybean for ASL content"
        }
        
        expected_output = {
            "expanded_description": "New feature component for American Sign Language content",
            "terminology_expansions": {
                "ASL": "American Sign Language",
                "jellybean": "feature component"
            }
        }
        
        result = await json_refactorer.process(input_data)
        assert "terminology_expansions" in result
        assert result["terminology_expansions"]["ASL"] == "American Sign Language"

class TestLawyerAgent:
    @pytest.mark.asyncio
    async def test_mcp_coordination(self):
        """Test parallel MCP execution and aggregation"""
        mock_mcps = {
            'utah': Mock(return_value={'compliance_required': True, 'risk_level': 3}),
            'eu': Mock(return_value={'compliance_required': False, 'risk_level': 1}),
        }
        
        lawyer = LawyerAgent()
        lawyer.mcps = mock_mcps
        
        result = await lawyer.analyze({'feature': 'test'})
        
        # Verify aggregation logic
        assert result['compliance_required'] == True  # Any MCP requires compliance
        assert result['risk_level'] >= 3  # Max risk level
```

#### 9.1.2 MCP Testing
```python
class TestUtahMCP:
    @pytest.fixture
    def utah_mcp(self):
        return UtahMCP()
    
    @pytest.mark.asyncio
    async def test_age_verification_detection(self, utah_mcp):
        """Test Utah MCP detects age verification requirements"""
        feature_context = {
            "feature_category": "Social Features",
            "expanded_description": "User profile creation with age collection",
            "geographic_implications": ["United States", "Utah"]
        }
        
        result = await utah_mcp.analyze(feature_context)
        
        assert result["compliance_required"] == True
        assert "age verification" in str(result["requirements"]).lower()
        assert result["risk_level"] >= 2
```

### 9.2 Integration Testing

#### 9.2.1 End-to-End Workflow Testing
```python
class TestWorkflowIntegration:
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self):
        """Test complete feature analysis from input to output"""
        
        test_feature = {
            "name": "Live Shopping",
            "description": "Real-time shopping experience with age verification",
            "geographic_context": "Global rollout including Utah and EU"
        }
        
        # Execute full workflow
        result = await execute_analysis_workflow(test_feature)
        
        # Validate structure
        assert "compliance_required" in result
        assert "jurisdiction_details" in result
        assert len(result["jurisdiction_details"]) > 0
        
        # Validate business logic
        if result["compliance_required"]:
            assert len(result["requirements"]) > 0
            assert len(result["implementation_steps"]) > 0
            assert result["risk_level"] >= 1
```

#### 9.2.2 Performance Testing
```python
class TestPerformance:
    @pytest.mark.asyncio
    async def test_concurrent_analyses(self):
        """Test system handles concurrent requests"""
        
        features = [
            {"name": f"Feature {i}", "description": f"Test feature {i}"}
            for i in range(10)
        ]
        
        start_time = time.time()
        
        # Execute 10 concurrent analyses
        tasks = [execute_analysis_workflow(feature) for feature in features]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        
        # Validate performance
        assert end_time - start_time < 15  # Should complete in under 15 seconds
        assert len(results) == 10
        assert all('compliance_required' in result for result in results)
    
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test caching improves response time"""
        
        feature = {"name": "Test Feature", "description": "Cache test feature"}
        
        # First request (uncached)
        start_time = time.time()
        result1 = await execute_analysis_workflow(feature)
        uncached_time = time.time() - start_time
        
        # Second request (cached)
        start_time = time.time()
        result2 = await execute_analysis_workflow(feature)
        cached_time = time.time() - start_time
        
        # Validate caching effectiveness
        assert cached_time < uncached_time * 0.5  # At least 50% improvement
        assert result1 == result2  # Same results
```

### 9.3 Competition Dataset Validation

#### 9.3.1 Accuracy Testing
```python
class TestCompetitionDataset:
    def load_test_dataset(self):
        """Load competition-provided test dataset"""
        # Load from competition CSV or test cases
        return pd.read_csv('competition_test_dataset.csv')
    
    @pytest.mark.asyncio
    async def test_dataset_accuracy(self):
        """Validate system accuracy against competition dataset"""
        
        test_dataset = self.load_test_dataset()
        correct_predictions = 0
        total_predictions = len(test_dataset)
        
        for _, row in test_dataset.iterrows():
            feature_input = {
                "name": row["feature_name"],
                "description": row["feature_description"],
                "geographic_context": row.get("geographic_context")
            }
            
            result = await execute_analysis_workflow(feature_input)
            
            # Compare against expected results (if provided)
            if "expected_compliance" in row:
                if result["compliance_required"] == row["expected_compliance"]:
                    correct_predictions += 1
        
        accuracy = correct_predictions / total_predictions
        assert accuracy >= 0.85  # 85% minimum accuracy requirement
```

### 9.4 MVP Testing Timeline
- **Hours 0-6**: Unit tests for core agents
- **Hours 6-12**: Integration tests for workflow
- **Hours 12-18**: Performance and load testing  
- **Hours 18-24**: Competition dataset validation

---

## 10. Deployment and DevOps

### 10.1 Docker Configuration

#### 10.1.1 Multi-Service Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
      - "8501:8501"  # Streamlit
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/geolegal
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=geolegal
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

#### 10.1.2 Application Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start script
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
```

#### 10.1.3 Start Script
```bash
#!/bin/bash
# start.sh

set -e

echo "Starting Geo-Regulation AI System..."

# Wait for database
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 0.1
done

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done

# Run database migrations
echo "Running database setup..."
python scripts/setup_db.py

# Start FastAPI backend
echo "Starting FastAPI backend..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

# Start Streamlit frontend
echo "Starting Streamlit frontend..."
streamlit run demo/app.py --server.port 8501 --server.address 0.0.0.0 &

# Wait for all background processes
wait
```

### 10.2 Environment Configuration

#### 10.2.1 Environment Variables
```bash
# .env.template
# Copy to .env and fill in your values

# LLM API Keys
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/geolegal
REDIS_URL=redis://localhost:6379/0

# Application Settings
API_KEY=your_demo_api_key
LOG_LEVEL=INFO
ENVIRONMENT=development

# Performance Tuning
MAX_CONCURRENT_ANALYSES=10
CACHE_TTL_SECONDS=3600
LLM_TIMEOUT_SECONDS=30
```

#### 10.2.2 Configuration Management
```python
# config.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str
    openai_api_key: str
    api_key: str = "demo-key-2025"
    
    # Database
    database_url: str
    redis_url: str
    
    # Performance
    max_concurrent_analyses: int = 10
    cache_ttl_seconds: int = 3600
    llm_timeout_seconds: int = 30
    
    # Feature flags
    enable_caching: bool = True
    enable_metrics: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 10.3 Health Monitoring

#### 10.3.1 Health Check Endpoints
```python
@app.get("/api/v1/health")
async def health_check():
    """Comprehensive system health check"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check database connection
    try:
        await database.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis connection
    try:
        await redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check LLM service
    try:
        test_result = await llm_router.complete(
            "Test prompt", 
            max_tokens=10,
            timeout=5
        )
        health_status["services"]["llm"] = "healthy"
    except Exception as e:
        health_status["services"]["llm"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/api/v1/metrics")
async def system_metrics():
    """System performance metrics"""
    return await metrics_collector.get_current_metrics()
```

### 10.4 MVP Deployment Strategy

#### 10.4.1 Development Setup (5 minutes)
```bash
# Quick development setup
git clone https://github.com/team/geo-regulation-ai
cd geo-regulation-ai

# Copy environment template
cp .env.template .env
# Edit .env with your API keys

# Start services
docker-compose up -d postgres redis

# Install dependencies  
pip install -r requirements.txt

# Setup database
python scripts/setup_db.py

# Start development servers
python main.py &  # FastAPI backend
streamlit run demo/app.py  # Frontend
```

#### 10.4.2 Competition Demo Setup (1 minute)
```bash
# Single command deployment
docker-compose up -d

# Verify system health
curl http://localhost:8000/api/v1/health

# Access demo interface
open http://localhost:8501
```

#### 10.4.3 Backup Cloud Deployment
- **Platform**: Railway/Render for quick cloud deployment
- **Configuration**: Environment variables through web interface
- **Database**: Managed PostgreSQL and Redis instances
- **Monitoring**: Basic uptime monitoring for demo reliability

---

## 11. Risk Mitigation

### 11.1 Technical Risk Mitigation

| Risk | Probability | Impact | Mitigation Strategy | Implementation |
|------|------------|---------|-------------------|-----------------|
| LLM API Failures | Medium | High | Multiple provider fallback | `LLMRouter` with Claude → GPT-4 fallback |
| Database Connection Issues | Low | Medium | Connection pooling + retries | SQLAlchemy with retry logic |
| Performance Bottlenecks | Medium | Medium | Caching + async processing | Redis cache + asyncio |
| Memory Leaks | Low | High | Resource monitoring + limits | Docker memory limits + monitoring |

### 11.2 Development Risk Mitigation

#### 11.2.1 Time Management
```python
# Development milestone checkpoints
MILESTONES = {
    "Hour 6": ["Core workflow operational", "Basic UI functional"],
    "Hour 12": ["All MCPs implemented", "Caching working"],
    "Hour 18": ["End-to-end demo ready", "Performance acceptable"],
    "Hour 24": ["Competition submission prepared", "Demo rehearsed"]
}

# Risk indicators
RISK_INDICATORS = {
    "red": "Behind by >2 hours",
    "yellow": "Behind by 1-2 hours",
    "green": "On track or ahead"
}
```

#### 11.2.2 Team Coordination Strategy
- **Daily Standups**: 15-minute sync every 8 hours during hackathon
- **Task Assignment**: Clear ownership with backup assignments
- **Code Reviews**: Pair programming for critical components
- **Integration Points**: Well-defined API contracts between components

### 11.3 Competition Risk Mitigation

#### 11.3.1 Demo Failure Prevention
```python
# Demo backup strategies
DEMO_STRATEGIES = [
    {
        "primary": "Live system demonstration",
        "backup": "Pre-recorded demo with live Q&A",
        "fallback": "Static results presentation"
    }
]

# System redundancy
REDUNDANCY_MEASURES = [
    "Local development environment backup",
    "Cloud deployment backup", 
    "Pre-generated results for demo scenarios",
    "Offline mode with cached responses"
]
```

---

## 12. Success Criteria and Acceptance

### 12.1 MVP Acceptance Criteria

#### 12.1.1 Core Functionality ✅
- [ ] Single feature analysis returns compliance decision in <5 seconds
- [ ] All 5 jurisdictions (Utah, EU, California, Florida, Brazil) analyze features
- [ ] Batch processing handles CSV upload/download
- [ ] Results include risk level, requirements, and implementation steps
- [ ] System handles malformed inputs gracefully

#### 12.1.2 Technical Excellence ✅
- [ ] LangGraph orchestration with visual workflow
- [ ] Caching improves repeat query performance by >50%
- [ ] Docker deployment works with single command
- [ ] API documentation auto-generated and accessible
- [ ] Test coverage >70% for core components

#### 12.1.3 Demo Quality ✅
- [ ] Streamlit interface loads and functions properly
- [ ] Real-time workflow visualization during analysis
- [ ] Batch processing shows progress indicators
- [ ] System metrics dashboard displays performance data
- [ ] Error scenarios handled gracefully in UI

### 12.2 Competition Winning Criteria

#### 12.2.1 Technical Sophistication ✅
- [ ] Multi-agent AI architecture with specialized MCPs
- [ ] JSON Refactorer provides unique competitive advantage
- [ ] Performance optimization through intelligent caching
- [ ] Production-ready error handling and monitoring
- [ ] Clean, documented, immediately deployable code

#### 12.2.2 Business Impact ✅
- [ ] >90% accuracy on competition test dataset
- [ ] Addresses genuine TikTok operational challenges
- [ ] Provides audit trail for regulatory compliance
- [ ] Scales to handle enterprise feature analysis volume
- [ ] Clear ROI proposition for compliance automation

#### 12.2.3 Presentation Excellence ✅
- [ ] Compelling 3-minute demo video showcasing capabilities
- [ ] Visual impact with real-time agent execution
- [ ] Performance metrics demonstrate system capabilities
- [ ] Business relevance clearly articulated
- [ ] Technical innovation highlighted effectively

---

## 13. Appendices

### 13.1 Competition Dataset Requirements

#### 13.1.1 Expected CSV Output Format
```csv
feature_name,compliance_required,risk_level,applicable_jurisdictions,requirements,implementation_steps,confidence_score,reasoning
Live Shopping,true,4,"Utah,EU,California","Age verification required,Content moderation needed,Parental controls","Implement ID verification system,Deploy content filtering,Add parental dashboard",0.92,"Feature involves commerce and user-generated content affecting minors"
```

#### 13.1.2 Terminology Table Integration
| TikTok Term | Legal Expansion | Context |
|-------------|-----------------|---------|
| ASL | American Sign Language | Accessibility feature |
| Jellybean | Feature Component | Internal development term |
| Creator Fund | Monetization Program | Revenue sharing system |
| LIVE | Live Streaming | Real-time content broadcast |

### 13.2 Regulation Summary Reference

#### 13.2.1 Utah Social Media Regulation Act
- **Age Verification**: Required for users under 18
- **Curfew Restrictions**: 10:30 PM - 6:30 AM for minors
- **Parental Controls**: Account access and oversight required
- **Addictive Features**: Restrictions on engagement-driving mechanisms

#### 13.2.2 EU Digital Services Act
- **Content Moderation**: Transparent policies and appeals process
- **Risk Assessment**: Systemic risk evaluation for large platforms
- **Algorithmic Transparency**: Recommender system disclosure
- **User Rights**: Content removal appeals and notifications

#### 13.2.3 California COPPA/CCPA
- **Child Protection**: Enhanced privacy for users under 13
- **Data Rights**: Collection, deletion, and portability rights
- **Age-Appropriate Design**: Child-focused interface requirements
- **Parental Consent**: Verified consent for data collection

#### 13.2.4 Florida Online Protections for Minors
- **Social Media Restrictions**: Account creation limitations for minors
- **Parental Oversight**: Required account access for parents
- **Content Filtering**: Harmful content identification and removal
- **Educational Requirements**: Digital literacy components

#### 13.2.5 Brazil LGPD & Data Localization
- **Data Localization**: Brazilian user data storage requirements
- **LGPD Compliance**: General Data Protection Law adherence
- **Cross-Border Transfers**: Restrictions on international data flows
- **User Consent**: Explicit consent requirements for data processing

---

*This Technical Requirements Document provides comprehensive specifications for implementing the Geo-Regulation AI System within the 72-hour TikTok TechJam 2025 timeline. All components are designed for MVP delivery while maintaining production-grade architecture patterns.*