<template>
  <div class="dashboard">
    <!-- 統一ヘッダー -->
    <UnifiedHeader
      :connection-status="connectionStatus"
      @refresh="handleRefresh"
      @toggle-debug="toggleDebugMode"
    >
      <template #center>
        <div class="workers-summary">
          <div class="summary-item">
            <span class="summary-label">総ワーカー:</span>
            <span class="summary-value">{{ dashboardStore.totalWorkers }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">アクティブ:</span>
            <span class="summary-value active">{{ dashboardStore.activeWorkers.length }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">稼働時間:</span>
            <span class="summary-value">{{ uptime }}</span>
          </div>
        </div>
      </template>
    </UnifiedHeader>
    
    <!-- メインダッシュボード -->
    <div class="dashboard-container">
      <!-- ワーカーサイドバー -->
      <WorkersSidebar
        :workers="dashboardStore.workers"
        @worker-click="handleWorkerClick"
      />
      
      <!-- 中央コンテンツエリア -->
      <div class="dashboard-content">
        <!-- 通信フロー表示 -->
        <div class="flow-section">
          <CommunicationFlow
            :workers="dashboardStore.workers"
            :messages="dashboardStore.recentMessages"
          />
        </div>
        
        <!-- 通信パネル -->
        <div class="communications-section">
          <CommunicationsPanel
            :messages="dashboardStore.recentMessages"
            :total-messages="dashboardStore.messageCount"
          />
        </div>
        
        <!-- パフォーマンスメトリクス -->
        <div class="performance-section">
          <PerformancePanel
            :metrics="dashboardStore.performanceMetrics"
            :session="dashboardStore.currentSession"
          />
        </div>
      </div>
    </div>
    
    <!-- エラー表示 -->
    <div
      v-if="error"
      class="error-overlay"
    >
      <div class="error-dialog">
        <div class="error-header">
          <h3>⚠️ 接続エラー</h3>
          <button
            class="close-btn"
            @click="clearError"
          >
            ✕
          </button>
        </div>
        <div class="error-content">
          <p>{{ error }}</p>
          <div class="error-actions">
            <button
              class="retry-btn"
              @click="manualReconnect"
            >
              🔄 再接続
            </button>
            <button
              class="dismiss-btn"
              @click="clearError"
            >
              閉じる
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- デバッグモード表示 -->
    <div
      v-if="debugMode"
      class="debug-panel"
    >
      <div class="debug-header">
        <h4>🐛 Debug Info</h4>
        <button
          class="debug-close"
          @click="toggleDebugMode"
        >
          ✕
        </button>
      </div>
      <div class="debug-content">
        <div class="debug-item">
          <strong>接続状態:</strong> {{ isConnected ? '接続中' : '切断中' }}
        </div>
        <div class="debug-item">
          <strong>再接続試行:</strong> {{ connectionStatus.reconnectAttempts }}
        </div>
        <div class="debug-item">
          <strong>最終ハートビート:</strong> {{ connectionStatus.lastHeartbeat || 'なし' }}
        </div>
        <div class="debug-item">
          <strong>最終更新:</strong> {{ dashboardStore.lastUpdateTime || 'なし' }}
        </div>
        <div class="debug-item">
          <strong>メッセージ数:</strong> {{ dashboardStore.messageCount }}
        </div>
        <div class="debug-item">
          <strong>アクティブワーカー:</strong> {{ dashboardStore.activeWorkers.length }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useWebSocket } from '@/composables'
import { useDashboardStore } from '@/stores'
import UnifiedHeader from '@/components/UnifiedHeader.vue'
import WorkersSidebar from '@/components/WorkersSidebar.vue'
import CommunicationFlow from '@/components/CommunicationFlow.vue'
import CommunicationsPanel from '@/components/CommunicationsPanel.vue'
import PerformancePanel from '@/components/PerformancePanel.vue'
import type { Worker } from '@/types'

// WebSocket接続の設定
const websocketUrl = computed(() => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.hostname
  const port = (import.meta as any).env?.DEV ? '8002' : window.location.port
  return `${protocol}//${host}:${port}/ws`
})

const { 
  data, 
  error, 
  connectionStatus, 
  isConnected, 
  manualReconnect 
} = useWebSocket(websocketUrl.value)

const dashboardStore = useDashboardStore()
const debugMode = ref(false)
const startTime = ref(Date.now())

// 稼働時間計算
const uptime = computed(() => {
  const uptimeMs = Date.now() - startTime.value
  const hours = Math.floor(uptimeMs / (1000 * 60 * 60))
  const minutes = Math.floor((uptimeMs % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((uptimeMs % (1000 * 60)) / 1000)
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  } else {
    return `${seconds}s`
  }
})

// WebSocketデータをストアに同期
watch(data, (newData) => {
  if (newData) {
    dashboardStore.updateData(newData)
  }
}, { deep: true })

// エラーをストアに同期
watch(error, (newError) => {
  if (newError) {
    dashboardStore.setError(newError)
  }
})

const handleRefresh = () => {
  manualReconnect()
  dashboardStore.clearError()
}

const handleWorkerClick = (worker: Worker) => {
  console.log('Worker selected:', worker.name)
  // 必要に応じてワーカー詳細表示などの処理を追加
}

const clearError = () => {
  dashboardStore.clearError()
}

const toggleDebugMode = () => {
  debugMode.value = !debugMode.value
}

// URLパラメータからデバッグモードを有効化
if (window.location.search.includes('debug=true')) {
  debugMode.value = true
}
</script>

<style scoped>
.dashboard {
  height: 100vh;
  background: #f1f5f9;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Workers Summary Styles */
.workers-summary {
  display: flex;
  gap: 1.5rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.summary-label {
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 0.125rem;
}

.summary-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #1e293b;
}

.summary-value.active {
  color: #059669;
}

.dashboard-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.dashboard-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.flow-section {
  grid-column: 1 / -1;
  grid-row: 1;
}

.communications-section {
  grid-column: 1;
  grid-row: 2;
}

.performance-section {
  grid-column: 2;
  grid-row: 2;
}

.error-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.error-dialog {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  max-width: 400px;
  width: 90%;
  overflow: hidden;
}

.error-header {
  background: #fef2f2;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #fecaca;
}

.error-header h3 {
  margin: 0;
  color: #991b1b;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #991b1b;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-content {
  padding: 20px;
}

.error-content p {
  margin: 0 0 16px 0;
  color: #374151;
  line-height: 1.5;
}

.error-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.retry-btn,
.dismiss-btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.retry-btn {
  background: #3b82f6;
  color: white;
  border: none;
}

.retry-btn:hover {
  background: #2563eb;
}

.dismiss-btn {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.dismiss-btn:hover {
  background: #e5e7eb;
}

.debug-panel {
  position: fixed;
  top: 20px;
  right: 20px;
  background: rgba(0, 0, 0, 0.9);
  color: white;
  border-radius: 8px;
  padding: 0;
  min-width: 250px;
  z-index: 999;
  font-family: monospace;
  font-size: 12px;
}

.debug-header {
  background: rgba(255, 255, 255, 0.1);
  padding: 8px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.debug-header h4 {
  margin: 0;
  font-size: 14px;
}

.debug-close {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 14px;
}

.debug-content {
  padding: 12px;
}

.debug-item {
  margin-bottom: 4px;
  display: flex;
  gap: 8px;
}

.debug-item strong {
  min-width: 100px;
  color: #fbbf24;
}

@media (max-width: 1200px) {
  .dashboard-content {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
  }
  
  .flow-section {
    grid-column: 1;
    grid-row: 1;
    height: 300px;
  }
  
  .communications-section {
    grid-column: 1;
    grid-row: 2;
    height: 400px;
  }
  
  .performance-section {
    grid-column: 1;
    grid-row: 3;
    height: 300px;
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    flex-direction: column;
  }
  
  .dashboard-content {
    padding: 8px;
    gap: 8px;
  }
  
  .flow-section {
    height: 250px;
  }
  
  .communications-section {
    height: 300px;
  }
  
  .performance-section {
    height: 200px;
  }
  
  .debug-panel {
    position: static;
    margin: 16px;
    width: auto;
  }
}
</style>