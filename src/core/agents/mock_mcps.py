"""
Mock MCP Responses - Phase 1A Implementation
Provides static responses for testing until Team Member 1 implements real HTTP clients
"""
import json
import asyncio
from typing import Dict, Any, List
from pathlib import Path
from ..models import JurisdictionAnalysis

class MockMCPClient:
    """
    Mock MCP client that returns static responses for testing
    Team Member 1 will replace this with real HTTP clients
    """
    
    def __init__(self):
        # Load mock responses
        self.mock_data_path = Path(__file__).parent.parent.parent.parent / "data" / "mock_responses.json"
        self.mock_responses = self._load_mock_responses()
    
    def _load_mock_responses(self) -> Dict[str, Any]:
        """Load mock MCP responses from JSON file"""
        try:
            with open(self.mock_data_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback responses if file not found
            return {
                "utah": {
                    "jurisdiction": "Utah",
                    "applicable_regulations": ["Utah Social Media Regulation Act"],
                    "compliance_required": True,
                    "risk_level": 4,
                    "requirements": ["Age verification required"],
                    "implementation_steps": ["Implement ID verification"],
                    "confidence": 0.85,
                    "reasoning": "Feature may affect minors",
                    "analysis_time": 0.5
                }
            }
    
    async def analyze_feature(self, jurisdiction: str, feature_context: Dict[str, Any]) -> JurisdictionAnalysis:
        """
        Analyze feature for specific jurisdiction
        Phase 1A: Returns static mock responses
        """
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Get mock response for jurisdiction
        mock_data = self.mock_responses.get(jurisdiction.lower())
        if not mock_data:
            # Default response for unknown jurisdictions
            mock_data = {
                "jurisdiction": jurisdiction.title(),
                "applicable_regulations": [],
                "compliance_required": False,
                "risk_level": 1,
                "requirements": [],
                "implementation_steps": [],
                "confidence": 0.5,
                "reasoning": f"No specific regulations identified for {jurisdiction}",
                "analysis_time": 0.1
            }
        
        # Apply basic context-aware modifications
        modified_response = self._contextualize_response(mock_data, feature_context)
        
        return JurisdictionAnalysis(**modified_response)
    
    async def analyze_parallel(self, feature_context: Dict[str, Any]) -> List[JurisdictionAnalysis]:
        """
        Execute parallel analysis across all jurisdictions
        Phase 1A: Sequential execution of mock responses
        """
        
        jurisdictions = ["utah", "eu", "california", "florida", "brazil"]
        results = []
        
        # Phase 1A: Sequential for simplicity
        # Team Member 1 will implement true parallel execution
        for jurisdiction in jurisdictions:
            try:
                analysis = await self.analyze_feature(jurisdiction, feature_context)
                results.append(analysis)
            except Exception as e:
                # Continue with other jurisdictions on error
                print(f"Mock analysis failed for {jurisdiction}: {e}")
                continue
        
        return results
    
    def _contextualize_response(self, base_response: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply basic context-aware modifications to mock responses
        Phase 1A: Simple keyword-based adjustments
        """
        
        response = base_response.copy()
        
        # Get feature info from context
        feature_category = context.get("feature_category", "").lower()
        risk_indicators = context.get("risk_indicators", [])
        geographic_implications = context.get("geographic_implications", [])
        
        # Adjust risk level based on context
        if any("minor" in indicator.lower() or "children" in indicator.lower() 
               for indicator in risk_indicators):
            response["risk_level"] = min(5, response["risk_level"] + 1)
            if response["jurisdiction"].lower() in ["utah", "florida"]:
                response["compliance_required"] = True
        
        if "payment" in " ".join(risk_indicators).lower():
            response["risk_level"] = min(5, response["risk_level"] + 1)
        
        # Adjust based on feature category
        if "commerce" in feature_category:
            response["risk_level"] = min(5, response["risk_level"] + 1)
        
        # Geographic relevance
        jurisdiction_lower = response["jurisdiction"].lower()
        if "eu" in jurisdiction_lower or "european" in jurisdiction_lower:
            if "EU" not in geographic_implications:
                response["confidence"] = max(0.3, response["confidence"] - 0.2)
        
        # Add contextual reasoning
        original_reasoning = response["reasoning"]
        context_notes = []
        
        if risk_indicators:
            context_notes.append(f"Risk indicators: {', '.join(risk_indicators[:3])}")
        
        if context_notes:
            response["reasoning"] = f"{original_reasoning} Context: {'; '.join(context_notes)}"
        
        return response
    
    async def search_for_query(self, query_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Mock search for user queries across all jurisdictions
        Returns search results for legal context retrieval
        """
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        query = query_context.get("query", "").lower()
        context = query_context.get("context", {})
        
        # Mock search responses based on query content
        mock_search_results = []
        jurisdictions = ["utah", "eu", "california", "florida", "brazil"]
        
        for jurisdiction in jurisdictions:
            # Generate contextual search results based on query
            search_result = self._generate_mock_search_result(jurisdiction, query)
            if search_result:
                mock_search_results.append(search_result)
        
        return mock_search_results
    
    def _generate_mock_search_result(self, jurisdiction: str, query: str) -> Dict[str, Any]:
        """Generate mock search results based on query content and jurisdiction"""
        
        # Define jurisdiction-specific content snippets
        content_snippets = {
            "utah": {
                "age": "Utah Social Media Regulation Act requires age verification systems for users under 18. Platforms must implement robust ID verification and obtain parental consent for minors.",
                "verification": "Age verification in Utah must use government-issued identification or other reliable methods. Parental consent is required before minors can create accounts.",
                "curfew": "Utah law mandates curfew restrictions for minors between 10:30 PM and 6:30 AM. Social media platforms must enforce these time-based access restrictions.",
                "default": "Utah has comprehensive social media regulations focusing on minor protection, age verification, and parental oversight requirements."
            },
            "eu": {
                "content": "EU Digital Services Act requires content moderation policies, transparency reporting, and user appeals processes for content removal decisions.",
                "moderation": "Content moderation under DSA must include clear community guidelines, automated detection systems, and human review processes for appeals.",
                "transparency": "EU platforms must provide transparency reports on content moderation actions, including removal statistics and policy enforcement metrics.",
                "default": "EU Digital Services Act establishes comprehensive platform liability, content moderation requirements, and user protection measures."
            },
            "california": {
                "age": "California COPPA compliance requires enhanced privacy protections for users under 13, including parental consent for data collection and processing.",
                "privacy": "California privacy laws mandate data collection limitations, user consent requirements, and data subject rights including access and deletion.",
                "children": "Age-appropriate design requirements in California focus on child safety, data minimization, and privacy-by-design principles.",
                "default": "California has strict privacy and child protection regulations including COPPA compliance and age-appropriate design requirements."
            },
            "florida": {
                "minor": "Florida Online Protections for Minors Act requires parental oversight capabilities and content filtering for users under 18.",
                "parental": "Florida law mandates parental access to minor accounts, including activity monitoring and content restriction capabilities.",
                "filtering": "Content filtering requirements in Florida include harmful content detection and age-appropriate content curation systems.",
                "default": "Florida regulations focus on parental control requirements, content filtering, and minor protection in online platforms."
            },
            "brazil": {
                "data": "Brazil LGPD requires data localization for Brazilian user data and explicit consent for data processing activities.",
                "localization": "Data localization in Brazil mandates that personal data of Brazilian residents be stored and processed within Brazilian territory.",
                "consent": "LGPD consent requirements include clear, specific, and informed consent for data collection and processing purposes.",
                "default": "Brazil LGPD and data localization laws require local data storage, explicit consent, and comprehensive privacy protections."
            }
        }
        
        # Find relevant content based on query keywords
        jurisdiction_content = content_snippets.get(jurisdiction.lower(), {})
        selected_content = jurisdiction_content.get("default", "No relevant information found.")
        
        # Check for keyword matches
        for keyword, content in jurisdiction_content.items():
            if keyword in query and keyword != "default":
                selected_content = content
                break
        
        # Create mock search result
        return {
            "jurisdiction": jurisdiction.title(),
            "results": [
                {
                    "chunk_id": f"{jurisdiction}_query_chunk_001",
                    "source_document": f"{jurisdiction.title()} Legal Regulation Database",
                    "content": selected_content,
                    "relevance_score": 0.85 if any(kw in query for kw in jurisdiction_content.keys()) else 0.6,
                    "metadata": {
                        "document_type": "regulation",
                        "chunk_index": 1,
                        "character_start": 0,
                        "character_end": len(selected_content)
                    }
                }
            ],
            "total_results": 1,
            "search_time": 0.1
        }

# TODO: Team Member 1 - Replace with real HTTP client
# class RealMCPClient:
#     """Real MCP client for HTTP communication with jurisdiction services"""
#     
#     def __init__(self, service_config: Dict[str, Dict]):
#         self.services = service_config
#     
#     async def analyze_feature(self, jurisdiction: str, feature_context: Dict[str, Any]) -> JurisdictionAnalysis:
#         # TODO: Team Member 1 - Implement HTTP calls to MCP services
#         # 1. Make async HTTP POST to jurisdiction MCP
#         # 2. Handle timeouts and retries
#         # 3. Parse response into JurisdictionAnalysis model
#         # 4. Add error handling for service failures
#         pass
#     
#     async def analyze_parallel(self, feature_context: Dict[str, Any]) -> List[JurisdictionAnalysis]:
#         # TODO: Team Member 1 - Implement true parallel execution
#         # 1. Use asyncio.gather for concurrent HTTP calls
#         # 2. Handle partial failures gracefully
#         # 3. Add circuit breaker pattern for reliability
#         pass