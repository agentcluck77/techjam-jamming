"""
Legal compliance chat endpoint - Fully LLM-orchestrated autonomous agent.
Real-time agent orchestration with tool calling and HITL gates, similar to Claude Code/Cursor.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import uuid
import json
import asyncio

from ...core.agents.lawyer_trd_agent import LawyerTRDAgent
from ...core.llm_service import llm_client
from ...core.models import ChatMessage as PersistentChatMessage
from ...services.chat_storage import chat_storage
from .hitl import WorkflowStartRequest, active_workflows, send_hitl_prompt, wait_for_hitl_response, pending_hitl_prompts

router = APIRouter(prefix="/api", tags=["legal-chat"])
logger = logging.getLogger(__name__)

# Initialize the lawyer agent for MCP calls
lawyer_agent = LawyerTRDAgent()

# Agent state management
agent_sessions = {}
agent_locks = {}  # Prevent concurrent agent loops
chat_request_locks = {}  # Prevent duplicate requests per chat

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    chat_id: Optional[str] = None  # For continuing existing chat sessions

class AgentAction(BaseModel):
    action_type: str  # "mcp_call", "analysis", "response", "hitl_prompt"
    details: Dict[str, Any]
    requires_approval: bool = False

class HITLPrompt(BaseModel):
    prompt_id: str
    question: str
    options: list[str]
    context: dict = {}
    mcp_tool: Optional[str] = None  # For MCP approval prompts
    mcp_query: Optional[str] = None  # Query being executed
    mcp_reason: Optional[str] = None  # One-line reason why this MCP call is needed

class ReasoningStep(BaseModel):
    type: str  # 'llm_decision', 'mcp_call', 'analysis', 'hitl_prompt'
    content: str
    duration: Optional[float] = None
    timestamp: str

class MCPExecution(BaseModel):
    tool: str
    query: str
    results_count: int
    execution_time: float
    result_summary: str
    timestamp: str
    raw_results: dict

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    workflow_started: Optional[bool] = False
    workflow_id: Optional[str] = None
    hitl_prompt: Optional[HITLPrompt] = None
    reasoning: Optional[List[ReasoningStep]] = None
    reasoning_duration: Optional[float] = None
    is_reasoning_complete: Optional[bool] = None
    mcp_executions: Optional[List[MCPExecution]] = None

class AgentState(BaseModel):
    session_id: str
    conversation_history: List[Dict[str, str]]
    current_task: Optional[str] = None
    tool_results: List[Dict[str, Any]] = []
    reasoning_steps: List[ReasoningStep] = []
    start_time: Optional[datetime] = None
    pending_mcp_decision: Optional[Dict[str, str]] = None
    status: str = "active"  # active, waiting_hitl, completed, error
    mcp_sent_count: int = 0  # Track sent MCP executions atomically
    mcp_executions_for_chat: List[Dict[str, Any]] = []  # Store MCP executions for frontend display

@router.post("/legal-chat-stream")
async def legal_compliance_chat_stream(request: ChatRequest):
    """
    Real-time streaming LLM responses - actual token streaming as they come from the LLM
    """
    
    logger.info(f"🌊 STREAMING CHAT - Message: '{request.message[:100]}...'")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    async def generate_stream():
        try:
            # Generate unique session for tracking
            session_id = f"stream-{uuid.uuid4().hex[:8]}"
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'session_id': session_id, 'message': 'Starting analysis...'})}\n\n"
            
            # Use LLM streaming for real-time token generation
            prompt = f"""Analyze this legal compliance request and provide a detailed assessment:

User Request: {request.message}

Provide a comprehensive legal compliance analysis focusing on:
1. Key regulatory areas that apply
2. Potential compliance risks
3. Specific requirements to address
4. Recommended next steps

