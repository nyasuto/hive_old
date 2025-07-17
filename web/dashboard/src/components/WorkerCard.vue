<template>
  <div 
    class="worker-card" 
    :class="[worker.status, { 'has-task': worker.current_task }]"
    @click="onWorkerClick"
  >
    <div class="worker-header">
      <div class="worker-avatar">{{ worker.emoji }}</div>
      <div class="worker-info">
        <h3 class="worker-name">{{ worker.name }}</h3>
        <span class="worker-status" :class="worker.status">
          {{ statusText }}
        </span>
      </div>
      <div class="worker-status-indicator" :class="worker.status"></div>
    </div>
    
    <div class="worker-details">
      <div v-if="worker.last_activity" class="last-activity">
        <span class="label">最終活動:</span>
        <span class="time">{{ formatTime(worker.last_activity) }}</span>
      </div>
      
      <div v-if="worker.current_task" class="current-task">
        <span class="label">現在のタスク:</span>
        <span class="task">{{ worker.current_task }}</span>
      </div>
      
      <div v-if="worker.performance" class="performance-metrics">
        <div class="metric">
          <span class="metric-label">完了タスク:</span>
          <span class="metric-value">{{ worker.performance.tasks_completed }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">応答時間:</span>
          <span class="metric-value">{{ formatResponseTime(worker.performance.avg_response_time) }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">成功率:</span>
          <span class="metric-value">{{ formatPercentage(worker.performance.success_rate) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Worker } from '@/types'

interface Props {
  worker: Worker
}

interface Emits {
  (e: 'click', worker: Worker): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const statusText = computed(() => {
  const statusMap = {
    active: 'アクティブ',
    idle: 'アイドル',
    working: '作業中',
    inactive: '非アクティブ'
  }
  return statusMap[props.worker.status] || props.worker.status
})

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

const formatResponseTime = (time: number): string => {
  if (time < 1000) {
    return `${Math.round(time)}ms`
  }
  return `${(time / 1000).toFixed(1)}s`
}

const formatPercentage = (rate: number): string => {
  return `${Math.round(rate * 100)}%`
}

const onWorkerClick = () => {
  emit('click', props.worker)
}
</script>

<style scoped>
.worker-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #e5e7eb;
  transition: all 0.2s ease;
  cursor: pointer;
}

.worker-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.worker-card.active {
  border-left-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%);
}

.worker-card.working {
  border-left-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
}

.worker-card.idle {
  border-left-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%);
}

.worker-card.inactive {
  border-left-color: #ef4444;
  background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
}

.worker-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.worker-avatar {
  font-size: 32px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  border: 2px solid rgba(0, 0, 0, 0.1);
}

.worker-info {
  flex: 1;
}

.worker-name {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.worker-status {
  font-size: 14px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.worker-status.active {
  background: #d1fae5;
  color: #065f46;
}

.worker-status.working {
  background: #dbeafe;
  color: #1e40af;
}

.worker-status.idle {
  background: #fef3c7;
  color: #92400e;
}

.worker-status.inactive {
  background: #fee2e2;
  color: #991b1b;
}

.worker-status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.worker-status-indicator.active {
  background: #10b981;
}

.worker-status-indicator.working {
  background: #3b82f6;
}

.worker-status-indicator.idle {
  background: #f59e0b;
}

.worker-status-indicator.inactive {
  background: #ef4444;
}

.worker-details {
  font-size: 14px;
  color: #6b7280;
}

.last-activity,
.current-task {
  margin-bottom: 8px;
}

.label {
  font-weight: 500;
  color: #374151;
}

.time,
.task {
  margin-left: 4px;
  color: #1f2937;
}

.performance-metrics {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 8px;
}

.metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.metric-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 2px;
}

.metric-value {
  font-weight: 600;
  color: #1f2937;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.has-task .worker-card {
  border-left-width: 6px;
}
</style>