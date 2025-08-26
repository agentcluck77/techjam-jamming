"""Compliance reasoning engine that matches features to legal requirements"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from loguru import logger
import json
from datetime import datetime

from .feature_analyzer import FeatureDocument, FeatureAnalyzer, ComplianceIndicator
from ..database.vector_store import VectorStore
from ..database.law_loader import LawLoader

@dataclass
class ComplianceMatch:
    """A match between a feature and legal requirement"""
    regulation_id: str
    regulation_name: str
    matched_text: str
    similarity_score: float
    confidence_score: float
    reasoning: str
    match_type: str  # 'provision', 'indicator', 'main'

@dataclass 
class ComplianceAssessment:
    """Complete compliance assessment for a feature"""
    feature_title: str
    requires_compliance: bool
    confidence: float
    reasoning: str
    matched_regulations: List[ComplianceMatch]
    compliance_indicators: List[ComplianceIndicator]
    assessment_timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'feature_title': self.feature_title,
            'requires_compliance': self.requires_compliance,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'matched_regulations': [
                {
                    'regulation_id': match.regulation_id,
                    'regulation_name': match.regulation_name,
                    'matched_text': match.matched_text,
                    'similarity_score': match.similarity_score,
                    'confidence_score': match.confidence_score,
                    'reasoning': match.reasoning,
                    'match_type': match.match_type
                }
                for match in self.matched_regulations
            ],
            'compliance_indicators': [
                {
                    'text': indicator.text,
                    'confidence': indicator.confidence,
                    'category': indicator.category,
                    'keywords': indicator.keywords
                }
                for indicator in self.compliance_indicators
            ],
            'assessment_timestamp': self.assessment_timestamp
        }

class ComplianceEngine:
    """Main compliance reasoning engine"""
    
    def __init__(self, 
                 vector_store: VectorStore = None,
                 similarity_threshold: float = 0.7,
                 confidence_threshold: float = 0.8):
        
        self.vector_store = vector_store or VectorStore()
        self.similarity_threshold = similarity_threshold
        self.confidence_threshold = confidence_threshold
        self.feature_analyzer = FeatureAnalyzer()
        self.law_loader = LawLoader()
        
        # Initialize vector store if needed
        if not self.vector_store.index_exists():
            logger.info("Building vector index for first time...")
            self.vector_store.build_index()
        else:
            self.vector_store.load_index()
    
    def assess_feature_compliance(self, feature_text: str) -> ComplianceAssessment:
        """Perform complete compliance assessment of a feature"""
        logger.info("Starting compliance assessment")
        
        # Parse feature document
        feature_doc = self.feature_analyzer.parse_document(feature_text)
        logger.info(f"Analyzing feature: {feature_doc.title}")
        
        # Extract compliance indicators
        indicators = self.feature_analyzer.extract_compliance_indicators(feature_doc)
        
        # Create optimized search query
        search_query = self.feature_analyzer.create_search_query(feature_doc, indicators)
        
        # Search for relevant legal requirements
        search_results = self.vector_store.search(
            search_query, 
            k=10,  # Get more results for better analysis
            similarity_threshold=self.similarity_threshold * 0.8  # Lower threshold for search
        )
        
        # Process matches and create compliance assessment
        matches = self._process_search_results(search_results, feature_doc, indicators)
        
        # Make final compliance decision
        requires_compliance, confidence, reasoning = self._make_compliance_decision(
            feature_doc, indicators, matches
        )
        
        assessment = ComplianceAssessment(
            feature_title=feature_doc.title,
            requires_compliance=requires_compliance,
            confidence=confidence,
            reasoning=reasoning,
            matched_regulations=matches,
            compliance_indicators=indicators,
            assessment_timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Assessment complete: Requires compliance = {requires_compliance} (confidence: {confidence:.2f})")
        return assessment
    
    def _process_search_results(self, 
                               search_results: List[Dict], 
                               feature_doc: FeatureDocument,
                               indicators: List[ComplianceIndicator]) -> List[ComplianceMatch]:
        """Process vector search results into compliance matches"""
        matches = []
        seen_regulations = set()
        
        for result in search_results:
            metadata = result['metadata']
            regulation_id = metadata['regulation_id']
            similarity = result['similarity_score']
            
            # Get full regulation info
            regulation = self.law_loader.get_regulation_by_id(regulation_id)
            if not regulation:
                continue
            
            # Calculate confidence based on multiple factors
            confidence = self._calculate_match_confidence(
                result, feature_doc, indicators, regulation
            )
            
            if confidence >= 0.5:  # Minimum confidence threshold
                # Generate reasoning for this match
                reasoning = self._generate_match_reasoning(
                    result, feature_doc, indicators, regulation
                )
                
                match = ComplianceMatch(
                    regulation_id=regulation_id,
                    regulation_name=regulation['name'],
                    matched_text=result['text'],
                    similarity_score=similarity,
                    confidence_score=confidence,
                    reasoning=reasoning,
                    match_type=metadata.get('type', 'unknown')
                )
                matches.append(match)
                seen_regulations.add(regulation_id)
        
        # Sort matches by confidence score
        matches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        logger.info(f"Found {len(matches)} compliance matches across {len(seen_regulations)} regulations")
        return matches[:5]  # Return top 5 matches
    
    def _calculate_match_confidence(self, 
                                  search_result: Dict,
                                  feature_doc: FeatureDocument, 
                                  indicators: List[ComplianceIndicator],
                                  regulation: Dict) -> float:
        """Calculate confidence score for a compliance match"""
        base_similarity = search_result['similarity_score']
        
        # Boost confidence based on indicator alignment
        indicator_boost = 0
        metadata = search_result['metadata']
        
        # Check if search result aligns with detected indicators
        for indicator in indicators:
            # Geographic alignment
            if (indicator.category == 'geographic' and 
                any(geo in search_result['text'].lower() 
                    for geo in ['eu', 'california', 'florida', 'utah', 'us'])):
                indicator_boost += 0.2
            
            # Age-related alignment
            if (indicator.category == 'age_related' and 
                any(age in search_result['text'].lower() 
                    for age in ['minor', 'child', 'age', 'parental'])):
                indicator_boost += 0.2
            
            # Data processing alignment
            if (indicator.category == 'data_processing' and 
                any(data in search_result['text'].lower() 
                    for data in ['data', 'privacy', 'personal'])):
                indicator_boost += 0.15
        
        # Match type weighting
        type_weight = {
            'main': 1.0,
            'provision': 0.9,
            'indicator': 0.8
        }.get(metadata.get('type'), 0.7)
        
        # Calculate final confidence
        confidence = (base_similarity * type_weight + indicator_boost) / (1 + indicator_boost)
        return min(confidence, 1.0)
    
    def _generate_match_reasoning(self, 
                                search_result: Dict,
                                feature_doc: FeatureDocument,
                                indicators: List[ComplianceIndicator],
                                regulation: Dict) -> str:
        """Generate human-readable reasoning for a compliance match"""
        reasons = []
        
        # Similarity-based reasoning
        similarity = search_result['similarity_score']
        if similarity > 0.8:
            reasons.append("Strong semantic similarity to legal text")
        elif similarity > 0.6:
            reasons.append("Moderate semantic similarity to legal text")
        
        # Indicator-based reasoning
        relevant_indicators = [ind for ind in indicators if ind.confidence > 0.6]
        if relevant_indicators:
            indicator_categories = [ind.category for ind in relevant_indicators]
            reasons.append(f"Feature contains {', '.join(set(indicator_categories))} elements")
        
        # Regulation-specific reasoning
        regulation_name = regulation['name']
        if 'dsa' in regulation_name.lower() or 'digital service' in regulation_name.lower():
            if any(cat in ['content_moderation', 'data_processing'] 
                   for cat in [ind.category for ind in indicators]):
                reasons.append("DSA applies to platform content and data processing features")
        
        if 'california' in regulation_name.lower() or 'florida' in regulation_name.lower() or 'utah' in regulation_name.lower():
            if any(cat == 'age_related' for cat in [ind.category for ind in indicators]):
                reasons.append("State minor protection laws triggered by age-related features")
        
        if 'ncmec' in regulation_name.lower():
            if any(cat == 'content_moderation' for cat in [ind.category for ind in indicators]):
                reasons.append("NCMEC reporting required for content processing systems")
        
        return "; ".join(reasons) if reasons else "Regulatory relevance detected through semantic analysis"
    
    def _make_compliance_decision(self, 
                                feature_doc: FeatureDocument,
                                indicators: List[ComplianceIndicator], 
                                matches: List[ComplianceMatch]) -> Tuple[bool, float, str]:
        """Make final decision on whether feature requires compliance logic"""
        
        if not matches:
            return False, 0.1, "No significant regulatory matches found"
        
        # Get top matches
        top_matches = [m for m in matches if m.confidence_score >= 0.6]
        
        if not top_matches:
            return False, 0.3, "Low confidence in regulatory matches"
        
        # High-confidence indicators that strongly suggest compliance needs
        strong_indicators = [ind for ind in indicators if ind.confidence > 0.7]
        
        # Decision logic
        max_match_confidence = max(m.confidence_score for m in top_matches)
        avg_match_confidence = sum(m.confidence_score for m in top_matches) / len(top_matches)
        
        # Strong compliance signals
        if (max_match_confidence > 0.8 and len(top_matches) >= 2):
            confidence = min(0.95, max_match_confidence)
            reasoning = f"Multiple high-confidence regulatory matches found ({len(top_matches)} matches)"
            return True, confidence, reasoning
        
        # Moderate compliance signals with strong indicators
        if (max_match_confidence > 0.7 and len(strong_indicators) >= 2):
            confidence = min(0.85, (max_match_confidence + avg_match_confidence) / 2)
            reasoning = f"Regulatory match combined with strong compliance indicators ({len(strong_indicators)} indicators)"
            return True, confidence, reasoning
        
        # Geographic or age-related features often need compliance
        geographic_match = any('geographic' in ind.category for ind in strong_indicators)
        age_match = any('age_related' in ind.category for ind in strong_indicators)
        
        if (geographic_match or age_match) and max_match_confidence > 0.6:
            confidence = min(0.8, max_match_confidence + 0.1)
            reason_type = "geographic" if geographic_match else "age-related"
            reasoning = f"Feature involves {reason_type} considerations with regulatory match"
            return True, confidence, reasoning
        
        # Uncertain cases
        if max_match_confidence > 0.6:
            confidence = max_match_confidence
            reasoning = f"Moderate regulatory relevance detected, manual review recommended"
            return True, confidence, reasoning
        
        # No compliance needed
        confidence = 1.0 - max_match_confidence
        reasoning = "Feature appears to be primarily business-driven without specific regulatory requirements"
        return False, confidence, reasoning