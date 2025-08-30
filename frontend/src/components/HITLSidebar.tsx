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
import { startWorkflow } from '@/lib/api'
import { cn } from '@/lib/utils'
import { Send, Bot, User, ChevronDown, ChevronRight, Brain, Settings, BarChart3, HelpCircle, Rocket, X, Check, XIcon } from 'lucide-react'

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
  type: 'user' | 'assistant' | 'hitl_prompt'
  content: string
  timestamp: Date
  hitl_prompt?: HITLPrompt
  workflow_id?: string
  reasoning?: ReasoningStep[]
  reasoning_duration?: number
  is_reasoning_complete?: boolean
}

// Cursor-style reasoning dropdown component
function ReasoningDropdown({ message }: { message: ChatMessage }) {
  // Open during thinking, closed when complete
  const [isExpanded, setIsExpanded] = useState(message.is_reasoning_complete === false)
  
  // Update expansion state when reasoning completes
  useEffect(() => {
    if (message.is_reasoning_complete === true && isExpanded) {
      // Auto-collapse after 2 seconds when reasoning is complete
      const timer = setTimeout(() => {
        setIsExpanded(false)
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [message.is_reasoning_complete, isExpanded])
  
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
        <span>Thought for {totalDuration}s</span>
      </button>
      
      {isExpanded && (
        <div className="mt-1 ml-4 space-y-1 text-gray-600 bg-gray-50 rounded px-2 py-1 border-l-2 border-gray-300">
          {message.reasoning.map((step, index) => (
            <div key={index} className="text-xs">
              <div className="flex items-center gap-1 font-medium text-gray-700">
                {step.type === 'llm_decision' && <Brain className="w-3 h-3" />}
                {step.type === 'mcp_call' && <Settings className="w-3 h-3" />}
                {step.type === 'analysis' && <BarChart3 className="w-3 h-3" />}
                {step.type === 'hitl_prompt' && <HelpCircle className="w-3 h-3" />}
                {step.type === 'agent_startup' && <Rocket className="w-3 h-3" />}
                <span className="capitalize">{step.type.replace('_', ' ')}</span>
                {step.duration && <span className="text-gray-500">({step.duration}s)</span>}
              </div>
              <div className="ml-4 text-gray-600 mt-0.5">{step.content}</div>
            </div>
          ))}
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
    
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: chatInput,
      timestamp: new Date(),
    }
    
    setChatMessages(prev => [...prev, userMessage])
    const originalInput = chatInput
    setChatInput('')
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
      
      // Add initial response message with reasoning
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
      
      setChatMessages(prev => [...prev, initialMessage])
      
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
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsQuerying(false)
    }
  }

  const pollForWorkflowMessages = async (workflowId: string) => {
    let isPolling = true
    const maxPolls = 60 // Max 5 minutes of polling (5 second intervals)
    let pollCount = 0
    
    while (isPolling && pollCount < maxPolls) {
      try {
        await new Promise(resolve => setTimeout(resolve, 5000)) // Poll every 5 seconds
        
        const response = await fetch(`${API_BASE_URL}/api/legal-chat/poll/${workflowId}`)
        
        if (!response.ok) {
          console.error('Polling failed:', response.status)
          break
        }
        
        const result = await response.json()
        
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
          
          setChatMessages(prev => [...prev, hitlMessage])
          // Stop polling - we'll restart after user responds
          isPolling = false
        }
        // Check if workflow is complete
        else if (!result.workflow_started || result.response.includes('Analysis Failed') || result.response.includes('complete')) {
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
          
          setChatMessages(prev => [...prev, finalMessage])
          isPolling = false
        }
        // Still in progress - update existing message with new reasoning
        else if (result.reasoning && result.reasoning.length > 0) {
          setChatMessages(prev => {
            const lastMessage = prev[prev.length - 1]
            if (lastMessage && lastMessage.workflow_id === workflowId && lastMessage.type === 'assistant') {
              // Update the last assistant message with new reasoning data
              const updatedMessage = {
                ...lastMessage,
                reasoning: result.reasoning?.map((step: any) => ({
                  type: step.type,
                  content: step.content,
                  duration: step.duration,
                  timestamp: new Date(step.timestamp)
                })),
                reasoning_duration: result.reasoning_duration,
                is_reasoning_complete: result.is_reasoning_complete
              }
              return [...prev.slice(0, -1), updatedMessage]
            }
            return prev
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
      
      // Add a confirmation message
      const confirmationMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `✓ Response "${response}" received. Continuing analysis...`,
        timestamp: new Date(),
      }
      setChatMessages(prev => [...prev, confirmationMessage])
      
      // Remove the HITL prompt message since it's been processed
      setTimeout(() => {
        setChatMessages(prev => prev.filter(msg => msg.id !== message.id))
      }, 500)
      
      // Continue polling for next message
      setTimeout(() => {
        pollForWorkflowMessages(message.workflow_id!)
      }, 1000) // Small delay to let backend process
      
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
              
              {chatMessages.map((message) => (
                <div key={message.id} className="space-y-1">
                  <div
                    className={cn(
                      "flex gap-2",
                      message.type === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    {(message.type === 'assistant' || message.type === 'hitl_prompt') && (
                      <div className={cn(
                        "w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5",
                        message.type === 'hitl_prompt' ? 'bg-orange-100' : 'bg-blue-100'
                      )}>
                        <Bot className={cn(
                          "w-4 h-4",
                          message.type === 'hitl_prompt' ? 'text-orange-600' : 'text-blue-600'
                        )} />
                      </div>
                    )}
                    
                    {/* Regular chat message */}
                    {message.type !== 'hitl_prompt' && (
                      <div>
                        <div
                          className={cn(
                            "rounded-lg px-3 py-2 text-sm max-w-[220px]",
                            message.type === 'user'
                              ? 'bg-blue-600 text-white rounded-br-sm'
                              : 'bg-gray-100 text-gray-900 rounded-bl-sm'
                          )}
                        >
                          <p className="whitespace-pre-wrap">{message.content}</p>
                        </div>
                        
                        {/* Cursor-style reasoning dropdown */}
                        {message.type === 'assistant' && (
                          <ReasoningDropdown message={message} />
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
              <div className="flex gap-2">
                <Input
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={handleChatKeyPress}
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
          </>
        )}
      </div>
    </div>
  )
}