"""
Core data models for the Geo-Regulation AI System
Enhanced with multi-input support and routing
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
import uuid

# Enhanced Request Models for Multiple Input Types
class FeatureAnalysisRequest(BaseModel):
    """Request model for structured feature analysis"""
    name: str = Field(..., description="Feature name")
    description: str = Field(..., description="Feature description")
    geographic_context: Optional[str] = Field(None, description="Geographic hints")
    documents: Optional[List[str]] = Field(None, description="Supporting documents")
    feature_type: Optional[str] = Field(None, description="Feature category")

class UserQueryRequest(BaseModel):
    """Request model for user queries"""
    query: str = Field(..., description="User question or query")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class PDFAnalysisRequest(BaseModel):
    """Request model for PDF document analysis"""
    filename: str = Field(..., description="PDF filename")
    content: bytes = Field(..., description="PDF file content")
    geographic_context: Optional[str] = Field(None, description="Geographic hints")

class MissingInfoResponse(BaseModel):
    """Response when additional information is required"""
    response_type: Literal["missing_info"] = "missing_info"
    message: str
    missing_fields: List[str]
    suggestions: Optional[List[str]] = None

class JurisdictionAnalysis(BaseModel):
    """Analysis result from a specific jurisdiction MCP"""
    jurisdiction: str
    applicable_regulations: List[str]
    compliance_required: bool
    risk_level: int = Field(ge=1, le=5, description="Risk level 1-5")
    requirements: List[str]
    implementation_steps: List[str]
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    reasoning: str
    analysis_time: Optional[float] = None

class FeatureAnalysisResponse(BaseModel):
    """Complete feature compliance analysis response"""
    response_type: Literal["compliance_analysis"] = "compliance_analysis"
    feature_id: str
    feature_name: str
    compliance_required: bool
    risk_level: int = Field(ge=1, le=5)
    applicable_jurisdictions: List[str]
    requirements: List[str]
    implementation_steps: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    jurisdiction_details: List[JurisdictionAnalysis]
    analysis_time: float
    created_at: datetime

class UserQueryResponse(BaseModel):
    """Response to user queries (advisory mode)"""
    response_type: Literal["advisory"] = "advisory"
    advice: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str]
    related_jurisdictions: Optional[List[str]] = None
    timestamp: datetime

# Enhanced LangGraph Workflow State
class WorkflowState(BaseModel):
    """Enhanced state object for multi-path workflow routing"""
    # Input data and classification
    input_data: Dict[str, Any]
    input_type: Optional[Literal["feature_description", "user_query", "pdf_document"]] = None
    feature_id: str
    
    # Processing stages
    enriched_context: Optional[Dict[str, Any]] = None
    legal_analyses: List[JurisdictionAnalysis] = []
    final_decision: Optional[Union[FeatureAnalysisResponse, UserQueryResponse]] = None
    
    # Missing information handling
    missing_info: Optional[List[str]] = None
    completeness_validated: bool = False
    
    # Execution tracking
    execution_path: List[str] = []
    error_state: Optional[str] = None
    confidence_scores: Dict[str, float] = {}
    
    # Metadata
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

# JSON Refactorer Models
class EnrichedContext(BaseModel):
    """Output from JSON Refactorer Agent"""
    original_feature: str
    expanded_description: str
    geographic_implications: List[str]
    feature_category: str
    risk_indicators: List[str]
    terminology_expansions: Dict[str, str]
    processing_notes: Optional[str] = None

# Mock MCP Response (for Phase 1)
class MockMCPResponse(BaseModel):
    """Mock response structure matching real MCP interface"""
    jurisdiction: str
    applicable_regulations: List[str]
    compliance_required: bool
    risk_level: int
    requirements: List[str]
    implementation_steps: List[str]
    confidence: float
    reasoning: str
    analysis_time: float = 0.5  # Mock timing

# Error Models
class APIError(BaseModel):
    """Standard API error response"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

# Health Check Model
class HealthStatus(BaseModel):
    """System health check response"""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    services: Dict[str, str]
    version: str = "1.0.0"