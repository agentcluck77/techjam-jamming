"""
Lawyer Agent - Phase 1A Implementation
Central coordinator for legal analysis and decision synthesis
"""
from typing import List, Dict, Any
import statistics
from datetime import datetime
import uuid

from ..models import JurisdictionAnalysis, FeatureAnalysisResponse, UserQueryResponse
from .mock_mcps import MockMCPClient
from ..llm_service import llm_client

class LawyerAgent:
    """
    Enhanced central coordinator for legal analysis with dual-mode operation:
    1. Feature compliance analysis (with MCP search)
    2. Direct user query responses (advisory mode)
    """
    
    def __init__(self, mcp_client=None):
        # Use dependency injection for easy testing and team member enhancement
        # If mcp_client is None, MCP functionality is disabled (no mock responses)
        self.mcp_client = mcp_client
    
    async def process_request(self, request_data: Dict[str, Any], request_type: str):
        """Route to appropriate processing method based on request type"""
        if request_type == "feature_description":
            return await self.analyze(request_data)
        elif request_type == "user_query":
            return await self.handle_user_query(request_data)
        else:
            raise ValueError(f"Unknown request type: {request_type}")

    async def handle_user_query(self, query_data: Dict[str, Any]) -> UserQueryResponse:
        """
        Handle direct user queries for legal advice
        Original requirement: "if receive user query: output advice"
        Uses MCP search for legal context, then LLM for advice generation
        """
        user_query = query_data.get("query", "")
        context = query_data.get("context", {})
        
        start_time = datetime.now()
        
        try:
            # Step 1: Search MCPs for relevant legal context (if enabled)
            legal_context_results = []
            if self.mcp_client is not None:
                search_context = {"query": user_query, "context": context}
                legal_context_results = await self.mcp_client.search_for_query(search_context)
            
            # Step 2: Generate advisory response using LLM (with or without MCP context)
            advice_response = await self._generate_legal_advice(
                user_query, context, legal_context_results
            )
            
            end_time = datetime.now()
            
            return UserQueryResponse(
                advice=advice_response.get("advice", ""),
                confidence=advice_response.get("confidence", 0.8),
                sources=advice_response.get("sources", ["Legal knowledge base"]),
                related_jurisdictions=advice_response.get("jurisdictions", []),
                timestamp=end_time
            )
            
        except Exception as e:
            # Fallback to basic LLM response if MCP search fails
            return await self._fallback_user_query_response(user_query, context)

    async def _generate_legal_advice(self, query: str, context: Dict, legal_context: List[Dict]) -> Dict[str, Any]:
        """Generate legal advice using MCP search results and LLM"""
        
        # Compile legal context from MCP search results
        context_text = ""
        sources = []
        jurisdictions = []
        
        for result in legal_context:
            if result and result.get("results"):
                jurisdiction = result.get("jurisdiction", "Unknown")
                jurisdictions.append(jurisdiction)
                
                for search_result in result["results"]:
                    context_text += f"\n{jurisdiction}: {search_result.get('content', '')}"
                    if search_result.get('source_document'):
                        sources.append(f"{jurisdiction} - {search_result['source_document']}")
        
        # Generate advice prompt with or without MCP legal context
        if context_text:
            # With MCP context
            advice_prompt = f"""You are a legal compliance expert for TikTok platform regulations.

User Query: {query}
Additional Context: {context}

Relevant Legal Context from Search:
{context_text}

Provide helpful, practical legal guidance addressing the user's question.
Focus on:
1. Direct answer to their question
2. Specific compliance recommendations
3. Jurisdictional considerations
4. Actionable next steps

Be concise but thorough. Provide specific guidance rather than generic advice.
"""
        else:
            # Without MCP context - general legal knowledge
            advice_prompt = f"""You are a legal compliance expert for TikTok platform regulations.

User Query: {query}
Additional Context: {context}

Since detailed legal database search is not available, provide general compliance guidance based on common regulatory patterns for social media platforms.

Focus on:
1. Direct answer to their question based on general legal principles
2. Common compliance requirements for similar features/situations
3. Major jurisdictional considerations (US, EU, etc.)
4. Actionable next steps including recommendation to consult legal experts

Note: This is general guidance based on common regulatory patterns. Specific legal review is recommended for implementation.
"""
        
        try:
            response = await llm_client.complete(advice_prompt, max_tokens=800, temperature=0.2)
            
            return {
                "advice": response.get("content", "Unable to generate specific advice."),
                "confidence": 0.85 if context_text else 0.6,
                "sources": list(set(sources)) if sources else ["Legal knowledge base"],
                "jurisdictions": list(set(jurisdictions))
            }
            
        except Exception as e:
            return {
                "advice": "I apologize, but I'm unable to provide specific legal advice at this time. Please consult with a legal professional for guidance on compliance matters.",
                "confidence": 0.3,
                "sources": ["System Error"],
                "jurisdictions": []
            }

    async def _fallback_user_query_response(self, query: str, context: Dict) -> UserQueryResponse:
        """Fallback response when MCP search is unavailable"""
        
        try:
            # Basic LLM response without MCP context
            fallback_prompt = f"""You are a legal compliance expert for TikTok platform regulations.

User Query: {query}
Context: {context}

Provide general legal compliance guidance for TikTok features and operations.
Be helpful but note that this is general guidance and specific legal review may be needed.
"""
            
            response = await llm_client.complete(fallback_prompt, max_tokens=600, temperature=0.2)
            
            return UserQueryResponse(
                advice=response.get("content", "Unable to provide guidance at this time."),
                confidence=0.5,
                sources=["General legal knowledge"],
                related_jurisdictions=["General"],
                timestamp=datetime.now()
            )
            
        except Exception:
            return UserQueryResponse(
                advice="I apologize, but I'm unable to provide legal advice at this time. Please consult with a legal professional.",
                confidence=0.1,
                sources=["System Error"],
                related_jurisdictions=[],
                timestamp=datetime.now()
            )

    async def analyze(self, enriched_context: Dict[str, Any]) -> FeatureAnalysisResponse:
        """
        Standard feature compliance analysis path
        Original requirement: "if receive JSON: check compliance for corresponding location"
        """
        
        start_time = datetime.now()
        feature_id = str(uuid.uuid4())
        
        # Get jurisdiction analyses (if MCP is enabled)
        jurisdiction_analyses = []
        if self.mcp_client is not None:
            jurisdiction_analyses = await self.mcp_client.analyze_parallel(enriched_context)
        
        # Synthesize final decision
        final_decision = await self._synthesize_decision(
            enriched_context,
            jurisdiction_analyses,
            feature_id,
            start_time
        )
        
        return final_decision
    
    async def _synthesize_decision(
        self, 
        context: Dict[str, Any], 
        analyses: List[JurisdictionAnalysis],
        feature_id: str,
        start_time: datetime
    ) -> FeatureAnalysisResponse:
        """
        Synthesize jurisdiction analyses into unified decision
        Phase 1A: Simple aggregation rules
        """
        
        if not analyses:
            # Use LLM-based analysis when MCP is disabled
            return await self._create_llm_based_fallback(context, feature_id, start_time)
        
        # Determine overall compliance requirement
        # Rule: If ANY jurisdiction requires compliance, overall compliance is required
        compliance_required = any(analysis.compliance_required for analysis in analyses)
        
        # Calculate overall risk level
        # Rule: Use maximum risk level across jurisdictions
        risk_levels = [analysis.risk_level for analysis in analyses if analysis.risk_level > 0]
        overall_risk_level = max(risk_levels) if risk_levels else 1
        
        # Identify applicable jurisdictions
        applicable_jurisdictions = [
            analysis.jurisdiction 
            for analysis in analyses 
            if analysis.compliance_required
        ]
        
        # Aggregate requirements and implementation steps
        all_requirements = []
        all_implementation_steps = []
        
        for analysis in analyses:
            if analysis.compliance_required:
                all_requirements.extend(analysis.requirements)
                all_implementation_steps.extend(analysis.implementation_steps)
        
        # Remove duplicates while preserving order
        requirements = list(dict.fromkeys(all_requirements))
        implementation_steps = list(dict.fromkeys(all_implementation_steps))
        
        # Calculate confidence score
        # Rule: Average confidence weighted by compliance requirement
        confidence_scores = [
            analysis.confidence 
            for analysis in analyses 
            if analysis.confidence > 0
        ]
        overall_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.5
        
        # Generate reasoning
        reasoning = self._generate_reasoning(analyses, compliance_required, overall_risk_level)
        
        # Calculate analysis time
        end_time = datetime.now()
        analysis_time = (end_time - start_time).total_seconds()
        
        return FeatureAnalysisResponse(
            feature_id=feature_id,
            feature_name=context.get("original_feature", "Unknown Feature"),
            compliance_required=compliance_required,
            risk_level=overall_risk_level,
            applicable_jurisdictions=applicable_jurisdictions,
            requirements=requirements,
            implementation_steps=implementation_steps,
            confidence_score=overall_confidence,
            reasoning=reasoning,
            jurisdiction_details=analyses,
            analysis_time=analysis_time,
            created_at=end_time
        )
    
    def _generate_reasoning(
        self, 
        analyses: List[JurisdictionAnalysis], 
        compliance_required: bool,
        risk_level: int
    ) -> str:
        """Generate human-readable reasoning for the decision"""
        
        if not compliance_required:
            return (
                "No significant compliance requirements identified across analyzed jurisdictions. "
                "Feature appears to have minimal regulatory impact based on current assessment."
            )
        
        # Count jurisdictions requiring compliance
        compliant_jurisdictions = [a for a in analyses if a.compliance_required]
        jurisdiction_names = [a.jurisdiction for a in compliant_jurisdictions]
        
        reasoning_parts = [
            f"Compliance required in {len(jurisdiction_names)} jurisdiction(s): {', '.join(jurisdiction_names)}."
        ]
        
        if risk_level >= 4:
            reasoning_parts.append("High risk level due to potential impact on minors or data handling requirements.")
        elif risk_level >= 3:
            reasoning_parts.append("Moderate risk level requiring careful implementation of regulatory requirements.")
        
        # Add specific jurisdiction insights
        key_concerns = []
        for analysis in compliant_jurisdictions:
            if analysis.jurisdiction.lower() == "utah" and analysis.compliance_required:
                key_concerns.append("Utah Social Media Act restrictions")
            elif analysis.jurisdiction.lower() == "eu" and analysis.compliance_required:
                key_concerns.append("EU transparency and user rights requirements")
        
        if key_concerns:
            reasoning_parts.append(f"Key concerns: {', '.join(key_concerns)}.")
        
        return " ".join(reasoning_parts)
    
    async def _create_llm_based_fallback(
        self, 
        context: Dict[str, Any], 
        feature_id: str, 
        start_time: datetime
    ) -> FeatureAnalysisResponse:
        """
        Create LLM-based legal analysis when MCP is disabled
        Uses the Lawyer Agent's legal expertise without MCP search
        """
        
        # Extract context information
        feature_name = context.get("original_feature", "Unknown Feature")
        expanded_description = context.get("expanded_description", "")
        geographic_implications = context.get("geographic_implications", [])
        feature_category = context.get("feature_category", "General Feature")
        risk_indicators = context.get("risk_indicators", [])
        
        # Create comprehensive legal analysis prompt
        analysis_prompt = f"""You are a senior legal compliance expert specializing in TikTok platform regulations across global jurisdictions.

Analyze this TikTok feature for regulatory compliance requirements:

**Feature Name**: {feature_name}
**Description**: {expanded_description}
**Category**: {feature_category}
**Geographic Context**: {', '.join(geographic_implications) if geographic_implications else 'Not specified'}
**Risk Indicators**: {', '.join(risk_indicators) if risk_indicators else 'None identified'}

Provide a comprehensive compliance analysis in the following JSON format:
{{
    "compliance_required": boolean,
    "risk_level": integer (1-5 scale),
    "applicable_jurisdictions": [list of relevant jurisdictions like "Utah", "EU", "California", "Florida", "Brazil"],
    "requirements": [list of specific regulatory requirements],
    "implementation_steps": [list of actionable implementation steps],
    "reasoning": "detailed explanation of compliance assessment",
    "confidence_score": float (0.0-1.0)
}}

Consider these jurisdiction-specific regulations:
- **Utah**: Social Media Regulation Act (age verification, curfews, parental controls)
- **EU**: Digital Services Act, GDPR (content moderation, data privacy, transparency)
- **California**: COPPA, CCPA, Age-Appropriate Design Code
- **Florida**: Online Protections for Minors Act
- **Brazil**: LGPD, data localization requirements

Focus on:
1. Whether the feature triggers any regulatory requirements
2. Specific compliance obligations in each relevant jurisdiction
3. Risk level based on potential regulatory impact
4. Concrete implementation steps for compliance
5. Confidence in your assessment

Respond ONLY with valid JSON."""

        try:
            # Get LLM analysis
            response = await llm_client.complete(analysis_prompt, max_tokens=1200, temperature=0.1)
            analysis_content = response.get("content", "")
            
            # Parse JSON response (handle markdown code blocks)
            import json
            import re
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', analysis_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = analysis_content.strip()
            
            analysis_data = json.loads(json_str)
            
            end_time = datetime.now()
            analysis_time = (end_time - start_time).total_seconds()
            
            return FeatureAnalysisResponse(
                feature_id=feature_id,
                feature_name=feature_name,
                compliance_required=analysis_data.get("compliance_required", False),
                risk_level=analysis_data.get("risk_level", 1),
                applicable_jurisdictions=analysis_data.get("applicable_jurisdictions", []),
                requirements=analysis_data.get("requirements", []),
                implementation_steps=analysis_data.get("implementation_steps", []),
                confidence_score=analysis_data.get("confidence_score", 0.7),
                reasoning=analysis_data.get("reasoning", "LLM-based legal analysis completed."),
                jurisdiction_details=[],  # No detailed jurisdiction breakdown without MCP
                analysis_time=analysis_time,
                created_at=end_time
            )
            
        except json.JSONDecodeError as e:
            # LLM didn't return valid JSON, try to extract useful information anyway
            return await self._create_text_based_analysis(context, feature_id, start_time, analysis_content)
        except Exception as e:
            # Other errors, fallback to basic analysis 
            return await self._create_basic_fallback(context, feature_id, start_time)

    async def _create_text_based_analysis(
        self,
        context: Dict[str, Any],
        feature_id: str, 
        start_time: datetime,
        llm_text_response: str
    ) -> FeatureAnalysisResponse:
        """Parse non-JSON LLM response to extract useful analysis"""
        
        end_time = datetime.now()
        analysis_time = (end_time - start_time).total_seconds()
        
        feature_name = context.get("original_feature", "Unknown Feature")
        text = llm_text_response.lower()
        
        # Extract compliance and risk information from text
        compliance_required = any(phrase in text for phrase in [
            "compliance required", "regulatory requirements", "must comply", 
            "violation", "regulation applies", "legal requirements"
        ])
        
        # Extract risk level (look for numbers 1-5)
        risk_level = 1
        for i in range(5, 0, -1):
            if f"risk level {i}" in text or f"risk: {i}" in text:
                risk_level = i
                break
        
        if compliance_required and risk_level == 1:
            risk_level = 3  # Default to moderate if compliance required but no explicit level
            
        # Extract jurisdictions mentioned
        jurisdictions = []
        jurisdiction_keywords = ["utah", "eu", "european union", "california", "florida", "brazil"]
        for keyword in jurisdiction_keywords:
            if keyword in text:
                if keyword == "eu" or keyword == "european union":
                    jurisdictions.append("EU")
                else:
                    jurisdictions.append(keyword.title())
        
        # Generate reasoning from LLM text
        reasoning = f"LLM Analysis: {llm_text_response[:300]}..." if len(llm_text_response) > 300 else llm_text_response
        
        return FeatureAnalysisResponse(
            feature_id=feature_id,
            feature_name=feature_name,
            compliance_required=compliance_required,
            risk_level=risk_level,
            applicable_jurisdictions=jurisdictions,
            requirements=[],  # Can't extract detailed requirements from text
            implementation_steps=[],  # Can't extract detailed steps from text
            confidence_score=0.6 if compliance_required else 0.7,
            reasoning=reasoning,
            jurisdiction_details=[],
            analysis_time=analysis_time,
            created_at=end_time
        )

    async def _create_basic_fallback(
        self, 
        context: Dict[str, Any], 
        feature_id: str, 
        start_time: datetime
    ) -> FeatureAnalysisResponse:
        """Basic rule-based fallback if LLM analysis fails"""
        
        end_time = datetime.now()
        analysis_time = (end_time - start_time).total_seconds()
        
        return FeatureAnalysisResponse(
            feature_id=feature_id,
            feature_name=context.get("original_feature", "Unknown Feature"),
            compliance_required=False,
            risk_level=1,
            applicable_jurisdictions=[],
            requirements=[],
            implementation_steps=[],
            confidence_score=0.3,
            reasoning="Analysis failed: Unable to process feature description. Manual legal review recommended.",
            jurisdiction_details=[],
            analysis_time=analysis_time,
            created_at=end_time
        )

# TODO: Team Member 1 - Enhanced version with caching and performance optimization
# class EnhancedLawyerAgent(LawyerAgent):
#     """Enhanced version with caching and advanced decision logic"""
#     
#     def __init__(self, mcp_client, cache_manager=None):
#         super().__init__(mcp_client)
#         self.cache = cache_manager  # Team Member 1 implements Redis caching
#     
#     async def analyze(self, enriched_context: Dict[str, Any]) -> FeatureAnalysisResponse:
#         # TODO: Team Member 1 - Add caching layer
#         # 1. Check cache for similar feature analysis
#         # 2. Use cached results if available and fresh
#         # 3. Cache new results with appropriate TTL
#         # 4. Add performance metrics collection
#         pass
#     
#     def _synthesize_decision(self, ...):
#         # TODO: Team Member 1 - Enhanced decision logic
#         # 1. Conflict resolution between jurisdictions
#         # 2. Weighted confidence scoring
#         # 3. Advanced risk calculation algorithms
#         # 4. Legal precedent consideration
#         pass