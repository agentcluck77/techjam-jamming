"""Law database loader for processing and storing legal regulations"""

import json
import os
from typing import List, Dict, Tuple
from pathlib import Path
from loguru import logger

class LawLoader:
    """Loads and processes legal regulations from data files"""
    
    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = Path(__file__).parent.parent.parent / "data"
        self.data_path = Path(data_path)
        self.regulations_file = self.data_path / "regulations.json"
        
    def load_regulations(self) -> List[Dict]:
        """Load all regulations from the JSON file"""
        try:
            with open(self.regulations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data['regulations']
        except FileNotFoundError:
            logger.error(f"Regulations file not found: {self.regulations_file}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in regulations file: {e}")
            return []
    
    def extract_text_chunks(self, regulations: List[Dict]) -> List[Tuple[str, Dict]]:
        """Extract text chunks from regulations for embedding"""
        chunks = []
        
        for regulation in regulations:
            reg_id = regulation['id']
            name = regulation['name']
            description = regulation['description']
            
            # Create main regulation chunk
            main_text = f"{name}: {description}"
            chunks.append((main_text, {
                'regulation_id': reg_id,
                'type': 'main',
                'name': name
            }))
            
            # Create chunks for key provisions
            for i, provision in enumerate(regulation['key_provisions']):
                provision_text = f"{name} - Provision {i+1}: {provision}"
                chunks.append((provision_text, {
                    'regulation_id': reg_id,
                    'type': 'provision',
                    'name': name,
                    'provision_index': i
                }))
            
            # Create chunks for compliance indicators
            for i, indicator in enumerate(regulation['compliance_indicators']):
                indicator_text = f"{name} - Compliance Indicator: {indicator}"
                chunks.append((indicator_text, {
                    'regulation_id': reg_id,
                    'type': 'indicator',
                    'name': name,
                    'indicator_index': i
                }))
        
        logger.info(f"Extracted {len(chunks)} text chunks from {len(regulations)} regulations")
        return chunks
    
    def get_regulation_by_id(self, reg_id: str) -> Dict:
        """Get a specific regulation by ID"""
        regulations = self.load_regulations()
        for reg in regulations:
            if reg['id'] == reg_id:
                return reg
        return None
    
    def get_all_regulation_names(self) -> List[str]:
        """Get names of all loaded regulations"""
        regulations = self.load_regulations()
        return [reg['name'] for reg in regulations]
    
    def prepare_embeddings_data(self) -> Tuple[List[str], List[Dict]]:
        """Prepare data for embedding generation"""
        regulations = self.load_regulations()
        chunks = self.extract_text_chunks(regulations)
        
        texts = [chunk[0] for chunk in chunks]
        metadata = [chunk[1] for chunk in chunks]
        
        return texts, metadata