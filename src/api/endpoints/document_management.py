"""
Document management endpoints for the frontend integration.
Handles document upload, storage, and retrieval for the TRD system.
"""

import asyncio
import uuid
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from pydantic import BaseModel, HttpUrl
import json
import aiohttp
import aiofiles
from urllib.parse import urlparse
import re

from ...core.database import db_manager, DocumentRepository

router = APIRouter(prefix="/api/documents", tags=["document-management"])

# Database session dependency
def get_document_repo():
    db_session = next(db_manager.get_db_session())
    try:
        yield DocumentRepository(db_session)
    finally:
        db_session.close()

# File storage setup
BASE_DIR = Path(__file__).parent.parent.parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"

# Ensure upload directories exist
(UPLOAD_DIR / "requirements").mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "legal").mkdir(parents=True, exist_ok=True)

class DocumentResponse(BaseModel):
    id: str
    name: str
    type: str  # requirements, legal
    uploadDate: str
    status: str  # pending, processing, analyzed, stored, error
    size: int
    metadata: Optional[Dict[str, Any]] = None

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),  # requirements or legal
    metadata: Optional[str] = Form(None),
    doc_repo: DocumentRepository = Depends(get_document_repo)
):
    """Upload document with immediate library prompt response"""
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Check file type
    allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, DOCX, DOC, or TXT")
    
    # Check file size (50MB limit)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB")
    
    # Parse metadata if provided
    parsed_metadata = {}
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata format")
    
    # Create document record
    document_id = str(uuid.uuid4())
    
    # Save file to disk
    file_extension = Path(file.filename).suffix
    safe_filename = f"{document_id}_{file.filename.replace(' ', '_')}"
    file_path = UPLOAD_DIR / doc_type / safe_filename
    
    # Write file to disk
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Use law title as document name for legal documents if provided
    document_name = file.filename
    if doc_type == "legal" and parsed_metadata and parsed_metadata.get("law_title"):
        document_name = f"{parsed_metadata['law_title']} ({file.filename})"

    document = {
        "id": document_id,
        "name": document_name,
        "type": doc_type,
        "uploadDate": datetime.now().isoformat(),
        "status": "processing",
        "size": len(content),
        "metadata": parsed_metadata,
        "file_path": str(file_path),  # Store file path instead of content
        "processed": False,
        "original_filename": file.filename,
        "content_type": file.content_type
    }
    
    # Save to database instead of memory
    await doc_repo.save_document(document)
    
    # Simulate processing delay
    await asyncio.sleep(0.5)
    
    # Update status based on type
    if doc_type == "requirements":
        # Simulate requirements extraction
        document["status"] = "analyzed"
        document["processed"] = True
        document["requirements_extracted"] = 15  # Mock count
    else:  # legal
        # Legal documents are stored and ready
        document["status"] = "stored"
        document["processed"] = True
    
    # Update document status in database
    await doc_repo.update_document_status(document_id, document["status"])
    
    return DocumentResponse(
        id=document["id"],
        name=document["name"], 
        type=document["type"],
        uploadDate=document["uploadDate"],
        status=document["status"],
        size=document["size"],
        metadata=document.get("metadata")
    )

@router.get("", response_model=List[DocumentResponse])
async def get_documents(
    type_filter: Optional[str] = Query(None, alias="type"),
    status: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    doc_repo: DocumentRepository = Depends(get_document_repo)
):
    """Get documents with optional filtering"""
    
    # Get documents from database with filters
    filters = {}
    if type_filter:
        filters["type"] = type_filter
    if status:
        filters["status"] = status
    if limit:
        filters["limit"] = limit
    
    documents = await doc_repo.get_all_documents(filters)
    
    return [
        DocumentResponse(
            id=doc["id"],
            name=doc["name"],
            type=doc["type"], 
            uploadDate=doc["uploadDate"],
            status=doc["status"],
            size=doc["size"],
            metadata=doc.get("metadata")
        )
        for doc in documents
    ]

@router.get("/recent", response_model=List[DocumentResponse])
async def get_recent_uploads(limit: int = Query(5, ge=1, le=20)):
    """Get recent uploads for landing page display"""
    
    documents = list(stored_documents.values())
    
    # Sort by upload date (newest first)
    documents.sort(key=lambda x: x["uploadDate"], reverse=True)
    
    # Get recent documents
    recent_docs = documents[:limit]
    
    return [
        DocumentResponse(
            id=doc["id"],
            name=doc["name"],
            type=doc["type"],
            uploadDate=doc["uploadDate"], 
            status=doc["status"],
            size=doc["size"],
            metadata=doc.get("metadata")
        )
        for doc in recent_docs
    ]

# Knowledge Base endpoints (must be before dynamic routes)
@router.get("/knowledge-base")
async def get_knowledge_base():
    """Get knowledge base content"""
    return {"content": get_knowledge_base_content()}

@router.post("/knowledge-base")
async def update_knowledge_base(request: dict):
    """Update knowledge base content"""
    if "content" not in request:
        raise HTTPException(status_code=400, detail="Content field is required")
    
    success = update_knowledge_base_content(request["content"])
    
    if success:
        return {"message": "Knowledge base updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update knowledge base")

