<template>
  <div class="command-page">
    <!-- ヘッダー -->
    <DashboardHeader
      :connection-status="connectionStatus"
      :active-workers="activeMembersCount"
      :total-workers="totalMembersCount"
      @refresh="handleRefresh"
      @toggle-debug="toggleDebugMode"
    />
    
    <!-- メインコンテンツ -->
    <div class="command-container">
      <!-- コマンド入力エリア -->
      <div class="command-input-section">
        <div class="input-header">
          <h2>🎯 BeeKeeper Commands</h2>
          <div class="command-status">
            <span
              class="status-indicator"
              :class="{ active: isExecuting }"
            />
            <span class="status-text">{{ isExecuting ? '実行中...' : '待機中' }}</span>
          </div>
        </div>
        
        <div class="command-form">
          <!-- ワーカー選択 -->
          <div class="form-group">
            <label class="form-label">対象ワーカー:</label>
            <select
              v-model="selectedWorker"
              class="worker-select"
              :disabled="isExecuting"
            >
              <option value="">
                -- ワーカーを選択 --
              </option>
              <option
                v-for="worker in availableWorkers"
                :key="worker.id"
                :value="worker.id"
              >
                {{ worker.emoji }} {{ worker.name }}
              </option>
            </select>
          </div>
          
          <!-- コマンドタイプ選択 -->
          <div class="form-group">
            <label class="form-label">コマンドタイプ:</label>
            <div class="command-type-buttons">
              <button
                v-for="type in commandTypes"
                :key="type.id"
                class="type-btn"
                :class="{ active: selectedCommandType === type.id }"
                :disabled="isExecuting"
                @click="selectCommandType(type.id)"
              >
                {{ type.emoji }} {{ type.name }}
              </button>
            </div>
          </div>
          
          <!-- コマンド入力 -->
          <div class="form-group">
            <label class="form-label">
              コマンド内容:
              <span class="char-count">({{ commandText.length }}/2000)</span>
            </label>
            <textarea
              v-model="commandText"
              class="command-textarea"
              placeholder="実行したいコマンドやタスクを入力してください..."
              maxlength="2000"
              :disabled="isExecuting"
              @keydown.ctrl.enter="executeCommand"
            />
          </div>
          
          <!-- 実行ボタン -->
          <div class="form-actions">
            <button
              class="execute-btn"
              :disabled="!canExecute"
              @click="executeCommand"
            >
              <span v-if="isExecuting">⏳ 実行中...</span>
              <span v-else>🚀 実行</span>
            </button>
            <button
              v-if="isExecuting"
              class="cancel-btn"
              @click="cancelExecution"
            >
              ❌ キャンセル
            </button>
          </div>
        </div>
      </div>
      
      <!-- 結果表示エリア -->
      <div class="command-results-section">
        <div class="results-header">
          <h3>📋 実行結果</h3>
          <div class="results-controls">
            <button
              class="control-btn"
              :disabled="commandHistory.length === 0"
              @click="clearResults"
            >
              🗑️ クリア
            </button>
            <button
              class="control-btn"
              :disabled="commandHistory.length === 0"
              @click="downloadResults"
            >
              💾 保存
            </button>
          </div>
        </div>
        
        <div class="results-content">
          <div
            v-if="commandHistory.length === 0"
            class="empty-state"
          >
            <div class="empty-icon">
              📝
            </div>
            <p>まだコマンドが実行されていません</p>
          </div>
          
          <div
            v-else
            class="command-history"
          >
            <div
              v-for="(command, index) in commandHistory"
              :key="index"
              class="command-entry"
              :class="{ executing: command.status === 'executing' }"
            >
              <div class="command-header">
                <div class="command-info">
                  <span class="command-timestamp">{{ formatTimestamp(command.timestamp) }}</span>
                  <span class="command-worker">{{ command.worker }}</span>
                  <span class="command-type">{{ command.type }}</span>
                </div>
                <div
                  class="command-status-badge"
                  :class="command.status"
                >
                  {{ getStatusText(command.status) }}
                </div>
              </div>
              
              <div class="command-content">
                <div class="command-input">
                  <strong>入力:</strong>
                  <pre>{{ command.input }}</pre>
                </div>
                
                <div
                  v-if="command.output"
                  class="command-output"
                >
                  <strong>出力:</strong>
                  <pre>{{ command.output }}</pre>
                </div>
                
                <div
                  v-if="command.error"
                  class="command-error"
                >
                  <strong>エラー:</strong>
                  <pre>{{ command.error }}</pre>
                </div>
                
                <div
                  v-if="command.status === 'executing'"
                  class="command-progress"
                >
                  <div class="progress-indicator">
                    <div class="progress-spinner" />
                    <span>実行中...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import DashboardHeader from '@/components/DashboardHeader.vue'
import type { ConnectionStatus } from '@/types'

// デモ用データと設定
const connectionStatus = ref<ConnectionStatus>({
  isConnected: true,
  reconnectAttempts: 0,
  lastHeartbeat: new Date().toISOString()
})

