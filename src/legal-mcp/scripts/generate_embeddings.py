#!/usr/bin/env python3
"""
Generate embeddings for existing legal documents in PostgreSQL
Run this script to backfill vector embeddings for all existing legal documents
"""

import asyncio
import logging
import os
import sys
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import asyncpg
from dotenv import load_dotenv
import time

# Add the legal-mcp source to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src2_path = os.path.join(parent_dir, 'src2')
sys.path.insert(0, src2_path)

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

# Load the sentence transformer model
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Sentence transformer model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load sentence transformer model: {e}")
    sys.exit(1)

async def get_available_regions(conn) -> List[str]:
    """Get list of all available regions from database tables"""
    try:
        regions_result = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'techjam' 
            AND table_name LIKE 't_law_%_regulations'
        """)
        regions = [table['table_name'].replace('t_law_', '').replace('_regulations', '') 
                  for table in regions_result]
        logger.info(f"Found regions: {regions}")
        return regions
    except Exception as e:
        logger.error(f"Failed to get regions: {e}")
        return []

async def generate_embeddings_for_regulations(conn, region: str) -> int:
    """Generate embeddings for all regulations in a specific region"""
    try:
        logger.info(f"Processing regulations for region: {region}")
        
        # Get all regulations without embeddings or with outdated embeddings
        query = f"""
            SELECT law_id, regulations 
            FROM techjam.t_law_{region}_regulations 
            WHERE (embedding IS NULL OR embedding_created_at IS NULL)
            AND regulations IS NOT NULL 
            AND LENGTH(regulations) > 0
        """
        
        rows = await conn.fetch(query)
        logger.info(f"Found {len(rows)} regulations to process in {region}")
        
        if not rows:
            return 0
        
        processed_count = 0
        batch_size = 10  # Process in batches to avoid memory issues
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            
            # Generate embeddings for batch
            texts = [row['regulations'] for row in batch]
            law_ids = [row['law_id'] for row in batch]
            
            try:
                # Generate embeddings
                embeddings = model.encode(texts)
                
                # Update database with embeddings
                for j, (law_id, embedding) in enumerate(zip(law_ids, embeddings)):
                    update_query = f"""
                        UPDATE techjam.t_law_{region}_regulations 
                        SET embedding = $1, 
                            embedding_created_at = CURRENT_TIMESTAMP,
                            embedding_model = 'all-MiniLM-L6-v2'
                        WHERE law_id = $2
                    """
                    
                    # Convert numpy array to list for PostgreSQL
                    embedding_list = embedding.tolist()
                    
                    await conn.execute(update_query, embedding_list, law_id)
                    processed_count += 1
                
                logger.info(f"Processed batch {i//batch_size + 1} for {region}: {len(batch)} regulations")
                
            except Exception as e:
                logger.error(f"Failed to process batch {i//batch_size + 1} for {region}: {e}")
                continue
        
        logger.info(f"Completed processing {processed_count} regulations for {region}")
        return processed_count
        
    except Exception as e:
        logger.error(f"Failed to generate embeddings for {region} regulations: {e}")
        return 0

async def generate_embeddings_for_definitions(conn, region: str) -> int:
    """Generate embeddings for all definitions in a specific region"""
    try:
        logger.info(f"Processing definitions for region: {region}")
        
        # Get all definitions without embeddings
        query = f"""
            SELECT statute, definitions 
            FROM techjam.t_law_{region}_definitions 
            WHERE (embedding IS NULL OR embedding_created_at IS NULL)
            AND definitions IS NOT NULL 
            AND LENGTH(definitions) > 0
        """
        
        rows = await conn.fetch(query)
        logger.info(f"Found {len(rows)} definitions to process in {region}")
        
        if not rows:
            return 0
        
        processed_count = 0
        batch_size = 10
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            
            # Generate embeddings for batch
            texts = [row['definitions'] for row in batch]
            statutes = [row['statute'] for row in batch]
            
            try:
                # Generate embeddings
                embeddings = model.encode(texts)
                
                # Update database with embeddings
                for j, (statute, embedding) in enumerate(zip(statutes, embeddings)):
                    update_query = f"""
                        UPDATE techjam.t_law_{region}_definitions 
                        SET embedding = $1, 
                            embedding_created_at = CURRENT_TIMESTAMP,
                            embedding_model = 'all-MiniLM-L6-v2'
                        WHERE statute = $2 AND region = $3
                    """
                    
                    # Convert numpy array to list for PostgreSQL
                    embedding_list = embedding.tolist()
                    
                    await conn.execute(update_query, embedding_list, statute, region)
                    processed_count += 1
                
                logger.info(f"Processed batch {i//batch_size + 1} for {region}: {len(batch)} definitions")
                
            except Exception as e:
                logger.error(f"Failed to process batch {i//batch_size + 1} for {region}: {e}")
                continue
        
        logger.info(f"Completed processing {processed_count} definitions for {region}")
        return processed_count
        
    except Exception as e:
        logger.error(f"Failed to generate embeddings for {region} definitions: {e}")
        return 0

async def verify_embeddings(conn, region: str) -> Dict[str, int]:
    """Verify embedding generation results for a region"""
    try:
        # Count regulations with embeddings
        reg_query = f"""
            SELECT 
                COUNT(*) as total_regulations,
                COUNT(embedding) as regulations_with_embeddings
            FROM techjam.t_law_{region}_regulations
        """
        reg_result = await conn.fetchrow(reg_query)
        
        # Count definitions with embeddings  
        def_query = f"""
            SELECT 
                COUNT(*) as total_definitions,
                COUNT(embedding) as definitions_with_embeddings
            FROM techjam.t_law_{region}_definitions
        """
        def_result = await conn.fetchrow(def_query)
        
        return {
            "region": region,
            "total_regulations": reg_result['total_regulations'],
            "regulations_with_embeddings": reg_result['regulations_with_embeddings'],
            "total_definitions": def_result['total_definitions'], 
            "definitions_with_embeddings": def_result['definitions_with_embeddings']
        }
        
    except Exception as e:
        logger.error(f"Failed to verify embeddings for {region}: {e}")
        return {"region": region, "error": str(e)}

async def main():
    """Main embedding generation process"""
    logger.info("Starting embedding generation for Legal MCP")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        logger.info("Database connection established")
        
        # Get all available regions
        regions = await get_available_regions(conn)
        
        if not regions:
            logger.warning("No regions found. Make sure your legal document tables exist.")
            return
        
        total_processed = 0
        start_time = time.time()
        
        # Process each region
        for region in regions:
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing region: {region.upper()}")
            logger.info(f"{'='*50}")
            
            try:
                # Generate embeddings for regulations
                reg_processed = await generate_embeddings_for_regulations(conn, region)
                
                # Generate embeddings for definitions
                def_processed = await generate_embeddings_for_definitions(conn, region)
                
                total_processed += reg_processed + def_processed
                
                # Verify results
                verification = await verify_embeddings(conn, region)
                logger.info(f"Verification for {region}: {verification}")
                
            except Exception as e:
                logger.error(f"Failed to process region {region}: {e}")
                continue
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"\n{'='*50}")
        logger.info(f"EMBEDDING GENERATION COMPLETE")
        logger.info(f"{'='*50}")
        logger.info(f"Total documents processed: {total_processed}")
        logger.info(f"Total time: {duration:.2f} seconds")
        logger.info(f"Average time per document: {duration/total_processed:.3f} seconds" if total_processed > 0 else "No documents processed")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())