"""
Database models for chat system using SQLAlchemy
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class ChatSessionDB(Base):
    """Chat session database model"""
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, archived
    model_preference = Column(String(50), nullable=True)
    
    # Relationship to messages
    messages = relationship("ChatMessageDB", back_populates="session", cascade="all, delete-orphan")

class ChatMessageDB(Base):
    """Chat message database model"""
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    model_used = Column(String(50), nullable=True)
    
    # JSON fields for structured data
    reasoning_steps = Column(JSON, nullable=True)
    mcp_executions = Column(JSON, nullable=True)
    
    # Relationship back to session
    session = relationship("ChatSessionDB", back_populates="messages")