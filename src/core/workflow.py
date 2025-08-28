"""
Enhanced LangGraph Workflow Orchestration - Phase 1A Implementation
Central workflow management with smart routing for multiple input types
"""
from typing import Dict, Any, Union, List
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, START, END
from .models import (
    WorkflowState, FeatureAnalysisRequest, UserQueryRequest, 
    FeatureAnalysisResponse, UserQueryResponse, MissingInfoResponse
)
from .agents.json_refactorer import JSONRefactorer
from .agents.lawyer_agent import LawyerAgent

class EnhancedWorkflowOrchestrator:
    """
    Enhanced workflow orchestrator with smart routing for multiple input types
    Supports: Feature descriptions, User queries, PDF documents (placeholder)
    """
    
    def __init__(self, mcp_client=None, cache_manager=None):
        # Dependency injection for team member enhancements
        self.json_refactorer = JSONRefactorer()
        self.lawyer_agent = LawyerAgent(mcp_client=mcp_client)
        self.cache = cache_manager  # Team Member 1 will implement
        
        # Build the workflow graphs for different input types
        self.feature_workflow = self._build_feature_workflow()
        self.query_workflow = self._build_query_workflow()
        # TODO: Team Member 3 - PDF workflow
        # self.pdf_workflow = self._build_pdf_workflow()
    
    def _build_feature_workflow(self) -> StateGraph:
        """Build the feature analysis workflow"""
        
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for feature analysis path
        workflow.add_node("json_refactorer", self._json_refactor_node)
        workflow.add_node("legal_analysis", self._legal_analysis_node) 
        workflow.add_node("decision_synthesis", self._decision_synthesis_node)
        
        # Add edges - Sequential execution for feature analysis
        workflow.add_edge(START, "json_refactorer")
        workflow.add_edge("json_refactorer", "legal_analysis")
        workflow.add_edge("legal_analysis", "decision_synthesis")
        workflow.add_edge("decision_synthesis", END)
        
        return workflow.compile()
    
    def _build_query_workflow(self) -> StateGraph:
        """Build the user query workflow"""
        
        workflow = StateGraph(WorkflowState)
        
        # Add node for direct query handling
        workflow.add_node("query_handler", self._query_handler_node)
        
        # Simple direct execution for queries
        workflow.add_edge(START, "query_handler")
        workflow.add_edge("query_handler", END)
        
        return workflow.compile()
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced request processing with smart routing
        Routes to appropriate workflow based on input type detection
        """
        
        # Detect input type using simple Python logic
        input_type = self._detect_input_type(request_data)
        
        # Route to appropriate processing method
        if input_type == "feature_description":
            return await self._process_feature_analysis(request_data)
        elif input_type == "user_query":
            return await self._process_user_query(request_data)
        elif input_type == "pdf_document":
            # TODO: Team Member 3 - Implement PDF processing
            return self._create_missing_info_response(
                "PDF processing not yet implemented. Please provide feature description instead.",
                ["feature_description"],
                ["Describe the feature you want to analyze in text format"]
            )
        else:
            return self._create_missing_info_response(
                "Unable to determine input type. Please provide either a feature description or ask a question.",
                ["name", "description"],
                ["Provide structured feature data with name and description", "Ask a direct question about compliance"]
            )
    
    def _detect_input_type(self, request_data: Dict[str, Any]) -> str:
        """
        Simple input type detection based on data structure
        User guidance: "just do it based on type of input"
        """
        
        # Check for PDF document
        if "filename" in request_data and "content" in request_data:
            return "pdf_document"
        
        # Check for structured feature description
        if "name" in request_data and "description" in request_data:
            return "feature_description"
        
        # Check for user query
        if "query" in request_data or len(request_data) == 1 and any(
            key in ["query", "question", "message"] for key in request_data.keys()
        ):
            return "user_query"
        
        # If single string value, treat as user query
        if len(request_data) == 1:
            key, value = next(iter(request_data.items()))
            if isinstance(value, str) and len(value.strip()) > 0:
                return "user_query"
        
        return "unknown"
    
    async def _process_feature_analysis(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process structured feature analysis request"""
        
        # Initialize workflow state
        initial_state = WorkflowState(
            input_data=request_data,
            input_type="feature_description",
            feature_id=str(uuid.uuid4()),
            execution_path=[],
            start_time=datetime.now()
        )
        
        try:
            # Execute feature analysis workflow
            result = await self.feature_workflow.ainvoke(initial_state)
            
            # Return final decision
            if result.get("final_decision"):
                final_decision = result["final_decision"]
                # Handle both Pydantic model and dict cases
                if hasattr(final_decision, 'model_dump'):
                    return final_decision.model_dump()
                else:
                    return final_decision
            else:
                raise Exception("Feature analysis completed but no final decision generated")
                
        except Exception as e:
            # Error handling
            return self._create_error_response(str(e), initial_state)
    
    async def _process_user_query(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user query request"""
        
        # Extract query from various possible keys
        query_text = None
        for key in ["query", "question", "message"]:
            if key in request_data:
                query_text = request_data[key]
                break
        
        # If single key-value pair, use the value as query
        if not query_text and len(request_data) == 1:
            query_text = next(iter(request_data.values()))
        
        if not query_text:
            return self._create_missing_info_response(
                "No query text found. Please provide your question.",
                ["query"],
                ["Ask a question about TikTok compliance or regulations"]
            )
        
        # Initialize workflow state for query processing
        initial_state = WorkflowState(
            input_data={"query": query_text, "context": request_data.get("context", {})},
            input_type="user_query",
            feature_id=str(uuid.uuid4()),
            execution_path=[],
            start_time=datetime.now()
        )
        
        try:
            # Execute query workflow
            result = await self.query_workflow.ainvoke(initial_state)
            
            # Return final response
            if result.get("final_decision"):
                final_decision = result["final_decision"]
                # Handle both Pydantic model and dict cases
                if hasattr(final_decision, 'model_dump'):
                    return final_decision.model_dump()
                else:
                    return final_decision
            else:
                raise Exception("Query processing completed but no response generated")
                
        except Exception as e:
            # Error handling
            return self._create_query_error_response(str(e))
    
    async def _json_refactor_node(self, state: WorkflowState) -> WorkflowState:
        """
        JSON Refactorer workflow node
        Phase 1A: Basic terminology expansion
        """
        
        state.execution_path.append("json_refactorer")
        
        try:
            # TODO: Team Member 1 - Add caching check here
            # if self.cache:
            #     cached_result = await self.cache.get_cached_context(state.input_data)
            #     if cached_result:
            #         state.enriched_context = cached_result
            #         return state
            
            # Process input through JSON Refactorer
            enriched_context = await self.json_refactorer.process(state.input_data)
            state.enriched_context = enriched_context.model_dump()
            
            # TODO: Team Member 1 - Cache the result
            # if self.cache:
            #     await self.cache.cache_context(state.input_data, state.enriched_context)
            
        except Exception as e:
            state.error_state = f"JSON Refactorer failed: {str(e)}"
        
        return state
    
    async def _legal_analysis_node(self, state: WorkflowState) -> WorkflowState:
        """
        Legal analysis workflow node
        Phase 1A: Mock MCP analysis
        """
        
        state.execution_path.append("legal_analysis")
        
        if state.error_state or not state.enriched_context:
            return state
        
        try:
            # Get jurisdiction analyses through Lawyer Agent
            # Phase 1A: Uses mock MCPs
            final_decision = await self.lawyer_agent.analyze(state.enriched_context)
            state.legal_analyses = [analysis.model_dump() for analysis in final_decision.jurisdiction_details]
            
        except Exception as e:
            state.error_state = f"Legal analysis failed: {str(e)}"
        
        return state
    
    async def _decision_synthesis_node(self, state: WorkflowState) -> WorkflowState:
        """
        Decision synthesis workflow node
        Phase 1A: Basic decision aggregation
        """
        
        state.execution_path.append("decision_synthesis")
        
        if state.error_state:
            # Create error response
            state.final_decision = self._create_error_response(
                state.error_state,
                state
            )
            return state
        
        try:
            # Re-run lawyer agent analysis to get final decision
            # (In Phase 1A, this is a bit redundant but maintains clear separation)
            final_decision = await self.lawyer_agent.analyze(state.enriched_context)
            state.final_decision = final_decision
            
            # Record end time
            state.end_time = datetime.now()
            
        except Exception as e:
            state.error_state = f"Decision synthesis failed: {str(e)}"
            state.final_decision = self._create_error_response(str(e), state)
        
        return state
    
    async def _query_handler_node(self, state: WorkflowState) -> WorkflowState:
        """
        Direct query handler workflow node
        Routes user queries to Lawyer Agent for advisory responses
        """
        
        state.execution_path.append("query_handler")
        
        try:
            # Process query through Lawyer Agent
            query_response = await self.lawyer_agent.handle_user_query(state.input_data)
            state.final_decision = query_response
            
            # Record end time
            state.end_time = datetime.now()
            
        except Exception as e:
            state.error_state = f"Query handler failed: {str(e)}"
            state.final_decision = self._create_query_error_response(str(e))
        
        return state
    
    def _create_error_response(self, error_message: str, state: WorkflowState) -> Dict[str, Any]:
        """Create standardized error response for feature analysis"""
        
        from .models import FeatureAnalysisResponse
        
        end_time = datetime.now()
        analysis_time = (end_time - state.start_time).total_seconds() if state.start_time else 0
        
        error_response = FeatureAnalysisResponse(
            feature_id=state.feature_id,
            feature_name=state.input_data.get("name", "Unknown Feature"),
            compliance_required=False,
            risk_level=1,
            applicable_jurisdictions=[],
            requirements=[],
            implementation_steps=["Manual legal review recommended due to analysis error"],
            confidence_score=0.1,
            reasoning=f"Analysis error: {error_message}. Manual review required.",
            jurisdiction_details=[],
            analysis_time=analysis_time,
            created_at=end_time
        )
        
        return error_response.model_dump()
    
    def _create_query_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response for user queries"""
        
        from .models import UserQueryResponse
        
        error_response = UserQueryResponse(
            advice=f"I apologize, but I'm unable to process your query due to a technical error: {error_message}. Please try rephrasing your question or contact support.",
            confidence=0.1,
            sources=["System Error"],
            related_jurisdictions=[],
            timestamp=datetime.now()
        )
        
        return error_response.model_dump()
    
    def _create_missing_info_response(self, message: str, missing_fields: List[str], suggestions: List[str] = None) -> Dict[str, Any]:
        """Create missing information response"""
        
        from .models import MissingInfoResponse
        
        missing_response = MissingInfoResponse(
            message=message,
            missing_fields=missing_fields,
            suggestions=suggestions
        )
        
        return missing_response.model_dump()

# TODO: Team Member 1 - Enhanced workflow with parallel execution
# class EnhancedWorkflowOrchestrator(WorkflowOrchestrator):
#     """Enhanced orchestrator with parallel MCP execution and caching"""
#     
#     def _build_workflow(self) -> StateGraph:
#         # TODO: Team Member 1 - Implement parallel MCP execution
#         # 1. Add parallel_mcp_analysis node
#         # 2. Execute all 5 MCPs concurrently
#         # 3. Add timeout handling and retries
#         # 4. Implement circuit breaker pattern
#         
#         workflow = StateGraph(WorkflowState)
#         
#         workflow.add_node("json_refactorer", self._json_refactor_node)
#         workflow.add_node("parallel_mcp_analysis", self._parallel_mcp_node)  # New!
#         workflow.add_node("decision_synthesis", self._decision_synthesis_node)
#         
#         # Parallel execution flow
#         workflow.add_edge(START, "json_refactorer")
#         workflow.add_edge("json_refactorer", "parallel_mcp_analysis")
#         workflow.add_edge("parallel_mcp_analysis", "decision_synthesis")
#         workflow.add_edge("decision_synthesis", END)
#         
#         return workflow.compile()
#     
#     async def _parallel_mcp_node(self, state: WorkflowState) -> WorkflowState:
#         # TODO: Team Member 1 - Implement true parallel MCP execution
#         # 1. Use asyncio.gather for concurrent HTTP calls
#         # 2. Handle partial failures gracefully
#         # 3. Add performance monitoring
#         pass

# Create global enhanced workflow instance with MCP configuration
from ..config import settings

# Initialize MCP client based on settings
mcp_client = None
if settings.enable_real_mcps:
    # TODO: Team Member 1 - Initialize real MCP client when implemented
    # from .agents.real_mcp_client import RealMCPClient
    # mcp_client = RealMCPClient(MCP_SERVICES)
    pass
# If ENABLE_REAL_MCPS=false, mcp_client remains None (no mock responses)

workflow_orchestrator = EnhancedWorkflowOrchestrator(mcp_client=mcp_client)

# Legacy compatibility class for existing code
class WorkflowOrchestrator(EnhancedWorkflowOrchestrator):
    """Legacy compatibility wrapper - redirects to enhanced orchestrator"""
    
    async def analyze_feature(self, request: FeatureAnalysisRequest) -> Dict[str, Any]:
        """Legacy method - redirects to enhanced process_request"""
        return await self.process_request(request.model_dump())