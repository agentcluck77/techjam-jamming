"""
Knowledge Base and System Prompt Management API Endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict
from pydantic import BaseModel
import os

router = APIRouter(prefix="/api/documents", tags=["knowledge-base"])

# Configuration storage - in production use database
CONFIG_DIR = "data/config"
KNOWLEDGE_BASE_FILE = f"{CONFIG_DIR}/knowledge_base.md"
SYSTEM_PROMPT_FILE = f"{CONFIG_DIR}/system_prompt.md"

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

class ContentRequest(BaseModel):
    content: str

@router.get("/knowledge-base")
async def get_knowledge_base() -> Dict[str, str]:
    """
    Get current knowledge base content
    
    Returns:
        Knowledge base content
    """
    try:
        if os.path.exists(KNOWLEDGE_BASE_FILE):
            with open(KNOWLEDGE_BASE_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = get_default_knowledge_base()
            
        return {"content": content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge base: {str(e)}")

@router.post("/knowledge-base")
async def update_knowledge_base(request: ContentRequest) -> Dict[str, str]:
    """
    Update knowledge base content
    
    Args:
        request: Content to update knowledge base with
        
    Returns:
        Success message
    """
    try:
        with open(KNOWLEDGE_BASE_FILE, 'w', encoding='utf-8') as f:
            f.write(request.content)
            
        return {"message": "Knowledge base updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update knowledge base: {str(e)}")

@router.get("/system-prompt") 
async def get_system_prompt() -> Dict[str, str]:
    """
    Get current system prompt content
    
    Returns:
        System prompt content
    """
    try:
        if not os.path.exists(SYSTEM_PROMPT_FILE):
            raise HTTPException(status_code=404, detail=f"System prompt not found at {SYSTEM_PROMPT_FILE}. Please create the file with your system prompt configuration.")
        
        with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return {"content": content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system prompt: {str(e)}")

@router.post("/system-prompt")
async def update_system_prompt(request: ContentRequest) -> Dict[str, str]:
    """
    Update system prompt content
    
    Args:
        request: Content to update system prompt with
        
    Returns:
        Success message
    """
    try:
        with open(SYSTEM_PROMPT_FILE, 'w', encoding='utf-8') as f:
            f.write(request.content)
            
        return {"message": "System prompt updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update system prompt: {str(e)}")

def get_default_knowledge_base() -> str:
    """Get default knowledge base content"""
    return """# TikTok Terminology

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

def get_default_system_prompt() -> str:
    """DEPRECATED: Default system prompt - use system_prompt.md instead"""
    raise RuntimeError("Default system prompt deprecated. System prompt must be configured in data/config/system_prompt.md")