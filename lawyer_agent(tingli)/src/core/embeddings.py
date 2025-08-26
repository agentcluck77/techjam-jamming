"""Vector embedding pipeline using MiniLM-L6-v2"""

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from loguru import logger
import torch
from pathlib import Path

class EmbeddingGenerator:
    """Handles text embedding generation using sentence transformers"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            logger.info(f"Loading model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"Model loaded successfully on device: {self.device}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def encode_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        if not texts:
            logger.warning("Empty text list provided")
            return np.array([])
        
        try:
            logger.info(f"Encoding {len(texts)} texts with batch size {batch_size}")
            embeddings = self.model.encode(
                texts, 
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalize for cosine similarity
            )
            logger.info(f"Generated embeddings shape: {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            raise
    
    def encode_single_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        return self.encode_texts([text])[0]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by the model"""
        return self.model.get_sentence_embedding_dimension()
    
    def similarity_score(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        return float(np.dot(embedding1, embedding2))
    
    def batch_similarity(self, query_embedding: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
        """Calculate similarity scores between query and multiple embeddings"""
        return np.dot(embeddings, query_embedding)

class EmbeddingCache:
    """Cache for storing and retrieving embeddings"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "data" / "embeddings_cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Embedding cache directory: {self.cache_dir}")
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key"""
        return self.cache_dir / f"{cache_key}.npy"
    
    def save_embeddings(self, cache_key: str, embeddings: np.ndarray):
        """Save embeddings to cache"""
        cache_path = self._get_cache_path(cache_key)
        try:
            np.save(cache_path, embeddings)
            logger.info(f"Saved embeddings to cache: {cache_path}")
        except Exception as e:
            logger.error(f"Failed to save embeddings to cache: {e}")
    
    def load_embeddings(self, cache_key: str) -> Optional[np.ndarray]:
        """Load embeddings from cache"""
        cache_path = self._get_cache_path(cache_key)
        try:
            if cache_path.exists():
                embeddings = np.load(cache_path)
                logger.info(f"Loaded embeddings from cache: {cache_path}")
                return embeddings
        except Exception as e:
            logger.error(f"Failed to load embeddings from cache: {e}")
        return None
    
    def cache_exists(self, cache_key: str) -> bool:
        """Check if cache exists for a given key"""
        return self._get_cache_path(cache_key).exists()