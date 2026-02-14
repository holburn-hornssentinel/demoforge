/**
 * Custom hook for Server-Sent Events (SSE) with auto-reconnect
 */
import { useEffect, useRef, useState } from 'react'

export interface SSEMessage<T = any> {
  id?: string
  event?: string
  data: T
  retry?: number
}

export interface UseSSEOptions {
  enabled?: boolean
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onOpen?: () => void
  onError?: (error: Event) => void
}

export function useSSE<T = any>(
  url: string | null,
  options: UseSSEOptions = {}
) {
  const {
    enabled = true,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onOpen,
    onError,
  } = options

  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Event | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [reconnectCount, setReconnectCount] = useState(0)

  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    // Don't connect if disabled or no URL
    if (!enabled || !url) {
      return
    }

    // Clear any pending reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Create EventSource connection
    const eventSource = new EventSource(url)
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      setIsConnected(true)
      setError(null)
      setReconnectCount(0)
      onOpen?.()
    }

    eventSource.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data)
        setData(parsedData)
      } catch {
        // If parsing fails, use raw data
        setData(event.data as T)
      }
    }

    eventSource.onerror = (err) => {
      setIsConnected(false)
      setError(err)
      onError?.(err)

      // Close the connection
      eventSource.close()

      // Attempt reconnection if enabled
      if (reconnect && reconnectCount < maxReconnectAttempts) {
        reconnectTimeoutRef.current = setTimeout(() => {
          setReconnectCount((prev) => prev + 1)
        }, reconnectInterval)
      }
    }

    // Cleanup on unmount or URL change
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      eventSource.close()
      setIsConnected(false)
    }
  }, [
    url,
    enabled,
    reconnect,
    reconnectInterval,
    maxReconnectAttempts,
    reconnectCount,
    onOpen,
    onError,
  ])

  // Manual close function
  const close = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      setIsConnected(false)
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }

  return {
    data,
    error,
    isConnected,
    reconnectCount,
    close,
  }
}
