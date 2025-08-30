#!/usr/bin/env python3
"""
Legal MCP Server - Real Implementation with PostgreSQL and pgvector
Combines both MCP tool interface and HTTP API for lawyer agent integration
Provides semantic search for legal documents using PostgreSQL vector search
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

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

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
import asyncpg
from sentence_transformers import SentenceTransformer
import numpy as np

# Local imports - adjust path to your existing helpers
import sys
import os

# Add the legal-mcp source to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src2_path = os.path.join(current_dir, 'src2')
sys.path.insert(0, src2_path)

from helpers.db.common_queries import CommonQueries, Definitions, Regulations
from helpers.lawer_agent.get_regulation import get_region_regulation_details
from helpers.lawer_agent.get_definition import get_definition

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PDF processing import - optional for testing
try:
    from helpers.db.upsert_law_pdf import upsert_law_pdf_by_name
    PDF_PROCESSING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PDF processing not available: {e}")
    PDF_PROCESSING_AVAILABLE = False
    def upsert_law_pdf_by_name(*args, **kwargs):
        raise HTTPException(status_code=501, detail="PDF processing not available - missing dependencies")

# --- Database Configuration ---
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

# Load the sentence transformer model for embeddings
try:
    import os
    # Create cache directory if it doesn't exist
    cache_dir = os.path.join(os.getcwd(), '.sentence_transformers_cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=cache_dir)
    logger.info("Sentence transformer model loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load sentence transformer model: {e}")
    model = None

# Global database pool
db_pool = None

async def process_pdf_universal(pdf_path: str, region: str, statute: str, filename: str):
    """
    Simplified PDF processing that uses universal table and random chunking
    """
    import PyPDF2
    import random
    
    # Extract text from PDF
    text_content = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"
    
    # Simple random chunking - split into sentences and randomly group them
    sentences = text_content.replace('\n', ' ').split('. ')
    sentences = [s.strip() + '.' for s in sentences if len(s.strip()) > 10]
    
    # Create smaller, more precise chunks for legal document search
    chunks = []
    i = 0
    while i < len(sentences):
        chunk_size = random.randint(1, 3)  # Smaller chunks: 1-3 sentences
        chunk_sentences = sentences[i:i+chunk_size]
        if chunk_sentences:
            chunks.append(' '.join(chunk_sentences))
        i += chunk_size
    
    # Process more chunks for better legal document granularity
    for chunk_idx, chunk_text in enumerate(chunks[:15]):  # Increased to 15 chunks
        if len(chunk_text) < 100:  # Skip chunks under 100 characters
            continue
            
        # Generate embedding
        if model:
            embedding = model.encode(chunk_text)
            # Convert numpy array to vector format for PostgreSQL
            embedding_vector = f"[{','.join(map(str, embedding))}]"
        else:
            embedding_vector = None
        
        # Insert into universal table
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO techjam.legal_documents 
                    (region, statute, document_type, law_id, content, file_location, embedding)
                    VALUES ($1, $2, $3, $4, $5, $6, $7::vector)
                """, region, statute, "chunk", f"chunk_{chunk_idx}", chunk_text, pdf_path, embedding_vector)
    
    logger.info(f"Processed {len(chunks[:5])} chunks from {filename}")

