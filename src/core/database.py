"""
Database setup and models - Phase 1B Implementation
SQLAlchemy models and database connection management
"""
from sqlalchemy import create_engine, Column, String, Boolean, Integer, Float, DateTime, Text, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from typing import List
import uuid
import logging

from ..config import settings

logger = logging.getLogger(__name__)

# Database base class
Base = declarative_base()

# Database models
class FeatureAnalysisDB(Base):
    """
    Feature analysis storage - Phase 1B basic implementation
    Team Member 1 will add indexes and optimization
    """
    __tablename__ = "feature_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_name = Column(String(255), nullable=False)
    feature_description = Column(Text, nullable=False)
    geographic_context = Column(Text)
    enriched_context = Column(JSONB)  # JSON storage for enriched context
    
    # Analysis results
    compliance_required = Column(Boolean, nullable=False)
    risk_level = Column(Integer, nullable=False)
    applicable_jurisdictions = Column(ARRAY(String))  # PostgreSQL array
    requirements = Column(ARRAY(String))
    implementation_steps = Column(ARRAY(String))
    confidence_score = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)
    analysis_time = Column(Float, nullable=False)  # seconds
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# TODO: Team Member 1 - Add additional tables for detailed tracking
# class JurisdictionAnalysisDB(Base):
#     """Detailed jurisdiction analysis results"""
#     __tablename__ = "jurisdiction_analyses"
#     
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     feature_analysis_id = Column(UUID(as_uuid=True), ForeignKey('feature_analyses.id'))
#     jurisdiction = Column(String(50), nullable=False)
#     # ... other fields as per TRD specification

class DocumentDB(Base):
    """Document storage - files uploaded by users"""
    __tablename__ = "documents"
    
    id = Column(String(255), primary_key=True)  # UUID as string
    name = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False)  # requirements, legal
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), nullable=False)  # pending, processing, analyzed, stored, error
    size = Column(Integer, nullable=False)  # File size in bytes
    file_path = Column(String(1000), nullable=False)  # Path to file on disk
    doc_metadata = Column(JSONB)  # JSON metadata (law_title, etc.)
    processed = Column(Boolean, default=False)
    
    # Additional fields for tracking
    content_type = Column(String(100))  # MIME type
    original_filename = Column(String(500))
    source_url = Column(String(1000))  # If uploaded from URL
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatSessionDB(Base):
    """Chat sessions storage"""
    __tablename__ = "chat_sessions"
    
    id = Column(String(255), primary_key=True)  # UUID as string
    title = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="active")  # active, archived
    model_preference = Column(String(100))  # Preferred LLM model
    
    # Session metadata
    document_id = Column(String(255))  # Associated document if any
    workflow_id = Column(String(255))  # Associated workflow if any
    session_type = Column(String(50))  # chat, analysis, bulk_operation

class ChatMessageDB(Base):
    """Chat messages storage"""
    __tablename__ = "chat_messages"
    
    id = Column(String(255), primary_key=True)  # UUID as string
    session_id = Column(String(255), nullable=False)  # Foreign key to chat_sessions
    type = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String(100))  # LLM model that generated message
    reasoning_steps = Column(JSONB)  # Agent reasoning steps
    mcp_executions = Column(JSONB)  # MCP tool executions
    
    # Message metadata
    token_count = Column(Integer)
    processing_time_ms = Column(Integer)