# System Prompt endpoints
@router.get("/system-prompt")
async def get_system_prompt():
    """Get system prompt content"""
    return {"content": get_system_prompt_content()}

@router.post("/system-prompt")
async def update_system_prompt(request: dict):
    """Update system prompt content"""
    if "content" not in request:
        raise HTTPException(status_code=400, detail="Content field is required")
    
    success = update_system_prompt_content(request["content"])
    
    if success:
        return {"message": "System prompt updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update system prompt")

@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get specific document details"""
    
    if document_id not in stored_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = stored_documents[document_id]
    
    return DocumentResponse(
        id=doc["id"],
        name=doc["name"],
        type=doc["type"],
        uploadDate=doc["uploadDate"],
        status=doc["status"],
        size=doc["size"],
        metadata=doc.get("metadata")
    )

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its file"""
    
    if document_id not in stored_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = stored_documents[document_id]
    
    # Delete file from disk if it exists
    if "file_path" in doc:
        file_path = Path(doc["file_path"])
        if file_path.exists():
            try:
                file_path.unlink()  # Delete the file
            except OSError as e:
                # Log error but don't fail the request
                print(f"Warning: Could not delete file {file_path}: {e}")
    
    del stored_documents[document_id]
    
    return {"message": "Document deleted successfully", "document_id": document_id}

