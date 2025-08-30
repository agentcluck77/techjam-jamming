"""
Embedding operations for Legal MCP
Handles automatic embedding generation and updates for legal documents
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
import asyncpg

logger = logging.getLogger(__name__)

# Global model instance
_model = None

def get_embedding_model():
    """Get or initialize the embedding model"""
    global _model
    if _model is None:
        try:
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            _model = None
    return _model

async def generate_embedding_async(text: str) -> Optional[List[float]]:
    """Generate embedding for text asynchronously"""
    model = get_embedding_model()
    if not model or not text or not text.strip():
        return None
    
    try:
        # Run embedding generation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, lambda: model.encode([text])[0])
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None

async def update_regulation_embedding(conn, region: str, law_id: str, regulations_text: str) -> bool:
    """Update embedding for a specific regulation"""
    try:
        embedding = await generate_embedding_async(regulations_text)
        if not embedding:
            return False
        
        query = f"""
            UPDATE techjam.t_law_{region}_regulations 
            SET embedding = $1, 
                embedding_created_at = CURRENT_TIMESTAMP,
                embedding_model = 'all-MiniLM-L6-v2'
            WHERE law_id = $2
        """
        
        await conn.execute(query, embedding, law_id)
        logger.info(f"Updated embedding for regulation {law_id} in {region}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update embedding for regulation {law_id} in {region}: {e}")
        return False

async def update_definition_embedding(conn, region: str, statute: str, definitions_text: str) -> bool:
    """Update embedding for a specific definition"""
    try:
        embedding = await generate_embedding_async(definitions_text)
        if not embedding:
            return False
        
        query = f"""
            UPDATE techjam.t_law_{region}_definitions 
            SET embedding = $1, 
                embedding_created_at = CURRENT_TIMESTAMP,
                embedding_model = 'all-MiniLM-L6-v2'
            WHERE statute = $2 AND region = $3
        """
        
        await conn.execute(query, embedding, statute, region)
        logger.info(f"Updated embedding for definition {statute} in {region}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update embedding for definition {statute} in {region}: {e}")
        return False

async def batch_update_embeddings(conn, region: str, documents: List[Dict[str, Any]], doc_type: str = "regulation") -> int:
    """Batch update embeddings for multiple documents"""
    try:
        updated_count = 0
        
        for doc in documents:
            if doc_type == "regulation":
                text = doc.get("regulations")
                law_id = doc.get("law_id")
                if text and law_id:
                    success = await update_regulation_embedding(conn, region, law_id, text)
                    if success:
                        updated_count += 1
            
            elif doc_type == "definition":
                text = doc.get("definitions")
                statute = doc.get("statute")
                if text and statute:
                    success = await update_definition_embedding(conn, region, statute, text)
                    if success:
                        updated_count += 1
        
        logger.info(f"Batch updated {updated_count} embeddings for {region} {doc_type}s")
        return updated_count
        
    except Exception as e:
        logger.error(f"Batch embedding update failed for {region} {doc_type}s: {e}")
        return 0

async def ensure_embeddings_exist(conn, region: str) -> Dict[str, int]:
    """Ensure all documents in a region have embeddings, generating them if missing"""
    try:
        results = {"regulations": 0, "definitions": 0}
        
        # Process regulations without embeddings
        reg_query = f"""
            SELECT law_id, regulations 
            FROM techjam.t_law_{region}_regulations 
            WHERE (embedding IS NULL OR embedding_created_at IS NULL)
            AND regulations IS NOT NULL 
            AND LENGTH(regulations) > 0
        """
        
        reg_rows = await conn.fetch(reg_query)
        
        for row in reg_rows:
            success = await update_regulation_embedding(conn, region, row['law_id'], row['regulations'])
            if success:
                results["regulations"] += 1
        
        # Process definitions without embeddings
        def_query = f"""
            SELECT statute, definitions 
            FROM techjam.t_law_{region}_definitions 
            WHERE (embedding IS NULL OR embedding_created_at IS NULL)
            AND definitions IS NOT NULL 
            AND LENGTH(definitions) > 0
        """
        
        def_rows = await conn.fetch(def_query)
        
        for row in def_rows:
            success = await update_definition_embedding(conn, region, row['statute'], row['definitions'])
            if success:
                results["definitions"] += 1
        
        logger.info(f"Ensured embeddings for {region}: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Failed to ensure embeddings for {region}: {e}")
        return {"regulations": 0, "definitions": 0, "error": str(e)}

class EmbeddingMixin:
    """
    Mixin class to add embedding functionality to database operations
    Can be mixed into CommonQueries or other database classes
    """
    
    async def upsert_regulation_with_embedding(self, data, region: str) -> Dict[str, Any]:
        """Upsert regulation and automatically generate embedding"""
        try:
            # First, perform the regular upsert
            result = await self.upsert_regulations(data, region)
            
            if result.get("success") and data.regulations:
                # Generate and update embedding
                embedding_success = await update_regulation_embedding(
                    self.db, region, data.law_id, data.regulations
                )
                
                result["embedding_generated"] = embedding_success
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to upsert regulation with embedding: {e}")
            return {"success": False, "error": str(e)}
    
    async def upsert_definition_with_embedding(self, data, region: str) -> Dict[str, Any]:
        """Upsert definition and automatically generate embedding"""
        try:
            # First, perform the regular upsert
            result = await self.upsert_definitions(data, region)
            
            if result.get("success") and data.definitions:
                # Generate and update embedding
                embedding_success = await update_definition_embedding(
                    self.db, region, data.statute, data.definitions
                )
                
                result["embedding_generated"] = embedding_success
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to upsert definition with embedding: {e}")
            return {"success": False, "error": str(e)}

# Convenience functions for direct use
async def auto_generate_embeddings_on_insert(conn, region: str, law_id: str = None, statute: str = None):
    """
    Automatically generate embeddings after document insertion
    Call this after inserting new documents
    """
    try:
        if law_id:
            # Generate embedding for specific regulation
            reg_query = f"""
                SELECT regulations 
                FROM techjam.t_law_{region}_regulations 
                WHERE law_id = $1
            """
            result = await conn.fetchrow(reg_query, law_id)
            if result and result['regulations']:
                await update_regulation_embedding(conn, region, law_id, result['regulations'])
        
        if statute:
            # Generate embedding for specific definition
            def_query = f"""
                SELECT definitions 
                FROM techjam.t_law_{region}_definitions 
                WHERE statute = $1 AND region = $2
            """
            result = await conn.fetchrow(def_query, statute, region)
            if result and result['definitions']:
                await update_definition_embedding(conn, region, statute, result['definitions'])
        
    except Exception as e:
        logger.error(f"Auto embedding generation failed: {e}")