class ComplianceReportDB(Base):
    """Compliance analysis reports storage"""
    __tablename__ = "compliance_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(String(255), nullable=False)  # Reference to document
    document_name = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False)  # requirements or legal
    
    # Analysis metadata
    analysis_type = Column(String(50), nullable=False)  # single, bulk_requirements, bulk_legal
    related_documents = Column(ARRAY(String))  # For bulk analysis - IDs of related docs
    
    # Compliance results
    status = Column(String(50), nullable=False)  # compliant, non-compliant, needs-review
    summary = Column(Text, nullable=False)
    issues = Column(JSONB)  # JSON array of compliance issues
    recommendations = Column(JSONB)  # JSON array of recommendations
    
    # Workflow tracking
    workflow_id = Column(String(255))
    chat_session_id = Column(String(255))
    
    # Timing
    analysis_time_seconds = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BatchJobDB(Base):
    """Batch processing job tracking"""
    __tablename__ = "batch_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)  # bulk_requirements, bulk_legal
    status = Column(String(50), nullable=False)  # processing, completed, failed, cancelled
    
    # Document selection
    selected_documents = Column(ARRAY(String))  # Source documents for analysis
    target_documents = Column(ARRAY(String))  # Documents to analyze against
    
    # Progress tracking
    total_documents = Column(Integer, nullable=False)
    processed_documents = Column(Integer, default=0)
    
    # Results
    compliance_report_ids = Column(ARRAY(String))  # References to generated reports
    errors = Column(JSONB)  # JSON array of errors
    
    # Timing
    start_time = Column(DateTime, default=datetime.utcnow)
    completion_time = Column(DateTime)
    estimated_completion = Column(DateTime)

