"""
Chat Management API Endpoints - Persistent chat sessions
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
import logging

from ...core.models import (
    ChatSession, ChatMessage, CreateChatRequest, 
    ChatListResponse, SendMessageRequest
)
from ...services.chat_storage import chat_storage

router = APIRouter(prefix="/api/chats", tags=["chat-management"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=ChatSession)
async def create_chat(request: CreateChatRequest):
    """Create a new chat session"""
    try:
        chat = await chat_storage.create_chat(
            title=request.title,
            initial_message=request.initial_message
        )
        return chat
    except Exception as e:
        logger.error(f"Failed to create chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat session")

@router.get("/", response_model=ChatListResponse)
async def list_chats(limit: Optional[int] = 50):
    """List all chat sessions"""
    try:
        chats = await chat_storage.list_chats(limit=limit)
        return ChatListResponse(chats=chats, total=len(chats))
    except Exception as e:
        logger.error(f"Failed to list chats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat sessions")

@router.get("/{chat_id}", response_model=ChatSession)
async def get_chat(chat_id: str):
    """Get a specific chat session with full message history"""
    try:
        chat = await chat_storage.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return chat
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat session")

@router.post("/{chat_id}/messages", response_model=ChatMessage)
async def add_message(chat_id: str, request: SendMessageRequest):
    """Add a user message to a chat session"""
    try:
        # Verify chat exists
        chat = await chat_storage.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Create user message
        message = ChatMessage(
            type="user",
            content=request.message,
            timestamp=datetime.now()
        )
        
        # Add to chat
        updated_chat = await chat_storage.add_message(chat_id, message)
        if not updated_chat:
            raise HTTPException(status_code=500, detail="Failed to add message")
        
        return message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add message to chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add message")

@router.put("/{chat_id}/title")
async def update_chat_title(chat_id: str, title_data: dict):
    """Update chat title"""
    try:
        title = title_data.get("title", "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        
        updated_chat = await chat_storage.update_chat_title(chat_id, title)
        if not updated_chat:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return {"status": "success", "title": title}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update chat title {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update chat title")

@router.post("/{chat_id}/archive")
async def archive_chat(chat_id: str):
    """Archive a chat session"""
    try:
        updated_chat = await chat_storage.archive_chat(chat_id)
        if not updated_chat:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return {"status": "success", "archived": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to archive chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive chat")

@router.delete("/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a chat session permanently"""
    try:
        success = await chat_storage.delete_chat(chat_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return {"status": "success", "deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat")

@router.get("/stats/summary")
async def get_chat_stats():
    """Get chat storage statistics"""
    try:
        stats = await chat_storage.get_chat_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get chat stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat statistics")