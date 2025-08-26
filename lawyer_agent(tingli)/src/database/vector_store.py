"""FAISS-based vector database for legal regulations"""

import faiss
import numpy as np
import pickle
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from loguru import logger

from ..core.embeddings import EmbeddingGenerator, EmbeddingCache
from .law_loader import LawLoader

class VectorStore:
    """FAISS-based vector store for legal regulation embeddings"""
    
    def __init__(self, 
                 embedding_dim: int = 384,
                 index_type: str = "flat",
                 store_path: Optional[str] = None):
        
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        
        if store_path is None:
            store_path = Path(__file__).parent.parent.parent / "data" / "vector_store"
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.index = None
        self.metadata = []
        self.texts = []
        
        # File paths
        self.index_path = self.store_path / "faiss_index.bin"
        self.metadata_path = self.store_path / "metadata.pkl"
        self.texts_path = self.store_path / "texts.json"
        
        logger.info(f"Vector store initialized at: {self.store_path}")
    
    def _create_index(self) -> faiss.Index:
        """Create FAISS index based on configuration"""
        if self.index_type == "flat":
            # L2 distance index
            index = faiss.IndexFlatL2(self.embedding_dim)
        elif self.index_type == "cosine":
            # Cosine similarity index (using inner product with normalized vectors)
            index = faiss.IndexFlatIP(self.embedding_dim)
        else:
            logger.warning(f"Unknown index type: {self.index_type}, using flat L2")
            index = faiss.IndexFlatL2(self.embedding_dim)
        
        logger.info(f"Created FAISS index: {type(index).__name__}")
        return index
    
    def build_index(self, force_rebuild: bool = False):
        """Build vector index from legal regulations"""
        if not force_rebuild and self.index_exists():
            logger.info("Vector index already exists, loading from disk")
            self.load_index()
            return
        
        logger.info("Building vector index from scratch")
        
        # Load legal data
        law_loader = LawLoader()
        texts, metadata = law_loader.prepare_embeddings_data()
        
        if not texts:
            logger.error("No texts found to index")
            return
        
        # Generate embeddings
        embedding_generator = EmbeddingGenerator()
        embedding_cache = EmbeddingCache()
        
        cache_key = f"regulations_embeddings_{len(texts)}"
        embeddings = embedding_cache.load_embeddings(cache_key)
        
        if embeddings is None:
            logger.info("Generating new embeddings")
            embeddings = embedding_generator.encode_texts(texts)
            embedding_cache.save_embeddings(cache_key, embeddings)
        else:
            logger.info("Using cached embeddings")
        
        # Create and populate index
        self.index = self._create_index()
        
        # For cosine similarity, normalize embeddings
        if self.index_type == "cosine":
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Add to index
        self.index.add(embeddings.astype('float32'))
        self.metadata = metadata
        self.texts = texts
        
        # Save to disk
        self.save_index()
        
        logger.info(f"Built index with {len(texts)} documents")
    
    def search(self, 
               query_text: str, 
               k: int = 5, 
               similarity_threshold: float = 0.7) -> List[Dict]:
        """Search for similar legal regulations"""
        
        if self.index is None:
            logger.error("Index not built. Call build_index() first")
            return []
        
        # Generate query embedding
        embedding_generator = EmbeddingGenerator()
        query_embedding = embedding_generator.encode_single_text(query_text)
        
        # Normalize for cosine similarity
        if self.index_type == "cosine":
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Search
        scores, indices = self.index.search(
            query_embedding.reshape(1, -1).astype('float32'), k
        )
        
        # Process results
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1:  # No more results
                break
            
            # Convert distance to similarity score
            if self.index_type == "cosine":
                similarity = float(score)  # Inner product score
            else:
                # Convert L2 distance to similarity (rough approximation)
                similarity = 1.0 / (1.0 + float(score))
            
            if similarity >= similarity_threshold:
                result = {
                    'text': self.texts[idx],
                    'metadata': self.metadata[idx],
                    'similarity_score': similarity,
                    'rank': i + 1
                }
                results.append(result)
        
        logger.info(f"Found {len(results)} results above threshold {similarity_threshold}")
        return results
    
    def get_by_regulation_id(self, regulation_id: str) -> List[Dict]:
        """Get all entries for a specific regulation"""
        results = []
        for i, metadata in enumerate(self.metadata):
            if metadata.get('regulation_id') == regulation_id:
                results.append({
                    'text': self.texts[i],
                    'metadata': metadata,
                    'index': i
                })
        return results
    
    def save_index(self):
        """Save index and metadata to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            # Save texts
            with open(self.texts_path, 'w', encoding='utf-8') as f:
                json.dump(self.texts, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved vector store to {self.store_path}")
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
    
    def load_index(self):
        """Load index and metadata from disk"""
        try:
            if not self.index_exists():
                logger.warning("Vector store files not found")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            
            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            # Load texts
            with open(self.texts_path, 'r', encoding='utf-8') as f:
                self.texts = json.load(f)
            
            logger.info(f"Loaded vector store from {self.store_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return False
    
    def index_exists(self) -> bool:
        """Check if saved index exists"""
        return (self.index_path.exists() and 
                self.metadata_path.exists() and 
                self.texts_path.exists())
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        if self.index is None:
            return {"status": "not_built"}
        
        return {
            "status": "ready",
            "total_documents": self.index.ntotal,
            "embedding_dimension": self.embedding_dim,
            "index_type": self.index_type,
            "regulations_count": len(set(m.get('regulation_id', '') for m in self.metadata))
        }