<template>
  <div class="communications-panel">
    <div class="panel-header">
      <h2 class="panel-title">
        💬 Communications
      </h2>
      
      <div class="panel-controls">
        <div class="message-count">
          {{ filteredMessages.length }} / {{ totalMessages }} messages
        </div>
        
        <select 
          v-model="selectedFilter" 
          class="filter-select"
          @change="applyFilter"
        >
          <option value="all">
            All Types
          </option>
          <option value="task_assignment">
            Task Assignment
          </option>
          <option value="task_result">
            Task Result
          </option>
          <option value="coordination">
            Coordination
          </option>
          <option value="status_update">
            Status Update
          </option>
          <option value="error">
            Error
          </option>
        </select>
        
        <select 
          v-model="selectedWorker" 
          class="worker-select"
          @change="applyFilter"
        >
          <option value="all">
            All Workers
          </option>
          <option 
            v-for="worker in availableWorkers" 
            :key="worker" 
            :value="worker"
          >
            {{ worker }}
          </option>
        </select>
        
        <button 
          class="control-btn"
          :class="{ active: autoScroll }"
          @click="toggleAutoScroll"
        >
          📜 Auto
        </button>
        
        <button 
          class="control-btn"
          @click="clearMessages"
        >
          🗑️ Clear
        </button>
        
        <button 
          class="control-btn"
          @click="exportMessages"
        >
          💾 Export
        </button>
      </div>
    </div>
    
    <div 
      ref="messagesContainer"
      class="messages-container"
      @scroll="onScroll"
    >
      <div
        v-if="filteredMessages.length === 0"
        class="empty-state"
      >
        <div class="empty-icon">
          📭
        </div>
        <p class="empty-text">
          メッセージがありません
        </p>
        <p class="empty-subtext">
          {{ selectedFilter !== 'all' || selectedWorker !== 'all' 
            ? 'フィルターを変更してください' 
            : 'システムが起動中です...' }}
        </p>
      </div>
      
      <div
        v-else
        class="messages-list"
      >
        <MessageItem
          v-for="message in paginatedMessages"
          :key="message.id"
          :message="message"
          :is-highlighted="highlightedMessage === message.id"
          @click="onMessageClick"
          @copy="onMessageCopy"
        />
        
        <!-- 無限スクロール用のローダー -->
        <div 
          v-if="hasMoreMessages"
          ref="loadMoreTrigger"
          class="load-more-trigger"
        >
          <div class="loader">
            <div class="spinner" />
            <span>読み込み中...</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- メッセージ統計 -->
    <div class="panel-footer">
      <div class="message-stats">
        <div class="stat-group">
          <div class="stat-item">
            <span class="stat-dot task-assignment" />
            <span class="stat-label">Task</span>
            <span class="stat-value">{{ getMessageCountByType('task_assignment') }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-dot task-result" />
            <span class="stat-label">Result</span>
            <span class="stat-value">{{ getMessageCountByType('task_result') }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-dot coordination" />
            <span class="stat-label">Coord</span>
            <span class="stat-value">{{ getMessageCountByType('coordination') }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-dot error" />
            <span class="stat-label">Error</span>
            <span class="stat-value">{{ getMessageCountByType('error') }}</span>
          </div>
        </div>
        
        <div class="last-update">
          最終更新: {{ lastUpdateTime }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import MessageItem from './ui/MessageItem.vue'
import type { Message } from '@/types'

interface Props {
  messages: Message[]
  totalMessages: number
}

const props = defineProps<Props>()

const messagesContainer = ref<HTMLElement>()
const loadMoreTrigger = ref<HTMLElement>()

const selectedFilter = ref('all')
const selectedWorker = ref('all')
const autoScroll = ref(true)
const highlightedMessage = ref('')
const messagesPerPage = ref(50)
const currentPage = ref(1)

const filteredMessages = computed(() => {
  let filtered = [...props.messages]
  
  // タイプフィルター
  if (selectedFilter.value !== 'all') {
    filtered = filtered.filter(msg => msg.message_type === selectedFilter.value)
  }
  
  // ワーカーフィルター
  if (selectedWorker.value !== 'all') {
    filtered = filtered.filter(msg => 
      msg.source === selectedWorker.value || msg.target === selectedWorker.value
    )
  }
  
  // 時間順でソート（新しい順）
  return filtered.sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  )
})

const paginatedMessages = computed(() => {
  const endIndex = currentPage.value * messagesPerPage.value
  return filteredMessages.value.slice(0, endIndex)
})

const hasMoreMessages = computed(() => {
  return paginatedMessages.value.length < filteredMessages.value.length
})

const availableWorkers = computed(() => {
  const workers = new Set<string>()
  props.messages.forEach(msg => {
    if (msg.source) workers.add(msg.source)
    if (msg.target) workers.add(msg.target)
  })
  return Array.from(workers).sort()
})

const lastUpdateTime = computed(() => {
  if (props.messages.length === 0) return '--'
  const latest = props.messages[0]?.timestamp
  if (!latest) return '--'
  
  try {
    return new Date(latest).toLocaleTimeString('ja-JP')
  } catch {
    return '--'
  }
})

// メッセージタイプ別カウント
const getMessageCountByType = (type: string): number => {
  return props.messages.filter(msg => msg.message_type === type).length
}

// 新しいメッセージが追加された時の自動スクロール
watch(
  () => props.messages.length,
  async () => {
    if (autoScroll.value) {
      await nextTick()
      scrollToBottom()
    }
  }
)

// Intersection Observer for infinite scroll
let intersectionObserver: IntersectionObserver | null = null

onMounted(() => {
  setupInfiniteScroll()
})

onUnmounted(() => {
  if (intersectionObserver) {
    intersectionObserver.disconnect()
  }
})

const setupInfiniteScroll = () => {
  intersectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && hasMoreMessages.value) {
          loadMoreMessages()
        }
      })
    },
    { threshold: 0.1 }
  )
  
  if (loadMoreTrigger.value) {
    intersectionObserver.observe(loadMoreTrigger.value)
  }
}

