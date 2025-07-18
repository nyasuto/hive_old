<template>
  <header class="unified-header">
    <!-- 左側: ロゴ・ナビゲーション・接続状態 -->
    <div class="header-left">
      <div class="logo-section">
        <h1 class="app-title">
          🐝 Hive
        </h1>
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
        v-if="showConnectionStatus"
        class="connection-status"
        :class="connectionStatus?.isConnected ? 'connected' : 'disconnected'"
      >
        <div class="status-indicator" />
        <span class="status-text">
          {{ connectionStatus?.isConnected ? '接続中' : '切断中' }}
        </span>
        <span
          v-if="connectionStatus?.reconnectAttempts && connectionStatus.reconnectAttempts > 0"
          class="reconnect-info"
        >
          (再接続試行: {{ connectionStatus.reconnectAttempts }})
        </span>
      </div>
    </div>
    
    <!-- 中央: ページ固有コンテンツ（スロット） -->
    <div class="header-center">
      <slot name="center" />
    </div>
    
    <!-- 右側: コントロール・時刻 -->
    <div class="header-right">
      <div class="header-controls">
        <!-- ページ固有ボタン（スロット） -->
        <slot name="controls" />
        
        <!-- 共通コントロール -->
        <button 
          v-if="showRefresh"
          class="control-btn"
          :disabled="!connectionStatus?.isConnected"
          title="更新"
          @click="$emit('refresh')"
        >
          🔄 Refresh
        </button>
        
        <button 
          v-if="showDebug"
          class="control-btn"
          title="デバッグモード切替"
          @click="$emit('toggle-debug')"
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
import { ref, onMounted, onUnmounted } from 'vue'
import type { ConnectionStatus } from '@/types'

interface Props {
  connectionStatus?: ConnectionStatus
  showConnectionStatus?: boolean
  showRefresh?: boolean
  showDebug?: boolean
}

interface Emits {
  (_e: 'refresh'): void
  (_e: 'toggle-debug'): void
}

withDefaults(defineProps<Props>(), {
  connectionStatus: () => ({
    isConnected: false,
    reconnectAttempts: 0
  }),
  showConnectionStatus: true,
  showRefresh: true,
  showDebug: true
})

defineEmits<Emits>()

const currentTime = ref('')
const showSettings = ref(false)

const settings = ref({
  autoRefresh: true,
  refreshInterval: 30,
  showNotifications: true,
  darkMode: false,
})

let timeInterval: number | null = null

const updateCurrentTime = () => {
  currentTime.value = new Date().toLocaleTimeString('ja-JP')
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
.unified-header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 0.75rem 1.25rem;
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
  gap: 1rem;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.app-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
}

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
  font-size: 0.875rem;
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

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.connection-status.connected {
  color: #059669;
}

.connection-status.disconnected {
  color: #dc2626;
}

.status-indicator {
  width: 0.5rem;
  height: 0.5rem;
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
  font-size: 0.75rem;
  opacity: 0.7;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-controls {
  display: flex;
  gap: 0.5rem;
}

.control-btn {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  color: #374151;
  font-size: 0.875rem;
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
  font-size: 0.875rem;
  color: #64748b;
  background: #f1f5f9;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.settings-panel {
  position: absolute;
  top: 100%;
  right: 1.25rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  min-width: 300px;
}

.settings-header {
  padding: 0.75rem 1rem;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #1e293b;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  color: #64748b;
  padding: 0;
}

.settings-content {
  padding: 1rem;
}

.setting-group {
  margin-bottom: 1rem;
}

.setting-group:last-child {
  margin-bottom: 0;
}

.setting-label {
  display: block;
  font-size: 0.875rem;
  color: #374151;
  margin-bottom: 0.25rem;
  cursor: pointer;
}

.setting-label input[type="checkbox"] {
  margin-right: 0.5rem;
}

.setting-input {
  width: 100%;
  padding: 0.375rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  font-size: 0.875rem;
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
  .nav-tabs {
    gap: 0.25rem;
  }
}

@media (max-width: 768px) {
  .unified-header {
    flex-direction: column;
    gap: 0.75rem;
    align-items: stretch;
  }
  
  .header-left,
  .header-center,
  .header-right {
    justify-content: center;
  }
  
  .header-left {
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }
  
  .nav-tabs {
    justify-content: center;
  }
  
  .header-controls {
    justify-content: center;
  }
  
  .control-btn {
    font-size: 0.75rem;
    padding: 0.375rem 0.625rem;
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
</style>