"""
Legal compliance chat endpoint - Fully LLM-orchestrated autonomous agent.
Real-time agent orchestration with tool calling and HITL gates, similar to Claude Code/Cursor.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import uuid
import json
import asyncio

from ...core.agents.lawyer_trd_agent import LawyerTRDAgent
from ...core.llm_service import llm_client
from .hitl import WorkflowStartRequest, active_workflows, send_hitl_prompt, wait_for_hitl_response, pending_hitl_prompts

router = APIRouter(prefix="/api", tags=["legal-chat"])
logger = logging.getLogger(__name__)

# Initialize the lawyer agent for MCP calls
lawyer_agent = LawyerTRDAgent()

# Agent state management
agent_sessions = {}

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None

class AgentAction(BaseModel):
    action_type: str  # "mcp_call", "analysis", "response", "hitl_prompt"
    details: Dict[str, Any]
    requires_approval: bool = False

class HITLPrompt(BaseModel):
    prompt_id: str
    question: str
    options: list[str]
    context: dict = {}

class ReasoningStep(BaseModel):
    type: str  # 'llm_decision', 'mcp_call', 'analysis', 'hitl_prompt'
    content: str
    duration: Optional[float] = None
    timestamp: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    workflow_started: Optional[bool] = False
    workflow_id: Optional[str] = None
    hitl_prompt: Optional[HITLPrompt] = None
    reasoning: Optional[List[ReasoningStep]] = None
    reasoning_duration: Optional[float] = None
    is_reasoning_complete: Optional[bool] = None

class AgentState(BaseModel):
    session_id: str
    conversation_history: List[Dict[str, str]]
    current_task: Optional[str] = None
    tool_results: List[Dict[str, Any]] = []
    reasoning_steps: List[ReasoningStep] = []
    start_time: Optional[datetime] = None
    pending_mcp_decision: Optional[Dict[str, str]] = None
    status: str = "active"  # active, waiting_hitl, completed, error

@router.post("/legal-chat", response_model=ChatResponse)
async def legal_compliance_chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Autonomous LLM agent for legal compliance - fully orchestrated like Claude Code/Cursor
    """
    
    logger.info(f"🤖 AUTONOMOUS AGENT - Message: '{request.message[:100]}...'")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        # Generate unique agent session
        session_id = f"agent-{uuid.uuid4().hex[:8]}"
        
        # Initialize agent state
        start_time = datetime.now()
        agent_sessions[session_id] = AgentState(
            session_id=session_id,
            conversation_history=[{"role": "user", "content": request.message}],
            current_task=f"legal_analysis: {request.message[:50]}...",
            start_time=start_time,
            status="active"
        )
        
        # Start autonomous agent loop
        background_tasks.add_task(_run_autonomous_agent, session_id, request.message, request.context)
        
        # Add agent activation as reasoning step
        agent_sessions[session_id].reasoning_steps.append(ReasoningStep(
            type="agent_startup",
            content=f"🤖 **Autonomous Legal Agent Activated**\n\nStarting autonomous analysis of: \"{request.message[:100]}...\"\n\n**Agent Session**: `{session_id}`\n\nI'll analyze your request and autonomously determine what actions to take.",
            duration=0.1,
            timestamp=datetime.now().isoformat()
        ))
        
        return ChatResponse(
            response="⏳ Analyzing your request...",
            timestamp=datetime.now().isoformat(),
            workflow_started=True,
            workflow_id=session_id,
            reasoning=[agent_sessions[session_id].reasoning_steps[0]],
            reasoning_duration=0.1,
            is_reasoning_complete=False
        )
        
    except Exception as e:
        logger.error(f"❌ Agent initialization error: {str(e)}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start autonomous agent. Please try again."
        )

