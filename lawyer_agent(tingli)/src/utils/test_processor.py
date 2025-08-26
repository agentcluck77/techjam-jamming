"""Test dataset processor for competition CSV output"""

import csv
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
from datetime import datetime
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.compliance_engine import ComplianceEngine

class TestDatasetProcessor:
    """Processes test datasets and generates competition-format CSV output"""
    
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent / "output"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.compliance_engine = ComplianceEngine()
        logger.info(f"Test processor initialized, output dir: {self.output_dir}")
    
    def process_csv_dataset(self, input_csv_path: str, output_csv_path: str = None) -> str:
        """Process a CSV dataset and generate results"""
        input_path = Path(input_csv_path)
        
        if output_csv_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_csv_path = self.output_dir / f"compliance_results_{timestamp}.csv"
        
        logger.info(f"Processing dataset: {input_path}")
        
        # Read input CSV
        try:
            df = pd.read_csv(input_path)
            logger.info(f"Loaded {len(df)} test cases")
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            raise
        
        # Process each row
        results = []
        for idx, row in df.iterrows():
            try:
                logger.info(f"Processing test case {idx + 1}/{len(df)}")
                result = self._process_single_test_case(row, idx)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                # Add error result
                results.append({
                    'test_case_id': idx,
                    'feature_title': str(row.get('title', 'Unknown')),
                    'requires_compliance': False,
                    'confidence': 0.0,
                    'reasoning': f"Processing error: {str(e)}",
                    'matched_regulations': '',
                    'assessment_timestamp': datetime.now().isoformat()
                })
        
        # Save results to CSV
        self._save_results_csv(results, output_csv_path)
        
        logger.info(f"Processing complete. Results saved to: {output_csv_path}")
        return str(output_csv_path)
    
    def _process_single_test_case(self, row: pd.Series, idx: int) -> Dict[str, Any]:
        """Process a single test case row"""
        # Extract feature text from row
        feature_text = self._extract_feature_text(row)
        
        # Perform compliance assessment
        assessment = self.compliance_engine.assess_feature_compliance(feature_text)
        
        # Format regulation matches
        regulation_names = [match.regulation_name for match in assessment.matched_regulations]
        regulation_string = "; ".join(regulation_names) if regulation_names else ""
        
        return {
            'test_case_id': idx,
            'feature_title': assessment.feature_title,
            'requires_compliance': assessment.requires_compliance,
            'confidence': round(assessment.confidence, 3),
            'reasoning': assessment.reasoning,
            'matched_regulations': regulation_string,
            'assessment_timestamp': assessment.assessment_timestamp,
            'total_matches': len(assessment.matched_regulations),
            'top_similarity_score': round(max([m.similarity_score for m in assessment.matched_regulations], default=0.0), 3),
            'compliance_indicators_count': len(assessment.compliance_indicators)
        }
    
    def _extract_feature_text(self, row: pd.Series) -> str:
        """Extract feature text from a CSV row"""
        # Common column names to look for
        text_columns = ['feature_text', 'description', 'title', 'text', 'content', 'feature_description']
        
        # Try to find the main text content
        feature_parts = []
        
        for col_name in text_columns:
            if col_name in row and pd.notna(row[col_name]):
                feature_parts.append(f"{col_name.title()}: {str(row[col_name])}")
        
        # If no standard columns found, use all text columns
        if not feature_parts:
            for col_name, value in row.items():
                if pd.notna(value) and isinstance(value, str) and len(str(value)) > 10:
                    feature_parts.append(f"{col_name}: {str(value)}")
        
        return "\n".join(feature_parts) if feature_parts else "No feature description available"
    
    def _save_results_csv(self, results: List[Dict], output_path: Path):
        """Save results to CSV file in competition format"""
        try:
            df = pd.DataFrame(results)
            df.to_csv(output_path, index=False)
            logger.info(f"Saved {len(results)} results to CSV")
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            raise
    
    def process_json_dataset(self, input_json_path: str, output_csv_path: str = None) -> str:
        """Process a JSON dataset and generate CSV results"""
        input_path = Path(input_json_path)
        
        if output_csv_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_csv_path = self.output_dir / f"compliance_results_{timestamp}.csv"
        
        logger.info(f"Processing JSON dataset: {input_path}")
        
        # Read JSON
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to list if needed
            if isinstance(data, dict):
                if 'features' in data:
                    test_cases = data['features']
                elif 'test_cases' in data:
                    test_cases = data['test_cases']
                else:
                    test_cases = [data]  # Single feature
            elif isinstance(data, list):
                test_cases = data
            else:
                raise ValueError("Unsupported JSON format")
            
            logger.info(f"Loaded {len(test_cases)} test cases from JSON")
            
        except Exception as e:
            logger.error(f"Error reading JSON: {e}")
            raise
        
        # Process each test case
        results = []
        for idx, case in enumerate(test_cases):
            try:
                logger.info(f"Processing test case {idx + 1}/{len(test_cases)}")
                
                # Extract feature text
                if isinstance(case, str):
                    feature_text = case
                elif isinstance(case, dict):
                    feature_text = self._extract_feature_text_from_dict(case)
                else:
                    feature_text = str(case)
                
                # Perform assessment
                assessment = self.compliance_engine.assess_feature_compliance(feature_text)
                
                # Format result
                regulation_names = [match.regulation_name for match in assessment.matched_regulations]
                regulation_string = "; ".join(regulation_names) if regulation_names else ""
                
                result = {
                    'test_case_id': idx,
                    'feature_title': assessment.feature_title,
                    'requires_compliance': assessment.requires_compliance,
                    'confidence': round(assessment.confidence, 3),
                    'reasoning': assessment.reasoning,
                    'matched_regulations': regulation_string,
                    'assessment_timestamp': assessment.assessment_timestamp
                }
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing case {idx}: {e}")
                results.append({
                    'test_case_id': idx,
                    'feature_title': 'Error',
                    'requires_compliance': False,
                    'confidence': 0.0,
                    'reasoning': f"Processing error: {str(e)}",
                    'matched_regulations': '',
                    'assessment_timestamp': datetime.now().isoformat()
                })
        
        # Save results
        self._save_results_csv(results, output_csv_path)
        
        logger.info(f"JSON processing complete. Results saved to: {output_csv_path}")
        return str(output_csv_path)
    
    def _extract_feature_text_from_dict(self, case_dict: Dict) -> str:
        """Extract feature text from a dictionary"""
        text_keys = ['feature_text', 'description', 'title', 'text', 'content']
        
        parts = []
        for key in text_keys:
            if key in case_dict and case_dict[key]:
                parts.append(f"{key.title()}: {case_dict[key]}")
        
        # Add any other string fields
        for key, value in case_dict.items():
            if key not in text_keys and isinstance(value, str) and len(value) > 5:
                parts.append(f"{key}: {value}")
        
        return "\n".join(parts) if parts else str(case_dict)
    
    def create_sample_test_cases(self, output_path: str = None) -> str:
        """Create sample test cases for testing"""
        if output_path is None:
            output_path = self.output_dir / "sample_test_cases.json"
        
        sample_cases = [
            {
                "id": 1,
                "title": "Location-based Content Blocking",
                "description": "Feature reads user location to enforce France's copyright rules (download blocking)",
                "geographic_scope": ["EU", "France"],
                "data_processing": ["location tracking", "user geolocation"]
            },
            {
                "id": 2,
                "title": "Age Gate for Indonesia",
                "description": "Requires age gates specific to Indonesia's Child Protection Law",
                "geographic_scope": ["Indonesia"],
                "target_users": ["minors", "children under 18"]
            },
            {
                "id": 3,
                "title": "US Market Testing",
                "description": "Geofences feature rollout in US for market testing",
                "geographic_scope": ["US"],
                "note": "Business-driven, not legal requirement"
            },
            {
                "id": 4,
                "title": "Korea Video Filter",
                "description": "A video filter feature is available globally except KR",
                "geographic_scope": ["Global except Korea"],
                "note": "Unclear intention, needs human evaluation"
            },
            {
                "id": 5,
                "title": "Content Scanning System",
                "description": "Automated system to detect and report inappropriate content to authorities",
                "technical_requirements": ["image scanning", "CSAM detection", "automated reporting"],
                "geographic_scope": ["US"]
            }
        ]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sample_cases, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created {len(sample_cases)} sample test cases at: {output_path}")
        return str(output_path)