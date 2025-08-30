#!/usr/bin/env python3
"""
Requirements MCP Server - Real Implementation with ChromaDB and PostgreSQL
Combines both MCP tool interface and HTTP API for lawyer agent integration
"""

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import io

# MCP imports
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio

# FastAPI imports
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Real MCP dependencies
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import psycopg2
import PyPDF2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Database Configuration ---
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/geolegal")

# Parse DATABASE_URL
if DATABASE_URL.startswith("postgresql://"):
    # Extract components from URL
    import urllib.parse
    parsed = urllib.parse.urlparse(DATABASE_URL)
    DB_HOST = parsed.hostname
    DB_PORT = parsed.port
    DB_NAME = parsed.path[1:]  # Remove leading slash
    DB_USER = parsed.username
    DB_PASSWORD = parsed.password
else:
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "geolegal")
    DB_USER = os.environ.get("DB_USER", "user")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

# --- ChromaDB Configuration ---
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))

# Load the sentence transformer model
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.warning(f"Failed to load sentence transformer model: {e}")
    model = None

# Initialize ChromaDB client with persistence
try:
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
except Exception as e:
    logger.warning(f"Failed to initialize ChromaDB client: {e}")
    client = None


def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


def get_or_create_collection():
    """Get or create the requirements collection"""
    try:
        if client is None:
            raise Exception("ChromaDB client not initialized")
        collection = client.get_or_create_collection(
            name="requirements_collection",
            metadata={"hnsw:space": "cosine"}
        )
        return collection
    except Exception as e:
        logger.error(f"ChromaDB collection error: {e}")
        raise HTTPException(status_code=500, detail="ChromaDB connection failed")

# Pydantic models for request/response
class SearchRequest(BaseModel):
    query: str
    max_results: int = 10

class SearchMatch(BaseModel):
    content: str
    source_document: str
    document_type: str
    relevance_score: float
    metadata: Dict[str, Any] = {}

class SearchResponse(BaseModel):
    results: List[SearchMatch]
    total_results: int
    search_time: float

class UploadResponse(BaseModel):
    document_id: str
    message: str
    processing_details: Optional[Dict[str, Any]] = None

# Helper functions
def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text content from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to extract text from PDF")

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    start = 0
    
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        
        if end == len(words):
            break
        start = end - overlap
    
    return chunks

