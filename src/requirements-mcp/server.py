#!/usr/bin/env python3
"""
Requirements MCP Mock Server
Minimal implementation for testing agent MCP integration
"""

import asyncio
from typing import Dict, List, Any, Optional
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import uvicorn
import threading
import time

# Mock requirements documents database (hardcoded)
MOCK_REQUIREMENTS = {
    "req_001": {
        "chunk_id": "req_001",
        "content": "Live shopping feature must include payment processing, age verification for purchases, and real-time inventory management.",
        "source_document": "E-commerce Integration Requirements v2.1",
        "relevance_score": 0.9,
        "document_type": "PRD",
        "metadata": {
            "version": "2.1",
            "team": "Commerce Platform",
            "last_updated": "2025-01-15T10:00:00Z",
            "document_id": "req_doc_12345"
        }
    },
    "req_002": {
        "chunk_id": "req_002",
        "content": "User data must be retained for maximum 180 days with automatic deletion and user consent required for all data collection.",
        "source_document": "Data Privacy Requirements Specification",
        "relevance_score": 0.95,
        "document_type": "technical",
        "metadata": {
            "version": "1.3",
            "team": "Privacy Team",
            "last_updated": "2025-01-10T10:00:00Z",
            "document_id": "req_doc_67890"
        }
    },
    "req_003": {
        "chunk_id": "req_003",
        "content": "Content moderation system must respond to reports within 48 hours and provide appeal mechanisms for users.",
        "source_document": "Content Safety Technical Spec",
        "relevance_score": 0.88,
        "document_type": "feature",
        "metadata": {
            "version": "2.0",
            "team": "Safety Team",
            "last_updated": "2025-01-12T10:00:00Z",
            "document_id": "req_doc_33333"
        }
    },
    "req_004": {
        "chunk_id": "req_004",
        "content": "Age verification must be implemented for users under 18 using government-issued ID verification and parental consent workflows.",
        "source_document": "User Safety Requirements",
        "relevance_score": 0.92,
        "document_type": "user_story",
        "metadata": {
            "version": "1.5",
            "team": "User Safety",
            "last_updated": "2025-01-08T10:00:00Z",
            "document_id": "req_doc_44444"
        }
    }
}

MOCK_DOCUMENTS = {
    "req_doc_12345": {
        "document_id": "req_doc_12345",
        "title": "E-commerce Integration Requirements",
        "document_type": "prd",
        "upload_date": "2025-01-15T10:00:00Z",
        "team": "Commerce Platform",
        "version": "2.1",
        "status": "processed",
        "chunks_count": 23
    },
    "req_doc_67890": {
        "document_id": "req_doc_67890",
        "title": "Live Shopping Platform Requirements",
        "document_type": "prd",
        "upload_date": "2025-01-20T10:00:00Z",
        "team": "Product Team",
        "version": "1.0",
        "status": "processed", 
        "chunks_count": 15
    },
    "req_doc_33333": {
        "document_id": "req_doc_33333",
        "title": "Content Safety Technical Spec",
        "document_type": "technical",
        "upload_date": "2025-01-12T10:00:00Z",
        "team": "Safety Team",
        "version": "2.0",
        "status": "processed",
        "chunks_count": 31
    }
}

EXTRACTED_REQUIREMENTS_SAMPLE = [
    {
        "requirement_id": "req_67890_001",
        "requirement_text": "Payment processing must support multiple currencies including USD, EUR, and local currencies",
        "requirement_type": "functional",
        "priority": "high",
        "chunk_source": "Section 3.2 - Payment Integration"
    },
    {
        "requirement_id": "req_67890_002",
        "requirement_text": "Age verification required for purchases under 18 years old",
        "requirement_type": "compliance",
        "priority": "critical",
        "chunk_source": "Section 4.1 - User Safety"
    },
    {
        "requirement_id": "req_67890_003",
        "requirement_text": "Real-time inventory synchronization with backend systems",
        "requirement_type": "technical",
        "priority": "medium",
        "chunk_source": "Section 5.3 - Inventory Management"
    }
]

BULK_REQUIREMENTS_SAMPLE = [
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
    },
    {
        "requirement_id": "req_003",
        "requirement_text": "Age verification required for users under 18",
        "document_title": "User Safety Requirements",
        "document_type": "feature",
        "requirement_type": "compliance",
        "priority": "critical",
        "team": "User Safety",
        "last_updated": "2025-01-08T10:00:00Z"
    }
]

# MCP Server instance
server = Server("requirements-mcp")

