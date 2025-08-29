"""
Database setup and models - Phase 1B Implementation
SQLAlchemy models and database connection management
"""
from sqlalchemy import create_engine, Column, String, Boolean, Integer, Float, DateTime, Text, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
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

# TODO: Team Member 2 - Add batch processing tables
# class BatchJobDB(Base):
#     """Batch processing job tracking"""
#     __tablename__ = "batch_jobs"
#     # ... implementation for CSV batch processing

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
            # Create database engine
            self.engine = create_engine(
                settings.database_url,
                echo=True if settings.environment == "development" else False,
                pool_size=5,
                max_overflow=10
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
        try:
            db = self.SessionLocal()
            # Simple health check query
            db.execute("SELECT 1")
            db.close()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

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

# TODO: Team Member 1 - Enhanced repository with caching and performance optimization
# class EnhancedFeatureAnalysisRepository(FeatureAnalysisRepository):
#     """Enhanced repository with caching and batch operations"""
#     
#     def __init__(self, db_session, cache_manager=None):
#         super().__init__(db_session)
#         self.cache = cache_manager
#     
#     async def save_analysis(self, analysis_response: dict) -> str:
#         # TODO: Team Member 1 - Add caching layer
#         # 1. Save to database
#         # 2. Cache result for future lookups
#         # 3. Add batch save optimization
#         pass