<template>
  <div class="performance-panel">
    <div class="panel-header">
      <h2 class="panel-title">
        📊 Performance Metrics
      </h2>
      
      <div class="time-range-selector">
        <select
          v-model="selectedTimeRange"
          @change="updateTimeRange"
        >
          <option value="5m">
            5分
          </option>
          <option value="15m">
            15分
          </option>
          <option value="1h">
            1時間
          </option>
          <option value="24h">
            24時間
          </option>
        </select>
      </div>
    </div>
    
    <div class="panel-content">
      <!-- メトリクス概要 -->
      <div class="metrics-overview">
        <div class="metric-card">
          <div class="metric-icon">
            ⚡
          </div>
          <div class="metric-info">
            <div class="metric-label">
              成功率
            </div>
            <div
              class="metric-value"
              :class="getSuccessRateClass(metrics?.success_rate)"
            >
              {{ formatPercentage(metrics?.success_rate) }}
            </div>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon">
            🚀
          </div>
          <div class="metric-info">
            <div class="metric-label">
              平均応答時間
            </div>
            <div class="metric-value">
              {{ formatResponseTime(metrics?.avg_response_time) }}
            </div>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon">
            📋
          </div>
          <div class="metric-info">
            <div class="metric-label">
              完了タスク
            </div>
            <div class="metric-value">
              {{ metrics?.completed_tasks || 0 }} / {{ metrics?.total_tasks || 0 }}
            </div>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon">
            👥
          </div>
          <div class="metric-info">
            <div class="metric-label">
              アクティブワーカー
            </div>
            <div class="metric-value">
              {{ metrics?.active_workers || 0 }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- セッション情報 -->
      <div
        v-if="session"
        class="session-info"
      >
        <h3 class="section-title">
          🎯 Current Session
        </h3>
        <div class="session-details">
          <div class="session-item">
            <span class="session-label">セッションID:</span>
            <span class="session-value">{{ session.id }}</span>
          </div>
          <div class="session-item">
            <span class="session-label">開始時刻:</span>
            <span class="session-value">{{ formatTime(session.start_time) }}</span>
          </div>
          <div class="session-item">
            <span class="session-label">継続時間:</span>
            <span class="session-value">{{ formatDuration(session.duration) }}</span>
          </div>
          <div class="session-item">
            <span class="session-label">ステータス:</span>
            <span
              class="session-value"
              :class="session.status"
            >
              {{ getStatusLabel(session.status) }}
            </span>
          </div>
          <div class="session-item">
            <span class="session-label">総メッセージ:</span>
            <span class="session-value">{{ session.total_messages }}</span>
          </div>
          <div class="session-item">
            <span class="session-label">参加ワーカー:</span>
            <span class="session-value">{{ session.total_workers }}</span>
          </div>
        </div>
      </div>
      
      <!-- リソース使用状況 -->
      <div
        v-if="metrics?.memory_usage"
        class="resource-usage"
      >
        <h3 class="section-title">
          💾 Resource Usage
        </h3>
        
        <div class="resource-item">
          <div class="resource-header">
            <span class="resource-label">メモリ使用量</span>
            <span class="resource-value">
              {{ formatBytes(metrics.memory_usage.used) }} / {{ formatBytes(metrics.memory_usage.total) }}
              ({{ metrics.memory_usage.percentage.toFixed(1) }}%)
            </span>
          </div>
          <div class="progress-bar">
            <div 
              class="progress-fill"
              :style="{ width: `${metrics.memory_usage.percentage}%` }"
              :class="getMemoryUsageClass(metrics.memory_usage.percentage)"
            />
          </div>
        </div>
        
        <div
          v-if="metrics.cpu_usage"
          class="resource-item"
        >
          <div class="resource-header">
            <span class="resource-label">CPU使用率</span>
            <span class="resource-value">{{ metrics.cpu_usage.toFixed(1) }}%</span>
          </div>
          <div class="progress-bar">
            <div 
              class="progress-fill"
              :style="{ width: `${metrics.cpu_usage}%` }"
              :class="getCpuUsageClass(metrics.cpu_usage)"
            />
          </div>
        </div>
      </div>
      
      <!-- パフォーマンス履歴チャート (簡易版) -->
      <div class="performance-chart">
        <h3 class="section-title">
          📈 Performance Trend
        </h3>
        <div class="chart-placeholder">
          <div class="chart-message">
            📊 チャート機能は将来のアップデートで実装予定です
          </div>
          <div class="chart-mock">
            <div
              v-for="i in 12"
              :key="i"
              class="chart-bar"
              :style="{ height: `${Math.random() * 60 + 10}%` }"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { PerformanceMetrics, Session } from '@/types'

interface Props {
  metrics?: PerformanceMetrics
  session?: Session
}

defineProps<Props>()

const selectedTimeRange = ref('15m')

const updateTimeRange = () => {
  // 時間範囲変更の処理（将来実装）
  console.log('Time range changed to:', selectedTimeRange.value)
}

const formatPercentage = (value?: number): string => {
  if (value === undefined) return '--'
  return `${Math.round(value * 100)}%`
}

const formatResponseTime = (time?: number): string => {
  if (time === undefined) return '--'
  if (time < 1000) {
    return `${Math.round(time)}ms`
  }
  return `${(time / 1000).toFixed(1)}s`
}

const formatTime = (timestamp: string): string => {
  try {
    return new Date(timestamp).toLocaleString('ja-JP')
  } catch {
    return timestamp
  }
}

const formatDuration = (duration: number): string => {
  const hours = Math.floor(duration / 3600)
  const minutes = Math.floor((duration % 3600) / 60)
  const seconds = duration % 60
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  } else {
    return `${seconds}s`
  }
}