async def _run_autonomous_agent(session_id: str, user_message: str, context: Optional[str]):
    """
    Autonomous LLM agent loop - like Claude Code/Cursor agent orchestration.
    The LLM has full autonomy to decide next actions, call tools, and interact.
    """
    
    agent_state = agent_sessions[session_id]
    logger.info(f"🤖 Starting autonomous agent loop for session {session_id}")
    
    try:
        # Main agent orchestration loop
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations and agent_state.status == "active":
            iteration += 1
            logger.info(f"🔄 Agent iteration {iteration}/{max_iterations}")
            
            # Get next action from LLM agent
            next_action = await _agent_decide_next_action(session_id, user_message, context)
            
            if not next_action:
                logger.warning(f"❌ Agent couldn't decide next action - ending loop")
                break
                
            logger.info(f"🎯 Agent decided: {next_action.action_type}")
            
            # Execute the action
            if next_action.action_type == "mcp_call":
                # MCP calls require HITL approval - send HITL prompt first
                await _agent_send_mcp_approval_prompt(session_id, next_action)
                agent_state.status = "waiting_hitl"
                break  # Wait for user approval
            elif next_action.action_type == "analysis":
                await _agent_perform_analysis(session_id, next_action)
            elif next_action.action_type == "response":
                await _agent_send_final_response(session_id, next_action)
                break  # End the loop after final response
            elif next_action.action_type == "hitl_prompt":
                await _agent_send_hitl_prompt(session_id, next_action)
                agent_state.status = "waiting_hitl"
                break  # Wait for user input
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.5)
        
        if iteration >= max_iterations:
            logger.warning(f"⚠️ Agent hit max iterations limit")
            agent_state.status = "completed"
            # Send timeout message
            active_workflows[session_id] = {
                "id": session_id,
                "status": "complete",
                "final_response": "⏰ **Agent Analysis Complete**\n\nI've reached my processing limit. The analysis I've performed so far is available above.",
                "completed_at": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"❌ Autonomous agent failed for {session_id}: {e}")
        agent_state.status = "error"
        active_workflows[session_id] = {
            "id": session_id,
            "status": "error",
            "error": f"Agent encountered an error: {str(e)}",
            "completed_at": datetime.now().isoformat()
        }

