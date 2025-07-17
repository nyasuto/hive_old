import { ref, onMounted, onUnmounted, computed } from 'vue'
import type { DashboardData, ConnectionStatus } from '@/types'

export function useWebSocket(url: string) {
  const data = ref<DashboardData>()
  const error = ref<string>()
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const lastHeartbeat = ref<string>()
  
  let ws: WebSocket | null = null
  let reconnectTimer: number | null = null
  let heartbeatTimer: number | null = null
  
  const maxReconnectAttempts = 5
  const heartbeatInterval = 30000 // 30秒
  const reconnectDelay = 2000 // 2秒
  
  const connectionStatus = computed<ConnectionStatus>(() => ({
    isConnected: isConnected.value,
    lastHeartbeat: lastHeartbeat.value,
    reconnectAttempts: reconnectAttempts.value,
    error: error.value,
  }))
  
  const connect = () => {
    try {
      ws = new WebSocket(url)
      
      ws.onopen = () => {
        console.log('📡 WebSocket connected')
        isConnected.value = true
        reconnectAttempts.value = 0
        error.value = undefined
        startHeartbeat()
      }
      
      ws.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data) as DashboardData
          data.value = parsedData
          lastHeartbeat.value = new Date().toISOString()
          
          // デバッグログ（必要に応じて）
          if (window.location.search.includes('debug=true')) {
            console.log('📊 Dashboard update received:', parsedData.timestamp)
          }
        } catch (parseError) {
          console.error('Failed to parse WebSocket message:', parseError)
          error.value = 'メッセージの解析に失敗しました'
        }
      }
      
      ws.onclose = () => {
        console.log('📡 WebSocket disconnected')
        isConnected.value = false
        stopHeartbeat()
        scheduleReconnect()
      }
      
      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        error.value = 'WebSocket接続エラーが発生しました'
      }
      
    } catch (connectionError) {
      console.error('Failed to create WebSocket connection:', connectionError)
      error.value = 'WebSocket接続の作成に失敗しました'
    }
  }
  
  const disconnect = () => {
    if (ws) {
      ws.close()
      ws = null
    }
    stopHeartbeat()
    clearReconnectTimer()
  }
  
  const scheduleReconnect = () => {
    if (reconnectAttempts.value < maxReconnectAttempts) {
      reconnectAttempts.value++
      const delay = reconnectDelay * reconnectAttempts.value
      
      console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttempts.value}/${maxReconnectAttempts})`)
      
      reconnectTimer = window.setTimeout(() => {
        connect()
      }, delay)
    } else {
      error.value = '再接続の試行回数が上限に達しました'
    }
  }
  
  const startHeartbeat = () => {
    heartbeatTimer = window.setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, heartbeatInterval)
  }
  
  const stopHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }
  
  const clearReconnectTimer = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }
  
  const manualReconnect = () => {
    disconnect()
    reconnectAttempts.value = 0
    error.value = undefined
    connect()
  }
  
  onMounted(() => {
    connect()
  })
  
  onUnmounted(() => {
    disconnect()
  })
  
  return {
    data,
    error,
    connectionStatus,
    isConnected,
    connect,
    disconnect,
    manualReconnect,
  }
}