Be thorough and specific in your analysis."""
            
            # Stream tokens as they come from the LLM
            full_response = ""
            async for chunk in llm_client.stream(prompt, max_tokens=1500, temperature=0.1):
                if chunk.get("content"):
                    full_response += chunk["content"]
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk['content'], 'session_id': session_id})}\n\n"
                elif chunk.get("done"):
                    yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'full_response': full_response})}\n\n"
                    break
            
        except Exception as e:
            logger.error(f"❌ Streaming chat error: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'Analysis failed: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@router.post("/legal-chat/session", response_model=ChatResponse)
async def legal_compliance_chat_session(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Persistent chat session endpoint - maintains conversation context across messages
    """
    
    logger.info(f"💬 PERSISTENT CHAT - Message: '{request.message[:100]}...'")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        # Get or create chat session
        if request.chat_id:
            # Continue existing chat
            chat_session = await chat_storage.get_chat(request.chat_id)
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            chat_id = request.chat_id
        else:
            # Create new chat session
            chat_session = await chat_storage.create_chat(
                title=None,  # Will auto-generate from message
                initial_message=request.message
            )
            chat_id = chat_session.id
        
        # Use per-chat lock to prevent duplicate requests
        if chat_id not in chat_request_locks:
            chat_request_locks[chat_id] = asyncio.Lock()
        
        # Acquire lock for this chat to prevent concurrent processing
        async with chat_request_locks[chat_id]:
            # Check if there's already an active agent for this chat
            active_sessions = [sid for sid, state in agent_sessions.items() 
                              if sid.startswith(f"chat-{chat_id}-") and state.status == "active"]
            
            if active_sessions:
                logger.warning(f"🔄 Active agent already exists for chat {chat_id}: {active_sessions[0]}")
                return ChatResponse(
                    response="⏳ Agent already processing your request...",
                    timestamp=datetime.now().isoformat(),
                    workflow_started=True,
                    workflow_id=active_sessions[0],
                    reasoning=[],
                    reasoning_duration=0.0,
                    is_reasoning_complete=False
                )
            
            # Add user message to persistent storage
            user_message = PersistentChatMessage(
                type="user",
                content=request.message,
                timestamp=datetime.now()
            )
            
            # Only add if we didn't already add it during creation
            if request.chat_id:
                await chat_storage.add_message(chat_session.id, user_message)
            
            # Generate unique agent session linked to chat
            session_id = f"chat-{chat_session.id}-{uuid.uuid4().hex[:8]}"
            
            # Build conversation context from chat history
            conversation_history = []
            for msg in chat_session.messages:
                conversation_history.append({
                    "role": msg.type if msg.type != "assistant" else "assistant",
                    "content": msg.content
                })
            
            # Initialize agent state with conversation history
            start_time = datetime.now()
            agent_sessions[session_id] = AgentState(
                session_id=session_id,
                conversation_history=conversation_history,
                current_task=f"legal_analysis: {request.message[:50]}...",
                start_time=start_time,
                status="active"
            )
            agent_locks[session_id] = asyncio.Lock()
            
            # Start autonomous agent loop
            background_tasks.add_task(_run_persistent_chat_agent, session_id, chat_session.id, request.message, request.context)
            
            # Add agent activation as reasoning step
            agent_sessions[session_id].reasoning_steps.append(ReasoningStep(
                type="agent_startup",
                content=f"🤖 **Legal Agent Activated** (Session: {chat_session.id})\n\nContinuing analysis with {len(conversation_history)} previous messages in context.",
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Persistent chat error: {str(e)}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start persistent chat session. Please try again."
        )

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
        
        # Initialize agent state and lock
        start_time = datetime.now()
        agent_sessions[session_id] = AgentState(
            session_id=session_id,
            conversation_history=[{"role": "user", "content": request.message}],
            current_task=f"legal_analysis: {request.message[:50]}...",
            start_time=start_time,
            status="active"
        )
        agent_locks[session_id] = asyncio.Lock()  # Prevent concurrent loops
        
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

async def _run_persistent_chat_agent(session_id: str, chat_id: str, user_message: str, context: Optional[str]):
    """
    Persistent chat agent - saves assistant responses to database
    """
    
    # Run the standard autonomous agent
    await _run_autonomous_agent(session_id, user_message, context)
    
    # After agent completes, save assistant response to database
    try:
        if session_id in active_workflows and active_workflows[session_id].get("status") == "complete":
            final_response = active_workflows[session_id].get("final_response", "")
            
            if final_response and final_response.strip():
                # Get reasoning steps and MCP executions for storage
                agent_state = agent_sessions.get(session_id)
                reasoning_steps = []
                mcp_executions = []
                
                if agent_state:
                    reasoning_steps = [
                        {
                            "type": step.type,
                            "content": step.content,
                            "duration": step.duration,
                            "timestamp": step.timestamp
                        } for step in agent_state.reasoning_steps
                    ]
                    
                    # Convert MCP executions from agent state
                    if hasattr(agent_state, 'mcp_executions_for_chat'):
                        mcp_executions = agent_state.mcp_executions_for_chat
                
                # Create assistant message
                assistant_message = PersistentChatMessage(
                    type="assistant",
                    content=final_response,
                    timestamp=datetime.now(),
                    model_used=llm_client.preferred_model,
                    reasoning_steps=reasoning_steps,
                    mcp_executions=mcp_executions
                )
                
                # Save to database
                await chat_storage.add_message(chat_id, assistant_message)
                logger.info(f"💾 Saved assistant response to chat {chat_id}")
                
    except Exception as e:
        logger.error(f"❌ Failed to save assistant response to database: {e}")

async def _run_autonomous_agent(session_id: str, user_message: str, context: Optional[str]):
    """
    Autonomous LLM agent loop - like Claude Code/Cursor agent orchestration.
    The LLM has full autonomy to decide next actions, call tools, and interact.
    """
    
    # Acquire lock to prevent concurrent agent loops
    if session_id not in agent_locks:
        logger.error(f"❌ No lock found for session {session_id}")
        return
        
    async with agent_locks[session_id]:
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
                    # Yield control aggressively to allow frontend polling between reasoning steps  
                    # Agent controls its own pacing - no artificial delays
                elif next_action.action_type == "response":
                    await _agent_send_final_response(session_id, next_action)
                    break  # End the loop after final response
                elif next_action.action_type == "hitl_prompt":
                    await _agent_send_hitl_prompt(session_id, next_action)
                    agent_state.status = "waiting_hitl"
                    break  # Wait for user input
                
                # Brief yield for frontend responsiveness (agent still controls overall pacing)
                await asyncio.sleep(0.05)  # 50ms yield for UI updates
            
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
    
    # Enhanced autonomous agent system prompt - 100% agent orchestrated
    system_prompt = f"""You are an autonomous legal compliance agent with complete decision-making authority. You operate like ChatGPT or Cursor - making all workflow decisions independently through reasoning.

=== CURRENT CONTEXT ===
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

=== AUTONOMOUS AGENT FRAMEWORK ===

AVAILABLE ACTIONS:
1. "mcp_call" - Access external legal databases (requires human approval for security)
   - legal_mcp.search_documents: Search legal regulations, statutes, case law
   - requirements_mcp.search_requirements: Search technical requirements, standards
2. "analysis" - Perform deep reasoning/analysis on available information
3. "response" - Provide final answer to user (when sufficient information gathered)
4. "hitl_prompt" - Request human input (rare - only for clarifications)

=== AGENT ORCHESTRATION PRINCIPLES ===

FULL AUTONOMY: You control ALL workflow decisions:
- When to gather more information vs. respond immediately
- How many analysis steps to perform 
- Which external tools to use and in what order
- How to structure and pace your reasoning process
- Quality standards for your final response

INTELLIGENT DECISION-MAKING:
- Simple questions (definitions, basic concepts): Respond immediately if you have knowledge
- Complex compliance analysis: May need 1-3 analysis steps + external data
- Multi-jurisdictional queries: Often require MCP calls for specific regulations
- Precedent/case law questions: Usually need legal database access

EFFICIENCY OPTIMIZATION:
- Avoid repetitive analysis - build on previous work
- Batch related MCP calls when possible
- Balance thoroughness with response time
- Aim for complete, actionable answers

ERROR HANDLING & QUALITY:
- If MCP calls fail, acknowledge and work with available information
- If analysis reveals gaps, either gather more data or acknowledge limitations
- Provide confidence levels for complex legal interpretations
- Always cite sources when making specific legal claims

=== DECISION LOGIC FRAMEWORK ===

RESPONSE IMMEDIATELY IF:
- Question is straightforward and within your knowledge base
- You have sufficient context from conversation history
- No external data needed for accurate answer

PERFORM ANALYSIS IF:
- Need to reason through complex legal implications
- Must synthesize multiple concepts or jurisdictions
- Working through multi-step compliance assessment
- Building on previous analysis with new insights

CALL MCP TOOLS IF:
- Need specific statute text, regulation details, or case law
- User asks about specific jurisdictions (Utah, GDPR, CCPA, etc.)
- Require current legal precedents or recent regulatory changes
- Need to verify compliance requirements for specific industries

=== RESPONSE QUALITY STANDARDS ===

EXCELLENT RESPONSES INCLUDE:
- Direct answer to user's specific question
- Relevant legal context and implications
- Specific citations when making legal claims
- Practical next steps or recommendations
- Clear confidence levels for interpretations

AVOID:
- Vague or overly general responses
- Repeating previous analysis without new insights  
- Unnecessary delays when you have sufficient information
- Making specific legal claims without proper sourcing

=== DECISION FORMAT ===
Respond with exactly this format:

ACTION_TYPE: [mcp_call|analysis|response|hitl_prompt]
REASONING: [Your strategic reasoning for this choice - 1-2 sentences]
RESPONSE_CONTENT: [If action_type is "response", provide complete answer here]
DETAILS: [For other action types: specific MCP query, analysis focus, etc.]

What is your autonomous decision for the next action?"""

    try:
        # Allocate tokens based on action type - agent controls response length
        max_tokens = 2000  # Generous allocation for autonomous decision-making
        
        response = await llm_client.complete(
            system_prompt,
            max_tokens=max_tokens,
            temperature=0.1
        )
        
        content = response.get("content", "").strip()
        logger.info(f"🧠 Agent decision: {content[:200]}...")
        
        # Parse agent decision with robust parsing - handle multi-line content
        action_type = None
        reasoning = ""
        details = {}
        response_content = ""
        
        # Improved parsing method to handle multi-line RESPONSE_CONTENT
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("ACTION_TYPE:"):
                action_type = line.replace("ACTION_TYPE:", "").strip()
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("RESPONSE_CONTENT:"):
                # Handle multi-line response content
                response_lines = []
                first_line_content = line.replace("RESPONSE_CONTENT:", "").strip()
                if first_line_content:
                    response_lines.append(first_line_content)
                
                # Continue reading lines until we hit another field or end of content
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if (next_line.startswith("DETAILS:") or 
                        next_line.startswith("ACTION_TYPE:") or 
                        next_line.startswith("REASONING:")):
                        i -= 1  # Step back so outer loop processes this line
                        break
                    if next_line:  # Only add non-empty lines
                        response_lines.append(next_line)
                    i += 1
                
                response_content = "\n".join(response_lines).strip()
                logger.info(f"🔍 Parsed multi-line response_content: {response_content[:300]}...")
            elif line.startswith("DETAILS:"):
                details_str = line.replace("DETAILS:", "").strip()
                details = {"description": details_str}
            i += 1
        
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
                "response_content": response_content,  # Store the actual response content for response actions
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
REASONING: [brief 10-word reason for tool choice]

Make your decision based purely on context and reasoning - no keyword matching allowed.
KEEP REASONING BRIEF: Maximum 10 words explaining your choice."""

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
        # Extract the actual LLM response content - prioritize response_content field for response actions
        response_content = (
            action.details.get("response_content", "") or 
            action.details.get("raw_response", "") or 
            action.details.get("description", "") or
            "Analysis complete - no response content available"
        ).strip()
        
        logger.info(f"🔍 Final response content length: {len(response_content)}")
        logger.info(f"🔍 Final response content preview: {response_content[:300]}...")
        logger.info(f"🔍 Action details keys: {list(action.details.keys())}")
        
        # Mark workflow as complete with the actual LLM response
        active_workflows[session_id] = {
            "id": session_id,
            "status": "complete", 
            "final_response": response_content,  # The actual LLM-generated response
            "completed_at": datetime.now().isoformat(),
            "tool_results_count": len(agent_state.tool_results)
        }
        
        agent_state.status = "completed"
        
        logger.info(f"✅ Agent sent final response for session {session_id}")
        logger.info(f"🔍 Active workflows now contains: {session_id in active_workflows}")
        if session_id in active_workflows:
            logger.info(f"🔍 Workflow status: {active_workflows[session_id].get('status')}")
            logger.info(f"🔍 Final response length: {len(active_workflows[session_id].get('final_response', ''))}")
        
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
            
        # Create HITL prompt for MCP approval with correct field names
        await send_hitl_prompt(session_id, {
            "type": "mcp_approval",
            "question": f"I want to search {tool_decision['tool']} for: '{tool_decision['query']}'. Should I proceed?",
            "options": ["Approve", "Skip"],
            "context": {
                "mcp_tool": tool_decision['tool'],
                "mcp_query": tool_decision['query'],  # Use mcp_query field name
                "mcp_reason": tool_decision['reasoning'],  # Use mcp_reason field name
                "query": tool_decision['query'],  # Keep legacy field for fallback
                "reasoning": tool_decision['reasoning'],  # Keep legacy field for fallback
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
            
            # Resume agent loop - RESTART THE AUTONOMOUS LOOP
            agent_state.status = "active"
            # Get the original user message to resume with
            original_message = ""
            for msg in agent_state.conversation_history:
                if msg['role'] == 'user' and not msg.get('hitl_response', False):
                    original_message = msg['content']
                    break
            
            # Restart the autonomous agent loop in background - with locking
            import asyncio
            asyncio.create_task(_resume_autonomous_agent_locked(session_id, original_message))
            
        else:
            # User declined - clear pending decision and continue
            agent_state.pending_mcp_decision = None
            agent_state.status = "active"
            
            # Still resume the loop to let agent decide what to do next
            original_message = ""
            for msg in agent_state.conversation_history:
                if msg['role'] == 'user' and not msg.get('hitl_response', False):
                    original_message = msg['content']
                    break
            
            import asyncio
            asyncio.create_task(_resume_autonomous_agent_locked(session_id, original_message))
            
        logger.info(f"✅ Agent ready to continue after HITL")
        
    except Exception as e:
        logger.error(f"❌ Agent HITL continuation failed: {e}")

async def _resume_autonomous_agent_locked(session_id: str, original_message: str):
    """
    Resume the autonomous agent loop after HITL approval - with proper locking
    """
    
    # Acquire lock to prevent concurrent agent loops
    if session_id not in agent_locks:
        logger.error(f"❌ No lock found for session {session_id}")
        return
        
    async with agent_locks[session_id]:
        try:
            logger.info(f"🔄 Resuming autonomous agent loop for session {session_id}")
            
            agent_state = agent_sessions[session_id]
            
            if agent_state.status != "active":
                logger.info(f"❌ Agent not in active state, cannot resume: {agent_state.status}")
                return
            
            # Main agent orchestration loop (resumed)
            max_iterations = 8  # Fewer iterations since we've already started
            iteration = 0
            
            while iteration < max_iterations and agent_state.status == "active":
                iteration += 1
                logger.info(f"🔄 Agent resume iteration {iteration}/{max_iterations}")
                
                # Get next action from LLM agent
                next_action = await _agent_decide_next_action(session_id, original_message, None)
                
                if not next_action:
                    logger.warning(f"❌ Agent couldn't decide next action - ending resumed loop")
                    break
                    
                logger.info(f"🎯 Agent resumed decision: {next_action.action_type}")
                
                # Execute the action
                if next_action.action_type == "mcp_call":
                    # MCP calls require HITL approval - send HITL prompt first
                    await _agent_send_mcp_approval_prompt(session_id, next_action)
                    agent_state.status = "waiting_hitl"
                    break  # Wait for user approval
                elif next_action.action_type == "analysis":
                    await _agent_perform_analysis(session_id, next_action)
                    # Yield control aggressively to allow frontend polling between reasoning steps  
                    # Agent controls its own pacing - no artificial delays
                elif next_action.action_type == "response":
                    await _agent_send_final_response(session_id, next_action)
                    break  # End the loop after final response
                elif next_action.action_type == "hitl_prompt":
                    await _agent_send_hitl_prompt(session_id, next_action)
                    agent_state.status = "waiting_hitl"
                    break  # Wait for user input
                
                # Brief yield for frontend responsiveness (agent still controls overall pacing)
                await asyncio.sleep(0.05)  # 50ms yield for UI updates
            
            if iteration >= max_iterations:
                logger.warning(f"⚠️ Resumed agent hit max iterations limit")
                agent_state.status = "completed"
                # Send timeout message
                active_workflows[session_id] = {
                    "id": session_id,
                    "status": "complete",
                    "final_response": "⏰ **Agent Analysis Complete**\n\nI've reached my processing limit for this session. The analysis I've performed so far is available above.",
                    "completed_at": datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"❌ Autonomous agent resume failed for {session_id}: {e}")
            agent_state = agent_sessions.get(session_id)
            if agent_state:
                agent_state.status = "error"
            active_workflows[session_id] = {
                "id": session_id,
                "status": "error", 
                "error": f"Agent resume encountered an error: {str(e)}",
                "completed_at": datetime.now().isoformat()
            }

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
            "timestamp": datetime.now().isoformat(),
            "execution_time": (datetime.now() - mcp_start).total_seconds()
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
        
        # Store MCP execution for chat display - with atomic operations
        if not hasattr(agent_state, 'mcp_executions_for_chat'):
            agent_state.mcp_executions_for_chat = []
        
        # Create result summary
        results_count = len(result.get('results', []))
        if results_count > 0:
            result_summary = f"Found {results_count} relevant documents"
            if results_count >= 3:
                result_summary += f" including {result['results'][0].get('title', 'document')} and others"
        else:
            result_summary = "No matching documents found"
        
        # Atomic append operation
        mcp_execution = {
            "tool": tool_decision["tool"],
            "query": tool_decision["query"],
            "results_count": results_count,
            "execution_time": mcp_duration,
            "timestamp": datetime.now().isoformat(),
            "result_summary": result_summary,
            "raw_results": result  # Include the full JSON response
        }
        agent_state.mcp_executions_for_chat.append(mcp_execution)
        
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
    
    # Mark the HITL prompt as completed
    if prompt_id and prompt_id in pending_hitl_prompts:
        pending_hitl_prompts[prompt_id]["completed"] = True
    
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
            if prompt.get("workflow_id") == workflow_id and not prompt.get("completed", False):
                # Mark as sent (but not completed until user responds)
                pending_hitl_prompts[prompt_id]["sent"] = True
                
                # Extract MCP-specific fields from context for MCP approval prompts
                context = prompt.get("context", {})
                mcp_tool = context.get("mcp_tool")
                mcp_query = context.get("mcp_query") or context.get("query")  # Prioritize mcp_query
                mcp_reason = context.get("mcp_reason") or context.get("reasoning")  # Prioritize mcp_reason
                
                return ChatResponse(
                    response=f"🤖 **Agent Approval Required**\n\n{prompt.get('question', 'Should I proceed?')}",
                    timestamp=datetime.now().isoformat(),
                    workflow_started=True,
                    workflow_id=workflow_id,
                    hitl_prompt=HITLPrompt(
                        prompt_id=prompt_id,
                        question=prompt.get("question", "Should I proceed with this action?"),
                        options=prompt.get("options", ["Approve", "Skip"]),
                        context=context,
                        mcp_tool=mcp_tool,
                        mcp_query=mcp_query,
                        mcp_reason=mcp_reason
                    )
                )
        
        # Check if agent completed
        if workflow_id in active_workflows and active_workflows[workflow_id].get("status") == "complete":
            final_response = active_workflows[workflow_id].get("final_response", "Agent analysis complete")
            
            # Calculate total reasoning duration
            total_duration = 0
            if agent_state.start_time:
                total_duration = (datetime.now() - agent_state.start_time).total_seconds()
            
            # ALSO check for any remaining MCP executions when workflow is complete - atomic tracking
            mcp_executions_to_send = []
            if hasattr(agent_state, 'mcp_executions_for_chat'):
                # Use atomic field from AgentState model instead of hasattr
                current_sent_count = agent_state.mcp_sent_count
                total_executions = len(agent_state.mcp_executions_for_chat)
                
                # Send any remaining MCP executions
                new_executions = agent_state.mcp_executions_for_chat[current_sent_count:]
                if new_executions:
                    logger.info(f"🔍 Sending {len(new_executions)} remaining MCP executions with final response")
                    mcp_executions_to_send = [
                        MCPExecution(
                            tool=exec["tool"],
                            query=exec["query"],
                            results_count=exec["results_count"],
                            execution_time=exec["execution_time"],
                            result_summary=exec["result_summary"],
                            timestamp=exec["timestamp"],
                            raw_results=exec["raw_results"]
                        ) for exec in new_executions
                    ]
                    agent_state.mcp_sent_count = total_executions  # Atomic update
            
            return ChatResponse(
                response=final_response,
                timestamp=datetime.now().isoformat(),
                workflow_started=False,
                workflow_id=workflow_id,
                reasoning=agent_state.reasoning_steps,
                reasoning_duration=total_duration,
                is_reasoning_complete=True,
                mcp_executions=mcp_executions_to_send if mcp_executions_to_send else None
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
        
        # Check for new MCP executions to show as chat messages - atomic tracking
        mcp_executions_to_send = []
        if hasattr(agent_state, 'mcp_executions_for_chat'):
            # Use atomic field from AgentState model
            current_sent_count = agent_state.mcp_sent_count
            total_executions = len(agent_state.mcp_executions_for_chat)
            
            # Send any new MCP executions
            new_executions = agent_state.mcp_executions_for_chat[current_sent_count:]
            if new_executions:
                mcp_executions_to_send = [
                    MCPExecution(
                        tool=exec["tool"],
                        query=exec["query"],
                        results_count=exec["results_count"],
                        execution_time=exec["execution_time"],
                        result_summary=exec["result_summary"],
                        timestamp=exec["timestamp"],
                        raw_results=exec["raw_results"]
                    ) for exec in new_executions
                ]
                agent_state.mcp_sent_count = total_executions  # Atomic update
        
        # Agent still processing
        status_msg = "active" if agent_state.status == "active" else agent_state.status
        
        # Calculate current reasoning duration
        current_duration = 0
        if agent_state.start_time:
            current_duration = (datetime.now() - agent_state.start_time).total_seconds()
        
        # Debug logging for MCP executions - with atomic tracking
        if mcp_executions_to_send:
            logger.info(f"🔍 Sending {len(mcp_executions_to_send)} MCP executions to frontend")
        elif hasattr(agent_state, 'mcp_executions_for_chat') and agent_state.mcp_executions_for_chat:
            logger.info(f"🔍 Agent has {len(agent_state.mcp_executions_for_chat)} total MCP executions, sent_count: {agent_state.mcp_sent_count}")
        
        return ChatResponse(
            response="⏳ Thinking...",
            timestamp=datetime.now().isoformat(),
            workflow_started=True,
            workflow_id=workflow_id,
            reasoning=agent_state.reasoning_steps,
            reasoning_duration=current_duration,
            is_reasoning_complete=False,
            mcp_executions=mcp_executions_to_send if mcp_executions_to_send else None
        )
    
    # Legacy workflow support
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Session not found")
    
    workflow = active_workflows[workflow_id]
    
    # Check for pending HITL prompts (legacy)
    for prompt_id, prompt in pending_hitl_prompts.items():
        if prompt.get("workflow_id") == workflow_id and not prompt.get("completed", False):
            pending_hitl_prompts[prompt_id]["sent"] = True
            
            # Extract MCP-specific fields from context for legacy prompts too
            context = prompt.get("context", {})
            mcp_tool = context.get("mcp_tool")
            mcp_query = context.get("mcp_query") or context.get("query")  # Prioritize mcp_query
            mcp_reason = context.get("mcp_reason") or context.get("reasoning")  # Prioritize mcp_reason
            
            return ChatResponse(
                response="🤔 **Legacy Workflow Approval Required**",
                timestamp=datetime.now().isoformat(),
                workflow_started=True,
                workflow_id=workflow_id,
                hitl_prompt=HITLPrompt(
                    prompt_id=prompt_id,
                    question=prompt.get("question", "Approve action?"),
                    options=prompt.get("options", ["YES", "NO"]),
                    context=context,
                    mcp_tool=mcp_tool,
                    mcp_query=mcp_query,
                    mcp_reason=mcp_reason
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