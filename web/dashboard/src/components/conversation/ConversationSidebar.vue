<template>
  <aside class="conversation-sidebar">
    <div class="sidebar-header">
      <h3 class="sidebar-title">
        🎯 Filters
      </h3>
      <button
        class="clear-filters-btn"
        @click="clearAllFilters"
      >
        Clear All
      </button>
    </div>
    
    <div class="filter-section">
      <h4 class="filter-title">
        👥 Workers
      </h4>
      <div class="workers-list">
        <label
          v-for="worker in workers"
          :key="worker.name"
          class="worker-checkbox"
        >
          <input
            v-model="selectedWorkers"
            type="checkbox"
            :value="worker.name"
            @change="updateFilters"
          >
          <span class="worker-info">
            <span class="worker-emoji">{{ worker.emoji }}</span>
            <span class="worker-name">{{ worker.name }}</span>
            <span 
              class="worker-status"
              :class="worker.status"
            >
              {{ worker.status }}
            </span>
          </span>
        </label>
      </div>
    </div>
    
    <div class="filter-section">
      <h4 class="filter-title">
        📝 Message Types
      </h4>
      <div class="message-types-list">
        <label
          v-for="type in messageTypes"
          :key="type.value"
          class="type-checkbox"
        >
          <input
            v-model="selectedMessageTypes"
            type="checkbox"
            :value="type.value"
            @change="updateFilters"
          >
          <span class="type-info">
            <span class="type-icon">{{ type.icon }}</span>
            <span class="type-name">{{ type.label }}</span>
            <span class="type-count">{{ type.count }}</span>
          </span>
        </label>
      </div>
    </div>
    
    <div class="filter-section">
      <h4 class="filter-title">
        📊 Statistics
      </h4>
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">Total Messages</span>
          <span class="stat-value">{{ totalMessages }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Active Conversations</span>
          <span class="stat-value">{{ activeConversations }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Most Active Worker</span>
          <span class="stat-value">{{ mostActiveWorker }}</span>
        </div>
      </div>
    </div>
    
    <div class="filter-section">
      <h4 class="filter-title">
        🔍 Quick Filters
      </h4>
      <div class="quick-filters">
        <button
          v-for="filter in quickFilters"
          :key="filter.name"
          class="quick-filter-btn"
          :class="{ active: isQuickFilterActive(filter) }"
          @click="applyQuickFilter(filter)"
        >
          {{ filter.icon }} {{ filter.label }}
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Worker {
  name: string
  emoji: string
  status: string
}

interface MessageType {
  value: string
  label: string
  icon: string
  count: number
}

interface QuickFilter {
  name: string
  label: string
  icon: string
  workers?: string[]
  messageTypes?: string[]
}

interface Props {
  workers: Worker[]
  selectedWorkers: string[]
  messages: Message[]
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

interface Emits {
  (_e: 'update-filters', _filters: {
    workers: string[]
    messageTypes: string[]
  }): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Local state
const selectedWorkers = ref<string[]>([...props.selectedWorkers])
const selectedMessageTypes = ref<string[]>([])

// Message types configuration - matches actual data from API
const messageTypes = ref<MessageType[]>([
  { value: 'direct', label: 'Direct Message', icon: '💬', count: 45 },
  { value: 'response', label: 'Response', icon: '↩️', count: 32 }
])

// Quick filters - updated to match actual data
const quickFilters = ref<QuickFilter[]>([
  {
    name: 'queen-conversations',
    label: 'Queen Conversations',
    icon: '👑',
    workers: ['queen']
  },
  {
    name: 'direct-messages',
    label: 'Direct Messages',
    icon: '💬',
    messageTypes: ['direct']
  },
  {
    name: 'responses',
    label: 'Responses',
    icon: '↩️',
    messageTypes: ['response']
  },
  {
    name: 'all-communications',
    label: 'All Communications',
    icon: '📡',
    messageTypes: ['direct', 'response']
  }
])

// Computed properties
const totalMessages = computed(() => 
  messageTypes.value.reduce((sum, type) => sum + type.count, 0)
)

const activeConversations = computed(() => {
  // Calculate based on unique worker pairs
  return Math.ceil(props.workers.length / 2)
})

const mostActiveWorker = computed(() => {
  // This would be calculated from actual message data
  return props.workers.length > 0 ? props.workers[0].name : 'N/A'
})

// Methods
const updateFilters = () => {
  emit('update-filters', {
    workers: selectedWorkers.value,
    messageTypes: selectedMessageTypes.value
  })
}

const clearAllFilters = () => {
  selectedWorkers.value = []
  selectedMessageTypes.value = []
  updateFilters()
}

const isQuickFilterActive = (filter: QuickFilter) => {
  if (filter.workers) {
    return filter.workers.every(worker => selectedWorkers.value.includes(worker))
  }
  if (filter.messageTypes) {
    return filter.messageTypes.every(type => selectedMessageTypes.value.includes(type))
  }
  return false
}

const applyQuickFilter = (filter: QuickFilter) => {
  if (isQuickFilterActive(filter)) {
    // Remove filter
    if (filter.workers) {
      selectedWorkers.value = selectedWorkers.value.filter(w => !filter.workers!.includes(w))
    }
    if (filter.messageTypes) {
      selectedMessageTypes.value = selectedMessageTypes.value.filter(t => !filter.messageTypes!.includes(t))
    }
  } else {
    // Apply filter
    if (filter.workers) {
      selectedWorkers.value = [...new Set([...selectedWorkers.value, ...filter.workers])]
    }
    if (filter.messageTypes) {
      selectedMessageTypes.value = [...new Set([...selectedMessageTypes.value, ...filter.messageTypes])]
    }
  }
  updateFilters()
}

// Update message counts when messages change
const updateMessageCounts = () => {
  const counts: Record<string, number> = {}
  
  props.messages.forEach(message => {
    counts[message.messageType] = (counts[message.messageType] || 0) + 1
  })
  
  messageTypes.value.forEach(type => {
    type.count = counts[type.value] || 0
  })
}

// Watch for prop changes
watch(() => props.selectedWorkers, (newVal) => {
  selectedWorkers.value = [...newVal]
}, { deep: true })

watch(() => props.messages, () => {
  updateMessageCounts()
}, { deep: true, immediate: true })
</script>

<style scoped>
.conversation-sidebar {
  width: 300px;
  background: white;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.sidebar-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.clear-filters-btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  color: #6b7280;
  background: transparent;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-filters-btn:hover {
  color: #374151;
  border-color: #9ca3af;
}

.filter-section {
  padding: 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.filter-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.75rem 0;
}

.workers-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.worker-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.375rem;
  transition: background-color 0.2s;
}

.worker-checkbox:hover {
  background: #f9fafb;
}

.worker-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.worker-emoji {
  font-size: 1.25rem;
}

.worker-name {
  font-weight: 500;
  color: #374151;
}

.worker-status {
  font-size: 0.75rem;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  text-transform: capitalize;
}

.worker-status.active {
  background: #dcfce7;
  color: #166534;
}

.worker-status.inactive {
  background: #fee2e2;
  color: #991b1b;
}

.message-types-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.type-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.375rem;
  border-radius: 0.25rem;
  transition: background-color 0.2s;
}

.type-checkbox:hover {
  background: #f9fafb;
}

.type-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.type-name {
  font-size: 0.875rem;
  color: #374151;
  flex: 1;
}

.type-count {
  font-size: 0.75rem;
  color: #6b7280;
  background: #f3f4f6;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
}

.stats-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: 0.75rem;
  color: #6b7280;
}

.stat-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.quick-filters {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.quick-filter-btn {
  padding: 0.5rem;
  font-size: 0.75rem;
  text-align: left;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-filter-btn:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.quick-filter-btn.active {
  background: #dbeafe;
  border-color: #3b82f6;
  color: #1d4ed8;
}

@media (max-width: 768px) {
  .conversation-sidebar {
    width: 100%;
    max-height: 300px;
  }
}
</style>