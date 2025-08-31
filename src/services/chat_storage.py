"""
Chat Storage Service - PostgreSQL-based persistence for chat sessions
"""
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import desc, func, create_engine
import logging
import uuid

from ..core.models import ChatSession, ChatMessage
from ..database.chat_models import ChatSessionDB, ChatMessageDB, Base
from ..config import settings

logger = logging.getLogger(__name__)

class ChatStorageService:
    """PostgreSQL-based chat storage service"""
    
    def __init__(self):
        # Create database engine
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create tables if they don't exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Chat tables created/verified")
        except Exception as e:
            logger.error(f"Failed to create chat tables: {e}")
    
    def _get_db(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def _db_to_pydantic_session(self, db_session: ChatSessionDB) -> ChatSession:
        """Convert database session to Pydantic model"""
        messages = [
            ChatMessage(
                id=msg.id,
                type=msg.type,
                content=msg.content,
                timestamp=msg.timestamp,
                model_used=msg.model_used,
                reasoning_steps=msg.reasoning_steps,
                mcp_executions=msg.mcp_executions
            ) for msg in sorted(db_session.messages, key=lambda x: x.timestamp)
        ]
        
        return ChatSession(
            id=db_session.id,
            title=db_session.title,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            messages=messages,
            status=db_session.status,
            model_preference=db_session.model_preference
        )
    
    def _pydantic_to_db_message(self, message: ChatMessage) -> ChatMessageDB:
        """Convert Pydantic message to database model"""
        return ChatMessageDB(
            id=message.id,
            type=message.type,
            content=message.content,
            timestamp=message.timestamp,
            model_used=message.model_used,
            reasoning_steps=message.reasoning_steps,
            mcp_executions=message.mcp_executions
        )
    
    async def create_chat(self, title: Optional[str] = None, initial_message: Optional[str] = None) -> ChatSession:
        """Create a new chat session"""
        db = self._get_db()
        try:
            # Generate title if not provided
            if not title:
                if initial_message:
                    title = initial_message[:50].strip()
                    if len(initial_message) > 50:
                        title += "..."
                else:
                    title = f"Legal Chat {datetime.now().strftime('%m/%d %H:%M')}"
            
            # Create database session
            db_session = ChatSessionDB(
                id=str(uuid.uuid4()),
                title=title,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(db_session)
            db.flush()  # Get the ID
            
            # Add initial message if provided
            if initial_message:
                db_message = ChatMessageDB(
                    id=str(uuid.uuid4()),
                    session_id=db_session.id,
                    type="user",
                    content=initial_message,
                    timestamp=datetime.now()
                )
                db.add(db_message)
            
            db.commit()
            db.refresh(db_session)
            
            logger.info(f"Created chat session: {db_session.id} - '{title}'")
            return self._db_to_pydantic_session(db_session)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create chat: {e}")
            raise
        finally:
            db.close()
    
    async def get_chat(self, chat_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID with all messages"""
        db = self._get_db()
        try:
            db_session = db.query(ChatSessionDB).filter(
                ChatSessionDB.id == chat_id
            ).first()
            
            if not db_session:
                return None
                
            return self._db_to_pydantic_session(db_session)
            
        except Exception as e:
            logger.error(f"Failed to get chat {chat_id}: {e}")
            return None
        finally:
            db.close()
    
    async def list_chats(self, limit: Optional[int] = None) -> List[ChatSession]:
        """List all chat sessions, ordered by most recent"""
        db = self._get_db()
        try:
            query = db.query(ChatSessionDB).order_by(desc(ChatSessionDB.updated_at))
            
            if limit:
                query = query.limit(limit)
            
            db_sessions = query.all()
            
            # Convert to Pydantic models (without full message loading for list view)
            sessions = []
            for db_session in db_sessions:
                # For list view, only load basic info and recent messages
                recent_messages = db.query(ChatMessageDB).filter(
                    ChatMessageDB.session_id == db_session.id
                ).order_by(desc(ChatMessageDB.timestamp)).limit(3).all()
                
                messages = [
                    ChatMessage(
                        id=msg.id,
                        type=msg.type,
                        content=msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,  # Truncate for list
                        timestamp=msg.timestamp,
                        model_used=msg.model_used
                    ) for msg in reversed(recent_messages)  # Restore chronological order
                ]
                
                session = ChatSession(
                    id=db_session.id,
                    title=db_session.title,
                    created_at=db_session.created_at,
                    updated_at=db_session.updated_at,
                    messages=messages,
                    status=db_session.status,
                    model_preference=db_session.model_preference
                )
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list chats: {e}")
            return []
        finally:
            db.close()
    
    async def add_message(self, chat_id: str, message: ChatMessage) -> Optional[ChatSession]:
        """Add a message to a chat session"""
        db = self._get_db()
        try:
            # Verify chat exists
            db_session = db.query(ChatSessionDB).filter(
                ChatSessionDB.id == chat_id
            ).first()
            
            if not db_session:
                return None
            
            # Create message
            db_message = ChatMessageDB(
                id=message.id,
                session_id=chat_id,
                type=message.type,
                content=message.content,
                timestamp=message.timestamp,
                model_used=message.model_used,
                reasoning_steps=message.reasoning_steps,
                mcp_executions=message.mcp_executions
            )
            
            # Update session timestamp
            db_session.updated_at = datetime.now()
            
            db.add(db_message)
            db.commit()
            db.refresh(db_session)
            
            logger.debug(f"Added message to chat {chat_id}: {message.type}")
            return self._db_to_pydantic_session(db_session)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add message to chat {chat_id}: {e}")
            return None
        finally:
            db.close()
    
    async def update_chat_title(self, chat_id: str, title: str) -> Optional[ChatSession]:
        """Update chat title"""
        db = self._get_db()
        try:
            db_session = db.query(ChatSessionDB).filter(
                ChatSessionDB.id == chat_id
            ).first()
            
            if not db_session:
                return None
            
            db_session.title = title
            db_session.updated_at = datetime.now()
            
            db.commit()
            db.refresh(db_session)
            
            return self._db_to_pydantic_session(db_session)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update chat title {chat_id}: {e}")
            return None
        finally:
            db.close()
    
    async def archive_chat(self, chat_id: str) -> Optional[ChatSession]:
        """Archive a chat session"""
        db = self._get_db()
        try:
            db_session = db.query(ChatSessionDB).filter(
                ChatSessionDB.id == chat_id
            ).first()
            
            if not db_session:
                return None
            
            db_session.status = "archived"
            db_session.updated_at = datetime.now()
            
            db.commit()
            db.refresh(db_session)
            
            return self._db_to_pydantic_session(db_session)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to archive chat {chat_id}: {e}")
            return None
        finally:
            db.close()
    
    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat session completely"""
        db = self._get_db()
        try:
            # Delete session (messages will cascade delete)
            deleted = db.query(ChatSessionDB).filter(
                ChatSessionDB.id == chat_id
            ).delete()
            
            db.commit()
            
            if deleted > 0:
                logger.info(f"Deleted chat session: {chat_id}")
                return True
            return False
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete chat {chat_id}: {e}")
            return False
        finally:
            db.close()
    
    async def get_chat_stats(self) -> Dict[str, int]:
        """Get basic statistics about stored chats"""
        db = self._get_db()
        try:
            total_chats = db.query(func.count(ChatSessionDB.id)).scalar()
            active_chats = db.query(func.count(ChatSessionDB.id)).filter(
                ChatSessionDB.status == "active"
            ).scalar()
            archived_chats = db.query(func.count(ChatSessionDB.id)).filter(
                ChatSessionDB.status == "archived"
            ).scalar()
            total_messages = db.query(func.count(ChatMessageDB.id)).scalar()
            
            return {
                "total_chats": total_chats or 0,
                "active_chats": active_chats or 0,
                "archived_chats": archived_chats or 0,
                "total_messages": total_messages or 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get chat stats: {e}")
            return {"total_chats": 0, "active_chats": 0, "archived_chats": 0, "total_messages": 0}
        finally:
            db.close()

# Global instance
chat_storage = ChatStorageService()