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
from .agents.lawyer_agent import LawyerAgent
# NOTE: JSON Refactorer deprecated - functionality moved to Knowledge Base

class EnhancedWorkflowOrchestrator:
    """
    Enhanced workflow orchestrator with smart routing for multiple input types
    Supports: Feature descriptions, User queries, PDF documents (placeholder)
    """
    
    def __init__(self, mcp_client=None, cache_manager=None):
        # Dependency injection for team member enhancements
        self.lawyer_agent = LawyerAgent(mcp_client=mcp_client)
        self.cache = cache_manager  # MCP Integration will implement
        # NOTE: JSON Refactorer removed - direct processing via lawyer agent + knowledge base
        
        # Build unified workflow - ALL inputs go through same pipeline
        self.unified_workflow = self._build_unified_workflow()
    
    def _build_unified_workflow(self) -> StateGraph:
        """
        Build unified workflow - ALL inputs go through same pipeline:
        Input → JSON Refactorer → Lawyer Agent → Output
        """
        
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for unified pipeline (JSON Refactorer removed)
        workflow.add_node("input_preprocessing", self._input_preprocessing_node)  # Handle batch/PDF extraction
        workflow.add_node("lawyer_agent", self._lawyer_agent_node)                # Direct processing with Knowledge Base
        
        # Simplified execution - direct to lawyer agent (Knowledge Base handles terminology)
        workflow.add_edge(START, "input_preprocessing")
        workflow.add_edge("input_preprocessing", "lawyer_agent")
        workflow.add_edge("lawyer_agent", END)
        
        return workflow.compile()
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified request processing - Simplified workflow (JSON Refactorer deprecated):
        Input → Preprocessing → Lawyer Agent (with Knowledge Base) → Output
        """
        
        # Detect input type for preprocessing decisions
        input_type = self._detect_input_type(request_data)
        
        # Initialize workflow state for unified pipeline
        initial_state = WorkflowState(
            input_data=request_data,
            input_type=input_type,
            feature_id=str(uuid.uuid4()),
            execution_path=[],
            start_time=datetime.now()
        )
        
        try:
            # Execute unified workflow for ALL input types
            result = await self.unified_workflow.ainvoke(initial_state)
            
            # Return final decision
            if result.get("final_decision"):
                final_decision = result["final_decision"]
                # Handle both Pydantic model and dict cases
                if hasattr(final_decision, 'model_dump'):
                    return final_decision.model_dump()
                else:
                    return final_decision
            else:
                raise Exception("Processing completed but no final decision generated")
                
        except Exception as e:
            # Error handling
            return self._create_error_response(str(e), initial_state)
    
    async def process_bulk_requirements_analysis(
        self,
        requirements_document_id: str,
        legal_document_filter: str,
        mcp_query: str
    ) -> Dict[str, Any]:
        """
        Process bulk requirements analysis using MCP call
        """
        try:
            # Construct query data for lawyer agent to analyze requirements against legal docs
            query_data = {
                "query": f"Please analyze requirements document {requirements_document_id} against legal documents using MCP search with query: '{mcp_query}'. Provide a comprehensive compliance analysis.",
                "context": {
                    "requirements_document_id": requirements_document_id,
                    "mcp_query": mcp_query,
                    "analysis_type": "requirements_bulk_analysis"
                }
            }
            
            # Use lawyer agent to process the bulk analysis
            result = await self.lawyer_agent.handle_user_query(query_data)
            
            return {
                "document_name": f"Requirements-{requirements_document_id}",
                "status": "completed",
                "summary": result.advice if hasattr(result, 'advice') else "Analysis completed",
                "issues": self._extract_issues_from_response(result.advice if hasattr(result, 'advice') else ""),
                "recommendations": self._extract_recommendations_from_response(result.advice if hasattr(result, 'advice') else ""),
                "workflow_id": None,
                "analysis_time": 30  # Mock timing
            }
            
        except Exception as e:
            return {
                "document_name": f"Requirements-{requirements_document_id}",
                "status": "failed",
                "summary": f"Analysis failed: {str(e)}",
                "issues": [],
                "recommendations": [],
                "workflow_id": None,
                "analysis_time": 0
            }
    
    async def process_bulk_legal_analysis(
        self,
        legal_document_id: str,
        requirements_document_filter: str,
        mcp_query: str
    ) -> Dict[str, Any]:
        """
        Process bulk legal analysis using MCP call
        """
        try:
            # Construct query data for lawyer agent to analyze legal doc against requirements
            query_data = {
                "query": f"Please analyze legal document {legal_document_id} against requirements documents using MCP search with query: '{mcp_query}'. Identify compliance gaps and requirements coverage.",
                "context": {
                    "legal_document_id": legal_document_id,
                    "requirements_document_filter": requirements_document_filter,
                    "mcp_query": mcp_query,
                    "analysis_type": "legal_bulk_analysis"
                }
            }
            
            # Use lawyer agent to process the bulk analysis
            result = await self.lawyer_agent.handle_user_query(query_data)
            
            return {
                "document_name": f"Legal-{legal_document_id}",
                "status": "completed", 
                "summary": result.advice if hasattr(result, 'advice') else "Analysis completed",
                "issues": self._extract_issues_from_response(result.advice if hasattr(result, 'advice') else ""),
                "recommendations": self._extract_recommendations_from_response(result.advice if hasattr(result, 'advice') else ""),
                "workflow_id": None,
                "analysis_time": 30  # Mock timing
            }
            
        except Exception as e:
            return {
                "document_name": f"Legal-{legal_document_id}",
                "status": "failed",
                "summary": f"Analysis failed: {str(e)}",
                "issues": [],
                "recommendations": [],
                "workflow_id": None,
                "analysis_time": 0
            }
    
    def _extract_issues_from_response(self, content: str) -> List[Dict[str, str]]:
        """Extract compliance issues from lawyer agent response"""
        # Simple extraction - in production this would be more sophisticated
        issues = []
        if "non-compliant" in content.lower() or "violation" in content.lower():
            issues.append({
                "type": "non-compliant",
                "requirement": "Extracted from analysis",
                "regulation": "Various regulations",
                "severity": "medium",
                "description": "Compliance issue identified in analysis"
            })
        return issues
    
    def _extract_recommendations_from_response(self, content: str) -> List[str]:
        """Extract recommendations from lawyer agent response"""
        # Simple extraction - in production this would be more sophisticated
        if "recommend" in content.lower() or "should" in content.lower():
            return ["Review compliance requirements", "Update implementation", "Consult legal team"]
        return []
    
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
    
    async def _input_preprocessing_node(self, state: WorkflowState) -> WorkflowState:
        """
        Input preprocessing workflow node - handles batch/PDF extraction
        Routes different input types for preprocessing before JSON Refactorer
        """
        
        state.execution_path.append("input_preprocessing")
        
        try:
            if state.input_type == "csv_batch":
                # TODO: UI Enhancement - Extract multiple features from CSV
                # For now, pass through as-is
                pass
            elif state.input_type == "pdf_document":
                # TODO: UI Enhancement - Extract features from PDF content
                # For now, return not implemented error
                state.error_state = "PDF processing not yet implemented by UI Enhancement team"
            else:
                # Single features and queries pass through unchanged
                pass
                
        except Exception as e:
            state.error_state = f"Input preprocessing failed: {str(e)}"
        
        return state
    
    # NOTE: _json_refactor_node removed - functionality moved to Knowledge Base
    # Direct processing now handled by lawyer agent with terminology expansion
    async def _lawyer_agent_node(self, state: WorkflowState) -> WorkflowState:
        """
        Unified lawyer agent workflow node - handles both analysis and advisory
        Determines response type based on input and returns appropriate format
        """
        
        state.execution_path.append("lawyer_agent")
        
        if state.error_state:
            # Create error response based on input type
            if state.input_type == "user_query":
                state.final_decision = self._create_query_error_response(state.error_state)
            else:
                state.final_decision = self._create_error_response(state.error_state, state)
            return state
        
        try:
            # Lawyer Agent processes input directly (Knowledge Base handles terminology)
            if state.input_type == "user_query":
                # Return advisory response for queries
                final_decision = await self.lawyer_agent.handle_user_query(state.input_data)
            else:
                # Return compliance analysis for features/documents/batch  
                final_decision = await self.lawyer_agent.analyze(state.input_data)
            
            state.final_decision = final_decision
            
            # Record end time
            state.end_time = datetime.now()
            
        except Exception as e:
            state.error_state = f"Lawyer agent processing failed: {str(e)}"
            if state.input_type == "user_query":
                state.final_decision = self._create_query_error_response(str(e))
            else:
                state.final_decision = self._create_error_response(str(e), state)
        
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

# TODO: MCP Integration - Enhanced workflow with parallel execution
# class EnhancedWorkflowOrchestrator(WorkflowOrchestrator):
#     """Enhanced orchestrator with parallel MCP execution and caching"""
#     
#     def _build_workflow(self) -> StateGraph:
#         # TODO: MCP Integration - Implement parallel MCP execution
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
#         # TODO: MCP Integration - Implement true parallel MCP execution
#         # 1. Use asyncio.gather for concurrent HTTP calls
#         # 2. Handle partial failures gracefully
#         # 3. Add performance monitoring
#         pass

# Create global enhanced workflow instance with MCP configuration
from ..config import settings

# Initialize MCP client - always use real MCPs now
mcp_client = None
# TODO: MCP Integration - Initialize real MCP client when implemented
# from .agents.real_mcp_client import RealMCPClient
# mcp_client = RealMCPClient(MCP_SERVICES)

workflow_orchestrator = EnhancedWorkflowOrchestrator(mcp_client=mcp_client)

# Legacy compatibility class for existing code
class WorkflowOrchestrator(EnhancedWorkflowOrchestrator):
    """Legacy compatibility wrapper - redirects to enhanced orchestrator"""
    
    async def analyze_feature(self, request: FeatureAnalysisRequest) -> Dict[str, Any]:
        """Legacy method - redirects to enhanced process_request"""
        return await self.process_request(request.model_dump())