async def init_db_pool():
    """Initialize the database connection pool"""
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            min_size=1,
            max_size=10
        )
        logger.info("Database connection pool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise

async def close_db_pool():
    """Close the database connection pool"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")

# --- Pydantic Models ---
class DocumentSearchRequest(BaseModel):
    search_type: str = "semantic"  # semantic, similarity, text
    query: str = ""
    document_content: Optional[str] = None
    jurisdictions: Optional[List[str]] = None
    max_results: int = 10

class UploadRequest(BaseModel):
    region: str
    statute: str
    pdf_file_name: str

# --- Vector Search Functions ---
async def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding for text using sentence transformer"""
    if model is None:
        return None
    try:
        embedding = model.encode([text])[0].tolist()
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None

async def semantic_search_documents(query: str, jurisdictions: List[str] = None, max_results: int = 10) -> Dict[str, Any]:
    """
    Universal table semantic search - FAST and SIMPLE
    """
    if not model or not db_pool:
        return {"documents": [], "total_documents": 0, "retrieval_time": 0.0}
    
    start_time = time.time()
    
    try:
        # Generate query embedding and convert to PostgreSQL vector format
        query_embedding_array = model.encode(query)
        query_embedding_str = f"[{','.join(map(str, query_embedding_array))}]"
        
        # Build search query
        base_query = """
            SELECT region, statute, law_id, content, file_location,
                   embedding <=> $1::vector as similarity
            FROM techjam.legal_documents
            WHERE embedding IS NOT NULL
        """
        params = [query_embedding_str]
        
        if jurisdictions:
            base_query += " AND region = ANY($2)"
            params.append(jurisdictions)
            
        base_query += " ORDER BY similarity LIMIT $" + str(len(params) + 1)
        params.append(max_results)
        
        async with db_pool.acquire() as conn:
            results = await conn.fetch(base_query, *params)
            
        documents = [
            {
                "jurisdiction": row["region"],
                "region": row["region"],
                "statute": row["statute"], 
                "law_id": row["law_id"],
                "content": row["content"][:500] + "..." if len(row["content"]) > 500 else row["content"],
                "file_location": row["file_location"],
                "similarity_score": 1.0 - float(row["similarity"])  # Convert distance to similarity
            }
            for row in results
        ]
        
        retrieval_time = time.time() - start_time
        return {
            "documents": documents,
            "total_documents": len(documents),
            "retrieval_time": retrieval_time
        }
        
    except Exception as e:
        logger.warning(f"Vector search failed, falling back to text search: {e}")
        return await text_search_documents(query, jurisdictions, max_results)

async def text_search_documents(query: str, jurisdictions: List[str] = None, max_results: int = 10) -> Dict[str, Any]:
    """
    Universal table text search - FAST and SIMPLE
    """
    if not db_pool:
        return {"documents": [], "total_documents": 0, "retrieval_time": 0.0}
    
    start_time = time.time()
    
    try:
        base_query = """
            SELECT region, statute, law_id, content, file_location
            FROM techjam.legal_documents
            WHERE content ILIKE $1
        """
        params = [f"%{query}%"]
        
        if jurisdictions:
            base_query += " AND region = ANY($2)"
            params.append(jurisdictions)
            
        base_query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
        params.append(max_results)
        
        async with db_pool.acquire() as conn:
            results = await conn.fetch(base_query, *params)
            
        documents = [
            {
                "jurisdiction": row["region"], 
                "region": row["region"],
                "statute": row["statute"],
                "law_id": row["law_id"],
                "content": row["content"][:500] + "..." if len(row["content"]) > 500 else row["content"],
                "file_location": row["file_location"],
                "similarity_score": 0.7  # Default for text search
            }
            for row in results
        ]
        
        retrieval_time = time.time() - start_time
        return {
            "documents": documents,
            "total_documents": len(documents),
            "retrieval_time": retrieval_time
        }
        
    except Exception as e:
        logger.error(f"Text search failed: {e}")
        return {"documents": [], "total_documents": 0, "retrieval_time": time.time() - start_time}

async def similarity_search_documents(document_content: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Universal table similarity search - FAST and SIMPLE
    """
    if not model or not db_pool:
        return {"similar_documents": [], "total_found": 0, "search_time": 0.0}
    
    start_time = time.time()
    
    try:
        # Generate document embedding and convert to PostgreSQL vector format
        doc_embedding_array = model.encode(document_content)
        doc_embedding_str = f"[{','.join(map(str, doc_embedding_array))}]"
        
        async with db_pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT region, statute, law_id, content, file_location,
                       embedding <=> $1::vector as similarity
                FROM techjam.legal_documents  
                WHERE embedding IS NOT NULL
                ORDER BY similarity
                LIMIT $2
            """, doc_embedding_str, max_results)
            
        documents = [
            {
                "region": row["region"],
                "statute": row["statute"],
                "law_id": row["law_id"], 
                "content": row["content"][:500] + "..." if len(row["content"]) > 500 else row["content"],
                "file_location": row["file_location"],
                "similarity_score": 1.0 - float(row["similarity"])  # Convert distance to similarity
            }
            for row in results
        ]
        
        search_time = time.time() - start_time
        return {
            "similar_documents": documents,
            "total_found": len(documents),
            "search_time": search_time
        }
        
    except Exception as e:
        logger.error(f"Similarity search failed: {e}")
        return {"similar_documents": [], "total_found": 0, "search_time": time.time() - start_time}

# --- MCP Server Setup ---
server = Server("legal-mcp")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="search_documents",
            description="Search legal documents across all jurisdictions with jurisdiction filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_type": {
                        "type": "string",
                        "description": "Type of search: 'semantic' for AI-powered search, 'similarity' for document matching, 'text' for keyword search",
                        "enum": ["semantic", "similarity", "text"]
                    },
                    "query": {
                        "type": "string", 
                        "description": "Search query or keywords"
                    },
                    "document_content": {
                        "type": "string",
                        "description": "Document content for similarity search (optional)"
                    },
                    "jurisdictions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of jurisdictions to search (e.g. ['EU', 'Utah', 'California']). If not provided, searches all jurisdictions."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="delete_document",
            description="Delete legal document for past iteration removal",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "ID of the document to delete"
                    },
                    "confirm_deletion": {
                        "type": "boolean",
                        "description": "Confirm deletion (must be true)",
                        "default": False
                    }
                },
                "required": ["document_id", "confirm_deletion"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle MCP tool calls"""
    try:
        if name == "search_documents":
            search_type = arguments.get("search_type", "semantic")
            query = arguments.get("query", "")
            document_content = arguments.get("document_content")
            jurisdictions = arguments.get("jurisdictions")
            max_results = arguments.get("max_results", 10)
            
            if search_type == "semantic":
                result = await semantic_search_documents(query, jurisdictions, max_results)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif search_type == "similarity":
                if not document_content:
                    return [TextContent(type="text", text=json.dumps({"error": "document_content required for similarity search"}))]
                result = await similarity_search_documents(document_content, max_results)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif search_type == "text":
                result = await text_search_documents(query, jurisdictions, max_results)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            else:
                return [TextContent(type="text", text=json.dumps({"error": f"Invalid search_type: {search_type}"}))]
        
        elif name == "delete_document":
            document_id = arguments.get("document_id")
            confirm = arguments.get("confirm_deletion", False)
            
            if not confirm:
                return [TextContent(type="text", text=json.dumps({"error": "confirm_deletion must be true"}))]
            
            # For now, return a mock deletion response
            # TODO: Implement actual document deletion logic
            result = {
                "success": True,
                "document_id": document_id,
                "message": f"Document {document_id} marked for deletion (simulation)"
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
            
    except Exception as e:
        logger.error(f"Tool call failed for {name}: {e}")
        return [TextContent(type="text", text=json.dumps({"error": f"Tool execution failed: {str(e)}"}))]

# --- FastAPI Application ---
app = FastAPI(
    title="Legal MCP Server",
    description="Real Legal MCP implementation with PostgreSQL + pgvector semantic search",
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

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await init_db_pool()
        logger.info("Legal MCP Server started successfully with database")
    except Exception as e:
        logger.warning(f"Legal MCP Server started WITHOUT database connection: {e}")
        logger.info("Running in database-free mode - MCP tools will return mock data")

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_db_pool()
    logger.info("Legal MCP Server shutdown complete")

# --- HTTP API Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status = "healthy"
        else:
            db_status = "unhealthy"
        
        return {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "database": db_status,
            "embedding_model": "available" if model else "unavailable",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.post("/api/v1/upload")
async def upload_document(
    region: str = Form(...),
    statute: str = Form(...),
    pdf_file_name: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload and process a legal PDF document
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file temporarily
        temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process the PDF using simplified universal table approach
        try:
            await process_pdf_universal(temp_path, region, statute, file.filename)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return {
                "success": True,
                "message": f"Document {file.filename} processed successfully for {region}/{statute}",
                "region": region,
                "statute": statute,
                "filename": file.filename
            }
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/v1/search")
async def search_documents_endpoint(request: DocumentSearchRequest):
    """
    Search legal documents via HTTP API
    """
    try:
        if request.search_type == "semantic":
            result = await semantic_search_documents(
                request.query, 
                request.jurisdictions, 
                request.max_results
            )
        elif request.search_type == "similarity":
            if not request.document_content:
                raise HTTPException(status_code=400, detail="document_content required for similarity search")
            result = await similarity_search_documents(
                request.document_content,
                request.max_results
            )
        elif request.search_type == "text":
            result = await text_search_documents(
                request.query,
                request.jurisdictions, 
                request.max_results
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid search_type: {request.search_type}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/v1/regions")
async def get_available_regions():
    """
    Get list of available legal jurisdictions/regions
    """
    try:
        if not db_pool:
            return {"regions": []}
        
        async with db_pool.acquire() as conn:
            regions_result = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'techjam' 
                AND table_name LIKE 't_law_%_regulations'
            """)
            regions = [table['table_name'].replace('t_law_', '').replace('_regulations', '').upper() 
                      for table in regions_result]
        
        return {"regions": regions}
        
    except Exception as e:
        logger.error(f"Failed to get regions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get regions: {str(e)}")

