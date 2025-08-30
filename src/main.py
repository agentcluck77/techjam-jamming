"""
FastAPI Main Application - Phase 1B Implementation
Main entry point for the Geo-Regulation AI System API
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import logging

from .config import settings
from .core.models import (
    FeatureAnalysisRequest, UserQueryRequest, PDFAnalysisRequest,
    FeatureAnalysisResponse, UserQueryResponse, MissingInfoResponse, 
    HealthStatus, APIError
)
from .core.workflow import workflow_orchestrator
from .core.llm_service import llm_client, GEMINI_MODELS, CLAUDE_MODELS

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Geo-Regulation AI System")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Feature flags - Batch Processing: {settings.enable_batch_processing}")
    
    # TODO: Team Member - Initialize MCP clients (always real MCPs now)
    # await initialize_mcp_clients()
    
    yield
    
    logger.info("Shutting down Geo-Regulation AI System")

# Create FastAPI application
app = FastAPI(
    title="TikTok Geo-Regulation AI System",
    description="Automated compliance analysis for TikTok features across global jurisdictions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/api/v1/health", response_model=HealthStatus)
async def health_check():
    """
    Comprehensive system health check
    Phase 1B: Basic health verification
    """
    
    health_status = HealthStatus(
        status="healthy",
        timestamp=datetime.now(),
        services={
            "workflow_orchestrator": "healthy",
            "json_refactorer": "healthy",
            "legal_mcp": "healthy",
            "requirements_mcp": "healthy"
        }
    )
    
    # TODO: Team Member 1 - Add real service health checks
    # try:
    #     if settings.enable_caching:
    #         await check_redis_health()
    #         health_status.services["redis"] = "healthy"
    #     
    #     # Always check MCP services (no feature flag needed)
    #     mcp_health = await check_mcp_services()
    #     health_status.services.update(mcp_health)
    # except Exception as e:
    #     health_status.status = "degraded"
    #     health_status.services["error"] = str(e)
    
    return health_status

# Enhanced universal processing endpoint
@app.post("/api/v1/process")
async def process_request(request_data: dict):
    """
    Enhanced universal processing endpoint with smart routing
    Handles feature descriptions, user queries, and PDF documents
    """
    
    logger.info(f"Processing request with data keys: {list(request_data.keys())}")
    
    try:
        # Execute enhanced workflow with smart routing
        result = await workflow_orchestrator.process_request(request_data)
        
        # Log result type for debugging
        result_type = result.get("response_type", "unknown")
        logger.info(f"Request processed - Result type: {result_type}")
        
        return result
        
    except Exception as e:
        logger.error(f"Request processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=APIError(
                error_code="PROCESSING_FAILED",
                message=f"Request processing failed: {str(e)}",
                timestamp=datetime.now()
            ).model_dump()
        )

# Legacy endpoint for backward compatibility
@app.post("/api/v1/analyze-feature", response_model=FeatureAnalysisResponse)
async def analyze_feature(request: FeatureAnalysisRequest):
    """
    Legacy feature analysis endpoint - redirects to universal processor
    Maintained for backward compatibility
    """
    
    logger.info(f"Legacy endpoint called for feature: {request.name}")
    
    try:
        # Convert to dict and process through universal endpoint
        result = await process_request(request.model_dump())
        
        # Ensure result is a FeatureAnalysisResponse
        if result.get("response_type") != "compliance_analysis":
            raise ValueError("Unexpected response type from legacy endpoint")
            
        return FeatureAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Legacy analysis failed for {request.name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=APIError(
                error_code="ANALYSIS_FAILED",
                message=f"Feature analysis failed: {str(e)}",
                timestamp=datetime.now()
            ).model_dump()
        )

# User query endpoint
@app.post("/api/v1/query", response_model=UserQueryResponse)
async def handle_user_query(request: UserQueryRequest):
    """
    Handle user questions about compliance and regulations
    Provides advisory responses using MCP search + LLM analysis
    """
    
    logger.info(f"Processing user query: {request.query[:50]}...")
    
    try:
        # Process through universal endpoint
        result = await process_request(request.model_dump())
        
        # Ensure result is a UserQueryResponse
        if result.get("response_type") != "advisory":
            raise ValueError("Unexpected response type from query endpoint")
            
        return UserQueryResponse(**result)
        
    except Exception as e:
        logger.error(f"User query processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=APIError(
                error_code="QUERY_FAILED",
                message=f"Query processing failed: {str(e)}",
                timestamp=datetime.now()
            ).model_dump()
        )

# PDF analysis endpoint (placeholder)
@app.post("/api/v1/analyze-pdf")
async def analyze_pdf(request: PDFAnalysisRequest):
    """
    Analyze PDF documents for compliance requirements
    TODO: Team Member 3 - Implement PDF processing capabilities
    """
    
    logger.info(f"PDF analysis requested for: {request.filename}")
    
    try:
        # Process through universal endpoint (will return not implemented response)
        result = await process_request(request.model_dump())
        return result
        
    except Exception as e:
        logger.error(f"PDF analysis failed for {request.filename}: {str(e)}")
        raise HTTPException(
            status_code=501,
            detail=APIError(
                error_code="PDF_NOT_IMPLEMENTED",
                message="PDF processing not yet implemented. Team Member 3 will add this functionality.",
                timestamp=datetime.now()
            ).model_dump()
        )

# TODO: Team Member 2 - Batch processing endpoint
@app.post("/api/v1/batch-analyze")
async def batch_analyze():
    """
    Process CSV batch of features
    Team Member 2 will implement this endpoint
    """
    raise HTTPException(
        status_code=501,
        detail=APIError(
            error_code="NOT_IMPLEMENTED",
            message="Batch processing not yet implemented. Team Member 2 will add this functionality.",
            timestamp=datetime.now()
        ).model_dump()
    )

# TODO: Team Member 2 - Batch status endpoint  
@app.get("/api/v1/batch-status/{batch_id}")
async def get_batch_status(batch_id: str):
    """
    Get status of batch processing job
    Team Member 2 will implement this endpoint
    """
    raise HTTPException(
        status_code=501,
        detail=APIError(
            error_code="NOT_IMPLEMENTED", 
            message="Batch status tracking not yet implemented. Team Member 2 will add this functionality.",
            timestamp=datetime.now()
        ).model_dump()
    )

# System metrics endpoint (basic)
@app.get("/api/v1/metrics")
async def get_metrics():
    """
    Basic system metrics
    Team Member 1 will enhance with detailed performance tracking
    """
    
    basic_metrics = {
        "timestamp": datetime.now(),
        "system_status": "operational",
        "feature_flags": {
            "real_mcps_enabled": True,  # Always true - no mock fallbacks
            "batch_processing_enabled": settings.enable_batch_processing
        },
        "phase": "1B - Basic Implementation"
    }
    
    # TODO: Team Member - Add detailed metrics
    # basic_metrics["performance"] = {
    #     "avg_analysis_time": await get_avg_analysis_time(),
    #     "requests_per_minute": await get_request_rate(),
    #     "success_rate": await get_success_rate()
    # }
    
    return basic_metrics

# Model selection endpoints
@app.get("/api/v1/models/available")
async def get_available_models():
    """Get available models (Gemini and Claude)"""
    return {
        "gemini_models": GEMINI_MODELS,
        "claude_models": CLAUDE_MODELS,
        "current_model": llm_client.preferred_model or "claude-sonnet-4-20250514"
    }

@app.post("/api/v1/models/select")
async def select_model(model_data: dict):
    """Set preferred model (Gemini or Claude)"""
    model_id = model_data.get("model_id")
    if model_id in GEMINI_MODELS or model_id in CLAUDE_MODELS:
        llm_client.set_preferred_model(model_id)
        return {"status": "success", "model": model_id}
    else:
        available_models = list(GEMINI_MODELS.keys()) + list(CLAUDE_MODELS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model ID. Available models: {available_models}"
        )

# Development helper endpoints
if settings.environment == "development":
    
    @app.get("/api/v1/dev/terminology")
    async def get_terminology():
        """Development endpoint to view loaded terminology"""
        from .core.agents.json_refactorer import JSONRefactorer
        refactorer = JSONRefactorer()
        return refactorer.terminology
    
    @app.get("/api/v1/dev/mcp-status")
    async def get_mcp_status():
        """Development endpoint to check MCP server status"""
        from .services.mcp_client import MCPSearchClient
        mcp_client = MCPSearchClient()
        return await mcp_client.health_check_all_services()
    
    @app.get("/api/v1/dev/test-model")
    async def test_current_model():
        """Test endpoint to verify which model is actually being used"""
        try:
            response = await llm_client.complete(
                "Hello! Please respond with just your model name/version.",
                max_tokens=50,
                temperature=0.1
            )
            return {
                "status": "success",
                "llm_response_model": response.get("model", "unknown"),
                "llm_response_content": response.get("content", "no content"),
                "configured_model": llm_client.preferred_model,
                "tokens_used": response.get("tokens_used", 0)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "configured_model": llm_client.preferred_model
            }

# Include API endpoints for frontend integration
from .api.endpoints import hitl, document_management, results, legal_chat, chat_management, batch

app.include_router(hitl.router)
app.include_router(document_management.router)
app.include_router(results.router)
app.include_router(legal_chat.router)
app.include_router(chat_management.router)
app.include_router(batch.router)

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Standard HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": "HTTP_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again.",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False,
        log_level=settings.log_level.lower()
    )