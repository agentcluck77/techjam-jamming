'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'

import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue, SelectLabel, SelectGroup } from '@/components/ui/select'
import { useHITL } from '@/hooks/use-hitl'
import { useWorkflowStore } from '@/lib/stores'
import { useSSE } from '@/hooks/use-sse'
// Removed streaming chat - using autonomous agent mode only
import { startWorkflow } from '@/lib/api'
import { cn } from '@/lib/utils'
import { Send, Bot, User, ChevronDown, ChevronRight, Settings, X, Check, XIcon, Code, AlertTriangle, RotateCcw, Brain, MessageSquarePlus, List } from 'lucide-react'
import { ChatList } from './ChatList'

interface HITLPrompt {
  prompt_id: string
  question: string
  options: string[]
  context: Record<string, any>
  mcp_tool?: string // For MCP approval prompts
  mcp_query?: string // Query being executed
  mcp_reason?: string // One-line reason why this MCP call is needed
}

interface ModelInfo {
  name: string
  description: string
  input_tokens: number
  output_tokens: number
}

interface ReasoningStep {
  type: 'llm_decision' | 'mcp_call' | 'analysis' | 'hitl_prompt' | 'agent_startup'
  content: string
  duration?: number
  timestamp: Date
}

interface ChatMessage {
  id: string
  type: 'user' | 'assistant' | 'hitl_prompt' | 'mcp_call'
  content: string
  timestamp: Date
  hitl_prompt?: HITLPrompt
  workflow_id?: string
  reasoning?: ReasoningStep[]
  reasoning_duration?: number
  is_reasoning_complete?: boolean
  mcp_details?: {
    tool: string
    query: string
    results_count?: number
    execution_time?: number
    raw_results?: any
  }
  mcp_approved?: boolean // Flag for approved MCP requests
  awaiting_mcp_result?: boolean // Track pending MCP result after approval
  mcp_result?: any // Store MCP result after approval
  mcp_error?: string // Store MCP error if any
  mcp_output_expanded?: { [key: string]: boolean } // Track MCP output toggle states
}

// Utility: strip emojis from any incoming content
function stripEmojis(input: string): string {
  if (!input) return ''
  try {
    return input.replace(/([\u{1F000}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F100}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}])/gu, '').trim()
  } catch {
    // Simple fallback that removes common emoji ranges
    return input.replace(/[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '').trim()
  }
}