// ワーカー定義
const availableWorkers = ref([
  { id: 'queen', name: 'Queen', emoji: '👑', description: 'タスク管理と調整' },
  { id: 'developer', name: 'Developer', emoji: '👨‍💻', description: '開発タスク' },
  { id: 'tester', name: 'Tester', emoji: '🧪', description: 'テストと品質保証' },
  { id: 'analyzer', name: 'Analyzer', emoji: '🔍', description: '分析と調査' },
  { id: 'documenter', name: 'Documenter', emoji: '📝', description: 'ドキュメント作成' },
  { id: 'reviewer', name: 'Reviewer', emoji: '👀', description: 'コードレビューと検証' }
])

// ワーカー情報をAPIから取得
const loadAvailableWorkers = async () => {
  try {
    const response = await window.fetch('/api/workers')
    if (response.ok) {
      const data = await response.json()
      if (data.workers && data.workers.length > 0) {
        availableWorkers.value = data.workers.map((worker: any) => ({
          id: worker.name.toLowerCase(),
          name: worker.name,
          emoji: worker.emoji,
          description: worker.status === 'active' ? 'アクティブ' : 'アイドル'
        }))
      }
    }
  } catch (error) {
    console.warn('Failed to load workers from API, using defaults:', error)
  }
}

// コマンドタイプ定義
const commandTypes = ref([
  { id: 'direct', name: 'Direct', emoji: '📨', description: '直接メッセージ' },
  { id: 'task', name: 'Task', emoji: '📋', description: 'タスク実行' },
  { id: 'query', name: 'Query', emoji: '❓', description: 'クエリ・質問' },
  { id: 'urgent', name: 'Urgent', emoji: '🚨', description: '緊急タスク' }
])

// フォーム状態
const selectedWorker = ref('')
const selectedCommandType = ref('direct')
const commandText = ref('')
const isExecuting = ref(false)

// コマンド履歴
interface CommandEntry {
  id: string
  timestamp: Date
  worker: string
  type: string
  input: string
  output?: string
  error?: string
  status: 'executing' | 'completed' | 'failed'
}

const commandHistory = ref<CommandEntry[]>([])

// 計算プロパティ
const activeMembersCount = computed(() => availableWorkers.value.filter(w => w.id !== 'beekeeper').length)
const totalMembersCount = computed(() => availableWorkers.value.length)

const canExecute = computed(() => {
  return selectedWorker.value && 
         commandText.value.trim().length > 0 && 
         !isExecuting.value
})

// メソッド
const selectCommandType = (typeId: string) => {
  selectedCommandType.value = typeId
}

const executeCommand = async () => {
  if (!canExecute.value) return
  
  isExecuting.value = true
  
  const commandEntry: CommandEntry = {
    id: `cmd_${Date.now()}`,
    timestamp: new Date(),
    worker: selectedWorker.value,
    type: selectedCommandType.value,
    input: commandText.value,
    status: 'executing'
  }
  
  commandHistory.value.unshift(commandEntry)
  
  try {
    // 接続状態確認
    if (!connectionStatus.value.isConnected) {
      throw new Error('サーバーに接続されていません。接続を確認してください。')
    }
    
    // hive_cli経由でコマンド実行
    const response = await sendCommand(
      selectedWorker.value,
      commandText.value,
      selectedCommandType.value
    )
    
    // WebSocketによるリアルタイム更新がない場合の直接更新
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
      commandEntry.output = response.output
      commandEntry.status = response.success ? 'completed' : 'failed'
      if (!response.success) {
        commandEntry.error = response.error
      }
    }
    // WebSocketが接続されている場合は、WebSocketメッセージで更新される
    
  } catch (error) {
    commandEntry.error = error instanceof Error ? error.message : 'Unknown error'
    commandEntry.status = 'failed'
    isExecuting.value = false
  }
  
  // フォームリセット
  commandText.value = ''
}

const cancelExecution = () => {
  isExecuting.value = false
  // 実行中のコマンドをキャンセル済みにマーク
  const executingCommand = commandHistory.value.find(cmd => cmd.status === 'executing')
  if (executingCommand) {
    executingCommand.status = 'failed'
    executingCommand.error = 'ユーザーによりキャンセルされました'
  }
}

const clearResults = () => {
  commandHistory.value = []
}

