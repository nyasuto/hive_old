<template>
  <div class="conversations-page">
    <UnifiedHeader
      :show-connection-status="false"
      :show-refresh="false"
      :show-debug="false"
    >
      <template #center>
        <div class="search-container">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="🔍 Search conversations..."
            class="search-input"
            @input="updateSearchQuery"
          >
        </div>
      </template>
      <template #controls>
        <select
          v-model="timeRange"
          class="time-select"
          @change="updateTimeRange"
        >
          <option value="1h">
            📅 Last 1 hour
          </option>
          <option value="6h">
            📅 Last 6 hours
          </option>
          <option value="24h">
            📅 Last 24 hours
          </option>
          <option value="7d">
            📅 Last 7 days
          </option>
          <option value="30d">
            📅 Last 30 days
          </option>
          <option value="all">
            📅 All time
          </option>
        </select>
      </template>
    </UnifiedHeader>
    
    <div class="conversations-layout">
      <ConversationSidebar 
        :workers="workers"
        :selected-workers="selectedWorkers"
        :messages="messages"
        @update-filters="updateFilters"
      />
      
      <main class="conversation-main">
        <ConversationThread 
          :messages="filteredMessages"
          :loading="loading"
          @load-more="loadMoreMessages"
        />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import UnifiedHeader from '@/components/UnifiedHeader.vue'
import ConversationSidebar from '@/components/conversation/ConversationSidebar.vue'
import ConversationThread from '@/components/conversation/ConversationThread.vue'
import { useWebSocket } from '@/composables/useWebSocket'

interface Worker {
  name: string
  emoji: string
  status: string
}

interface Message {
  id: string
  timestamp: string
  source: string
  target: string
  messageType: string
  message: string
  sessionId?: string
}

interface ConversationFilters {
  workers: string[]
  messageTypes: string[]
  timeRange: string
  searchQuery: string
}

// Reactive state
const workers = ref<Worker[]>([])
const messages = ref<Message[]>([])
const loading = ref(false)
const selectedWorkers = ref<string[]>([])
const timeRange = ref('1h')
const searchQuery = ref('')
const filters = ref<ConversationFilters>({
  workers: [],
  messageTypes: [],
  timeRange: '1h',
  searchQuery: ''
})

// WebSocket connection - ready for future real-time updates
useWebSocket('ws://localhost:8002/ws')

// Computed properties
const filteredMessages = computed(() => {
  let filtered = [...messages.value]
  
  // Filter out system messages (CLI_RESPONSE: Success etc.)
  filtered = filtered.filter(msg => {
    // Hide CLI system response messages
    if (msg.message.startsWith('CLI_RESPONSE:')) {
      return false
    }
    return true
  })
  
  // Filter by time range
  if (filters.value.timeRange !== 'all') {
    const now = new Date()
    const timeRangeMs = getTimeRangeInMs(filters.value.timeRange)
    const cutoffTime = new Date(now.getTime() - timeRangeMs)
    
    filtered = filtered.filter(msg => {
      const messageTime = new Date(msg.timestamp)
      return messageTime >= cutoffTime
    })
  }
  
  // Filter by workers
  if (filters.value.workers.length > 0) {
    filtered = filtered.filter(msg => 
      filters.value.workers.includes(msg.source) || 
      filters.value.workers.includes(msg.target)
    )
  }
  
  // Filter by message types
  if (filters.value.messageTypes.length > 0) {
    filtered = filtered.filter(msg => 
      filters.value.messageTypes.includes(msg.messageType)
    )
  }
  
  // Filter by search query
  if (filters.value.searchQuery) {
    const query = filters.value.searchQuery.toLowerCase()
    filtered = filtered.filter(msg => 
      msg.message.toLowerCase().includes(query) ||
      msg.source.toLowerCase().includes(query) ||
      msg.target.toLowerCase().includes(query)
    )
  }
  
  // Sort by timestamp (newest first)
  return filtered.sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  )
})