// Simple reasoning dropdown component (static text, no streaming)
function ReasoningDropdown({ message }: { message: ChatMessage }) {
  // Simple toggle state - default closed
  const [isExpanded, setIsExpanded] = useState(false)
  if (!message.reasoning || message.reasoning.length === 0) {
    return null
  }
  
  const totalDuration = message.reasoning_duration || 0
  
  return (
    <div className="mt-1 text-xs">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="w-3 h-3" />
        ) : (
          <ChevronRight className="w-3 h-3" />
        )}
        <span>Thought for {totalDuration.toFixed(1)}s</span>
      </button>
      
      {isExpanded && (
        <div className="mt-1 ml-4 space-y-1 text-gray-600 bg-gray-50 rounded px-2 py-1 border-l-2 border-gray-300 max-h-64 overflow-y-auto">
          {/* All reasoning steps as static text */}
          {message.reasoning.map((step, index) => (
            <div key={index} className="text-xs whitespace-pre-wrap text-gray-600">
              {stripEmojis(step.content)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Expandable JSON component for MCP results
function ExpandableJSON({ data, label = "Raw Results" }: { data: any, label?: string }) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  if (!data) return null
  
  return (
    <div className="mt-2 border-t border-green-300 pt-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1 text-xs text-green-700 hover:text-green-800 transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="w-3 h-3" />
        ) : (
          <ChevronRight className="w-3 h-3" />
        )}
        <Code className="w-3 h-3" />
        <span>{isExpanded ? 'Hide' : 'Show'} {label}</span>
      </button>
      
      {isExpanded && (
        <div className="mt-2 max-h-64 overflow-y-auto bg-gray-900 rounded border text-xs">
          <pre className="p-2 text-green-400 whitespace-pre-wrap overflow-x-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

// MCP Output toggle component for approved messages
function MCPOutputToggle({ result, messageId }: { result: any, messageId: string }) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  if (!result) return null
  
  return (
    <div className="mt-2 border-t border-green-300 pt-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1 text-xs text-green-700 hover:text-green-800 transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="w-3 h-3" />
        ) : (
          <ChevronRight className="w-3 h-3" />
        )}
        <Code className="w-3 h-3" />
        <span>MCP Output</span>
      </button>
      
      {isExpanded && (
        <div className="mt-2 max-h-64 overflow-y-auto bg-gray-900 rounded border text-xs">
          <pre className="p-2 text-green-400 whitespace-pre-wrap overflow-x-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

interface HITLSidebarProps {
  onWidthChange?: (width: number, open: boolean) => void
}

export function HITLSidebar({ onWidthChange }: HITLSidebarProps = {}) {
  const { sidebarOpen, progress, setSidebarOpen, currentWorkflow, setProgress, setHitlPrompt, setCurrentWorkflow } = useWorkflowStore()
  const { hitlPrompt, isResponding, respond } = useHITL()
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [isQuerying, setIsQuerying] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const messageIdsRef = useRef<Set<string>>(new Set()) // Track message IDs to prevent duplicates
  // Always use autonomous agent mode (no streaming toggle)
  
  // Model selection state
  const [availableModels, setAvailableModels] = useState<{
    gemini_models: Record<string, ModelInfo>,
    claude_models: Record<string, ModelInfo>
  }>({ gemini_models: {}, claude_models: {} })
  const [currentModel, setCurrentModel] = useState<string>('claude-sonnet-4-20250514')
  const [isModelLoading, setIsModelLoading] = useState(false)
  
  // Load available models on component mount
  useEffect(() => {
    const loadModels = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/models/available`)
        if (response.ok) {
          const data = await response.json()
          setAvailableModels({
            gemini_models: data.gemini_models || {},
            claude_models: data.claude_models || {}
          })
          setCurrentModel(data.current_model || 'claude-sonnet-4-20250514')
        }
      } catch (error) {
        console.error('Failed to load models:', error)
      }
    }
    loadModels()
  }, [])

  // Debug logging for message changes
  useEffect(() => {
    const mcpCount = chatMessages.filter(m => m.type === 'mcp_call').length
    console.log('🔍 Chat messages changed:', chatMessages.length, 'total,', mcpCount, 'MCP messages')
  }, [chatMessages])
  const [chatInput, setChatInput] = useState('')
  const [sidebarWidth, setSidebarWidth] = useState(320) // 320px = w-80
  const [isResizing, setIsResizing] = useState(false)
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null)
  const activePollingRef = useRef<Set<string>>(new Set()) // Track active polling loops
  
  // Chat state
  const [selectedChat, setSelectedChat] = useState<any>(null)
  const [showChatList, setShowChatList] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  // SSE connection for workflow progress
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const sseUrl = currentWorkflow ? `${API_BASE_URL}/api/workflow/${currentWorkflow.id}/progress` : null
  
  useSSE(sseUrl || '', {
    enabled: !!currentWorkflow,
    onMessage: (data) => {
      console.log('SSE message received:', data)
      
      if (data.type === 'progress') {
        setProgress(data.payload)
      } else if (data.type === 'hitl_prompt') {
        setHitlPrompt(data.payload)
      } else if (data.type === 'workflow_complete') {
        setCurrentWorkflow(null)
        setProgress(null)
        setHitlPrompt(null)
      }
    },
    onError: (error) => {
      console.error('SSE connection error:', error)
    }
  })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Removed auto-scroll - let user control scrolling manually

  // Resize functionality
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsResizing(true)
    e.preventDefault()
  }

  // Notify parent of width changes
  useEffect(() => {
    onWidthChange?.(sidebarWidth, sidebarOpen)
  }, [sidebarWidth, sidebarOpen, onWidthChange])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return
      
      const newWidth = window.innerWidth - e.clientX
      if (newWidth >= 280 && newWidth <= 600) { // Min 280px, Max 600px
        setSidebarWidth(newWidth)
      }
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isResizing])

  const handleResponse = async (response: string) => {
    try {
      await respond(response)
      setSelectedOption(null)
    } catch (error) {
      console.error('Failed to respond:', error)
    }
  }

  const handleModelChange = async (modelId: string) => {
    if (modelId === currentModel || isModelLoading) return
    
    setIsModelLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/models/select`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_id: modelId }),
      })
      
      if (response.ok) {
        setCurrentModel(modelId)
        console.log(`Model switched to: ${modelId}`)
      } else {
        console.error('Failed to switch model:', await response.text())
      }
    } catch (error) {
      console.error('Error switching model:', error)
    } finally {
      setIsModelLoading(false)
    }
  }

  const handleSelectChat = async (chat: any) => {
    setSelectedChat(chat)
    setShowChatList(false)
    
    // Load chat messages and replace current messages
    const chatMessages: ChatMessage[] = chat.messages.map((msg: any) => ({
      id: msg.id,
      type: msg.type,
      content: msg.content,
      timestamp: new Date(msg.timestamp),
      reasoning: msg.reasoning_steps?.map((step: any) => ({
        type: step.type,
        content: step.content,
        duration: step.duration,
        timestamp: step.timestamp
      })),
      reasoning_duration: msg.reasoning_steps?.reduce((total: number, step: any) => total + (step.duration || 0), 0),
      is_reasoning_complete: true,
      mcp_executions: msg.mcp_executions?.map((exec: any) => ({
        tool: exec.tool,
        query: exec.query,
        results_count: exec.results_count || 0,
        execution_time: exec.execution_time || 0,
        result_summary: exec.result_summary || '',
        timestamp: exec.timestamp,
        raw_results: exec.raw_results
      }))
    }))
    
    setChatMessages(chatMessages)
  }

  const handleNewChat = () => {
    setSelectedChat(null)
    setChatMessages([])
    setShowChatList(false)
  }


  const handleChatSend = async () => {
    if (!chatInput.trim()) return
    
    const originalInput = chatInput
    setChatInput('')
    setIsQuerying(true)
    
    // Add user message immediately
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: originalInput,
      timestamp: new Date(),
    }
    setChatMessages(prev => [...prev, userMessage])
    
    // Use persistent chat session endpoint
    try {
      const response = await fetch(`${API_BASE_URL}/api/legal-chat/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: originalInput, 
          context: '',
          chat_id: selectedChat?.id  // Include chat ID for persistence
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const result = await response.json()
      
      if (result.workflow_id) {
        setCurrentWorkflowId(result.workflow_id)
        await pollForWorkflowMessages(result.workflow_id)
      }
    } catch (error) {
      console.error('Failed to start legal chat workflow:', error)
      // Add error message
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `Error: Failed to start analysis. ${error}`,
        timestamp: new Date(),
        is_reasoning_complete: true
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsQuerying(false)
    }
  }


  const pollForWorkflowMessages = async (workflowId: string) => {
    // Synchronous duplicate prevention - check and add atomically
    if (activePollingRef.current.has(workflowId)) {
      console.log(`🔄 Polling already active for workflow ${workflowId}, skipping duplicate`)
      return
    }
    
    // Immediately add to prevent race condition
    activePollingRef.current.add(workflowId)
    console.log(`🔄 Starting polling for workflow ${workflowId}`)
    
    let isPolling = true
    const maxPolls = 300 // Max 5 minutes of polling (1 second intervals)
    let pollCount = 0
    let finalResponseSent = false // Track if we already sent final response
    
    while (isPolling && pollCount < maxPolls) {
      try {
        await new Promise(resolve => setTimeout(resolve, 1000)) // Poll every 1000ms for stability
        
        const response = await fetch(`${API_BASE_URL}/api/legal-chat/poll/${workflowId}`)
        
        if (!response.ok) {
          console.error('Polling failed:', response.status)
          break
        }
        
        const result = await response.json()
        console.log('🔍 Poll result:', {
          workflow_started: result.workflow_started,
          is_reasoning_complete: result.is_reasoning_complete,
          reasoning_steps: result.reasoning?.length,
          has_mcp_executions: !!result.mcp_executions,
          mcp_executions_count: result.mcp_executions?.length || 0,
          response_preview: result.response?.substring(0, 100)
        })
        
        // Debug: Log the full result if it has MCP executions
        if (result.mcp_executions && result.mcp_executions.length > 0) {
          console.log('🔍 MCP EXECUTIONS FOUND:', result.mcp_executions)
        } else {
          console.log('🔍 No MCP executions in result')
        }
        
        // FIRST: Process any MCP executions to display results
        if (result.mcp_executions && result.mcp_executions.length > 0) {
          console.log('🔍 Adding MCP messages:', result.mcp_executions)
          result.mcp_executions.forEach((mcpExec: any) => {
            const mcpMessage: ChatMessage = {
              id: `mcp-${Date.now()}-${Math.random()}`,
              type: 'mcp_call',
              content: `🔍 **${mcpExec.tool.replace('_', ' ').toUpperCase()}**\n\n📝 **Query:** ${mcpExec.query}\n\n📊 **Results:** ${mcpExec.result_summary}\n\n⏱️ *${mcpExec.execution_time.toFixed(2)}s*`,
              timestamp: new Date(mcpExec.timestamp),
              workflow_id: workflowId,
              mcp_details: {
                tool: mcpExec.tool,
                query: mcpExec.query,
                results_count: mcpExec.results_count,
                execution_time: mcpExec.execution_time,
                raw_results: mcpExec.raw_results
              }
            }
            
            // Add MCP message with deduplication
            if (!messageIdsRef.current.has(mcpMessage.id)) {
              messageIdsRef.current.add(mcpMessage.id)
              setChatMessages(prev => [...prev, mcpMessage])
            }
          })
        }
        
        // SECOND: Check if we got a HITL prompt (after processing MCP results)
        if (result.hitl_prompt) {
          const hitlMessage: ChatMessage = {
            id: Date.now().toString(),
            type: 'hitl_prompt',
            content: result.response,
            timestamp: new Date(),
            hitl_prompt: result.hitl_prompt,
            workflow_id: workflowId
          }
          
          // Add HITL message with deduplication
          if (!messageIdsRef.current.has(hitlMessage.id)) {
            messageIdsRef.current.add(hitlMessage.id)
            setChatMessages(prev => [...prev, hitlMessage])
          }
          // Stop polling - we'll restart after user responds
          isPolling = false
        }
        // THIRD: Check if workflow is complete
        else if (!result.workflow_started || result.response.includes('Analysis Failed') || result.response.includes('complete')) {
          // Only add final message if it has meaningful content AND reasoning is complete AND not already sent
          if (result.response && 
              !result.response.includes('Thinking...') && 
              !result.response.includes('received. Continuing') &&
              result.is_reasoning_complete === true &&
              !finalResponseSent) {
            
            console.log('🎯 Adding final response after reasoning complete')
            finalResponseSent = true
            
            const finalMessage: ChatMessage = {
              id: Date.now().toString(),
              type: 'assistant',
              content: result.response,
              timestamp: new Date(),
              reasoning: result.reasoning?.map((step: any) => ({
                type: step.type,
                content: step.content,
                duration: step.duration,
                timestamp: new Date(step.timestamp)
              })),
              reasoning_duration: result.reasoning_duration,
              is_reasoning_complete: result.is_reasoning_complete
            }
            
            // Add final message with deduplication
            if (!messageIdsRef.current.has(finalMessage.id)) {
              messageIdsRef.current.add(finalMessage.id)
              setChatMessages(prev => [...prev, finalMessage])
            }
            isPolling = false
          } else if (result.is_reasoning_complete !== true) {
            console.log('🔄 Workflow complete but reasoning still streaming, continuing to poll...')
            // Continue polling until reasoning is complete
          } else {
            isPolling = false
          }
        }
        
        // Still in progress - update existing message with new reasoning
        if (result.reasoning && result.reasoning.length > 0) {
          setChatMessages(prev => {
            console.log('🔍 Updating reasoning. Current messages:', prev.length, 'MCP messages:', prev.filter(m => m.type === 'mcp_call').length)
            
            // Find the most recent assistant message for this workflow
            let targetMessageIndex = -1
            for (let i = prev.length - 1; i >= 0; i--) {
              if (prev[i].workflow_id === workflowId && prev[i].type === 'assistant') {
                targetMessageIndex = i
                break
              }
            }
            
            // Check if reasoning is already up to date (prevent duplicate updates)
            if (targetMessageIndex >= 0) {
              const currentReasoning = prev[targetMessageIndex].reasoning || []
              if (currentReasoning.length === result.reasoning.length && 
                  result.reasoning.every((step: any, index: number) => 
                    currentReasoning[index] && currentReasoning[index].content === step.content)) {
                console.log('🔍 Reasoning already up to date, skipping duplicate update')
                return prev
              }
            }
            
            if (targetMessageIndex >= 0) {
              const targetMessage = prev[targetMessageIndex]
              const updatedMessage = {
                ...targetMessage,
                reasoning: result.reasoning?.map((step: any) => ({
                  type: step.type,
                  content: step.content,
                  duration: step.duration,
                  timestamp: new Date(step.timestamp)
                })),
                reasoning_duration: result.reasoning_duration,
                is_reasoning_complete: result.is_reasoning_complete
              }
              const newMessages = [...prev]
              newMessages[targetMessageIndex] = updatedMessage
              
              console.log('🔍 After reasoning update. Messages:', newMessages.length, 'MCP messages:', newMessages.filter(m => m.type === 'mcp_call').length)
              return newMessages
            }
            
            // If no existing assistant message found, create one for reasoning updates
            const reasoningMessage: ChatMessage = {
              id: Date.now().toString(),
              type: 'assistant',
              content: '', // Empty content - only showing reasoning
              timestamp: new Date(),
              workflow_id: workflowId,
              reasoning: result.reasoning?.map((step: any) => ({
                type: step.type,
                content: step.content,
                duration: step.duration,
                timestamp: new Date(step.timestamp)
              })),
              reasoning_duration: result.reasoning_duration,
              is_reasoning_complete: result.is_reasoning_complete
            }
            
            const newMessages = [...prev, reasoningMessage]
            console.log('🔍 Created new reasoning message. Messages:', newMessages.length, 'MCP messages:', newMessages.filter(m => m.type === 'mcp_call').length)
            return newMessages
          })
        }
        
        pollCount++
      } catch (error) {
        console.error('Polling error:', error)
        break
      }
    }
    
    // Cleanup: Remove from active polling set when done
    activePollingRef.current.delete(workflowId)
    console.log(`🔄 Stopped polling for workflow ${workflowId}`)
  }

  const handleHITLResponse = async (message: ChatMessage, response: string) => {
    if (!message.hitl_prompt || !message.workflow_id) {
      console.error('Missing HITL prompt or workflow ID', { 
        hasPrompt: !!message.hitl_prompt, 
        hasWorkflowId: !!message.workflow_id 
      })
      return
    }
    
    console.log('🎯 HITL Response clicked:', {
      response,
      workflowId: message.workflow_id,
      promptId: message.hitl_prompt.prompt_id
    })
    
    try {
      // Temporarily disable the button by updating the message
      setChatMessages(prev => prev.map(msg => 
        msg.id === message.id 
          ? { ...msg, hitl_prompt: { ...msg.hitl_prompt!, processing: true } as any }
          : msg
      ))
      
      // Send the HITL response
      const result = await fetch(`${API_BASE_URL}/api/legal-chat/hitl-respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt_id: message.hitl_prompt.prompt_id,
          response: response,
          workflow_id: message.workflow_id
        })
      })
      
      const responseData = await result.json()
      console.log('✅ HITL Response sent successfully:', {
        status: result.status,
        data: responseData
      })
      
      if (!result.ok) {
        throw new Error(`HTTP ${result.status}: ${responseData.detail || 'Failed to send response'}`)
      }
      
      // Transform HITL prompt to approved state instead of removing
      const isApproved = response.toLowerCase().includes('approve')
      
      // Add audit line to reasoning of the most recent assistant message
      const addAuditLineToRecentThoughts = (action: string, tool: string, query: string) => {
        setChatMessages(prev => {
          // Find the most recent assistant message
          let targetMessageIndex = -1
          for (let i = prev.length - 1; i >= 0; i--) {
            if (prev[i].type === 'assistant' && prev[i].reasoning) {
              targetMessageIndex = i
              break
            }
          }
          
          if (targetMessageIndex >= 0) {
            const targetMessage = prev[targetMessageIndex]
            const auditStep: ReasoningStep = {
              type: 'hitl_prompt',
              content: `User ${action} ${tool}${query ? ` (query=${query.substring(0, 50)}...)` : ''}`,
              timestamp: new Date()
            }
            
            const updatedMessage = {
              ...targetMessage,
              reasoning: [...(targetMessage.reasoning || []), auditStep]
            }
            
            const newMessages = [...prev]
            newMessages[targetMessageIndex] = updatedMessage
            return newMessages
          }
          return prev
        })
      }
      
      if (isApproved) {
        const tool = message.hitl_prompt?.mcp_tool || message.hitl_prompt?.context?.mcp_tool || 'MCP'
        const query = message.hitl_prompt?.mcp_query || message.hitl_prompt?.context?.query || ''
        
        // Add audit line
        addAuditLineToRecentThoughts('approved', tool, query)
        
        // Transform to green approved message with MCP result summary
        setTimeout(() => {
          setChatMessages(prev => prev.map(msg => {
            if (msg.id === message.id && msg.hitl_prompt) {
              // Prepare approved content with summary
              let approvedContent = ''
              let mcpResult = null
              
              if (msg.hitl_prompt.mcp_tool) {
                approvedContent = `Approved: ${stripEmojis(msg.hitl_prompt.mcp_tool)} — Processing query...`
                // Store MCP details for later result population
                mcpResult = {
                  tool: msg.hitl_prompt.mcp_tool,
                  query: msg.hitl_prompt.mcp_query,
                  reason: msg.hitl_prompt.mcp_reason
                }
              } else {
                approvedContent = `Approved: ${stripEmojis(msg.hitl_prompt.context?.mcp_tool || 'action')} — ${stripEmojis(msg.hitl_prompt.context?.query?.substring(0, 50) || 'query')}...`
              }
              
              return {
                ...msg,
                type: 'assistant' as const, // Change from hitl_prompt to assistant for styling
                content: approvedContent,
                hitl_prompt: undefined, // Remove the prompt to hide buttons
                mcp_approved: true, // Add flag for green styling
                awaiting_mcp_result: true, // Flag to indicate waiting for result
                mcp_result: mcpResult // Store MCP details for result display
              }
            }
            return msg
          }))
        }, 200)
      } else {
        const tool = message.hitl_prompt?.mcp_tool || message.hitl_prompt?.context?.mcp_tool || 'MCP'
        const query = message.hitl_prompt?.mcp_query || message.hitl_prompt?.context?.query || ''
        
        // Add audit line for skip
        addAuditLineToRecentThoughts('skipped', tool, query)
        
        // If skipped, remove the message
        setTimeout(() => {
          setChatMessages(prev => prev.filter(msg => msg.id !== message.id))
        }, 500)
      }
      
      // Start polling (will be skipped if already active)
      await pollForWorkflowMessages(message.workflow_id!)
      
    } catch (error) {
      console.error('❌ Failed to send HITL response:', error)
      
      // Re-enable the buttons
      setChatMessages(prev => prev.map(msg => 
        msg.id === message.id 
          ? { ...msg, hitl_prompt: { ...msg.hitl_prompt!, processing: false } as any }
          : msg
      ))
      
      // Show error message  
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `❌ Failed to send response: ${error}`,
        timestamp: new Date(),
      }
      setChatMessages(prev => [...prev, errorMessage])
    }
  }


  // Always render sidebar, but show/hide with transform
  const isVisible = sidebarOpen || true // Always show for now

  return (
    <div 
      className="fixed right-0 top-0 h-full bg-white border-l border-gray-200 shadow-lg z-40 flex flex-col"
      style={{ 
        width: `${sidebarWidth}px`,
        transform: sidebarOpen ? 'translateX(0)' : 'translateX(100%)',
        transition: isResizing ? 'none' : 'transform 200ms ease-in-out'
      }}
    >
      {/* Resize Handle */}
      <div
        className="absolute left-0 top-0 w-2 h-full cursor-col-resize group z-10"
        onMouseDown={handleMouseDown}
        style={{ left: '-1px' }}
      >
        {/* Active resize area */}
        <div 
          className={`w-full h-full transition-colors ${
            isResizing 
              ? 'bg-blue-400' 
              : 'bg-transparent hover:bg-blue-200'
          }`}
        />
        
        {/* Visual indicator */}
        <div className={`
          absolute left-1 top-1/2 transform -translate-y-1/2 
          w-1 h-8 bg-gray-400 rounded-full
          transition-all duration-200 
          ${isResizing ? 'opacity-100 scale-110' : 'opacity-0 group-hover:opacity-60'}
        `} />
        
        {/* Resize grip dots */}
        <div className={`
          absolute left-0.5 top-1/2 transform -translate-y-1/2 
          flex flex-col gap-1 pointer-events-none
          transition-opacity duration-200
          ${isResizing ? 'opacity-100' : 'opacity-0 group-hover:opacity-40'}
        `}>
          <div className="w-1 h-1 bg-gray-500 rounded-full" />
          <div className="w-1 h-1 bg-gray-500 rounded-full" />
          <div className="w-1 h-1 bg-gray-500 rounded-full" />
        </div>
      </div>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-gray-900">
              {hitlPrompt || progress ? 'Workflow Assistant' : showChatList ? 'Chat History' : selectedChat ? selectedChat.title : 'Legal Chat'}
            </h2>
            {!showChatList && !hitlPrompt && !progress && (
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowChatList(true)}
                  className="h-7 w-7 p-0"
                  title="View chat history"
                >
                  <List className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleNewChat}
                  className="h-7 w-7 p-0"
                  title="New chat"
                >
                  <MessageSquarePlus className="w-4 h-4" />
                </Button>
              </div>
            )}
            {showChatList && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowChatList(false)}
                className="h-7 w-7 p-0"
                title="Back to chat"
              >
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setSidebarOpen(false)
              onWidthChange?.(sidebarWidth, false)
            }}
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
        

      </div>

      <div className="flex-1 overflow-hidden flex flex-col">
        {hitlPrompt ? (
          <div className="p-4 overflow-y-auto">
            <Card>
              <CardHeader>
                <h3 className="font-medium text-gray-900">Human Input Required</h3>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-gray-700">{hitlPrompt.question}</p>
                
                {hitlPrompt.context && Object.keys(hitlPrompt.context).length > 0 && (
                  <div className="bg-gray-50 p-3 rounded-md">
                    <h4 className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-2">
                      Context
                    </h4>
                    {Object.entries(hitlPrompt.context).map(([key, value]) => (
                      <div key={key} className="mb-2">
                        <span className="text-xs font-medium text-gray-600">{key}:</span>
                        <p className="text-sm text-gray-800 mt-1">
                          {typeof value === 'string' ? value : JSON.stringify(value)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                <div className="space-y-2">
                  {hitlPrompt.options.map((option) => (
                    <Button
                      key={option}
                      variant={selectedOption === option ? "default" : "outline"}
                      className="w-full justify-start"
                      onClick={() => setSelectedOption(option)}
                      disabled={isResponding}
                    >
                      {option}
                    </Button>
                  ))}
                </div>

                <Button
                  className="w-full"
                  onClick={() => selectedOption && handleResponse(selectedOption)}
                  disabled={!selectedOption || isResponding}
                >
                  {isResponding ? 'Submitting...' : 'Submit Response'}
                </Button>
              </CardContent>
            </Card>
          </div>
        ) : showChatList ? (
          /* Chat List View */
          <ChatList
            onSelectChat={handleSelectChat}
            onNewChat={handleNewChat}
            selectedChatId={selectedChat?.id}
            className="flex-1"
          />
        ) : (
          <>


            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {chatMessages.length === 0 && (
                <div className="flex items-start gap-2">
                  <div className="w-7 h-7 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Bot className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="bg-gray-100 rounded-lg rounded-bl-sm px-3 py-2 text-sm text-gray-700 max-w-[220px]">
                    Hi! I'm ready to help with compliance questions. What would you like to know?
                  </div>
                </div>
              )}
              
              {/* Show regular chat messages with MCP approval support */}
              {chatMessages.map((message) => (
                <div key={message.id} className="space-y-1">
                  <div
                    className={cn(
                      "flex gap-2",
                      message.type === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    {(message.type === 'assistant' || message.type === 'hitl_prompt' || message.type === 'mcp_call') && (
                      <div className={cn(
                        "w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5",
                        message.type === 'hitl_prompt' ? 'bg-orange-100' : 
                        message.type === 'mcp_call' ? 'bg-green-100' : 
                        message.mcp_approved ? 'bg-green-100' : 'bg-blue-100'
                      )}>
                        {message.type === 'mcp_call' ? (
                          <Settings className="w-4 h-4 text-green-600" />
                        ) : (
                          <Bot className={cn(
                            "w-4 h-4",
                            message.type === 'hitl_prompt' ? 'text-orange-600' : 
                            message.mcp_approved ? 'text-green-600' : 'text-blue-600'
                          )} />
                        )}
                      </div>
                    )}
                    
                    {/* Regular chat message */}
                    {message.type !== 'hitl_prompt' && (
                      <div>
                        {/* Only show message box if there's actual content */}
                        {message.content && message.content.trim() && (
                          <div
                            className={cn(
                              "rounded-lg px-3 py-2 text-sm max-w-[220px]",
                              message.type === 'user'
                                ? 'bg-blue-600 text-white rounded-br-sm'
                                : message.type === 'mcp_call'
                                ? 'bg-green-50 text-green-900 border border-green-200 rounded-bl-sm'
                                : message.mcp_approved
                                ? 'bg-green-50 text-green-900 border border-green-200 rounded-bl-sm'
                                : 'bg-gray-100 text-gray-900 rounded-bl-sm'
                            )}
                          >
                            <p className="whitespace-pre-wrap">{stripEmojis(message.content)}</p>
                          </div>
                        )}
                        
                        {/* Cursor-style reasoning dropdown - shown even without message content */}
                        {message.type === 'assistant' && (
                          <ReasoningDropdown message={message} />
                        )}
                        
                        {/* Expandable JSON for MCP messages */}
                        {message.type === 'mcp_call' && message.mcp_details?.raw_results && (
                          <ExpandableJSON 
                            data={message.mcp_details.raw_results} 
                            label="Raw Results"
                          />
                        )}
                        
                        {/* MCP Output toggle for approved messages */}
                        {message.mcp_approved && message.mcp_result && (
                          <MCPOutputToggle 
                            result={message.mcp_result} 
                            messageId={message.id}
                          />
                        )}
                      </div>
                    )}
                  
                  {/* HITL Prompt Inline Message */}
                  {message.type === 'hitl_prompt' && message.hitl_prompt && (
                    <div className="bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 text-sm max-w-[280px]">
                      {/* MCP-specific approval prompt layout */}
                      {message.hitl_prompt.mcp_tool ? (
                        <div>
                          <div className="text-orange-800 font-medium mb-2">
                            MCP Approval Required
                          </div>
                          <div className="space-y-1 text-xs text-orange-700 mb-3">
                            <div><strong>Tool:</strong> {stripEmojis(message.hitl_prompt.mcp_tool)}</div>
                            <div><strong>Query:</strong> {stripEmojis(message.hitl_prompt.mcp_query || 'N/A')}</div>
                            <div><strong>Reason:</strong> {stripEmojis(message.hitl_prompt.mcp_reason || 'Processing request')}</div>
                          </div>
                        </div>
                      ) : (
                        /* Regular HITL prompt */
                        <>
                          <p className="text-orange-800 font-medium mb-2">{stripEmojis(message.hitl_prompt.question)}</p>
                          
                          {/* Context info if available */}
                          {message.hitl_prompt.context && Object.keys(message.hitl_prompt.context).length > 0 && (
                            <div className="bg-orange-100 rounded px-2 py-1 mb-2 text-xs text-orange-700">
                              {Object.entries(message.hitl_prompt.context).slice(0, 2).map(([key, value]) => (
                                <div key={key}>
                                  <strong>{key}:</strong> {typeof value === 'string' ? stripEmojis(value.slice(0, 50)) + '...' : JSON.stringify(value).slice(0, 50) + '...'}
                                </div>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                      
                      {/* Interactive buttons */}
                      <div className="flex gap-2 mt-2">
                        {message.hitl_prompt.options.map((option) => {
                          const isApprove = option.toLowerCase().includes('approve')
                          const isSkip = option.toLowerCase().includes('skip')
                          const isProcessing = (message.hitl_prompt as any)?.processing
                          return (
                            <Button
                              key={option}
                              onClick={() => {
                                console.log('HITL Button clicked:', option)
                                handleHITLResponse(message, option)
                              }}
                              size="sm"
                              variant={isApprove ? "default" : "outline"}
                              disabled={isProcessing}
                              className={`
                                text-xs px-3 py-2 h-8 flex items-center gap-1 font-medium
                                ${isApprove 
                                  ? 'bg-green-600 hover:bg-green-700 text-white border-green-600 disabled:bg-green-300' 
                                  : 'bg-white hover:bg-red-50 text-red-600 border-red-300 disabled:bg-gray-100'
                                }
                                ${isProcessing ? 'opacity-75 cursor-not-allowed' : 'cursor-pointer'}
                              `.trim()}
                            >
                              {!isProcessing && isApprove && <Check className="w-3 h-3" />}
                              {!isProcessing && isSkip && <XIcon className="w-3 h-3" />}
                              {isProcessing ? 'Sending...' : option}
                            </Button>
                          )
                        })}
                      </div>
                    </div>
                  )}
                  
                    {message.type === 'user' && (
                      <div className="w-7 h-7 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <User className="w-4 h-4 text-gray-600" />
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {/* Typing indicator */}
              {isQuerying && (
                <div className="flex items-start gap-2">
                  <div className="w-7 h-7 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Bot className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="bg-gray-100 rounded-lg rounded-bl-sm px-3 py-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
            
            {/* Fixed Chat Input at Bottom */}
            <div className="border-t border-gray-200 p-4">
              <div className="space-y-3">
                {/* Model Selector */}
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-gray-500" />
                  <Select
                    value={currentModel}
                    onValueChange={handleModelChange}
                    disabled={isModelLoading || isQuerying}
                  >
                    <SelectTrigger className="h-8 text-xs flex-1">
                      <SelectValue>
                        <div className="flex items-center gap-1">
                          <span className="truncate">
                            {availableModels.gemini_models[currentModel]?.name || 
                             availableModels.claude_models[currentModel]?.name || 
                             currentModel}
                          </span>
                          {isModelLoading && (
                            <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                          )}
                        </div>
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {/* Gemini Models Group */}
                      <SelectGroup>
                        <SelectLabel className="text-xs font-semibold text-gray-700">
                          Google Gemini Models
                        </SelectLabel>
                        {Object.entries(availableModels.gemini_models).map(([modelId, modelInfo]) => (
                          <SelectItem key={modelId} value={modelId} className="text-xs">
                            <div className="flex flex-col items-start">
                              <span className="font-medium">{modelInfo.name}</span>
                              <span className="text-gray-500 text-xs truncate">
                                {modelInfo.description}
                              </span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectGroup>
                      
                      {/* Claude Models Group */}
                      <SelectGroup>
                        <SelectLabel className="text-xs font-semibold text-gray-700">
                          Anthropic Claude Models
                        </SelectLabel>
                        {Object.entries(availableModels.claude_models).map(([modelId, modelInfo]) => (
                          <SelectItem key={modelId} value={modelId} className="text-xs">
                            <div className="flex flex-col items-start">
                              <span className="font-medium">{modelInfo.name}</span>
                              <span className="text-gray-500 text-xs truncate">
                                {modelInfo.description}
                              </span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="flex gap-2">
                  <Input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleChatSend()
                      }
                    }}
                    placeholder="Ask about compliance..."
                    className="flex-1 text-sm"
                    disabled={isQuerying}
                  />
                  <Button
                    onClick={handleChatSend}
                    disabled={!chatInput.trim() || isQuerying}
                    size="sm"
                    className="px-3"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}