const formatBytes = (bytes: number): string => {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)}MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(1)}GB`
}

const getSuccessRateClass = (rate?: number): string => {
  if (!rate) return ''
  if (rate >= 0.9) return 'excellent'
  if (rate >= 0.8) return 'good'
  if (rate >= 0.7) return 'fair'
  return 'poor'
}

const getMemoryUsageClass = (percentage: number): string => {
  if (percentage >= 90) return 'critical'
  if (percentage >= 75) return 'warning'
  return 'normal'
}

const getCpuUsageClass = (percentage: number): string => {
  if (percentage >= 90) return 'critical'
  if (percentage >= 75) return 'warning'
  return 'normal'
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    active: 'アクティブ',
    paused: '一時停止',
    completed: '完了'
  }
  return labels[status] || status
}
</script>

<style scoped>
.performance-panel {
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

.time-range-selector select {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.panel-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.metrics-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid #e2e8f0;
}

.metric-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 8px;
}

.metric-info {
  flex: 1;
}

.metric-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.metric-value.excellent {
  color: #059669;
}

.metric-value.good {
  color: #0891b2;
}

.metric-value.fair {
  color: #d97706;
}

.metric-value.poor {
  color: #dc2626;
}

.session-info,
.resource-usage,
.performance-chart {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 12px 0;
}

.session-details {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.session-item:last-child {
  margin-bottom: 0;
}

.session-label {
  color: #64748b;
  font-weight: 500;
}

.session-value {
  color: #1e293b;
  font-weight: 600;
}

.session-value.active {
  color: #059669;
}

.session-value.paused {
  color: #d97706;
}

.session-value.completed {
  color: #0891b2;
}

.resource-item {
  margin-bottom: 16px;
}

.resource-item:last-child {
  margin-bottom: 0;
}

.resource-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.resource-label {
  color: #64748b;
  font-weight: 500;
}

.resource-value {
  color: #1e293b;
  font-weight: 600;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-fill.normal {
  background: #10b981;
}

.progress-fill.warning {
  background: #f59e0b;
}

.progress-fill.critical {
  background: #ef4444;
}

.chart-placeholder {
  background: #f8fafc;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  border: 1px solid #e2e8f0;
}

.chart-message {
  color: #64748b;
  font-size: 14px;
  margin-bottom: 16px;
}

.chart-mock {
  display: flex;
  align-items: end;
  justify-content: space-between;
  height: 80px;
  gap: 4px;
}

.chart-bar {
  background: #3b82f6;
  opacity: 0.7;
  border-radius: 2px;
  flex: 1;
  animation: chartBarGrow 1s ease;
}

@keyframes chartBarGrow {
  from {
    height: 0;
  }
}

@media (max-width: 768px) {
  .metrics-overview {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .metric-card {
    padding: 12px;
  }
  
  .metric-icon {
    font-size: 20px;
    width: 32px;
    height: 32px;
  }
  
  .metric-value {
    font-size: 16px;
  }
  
  .session-item {
    flex-direction: column;
    align-items: stretch;
    gap: 4px;
  }
  
  .panel-content {
    padding: 16px;
  }
}
</style>