@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="search_requirements",
            description="Search requirements documents with multiple search types",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_type": {
                        "type": "string",
                        "enum": ["semantic", "metadata", "bulk_retrieve"],
                        "description": "Type of search: 'semantic' for query-based search, 'metadata' for document-specific search, 'bulk_retrieve' for all requirements"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query (required for semantic and metadata search)"
                    },
                    "document_id": {
                        "type": "string",
                        "description": "Document ID for metadata search (required if search_type='metadata')"
                    },
                    "doc_types": {
                        "type": "array",
                        "items": {"enum": ["prd", "technical", "feature", "user_story"]},
                        "description": "Optional document type filtering"
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 5,
                        "description": "Maximum number of results to return"
                    },
                    "extract_requirements": {
                        "type": "boolean",
                        "default": False,
                        "description": "Extract structured requirements from chunks (for metadata search)"
                    },
                    "include_content": {
                        "type": "boolean", 
                        "default": True,
                        "description": "Include full content vs just metadata (for bulk_retrieve)"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["structured", "raw"],
                        "default": "structured",
                        "description": "Return format for bulk retrieve"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 100,
                        "description": "Limit for bulk retrieve"
                    }
                },
                "required": ["search_type"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "search_requirements":
        search_type = arguments.get("search_type")
        max_results = arguments.get("max_results", 5)
        doc_types = arguments.get("doc_types", [])
        
        if search_type == "semantic":
            # Filter by doc types if provided
            results = []
            for req in MOCK_REQUIREMENTS.values():
                if not doc_types or req["document_type"] in doc_types:
                    results.append(req)
                if len(results) >= max_results:
                    break
            
            response = {
                "results": results,
                "total_results": len(results),
                "search_time": 0.2
            }
            
        elif search_type == "metadata":
            document_id = arguments.get("document_id")
            extract_requirements = arguments.get("extract_requirements", False)
            
            if extract_requirements:
                response = {
                    "document_id": document_id,
                    "document_title": "Live Shopping Platform Requirements",
                    "extracted_requirements": EXTRACTED_REQUIREMENTS_SAMPLE,
                    "total_requirements": len(EXTRACTED_REQUIREMENTS_SAMPLE),
                    "extraction_time": 1.2
                }
            else:
                # Return chunks from specific document
                doc_results = []
                for req in MOCK_REQUIREMENTS.values():
                    if req["metadata"]["document_id"] == document_id:
                        doc_results.append(req)
                
                response = {
                    "document_id": document_id,
                    "results": doc_results,
                    "total_results": len(doc_results),
                    "search_time": 0.3
                }
                
        elif search_type == "bulk_retrieve":
            limit = arguments.get("limit", 100)
            format_type = arguments.get("format", "structured")
            
            if format_type == "structured":
                response = {
                    "requirements": BULK_REQUIREMENTS_SAMPLE[:limit],
                    "total_requirements": len(BULK_REQUIREMENTS_SAMPLE),
                    "retrieval_time": 1.5
                }
            else:
                response = {
                    "documents": list(MOCK_REQUIREMENTS.values())[:limit],
                    "total_documents": len(MOCK_REQUIREMENTS),
                    "retrieval_time": 1.0
                }
        
        else:
            response = {"error": "Invalid search_type. Must be 'semantic', 'metadata', or 'bulk_retrieve'"}
        
        return [TextContent(type="text", text=str(response))]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

# HTTP REST API (FastAPI)
app = FastAPI(title="Requirements MCP HTTP API", version="1.0.0")

@app.post("/api/v1/search")
async def search_documents(request: Dict[str, Any]):
    """Search requirements documents"""
    query = request.get("query", "")
    doc_types = request.get("doc_types", [])
    max_results = request.get("max_results", 5)
    
    # Filter results
    results = []
    for req in MOCK_REQUIREMENTS.values():
        if not doc_types or req["document_type"] in doc_types:
            results.append(req)
        if len(results) >= max_results:
            break
    
    return JSONResponse({
        "results": results,
        "total_results": len(results),
        "search_time": 0.2
    })

@app.post("/api/v1/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process requirements document"""
    
    # Simple text extraction mock
    content = await file.read()
    
    return JSONResponse({
        "success": True,
        "document_id": f"req_doc_{int(time.time())}",
        "message": "Document uploaded and processed successfully",
        "processing_details": {
            "pages_processed": 15,
            "chunks_created": 23,
            "processing_time": 8.5
        }
    })

@app.post("/api/v1/search_by_metadata")
async def search_by_metadata(request: Dict[str, Any]):
    """Search within specific document using metadata"""
    document_id = request.get("document_id")
    extract_requirements = request.get("extract_requirements", True)
    
    return JSONResponse({
        "document_id": document_id,
        "document_title": "Live Shopping Platform Requirements",
        "extracted_requirements": EXTRACTED_REQUIREMENTS_SAMPLE,
        "total_requirements": len(EXTRACTED_REQUIREMENTS_SAMPLE),
        "extraction_time": 1.2
    })

@app.post("/api/v1/bulk_retrieve")
async def bulk_retrieve(request: Dict[str, Any]):
    """Retrieve all requirements for compliance checking"""
    
    return JSONResponse({
        "requirements": BULK_REQUIREMENTS_SAMPLE,
        "total_requirements": len(BULK_REQUIREMENTS_SAMPLE),
        "retrieval_time": 1.5
    })

@app.get("/api/v1/documents")
async def list_documents():
    """List uploaded documents with metadata"""
    
    return JSONResponse({
        "documents": list(MOCK_DOCUMENTS.values()),
        "total_documents": len(MOCK_DOCUMENTS)
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "requirements-mcp",
        "version": "1.0.0",
        "chroma_status": "connected",
        "document_count": len(MOCK_DOCUMENTS),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })

async def run_mcp_server():
    """Run MCP server via stdio"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

def run_http_server():
    """Run HTTP server on port 8011"""
    uvicorn.run(app, host="0.0.0.0", port=8011, log_level="info")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        # Run HTTP server only
        run_http_server()
    else:
        # Run MCP server via stdio
        asyncio.run(run_mcp_server())