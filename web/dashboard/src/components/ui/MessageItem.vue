<template>
  <div 
    class="message-item"
    :class="[message.message_type, { highlighted: isHighlighted, 'high-priority': message.priority === 'high' }]"
    @click="onClick"
  >
    <div class="message-header">
      <div class="message-flow">
        <div class="worker-badge source">
          {{ getWorkerEmoji(message.source) }} {{ message.source }}
        </div>
        <div class="flow-arrow" :class="message.message_type">
          {{ getFlowArrow(message.message_type) }}
        </div>
        <div class="worker-badge target">
          {{ getWorkerEmoji(message.target) }} {{ message.target }}
        </div>
      </div>
      
      <div class="message-meta">
        <span class="message-type" :class="message.message_type">
          {{ getMessageTypeLabel(message.message_type) }}
        </span>
        <span class="message-time">
          {{ formatTime(message.timestamp) }}
        </span>
        <button 
          class="copy-btn"
          @click.stop="onCopy"
          title="コピー"
        >
          📋
        </button>
      </div>
    </div>
    
    <div class="message-content">
      <div class="message-text">
        {{ truncateMessage(message.message) }}
      </div>
      
      <div v-if="isLongMessage" class="expand-toggle">
        <button 
          class="expand-btn"
          @click.stop="toggleExpanded"
        >
          {{ isExpanded ? '▲ 縮小' : '▼ 展開' }}
        </button>
      </div>
    </div>
    
    <!-- 優先度インジケーター -->
    <div 
      v-if="message.priority && message.priority !== 'medium'"
      class="priority-indicator"
      :class="message.priority"
    >
      {{ message.priority === 'high' ? '🔥' : '🔽' }}
    </div>
    
    <!-- エラーメッセージの場合の詳細表示 -->
    <div v-if="message.message_type === 'error'" class="error-details">
      <div class="error-badge">⚠️ エラー</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Message } from '@/types'

interface Props {
  message: Message
  isHighlighted?: boolean
}

interface Emits {
  (e: 'click', message: Message): void
  (e: 'copy', message: Message): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const isExpanded = ref(false)
const maxMessageLength = 120

const isLongMessage = computed(() => {
  return props.message.message.length > maxMessageLength
})

const truncateMessage = (text: string): string => {
  if (isExpanded.value || text.length <= maxMessageLength) {
    return text
  }
  return text.substring(0, maxMessageLength) + '...'
}

const getWorkerEmoji = (workerName: string): string => {
  const emojiMap: Record<string, string> = {
    beekeeper: '🕺',
    queen: '👑',
    developer: '👨‍💻',
    researcher: '🔬',
    coordinator: '🎯',
    specialist: '🔧',
  }
  return emojiMap[workerName] || '🐝'
}

const getFlowArrow = (messageType: string): string => {
  const arrowMap: Record<string, string> = {
    task_assignment: '📤',
    task_result: '📥',
    coordination: '↔️',
    status_update: '📊',
    error: '❌',
  }
  return arrowMap[messageType] || '→'
}

const getMessageTypeLabel = (type: string): string => {
  const labelMap: Record<string, string> = {
    task_assignment: 'タスク割当',
    task_result: 'タスク結果',
    coordination: '調整',
    status_update: 'ステータス',
    error: 'エラー',
  }
  return labelMap[type] || type
}

const formatTime = (timestamp: string): string => {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return timestamp
  }
}

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}

const onClick = () => {
  emit('click', props.message)
}

const onCopy = () => {
  emit('copy', props.message)
}
</script>

<style scoped>
.message-item {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  border-left: 4px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  cursor: pointer;
  position: relative;
}

.message-item:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.message-item.highlighted {
  background: #fef3c7;
  border-left-color: #f59e0b;
}

.message-item.high-priority {
  border-left-width: 6px;
  background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
}

.message-item.task-assignment {
  border-left-color: #3b82f6;
}

.message-item.task-result {
  border-left-color: #10b981;
}

.message-item.coordination {
  border-left-color: #8b5cf6;
}

.message-item.status_update {
  border-left-color: #f59e0b;
}

.message-item.error {
  border-left-color: #ef4444;
  background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
}

.message-flow {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.worker-badge {
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  color: #475569;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.worker-badge.source {
  background: #e0f2fe;
  color: #0369a1;
}

.worker-badge.target {
  background: #ecfdf5;
  color: #047857;
}

.flow-arrow {
  font-size: 16px;
  opacity: 0.7;
}

.flow-arrow.task-assignment {
  color: #3b82f6;
}

.flow-arrow.task-result {
  color: #10b981;
}

.flow-arrow.coordination {
  color: #8b5cf6;
}

.flow-arrow.status_update {
  color: #f59e0b;
}

.flow-arrow.error {
  color: #ef4444;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.message-type {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.message-type.task-assignment {
  background: #dbeafe;
  color: #1e40af;
}

.message-type.task-result {
  background: #d1fae5;
  color: #065f46;
}

.message-type.coordination {
  background: #ede9fe;
  color: #5b21b6;
}

.message-type.status_update {
  background: #fef3c7;
  color: #92400e;
}

.message-type.error {
  background: #fee2e2;
  color: #991b1b;
}

.message-time {
  font-size: 12px;
  color: #6b7280;
  font-family: monospace;
}

.copy-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.5;
  transition: opacity 0.2s ease;
  padding: 2px;
}

.copy-btn:hover {
  opacity: 1;
}

.message-content {
  color: #374151;
  line-height: 1.4;
}

.message-text {
  word-break: break-word;
  white-space: pre-wrap;
}

.expand-toggle {
  margin-top: 8px;
}

.expand-btn {
  background: none;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s ease;
}

.expand-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.priority-indicator {
  position: absolute;
  top: -8px;
  right: -8px;
  font-size: 16px;
  background: white;
  border-radius: 50%;
  padding: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.priority-indicator.high {
  animation: pulse 2s infinite;
}

.error-details {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #fee2e2;
}

.error-badge {
  display: inline-block;
  background: #fee2e2;
  color: #991b1b;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@media (max-width: 768px) {
  .message-item {
    padding: 10px;
  }
  
  .message-header {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .message-flow {
    justify-content: space-between;
  }
  
  .worker-badge {
    font-size: 11px;
    padding: 3px 6px;
    max-width: 80px;
  }
  
  .message-meta {
    justify-content: space-between;
  }
  
  .message-type {
    font-size: 10px;
  }
}
</style>