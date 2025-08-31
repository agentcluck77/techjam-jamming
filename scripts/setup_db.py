#!/usr/bin/env python3
"""
Database setup script - Phase 1B
Initialize database tables and basic configuration
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import Base, db_manager
from src.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Setup database tables and basic configuration"""
    
    logger.info("Setting up database...")
    logger.info(f"Database URL: {settings.database_url}")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=db_manager.engine)
        logger.info("Database tables created successfully")
        
        # Test connection
        if db_manager.health_check():
            logger.info("Database connection verified")
        else:
            logger.error("Database connection failed")
            return False
            
        logger.info("Database setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    if not success:
        sys.exit(1)