class DatabaseManager:
    """
    Database connection and session management
    Phase 1B: Basic connection setup
    """
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            # Create database engine with larger pool
            self.engine = create_engine(
                settings.database_url,
                echo=True if settings.environment == "development" else False,
                pool_size=20,  # Increased from 5
                max_overflow=30,  # Increased from 10
                pool_timeout=30,  # Wait 30 seconds for connection
                pool_recycle=3600,  # Recycle connections every hour
                pool_pre_ping=True,  # Verify connections before use
                echo_pool=True if settings.environment == "development" else False
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def get_db_session(self):
        """Get database session - dependency for FastAPI"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        db = None
        try:
            db = self.SessionLocal()
            # Simple health check query
            db.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
        finally:
            if db:
                db.close()

    def get_session_context(self):
        """Context manager for database sessions"""
        from contextlib import contextmanager
        
        @contextmanager
        def session_scope():
            db = self.SessionLocal()
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
        
        return session_scope()

# Global database manager instance
db_manager = DatabaseManager()

# Database operations
class FeatureAnalysisRepository:
    """
    Repository pattern for feature analysis data access
    Phase 1B: Basic CRUD operations
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def save_analysis(self, analysis_response: dict) -> str:
        """
        Save feature analysis to database
        Phase 1B: Basic storage without optimization
        """
        
        try:
            # Convert response to database model
            db_analysis = FeatureAnalysisDB(
                id=analysis_response["feature_id"],
                feature_name=analysis_response["feature_name"],
                feature_description="",  # TODO: Store original description
                compliance_required=analysis_response["compliance_required"],
                risk_level=analysis_response["risk_level"],
                applicable_jurisdictions=analysis_response["applicable_jurisdictions"],
                requirements=analysis_response["requirements"],
                implementation_steps=analysis_response["implementation_steps"],
                confidence_score=analysis_response["confidence_score"],
                reasoning=analysis_response["reasoning"],
                analysis_time=analysis_response["analysis_time"]
            )
            
            # Save to database
            self.db.add(db_analysis)
            self.db.commit()
            self.db.refresh(db_analysis)
            
            logger.info(f"Analysis saved for feature: {analysis_response['feature_name']}")
            return str(db_analysis.id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save analysis: {e}")
            raise
    
    async def get_analysis_by_id(self, analysis_id: str) -> dict:
        """Get analysis by ID"""
        try:
            analysis = self.db.query(FeatureAnalysisDB).filter(
                FeatureAnalysisDB.id == analysis_id
            ).first()
            
            if not analysis:
                return None
            
            return {
                "feature_id": str(analysis.id),
                "feature_name": analysis.feature_name,
                "compliance_required": analysis.compliance_required,
                "risk_level": analysis.risk_level,
                "applicable_jurisdictions": analysis.applicable_jurisdictions,
                "requirements": analysis.requirements,
                "implementation_steps": analysis.implementation_steps,
                "confidence_score": analysis.confidence_score,
                "reasoning": analysis.reasoning,
                "analysis_time": analysis.analysis_time,
                "created_at": analysis.created_at
            }
            
        except Exception as e:
            logger.error(f"Failed to get analysis {analysis_id}: {e}")
            return None
    
    async def get_recent_analyses(self, limit: int = 10) -> list:
        """Get recent analyses for dashboard"""
        try:
            analyses = self.db.query(FeatureAnalysisDB).order_by(
                FeatureAnalysisDB.created_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "feature_id": str(analysis.id),
                    "feature_name": analysis.feature_name,
                    "compliance_required": analysis.compliance_required,
                    "risk_level": analysis.risk_level,
                    "created_at": analysis.created_at
                }
                for analysis in analyses
            ]
            
        except Exception as e:
            logger.error(f"Failed to get recent analyses: {e}")
            return []

class DocumentRepository:
    """Repository for document data access"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def save_document(self, document_data: dict) -> str:
        """Save document to database"""
        try:
            db_document = DocumentDB(
                id=document_data["id"],
                name=document_data["name"],
                type=document_data["type"],
                upload_date=datetime.fromisoformat(document_data["uploadDate"]) if isinstance(document_data["uploadDate"], str) else document_data["uploadDate"],
                status=document_data["status"],
                size=document_data["size"],
                file_path=document_data["file_path"],
                doc_metadata=document_data.get("metadata", {}),
                processed=document_data.get("processed", False),
                content_type=document_data.get("content_type"),
                original_filename=document_data.get("original_filename"),
                source_url=document_data.get("source_url")
            )
            
            self.db.add(db_document)
            self.db.commit()
            self.db.refresh(db_document)
            
            logger.info(f"Document saved: {document_data['name']}")
            return db_document.id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save document: {e}")
            raise
    
    async def get_document_by_id(self, document_id: str) -> dict:
        """Get document by ID"""
        try:
            document = self.db.query(DocumentDB).filter(
                DocumentDB.id == document_id
            ).first()
            
            if not document:
                return None
            
            return {
                "id": document.id,
                "name": document.name,
                "type": document.type,
                "uploadDate": document.upload_date.isoformat(),
                "status": document.status,
                "size": document.size,
                "file_path": document.file_path,
                "metadata": document.doc_metadata,
                "processed": document.processed,
                "content_type": document.content_type,
                "original_filename": document.original_filename,
                "source_url": document.source_url
            }
            
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None
    
    async def get_all_documents(self, filters: dict = None) -> List[dict]:
        """Get all documents with optional filtering"""
        try:
            query = self.db.query(DocumentDB)
            
            # Apply filters
            if filters:
                if filters.get("type") and filters["type"] != "all":
                    query = query.filter(DocumentDB.type == filters["type"])
                if filters.get("status"):
                    query = query.filter(DocumentDB.status == filters["status"])
            
            # Sort by upload date (newest first)
            query = query.order_by(DocumentDB.upload_date.desc())
            
            # Apply limit
            if filters and filters.get("limit"):
                query = query.limit(filters["limit"])
            
            documents = query.all()
            
            return [
                {
                    "id": doc.id,
                    "name": doc.name,
                    "type": doc.type,
                    "uploadDate": doc.upload_date.isoformat(),
                    "status": doc.status,
                    "size": doc.size,
                    "metadata": doc.doc_metadata
                }
                for doc in documents
            ]
            
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            return []
    
    async def update_document_status(self, document_id: str, status: str) -> bool:
        """Update document status"""
        try:
            document = self.db.query(DocumentDB).filter(
                DocumentDB.id == document_id
            ).first()
            
            if not document:
                return False
            
            document.status = status
            document.updated_at = datetime.utcnow()
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update document status: {e}")
            return False
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document from database"""
        try:
            document = self.db.query(DocumentDB).filter(
                DocumentDB.id == document_id
            ).first()
            
            if not document:
                return False
            
            self.db.delete(document)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete document: {e}")
            return False

class ChatSessionRepository:
    """Repository for chat session data access"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def save_session(self, session_data: dict) -> str:
        """Save chat session to database"""
        try:
            db_session = ChatSessionDB(
                id=session_data["id"],
                title=session_data["title"],
                status=session_data.get("status", "active"),
                model_preference=session_data.get("model_preference"),
                document_id=session_data.get("document_id"),
                workflow_id=session_data.get("workflow_id"),
                session_type=session_data.get("session_type", "chat")
            )
            
            self.db.add(db_session)
            self.db.commit()
            self.db.refresh(db_session)
            
            logger.info(f"Chat session saved: {session_data['title']}")
            return db_session.id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save session: {e}")
            raise
    
    async def save_message(self, message_data: dict) -> str:
        """Save chat message to database"""
        try:
            db_message = ChatMessageDB(
                id=message_data["id"],
                session_id=message_data["session_id"],
                type=message_data["type"],
                content=message_data["content"],
                model_used=message_data.get("model_used"),
                reasoning_steps=message_data.get("reasoning_steps"),
                mcp_executions=message_data.get("mcp_executions"),
                token_count=message_data.get("token_count"),
                processing_time_ms=message_data.get("processing_time_ms")
            )
            
            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)
            
            return db_message.id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save message: {e}")
            raise
    
    async def get_session_with_messages(self, session_id: str) -> dict:
        """Get session with all messages"""
        try:
            session = self.db.query(ChatSessionDB).filter(
                ChatSessionDB.id == session_id
            ).first()
            
            if not session:
                return None
            
            messages = self.db.query(ChatMessageDB).filter(
                ChatMessageDB.session_id == session_id
            ).order_by(ChatMessageDB.timestamp.asc()).all()
            
            return {
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "status": session.status,
                "model_preference": session.model_preference,
                "document_id": session.document_id,
                "workflow_id": session.workflow_id,
                "session_type": session.session_type,
                "messages": [
                    {
                        "id": msg.id,
                        "type": msg.type,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "model_used": msg.model_used,
                        "reasoning_steps": msg.reasoning_steps,
                        "mcp_executions": msg.mcp_executions
                    }
                    for msg in messages
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

class ComplianceReportRepository:
    """Repository for compliance report data access"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def save_report(self, report_data: dict) -> str:
        """Save compliance report to database"""
        try:
            db_report = ComplianceReportDB(
                document_id=report_data["document_id"],
                document_name=report_data["document_name"],
                document_type=report_data["document_type"],
                analysis_type=report_data["analysis_type"],
                related_documents=report_data.get("related_documents", []),
                status=report_data["status"],
                summary=report_data["summary"],
                issues=report_data["issues"],
                recommendations=report_data.get("recommendations", []),
                workflow_id=report_data.get("workflow_id"),
                chat_session_id=report_data.get("chat_session_id"),
                analysis_time_seconds=report_data["analysis_time_seconds"]
            )
            
            self.db.add(db_report)
            self.db.commit()
            self.db.refresh(db_report)
            
            logger.info(f"Report saved for document: {report_data['document_name']}")
            return str(db_report.id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save report: {e}")
            raise
    
    async def get_report_by_document_id(self, document_id: str) -> dict:
        """Get latest report for a document"""
        try:
            report = self.db.query(ComplianceReportDB).filter(
                ComplianceReportDB.document_id == document_id
            ).order_by(ComplianceReportDB.created_at.desc()).first()
            
            if not report:
                return None
            
            return {
                "id": str(report.id),
                "document_id": report.document_id,
                "document_name": report.document_name,
                "document_type": report.document_type,
                "analysis_type": report.analysis_type,
                "related_documents": report.related_documents,
                "status": report.status,
                "summary": report.summary,
                "issues": report.issues,
                "recommendations": report.recommendations,
                "workflow_id": report.workflow_id,
                "chat_session_id": report.chat_session_id,
                "analysis_time_seconds": report.analysis_time_seconds,
                "created_at": report.created_at
            }
        except Exception as e:
            logger.error(f"Failed to get report for document {document_id}: {e}")
            return None
    
    async def get_reports_by_ids(self, report_ids: List[str]) -> List[dict]:
        """Get multiple reports by IDs for export"""
        try:
            reports = self.db.query(ComplianceReportDB).filter(
                ComplianceReportDB.id.in_(report_ids)
            ).all()
            
            return [
                {
                    "id": str(report.id),
                    "document_name": report.document_name,
                    "status": report.status,
                    "summary": report.summary,
                    "issues": report.issues,
                    "recommendations": report.recommendations,
                    "created_at": report.created_at
                }
                for report in reports
            ]
        except Exception as e:
            logger.error(f"Failed to get reports: {e}")
            return []