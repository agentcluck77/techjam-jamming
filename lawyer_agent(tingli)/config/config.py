"""Configuration settings for the Lawyer Agent"""

import os
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ModelConfig:
    """Configuration for the embedding model"""
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    max_seq_length: int = 512
    device: str = "cpu"  # Change to "cuda" if GPU available

@dataclass
class VectorDBConfig:
    """Configuration for vector database"""
    index_type: str = "faiss"
    dimension: int = 384  # MiniLM-L6-v2 embedding dimension
    similarity_metric: str = "cosine"
    db_path: str = "lawyer_agent/data/law_vectors"

@dataclass
class ComplianceConfig:
    """Configuration for compliance detection"""
    similarity_threshold: float = 0.7
    confidence_threshold: float = 0.8
    max_results: int = 5
    
@dataclass
class RegulationConfig:
    """Configuration for target regulations"""
    target_regulations: List[str] = None
    
    def __post_init__(self):
        if self.target_regulations is None:
            self.target_regulations = [
                "EU Digital Service Act (DSA)",
                "California - Protecting Our Kids from Social Media Addiction Act", 
                "Florida - Online Protections for Minors",
                "Utah Social Media Regulation Act",
                "US - Reporting requirements of providers (NCMEC)"
            ]

@dataclass
class Config:
    """Main configuration class"""
    model: ModelConfig = None
    vector_db: VectorDBConfig = None
    compliance: ComplianceConfig = None
    regulations: RegulationConfig = None
    
    def __post_init__(self):
        if self.model is None:
            self.model = ModelConfig()
        if self.vector_db is None:
            self.vector_db = VectorDBConfig()
        if self.compliance is None:
            self.compliance = ComplianceConfig()
        if self.regulations is None:
            self.regulations = RegulationConfig()

# Global config instance
config = Config()