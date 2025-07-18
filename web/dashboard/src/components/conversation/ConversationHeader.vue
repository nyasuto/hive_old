<template>
  <header class="conversation-header">
    <div class="header-left">
      <nav class="nav-tabs">
        <router-link
          to="/"
          class="nav-tab"
        >
          📊 Dashboard
        </router-link>
        <router-link
          to="/conversations"
          class="nav-tab active"
        >
          💬 Conversations
        </router-link>
      </nav>
    </div>
    
    <div class="header-center">
      <div class="search-container">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="🔍 Search conversations..."
          class="search-input"
          @input="$emit('search', searchQuery)"
        >
      </div>
    </div>
    
    <div class="header-right">
      <div class="header-controls">
        <select
          v-model="timeRange"
          class="time-select"
          @change="$emit('time-range-change', timeRange)"
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
          <option value="all">
            📅 All time
          </option>
        </select>
        
        <button
          class="control-btn"
          title="Export conversations"
          @click="$emit('export')"
        >
          💾 Export
        </button>
        
        <button
          class="control-btn"
          title="Refresh conversations"
          @click="$emit('refresh')"
        >
          🔄 Refresh
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Emits {
  (_e: 'search', _query: string): void
  (_e: 'time-range-change', _range: string): void
  (_e: 'export'): void
  (_e: 'refresh'): void
}

defineEmits<Emits>()

const searchQuery = ref('')
const timeRange = ref('1h')
</script>

<style scoped>
.conversation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.header-left {
  flex: 1;
}

.nav-tabs {
  display: flex;
  gap: 0.5rem;
}

.nav-tab {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  text-decoration: none;
  color: #64748b;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-tab:hover {
  background: #f1f5f9;
  color: #334155;
}

.nav-tab.active {
  background: #3b82f6;
  color: white;
}

.header-center {
  flex: 2;
  display: flex;
  justify-content: center;
}

.search-container {
  width: 100%;
  max-width: 400px;
}

.search-input {
  width: 100%;
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.header-right {
  flex: 1;
  display: flex;
  justify-content: flex-end;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.time-select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  background: white;
  cursor: pointer;
}

.control-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.control-btn:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.control-btn:active {
  transform: translateY(1px);
}

@media (max-width: 768px) {
  .conversation-header {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }
  
  .header-left,
  .header-center,
  .header-right {
    flex: none;
    width: 100%;
  }
  
  .nav-tabs {
    justify-content: center;
  }
  
  .header-controls {
    justify-content: center;
    flex-wrap: wrap;
  }
}
</style>