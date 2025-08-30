#!/usr/bin/env python3
"""
ChromaDB Setup Script for Requirements MCP
Initializes the ChromaDB collection with sample data
"""
import chromadb
import os
import logging
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_chromadb():
    """Initialize ChromaDB collection with sample data"""
    
    # ChromaDB configuration
    CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))
    
    try:
        # Initialize ChromaDB client
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        
        # Load sentence transformer model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create collection
        collection = client.get_or_create_collection(
            name="requirements_collection",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Sample data to initialize the collection
        sample_chunks = [
            {
                "id": "sample-001",
                "content": "Live Shopping Platform Requirements - Real-time payment processing with multiple currencies, age verification for purchases under 18 years, inventory management with real-time synchronization",
                "metadata": {
                    "source_document": "TikTok_Creator_Studio_v2.1_Live_Shopping.md",
                    "document_type": "prd",
                    "pdf_id": "sample-prd-001",
                    "chunk_index": 0,
                    "total_chunks": 3
                }
            },
            {
                "id": "sample-002", 
                "content": "Compliance Requirements - GDPR compliance for EU users data retention (max 180 days), California CCPA privacy requirements, Utah Social Media Act age verification, Payment Card Industry (PCI) compliance",
                "metadata": {
                    "source_document": "TikTok_Creator_Studio_v2.1_Live_Shopping.md",
                    "document_type": "prd",
                    "pdf_id": "sample-prd-001",
                    "chunk_index": 1,
                    "total_chunks": 3
                }
            },
            {
                "id": "sample-003",
                "content": "Technical Requirements - 99.9% uptime during live sessions, Sub-second payment processing latency, Support for 50,000+ concurrent viewers, Multi-language support",
                "metadata": {
                    "source_document": "TikTok_Creator_Studio_v2.1_Live_Shopping.md",
                    "document_type": "prd", 
                    "pdf_id": "sample-prd-001",
                    "chunk_index": 2,
                    "total_chunks": 3
                }
            }
        ]
        
        # Check if collection already has data
        existing_count = collection.count()
        logger.info(f"Collection currently has {existing_count} items")
        
        if existing_count == 0:
            # Generate embeddings
            documents = [chunk["content"] for chunk in sample_chunks]
            embeddings = model.encode(documents).tolist()
            
            # Add to collection
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=[chunk["metadata"] for chunk in sample_chunks],
                ids=[chunk["id"] for chunk in sample_chunks]
            )
            
            logger.info(f"Initialized ChromaDB collection with {len(sample_chunks)} sample chunks")
        else:
            logger.info("Collection already has data, skipping initialization")
            
        # Verify setup
        final_count = collection.count()
        logger.info(f"ChromaDB setup complete. Collection has {final_count} total items")
        
        return True
        
    except Exception as e:
        logger.error(f"ChromaDB setup failed: {e}")
        return False

if __name__ == "__main__":
    success = setup_chromadb()
    if success:
        print("✅ ChromaDB setup completed successfully")
    else:
        print("❌ ChromaDB setup failed")
        exit(1)