// Helper function to convert time range to milliseconds
const getTimeRangeInMs = (timeRange: string): number => {
  switch (timeRange) {
    case '1h':
      return 60 * 60 * 1000 // 1 hour
    case '6h':
      return 6 * 60 * 60 * 1000 // 6 hours
    case '24h':
      return 24 * 60 * 60 * 1000 // 24 hours
    case '7d':
      return 7 * 24 * 60 * 60 * 1000 // 7 days
    default:
      return 0
  }
}

// Methods
const updateFilters = (newFilters: Partial<ConversationFilters>) => {
  filters.value = { ...filters.value, ...newFilters }
}

const updateTimeRange = () => {
  filters.value = { ...filters.value, timeRange: timeRange.value }
}

const updateSearchQuery = () => {
  filters.value = { ...filters.value, searchQuery: searchQuery.value }
}

const loadMoreMessages = async () => {
  loading.value = true
  try {
    // API call to load more messages
    const response = await window.fetch('/api/messages?limit=50&offset=' + messages.value.length)
    const data = await response.json()
    messages.value.push(...data.messages)
  } catch (error) {
    console.error('Failed to load more messages:', error)
  } finally {
    loading.value = false
  }
}

const loadInitialData = async () => {
  loading.value = true
  try {
    // Load workers - use existing API endpoint
    const workersResponse = await window.fetch('http://localhost:8002/api/workers')
    const workersData = await workersResponse.json()
    workers.value = workersData.workers
    
    // Load recent messages - use existing API endpoint
    const messagesResponse = await window.fetch('http://localhost:8002/api/messages?limit=100')
    const messagesData = await messagesResponse.json()
    messages.value = messagesData.messages
  } catch (error) {
    console.error('Failed to load initial data:', error)
    // Fallback with sample data for demonstration
    workers.value = [
      { name: 'queen', emoji: '👑', status: 'active' },
      { name: 'developer', emoji: '👨‍💻', status: 'active' },
      { name: 'tester', emoji: '🧪', status: 'active' },
      { name: 'analyzer', emoji: '🔍', status: 'active' },
      { name: 'documenter', emoji: '📝', status: 'active' },
      { name: 'reviewer', emoji: '👀', status: 'active' },
      { name: 'beekeeper', emoji: '📋', status: 'active' }
    ]
    
    // Generate sample messages for demonstration
    messages.value = [
      {
        id: '1',
        timestamp: new Date().toISOString(),
        source: 'queen',
        target: 'developer',
        messageType: 'direct',
        message: 'Please implement the new authentication system for the user management module.',
        sessionId: 'session_1'
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 60000).toISOString(),
        source: 'developer',
        target: 'queen',
        messageType: 'response',
        message: 'I will start working on the authentication system. I will need about 2 hours to complete the implementation.',
        sessionId: 'session_1'
      },
      {
        id: '3',
        timestamp: new Date(Date.now() - 120000).toISOString(),
        source: 'analyzer',
        target: 'reviewer',
        messageType: 'coordination',
        message: 'I have completed the code analysis. The following issues need to be addressed: 1) Security vulnerabilities in the input validation, 2) Performance bottlenecks in the database queries.',
        sessionId: 'session_2'
      }
    ]
  } finally {
    loading.value = false
  }
}

// Future: WebSocket real-time updates will be integrated here

// Lifecycle
onMounted(() => {
  loadInitialData()
})

// Watch WebSocket data - simplified approach
// Real-time updates will be handled through WebSocket message handling in useWebSocket composable

onUnmounted(() => {
  // Cleanup is handled by useWebSocket composable
})
</script>

<style scoped>
.conversations-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

/* Header Controls Styles */
.search-container {
  display: flex;
  align-items: center;
  max-width: 400px;
  width: 100%;
}

.search-input {
  width: 100%;
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  background: white;
  transition: border-color 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.time-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  color: #374151;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.time-select:hover {
  border-color: #9ca3af;
}

.time-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.conversations-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.conversation-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

@media (max-width: 768px) {
  .conversations-layout {
    flex-direction: column;
  }
}
</style>