# === MCP SERVER IMPLEMENTATION ===

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
        query = arguments.get("query", "")
        
        try:
            if search_type == "semantic":
                # Real semantic search using ChromaDB
                if not model or not client:
                    response = {
                        "error": "ChromaDB or embedding model not available",
                        "results": [],
                        "total_results": 0,
                        "search_time": 0.0
                    }
                else:
                    collection = get_or_create_collection()
                    query_embedding = model.encode([query]).tolist()
                    
                    results = collection.query(
                        query_embeddings=query_embedding,
                        n_results=max_results
                    )
                    
                    search_results = []
                    if results['documents'] and len(results['documents']) > 0:
                        for i in range(len(results['documents'][0])):
                            search_results.append({
                                "chunk_id": results['ids'][0][i],
                                "content": results['documents'][0][i],
                                "source_document": results['metadatas'][0][i].get('source_document', 'Unknown'),
                                "document_type": results['metadatas'][0][i].get('document_type', 'Unknown'),
                                "relevance_score": 1.0 - results['distances'][0][i],
                                "metadata": results['metadatas'][0][i]
                            })
                    
                    response = {
                        "results": search_results,
                        "total_results": len(search_results),
                        "search_time": 0.2
                    }
                
            elif search_type == "metadata":
                document_id = arguments.get("document_id")
                extract_requirements = arguments.get("extract_requirements", False)
                
                if extract_requirements:
                    # Extract structured requirements from document
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT pl.chunk_content, pl.chunk_index
                        FROM pdfs p
                        JOIN processing_log pl ON p.id = pl.pdf_id
                        WHERE p.id = %s
                        ORDER BY pl.chunk_index
                    """, (document_id,))
                    
                    extracted_requirements = []
                    for row in cursor.fetchall():
                        content, chunk_index = row
                        extracted_requirements.append({
                            "requirement_id": f"req_{document_id}_{chunk_index:03d}",
                            "requirement_text": content,
                            "requirement_type": "functional",
                            "priority": "medium",
                            "chunk_source": f"Chunk {chunk_index}"
                        })
                    
                    cursor.close()
                    conn.close()
                    
                    response = {
                        "document_id": document_id,
                        "extracted_requirements": extracted_requirements,
                        "total_requirements": len(extracted_requirements),
                        "extraction_time": 1.2
                    }
                else:
                    # Return chunks from specific document
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT pl.chunk_content, pl.chunk_index, pl.metadata, p.filename
                        FROM pdfs p
                        JOIN processing_log pl ON p.id = pl.pdf_id
                        WHERE p.id = %s
                        ORDER BY pl.chunk_index
                        LIMIT %s
                    """, (document_id, max_results))
                    
                    doc_results = []
                    for row in cursor.fetchall():
                        content, chunk_index, metadata, filename = row
                        doc_results.append({
                            "chunk_id": f"{document_id}_chunk_{chunk_index}",
                            "content": content,
                            "source_document": filename,
                            "document_type": "prd",
                            "relevance_score": 1.0,
                            "metadata": metadata or {}
                        })
                    
                    cursor.close()
                    conn.close()
                    
                    response = {
                        "document_id": document_id,
                        "results": doc_results,
                        "total_results": len(doc_results),
                        "search_time": 0.3
                    }
                    
            elif search_type == "bulk_retrieve":
                limit = arguments.get("limit", 100)
                format_type = arguments.get("format", "structured")
                
                conn = get_db_connection()
                cursor = conn.cursor()
                
                if format_type == "structured":
                    cursor.execute("""
                        SELECT p.filename, p.file_type, pl.chunk_content, pl.chunk_index, pl.metadata
                        FROM pdfs p
                        JOIN processing_log pl ON p.id = pl.pdf_id
                        WHERE p.processing_status = 'completed'
                        ORDER BY p.upload_date DESC, pl.chunk_index
                        LIMIT %s
                    """, (limit,))
                    
                    requirements = []
                    for row in cursor.fetchall():
                        filename, file_type, content, chunk_index, metadata = row
                        requirements.append({
                            "requirement_id": f"req_{hash(content) % 10000:04d}",
                            "requirement_text": content[:200] + "..." if len(content) > 200 else content,
                            "document_title": filename,
                            "document_type": file_type,
                            "requirement_type": "functional",
                            "priority": "medium",
                            "chunk_index": chunk_index,
                            "metadata": metadata or {}
                        })
                    
                    response = {
                        "requirements": requirements,
                        "total_requirements": len(requirements),
                        "retrieval_time": 1.5
                    }
                else:
                    cursor.execute("""
                        SELECT p.id, p.filename, p.file_type, p.upload_date, p.processing_status
                        FROM pdfs p
                        WHERE p.processing_status = 'completed'
                        ORDER BY p.upload_date DESC
                        LIMIT %s
                    """, (limit,))
                    
                    documents = []
                    for row in cursor.fetchall():
                        doc_id, filename, file_type, upload_date, status = row
                        documents.append({
                            "document_id": doc_id,
                            "filename": filename,
                            "document_type": file_type,
                            "upload_date": upload_date.isoformat(),
                            "processing_status": status
                        })
                    
                    response = {
                        "documents": documents,
                        "total_documents": len(documents),
                        "retrieval_time": 1.0
                    }
                
                cursor.close()
                conn.close()
            
            else:
                response = {"error": "Invalid search_type. Must be 'semantic', 'metadata', or 'bulk_retrieve'"}
        
        except Exception as e:
            logger.error(f"MCP search failed: {str(e)}")
            response = {"error": f"Search failed: {str(e)}"}
        
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

# === HTTP API IMPLEMENTATION ===

