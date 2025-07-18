<template>
  <div class="conversation-thread">
    <div class="thread-header">
      <h2 class="thread-title">
        💬 Conversation Thread
      </h2>
      <div class="thread-stats">
        <span class="message-count">{{ messages.length }} messages</span>
        <span
          v-if="loading"
          class="loading-indicator"
        >🔄 Loading...</span>
      </div>
    </div>
    
    <div 
      ref="messageContainer"
      class="message-container"
      @scroll="handleScroll"
    >
      <div
        v-if="messages.length === 0 && !loading"
        class="empty-state"
      >
        <div class="empty-icon">
          💬
        </div>
        <h3 class="empty-title">
          No conversations found
        </h3>
        <p class="empty-description">
          Try adjusting your filters or check back later for new conversations.
        </p>
      </div>
      
      <!-- Slack風のメッセージフロー表示 -->
      <div class="message-list">
        <div
          v-for="message in sortedMessages"
          :key="message.id"
          class="message-item"
          :class="getMessageClass(message)"
        >
          <div class="message-avatar">
            <span class="avatar-emoji">{{ getWorkerEmoji(message.source) }}</span>
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="sender-name">{{ message.source }}</span>
              <span class="message-time">{{ formatTime(message.timestamp) }}</span>
              <span
                class="message-type"
                :class="`type-${message.messageType}`"
              >
                {{ getMessageTypeIcon(message.messageType) }}
              </span>
            </div>
            <div class="message-body">
              {{ message.message }}
            </div>
          </div>
          <div class="message-actions">
            <button
              class="action-btn"
              title="Copy message"
              @click="copyMessage(message)"
            >
              📋
            </button>
            <button
              class="action-btn"
              title="Show details"
              @click="showMessageDetails(message)"
            >
              ℹ️
            </button>
          </div>
        </div>
      </div>
      
      <div
        v-if="loading"
        class="loading-more"
      >
        <div class="loading-spinner" />
        <span>Loading more messages...</span>
      </div>
    </div>
    
    <!-- Message Details Modal -->
    <div
      v-if="selectedMessage"
      class="message-modal-overlay"
      @click="closeMessageDetails"
    >
      <div
        class="message-modal"
        @click.stop
      >
        <div class="modal-header">
          <h3 class="modal-title">
            Message Details
          </h3>
          <button
            class="close-btn"
            @click="closeMessageDetails"
          >
            ✕
          </button>
        </div>
        <div class="modal-content">
          <div class="detail-row">
            <span class="detail-label">From:</span>
            <span class="detail-value">{{ getWorkerEmoji(selectedMessage.source) }} {{ selectedMessage.source }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">To:</span>
            <span class="detail-value">{{ getWorkerEmoji(selectedMessage.target) }} {{ selectedMessage.target }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Type:</span>
            <span class="detail-value">{{ selectedMessage.messageType }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Time:</span>
            <span class="detail-value">{{ formatFullTime(selectedMessage.timestamp) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Session ID:</span>
            <span class="detail-value">{{ selectedMessage.sessionId || 'N/A' }}</span>
          </div>
          <div class="detail-row full-width">
            <span class="detail-label">Message:</span>
            <pre class="detail-message">{{ selectedMessage.message }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'

interface Message {
  id: string
  timestamp: string
  source: string
  target: string
  messageType: string
  message: string
  sessionId?: string
}

// MessageGroup interface removed - using direct message flow

interface Props {
  messages: Message[]
  loading: boolean
}

interface Emits {
  (_e: 'load-more'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Refs
const messageContainer = ref<HTMLElement>()
const selectedMessage = ref<Message | null>(null)

// Worker emoji mapping (should match the main dashboard)
const workerEmojis: Record<string, string> = {
  queen: '👑',
  developer: '👨‍💻',
  tester: '🧪',
  analyzer: '🔍',
  documenter: '📝',
  reviewer: '👀',
  beekeeper: '📋',
  hive_cli: '🐝'
}

// Computed properties
const sortedMessages = computed(() => {
  // Sort messages by timestamp (newest first for Hive)
  return [...props.messages].sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  )
})

// Methods
const getWorkerEmoji = (workerName: string): string => {
  return workerEmojis[workerName] || '🤖'
}

const getMessageTypeIcon = (type: string): string => {
  const icons: Record<string, string> = {
    direct: '💬',
    response: '↩️',
    error: '⚠️',
    task_start: '🚀',
    task_complete: '✅',
    test: '🧪'
  }
  return icons[type] || '💬'
}

// formatMessageType removed - not used in Slack-style layout

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// formatGroupTime removed - not needed for Slack-style layout

const formatFullTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString('ja-JP')
}

const getMessageClass = (message: Message): string => {
  return `message-${message.messageType}`
}

const copyMessage = async (message: Message) => {
  try {
    await navigator.clipboard.writeText(message.message)
    // Show toast notification (you could add a toast system here)
    console.log('Message copied to clipboard')
  } catch (error) {
    console.error('Failed to copy message:', error)
  }
}

const showMessageDetails = (message: Message) => {
  selectedMessage.value = message
}

const closeMessageDetails = () => {
  selectedMessage.value = null
}

const handleScroll = () => {
  if (!messageContainer.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = messageContainer.value
  const scrollPercentage = scrollTop / (scrollHeight - clientHeight)
  
  // Load more when scrolled to bottom
  if (scrollPercentage > 0.9 && !props.loading) {
    emit('load-more')
  }
}

// Auto-scroll to top when new messages arrive (Slack-style)
watch(() => props.messages.length, async () => {
  await nextTick()
  if (messageContainer.value) {
    messageContainer.value.scrollTop = 0
  }
})
</script>

<style scoped>
.conversation-thread {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
}

.thread-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.thread-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.thread-stats {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.loading-indicator {
  color: #3b82f6;
}

.message-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #6b7280;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: #374151;
}

.empty-description {
  font-size: 0.875rem;
  margin: 0;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.message-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 16px;
  transition: background-color 0.2s;
  border-radius: 0;
  min-height: 48px;
}

.message-item:hover {
  background: #f9fafb;
}

.message-error {
  background: #fef2f2;
  border-left: 4px solid #ef4444;
}

.message-avatar {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.avatar-emoji {
  font-size: 1.5rem;
  line-height: 1;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 4px;
}

.sender-name {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.message-time {
  color: #6b7280;
  font-size: 0.75rem;
}

.message-type {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.type-direct {
  background: #dbeafe;
  color: #1e40af;
}

.type-response {
  background: #d1fae5;
  color: #065f46;
}

.type-error {
  background: #fee2e2;
  color: #991b1b;
}

.type-task_start {
  background: #ddd6fe;
  color: #5b21b6;
}

.type-task_complete {
  background: #d1fae5;
  color: #065f46;
}

.type-test {
  background: #fef3c7;
  color: #92400e;
}

.message-body {
  color: #374151;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.875rem;
}

.message-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  margin-left: 8px;
  flex-shrink: 0;
}

.message-item:hover .message-actions {
  opacity: 1;
}

.action-btn {
  padding: 0.25rem;
  background: transparent;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1rem;
  color: #6b7280;
}

.loading-spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid #e5e7eb;
  border-top: 2px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Message Details Modal */
.message-modal-overlay {
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

.message-modal {
  background: white;
  border-radius: 0.75rem;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #6b7280;
  padding: 0.25rem;
}

.close-btn:hover {
  color: #374151;
}

.modal-content {
  padding: 1.5rem;
  overflow-y: auto;
}

.detail-row {
  display: flex;
  margin-bottom: 1rem;
  align-items: flex-start;
}

.detail-row.full-width {
  flex-direction: column;
}

.detail-label {
  font-weight: 600;
  color: #374151;
  min-width: 80px;
  margin-right: 1rem;
}

.detail-value {
  color: #6b7280;
}

.detail-message {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  padding: 1rem;
  margin-top: 0.5rem;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 0.875rem;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .thread-header {
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
  }
  
  .message-item {
    padding: 12px;
    gap: 8px;
  }
  
  .message-avatar {
    width: 32px;
    height: 32px;
  }
  
  .avatar-emoji {
    font-size: 1.25rem;
  }
  
  .message-header {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .sender-name {
    font-size: 0.8rem;
  }
  
  .message-time {
    font-size: 0.7rem;
  }
  
  .message-body {
    font-size: 0.8rem;
  }
  
  .message-actions {
    opacity: 1;
    margin-left: 0;
    margin-top: 4px;
  }
  
  .message-modal {
    width: 95%;
    margin: 1rem;
  }
}
</style>