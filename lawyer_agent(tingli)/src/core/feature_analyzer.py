"""Feature analysis module for processing standardized documents"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger
import re

@dataclass
class FeatureDocument:
    """Standardized feature document structure"""
    title: str
    description: str
    user_stories: List[str] = None
    technical_requirements: List[str] = None
    geographic_scope: List[str] = None
    target_users: List[str] = None
    data_processing: List[str] = None
    additional_context: str = ""
    
    def __post_init__(self):
        if self.user_stories is None:
            self.user_stories = []
        if self.technical_requirements is None:
            self.technical_requirements = []
        if self.geographic_scope is None:
            self.geographic_scope = []
        if self.target_users is None:
            self.target_users = []
        if self.data_processing is None:
            self.data_processing = []

@dataclass
class ComplianceIndicator:
    """Individual compliance indicator found in feature"""
    text: str
    confidence: float
    category: str  # 'geographic', 'age_related', 'data_processing', etc.
    keywords: List[str]

class FeatureAnalyzer:
    """Analyzes feature documents for compliance-relevant content"""
    
    def __init__(self):
        self.geographic_keywords = [
            'eu', 'europe', 'european', 'gdpr', 'california', 'ca', 'florida', 'fl', 
            'utah', 'ut', 'us', 'usa', 'united states', 'location', 'geofence', 
            'region', 'country', 'jurisdiction', 'dsa', 'digital service act'
        ]
        
        self.age_keywords = [
            'minor', 'child', 'children', 'kids', 'teen', 'teenager', 'age', 'under 18',
            'under 16', 'under 13', 'parental', 'parent', 'guardian', 'coppa',
            'age verification', 'age gate', 'youth'
        ]
        
        self.data_keywords = [
            'data', 'personal', 'privacy', 'collect', 'process', 'store', 'share',
            'tracking', 'analytics', 'profile', 'behavioral', 'location data',
            'user data', 'personal information'
        ]
        
        self.content_keywords = [
            'content', 'moderation', 'filter', 'csam', 'abuse', 'harmful',
            'inappropriate', 'report', 'flag', 'removal', 'takedown'
        ]
        
        self.addictive_keywords = [
            'notification', 'push', 'alert', 'infinite scroll', 'autoplay',
            'recommendation', 'algorithm', 'feed', 'timeline', 'engagement',
            'addictive', 'habit', 'usage time'
        ]
    
    def parse_document(self, document_text: str) -> FeatureDocument:
        """Parse raw document text into structured format"""
        lines = document_text.strip().split('\n')
        
        title = ""
        description = ""
        user_stories = []
        technical_requirements = []
        geographic_scope = []
        target_users = []
        data_processing = []
        additional_context = ""
        
        current_section = "general"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Section headers
            if line.lower().startswith('title:'):
                title = line[6:].strip()
            elif line.lower().startswith('description:'):
                description = line[12:].strip()
            elif line.lower().startswith('user stories:'):
                current_section = "user_stories"
            elif line.lower().startswith('technical requirements:'):
                current_section = "technical_requirements"
            elif line.lower().startswith('geographic scope:'):
                current_section = "geographic_scope"
            elif line.lower().startswith('target users:'):
                current_section = "target_users"
            elif line.lower().startswith('data processing:'):
                current_section = "data_processing"
            elif line.startswith('- '):
                # Bullet point
                content = line[2:].strip()
                if current_section == "user_stories":
                    user_stories.append(content)
                elif current_section == "technical_requirements":
                    technical_requirements.append(content)
                elif current_section == "geographic_scope":
                    geographic_scope.append(content)
                elif current_section == "target_users":
                    target_users.append(content)
                elif current_section == "data_processing":
                    data_processing.append(content)
            else:
                # General content
                if current_section == "general":
                    additional_context += line + " "
        
        # If no structured format, treat as description
        if not title and not description:
            description = document_text
            title = "Untitled Feature"
        
        return FeatureDocument(
            title=title,
            description=description,
            user_stories=user_stories,
            technical_requirements=technical_requirements,
            geographic_scope=geographic_scope,
            target_users=target_users,
            data_processing=data_processing,
            additional_context=additional_context.strip()
        )
    
    def extract_compliance_indicators(self, feature_doc: FeatureDocument) -> List[ComplianceIndicator]:
        """Extract compliance-relevant indicators from feature document"""
        indicators = []
        
        # Combine all text for analysis
        all_text = f"{feature_doc.title} {feature_doc.description} {feature_doc.additional_context}"
        all_text += " " + " ".join(feature_doc.user_stories + feature_doc.technical_requirements)
        all_text = all_text.lower()
        
        # Geographic indicators
        geographic_matches = self._find_keyword_matches(all_text, self.geographic_keywords)
        if geographic_matches:
            indicators.append(ComplianceIndicator(
                text=f"Geographic scope detected: {', '.join(geographic_matches)}",
                confidence=min(0.9, 0.3 * len(geographic_matches)),
                category="geographic",
                keywords=geographic_matches
            ))
        
        # Age-related indicators
        age_matches = self._find_keyword_matches(all_text, self.age_keywords)
        if age_matches:
            indicators.append(ComplianceIndicator(
                text=f"Age-related features detected: {', '.join(age_matches)}",
                confidence=min(0.9, 0.4 * len(age_matches)),
                category="age_related",
                keywords=age_matches
            ))
        
        # Data processing indicators
        data_matches = self._find_keyword_matches(all_text, self.data_keywords)
        if data_matches:
            indicators.append(ComplianceIndicator(
                text=f"Data processing activities: {', '.join(data_matches)}",
                confidence=min(0.8, 0.3 * len(data_matches)),
                category="data_processing",
                keywords=data_matches
            ))
        
        # Content-related indicators
        content_matches = self._find_keyword_matches(all_text, self.content_keywords)
        if content_matches:
            indicators.append(ComplianceIndicator(
                text=f"Content handling features: {', '.join(content_matches)}",
                confidence=min(0.8, 0.35 * len(content_matches)),
                category="content_moderation",
                keywords=content_matches
            ))
        
        # Addictive design indicators
        addictive_matches = self._find_keyword_matches(all_text, self.addictive_keywords)
        if addictive_matches:
            indicators.append(ComplianceIndicator(
                text=f"Engagement/notification features: {', '.join(addictive_matches)}",
                confidence=min(0.7, 0.25 * len(addictive_matches)),
                category="addictive_design",
                keywords=addictive_matches
            ))
        
        logger.info(f"Extracted {len(indicators)} compliance indicators from feature")
        return indicators
    
    def _find_keyword_matches(self, text: str, keywords: List[str]) -> List[str]:
        """Find keyword matches in text"""
        matches = []
        for keyword in keywords:
            if keyword.lower() in text:
                matches.append(keyword)
        return list(set(matches))  # Remove duplicates
    
    def create_search_query(self, feature_doc: FeatureDocument, indicators: List[ComplianceIndicator]) -> str:
        """Create optimized search query for legal database"""
        query_parts = []
        
        # Add title and description
        query_parts.append(f"Feature: {feature_doc.title}")
        if feature_doc.description:
            query_parts.append(feature_doc.description)
        
        # Add high-confidence indicator keywords
        for indicator in indicators:
            if indicator.confidence > 0.6:
                query_parts.extend(indicator.keywords[:3])  # Top 3 keywords per indicator
        
        # Add specific compliance-relevant content
        if feature_doc.geographic_scope:
            query_parts.extend(feature_doc.geographic_scope)
        
        query = " ".join(query_parts)
        logger.debug(f"Generated search query: {query[:200]}...")
        return query
    
    def summarize_feature(self, feature_doc: FeatureDocument) -> str:
        """Create a concise summary of the feature for reasoning"""
        summary_parts = [f"Feature: {feature_doc.title}"]
        
        if feature_doc.description:
            summary_parts.append(f"Description: {feature_doc.description}")
        
        if feature_doc.user_stories:
            summary_parts.append(f"User Stories: {'; '.join(feature_doc.user_stories[:2])}")
        
        if feature_doc.geographic_scope:
            summary_parts.append(f"Geographic Scope: {', '.join(feature_doc.geographic_scope)}")
        
        return " | ".join(summary_parts)