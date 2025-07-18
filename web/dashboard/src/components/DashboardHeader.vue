<template>
  <header class="dashboard-header">
    <div class="header-left">
      <div class="logo-section">
        <h1 class="app-title">
          🐝 Hive Dashboard
        </h1>
        <div class="version-badge">
          v2.0 TypeScript
        </div>
      </div>
      
      <nav class="nav-tabs">
        <router-link
          to="/"
          class="nav-tab"
        >
          📊 Dashboard
        </router-link>
        <router-link
          to="/conversations"
          class="nav-tab"
        >
          💬 Conversations
        </router-link>
        <router-link
          to="/command"
          class="nav-tab"
        >
          🎯 Commands
        </router-link>
      </nav>
      
      <div
        class="connection-status"
        :class="connectionStatus.isConnected ? 'connected' : 'disconnected'"
      >
        <div class="status-indicator" />
        <span class="status-text">
          {{ connectionStatus.isConnected ? '接続中' : '切断中' }}
        </span>
        <span
          v-if="connectionStatus.reconnectAttempts > 0"
          class="reconnect-info"
        >
          (再接続試行: {{ connectionStatus.reconnectAttempts }})
        </span>
      </div>
    </div>
    
    <div class="header-center">
      <div class="workers-summary">
        <div class="summary-item">
          <span class="summary-label">総ワーカー:</span>
          <span class="summary-value">{{ totalWorkers }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">アクティブ:</span>
          <span class="summary-value active">{{ activeWorkers }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">稼働時間:</span>
          <span class="summary-value">{{ uptime }}</span>
        </div>
      </div>
    </div>
    
    <div class="header-right">
      <div class="header-controls">
        <button 
          class="control-btn"
          :disabled="!connectionStatus.isConnected"
          title="更新"
          @click="onRefresh"
        >
          🔄 Refresh
        </button>
        
        <button 
          class="control-btn"
          title="デバッグモード切替"
          @click="toggleDebug"
        >
          🐛 Debug
        </button>
        
        <button 
          class="control-btn settings-btn"
          title="設定"
          @click="toggleSettings"
        >
          ⚙️ Settings
        </button>
      </div>
      
      <div class="current-time">
        {{ currentTime }}
      </div>
    </div>
    
    <!-- 設定パネル -->
    <div
      v-if="showSettings"
      class="settings-panel"
    >
      <div class="settings-header">
        <h3>⚙️ Settings</h3>
        <button
          class="close-btn"
          @click="toggleSettings"
        >
          ✕
        </button>
      </div>
      <div class="settings-content">
        <div class="setting-group">
          <label class="setting-label">
            <input 
              v-model="settings.autoRefresh" 
              type="checkbox"
              @change="saveSettings"
            >
            自動更新を有効にする
          </label>
        </div>
        
        <div class="setting-group">
          <label class="setting-label">更新間隔 (秒)</label>
          <input 
            v-model.number="settings.refreshInterval" 
            type="number" 
            min="1" 
            max="60"
            class="setting-input"
            @change="saveSettings"
          >
        </div>
        
        <div class="setting-group">
          <label class="setting-label">
            <input 
              v-model="settings.showNotifications" 
              type="checkbox"
              @change="saveSettings"
            >
            通知を表示する
          </label>
        </div>
        
        <div class="setting-group">
          <label class="setting-label">
            <input 
              v-model="settings.darkMode" 
              type="checkbox"
              @change="saveSettings"
            >
            ダークモード (未実装)
          </label>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { ConnectionStatus } from '@/types'

interface Props {
  connectionStatus: ConnectionStatus
  activeWorkers: number
  totalWorkers: number
}

interface Emits {
  (_e: 'refresh'): void
  (_e: 'toggle-debug'): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const currentTime = ref('')
const showSettings = ref(false)
const startTime = ref(Date.now())

const settings = ref({
  autoRefresh: true,
  refreshInterval: 30,
  showNotifications: true,
  darkMode: false,
})

let timeInterval: number | null = null

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

const updateCurrentTime = () => {
  currentTime.value = new Date().toLocaleTimeString('ja-JP')
}

const onRefresh = () => {
  emit('refresh')
}

const toggleDebug = () => {
  emit('toggle-debug')
}

const toggleSettings = () => {
  showSettings.value = !showSettings.value
}

const saveSettings = () => {
  localStorage.setItem('hive-dashboard-settings', JSON.stringify(settings.value))
}

const loadSettings = () => {
  const savedSettings = localStorage.getItem('hive-dashboard-settings')
  if (savedSettings) {
    try {
      settings.value = { ...settings.value, ...JSON.parse(savedSettings) }
    } catch (error) {
      console.warn('Failed to load settings:', error)
    }
  }
}

onMounted(() => {
  updateCurrentTime()
  timeInterval = window.setInterval(updateCurrentTime, 1000)
  loadSettings()
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.dashboard-header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 12px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  position: relative;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
}

.version-badge {
  background: #3b82f6;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
}

.connection-status.connected {
  color: #059669;
}

.connection-status.disconnected {
  color: #dc2626;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.connection-status.connected .status-indicator {
  background: #10b981;
}

.connection-status.disconnected .status-indicator {
  background: #ef4444;
}

.reconnect-info {
  font-size: 12px;
  opacity: 0.7;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.workers-summary {
  display: flex;
  gap: 24px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.summary-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 2px;
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.summary-value.active {
  color: #059669;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-controls {
  display: flex;
  gap: 8px;
}

.control-btn {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  color: #374151;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control-btn:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.settings-btn {
  background: #f8fafc;
}

.current-time {
  font-family: monospace;
  font-size: 14px;
  color: #64748b;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 4px;
}

.settings-panel {
  position: absolute;
  top: 100%;
  right: 20px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  min-width: 300px;
}

.settings-header {
  padding: 12px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-header h3 {
  margin: 0;
  font-size: 16px;
  color: #1e293b;
}

.close-btn {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: #64748b;
  padding: 0;
}

.settings-content {
  padding: 16px;
}

.setting-group {
  margin-bottom: 16px;
}

.setting-group:last-child {
  margin-bottom: 0;
}

.setting-label {
  display: block;
  font-size: 14px;
  color: #374151;
  margin-bottom: 4px;
  cursor: pointer;
}

.setting-label input[type="checkbox"] {
  margin-right: 8px;
}

.setting-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
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
  .workers-summary {
    gap: 16px;
  }
  
  .summary-item {
    font-size: 12px;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .header-left,
  .header-center,
  .header-right {
    justify-content: center;
  }
  
  .workers-summary {
    gap: 12px;
  }
  
  .header-controls {
    justify-content: center;
  }
  
  .control-btn {
    font-size: 12px;
    padding: 6px 10px;
  }
  
  .settings-panel {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    right: auto;
    width: 90%;
    max-width: 400px;
  }
}

/* Navigation tabs */
.nav-tabs {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.nav-tab {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  text-decoration: none;
  color: #64748b;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.nav-tab:hover {
  background: #f1f5f9;
  color: #334155;
}

.nav-tab.router-link-active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

@media (max-width: 768px) {
  .header-left {
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
  
  .nav-tabs {
    justify-content: center;
  }
}
</style>