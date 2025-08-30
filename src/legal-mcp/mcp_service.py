#!/usr/bin/env python3
"""
Legal MCP Service - Production Ready
Exposes MCP endpoints and HTTP REST APIs for integration with Lawyer Agent
"""
import uvicorn
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
import chromadb
from datetime import datetime

# ===== Data Models =====

class SemanticSearchRequest(BaseModel):
    search_type: str = "semantic"
    query: str
    jurisdictions: Optional[List[str]] = None
    max_results: int = 10

class SimilaritySearchRequest(BaseModel):
    search_type: str = "similarity"
    document_content: str
    similarity_threshold: float = 0.7
    max_results: int = 10

class MCPToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class BulkRetrieveRequest(BaseModel):
    document_type: str = "all"
    jurisdictions: List[str] = ["utah", "eu", "california", "florida"]
    include_content: bool = True
    limit: int = 100

# ===== Legal MCP Service =====

class LegalMCPService:
    """Legal MCP Service with ChromaDB integration"""
    
    def __init__(self):
        self.collection_name = "legal_regulations"
        self.client = None
        self.collection = None
        self.initialize_chromadb()
        
        # MCP Tools definition
        self.mcp_tools = [
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
                            "description": "Search query for semantic search"
                        },
                        "document_content": {
                            "type": "string", 
                            "description": "Document content for similarity search"
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
            },
            {
                "name": "delete_document",
                "description": "Delete a legal document",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "string"},
                        "confirm_deletion": {"type": "boolean", "default": True}
                    },
                    "required": ["document_id"]
                }
            }
        ]
    
    def initialize_chromadb(self):
        """Initialize ChromaDB"""
        try:
            self.client = chromadb.PersistentClient()
            
            try:
                self.collection = self.client.get_collection(self.collection_name)
                print(f"✅ Connected to existing ChromaDB collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(self.collection_name)
                print(f"✅ Created new ChromaDB collection: {self.collection_name}")
                
        except Exception as e:
            print(f"❌ ChromaDB initialization failed: {e}")
            raise
    
    async def search_documents_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search_documents MCP tool"""
        search_type = arguments.get("search_type")
        start_time = datetime.now()
        
        try:
            if search_type == "semantic":
                return await self._semantic_search(arguments, start_time)
            elif search_type == "similarity":
                return await self._similarity_search(arguments, start_time)
            else:
                return {"error": f"Invalid search_type: {search_type}"}
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    async def _semantic_search(self, arguments: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """Execute semantic search"""
        query = arguments.get("query")
        if not query:
            return {"error": "Query required for semantic search"}
            
        juris = arguments.get("jurisdictions", [])
        jurisdictions = []
        for jurisdiction in juris:
            jurisdictions.append(jurisdiction.lower())
        max_results = arguments.get("max_results", 10)
        
        # Build filters
        where_filter = {}
        if jurisdictions:
            where_filter["region"] = {"$in": jurisdictions}
        
        # Execute search
        results = self.collection.query(
            query_texts=[query],
            n_results=max_results,
            where=where_filter if where_filter else None,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        formatted_results = []
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0] 
        distances = results.get('distances', [[]])[0]
        
        for doc, metadata, distance in zip(documents, metadatas, distances):
            if metadata:
                formatted_results.append({
                    "chunk_id": metadata.get('law_id', 'unknown_chunk'),
                    "content": doc,
                    "source_document": f"{metadata.get('statute', 'Unknown')} {metadata.get('law_id', '')}",
                    "relevance_score": round(1.0 - distance, 3),
                    "jurisdiction": metadata.get('region', 'Unknown')
                })
        
        search_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "search_type": "semantic",
            "results": formatted_results,
            "total_results": len(formatted_results),
            "search_time": round(search_time, 2)
        }
    
    async def _similarity_search(self, arguments: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """Execute document similarity search"""
        document_content = arguments.get("document_content")
        if not document_content:
            return {"error": "Document content required for similarity search"}
            
        similarity_threshold = arguments.get("similarity_threshold", 0.8)
        max_results = arguments.get("max_results", 10)
        
        # Execute similarity search
        results = self.collection.query(
            query_texts=[document_content],
            n_results=max_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Filter by threshold
        similar_documents = []
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        
        for doc, metadata, distance in zip(documents, metadatas, distances):
            similarity_score = 1.0 - distance
            if similarity_score >= similarity_threshold and metadata:
                doc_id = f"{metadata.get('region', 'unknown')}_{metadata.get('law_id', 'unknown')}"
                
                similar_documents.append({
                    "document_id": doc_id,
                    "title": f"{metadata.get('statute', 'Unknown')} {metadata.get('law_id', '')}",
                    "similarity_score": round(similarity_score, 3),
                    "preview": doc[:200] + "..." if len(doc) > 200 else doc,
                    "jurisdiction": metadata.get('region', 'Unknown')
                })
        
        search_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "search_type": "similarity", 
            "similar_documents": similar_documents,
            "total_found": len(similar_documents),
            "search_time": round(search_time, 2)
        }
    
    async def delete_document_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute delete_document MCP tool"""
        document_id = arguments.get("document_id")
        confirm_deletion = arguments.get("confirm_deletion", True)
        
        if not document_id or not confirm_deletion:
            return {"error": "Document ID and confirmation required"}
        
        try:
            # Find document
            all_results = self.collection.get(include=['metadatas'])
            
            matching_ids = []
            for i, metadata in enumerate(all_results.get('metadatas', [])):
                if metadata:
                    doc_id = f"{metadata.get('region', 'unknown')}_{metadata.get('law_id', 'unknown')}"
                    if doc_id == document_id:
                        matching_ids.append(all_results['ids'][i])
            
            if not matching_ids:
                return {"success": False, "message": f"Document {document_id} not found"}
            
            # Delete
            self.collection.delete(ids=matching_ids)
            
            return {"success": True, "message": f"Document {document_id} deleted successfully"}
            
        except Exception as e:
            return {"success": False, "message": f"Deletion failed: {str(e)}"}

# ===== FastAPI Application =====

# Initialize service
legal_mcp = LegalMCPService()

# Create app
app = FastAPI(
    title="Legal MCP Service",
    description="Hybrid Legal MCP Service - Standard MCP Tools + HTTP REST APIs",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MCP Protocol Endpoints =====

@app.get("/mcp/tools")
async def list_mcp_tools():
    """List available MCP tools"""
    return {"tools": legal_mcp.mcp_tools}

@app.post("/mcp/call_tool")
async def call_mcp_tool(tool_call: MCPToolCall):
    """Execute MCP tool call"""
    tool_name = tool_call.name
    arguments = tool_call.arguments
    
    try:
        if tool_name == "search_documents":
            result = await legal_mcp.search_documents_tool(arguments)
        elif tool_name == "delete_document":
            result = await legal_mcp.delete_document_tool(arguments)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

# ===== HTTP REST API Endpoints =====

@app.post("/api/v1/search")
async def search_documents(
    request: Union[SemanticSearchRequest, SimilaritySearchRequest]
):
    """HTTP API: Search legal documents"""
    try:
        arguments = request.dict()
        result = await legal_mcp.search_documents_tool(arguments)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/api/v1/bulk_retrieve")
async def bulk_retrieve(request: BulkRetrieveRequest):
    """HTTP API: Bulk retrieve documents"""
    try:
        # Build filters
        where_filter = {}
        if request.jurisdictions:
            where_filter["region"] = {"$in": request.jurisdictions}
        
        # Get documents
        if request.include_content:
            results = legal_mcp.collection.get(
                where=where_filter if where_filter else None,
                include=['documents', 'metadatas']
            )
        else:
            results = legal_mcp.collection.get(
                where=where_filter if where_filter else None,
                include=['metadatas']
            )
        
        # Format response
        documents = []
        for i, metadata in enumerate(results.get('metadatas', [])):
            if len(documents) >= request.limit:
                break
                
            doc_data = {
                "document_id": f"{metadata.get('region', 'unknown')}_{metadata.get('law_id', 'unknown')}",
                "jurisdiction": metadata.get('region', 'Unknown'),
                "statute": metadata.get('statute', 'Unknown'),
                "law_id": metadata.get('law_id', 'Unknown'),
                "metadata": metadata
            }
            
            if request.include_content and results.get('documents'):
                doc_data["content"] = results['documents'][i]
            
            documents.append(doc_data)
        
        return {
            "documents": documents,
            "total_retrieved": len(documents),
            "total_available": len(results.get('metadatas', [])),
            "jurisdictions_included": list(set([doc["jurisdiction"] for doc in documents]))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk retrieval failed: {str(e)}")

@app.post("/api/v1/upload")
async def upload_document(
    document: UploadFile = File(...),
    jurisdiction: Optional[str] = Form(None)
):
    """HTTP API: Upload legal document (placeholder)"""
    return {
        "message": "Document upload endpoint - Implementation pending",
        "filename": document.filename,
        "jurisdiction": jurisdiction,
        "status": "accepted"
    }

@app.get("/health")
async def health_check():
    """HTTP API: Health check"""
    try:
        collection_count = legal_mcp.collection.count() if legal_mcp.collection else 0
        
        return {
            "status": "healthy",
            "service": "Legal MCP Service",
            "port": 8010,
            "chromadb_status": "connected" if legal_mcp.collection else "disconnected",
            "documents_count": collection_count,
            "available_tools": [tool["name"] for tool in legal_mcp.mcp_tools],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# ===== Main =====

if __name__ == "__main__":
    print("🚀 Launching Legal MCP Service on port 8010...")
    uvicorn.run(
        "mcp_service:app",
        host="0.0.0.0",
        port=8010,
        reload=True,
        log_level="info"
    )