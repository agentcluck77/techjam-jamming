'use client'

import { useState, useRef, useCallback } from 'react'

interface StreamingMessage {
  id: string
  type: 'user' | 'assistant' | 'thinking'
  content: string
  timestamp: Date
  isStreaming?: boolean
  sessionId?: string
}

interface StreamingChatHook {
  messages: StreamingMessage[]
  isStreaming: boolean
  sendMessage: (message: string) => Promise<void>
  clearMessages: () => void
}

export function useStreamingChat(): StreamingChatHook {
  const [messages, setMessages] = useState<StreamingMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)
  const currentResponseRef = useRef<string>('')
  const currentMessageIdRef = useRef<string | null>(null)

  const addMessage = useCallback((message: StreamingMessage) => {
    setMessages(prev => [...prev, message])
  }, [])

  const updateStreamingMessage = useCallback((sessionId: string, content: string) => {
    setMessages(prev => prev.map(msg => 
      msg.sessionId === sessionId && msg.isStreaming 
        ? { ...msg, content: content }
        : msg
    ))
  }, [])

  const completeStreamingMessage = useCallback((sessionId: string) => {
    setMessages(prev => prev.map(msg => 
      msg.sessionId === sessionId && msg.isStreaming 
        ? { ...msg, isStreaming: false }
        : msg
    ))
    setIsStreaming(false)
  }, [])

  const sendMessage = useCallback(async (messageContent: string) => {
    if (isStreaming) return // Prevent sending while streaming

    // Add user message
    const userMessage: StreamingMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: messageContent,
      timestamp: new Date()
    }
    addMessage(userMessage)

    // Create initial assistant message
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: StreamingMessage = {
      id: assistantMessageId,
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      sessionId: '' // Will be set when we get session_id from stream
    }
    addMessage(assistantMessage)

    setIsStreaming(true)
    currentResponseRef.current = ''

    try {
      // Close existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }

      // Start streaming request
      const response = await fetch('/api/legal-chat-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: messageContent })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body reader available')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'status') {
                // Update the assistant message with session ID
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, sessionId: data.session_id }
                    : msg
                ))
              } else if (data.type === 'token') {
                // Append token to current response
                currentResponseRef.current += data.content
                updateStreamingMessage(data.session_id, currentResponseRef.current)
              } else if (data.type === 'complete') {
                // Stream complete
                completeStreamingMessage(data.session_id)
                break
              } else if (data.type === 'error') {
                // Handle error
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: `Error: ${data.message}`, isStreaming: false }
                    : msg
                ))
                setIsStreaming(false)
                break
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error)
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId 
          ? { ...msg, content: `Error: Failed to get response. ${error}`, isStreaming: false }
          : msg
      ))
      setIsStreaming(false)
    }
  }, [isStreaming, addMessage, updateStreamingMessage, completeStreamingMessage])

  const clearMessages = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }
    setMessages([])
    setIsStreaming(false)
    currentResponseRef.current = ''
  }, [])

  return {
    messages,
    isStreaming,
    sendMessage,
    clearMessages
  }
}