# FastAPI app
app = FastAPI(
    title="Requirements MCP Server",
    description="Requirements document search and management for lawyer agent workflows",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint with full system status"""
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        db_status = "connected"
        
        # Get document count
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pdfs")
        doc_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
        doc_count = 0
    
    try:
        # Test ChromaDB connection
        collection = get_or_create_collection()
        chroma_count = collection.count()
        chroma_status = "connected"
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {e}")
        chroma_status = "disconnected"
        chroma_count = 0
    
    return {
        "status": "healthy" if db_status == "connected" and chroma_status == "connected" else "degraded",
        "service": "requirements-mcp",
        "version": "1.0.0",
        "database_status": db_status,
        "chroma_status": chroma_status,
        "document_count": doc_count,
        "chroma_chunks": chroma_count,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Semantic search across requirements documents"""
    start_time = time.time()
    
    try:
        # Get ChromaDB collection
        collection = get_or_create_collection()
        
        # Generate query embedding
        query_embedding = model.encode([request.query]).tolist()
        
        # Search in ChromaDB
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=request.max_results
        )
        
        # Format results
        search_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                result = SearchMatch(
                    content=results['documents'][0][i],
                    source_document=results['metadatas'][0][i].get('source_document', 'Unknown'),
                    document_type=results['metadatas'][0][i].get('document_type', 'Unknown'),
                    relevance_score=1.0 - results['distances'][0][i],  # Convert distance to similarity
                    metadata={
                        "chunk_id": results['ids'][0][i],
                        "pdf_id": results['metadatas'][0][i].get('pdf_id'),
                        "chunk_index": results['metadatas'][0][i].get('chunk_index'),
                        **results['metadatas'][0][i]
                    }
                )
                search_results.append(result)
        
        search_time = time.time() - start_time
        
        return SearchResponse(
            results=search_results,
            total_results=len(search_results),
            search_time=search_time
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/api/v1/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...), 
    document_type: str = Form(default="prd")
):
    """Upload and process a requirements document"""
    start_time = time.time()
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Extract text based on file type
        if file.filename.lower().endswith('.pdf'):
            text_content = extract_text_from_pdf(file_content)
        else:
            # Assume text file
            text_content = file_content.decode('utf-8')
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Insert into PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO pdfs (id, filename, file_type, upload_date, processing_status, content, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            document_id,
            file.filename,
            document_type,
            datetime.now(),
            'processing',
            text_content,
            json.dumps({
                "original_filename": file.filename,
                "file_size": len(file_content),
                "content_type": file.content_type
            })
        ))
        
        pdf_id = cursor.fetchone()[0]
        
        # Chunk the text
        chunks = chunk_text(text_content)
        
        # Get ChromaDB collection
        collection = get_or_create_collection()
        
        # Process and store chunks
        chunk_ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            documents.append(chunk)
            
            # Generate embedding
            embedding = model.encode([chunk])[0].tolist()
            embeddings.append(embedding)
            
            # Metadata
            metadata = {
                "source_document": file.filename,
                "document_type": document_type,
                "pdf_id": pdf_id,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            metadatas.append(metadata)
            
            # Insert chunk info into processing_log
            cursor.execute("""
                INSERT INTO processing_log (pdf_id, chunk_index, chunk_content, embedding_model, processing_timestamp, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                pdf_id,
                i,
                chunk,
                'all-MiniLM-L6-v2',
                datetime.now(),
                json.dumps(metadata)
            ))
        
        # Add all chunks to ChromaDB at once
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=chunk_ids
        )
        
        # Update processing status
        cursor.execute("""
            UPDATE pdfs SET processing_status = 'completed', processing_details = %s
            WHERE id = %s
        """, (
            json.dumps({
                "chunks_created": len(chunks),
                "processing_time": time.time() - start_time,
                "model_used": "all-MiniLM-L6-v2"
            }),
            pdf_id
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        processing_time = time.time() - start_time
        
        return UploadResponse(
            document_id=document_id,
            message="Document uploaded and processed successfully",
            processing_details={
                "pages_processed": len(chunks),  # Using chunks as proxy for pages
                "chunks_created": len(chunks),
                "processing_time": processing_time
            }
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        # Clean up on failure
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pdfs WHERE id = %s", (document_id,))
            cursor.execute("DELETE FROM processing_log WHERE pdf_id = %s", (document_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/v1/documents")
async def list_documents():
    """List all uploaded documents with metadata"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, filename, file_type, upload_date, processing_status, 
                   processing_details, metadata
            FROM pdfs 
            ORDER BY upload_date DESC
        """)
        
        documents = []
        for row in cursor.fetchall():
            doc_id, filename, file_type, upload_date, status, details, metadata = row
            
            # Get chunk count
            cursor.execute("SELECT COUNT(*) FROM processing_log WHERE pdf_id = %s", (doc_id,))
            chunk_count = cursor.fetchone()[0]
            
            documents.append({
                "document_id": doc_id,
                "filename": filename,
                "file_type": file_type,
                "upload_date": upload_date.isoformat(),
                "processing_status": status,
                "chunk_count": chunk_count,
                "processing_details": details,
                "metadata": metadata
            })
        
        cursor.close()
        conn.close()
        
        return {
            "documents": documents,
            "total_documents": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.delete("/api/v1/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get document info first
        cursor.execute("SELECT filename FROM pdfs WHERE id = %s", (document_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Document not found")
        
        filename = result[0]
        
        # Delete from ChromaDB first
        collection = get_or_create_collection()
        
        # Find all chunks for this document
        chroma_results = collection.get(
            where={"source_document": filename}
        )
        
        if chroma_results["ids"]:
            collection.delete(ids=chroma_results["ids"])
            logger.info(f"Deleted {len(chroma_results['ids'])} chunks from ChromaDB")
        
        # Delete from PostgreSQL
        cursor.execute("DELETE FROM processing_log WHERE pdf_id = %s", (document_id,))
        cursor.execute("DELETE FROM pdfs WHERE id = %s", (document_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Document {filename} deleted successfully",
            "document_id": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

# Legacy endpoints for backward compatibility
@app.post("/api/v1/bulk_retrieve")
async def bulk_retrieve(request: Dict[str, Any]):
    """Retrieve all requirements for compliance checking (legacy endpoint)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.filename, p.file_type, pl.chunk_content, pl.chunk_index, pl.metadata
            FROM pdfs p
            JOIN processing_log pl ON p.id = pl.pdf_id
            WHERE p.processing_status = 'completed'
            ORDER BY p.upload_date DESC, pl.chunk_index
        """)
        
        requirements = []
        for row in cursor.fetchall():
            filename, file_type, content, chunk_index, metadata = row
            requirements.append({
                "requirement_id": f"req_{hash(content) % 10000:04d}",
                "requirement_text": content[:200] + "..." if len(content) > 200 else content,
                "document_title": filename,
                "document_type": file_type,
                "requirement_type": "functional",
                "priority": "medium",
                "chunk_index": chunk_index,
                "metadata": metadata
            })
        
        cursor.close()
        conn.close()
        
        return {
            "requirements": requirements,
            "total_requirements": len(requirements),
            "retrieval_time": 0.5
        }
        
    except Exception as e:
        logger.error(f"Bulk retrieve failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk retrieve failed: {str(e)}")

@app.post("/api/v1/search_by_metadata")
async def search_by_metadata(request: Dict[str, Any]):
    """Search within specific document using metadata (legacy endpoint)"""
    document_id = request.get("document_id")
    extract_requirements = request.get("extract_requirements", True)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if extract_requirements:
            cursor.execute("""
                SELECT pl.chunk_content, pl.chunk_index
                FROM pdfs p
                JOIN processing_log pl ON p.id = pl.pdf_id
                WHERE p.id = %s
                ORDER BY pl.chunk_index
            """, (document_id,))
            
            extracted_requirements = []
            for row in cursor.fetchall():
                content, chunk_index = row
                extracted_requirements.append({
                    "requirement_id": f"req_{document_id}_{chunk_index:03d}",
                    "requirement_text": content,
                    "requirement_type": "functional",
                    "priority": "medium",
                    "chunk_source": f"Chunk {chunk_index}"
                })
            
            response = {
                "document_id": document_id,
                "document_title": "Requirements Document",
                "extracted_requirements": extracted_requirements,
                "total_requirements": len(extracted_requirements),
                "extraction_time": 1.2
            }
        else:
            # Return document metadata only
            cursor.execute("""
                SELECT filename, file_type, upload_date
                FROM pdfs
                WHERE id = %s
            """, (document_id,))
            
            result = cursor.fetchone()
            if result:
                filename, file_type, upload_date = result
                response = {
                    "document_id": document_id,
                    "document_title": filename,
                    "document_type": file_type,
                    "upload_date": upload_date.isoformat(),
                    "extraction_time": 0.1
                }
            else:
                response = {
                    "error": "Document not found",
                    "document_id": document_id
                }
        
        cursor.close()
        conn.close()
        
        return JSONResponse(response)
        
    except Exception as e:
        logger.error(f"Metadata search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metadata search failed: {str(e)}")

# === SERVER RUNNERS ===

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