async def _agent_decide_next_action(session_id: str, user_message: str, context: Optional[str]) -> Optional[AgentAction]:
    """
    Autonomous LLM agent decides what to do next - like Claude Code's tool calling system.
    The agent has full autonomy to choose actions based on conversation state.
    """
    
    agent_state = agent_sessions[session_id]
    decision_start = datetime.now()
    
    # Build context from conversation history and tool results
    conversation_context = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in agent_state.conversation_history
    ])
    
    tool_results_context = "\n".join([
        f"Tool Result: {json.dumps(result, indent=2)}"
        for result in agent_state.tool_results
    ])
    
    # Build reasoning steps context to show agent what it has already done
    reasoning_steps_context = "\n".join([
        f"Step {i+1}: {step.type.upper()} - {step.content}"
        for i, step in enumerate(agent_state.reasoning_steps)
    ]) or "No previous reasoning steps"
    
    # Count how many analysis steps have been done
    analysis_count = len([step for step in agent_state.reasoning_steps if step.type == "llm_decision" and "analysis" in step.content.lower()])
    
    # Autonomous agent system prompt with continuity
    system_prompt = f"""You are an autonomous legal compliance agent with full decision-making authority.

CURRENT CONTEXT:
User Request: {user_message}
Conversation History:
{conversation_context}

PREVIOUS REASONING STEPS:
{reasoning_steps_context}

Previous Tool Results:
{tool_results_context}

STATE ANALYSIS:
- Analysis decisions made: {analysis_count}
- Tool calls made: {len(agent_state.tool_results)}
- Current iteration: Look at your previous reasoning steps above

AVAILABLE ACTIONS:
1. "mcp_call" - Call MCP tools (legal_mcp.search_documents, requirements_mcp.search_requirements)
2. "analysis" - Perform internal analysis/reasoning (ONLY if you haven't already analyzed this specific aspect)
3. "response" - Send final response to user (when you have sufficient information)
4. "hitl_prompt" - Ask user for approval/input (ONLY for MCP tool approval)

AGENT RULES:
- You have FULL AUTONOMY to decide next actions
- AVOID REPETITION: Look at your previous reasoning steps - don't repeat the same analysis
- BUILD ON PREVIOUS WORK: Each step should advance toward a complete response
- For simple questions: Use "response" action directly
- For complex legal queries needing external data: Use "mcp_call"
- PROGRESS REQUIREMENT: Each decision must move closer to answering the user's question

DECISION LOGIC:
- If you've already analyzed the core issues multiple times → Use "mcp_call" or "response"
- If you need specific legal/regulatory data → Use "mcp_call"
- If you have sufficient information → Use "response"
- If you need to analyze a NEW aspect not covered in previous steps → Use "analysis"

DECISION FORMAT:
Respond with ONE action type and explain your reasoning:

ACTION_TYPE: [mcp_call|analysis|response|hitl_prompt]
REASONING: [why you chose this action AND how it advances beyond your previous steps]
DETAILS: [specific details for the action]

What is your next action?"""

    try:
        response = await llm_client.complete(
            system_prompt,
            max_tokens=300,
            temperature=0.1
        )
        
        content = response.get("content", "").strip()
        logger.info(f"🧠 Agent decision: {content[:200]}...")
        
        # Parse agent decision with robust parsing
        action_type = None
        reasoning = ""
        details = {}
        
        # Primary parsing method
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith("ACTION_TYPE:"):
                action_type = line.replace("ACTION_TYPE:", "").strip()
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("DETAILS:"):
                details_str = line.replace("DETAILS:", "").strip()
                details = {"description": details_str}
        
        # Fallback parsing - look for action types anywhere in the text
        if not action_type or action_type not in ["mcp_call", "analysis", "response", "hitl_prompt"]:
            content_lower = content.lower()
            if "mcp_call" in content_lower:
                action_type = "mcp_call"
                reasoning = "Fallback: Detected mcp_call in response"
            elif "analysis" in content_lower and analysis_count < 3:  # Allow max 3 analysis steps
                action_type = "analysis"
                reasoning = "Fallback: Detected analysis request"
            elif "response" in content_lower or analysis_count >= 3:
                action_type = "response"
                reasoning = "Fallback: Ready to provide response"
            else:
                # Last resort - default to response after multiple analysis attempts
                action_type = "response"
                reasoning = "Fallback: Defaulting to response after multiple reasoning steps"
                
            details = {"description": content[:100]}
        
        if not action_type:
            logger.warning(f"❌ Could not determine action type from: {content[:200]}")
            return None
            
        # Determine if approval needed
        requires_approval = action_type == "mcp_call"
        
        # Record reasoning step with timing
        decision_duration = (datetime.now() - decision_start).total_seconds()
        agent_state.reasoning_steps.append(ReasoningStep(
            type="llm_decision",
            content=f"Decided to {action_type}: {reasoning}",
            duration=decision_duration,
            timestamp=datetime.now().isoformat()
        ))
        
        return AgentAction(
            action_type=action_type,
            details={
                "reasoning": reasoning,
                "description": details.get("description", ""),
                "raw_response": content
            },
            requires_approval=requires_approval
        )
        
    except Exception as e:
        logger.error(f"❌ Agent decision failed: {e}")
        return None

async def _llm_decide_mcp_tool(session_id: str, action: AgentAction) -> Optional[Dict[str, str]]:
    """
    100% LLM-orchestrated MCP tool selection - NO HARDCODING
    """
    
    agent_state = agent_sessions[session_id]
    mcp_decision_start = datetime.now()
    
    # Build context for LLM decision
    conversation_context = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in agent_state.conversation_history[-5:]  # Last 5 messages for context
    ])
    
    tool_results_summary = "\n".join([
        f"Previous Tool: {result.get('tool', 'unknown')} - Success: {bool(result.get('result'))}"
        for result in agent_state.tool_results[-3:]  # Last 3 tool results
    ])
    
    # Pure LLM decision prompt
    decision_prompt = f"""You are an autonomous legal compliance agent. You must decide which MCP tool to call and what query to use.

AVAILABLE MCP TOOLS:
- legal_mcp: Search legal documents, regulations, laws, compliance rules
- requirements_mcp: Search platform requirements, technical specifications, business requirements

CONVERSATION CONTEXT:
{conversation_context}

PREVIOUS TOOL RESULTS:
{tool_results_summary}

CURRENT ACTION DETAILS:
{action.details}

DECISION REQUIRED:
Based on the conversation context and what you're trying to accomplish, decide:
1. Which MCP tool to call (legal_mcp OR requirements_mcp)
2. What specific query to send to that tool

RESPONSE FORMAT:
TOOL: [legal_mcp|requirements_mcp]
QUERY: [your specific search query]
REASONING: [why you chose this tool and query]

Make your decision based purely on context and reasoning - no keyword matching allowed."""

    try:
        response = await llm_client.complete(
            decision_prompt,
            max_tokens=200,
            temperature=0.1
        )
        
        content = response.get("content", "").strip()
        logger.info(f"🧠 LLM MCP decision: {content[:200]}...")
        
        # Parse LLM decision
        tool = None
        query = None
        reasoning = ""
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith("TOOL:"):
                tool = line.replace("TOOL:", "").strip()
            elif line.startswith("QUERY:"):
                query = line.replace("QUERY:", "").strip()
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
        
        if not tool or not query:
            logger.warning(f"❌ LLM failed to provide valid tool/query decision")
            return None
            
        if tool not in ["legal_mcp", "requirements_mcp"]:
            logger.warning(f"❌ LLM chose invalid tool: {tool}")
            return None
            
        # Record MCP decision reasoning
        mcp_decision_duration = (datetime.now() - mcp_decision_start).total_seconds()
        agent_state.reasoning_steps.append(ReasoningStep(
            type="mcp_call",
            content=f"Selected {tool} with query '{query}': {reasoning}",
            duration=mcp_decision_duration,
            timestamp=datetime.now().isoformat()
        ))
            
        return {
            "tool": tool,
            "query": query,
            "reasoning": reasoning
        }
        
    except Exception as e:
        logger.error(f"❌ LLM MCP tool decision failed: {e}")
        return None

