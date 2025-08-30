"""
Human-in-the-Loop (HITL) management endpoints for TRD workflows.
Handles workflow orchestration, progress updates, and user interactions.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

# Import the real lawyer agent for actual workflow execution
from ...core.agents.lawyer_trd_agent import LawyerTRDAgent

class HITLEnabledMCP:
    """Wrapper around MCP that asks for HITL approval before each call"""
    
    def __init__(self, original_mcp, mcp_type: str, hitl_callback):
        self.original_mcp = original_mcp
        self.mcp_type = mcp_type
        self.hitl_callback = hitl_callback
    
    async def search_documents(self, **kwargs):
        """Ask for approval before searching documents"""
        # Ask user for approval
        approval = await self.hitl_callback({
            "question": f"Should I search the {self.mcp_type} database?",
            "options": ["YES - Search documents", "NO - Skip search"],
            "context": {
                "mcp_type": self.mcp_type,
                "method": "search_documents",
                "params": kwargs
            }
        })
        
        if "YES" in approval:
            return await self.original_mcp.search_documents(**kwargs)
        else:
            return {"results": [], "message": f"User declined {self.mcp_type} search"}
    
    async def search_requirements(self, **kwargs):
        """Ask for approval before searching requirements"""
        # Ask user for approval  
        approval = await self.hitl_callback({
            "question": f"Should I search the {self.mcp_type} database?",
            "options": ["YES - Search requirements", "NO - Skip search"],
            "context": {
                "mcp_type": self.mcp_type,
                "method": "search_requirements", 
                "params": kwargs
            }
        })
        
        if "YES" in approval:
            return await self.original_mcp.search_requirements(**kwargs)
        else:
            return {"results": [], "message": f"User declined {self.mcp_type} search"}

router = APIRouter(prefix="/api/workflow", tags=["workflow-hitl"])

# In-memory storage for demo (would be database in production)
active_workflows: Dict[str, Dict] = {}
workflow_progress: Dict[str, Dict] = {}
pending_hitl_prompts: Dict[str, Dict] = {}

class WorkflowStartRequest(BaseModel):
    workflow_type: str  # workflow_1, workflow_2, workflow_3
    document_id: str

class HITLResponse(BaseModel):
    prompt_id: Optional[str] = None
    response: str
    timestamp: Optional[str] = None

class WorkflowResponse(BaseModel):
    id: str
    type: str
    status: str
    document_id: str
    created_at: str

@router.post("/start", response_model=WorkflowResponse)
async def start_workflow(request: WorkflowStartRequest, background_tasks: BackgroundTasks):
    """Start a TRD workflow with web-friendly HITL integration"""
    
    workflow_id = str(uuid.uuid4())
    
    workflow = {
        "id": workflow_id,
        "type": request.workflow_type,
        "status": "running",
        "document_id": request.document_id,
        "created_at": datetime.now().isoformat(),
        "current_step": 1,
        "total_steps": 5
    }
    
    active_workflows[workflow_id] = workflow
    
    # Start the workflow in background
    background_tasks.add_task(simulate_workflow, workflow_id, request.workflow_type)
    
    return WorkflowResponse(**workflow)

async def simulate_workflow(workflow_id: str, workflow_type: str):
    """Execute workflow with progress updates and HITL prompts"""
    
    print(f"🚀 Starting workflow {workflow_id} of type {workflow_type}")
    
    try:
        if workflow_type == "workflow_3":
            # Requirements → Legal Compliance workflow
            await simulate_workflow_3(workflow_id)
        elif workflow_type == "workflow_1":
            # Legal → Requirements workflow
            await simulate_workflow_1(workflow_id)
        elif workflow_type == "workflow_2":
            # Past iteration detection workflow
            await simulate_workflow_2(workflow_id)
        elif workflow_type == "mcp_approval":
            # MCP tool approval workflow
            await simulate_mcp_approval_workflow(workflow_id)
        elif workflow_type == "lawyer_analysis":
            print(f"🧠 Executing lawyer workflow {workflow_id}")
            # Lawyer agent analysis with HITL
            await execute_lawyer_workflow(workflow_id)
        else:
            print(f"❌ Unknown workflow type: {workflow_type}")
            active_workflows[workflow_id]["status"] = "error"
            active_workflows[workflow_id]["error"] = f"Unknown workflow type: {workflow_type}"
            
    except Exception as e:
        # Mark workflow as error
        if workflow_id in active_workflows:
            active_workflows[workflow_id]["status"] = "error"
            active_workflows[workflow_id]["error"] = str(e)

async def simulate_workflow_3(workflow_id: str):
    """Simulate Workflow 3: Requirements → Legal Compliance"""
    
    # Step 1: Extract requirements
    await update_progress(workflow_id, "Extracting requirements from document...", 1, 5, 20)
    await asyncio.sleep(2)
    
    # Step 2: Analyze first requirement - trigger HITL for jurisdiction
    await update_progress(workflow_id, "Analyzing requirement 1 of 15...", 2, 5, 30)
    await asyncio.sleep(1)
    
    # HITL Prompt: Region selection
    await send_hitl_prompt(workflow_id, {
        "type": "region_selection",
        "question": "This requirement doesn't specify a jurisdiction. Which regions should we check?",
        "options": ["Utah", "EU", "California", "Florida", "Brazil", "All Regions"],
        "context": {
            "requirement": "System shall provide age verification for users under 18"
        }
    })
    
    # Wait for user response
    active_workflows[workflow_id]["status"] = "waiting_hitl"
    response = await wait_for_hitl_response(workflow_id)
    active_workflows[workflow_id]["status"] = "running"
    
    # Step 3: Continue analysis with selected jurisdiction
    await update_progress(workflow_id, f"Checking compliance for {response}...", 3, 5, 60)
    await asyncio.sleep(2)
    
    # HITL Prompt: Compliance assessment
    await send_hitl_prompt(workflow_id, {
        "type": "compliance_assessment",
        "question": "How should this age verification requirement be classified?",
        "options": ["COMPLIANT", "NON-COMPLIANT", "NEEDS-REVIEW", "REQUIRES-MODIFICATION"],
        "context": {
            "requirement": "System shall provide age verification for users under 18",
            "conflicting_regulations": ["Utah Social Media Act requires specific age verification methods"]
        }
    })
    
    response2 = await wait_for_hitl_response(workflow_id)
    
    # Step 4: Generate report
    await update_progress(workflow_id, "Generating compliance report...", 4, 5, 90)
    await asyncio.sleep(1)
    
    # Step 5: Complete
    await update_progress(workflow_id, "Workflow completed successfully", 5, 5, 100)
    active_workflows[workflow_id]["status"] = "complete"
    active_workflows[workflow_id]["completed_at"] = datetime.now().isoformat()

async def simulate_workflow_1(workflow_id: str):
    """Simulate Workflow 1: Legal → Requirements"""
    
    await update_progress(workflow_id, "Loading legal documents...", 1, 4, 25)
    await asyncio.sleep(1)
    
    await update_progress(workflow_id, "Searching requirements database...", 2, 4, 50)
    await asyncio.sleep(2)
    
    await update_progress(workflow_id, "Analyzing compliance...", 3, 4, 75)
    await asyncio.sleep(2)
    
    await update_progress(workflow_id, "Generating report...", 4, 4, 100)
    active_workflows[workflow_id]["status"] = "complete"

async def simulate_workflow_2(workflow_id: str):
    """Simulate Workflow 2: Past iteration detection"""
    
    await update_progress(workflow_id, "Scanning for similar documents...", 1, 3, 33)
    await asyncio.sleep(1)
    
    # HITL Prompt: Past iteration decision
    await send_hitl_prompt(workflow_id, {
        "type": "yes_no",
        "question": "Found potential past iteration: 'Utah Social Media Act 2024'. Should we delete the old version?",
        "options": ["YES", "NO"],
        "context": {
            "new_document": "Utah Social Media Act 2025",
            "old_document": "Utah Social Media Act 2024",
            "similarity_score": 0.87
        }
    })
    
    active_workflows[workflow_id]["status"] = "waiting_hitl"
    response = await wait_for_hitl_response(workflow_id)
    active_workflows[workflow_id]["status"] = "running"
    
    await update_progress(workflow_id, f"Processing decision: {response}...", 2, 3, 66)
    await asyncio.sleep(1)
    
    await update_progress(workflow_id, "Workflow completed", 3, 3, 100)
    active_workflows[workflow_id]["status"] = "complete"

async def simulate_mcp_approval_workflow(workflow_id: str):
    """Simulate MCP approval workflow with user prompts for tool calls"""
    
    # Step 1: Initialize workflow
    await update_progress(workflow_id, "Analyzing request for MCP tool requirements...", 1, 4, 25)
    await asyncio.sleep(1)
    
    # Step 2: Ask user to approve Legal MCP search
    await send_hitl_prompt(workflow_id, {
        "type": "mcp_approval",
        "question": "Should I search the Legal MCP database for relevant regulations and legal documents?",
        "options": [
            "YES - Search legal documents",
            "NO - Skip legal search", 
            "MORE INFO - What will be searched?"
        ],
        "context": {
            "mcp_type": "legal_mcp",
            "search_query": "User's compliance question",
            "purpose": "Find relevant legal regulations and compliance requirements"
        }
    })
    
    # Wait for user approval for Legal MCP
    active_workflows[workflow_id]["status"] = "waiting_hitl"
    legal_approval = await wait_for_hitl_response(workflow_id)
    active_workflows[workflow_id]["status"] = "running"
    
    await update_progress(workflow_id, f"Legal MCP: {legal_approval}", 2, 4, 50)
    await asyncio.sleep(1)
    
    # Step 3: Ask user to approve Requirements MCP search  
    await send_hitl_prompt(workflow_id, {
        "type": "mcp_approval", 
        "question": "Should I search the Requirements MCP database for platform requirements and specifications?",
        "options": [
            "YES - Search requirements",
            "NO - Skip requirements search",
            "MORE INFO - What will be searched?"
        ],
        "context": {
            "mcp_type": "requirements_mcp",
            "search_query": "User's compliance question", 
            "purpose": "Find relevant platform requirements and technical specifications"
        }
    })
    
    # Wait for user approval for Requirements MCP
    active_workflows[workflow_id]["status"] = "waiting_hitl"
    requirements_approval = await wait_for_hitl_response(workflow_id)
    active_workflows[workflow_id]["status"] = "running"
    
    await update_progress(workflow_id, f"Requirements MCP: {requirements_approval}", 3, 4, 75)
    await asyncio.sleep(1)
    
    # Step 4: Generate final analysis based on approved searches
    await update_progress(workflow_id, "Generating analysis with approved MCP data...", 4, 4, 100)
    await asyncio.sleep(2)
    
    active_workflows[workflow_id]["status"] = "complete"
    active_workflows[workflow_id]["completed_at"] = datetime.now().isoformat()

async def execute_lawyer_workflow(workflow_id: str):
    """Execute lawyer agent workflow with HITL prompts for MCP approval"""
    
    try:
        # Step 1: Initialize analysis
        await update_progress(workflow_id, "Starting lawyer agent analysis...", 1, 4, 25)
        
        # Create a HITL callback function that sends prompts to the frontend
        async def hitl_callback(question_data):
            """HITL callback that sends prompts via SSE"""
            await send_hitl_prompt(workflow_id, {
                "type": "mcp_approval",
                "question": question_data.get("question", "Approve MCP call?"),
                "options": question_data.get("options", ["YES", "NO"]),
                "context": question_data.get("context", {})
            })
            
            # Wait for user response
            active_workflows[workflow_id]["status"] = "waiting_hitl"
            user_response = await wait_for_hitl_response(workflow_id)
            active_workflows[workflow_id]["status"] = "running"
            
            return user_response
        
        await update_progress(workflow_id, "Analyzing request for MCP requirements...", 2, 4, 50)
        
        # Step 2: Create lawyer agent with HITL-enabled MCPs
        lawyer_agent = LawyerTRDAgent()
        
        # Replace the original MCPs with HITL-enabled wrappers
        lawyer_agent.legal_mcp = HITLEnabledMCP(
            lawyer_agent.legal_mcp, 
            "Legal MCP", 
            hitl_callback
        )
        lawyer_agent.requirements_mcp = HITLEnabledMCP(
            lawyer_agent.requirements_mcp, 
            "Requirements MCP", 
            hitl_callback
        )
        
        # Step 3: Execute the workflow (now with HITL-enabled MCPs)
        document_id = f"chat-analysis-{workflow_id}"
        
        await update_progress(workflow_id, "Executing lawyer agent workflow...", 3, 4, 75)
        
        # Execute the lawyer agent workflow - MCP calls will now trigger HITL prompts
        query_data = {
            "query": f"Please analyze requirements document {document_id} for compliance with legal regulations using MCP search. Provide a comprehensive compliance analysis.",
            "context": {
                "requirements_document_id": document_id,
                "analysis_type": "requirements_compliance_check"
            }
        }
        compliance_report = await lawyer_agent.handle_user_query(query_data)
        
        await update_progress(workflow_id, "Analysis complete with MCP data", 4, 4, 100)
        
        # Store the results for the frontend
        active_workflows[workflow_id]["results"] = {
            "type": "compliance_report",
            "report": compliance_report,
            "total_requirements": compliance_report.total_requirements,
            "issues_found": len(compliance_report.compliance_issues)
        }
        
        active_workflows[workflow_id]["status"] = "complete"
        active_workflows[workflow_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        await update_progress(workflow_id, f"Error: {str(e)}", 4, 4, 100)
        active_workflows[workflow_id]["status"] = "error"
        active_workflows[workflow_id]["error"] = str(e)

async def update_progress(workflow_id: str, message: str, step: int, total_steps: int, progress: int):
    """Update workflow progress"""
    progress_data = {
        "workflow_id": workflow_id,
        "current_step": step,
        "total_steps": total_steps,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    workflow_progress[workflow_id] = progress_data

async def send_hitl_prompt(workflow_id: str, prompt_data: Dict[str, Any]):
    """Send HITL prompt to user"""
    prompt_id = str(uuid.uuid4())
    prompt = {
        "prompt_id": prompt_id,
        "workflow_id": workflow_id,
        "timestamp": datetime.now().isoformat(),
        **prompt_data
    }
    pending_hitl_prompts[prompt_id] = prompt

async def wait_for_hitl_response(workflow_id: str, timeout: int = 300) -> str:
    """Wait for user response to HITL prompt (non-blocking)"""
    # Check if response is already available
    workflow = active_workflows.get(workflow_id, {})
    if "hitl_response" in workflow:
        response = workflow.pop("hitl_response")
        return response
    
    # For non-blocking operation, check response periodically with short sleeps
    for _ in range(min(timeout, 60)):  # Max 60 seconds total wait
        await asyncio.sleep(1)
        workflow = active_workflows.get(workflow_id, {})
        if "hitl_response" in workflow:
            response = workflow.pop("hitl_response")
            return response
    
    # After 60 seconds, return default response to prevent hanging
    print(f"⚠️ HITL response timeout for workflow {workflow_id}, using default response")
    return "All Regions"

@router.get("/{workflow_id}/progress")
async def workflow_progress_stream(workflow_id: str):
    """SSE stream for real-time progress updates"""
    
    async def generate():
        while workflow_id in active_workflows:
            workflow = active_workflows[workflow_id]
            
            # Send progress update
            if workflow_id in workflow_progress:
                progress_event = {
                    "type": "progress",
                    "payload": workflow_progress[workflow_id]
                }
                yield f"data: {json.dumps(progress_event)}\n\n"
            
            # Send HITL prompt if available (only send each prompt once)
            for prompt_id, prompt in list(pending_hitl_prompts.items()):
                if prompt["workflow_id"] == workflow_id and not prompt.get("sent", False):
                    hitl_event = {
                        "type": "hitl_prompt", 
                        "payload": prompt
                    }
                    yield f"data: {json.dumps(hitl_event)}\n\n"
                    # Mark as sent to avoid sending again
                    pending_hitl_prompts[prompt_id]["sent"] = True
            
            # Send completion event
            if workflow["status"] == "complete":
                complete_event = {
                    "type": "workflow_complete",
                    "payload": {"workflow_id": workflow_id, "status": "complete"}
                }
                yield f"data: {json.dumps(complete_event)}\n\n"
                break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@router.post("/{workflow_id}/hitl/respond")
async def respond_to_hitl(workflow_id: str, response: HITLResponse):
    """Handle user response from HITL sidebar"""
    
    print(f"🎯 HITL Response received: workflow_id={workflow_id}, response={response}")
    
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Remove the pending prompt (if prompt_id is provided)
    if hasattr(response, 'prompt_id') and response.prompt_id in pending_hitl_prompts:
        del pending_hitl_prompts[response.prompt_id]
    
    # Store response for workflow to pick up
    active_workflows[workflow_id]["hitl_response"] = response.response
    
    print(f"✅ HITL Response stored: {response.response}")
    
    return {"status": "response_received", "prompt_id": getattr(response, 'prompt_id', 'unknown')}

@router.get("/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get current workflow state and any pending HITL prompts"""
    
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[workflow_id]
    
    # Get pending prompts for this workflow
    pending_prompts = [
        prompt for prompt in pending_hitl_prompts.values()
        if prompt["workflow_id"] == workflow_id
    ]
    
    return {
        **workflow,
        "pending_prompts": pending_prompts,
        "progress": workflow_progress.get(workflow_id)
    }