@app.get("/api/v1/documents/summary")
async def get_documents_summary():
    """
    Get summary of all legal documents with upload dates
    """
    try:
        if not db_pool:
            return []
        
        async with db_pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT 
                    region,
                    statute,
                    COUNT(*) as chunks,
                    MIN(created_at) as upload_date
                FROM techjam.legal_documents 
                GROUP BY region, statute 
                ORDER BY region, statute
            """)
            
            documents = []
            for row in results:
                documents.append({
                    "region": row["region"],
                    "statute": row["statute"],
                    "chunks": row["chunks"],
                    "uploadDate": row["upload_date"].isoformat() if row["upload_date"] else None
                })
            
            return documents
            
    except Exception as e:
        logger.error(f"Failed to get document summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document summary: {str(e)}")

@app.post("/api/v1/delete")
async def delete_document(request: dict):
    """
    Delete all chunks for a specific region/statute combination
    """
    try:
        region = request.get("region")
        statute = request.get("statute")
        
        if not region or not statute:
            raise HTTPException(status_code=400, detail="Both region and statute are required")
        
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        async with db_pool.acquire() as conn:
            # Delete all chunks for the specified region and statute
            result = await conn.execute("""
                DELETE FROM techjam.legal_documents 
                WHERE region = $1 AND statute = $2
            """, region, statute)
            
            # Extract the number of deleted rows from the result
            deleted_count = int(result.split()[-1]) if result and result.split() else 0
            
            return {
                "success": True,
                "message": f"Deleted {deleted_count} chunks for {region}/{statute}",
                "region": region,
                "statute": statute,
                "deleted_chunks": deleted_count
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@app.get("/api/v1/bulk_retrieve")
async def bulk_retrieve_documents(
    include_content: bool = True,
    jurisdictions: Optional[str] = None,
    max_results: int = 50
):
    """
    Bulk retrieve documents - compatibility endpoint for existing integration
    """
    try:
        jurisdiction_list = None
        if jurisdictions:
            jurisdiction_list = [j.strip() for j in jurisdictions.split(',')]
        
        # Use semantic search with empty query to get all documents
        result = await semantic_search_documents("", jurisdiction_list, max_results)
        
        # Format for bulk retrieve response
        return {
            "documents": result["documents"],
            "total_documents": result["total_documents"],
            "retrieval_time": result["retrieval_time"],
            "include_content": include_content
        }
        
    except Exception as e:
        logger.error(f"Bulk retrieve failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk retrieve failed: {str(e)}")

# --- Main Execution ---
async def main():
    """Main entry point for MCP server"""
    # Run the MCP server with correct initialization
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            # MCP 1.0.0+ uses simple server.run without InitializationOptions
        )

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        # Run as HTTP server
        uvicorn.run(app, host="0.0.0.0", port=8010)
    else:
        # Run as MCP server
        asyncio.run(main())


# Import issue fixed - these are now imported at the top