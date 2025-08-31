import { useEffect, useRef } from 'react'

interface SSEOptions {
  onMessage?: (data: any) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  enabled?: boolean
}

export const useSSE = (url: string, options: SSEOptions = {}) => {
  const { onMessage, onError, onOpen, enabled = true } = options
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!enabled) return

    const eventSource = new EventSource(url)
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      console.log(`SSE connection opened: ${url}`)
      onOpen?.()
    }

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage?.(data)
      } catch (error) {
        console.error('Failed to parse SSE message:', error)
        onMessage?.(event.data)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE error:', error)
      onError?.(error)
    }

    return () => {
      eventSource.close()
    }
  }, [url, enabled, onMessage, onError, onOpen])

  const close = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
  }

  return { close }
}