'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { useHITL } from '@/hooks/use-hitl'
import { useWorkflowStore } from '@/lib/stores'
import { useSSE } from '@/hooks/use-sse'
import { useStreamingChat } from '@/hooks/use-streaming-chat'
import { startWorkflow } from '@/lib/api'
import { cn } from '@/lib/utils'
import { Send, Bot, User, ChevronDown, ChevronRight, Brain, Settings, BarChart3, HelpCircle, Rocket, X, Check, XIcon, Code } from 'lucide-react'

interface HITLPrompt {
  prompt_id: string
  question: string
  options: string[]
  context: Record<string, any>
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
}

// Cursor-style reasoning dropdown component with streaming support
function ReasoningDropdown({ message }: { message: ChatMessage }) {
  // Auto-open when reasoning, auto-close when complete (unless user interacted)
  const [isExpanded, setIsExpanded] = useState(message.is_reasoning_complete === false)
  const [userInteracted, setUserInteracted] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const [visibleSteps, setVisibleSteps] = useState<number>(0)
  const [streamingSteps, setStreamingSteps] = useState<{[key: number]: string}>({}) // Track streaming content for each step
  const [currentStreamingStep, setCurrentStreamingStep] = useState<number>(-1)
  
  // Auto-open when reasoning starts, auto-close when complete
  useEffect(() => {
    if (!userInteracted) {
      setIsExpanded(message.is_reasoning_complete === false)
    }
  }, [message.is_reasoning_complete, userInteracted])

  // Initialize streaming when reasoning first appears or new steps are added
  useEffect(() => {
    if (message.reasoning && message.reasoning.length > 0) {
      const currentLength = message.reasoning.length
      
      // Start streaming if we have steps to show and no current streaming
      if (currentLength > visibleSteps && currentStreamingStep === -1) {
        startStreamingStep(visibleSteps)
      }
    }
  }, [message.reasoning])

  // Function to start streaming a specific step
  const startStreamingStep = (stepIndex: number) => {
    if (!message.reasoning || stepIndex >= message.reasoning.length) return
    
    const step = message.reasoning[stepIndex]
    setCurrentStreamingStep(stepIndex)
    
    // Format the content: title + content combined
    const stepTitle = step.type.replace('_', ' ').charAt(0).toUpperCase() + step.type.replace('_', ' ').slice(1)
    const duration = step.duration ? ` (${step.duration.toFixed(1)}s)` : ''
    const fullContent = `${stepTitle}${duration}\n${step.content}`
    const tokens = fullContent.split(' ') // Split by tokens (words)
    
    let tokenIndex = 0
    setStreamingSteps(prev => ({ ...prev, [stepIndex]: '' }))
    
    const streamInterval = setInterval(() => {
      if (tokenIndex < tokens.length) {
        const currentTokens = tokens.slice(0, tokenIndex + 1).join(' ')
        setStreamingSteps(prev => ({ ...prev, [stepIndex]: currentTokens }))
        tokenIndex++
      } else {
        // Step completed
        clearInterval(streamInterval)
        setVisibleSteps(prev => prev + 1)
        setCurrentStreamingStep(-1)
        
        // Start next step after a brief delay
        const nextStepIndex = stepIndex + 1
        if (nextStepIndex < (message.reasoning?.length || 0)) {
          setTimeout(() => {
            startStreamingStep(nextStepIndex)
          }, 300) // 300ms delay between steps
        }
      }
    }, 100) // 100ms per token
  }
  
  // Update expansion state when reasoning completes
  useEffect(() => {
    if (message.is_reasoning_complete === true && isExpanded && !userInteracted && !isHovered) {
      // Only auto-collapse if user hasn't interacted and isn't hovering
      const timer = setTimeout(() => {
        setIsExpanded(false)
      }, 3000) // Increased to 3 seconds
      return () => clearTimeout(timer)
    }
  }, [message.is_reasoning_complete, isExpanded, userInteracted, isHovered])
  
  // Handle manual toggle - mark as user interaction
  const handleToggle = () => {
    setIsExpanded(!isExpanded)
    setUserInteracted(true) // Prevent auto-close after manual interaction
  }
  
  if (!message.reasoning || message.reasoning.length === 0) {
    return null
  }
  
  const totalDuration = message.reasoning_duration || 0
  
  return (
    <div 
      className="mt-1 text-xs"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <button
        onClick={handleToggle}
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
        <div 
          className="mt-1 ml-4 space-y-1 text-gray-600 bg-gray-50 rounded px-2 py-1 border-l-2 border-gray-300 max-h-64 overflow-y-auto"
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          onScroll={() => setUserInteracted(true)}
        >
          {/* Completed steps */}
          {message.reasoning.slice(0, visibleSteps).map((step, index) => (
            <div 
              key={index} 
              className="text-xs"
            >
              <div className="flex items-center gap-1 font-medium text-gray-700">
                {step.type === 'llm_decision' && <Brain className="w-3 h-3" />}
                {step.type === 'mcp_call' && <Settings className="w-3 h-3" />}
                {step.type === 'analysis' && <BarChart3 className="w-3 h-3" />}
                {step.type === 'hitl_prompt' && <HelpCircle className="w-3 h-3" />}
                {step.type === 'agent_startup' && <Rocket className="w-3 h-3" />}
                <span className="capitalize">{step.type.replace('_', ' ')}</span>
                {step.duration && <span className="text-gray-500">({step.duration.toFixed(1)}s)</span>}
              </div>
              <div className="ml-4 text-gray-600 mt-0.5">{step.content}</div>
            </div>
          ))}
          
          {/* Currently streaming step */}
          {currentStreamingStep >= 0 && message.reasoning && message.reasoning[currentStreamingStep] && (
            <div className="text-xs animate-fade-in">
              <div className="whitespace-pre-wrap text-gray-600">
                {streamingSteps[currentStreamingStep] || ''}
                <span className="inline-block w-0.5 h-4 bg-blue-500 animate-blink ml-0.5" />
              </div>
            </div>
          )}
          
          {/* Show a loading indicator for the next step if reasoning isn't complete */}
          {!message.is_reasoning_complete && visibleSteps < (message.reasoning?.length || 0) && (
            <div className="text-xs text-gray-400 animate-pulse">
              <div className="flex items-center gap-1 font-medium">
                <div className="w-3 h-3 bg-gray-300 rounded animate-pulse" />
                <span>Processing...</span>
              </div>
            </div>
          )}
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

export function HITLSidebar() {
  const { sidebarOpen, progress, setSidebarOpen, currentWorkflow, setProgress, setHitlPrompt, setCurrentWorkflow } = useWorkflowStore()
  const { hitlPrompt, isResponding, respond } = useHITL()
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [isQuerying, setIsQuerying] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const messageIdsRef = useRef<Set<string>>(new Set()) // Track message IDs to prevent duplicates
  const [useRealStreaming, setUseRealStreaming] = useState(true) // Toggle between real streaming and old system
  const streamingChat = useStreamingChat() // Real streaming hook
  
  // Debug logging for message changes
  useEffect(() => {
    const mcpCount = chatMessages.filter(m => m.type === 'mcp_call').length
    console.log('🔍 Chat messages changed:', chatMessages.length, 'total,', mcpCount, 'MCP messages')
  }, [chatMessages])
  const [chatInput, setChatInput] = useState('')
  const [sidebarWidth, setSidebarWidth] = useState(320) // 320px = w-80
  const [isResizing, setIsResizing] = useState(false)

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

  useEffect(() => {
    scrollToBottom()
  }, [chatMessages])

  // Resize functionality
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsResizing(true)
    e.preventDefault()
  }

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


  const handleChatSend = async () => {
    if (!chatInput.trim()) return
    
    const originalInput = chatInput
    setChatInput('')
    
    if (useRealStreaming) {
      // Use real streaming
      await streamingChat.sendMessage(originalInput)
      return
    }
    
    // Old system (for fallback)
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: originalInput,
      timestamp: new Date(),
    }
    
    // Add user message with deduplication
    if (!messageIdsRef.current.has(userMessage.id)) {
      messageIdsRef.current.add(userMessage.id)
      setChatMessages(prev => [...prev, userMessage])
    }
    setIsQuerying(true)
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/legal-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: originalInput })
      })
      
      if (!response.ok) {
        throw new Error('Failed to get response from lawyer agent')
      }
      
      const result = await response.json()
      
      // Only add message if it's not a generic "Analyzing" status message
      // Skip generic status messages - just show reasoning dropdown directly
      if (!result.response?.includes('Analyzing your request') && result.response?.trim() !== '⏳ Analyzing your request...') {
        const initialMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: result.response || 'No response received from lawyer agent',
          timestamp: new Date(),
          workflow_id: result.workflow_id,
          reasoning: result.reasoning?.map((step: any) => ({
            type: step.type,
            content: step.content,
            duration: step.duration,
            timestamp: new Date(step.timestamp)
          })),
          reasoning_duration: result.reasoning_duration,
          is_reasoning_complete: result.is_reasoning_complete
        }
        
        // Add assistant message with deduplication
        if (!messageIdsRef.current.has(initialMessage.id)) {
          messageIdsRef.current.add(initialMessage.id)
          setChatMessages(prev => [...prev, initialMessage])
        }
      } else {
        // For "Analyzing" messages, just create a reasoning-only message
        if (result.reasoning && result.reasoning.length > 0) {
          const reasoningMessage: ChatMessage = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: '', // Empty content - will only show reasoning dropdown
            timestamp: new Date(),
            workflow_id: result.workflow_id,
            reasoning: result.reasoning?.map((step: any) => ({
              type: step.type,
              content: step.content,
              duration: step.duration,
              timestamp: new Date(step.timestamp)
            })),
            reasoning_duration: result.reasoning_duration,
            is_reasoning_complete: result.is_reasoning_complete
          }
          
          // Add reasoning message with deduplication
          if (!messageIdsRef.current.has(reasoningMessage.id)) {
            messageIdsRef.current.add(reasoningMessage.id)
            setChatMessages(prev => [...prev, reasoningMessage])
          }
        }
      }
      
      // If a workflow was started, start polling for HITL prompts and responses
      if (result.workflow_started && result.workflow_id) {
        await pollForWorkflowMessages(result.workflow_id)
      }
    } catch (error) {
      console.error('Legal chat error:', error)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 2).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      }
      // Add error message with deduplication
      if (!messageIdsRef.current.has(errorMessage.id)) {
        messageIdsRef.current.add(errorMessage.id)
        setChatMessages(prev => [...prev, errorMessage])
      }
    } finally {
      setIsQuerying(false)
    }
  }

  const pollForWorkflowMessages = async (workflowId: string) => {
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
        
        // Check if we got a HITL prompt
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
        // Check if workflow is complete
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
        // Check for new MCP executions to display as chat messages
        if (result.mcp_executions && result.mcp_executions.length > 0) {
          console.log('🔍 Adding MCP messages:', result.mcp_executions)
          console.log('🔍 First MCP execution details:', {
            tool: result.mcp_executions[0]?.tool,
            query: result.mcp_executions[0]?.query,
            has_raw_results: !!result.mcp_executions[0]?.raw_results,
            raw_results_preview: JSON.stringify(result.mcp_executions[0]?.raw_results || {}).substring(0, 200)
          })
          result.mcp_executions.forEach(mcpExec => {
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
            
            console.log('🔍 Adding MCP message:', mcpMessage.id, mcpMessage.content.substring(0, 50))
            
            // Add MCP message with deduplication
            if (!messageIdsRef.current.has(mcpMessage.id)) {
              messageIdsRef.current.add(mcpMessage.id)
              setChatMessages(prev => {
                console.log('🔍 Current messages before adding MCP:', prev.length)
                const newMessages = [...prev, mcpMessage]
                console.log('🔍 Messages after adding MCP:', newMessages.length, 'MCP ID:', mcpMessage.id)
                return newMessages
              })
            } else {
              console.log('🔍 Skipping duplicate MCP message:', mcpMessage.id)
            }
          })
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
      
      if (isApproved) {
        // Transform to green approved message
        setTimeout(() => {
          setChatMessages(prev => prev.map(msg => {
            if (msg.id === message.id && msg.hitl_prompt) {
              return {
                ...msg,
                type: 'assistant' as const, // Change from hitl_prompt to assistant for styling
                content: `Approved: ${msg.hitl_prompt.context?.mcp_tool || 'mcp_tool'}: ${msg.hitl_prompt.context?.query?.substring(0, 50) || 'query'}...`,
                hitl_prompt: undefined, // Remove the prompt to hide buttons
                mcp_approved: true // Add flag for green styling
              }
            }
            return msg
          }))
        }, 200)
      } else {
        // If skipped, remove the message
        setTimeout(() => {
          setChatMessages(prev => prev.filter(msg => msg.id !== message.id))
        }, 500)
      }
      
      // Start polling immediately - no delay
      pollForWorkflowMessages(message.workflow_id!)
      
      // Also poll again shortly after to catch any rapid updates
      setTimeout(async () => {
        await pollForWorkflowMessages(message.workflow_id!)
      }, 100)
      
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

  const handleChatKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleChatSend()
    }
  }

  // Always render sidebar, but show/hide with transform
  const isVisible = sidebarOpen || true // Always show for now

  return (
    <div 
      className="fixed right-0 top-0 h-full bg-white border-l border-gray-200 shadow-lg z-50 flex flex-col"
      style={{ width: `${sidebarWidth}px` }}
    >
      {/* Resize Handle */}
      <div
        className="absolute left-0 top-0 w-1 h-full cursor-col-resize hover:bg-blue-200 active:bg-blue-300 transition-colors"
        onMouseDown={handleMouseDown}
        style={{ 
          backgroundColor: isResizing ? '#93c5fd' : 'transparent',
          zIndex: 10
        }}
      />
      
      {/* Resize Handle Visual Indicator */}
      <div
        className="absolute left-0 top-1/2 transform -translate-y-1/2 w-1 h-12 bg-gray-300 rounded-r opacity-0 hover:opacity-100 transition-opacity pointer-events-none"
        style={{ left: '-2px' }}
      />
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {hitlPrompt || progress ? 'Workflow Assistant' : 'Legal Chat'}
          </h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
        
        {progress && !hitlPrompt && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Step {progress.currentStep} of {progress.totalSteps}</span>
              <span>{progress.progress}%</span>
            </div>
            <Progress value={progress.progress} className="w-full" />
            <p className="text-sm text-gray-700">{progress.message}</p>
          </div>
        )}
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
              
              {/* Show streaming messages if using real streaming, otherwise show old messages */}
              {useRealStreaming ? (
                streamingChat.messages.map((message) => (
                  <div key={message.id} className="space-y-1">
                    <div
                      className={cn(
                        "flex gap-2",
                        message.type === 'user' ? 'justify-end' : 'justify-start'
                      )}
                    >
                      {message.type !== 'user' && (
                        <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 bg-blue-100">
                          <Bot className="w-4 h-4 text-blue-600" />
                        </div>
                      )}
                      
                      <div className={cn(
                        "rounded-lg px-3 py-2 max-w-[80%] text-sm",
                        message.type === 'user' 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-gray-100 text-gray-900'
                      )}>
                        <div className="whitespace-pre-wrap">
                          {message.content}
                          {message.isStreaming && (
                            <span className="animate-pulse ml-1 text-blue-500">▊</span>
                          )}
                        </div>
                        <div className="text-xs mt-1 opacity-70">
                          {message.timestamp.toLocaleTimeString()}
                          {message.isStreaming && (
                            <span className="ml-2 text-blue-500">Streaming...</span>
                          )}
                        </div>
                      </div>
                      
                      {message.type === 'user' && (
                        <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 bg-blue-500">
                          <User className="w-4 h-4 text-white" />
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                chatMessages.map((message) => (
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
                            <p className="whitespace-pre-wrap">{message.content}</p>
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
                      </div>
                    )}
                  
                  {/* HITL Prompt Inline Message */}
                  {message.type === 'hitl_prompt' && message.hitl_prompt && (
                    <div className="bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 text-sm max-w-[280px]">
                      <p className="text-orange-800 font-medium mb-2">{message.hitl_prompt.question}</p>
                      
                      {/* Context info if available */}
                      {message.hitl_prompt.context && Object.keys(message.hitl_prompt.context).length > 0 && (
                        <div className="bg-orange-100 rounded px-2 py-1 mb-2 text-xs text-orange-700">
                          {Object.entries(message.hitl_prompt.context).slice(0, 2).map(([key, value]) => (
                            <div key={key}>
                              <strong>{key}:</strong> {typeof value === 'string' ? value.slice(0, 50) + '...' : JSON.stringify(value).slice(0, 50) + '...'}
                            </div>
                          ))}
                        </div>
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
              <div className="space-y-2">
                {/* Streaming toggle */}
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">
                    {useRealStreaming ? '🌊 Real Token Streaming' : '⏳ Legacy Polling'}
                  </span>
                  <Button
                    onClick={() => setUseRealStreaming(!useRealStreaming)}
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-xs"
                  >
                    {useRealStreaming ? 'Legacy' : 'Streaming'}
                  </Button>
                </div>
                
                <div className="flex gap-2">
                  <Input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={handleChatKeyPress}
                    placeholder="Ask about compliance..."
                    className="flex-1 text-sm"
                    disabled={useRealStreaming ? streamingChat.isStreaming : isQuerying}
                  />
                  <Button
                    onClick={handleChatSend}
                    disabled={!chatInput.trim() || (useRealStreaming ? streamingChat.isStreaming : isQuerying)}
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