async def _agent_execute_mcp_call(session_id: str, action: AgentAction):
    """
    Execute MCP tool calls autonomously (after user approval) - 100% LLM-orchestrated
    """
    
    agent_state = agent_sessions[session_id]
    
    try:
        # LLM decides which MCP tool to call and what query to use
        tool_decision = await _llm_decide_mcp_tool(session_id, action)
        
        if not tool_decision:
            logger.error("❌ LLM failed to decide MCP tool")
            return
            
        mcp_tool = tool_decision["tool"]
        query = tool_decision["query"]
        
        logger.info(f"🧠 LLM decided to call {mcp_tool} with query: {query}")
        
        # Execute the MCP call based on LLM decision
        if mcp_tool == "legal_mcp":
            result = await lawyer_agent.legal_mcp.search_documents(
                search_type="semantic",
                query=query
            )
        elif mcp_tool == "requirements_mcp":
            result = await lawyer_agent.requirements_mcp.search_requirements(
                search_type="semantic", 
                query=query
            )
        else:
            logger.error(f"❌ Unknown MCP tool: {mcp_tool}")
            return
        
        # Store result for agent context
        agent_state.tool_results.append({
            "tool": mcp_tool,
            "query": query,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add to conversation history
        agent_state.conversation_history.append({
            "role": "tool",
            "content": f"MCP Tool {mcp_tool} executed with result: {json.dumps(result, indent=2)[:200]}..."
        })
        
        logger.info(f"✅ Agent MCP call completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Agent MCP call failed: {e}")
        agent_state.tool_results.append({
            "tool": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

async def _agent_perform_analysis(session_id: str, action: AgentAction):
    """
    Agent performs internal analysis/reasoning step - ACTUALLY analyze using LLM
    """
    
    agent_state = agent_sessions[session_id]
    analysis_start = datetime.now()
    
    try:
        # Get the original user message for analysis context
        user_message = ""
        for msg in agent_state.conversation_history:
            if msg['role'] == 'user' and not msg.get('hitl_response', False):
                user_message = msg['content']
                break
        
        # Build analysis context
        previous_analysis = "\n".join([
            step.content for step in agent_state.reasoning_steps 
            if step.type == "analysis" and step.content
        ]) or "No previous analysis"
        
        analysis_prompt = f"""You are analyzing this legal compliance request. Perform a structured analysis.

USER REQUEST:
{user_message}

PREVIOUS ANALYSIS:
{previous_analysis}

ANALYSIS TASK:
{action.details.get('description', 'Analyze the legal compliance aspects')}

Perform a detailed analysis addressing:
1. Key legal concepts mentioned
2. Potential compliance issues identified
3. Regulatory areas that need investigation
4. Specific concerns or red flags
5. What additional information is needed

Provide your analysis in structured format:"""
        
        # Perform actual LLM analysis
        response = await llm_client.complete(
            analysis_prompt,
            max_tokens=500,
            temperature=0.1
        )
        
        analysis_result = response.get("content", "Analysis failed").strip()
        logger.info(f"🧠 Agent completed analysis: {analysis_result[:200]}...")
        
        # Store the actual analysis result in conversation history
        agent_state.conversation_history.append({
            "role": "analysis",
            "content": f"Internal Analysis Result:\n{analysis_result}"
        })
        
        # Record the analysis as a reasoning step with actual content
        analysis_duration = (datetime.now() - analysis_start).total_seconds()
        agent_state.reasoning_steps.append(ReasoningStep(
            type="analysis",
            content=f"Performed analysis: {analysis_result[:100]}...",
            duration=analysis_duration,
            timestamp=datetime.now().isoformat()
        ))
        
        logger.info(f"✅ Agent analysis completed with actual results")
        
    except Exception as e:
        logger.error(f"❌ Agent analysis failed: {e}")
        # Still add something to prevent endless loop
        agent_state.conversation_history.append({
            "role": "analysis",
            "content": f"Analysis failed: {str(e)}"
        })

async def _agent_send_final_response(session_id: str, action: AgentAction):
    """
    Agent sends final response to user and completes the workflow
    """
    
    agent_state = agent_sessions[session_id]
    
    try:
        # Extract just the clean response content
        response_content = action.details.get("description", "")
        
        # Mark workflow as complete with clean response
        active_workflows[session_id] = {
            "id": session_id,
            "status": "complete", 
            "final_response": response_content,  # Just the clean answer
            "completed_at": datetime.now().isoformat(),
            "tool_results_count": len(agent_state.tool_results)
        }
        
        agent_state.status = "completed"
        
        logger.info(f"✅ Agent sent final response for session {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Agent final response failed: {e}")

async def _agent_send_mcp_approval_prompt(session_id: str, action: AgentAction):
    """
    Agent sends HITL prompt for MCP tool approval
    """
    
    try:
        # Get the MCP tool decision first
        tool_decision = await _llm_decide_mcp_tool(session_id, action)
        
        if not tool_decision:
            logger.error("❌ Failed to get MCP tool decision")
            return
            
        # Create HITL prompt for MCP approval
        await send_hitl_prompt(session_id, {
            "type": "mcp_approval",
            "question": f"I want to search {tool_decision['tool']} for: '{tool_decision['query']}'. Should I proceed?",
            "options": ["Approve", "Skip"],
            "context": {
                "mcp_tool": tool_decision['tool'],
                "query": tool_decision['query'],
                "reasoning": tool_decision['reasoning'],
                "action_details": action.details
            }
        })
        
        # Store the tool decision for later execution
        agent_sessions[session_id].pending_mcp_decision = tool_decision
        
        logger.info(f"🔒 Agent sent MCP approval prompt for session {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Agent MCP approval prompt failed: {e}")

async def _agent_send_hitl_prompt(session_id: str, action: AgentAction):
    """
    Agent sends HITL prompt as inline chat message for user approval
    """
    
    try:
        # Create HITL prompt that will appear as inline chat message
        await send_hitl_prompt(session_id, {
            "type": "agent_approval",
            "question": action.details.get("description", "Approve this action?"),
            "options": ["Approve", "Skip"],
            "context": {
                "action_type": action.action_type,
                "reasoning": action.details.get("reasoning", ""),
                "agent_decision": True
            }
        })
        
        logger.info(f"🔒 Agent sent HITL prompt for session {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Agent HITL prompt failed: {e}")

# Agent continuation after HITL response
async def _agent_continue_after_hitl(session_id: str, user_response: str):
    """
    Continue autonomous agent operation after user responds to HITL prompt
    """
    
    agent_state = agent_sessions[session_id]
    
    try:
        logger.info(f"🔄 Agent continuing after HITL response: {user_response}")
        
        # Add user response to conversation history
        agent_state.conversation_history.append({
            "role": "user_hitl",
            "content": f"HITL Response: {user_response}"
        })
        
        # If approved, execute pending MCP call or continue
        if "✅" in user_response or "Approve" in user_response:
            # If there's a pending MCP decision, execute it
            if agent_state.pending_mcp_decision:
                await _execute_approved_mcp_call(session_id)
            
            # Resume agent loop
            agent_state.status = "active"
        else:
            # User declined - clear pending decision and continue
            agent_state.pending_mcp_decision = None
            agent_state.status = "active"
            
        logger.info(f"✅ Agent ready to continue after HITL")
        
    except Exception as e:
        logger.error(f"❌ Agent HITL continuation failed: {e}")

async def _execute_approved_mcp_call(session_id: str):
    """
    Execute the MCP call that was approved by the user
    """
    
    agent_state = agent_sessions[session_id]
    tool_decision = agent_state.pending_mcp_decision
    
    if not tool_decision:
        logger.error("❌ No pending MCP decision to execute")
        return
    
    try:
        mcp_start = datetime.now()
        
        # Execute the approved MCP call
        if tool_decision["tool"] == "legal_mcp":
            result = await lawyer_agent.legal_mcp.search_documents(
                search_type="semantic",
                query=tool_decision["query"]
            )
        elif tool_decision["tool"] == "requirements_mcp":
            result = await lawyer_agent.requirements_mcp.search_requirements(
                search_type="semantic", 
                query=tool_decision["query"]
            )
        else:
            logger.error(f"❌ Unknown MCP tool: {tool_decision['tool']}")
            return
        
        # Store result for agent context
        agent_state.tool_results.append({
            "tool": tool_decision["tool"],
            "query": tool_decision["query"],
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add to conversation history
        agent_state.conversation_history.append({
            "role": "tool",
            "content": f"MCP Tool {tool_decision['tool']} executed with result: {json.dumps(result, indent=2)[:200]}..."
        })
        
        # Record the MCP execution as reasoning step
        mcp_duration = (datetime.now() - mcp_start).total_seconds()
        agent_state.reasoning_steps.append(ReasoningStep(
            type="mcp_call",
            content=f"Executed {tool_decision['tool']} with query '{tool_decision['query']}' - Found {len(result.get('results', []))} results",
            duration=mcp_duration,
            timestamp=datetime.now().isoformat()
        ))
        
        # Clear the pending decision
        agent_state.pending_mcp_decision = None
        
        logger.info(f"✅ Executed approved MCP call: {tool_decision['tool']}")
        
    except Exception as e:
        logger.error(f"❌ MCP call execution failed: {e}")
        agent_state.pending_mcp_decision = None

@router.get("/legal-chat/suggestions")
async def get_chat_suggestions():
    """Get suggested questions for legal chat"""
    return {
        "suggestions": [
            "Analyze this Utah Social Media requirement",
            "Check compliance with EU DSA regulations",
            "Review TikTok Live Shopping legal requirements",
            "Analyze Creator Fund compliance obligations"
        ]
    }

@router.post("/legal-chat/hitl-respond")
async def respond_to_inline_hitl(request: dict):
    """Handle HITL response from inline chat prompts in sidebar"""
    prompt_id = request.get("prompt_id")
    response = request.get("response") 
    workflow_id = request.get("workflow_id")
    
    logger.info(f"🎯 Autonomous Agent HITL response: {response} for session {workflow_id}")
    
    if not workflow_id:
        raise HTTPException(status_code=400, detail="Workflow ID required")
    
    # Check if it's an agent session
    if workflow_id in agent_sessions:
        # Continue autonomous agent after HITL response
        await _agent_continue_after_hitl(workflow_id, response)
        
        # Store response for agent to pick up
        if workflow_id not in active_workflows:
            active_workflows[workflow_id] = {"id": workflow_id, "status": "running"}
        active_workflows[workflow_id]["hitl_response"] = response
        active_workflows[workflow_id]["hitl_prompt_id"] = prompt_id
        
    elif workflow_id in active_workflows:
        # Legacy workflow support
        active_workflows[workflow_id]["hitl_response"] = response
        active_workflows[workflow_id]["hitl_prompt_id"] = prompt_id
    else:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"status": "response_received", "response": response, "agent_session": workflow_id in agent_sessions}

@router.get("/legal-chat/poll/{workflow_id}")
async def poll_for_next_message(workflow_id: str):
    """Poll for next autonomous agent message or HITL prompt (as inline chat messages)"""
    
    # Check if it's an autonomous agent session
    if workflow_id in agent_sessions:
        agent_state = agent_sessions[workflow_id]
        
        # Check for pending HITL prompts (to show as inline chat messages in sidebar)
        for prompt_id, prompt in pending_hitl_prompts.items():
            if prompt.get("workflow_id") == workflow_id and not prompt.get("sent", False):
                # Mark as sent
                pending_hitl_prompts[prompt_id]["sent"] = True
                
                return ChatResponse(
                    response=f"🤖 **Agent Approval Required**\n\n{prompt.get('question', 'Should I proceed?')}",
                    timestamp=datetime.now().isoformat(),
                    workflow_started=True,
                    workflow_id=workflow_id,
                    hitl_prompt=HITLPrompt(
                        prompt_id=prompt_id,
                        question=prompt.get("question", "Should I proceed with this action?"),
                        options=prompt.get("options", ["Approve", "Skip"]),
                        context=prompt.get("context", {})
                    )
                )
        
        # Check if agent completed
        if workflow_id in active_workflows and active_workflows[workflow_id].get("status") == "complete":
            final_response = active_workflows[workflow_id].get("final_response", "Agent analysis complete")
            
            # Calculate total reasoning duration
            total_duration = 0
            if agent_state.start_time:
                total_duration = (datetime.now() - agent_state.start_time).total_seconds()
            
            return ChatResponse(
                response=final_response,
                timestamp=datetime.now().isoformat(),
                workflow_started=False,
                workflow_id=workflow_id,
                reasoning=agent_state.reasoning_steps,
                reasoning_duration=total_duration,
                is_reasoning_complete=True
            )
        
        # Check if agent has error
        if workflow_id in active_workflows and active_workflows[workflow_id].get("status") == "error":
            error_msg = f"❌ **Autonomous Agent Error**: {active_workflows[workflow_id].get('error', 'Unknown error')}"
            return ChatResponse(
                response=error_msg,
                timestamp=datetime.now().isoformat(),
                workflow_started=False,
                workflow_id=workflow_id
            )
        
        # Agent still processing
        status_msg = "active" if agent_state.status == "active" else agent_state.status
        
        # Calculate current reasoning duration
        current_duration = 0
        if agent_state.start_time:
            current_duration = (datetime.now() - agent_state.start_time).total_seconds()
        
        return ChatResponse(
            response="⏳ Thinking...",
            timestamp=datetime.now().isoformat(),
            workflow_started=True,
            workflow_id=workflow_id,
            reasoning=agent_state.reasoning_steps,
            reasoning_duration=current_duration,
            is_reasoning_complete=False
        )
    
    # Legacy workflow support
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Session not found")
    
    workflow = active_workflows[workflow_id]
    
    # Check for pending HITL prompts (legacy)
    for prompt_id, prompt in pending_hitl_prompts.items():
        if prompt.get("workflow_id") == workflow_id and not prompt.get("sent", False):
            pending_hitl_prompts[prompt_id]["sent"] = True
            
            return ChatResponse(
                response="🤔 **Legacy Workflow Approval Required**",
                timestamp=datetime.now().isoformat(),
                workflow_started=True,
                workflow_id=workflow_id,
                hitl_prompt=HITLPrompt(
                    prompt_id=prompt_id,
                    question=prompt.get("question", "Approve action?"),
                    options=prompt.get("options", ["YES", "NO"]),
                    context=prompt.get("context", {})
                )
            )
    
    # Check workflow status
    if workflow.get("status") == "complete":
        return ChatResponse(
            response=workflow.get("final_response", "Analysis complete"),
            timestamp=datetime.now().isoformat(),
            workflow_started=False,
            workflow_id=workflow_id
        )
    elif workflow.get("status") == "error":
        return ChatResponse(
            response=f"❌ **Error**: {workflow.get('error', 'Unknown error')}",
            timestamp=datetime.now().isoformat(),
            workflow_started=False,
            workflow_id=workflow_id
        )
    
    # Still processing
    return ChatResponse(
        response="⏳ **Processing...**\n\nWorking on your request...",
        timestamp=datetime.now().isoformat(),
        workflow_started=True,
        workflow_id=workflow_id
    )

@router.get("/legal-chat/health")
async def legal_chat_health():
    """Health check for legal chat service"""
    return {"status": "healthy", "service": "legal-chat", "timestamp": datetime.now().isoformat()}