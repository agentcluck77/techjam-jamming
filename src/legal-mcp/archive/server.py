#!/usr/bin/env python3
"""
Legal MCP Mock Server
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

# Mock legal documents database (hardcoded)
MOCK_LEGAL_DOCS = {
    "utah_001": {
        "chunk_id": "utah_001",
        "content": "Utah Social Media Regulation Act requires age verification for users under 18 and content moderation response within 24 hours.",
        "source_document": "Utah Social Media Act Section 13-2a-3",
        "relevance_score": 0.95,
        "jurisdiction": "Utah"
    },
    "california_001": {
        "chunk_id": "california_001", 
        "content": "California Consumer Privacy Act mandates data retention limits of 180 days and user consent for data collection.",
        "source_document": "CCPA Amendment 2024 Section 1798.100",
        "relevance_score": 0.88,
        "jurisdiction": "California"
    },
    "eu_001": {
        "chunk_id": "eu_001",
        "content": "EU Digital Services Act establishes content moderation requirements and platform liability for harmful content.",
        "source_document": "EU Digital Services Act 2024",
        "relevance_score": 0.92,
        "jurisdiction": "EU"
    },
    "florida_001": {
        "chunk_id": "florida_001",
        "content": "Florida Online Safety Act requires parental consent for minors and content filtering mechanisms.",
        "source_document": "Florida Online Safety Act Section 501.2041",
        "relevance_score": 0.87,
        "jurisdiction": "Florida"
    },
    "brazil_001": {
        "chunk_id": "brazil_001",
        "content": "Brazilian Internet Framework requires local data storage and content takedown procedures within 48 hours.",
        "source_document": "Marco Civil da Internet Article 19",
        "relevance_score": 0.85,
        "jurisdiction": "Brazil"
    }
}

SIMILAR_DOCS = {
    "legal_doc_456": {
        "document_id": "legal_doc_456",
        "title": "EU Digital Services Act 2024",
        "similarity_score": 0.92,
        "preview": "EU Digital Services Act establishes content moderation requirements and platform liability...",
        "jurisdiction": "EU"
    },
    "legal_doc_789": {
        "document_id": "legal_doc_789", 
        "title": "California Content Safety Regulations",
        "similarity_score": 0.88,
        "preview": "California requires social media platforms to implement age verification...",
        "jurisdiction": "California"
    }
}

# MCP Server instance
server = Server("legal-mcp")

@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="search_documents",
            description="Unified search for legal documents - supports both semantic search and similarity detection",
            inputSchema={
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
        ),
        Tool(
            name="delete_document",
            description="Delete a legal document (for removing past iterations)",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "ID of document to delete"
                    },
                    "confirm_deletion": {
                        "type": "boolean",
                        "default": True,
                        "description": "Confirmation flag for deletion"
                    }
                },
                "required": ["document_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "search_documents":
        search_type = arguments.get("search_type")
        max_results = arguments.get("max_results", 10)
        jurisdictions = arguments.get("jurisdictions", [])
        
        if search_type == "semantic":
            # Filter by jurisdictions if provided
            results = []
            for doc in MOCK_LEGAL_DOCS.values():
                if not jurisdictions or doc["jurisdiction"] in jurisdictions:
                    results.append(doc)
                if len(results) >= max_results:
                    break
            
            response = {
                "search_type": "semantic",
                "results": results,
                "total_results": len(results),
                "search_time": 0.8
            }
            
        elif search_type == "similarity":
            threshold = arguments.get("similarity_threshold", 0.8)
            
            # Return similar documents above threshold
            similar_results = []
            for doc in SIMILAR_DOCS.values():
                if doc["similarity_score"] >= threshold:
                    similar_results.append(doc)
                if len(similar_results) >= max_results:
                    break
            
            response = {
                "search_type": "similarity",
                "similar_documents": similar_results,
                "total_found": len(similar_results),
                "search_time": 0.5
            }
        
        else:
            response = {"error": "Invalid search_type. Must be 'semantic' or 'similarity'"}
        
        return [TextContent(type="text", text=str(response))]
    
    elif name == "delete_document":
        document_id = arguments.get("document_id")
        confirm = arguments.get("confirm_deletion", True)
        
        if confirm:
            response = {
                "success": True,
                "document_id": document_id,
                "message": "Document successfully deleted from ChromaDB"
            }
        else:
            response = {
                "success": False,
                "document_id": document_id,
                "message": "Deletion cancelled - confirmation required"
            }
        
        return [TextContent(type="text", text=str(response))]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

# HTTP REST API (FastAPI)
app = FastAPI(title="Legal MCP HTTP API", version="1.0.0")

@app.post("/api/v1/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload legal document (mock implementation)"""
    
    # Simple text extraction mock
    content = await file.read()
    extracted_text = f"Extracted text from {file.filename}: Mock legal document content about regulations and compliance requirements."
    
    return JSONResponse({
        "success": True,
        "document_id": f"legal_doc_{int(time.time())}",
        "message": "Document uploaded and processed successfully",
        "extracted_text": extracted_text,
        "processing_details": {
            "file_size": len(content),
            "pages_processed": 5,
            "chunks_created": 8,
            "processing_time": 2.1
        }
    })

@app.post("/api/v1/search")
async def search_documents(request: Dict[str, Any]):
    """Search legal documents (semantic/similarity search)"""
    
    search_type = request.get("search_type", "semantic")
    query = request.get("query", "")
    max_results = request.get("max_results", 10)
    
    if search_type == "semantic":
        # Simple keyword matching for mock implementation
        results = []
        query_lower = query.lower()
        
        for doc in MOCK_LEGAL_DOCS.values():
            content_lower = doc["content"].lower()
            if any(keyword in content_lower for keyword in query_lower.split()):
                results.append(doc)
        
        # Sort by relevance and limit results
        results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:max_results]
        
        return JSONResponse({
            "search_type": "semantic",
            "results": results,
            "total_results": len(results),
            "search_time": 0.5
        })
        
    elif search_type == "similarity":
        document_content = request.get("document_content", "")
        similarity_threshold = request.get("similarity_threshold", 0.8)
        
        # Mock similarity search - return Utah docs if "utah" mentioned
        similar_results = []
        if "utah" in document_content.lower():
            for doc in MOCK_LEGAL_DOCS.values():
                if doc["jurisdiction"] == "Utah":
                    similar_results.append({
                        "document_id": doc["chunk_id"],
                        "title": doc["source_document"],
                        "similarity_score": 0.85,
                        "content_preview": doc["content"][:200] + "...",
                        "jurisdiction": doc["jurisdiction"]
                    })
        
        return JSONResponse({
            "search_type": "similarity",
            "similar_documents": similar_results,
            "total_found": len(similar_results),
            "search_time": 1.2
        })
    
    else:
        return JSONResponse({
            "error": f"Unknown search type: {search_type}"
        }, status_code=400)

@app.post("/api/v1/bulk_retrieve")
async def bulk_retrieve(request: Dict[str, Any]):
    """Retrieve all legal documents for compliance checking"""
    
    # Return all mock documents
    documents = list(MOCK_LEGAL_DOCS.values())
    
    return JSONResponse({
        "documents": documents,
        "total_documents": len(documents),
        "retrieval_time": 0.3
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "legal-mcp",
        "version": "1.0.0",
        "chroma_status": "connected",
        "document_count": len(MOCK_LEGAL_DOCS),
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
    """Run HTTP server on port 8010"""
    uvicorn.run(app, host="0.0.0.0", port=8010, log_level="info")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        # Run HTTP server only
        run_http_server()
    else:
        # Run MCP server via stdio
        asyncio.run(run_mcp_server())