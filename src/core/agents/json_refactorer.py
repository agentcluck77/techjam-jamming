"""
JSON Refactorer Agent - Phase 1A Implementation
Expands TikTok terminology and enriches feature context for legal analysis
"""
import json
from typing import Dict, Any, List
from pathlib import Path
from ..models import EnrichedContext
from ..llm_service import llm_client

class JSONRefactorer:
    """
    Phase 1A: Basic terminology expansion with hardcoded mappings
    Team Member 1 will enhance with LLM-powered context inference
    """
    
    def __init__(self):
        # Load hardcoded terminology database
        self.terminology_path = Path(__file__).parent.parent.parent.parent / "data" / "terminology.json"
        self.terminology = self._load_terminology()
    
    def _load_terminology(self) -> Dict[str, Any]:
        """Load terminology mappings from JSON file"""
        try:
            with open(self.terminology_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback if file not found
            return {
                "tiktok_terminology": {
                    "ASL": "American Sign Language",
                    "jellybean": "feature component",
                    "Creator Fund": "monetization program",
                    "LIVE": "live streaming"
                },
                "geographic_mappings": {
                    "US": ["United States", "America"],
                    "EU": ["Europe", "European Union"]
                },
                "feature_categories": {
                    "social_features": ["messaging", "following", "sharing"]
                },
                "risk_indicators": {
                    "high_risk": ["data collection", "minors", "payment processing"]
                }
            }
    
    async def process(self, raw_input: Dict[str, Any], retry_count: int = 0) -> EnrichedContext:
        """
        Process raw feature input with completeness validation and retry logic
        Enhanced to match original requirements: "if any important feature requirements were removed"
        """
        
        # Extract basic info
        feature_name = raw_input.get("name", "")
        feature_description = raw_input.get("description", "")
        geographic_context = raw_input.get("geographic_context", "") or ""
        
        # Always do basic processing first
        expanded_description = self._expand_terminology(feature_description)
        terminology_expansions = self._identify_expansions(feature_description)
        geographic_implications = self._infer_geography(
            feature_description + " " + geographic_context
        )
        feature_category = self._categorize_feature(expanded_description)
        risk_indicators = self._identify_risks(expanded_description)
        
        processing_notes = f"Phase 1A: Basic terminology expansion applied to {feature_name}"
        
        # Use LLM-based analysis if available, otherwise fallback to keyword matching
        if llm_client.available_providers:
            try:
                llm_result = await self._llm_based_analysis(
                    feature_name, feature_description, geographic_context, retry_count
                )
                
                # Use LLM results as primary analysis with data type validation
                if llm_result:
                    expanded_description = llm_result.get("expanded_description", expanded_description)
                    geographic_implications = llm_result.get("geographic_implications", geographic_implications)
                    
                    # Fix feature_category if it's returned as a list
                    llm_category = llm_result.get("feature_category", feature_category)
                    if isinstance(llm_category, list):
                        # Take the first/most relevant category
                        feature_category = llm_category[0] if llm_category else feature_category
                    else:
                        feature_category = llm_category
                    
                    risk_indicators = llm_result.get("risk_indicators", risk_indicators)
                    terminology_expansions = llm_result.get("terminology_expansions", terminology_expansions)
                    processing_notes = f"LLM-based analysis applied to {feature_name}"
                
            except Exception as e:
                # Fallback to keyword-based processing if LLM fails
                processing_notes += f" (LLM analysis failed, using keyword fallback: {str(e)})"
        
        # Create initial result
        enriched_context = EnrichedContext(
            original_feature=feature_name,
            expanded_description=expanded_description,
            geographic_implications=list(set(geographic_implications)),
            feature_category=feature_category,
            risk_indicators=list(set(risk_indicators)),
            terminology_expansions=terminology_expansions,
            processing_notes=processing_notes
        )
        
        # Completeness validation - original requirement check
        if not self._is_complete(enriched_context) and retry_count < 2:
            processing_notes += f" (Retry {retry_count + 1} - incomplete extraction detected)"
            # Retry with additional prompting for missing elements
            return await self.process(raw_input, retry_count + 1)
        
        return enriched_context
    
    def _is_complete(self, enriched_context: EnrichedContext) -> bool:
        """
        Validate completeness of enriched context
        Original requirement: "if any important feature requirements were removed"
        """
        
        # Check for required fields
        required_fields = [
            enriched_context.expanded_description,
            enriched_context.feature_category,
            enriched_context.geographic_implications,
            enriched_context.risk_indicators
        ]
        
        # Must have non-empty values for critical fields
        if not all(field for field in required_fields):
            return False
            
        # Must have at least one risk indicator or geographic implication
        if not enriched_context.risk_indicators and not enriched_context.geographic_implications:
            return False
            
        # Must have meaningful expanded description (more than just the original)
        if len(enriched_context.expanded_description) <= len(enriched_context.original_feature) + 10:
            return False
            
        return True
    
    def _expand_terminology(self, text: str) -> str:
        """Expand TikTok jargon to legal-friendly language"""
        expanded_text = text
        
        for term, expansion in self.terminology["tiktok_terminology"].items():
            # Case-insensitive replacement
            expanded_text = expanded_text.replace(term, f"{term} ({expansion})")
        
        return expanded_text
    
    def _identify_expansions(self, text: str) -> Dict[str, str]:
        """Identify which terms were expanded"""
        expansions = {}
        
        for term, expansion in self.terminology["tiktok_terminology"].items():
            if term.lower() in text.lower():
                expansions[term] = expansion
        
        return expansions
    
    def _infer_geography(self, text: str) -> List[str]:
        """Infer geographic implications from text"""
        implications = []
        text_lower = text.lower()
        
        # Check for explicit geographic mentions
        for region, keywords in self.terminology["geographic_mappings"].items():
            if any(keyword.lower() in text_lower for keyword in keywords):
                implications.append(region)
        
        # Default assumptions for Phase 1A
        if not implications:
            if "global" in text_lower or "worldwide" in text_lower:
                implications = ["US", "EU", "Brazil"]  # Major markets
            else:
                implications = ["US"]  # Default to US market
        
        return implications
    
    def _categorize_feature(self, text: str) -> str:
        """Categorize feature based on description"""
        text_lower = text.lower()
        
        # Check each category for keyword matches
        for category, keywords in self.terminology["feature_categories"].items():
            if any(keyword in text_lower for keyword in keywords):
                return category.replace("_", " ").title()
        
        # Default category
        return "General Feature"
    
    def _identify_risks(self, text: str) -> List[str]:
        """Identify potential compliance risk indicators"""
        risks = []
        text_lower = text.lower()
        
        # Check for risk indicators
        for risk_level, indicators in self.terminology["risk_indicators"].items():
            for indicator in indicators:
                if indicator.lower() in text_lower:
                    risks.append(indicator)
        
        return list(set(risks))  # Remove duplicates
    
    async def _llm_based_analysis(self, feature_name: str, feature_description: str, 
                                 geographic_context: str, retry_count: int = 0) -> Dict[str, Any]:
        """
        Comprehensive LLM-based feature analysis replacing keyword matching
        Uses LLM to understand complex features and their regulatory implications
        """
        
        retry_instruction = ""
        if retry_count > 0:
            retry_instruction = f"""
RETRY ATTEMPT {retry_count}: The previous analysis was incomplete. Please ensure:
- Expanded description is comprehensive with legal context
- At least 2-3 relevant jurisdictions are identified
- Multiple specific compliance risks are listed  
- Feature category accurately reflects regulatory scope
- TikTok terminology is properly expanded
"""

        prompt = f"""You are an expert legal compliance analyst specializing in TikTok platform regulations and social media compliance.

Analyze this TikTok feature for regulatory implications:

**Feature Name**: {feature_name}
**Description**: {feature_description}
**Geographic Context**: {geographic_context or "Global/Not specified"}
{retry_instruction}

Provide comprehensive analysis in JSON format:
{{
    "expanded_description": "Detailed description with legal context and regulatory implications",
    "geographic_implications": ["Utah", "EU", "California", "Florida", "Brazil"],
    "feature_category": "Content Moderation",
    "risk_indicators": ["content filtering", "user safety", "transparency requirements"],
    "terminology_expansions": {{"LCP": "Legal Compliance Protocol", "ShadowMode": "Testing deployment mode"}}
}}

CRITICAL: Ensure these exact data types:
- expanded_description: STRING (not array)
- geographic_implications: ARRAY of strings  
- feature_category: SINGLE STRING (pick the most relevant: "Content Moderation", "Commerce", "Data Processing", "Social Features", or "Safety")
- risk_indicators: ARRAY of strings
- terminology_expansions: OBJECT with string key-value pairs

Analysis Guidelines:
1. **TikTok Terminology**: Expand any TikTok-specific jargon (ASL→American Sign Language, jellybean→feature component, LIVE→live streaming, etc.)
2. **Content Moderation**: Features involving content restrictions, filtering, or moderation trigger EU DSA and transparency requirements
3. **Minor Protection**: Any feature accessible to users under 18 triggers Utah, Florida minor protection laws
4. **Data Processing**: Features collecting/processing data trigger GDPR (EU), CCPA (California), LGPD (Brazil)
5. **Commerce**: Payment processing, shopping features trigger financial regulations and minor protection
6. **Geographic Scope**: Infer jurisdictions based on feature type and scope

Specific Focus Areas:
- Content moderation and filtering → EU, US transparency requirements
- Payment/commerce features → Minor protection laws (Utah, Florida)
- Data collection/processing → Privacy laws (EU GDPR, California CCPA, Brazil LGPD)
- Social interactions → Platform liability and safety requirements
- Age-sensitive features → Child protection regulations across jurisdictions

Provide detailed, accurate analysis. Respond ONLY with valid JSON."""

        try:
            response = await llm_client.complete(prompt, max_tokens=1200, temperature=0.1)
            content = response.get("content", "")
            
            # Parse JSON response (handle markdown code blocks)
            import json
            import re
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content.strip()
                
            analysis_data = json.loads(json_str)
            return analysis_data
            
        except json.JSONDecodeError:
            # LLM didn't return valid JSON, return None to fallback
            return None
        except Exception as e:
            # Other errors, return None to fallback
            return None

# TODO: Team Member 1 - Enhance with LLM integration
# class EnhancedJSONRefactorer(JSONRefactorer):
#     """Enhanced version with LLM-powered context inference"""
#     
#     def __init__(self, llm_client):
#         super().__init__()
#         self.llm_client = llm_client  # Team Member 1 implements
#     
#     async def process(self, raw_input: Dict[str, Any]) -> EnrichedContext:
#         # TODO: Team Member 1 - Add LLM-powered analysis
#         # 1. Use LLM to understand feature context beyond keywords
#         # 2. Intelligent geographic inference
#         # 3. Contextual risk assessment
#         pass