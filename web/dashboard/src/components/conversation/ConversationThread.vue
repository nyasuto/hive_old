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
      
      <div
        v-for="(group, index) in groupedMessages"
        :key="index"
        class="message-group"
      >
        <div class="group-header">
          <span class="group-participants">
            <span class="participant">{{ group.participants.source.emoji }} {{ group.participants.source.name }}</span>
            <span class="conversation-arrow">💬</span>
            <span class="participant">{{ group.participants.target.emoji }} {{ group.participants.target.name }}</span>
          </span>
          <span class="group-time">{{ formatGroupTime(group.startTime) }}</span>
        </div>
        
        <div class="messages-list">
          <div
            v-for="message in group.messages"
            :key="message.id"
            class="message-item"
            :class="getMessageClass(message)"
          >
            <div class="message-header">
              <div class="message-sender">
                <span class="sender-emoji">{{ getWorkerEmoji(message.source) }}</span>
                <span class="sender-name">{{ message.source }}</span>
              </div>
              <div class="message-meta">
                <span
                  class="message-type"
                  :class="`type-${message.messageType}`"
                >
                  {{ getMessageTypeIcon(message.messageType) }} {{ formatMessageType(message.messageType) }}
                </span>
                <span class="message-time">{{ formatTime(message.timestamp) }}</span>
              </div>
            </div>
            
            <div class="message-content">
              <div class="message-text">
                {{ message.message }}
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

interface MessageGroup {
  participants: {
    source: { name: string; emoji: string }
    target: { name: string; emoji: string }
  }
  messages: Message[]
  startTime: string
}

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
const groupedMessages = computed(() => {
  const groups: MessageGroup[] = []
  const groupMap = new Map<string, MessageGroup>()
  
  for (const message of props.messages) {
    const key = `${message.source}-${message.target}`
    const reverseKey = `${message.target}-${message.source}`
    
    let group = groupMap.get(key) || groupMap.get(reverseKey)
    
    if (!group) {
      group = {
        participants: {
          source: {
            name: message.source,
            emoji: getWorkerEmoji(message.source)
          },
          target: {
            name: message.target,
            emoji: getWorkerEmoji(message.target)
          }
        },
        messages: [],
        startTime: message.timestamp
      }
      groups.push(group)
      groupMap.set(key, group)
    }
    
    group.messages.push(message)
    
    // Update start time if this message is earlier
    if (new Date(message.timestamp) < new Date(group.startTime)) {
      group.startTime = message.timestamp
    }
  }
  
  // Sort messages within each group by timestamp
  groups.forEach(group => {
    group.messages.sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )
  })
  
  // Sort groups by start time (most recent first)
  return groups.sort((a, b) => 
    new Date(b.startTime).getTime() - new Date(a.startTime).getTime()
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
    task: '📋',
    status: '📊',
    error: '⚠️',
    coordination: '🤝'
  }
  return icons[type] || '💬'
}

const formatMessageType = (type: string): string => {
  const labels: Record<string, string> = {
    direct: 'Direct',
    response: 'Response',
    task: 'Task',
    status: 'Status',
    error: 'Error',
    coordination: 'Coordination'
  }
  return labels[type] || type
}

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatGroupTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return 'Today ' + formatTime(timestamp)
  } else if (diffDays === 1) {
    return 'Yesterday ' + formatTime(timestamp)
  } else {
    return date.toLocaleDateString('ja-JP') + ' ' + formatTime(timestamp)
  }
}

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

// Auto-scroll to top when new messages arrive
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

.message-group {
  margin-bottom: 2rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  overflow: hidden;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
}

.group-participants {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #374151;
}

.participant {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.conversation-arrow {
  color: #9ca3af;
}

.group-time {
  font-size: 0.75rem;
  color: #6b7280;
}

.messages-list {
  display: flex;
  flex-direction: column;
}

.message-item {
  padding: 1rem;
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s;
}

.message-item:hover {
  background: #f9fafb;
}

.message-item:last-child {
  border-bottom: none;
}

.message-error {
  background: #fef2f2;
  border-left: 4px solid #ef4444;
}

.message-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.message-sender {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #374151;
}

.sender-emoji {
  font-size: 1.125rem;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.75rem;
}

.message-type {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
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

.type-task {
  background: #fef3c7;
  color: #92400e;
}

.message-time {
  color: #6b7280;
}

.message-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.message-text {
  flex: 1;
  color: #374151;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s;
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
  
  .message-content {
    flex-direction: column;
  }
  
  .message-actions {
    opacity: 1;
    justify-content: flex-end;
  }
  
  .message-modal {
    width: 95%;
    margin: 1rem;
  }
}
</style>