const downloadResults = () => {
  const data = JSON.stringify(commandHistory.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `hive_command_history_${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const handleRefresh = () => {
  // WebSocket再接続などの処理
  console.log('Refreshing connection...')
}

const toggleDebugMode = () => {
  console.log('Debug mode toggled')
}

// ユーティリティ関数
const formatTimestamp = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('ja-JP')
}

const getStatusText = (status: string) => {
  const statusMap = {
    executing: '⏳ 実行中',
    completed: '✅ 完了',
    failed: '❌ 失敗'
  }
  return statusMap[status as keyof typeof statusMap] || status
}

// API通信（実API統合）
const sendCommand = async (worker: string, message: string, type: string) => {
  try {
    const requestBody = {
      worker: worker,
      message: message,
      command_type: type,
      wait_for_response: true
    }
    
    const response = await window.fetch('/api/command', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const result = await response.json()
    
    return {
      success: result.success,
      output: result.response || result.error || 'No response received',
      error: result.success ? undefined : result.error
    }
  } catch (error) {
    console.error('Command execution failed:', error)
    return {
      success: false,
      output: undefined,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    }
  }
}

// WebSocket接続管理
let websocket: WebSocket | null = null

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.hostname
  const port = (import.meta as any).env?.DEV ? '8000' : window.location.port
  const wsUrl = `${protocol}//${host}:${port}/ws`
  
  websocket = new WebSocket(wsUrl)
  
  websocket.onopen = () => {
    console.log('WebSocket connected for commands')
    connectionStatus.value.isConnected = true
  }
  
  websocket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      
      // リアルタイムコマンド結果の受信
      if (data.type === 'command_executed') {
        const commandResult = data.data
        
        // 実行中のコマンドを探して更新
        const executingCommand = commandHistory.value.find(
          cmd => cmd.status === 'executing' && cmd.worker === commandResult.worker
        )
        
        if (executingCommand) {
          executingCommand.output = commandResult.response
          executingCommand.error = commandResult.error
          executingCommand.status = commandResult.success ? 'completed' : 'failed'
        }
        
        isExecuting.value = false
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }
  
  websocket.onclose = () => {
    console.log('WebSocket disconnected')
    connectionStatus.value.isConnected = false
    
    // 自動再接続（5秒後）
    setTimeout(() => {
      if (!websocket || websocket.readyState === WebSocket.CLOSED) {
        connectWebSocket()
      }
    }, 5000)
  }
  
  websocket.onerror = (error) => {
    console.error('WebSocket error:', error)
    connectionStatus.value.isConnected = false
  }
}

const disconnectWebSocket = () => {
  if (websocket) {
    websocket.close()
    websocket = null
  }
}

onMounted(() => {
  console.log('Command page initialized')
  loadAvailableWorkers()
  connectWebSocket()
})

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<style scoped>
.command-page {
  height: 100vh;
  background: #f1f5f9;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.command-container {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  padding: 20px;
  overflow: hidden;
}

.command-input-section,
.command-results-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.input-header,
.results-header {
  background: #f8fafc;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-header h2,
.results-header h3 {
  margin: 0;
  color: #1e293b;
  font-size: 18px;
}

.command-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #64748b;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
  transition: all 0.3s ease;
}

.status-indicator.active {
  background: #10b981;
  animation: pulse 2s infinite;
}

.command-form {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.char-count {
  font-weight: 400;
  color: #64748b;
  font-size: 12px;
}

.worker-select {
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  color: #374151;
}

.worker-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.command-type-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.type-btn {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  color: #374151;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.type-btn:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.type-btn.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.type-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.command-textarea {
  min-height: 120px;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  resize: vertical;
  background: white;
}

.command-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.execute-btn,
.cancel-btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  font-size: 14px;
}

.execute-btn {
  background: #3b82f6;
  color: white;
}

.execute-btn:hover:not(:disabled) {
  background: #2563eb;
}

.execute-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.cancel-btn {
  background: #ef4444;
  color: white;
}

.cancel-btn:hover {
  background: #dc2626;
}

.results-controls {
  display: flex;
  gap: 8px;
}

.control-btn {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  color: #374151;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control-btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.results-content {
  height: calc(100% - 70px);
  overflow-y: auto;
  padding: 20px;
}

.empty-state {
  text-align: center;
  color: #64748b;
  padding: 40px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.command-history {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.command-entry {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.command-entry.executing {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.command-header {
  background: #f8fafc;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
}

.command-info {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 12px;
  color: #64748b;
}

.command-timestamp {
  font-weight: 600;
  color: #374151;
}

.command-worker,
.command-type {
  background: #e2e8f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.command-status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.command-status-badge.executing {
  background: #dbeafe;
  color: #1d4ed8;
}

.command-status-badge.completed {
  background: #dcfce7;
  color: #166534;
}

.command-status-badge.failed {
  background: #fecaca;
  color: #991b1b;
}

.command-content {
  padding: 16px;
}

.command-input,
.command-output,
.command-error {
  margin-bottom: 12px;
}

.command-input strong {
  color: #374151;
}

.command-output strong {
  color: #059669;
}

.command-error strong {
  color: #dc2626;
}

.command-content pre {
  background: #f1f5f9;
  padding: 8px 12px;
  border-radius: 4px;
  margin-top: 4px;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
  color: #374151;
}

.command-progress {
  margin-top: 8px;
  padding: 8px 12px;
  background: #eff6ff;
  border-radius: 4px;
  border-left: 3px solid #3b82f6;
}

.progress-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1d4ed8;
  font-size: 13px;
}

.progress-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #e0e7ff;
  border-top: 2px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@media (max-width: 1024px) {
  .command-container {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
  
  .command-type-buttons {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .command-container {
    padding: 12px;
    gap: 16px;
  }
  
  .command-form {
    padding: 16px;
  }
  
  .command-type-buttons {
    grid-template-columns: 1fr;
  }
  
  .form-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .execute-btn,
  .cancel-btn {
    width: 100%;
  }
}
</style>