@router.get("/stats/overview")
async def get_document_stats():
    """Get document library statistics"""
    
    documents = list(stored_documents.values())
    
    total_count = len(documents)
    requirements_count = len([doc for doc in documents if doc["type"] == "requirements"])
    legal_count = len([doc for doc in documents if doc["type"] == "legal"])
    total_size = sum(doc["size"] for doc in documents)
    
    # Get latest upload
    latest_upload = None
    if documents:
        latest_doc = max(documents, key=lambda x: x["uploadDate"])
        upload_time = datetime.fromisoformat(latest_doc["uploadDate"])
        now = datetime.now()
        time_diff = now - upload_time
        
        if time_diff.days > 0:
            latest_upload = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            latest_upload = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = max(1, time_diff.seconds // 60)
            latest_upload = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    
    return {
        "total_documents": total_count,
        "requirements_documents": requirements_count,
        "legal_documents": legal_count,
        "total_size_mb": round(total_size / (1024 * 1024), 1),
        "latest_upload": latest_upload
    }

# Knowledge Base endpoints
_knowledge_base_content = """# TikTok Terminology

## Core Platform Terms
- **ASL** = American Sign Language
- **FYP** = For You Page (personalized recommendation feed)
- **LIVE** = live streaming feature
- **algo** = algorithm (recommendation system)

## Content Features
- **duet** = collaborative video feature allowing response videos
- **stitch** = video response feature for remixing content
- **sound sync** = audio synchronization feature
- **green screen** = background replacement feature
- **beauty filter** = appearance enhancement filter
- **AR effects** = augmented reality effects

## Creator & Commerce
- **Creator Fund** = monetization program for content creators
- **creator marketplace** = brand partnership platform
- **TikTok Shop** = e-commerce integration platform
- **branded content** = sponsored content feature

## Business & Analytics
- **pulse** = analytics dashboard for creators and businesses
- **spark ads** = advertising platform for businesses
- **brand takeover** = full-screen advertisement format
- **top view** = premium ad placement option

## Feature Components
- **jellybean** = individual feature component within the platform
- **hashtag challenge** = trending challenge campaign format"""

def get_knowledge_base_content() -> str:
    """Get current knowledge base content"""
    global _knowledge_base_content
    return _knowledge_base_content

def update_knowledge_base_content(content: str) -> bool:
    """Update knowledge base content"""
    global _knowledge_base_content
    _knowledge_base_content = content
    return True

# System Prompt storage
_system_prompt_content = """You are a senior legal compliance expert specializing in TikTok platform regulations and social media law across global jurisdictions.

## Core Expertise
- **Platform Regulations**: Deep understanding of social media platform compliance requirements
- **Geographic Coverage**: US (Federal, Utah, California, Florida), EU (DSA, GDPR), Brazil (LGPD), and emerging markets
- **Risk Assessment**: Expertise in evaluating feature compliance risk levels (1-5 scale)
- **Implementation Guidance**: Practical, actionable compliance recommendations

## Analysis Approach
1. **Feature Categorization**: Identify regulatory triggers based on feature functionality
2. **Jurisdiction Mapping**: Match features to applicable regulatory frameworks
3. **Risk Assessment**: Evaluate potential legal, financial, and operational impacts
4. **Implementation Planning**: Provide concrete steps for compliance achievement

## Key Regulatory Focus Areas
- **Minor Protection**: Age verification, parental controls, usage restrictions
- **Data Privacy**: GDPR, CCPA/CPRA, LGPD compliance for personal data handling
- **Content Moderation**: DSA requirements, transparency reporting, illegal content response
- **Algorithmic Transparency**: EU AI Act, platform algorithm disclosure requirements
- **Commercial Activity**: Consumer protection, advertising standards, payment processing

## Response Format
For each compliance analysis, provide:
- **Executive Summary**: High-level compliance status and risk assessment
- **Jurisdictional Analysis**: Specific requirements by geography
- **Implementation Roadmap**: Prioritized action items with timelines
- **Risk Mitigation**: Strategies to minimize regulatory exposure
- **Ongoing Monitoring**: Requirements for continuous compliance

## Decision Framework
- **Compliance Required**: Any jurisdiction requiring compliance triggers overall requirement
- **Risk Level**: Maximum risk across jurisdictions (1=minimal, 5=critical)
- **Priority**: Focus on minor protection and high-penalty regulations first
- **Implementation**: Balance legal requirements with technical feasibility"""

def get_system_prompt_content() -> str:
    """Get current system prompt content"""
    global _system_prompt_content
    return _system_prompt_content

def update_system_prompt_content(content: str) -> bool:
    """Update system prompt content"""
    global _system_prompt_content
    _system_prompt_content = content
    return True

class UrlUploadRequest(BaseModel):
    url: str
    doc_type: str  # requirements or legal
    metadata: Optional[Dict[str, Any]] = None

@router.post("/upload-url", response_model=DocumentResponse)
async def upload_from_url(
    request: UrlUploadRequest,
    doc_repo: DocumentRepository = Depends(get_document_repo)
):
    """Upload document from URL"""
    
    # Validate URL
    try:
        parsed_url = urlparse(request.url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise HTTPException(status_code=400, detail="Invalid URL format")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    # Create document record
    document_id = str(uuid.uuid4())
    
    try:
        # Fetch content from URL
        async with aiohttp.ClientSession() as session:
            async with session.get(request.url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail=f"Failed to fetch URL: HTTP {response.status}")
                
                content = await response.read()
                content_type = response.headers.get('content-type', '').lower()
                
                # Determine filename from URL or content type
                filename = Path(parsed_url.path).name
                if not filename:
                    if 'pdf' in content_type:
                        filename = f"document_{document_id}.pdf"
                    else:
                        filename = f"document_{document_id}.html"
                
                # Ensure we have a reasonable filename
                if not filename or '.' not in filename:
                    if 'pdf' in content_type:
                        filename = f"url_document_{document_id}.pdf"
                    else:
                        filename = f"url_document_{document_id}.txt"
        
        # Check file size (50MB limit)
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Document too large. Maximum size is 50MB")
        
        # Save file to disk
        safe_filename = f"{document_id}_{filename.replace(' ', '_')}"
        file_path = UPLOAD_DIR / request.doc_type / safe_filename
        
        # Write file to disk
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        # Merge user metadata with system metadata
        document_metadata = {
            "source_url": request.url,
            "content_type": content_type,
            "original_filename": filename
        }
        if request.metadata:
            document_metadata.update(request.metadata)

        # Use law title as document name for legal documents if provided
        document_name = f"URL: {request.url}"
        if request.doc_type == "legal" and document_metadata.get("law_title"):
            document_name = f"{document_metadata['law_title']} (from URL)"

        document = {
            "id": document_id,
            "name": document_name,
            "type": request.doc_type,
            "uploadDate": datetime.now().isoformat(),
            "status": "processing",
            "size": len(content),
            "metadata": document_metadata,
            "file_path": str(file_path),
            "processed": False
        }
        
        # Save to database
        await doc_repo.save_document(document)
        
        # Simulate processing delay
        await asyncio.sleep(0.5)
        
        # Update status based on type
        if request.doc_type == "requirements":
            # Simulate requirements extraction
            document["status"] = "analyzed"
            document["processed"] = True
            document["requirements_extracted"] = 12  # Mock count
        else:  # legal
            # Legal documents are stored and ready
            document["status"] = "stored"
            document["processed"] = True
        
        # Update document status in database
        await doc_repo.update_document_status(document_id, document["status"])
        
        return DocumentResponse(
            id=document["id"],
            name=document["name"],
            type=document["type"],
            uploadDate=document["uploadDate"],
            status=document["status"],
            size=document["size"],
            metadata=document.get("metadata")
        )
        
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        # Clean up any partial file
        if 'file_path' in locals():
            try:
                Path(file_path).unlink(missing_ok=True)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error processing URL: {str(e)}")

@router.get("/{document_id}/content")
async def get_document_content(
    document_id: str,
    doc_repo: DocumentRepository = Depends(get_document_repo)
):
    """Get document file content"""
    
    doc = await doc_repo.get_document_by_id(document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = Path(doc["file_path"])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found on disk")
    
    try:
        # Return file content based on type
        if file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"content": content, "type": "text", "encoding": "utf-8"}
        else:
            # For binary files like PDF, return file info
            return {
                "file_path": str(file_path),
                "type": "binary",
                "size": file_path.stat().st_size,
                "message": "Binary file stored on disk"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

def cleanup_document_files():
    """Utility function to clean up orphaned files (optional)"""
    # This would be called periodically to clean up files
    # whose document records have been deleted
    pass