const loadMoreMessages = () => {
  currentPage.value++
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const onScroll = () => {
  if (!messagesContainer.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10
  
  // ユーザーが手動でスクロールした場合は自動スクロールを無効にする
  if (!isAtBottom && autoScroll.value) {
    autoScroll.value = false
  }
}

const applyFilter = () => {
  currentPage.value = 1
}

const toggleAutoScroll = () => {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value) {
    scrollToBottom()
  }
}

const clearMessages = () => {
  // 実際のクリア処理は親コンポーネントで実装
  console.log('Clear messages requested')
}

const exportMessages = () => {
  const dataStr = JSON.stringify(filteredMessages.value, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = `hive-messages-${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  URL.revokeObjectURL(url)
}

const onMessageClick = (message: Message) => {
  highlightedMessage.value = highlightedMessage.value === message.id ? '' : message.id
}

const onMessageCopy = (message: Message) => {
  const textToCopy = `[${message.timestamp}] ${message.source} → ${message.target}: ${message.message}`
  
  if (navigator.clipboard) {
    navigator.clipboard.writeText(textToCopy)
  } else {
    // フォールバック
    const textArea = document.createElement('textarea')
    textArea.value = textToCopy
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
  }
}
</script>

<style scoped>
.communications-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.panel-header {
  padding: 16px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.panel-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.panel-controls {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.message-count {
  font-size: 14px;
  color: #64748b;
  margin-right: 8px;
}

.filter-select,
.worker-select {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  max-width: 120px;
}

.control-btn {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.control-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.control-btn.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  background: #fafbfc;
}

.messages-container::-webkit-scrollbar {
  width: 8px;
}

.messages-container::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  text-align: center;
  color: #64748b;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.empty-subtext {
  font-size: 14px;
  opacity: 0.7;
}

.messages-list {
  padding: 16px;
}

.load-more-trigger {
  padding: 20px;
  display: flex;
  justify-content: center;
}

.loader {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 14px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #e2e8f0;
  border-top: 2px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.panel-footer {
  padding: 12px 20px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.message-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-group {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.stat-dot.task-assignment {
  background: #3b82f6;
}

.stat-dot.task-result {
  background: #10b981;
}

.stat-dot.coordination {
  background: #8b5cf6;
}

.stat-dot.error {
  background: #ef4444;
}

.stat-label {
  color: #64748b;
  font-weight: 500;
}

.stat-value {
  color: #1f2937;
  font-weight: 600;
}

.last-update {
  font-size: 12px;
  color: #64748b;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .panel-controls {
    justify-content: center;
  }
  
  .filter-select,
  .worker-select {
    max-width: 100px;
    font-size: 12px;
  }
  
  .control-btn {
    font-size: 12px;
    padding: 4px 8px;
  }
  
  .stat-group {
    gap: 12px;
  }
  
  .message-stats {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
}
</style>