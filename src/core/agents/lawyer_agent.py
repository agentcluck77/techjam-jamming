"""
Lawyer Agent - Phase 1A Implementation
Central coordinator for legal analysis and decision synthesis
"""
from typing import List, Dict, Any
import statistics
from datetime import datetime
import uuid
import json
import re

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
        self.max_llm_retries = 3  # Maximum retries for LLM parsing
    
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
    
    async def handle_enriched_query(self, enriched_context: Dict[str, Any]) -> UserQueryResponse:
        """
        Handle user queries that have been processed through JSON Refactorer
        Uses enriched context for better legal analysis
        """
        
        # Extract original query information from enriched context
        query_info = {
            "query": enriched_context.get("expanded_description", ""),
            "context": {
                "geographic_implications": enriched_context.get("geographic_implications", []),
                "risk_indicators": enriched_context.get("risk_indicators", []),
                "feature_category": enriched_context.get("feature_category", "")
            }
        }
        
        # Process as enhanced user query with enriched context
        return await self.handle_user_query(query_info)

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

    async def analyze(self, enriched_context: Dict[str, Any], user_interaction_callback=None) -> FeatureAnalysisResponse:
        """
        LLM-driven feature compliance analysis with dynamic MCP reasoning
        Uses iterative MCP calling based on LLM reasoning decisions
        Supports interactive clarification for ambiguous features
        """
        
        start_time = datetime.now()
        feature_id = str(uuid.uuid4())
        
        # Use reasoning-based MCP orchestration if MCP client available
        if self.mcp_client is not None:
            jurisdiction_analyses = await self._analyze_with_interactive_reasoning(
                enriched_context, user_interaction_callback
            )
        else:
            jurisdiction_analyses = []
        
        # Synthesize final decision
        final_decision = await self._synthesize_decision(
            enriched_context,
            jurisdiction_analyses,
            feature_id,
            start_time
        )
        
        return final_decision
    
    async def _analyze_with_interactive_reasoning(self, enriched_context: Dict[str, Any], user_callback=None) -> List[JurisdictionAnalysis]:
        """
        Enhanced reasoning with interactive user clarification support
        Handles both pre-analysis and mid-analysis clarification requests
        """
        
        # Pre-analysis ambiguity detection
        if user_callback:
            enriched_context = await self._detect_and_resolve_ambiguity_pre_analysis(
                enriched_context, user_callback
            )
        
        return await self._analyze_with_reasoning(enriched_context, user_callback)
    
    async def _detect_and_resolve_ambiguity_pre_analysis(self, enriched_context: Dict[str, Any], user_callback) -> Dict[str, Any]:
        """
        Pre-analysis ambiguity detection and resolution
        Checks for unclear geographic scope before starting MCP analysis
        """
        
        # Check for ambiguity triggers
        geographic_implications = enriched_context.get("geographic_implications", [])
        feature_description = enriched_context.get("expanded_description", "")
        
        # Get available jurisdictions dynamically from MCP client
        available_jurisdictions = await self._get_available_jurisdictions()
        known_jurisdiction_names = [j.lower() for j in available_jurisdictions] if available_jurisdictions else []
        
        is_ambiguous = (
            not geographic_implications or  # Empty geographic implications
            geographic_implications == ["US"] or  # Generic US
            len(feature_description) < 50 or  # Very short description
            not any(geo.lower() in known_jurisdiction_names for geo in geographic_implications) if known_jurisdiction_names else True  # No recognized jurisdictions
        )
        
        if is_ambiguous:
            # Get available jurisdictions for options
            available_jurisdictions = await self._get_available_jurisdictions()
            
            # Create dynamic options
            dynamic_options = ["Global (all regions)"]
            if available_jurisdictions:
                dynamic_options.extend([f"{jurisdiction} only" for jurisdiction in available_jurisdictions])
            dynamic_options.append("Multiple specific regions")
            
            # Ask for geographic clarification
            clarification_question = {
                "type": "geographic_scope",
                "question": f"The geographic scope for feature '{enriched_context.get('original_feature', 'Unknown')}' is unclear. Is this feature being deployed globally or to specific regions?",
                "options": dynamic_options,
                "available_jurisdictions": available_jurisdictions,
                "context": {
                    "feature": enriched_context.get("original_feature", "Unknown"),
                    "description": enriched_context.get("expanded_description", "")[:200] + "..." if len(enriched_context.get("expanded_description", "")) > 200 else enriched_context.get("expanded_description", ""),
                    "current_geographic_implications": geographic_implications
                }
            }
            
            # Get user response
            user_response = await user_callback(clarification_question)
            
            # Update enriched context with user clarification
            enriched_context = await self._incorporate_geographic_clarification(
                enriched_context, user_response, user_callback
            )
        
        return enriched_context
    
    async def _incorporate_geographic_clarification(self, enriched_context: Dict[str, Any], user_response: str, user_callback) -> Dict[str, Any]:
        """
        Incorporate user's geographic clarification into enriched context
        Handles follow-up questions for unclear responses
        """
        
        new_geographic_implications = []
        
        # Use LLM to intelligently parse the response
        available_jurisdictions = await self._get_available_jurisdictions()
        if not available_jurisdictions:
            available_jurisdictions = ["Utah", "EU", "California", "Florida", "Brazil"]
            
        # Check if this is a global deployment request
        is_global = await self._is_global_deployment_request(user_response)
        if is_global:
            new_geographic_implications = available_jurisdictions
            
        elif await self._is_multiple_regions_request(user_response):
            # Ask follow-up for specific regions
            available_jurisdictions = await self._get_available_jurisdictions()
            followup_question = {
                "type": "specific_regions",
                "question": "Which specific regions will this feature be deployed to? (Select all that apply)",
                "options": available_jurisdictions,
                "available_jurisdictions": available_jurisdictions,
                "multiple_select": True,
                "context": {"previous_response": user_response}
            }
            
            specific_regions = await user_callback(followup_question)
            new_geographic_implications = await self._parse_multiple_regions(specific_regions)
            
        else:
            # First try to parse response against available jurisdictions
            parsed_jurisdictions = await self._parse_jurisdiction_response(
                user_response, await self._get_available_jurisdictions()
            )
            
            if parsed_jurisdictions:
                new_geographic_implications = parsed_jurisdictions
            else:
                # Unclear response - ask follow-up
                followup_question = {
                    "type": "clarify_response",
                    "question": f"I didn't understand '{user_response}'. Could you clarify: Is this feature for all regions globally, or specific regions only?",
                    "options": ["Global (all regions)", "Specific regions only"],
                    "context": {"unclear_response": user_response}
                }
                
                clarified_response = await user_callback(followup_question)
                # Recursively handle the clarified response
                return await self._incorporate_geographic_clarification(
                    enriched_context, clarified_response, user_callback
                )
        
        # Update enriched context
        updated_context = enriched_context.copy()
        updated_context["geographic_implications"] = new_geographic_implications
        updated_context["processing_notes"] += f" | User clarified geographic scope: {user_response}"
        
        return updated_context
    
    async def _parse_multiple_regions(self, regions_response: str) -> List[str]:
        """
        Parse user's multiple regions selection
        """
        # Parse against available jurisdictions dynamically
        available_jurisdictions = await self._get_available_jurisdictions()
        if not available_jurisdictions:
            available_jurisdictions = ["Utah", "EU", "California", "Florida", "Brazil"]
        regions = await self._parse_jurisdiction_response(regions_response, available_jurisdictions)
        
        return regions if regions else (available_jurisdictions[:1] if available_jurisdictions else [])  # First available jurisdiction as fallback
    
    async def _get_available_jurisdictions(self) -> List[str]:
        """
        Get list of available jurisdictions from MCP client dynamically
        Returns jurisdiction names that can be used for analysis
        """
        if not self.mcp_client:
            return []
        
        try:
            # Get available MCP tools
            available_tools = await self.mcp_client.list_available_tools()
            
            # Extract jurisdiction names from tool descriptions
            jurisdictions = []
            for tool in available_tools:
                jurisdiction = tool.get("jurisdiction")
                if jurisdiction and jurisdiction not in jurisdictions:
                    jurisdictions.append(jurisdiction)
            
            return jurisdictions
            
        except Exception:
            # Fallback to empty list - let LLM handle the situation
            return []
    
    async def _parse_jurisdiction_response(self, response: str, available_jurisdictions: List[str]) -> List[str]:
        """
        Parse user response against available jurisdictions using LLM intelligence
        Handles abbreviations, synonyms, and context intelligently
        """
        if not available_jurisdictions:
            return []
            
        return await self._parse_jurisdictions_with_llm(response, available_jurisdictions)
    
    async def _analyze_with_reasoning(self, enriched_context: Dict[str, Any], user_callback=None) -> List[JurisdictionAnalysis]:
        """
        LLM-driven iterative MCP calling with reasoning
        Agent discovers available MCPs and decides which to call based on legal analysis needs
        """
        
        analysis_state = {
            "context": enriched_context,
            "mcp_results": [],
            "reasoning_log": [],
            "iteration": 0,
            "available_tools": None
        }
        
        # Discover available MCP tools
        try:
            analysis_state["available_tools"] = await self.mcp_client.list_available_tools()
        except Exception as e:
            # Fallback to old method if tool discovery not implemented
            print(f"MCP tool discovery failed, using fallback: {e}")
            return await self.mcp_client.analyze_parallel(enriched_context)
        
        # Iterative reasoning loop
        max_iterations = 5
        while analysis_state["iteration"] < max_iterations:
            try:
                # LLM decides next action
                reasoning_decision = await self._reason_about_next_action(analysis_state)
                
                if reasoning_decision.get("action") == "request_clarification":
                    # Mid-analysis clarification request
                    if user_callback:
                        clarification_response = await user_callback(reasoning_decision)
                        # Update analysis state with clarification
                        analysis_state = await self._handle_mid_analysis_clarification(
                            analysis_state, reasoning_decision, clarification_response
                        )
                    else:
                        # No callback available - this should not happen per requirements
                        # But handle gracefully with best guess
                        reasoning_decision = await self._fallback_reasoning_decision(reasoning_decision)
                        
                elif reasoning_decision.get("action") == "call_mcp":
                    # Call specific MCP with targeted query
                    mcp_result = await self._call_specific_mcp(
                        reasoning_decision.get("mcp_tool_name"),
                        reasoning_decision.get("query_focus"),
                        enriched_context
                    )
                    
                    analysis_state["mcp_results"].append(mcp_result)
                    analysis_state["reasoning_log"].append({
                        "iteration": analysis_state["iteration"],
                        "decision": reasoning_decision,
                        "result_summary": mcp_result.get("jurisdiction", "Unknown") if mcp_result else "Failed"
                    })
                    
                elif reasoning_decision.get("action") == "finalize":
                    # LLM believes it has sufficient information
                    analysis_state["reasoning_log"].append({
                        "iteration": analysis_state["iteration"],
                        "decision": "Analysis complete - sufficient information gathered"
                    })
                    break
                    
                else:
                    # Unknown action, break to avoid infinite loop
                    break
                    
                analysis_state["iteration"] += 1
                
            except Exception as e:
                print(f"Reasoning iteration {analysis_state['iteration']} failed: {e}")
                break
        
        # Convert MCP results to JurisdictionAnalysis objects
        return self._convert_mcp_results_to_analyses(analysis_state["mcp_results"])
    
    async def _reason_about_next_action(self, analysis_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLM reasoning to decide which MCP tool to call next
        Uses dynamic MCP tool discovery for flexible jurisdiction selection
        """
        
        context = analysis_state["context"]
        available_tools = analysis_state["available_tools"] or []
        previous_results = analysis_state["mcp_results"]
        
        # Format available tools for LLM
        tools_description = "\n".join([
            f"- {tool.get('name', 'unknown')}: {tool.get('description', 'No description')} (Jurisdiction: {tool.get('jurisdiction', 'Unknown')})" 
            for tool in available_tools
        ])
        
        # Format previous results
        previous_calls = "\n".join([
            f"- Called {result.get('jurisdiction', 'Unknown')}: {result.get('reasoning', 'No reasoning provided')[:100]}..."
            for result in previous_results
        ])
        
        reasoning_prompt = f"""You are a legal reasoning agent analyzing TikTok feature compliance.

Feature Context:
- Feature: {context.get('original_feature', 'Unknown')}
- Description: {context.get('expanded_description', 'No description')}
- Geographic Implications: {context.get('geographic_implications', [])}
- Risk Indicators: {context.get('risk_indicators', [])}
- Category: {context.get('feature_category', 'Unknown')}

Available Legal Analysis Tools:
{tools_description or "No tools available"}

Previous MCP Calls Made:
{previous_calls or "None yet"}

Analysis Rules:
1. ONLY call tools for jurisdictions that are relevant to this specific feature
2. Focus on jurisdictions mentioned in geographic_implications first
3. Match feature requirements to tool specialties:
   - For minor protection features → tools with "minor protection" specialty
   - For data processing features → tools with "data protection" specialty  
   - For content moderation features → tools with "content moderation" specialty
4. Don't call tools for irrelevant jurisdictions just because they exist
5. Don't call the same tool twice unless you need different information
6. Stop when you have sufficient information for compliance analysis
7. If geographic_implications is empty or unclear, you may request clarification

Decide your next action:
- "call_mcp": Need more information from a specific jurisdiction MCP tool
- "request_clarification": Need user clarification on ambiguous aspects
- "finalize": Have sufficient information to make final compliance decision

For requesting clarification, specify:
- What type of clarification is needed (geographic_scope, feature_category, risk_assessment)
- Specific question to ask the user
- Why this clarification is critical for accurate analysis

If calling MCP, specify:
- Which MCP tool to call (exact name from available tools)
- What specific legal question/focus area to analyze
- Why this information is needed

Respond ONLY with valid JSON:
{{
    "action": "call_mcp" or "finalize",
    "mcp_tool_name": "exact_tool_name_from_list",
    "query_focus": "specific legal question to analyze",
    "reasoning": "why this action/tool is needed for complete analysis"
}}"""
        
        try:
            response = await llm_client.complete(reasoning_prompt, max_tokens=400, temperature=0.2)
            content = response.get("content", "")
            
            # Parse JSON response
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content.strip()
            
            reasoning_decision = json.loads(json_str)
            return reasoning_decision
            
        except Exception as e:
            # Fallback decision if LLM reasoning fails
            print(f"LLM reasoning failed: {e}")
            
            # Simple fallback: call first available tool if none called yet
            if not previous_results and available_tools:
                return {
                    "action": "call_mcp",
                    "mcp_tool_name": available_tools[0].get("name", "unknown"),
                    "query_focus": "general compliance analysis",
                    "reasoning": "Fallback decision due to LLM reasoning failure"
                }
            else:
                return {"action": "finalize", "reasoning": "LLM reasoning failed, finalizing with available data"}
    
    async def _handle_mid_analysis_clarification(self, analysis_state: Dict[str, Any], clarification_request: Dict[str, Any], user_response: str) -> Dict[str, Any]:
        """
        Handle user clarification during mid-analysis
        Update analysis state based on user input
        """
        
        clarification_type = clarification_request.get("clarification_type", "unknown")
        
        if clarification_type == "geographic_scope":
            # Update context with new geographic information  
            updated_implications = await self._parse_geographic_response(user_response)
            analysis_state["context"]["geographic_implications"] = updated_implications
            
        elif clarification_type == "feature_category":
            # Update feature category based on user input
            analysis_state["context"]["feature_category"] = user_response
            
        elif clarification_type == "risk_assessment":
            # Update risk indicators
            new_risks = await self._parse_risk_response(user_response)
            analysis_state["context"]["risk_indicators"].extend(new_risks)
        
        # Log the clarification
        analysis_state["reasoning_log"].append({
            "iteration": analysis_state["iteration"],
            "type": "user_clarification",
            "question": clarification_request.get("question", ""),
            "response": user_response,
            "clarification_type": clarification_type
        })
        
        return analysis_state
    
    async def _parse_geographic_response(self, response: str) -> List[str]:
        """
        Parse user's geographic response into jurisdiction list using LLM intelligence
        """
        # Get available jurisdictions dynamically
        available_jurisdictions = await self._get_available_jurisdictions()
        if not available_jurisdictions:
            # Fallback to default jurisdictions if MCP discovery fails
            available_jurisdictions = ["Utah", "EU", "California", "Florida", "Brazil"]
            
        return await self._parse_jurisdictions_with_llm(response, available_jurisdictions)
    
    async def _parse_risk_response(self, response: str) -> List[str]:
        """
        Parse user's risk assessment response using LLM intelligence
        """
        available_risk_categories = [
            "payment processing",
            "minor protection", 
            "data processing",
            "content moderation",
            "age verification",
            "transparency reporting",
            "user rights",
            "cross-border data transfer"
        ]
        
        return await self._parse_risk_categories_with_llm(response, available_risk_categories)
    
    async def _fallback_reasoning_decision(self, failed_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback decision when user interaction is not available
        Per requirements, user interaction should always be available
        This is just a safety net
        """
        return {
            "action": "finalize",
            "reasoning": "User interaction unavailable, cannot clarify ambiguous feature"
        }
    
    async def _call_specific_mcp(self, mcp_tool_name: str, query_focus: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call specific MCP tool with targeted query using proper MCP protocol
        """
        
        if not mcp_tool_name:
            return {"error": "No MCP tool name provided"}
        
        try:
            # Standard MCP tool calling
            result = await self.mcp_client.call_tool(
                name=mcp_tool_name,
                arguments={
                    "feature_context": context,
                    "analysis_focus": query_focus
                }
            )
            return result
            
        except Exception as e:
            print(f"MCP tool call failed for {mcp_tool_name}: {e}")
            return {
                "error": f"MCP call failed: {str(e)}",
                "jurisdiction": "Unknown",
                "tool_name": mcp_tool_name
            }
    
    def _convert_mcp_results_to_analyses(self, mcp_results: List[Dict[str, Any]]) -> List[JurisdictionAnalysis]:
        """
        Convert MCP tool results to JurisdictionAnalysis objects
        Handles various MCP response formats
        """
        
        analyses = []
        for result in mcp_results:
            if not result or "error" in result:
                continue
                
            try:
                # Convert MCP result to JurisdictionAnalysis format
                analysis = JurisdictionAnalysis(
                    jurisdiction=result.get("jurisdiction", "Unknown"),
                    applicable_regulations=result.get("applicable_regulations", []),
                    compliance_required=result.get("compliance_required", False),
                    risk_level=result.get("risk_level", 1),
                    requirements=result.get("requirements", []),
                    implementation_steps=result.get("implementation_steps", []),
                    confidence=result.get("confidence", 0.5),
                    reasoning=result.get("reasoning", "MCP analysis completed"),
                    analysis_time=result.get("analysis_time", 0.0)
                )
                analyses.append(analysis)
                
            except Exception as e:
                print(f"Failed to convert MCP result to JurisdictionAnalysis: {e}")
                continue
        
        return analyses
    
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
        
        # Extract risk level using LLM intelligence
        risk_level = await self._extract_risk_level_with_llm(llm_text_response)
        
        if compliance_required and risk_level == 1:
            risk_level = 3  # Default to moderate if compliance required but no explicit level
            
        # Extract jurisdictions mentioned using LLM intelligence
        available_jurisdictions = []
        if self.mcp_client:
            try:
                tools = await self.mcp_client.list_available_tools()
                available_jurisdictions = [tool.get("jurisdiction", "") for tool in tools if tool.get("jurisdiction")]
            except Exception:
                available_jurisdictions = ["Utah", "EU", "California", "Florida", "Brazil"]
        else:
            available_jurisdictions = ["Utah", "EU", "California", "Florida", "Brazil"]
            
        jurisdictions = await self._parse_jurisdictions_with_llm(llm_text_response, available_jurisdictions)
        
        # Generate reasoning from LLM text
        reasoning = f"LLM Analysis: {llm_text_response[:300]}..." if len(llm_text_response) > 300 else llm_text_response
        
        return FeatureAnalysisResponse(
            feature_id=feature_id,
            feature_name=feature_name,
            compliance_required=compliance_required,
            risk_level=risk_level,
            applicable_jurisdictions=list(set(jurisdictions)),
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
    
    # ===== LLM-BASED PARSING METHODS =====
    # Replace all hardcoded string matching with intelligent LLM parsing
    
    async def _parse_jurisdictions_with_llm(self, user_response: str, available_jurisdictions: List[str]) -> List[str]:
        """
        Parse user response to identify jurisdictions using LLM intelligence
        Handles abbreviations, synonyms, and contextual understanding
        """
        if not available_jurisdictions or not user_response.strip():
            return []
            
        prompt = f"""Parse this user response to identify relevant jurisdictions.

User Response: "{user_response}"

Available Jurisdictions: {available_jurisdictions}

Rules:
1. Match jurisdictions mentioned explicitly or through common abbreviations/synonyms
2. "Global", "worldwide", "all regions" = ALL available jurisdictions
3. "EU", "Europe", "European" = EU
4. "CA", "Cali" = California
5. "FL" = Florida
6. "US", "America" without specifics = all US jurisdictions (Utah, California, Florida)
7. If unclear or no matches, return empty list

Return ONLY a JSON array of matched jurisdiction names: ["jurisdiction1", "jurisdiction2"]"""
        
        return await self._llm_parse_with_retry(prompt, self._parse_jurisdiction_list_response)
    
    async def _parse_risk_categories_with_llm(self, user_response: str, available_categories: List[str]) -> List[str]:
        """
        Parse user response to identify risk categories using LLM intelligence
        """
        if not available_categories or not user_response.strip():
            return []
            
        prompt = f"""Analyze this user response for risk categories.

User Response: "{user_response}"

Available Risk Categories: {available_categories}

Identify which risk categories apply based on the user's description. Consider:
- "Payment", "financial", "money", "transactions" → payment processing
- "Kids", "children", "minors", "under 18" → minor protection
- "Personal data", "privacy", "information" → data processing
- "Posts", "videos", "moderation" → content moderation
- "Verify age", "age check" → age verification
- "Reports", "transparency" → transparency reporting
- "User rights", "access data" → user rights
- "International", "cross-border" → cross-border data transfer

Return ONLY a JSON array of matched category names: ["category1", "category2"]"""
        
        return await self._llm_parse_with_retry(prompt, self._parse_risk_list_response)
    
    async def _extract_risk_level_with_llm(self, text_response: str) -> int:
        """
        Extract risk level (1-5) from LLM text response using intelligent parsing
        """
        if not text_response.strip():
            return 1
            
        prompt = f"""Extract the risk level from this legal analysis text.

Text: "{text_response[:500]}..."

Risk Level Scale:
1 = Minimal/No risk
2 = Low risk  
3 = Moderate risk
4 = High risk
5 = Critical risk

Look for:
- Explicit mentions like "risk level 3", "high risk", "critical"
- Severity indicators: "minimal", "low", "moderate", "high", "critical"
- Compliance implications: major violations = higher risk
- Legal consequences mentioned

Return ONLY a single integer 1-5: 3"""
        
        return await self._llm_parse_with_retry(prompt, self._parse_risk_level_response, default_value=1)
    
    async def _llm_parse_with_retry(self, prompt: str, parser_func, default_value=None):
        """
        Execute LLM parsing with retry logic for robustness
        """
        last_error = None
        
        for attempt in range(self.max_llm_retries):
            try:
                response = await llm_client.complete(prompt, max_tokens=150, temperature=0.1)
                content = response.get("content", "").strip()
                
                if not content:
                    raise ValueError("Empty LLM response")
                    
                return parser_func(content)
                
            except Exception as e:
                last_error = e
                if attempt < self.max_llm_retries - 1:
                    # Try with a simpler prompt on retry
                    if "JSON" in prompt:
                        prompt = prompt.replace("Return ONLY a JSON array", "Return a simple list")
                    continue
                else:
                    break
        
        # All retries failed - return default
        print(f"LLM parsing failed after {self.max_llm_retries} retries: {last_error}")
        return default_value if default_value is not None else []
    
    def _parse_jurisdiction_list_response(self, llm_response: str) -> List[str]:
        """
        Parse LLM response into jurisdiction list with fallback parsing
        """
        try:
            # Try JSON parsing first
            if llm_response.startswith('[') and llm_response.endswith(']'):
                return json.loads(llm_response)
                
            # Extract JSON from text if wrapped
            json_match = re.search(r'\[.*?\]', llm_response)
            if json_match:
                return json.loads(json_match.group(0))
                
            # Fallback: look for quoted strings
            quoted_matches = re.findall(r'"([^"]+)"', llm_response)
            if quoted_matches:
                return quoted_matches
                
            # Last resort: split by common delimiters
            if ',' in llm_response:
                return [item.strip().strip('"').strip("'") for item in llm_response.split(',')]
                
            # Single item response
            clean_response = llm_response.strip().strip('"').strip("'")
            return [clean_response] if clean_response else []
            
        except Exception:
            return []
    
    def _parse_risk_list_response(self, llm_response: str) -> List[str]:
        """
        Parse LLM response into risk category list (same logic as jurisdictions)
        """
        return self._parse_jurisdiction_list_response(llm_response)
    
    def _parse_risk_level_response(self, llm_response: str) -> int:
        """
        Parse LLM response into risk level integer with robust fallback
        """
        try:
            # Look for single digit
            digit_match = re.search(r'\b([1-5])\b', llm_response)
            if digit_match:
                return int(digit_match.group(1))
                
            # Look for written numbers
            text_to_num = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'minimal': 1, 'low': 2, 'moderate': 3, 'high': 4, 'critical': 5
            }
            
            response_lower = llm_response.lower()
            for text, num in text_to_num.items():
                if text in response_lower:
                    return num
                    
            # Default fallback
            return 1
            
        except Exception:
            return 1
    
    async def _is_global_deployment_request(self, user_response: str) -> bool:
        """
        Determine if user response indicates global deployment
        """
        prompt = f"""Analyze this user response: "{user_response}"

Question: Does this response indicate GLOBAL or WORLDWIDE deployment?

Look for indicators like:
- "Global", "worldwide", "everywhere", "all regions"
- "International", "globally", "world-wide" 
- "All countries", "all markets"
- "Universal deployment"

Return ONLY: true or false"""
        
        result = await self._llm_parse_with_retry(prompt, self._parse_boolean_response, default_value=False)
        return result
    
    async def _is_multiple_regions_request(self, user_response: str) -> bool:
        """
        Determine if user response indicates multiple specific regions
        """
        prompt = f"""Analyze this user response: "{user_response}"

Question: Does this response indicate MULTIPLE SPECIFIC regions (not global)?

Look for indicators like:
- "Multiple", "several", "specific regions"
- "Some countries", "certain areas" 
- "A few jurisdictions", "select markets"
- Lists like "US and EU" or "California and Florida"

Return ONLY: true or false"""
        
        result = await self._llm_parse_with_retry(prompt, self._parse_boolean_response, default_value=False)
        return result
    
    def _parse_boolean_response(self, llm_response: str) -> bool:
        """
        Parse LLM response into boolean with robust fallback
        """
        response_lower = llm_response.lower().strip()
        
        # Direct boolean responses
        if response_lower in ['true', 'yes', '1']:
            return True
        if response_lower in ['false', 'no', '0']:
            return False
            
        # Look for boolean indicators in text
        if any(word in response_lower for word in ['true', 'yes', 'correct', 'indicates']):
            return True
        if any(word in response_lower for word in ['false', 'no', 'incorrect', 'does not']):
            return False
            
        # Default fallback
        return False

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