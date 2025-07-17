<template>
  <div class="workers-sidebar">
    <div class="sidebar-header">
      <h2 class="sidebar-title">
        🐝 Workers
        <span class="worker-count">({{ workers.length }})</span>
      </h2>
      
      <div class="status-summary">
        <div class="status-item active">
          <span class="status-dot"></span>
          <span>{{ activeCount }}</span>
        </div>
        <div class="status-item working">
          <span class="status-dot"></span>
          <span>{{ workingCount }}</span>
        </div>
        <div class="status-item idle">
          <span class="status-dot"></span>
          <span>{{ idleCount }}</span>
        </div>
        <div class="status-item inactive">
          <span class="status-dot"></span>
          <span>{{ inactiveCount }}</span>
        </div>
      </div>
    </div>
    
    <div class="workers-list">
      <WorkerCard
        v-for="worker in sortedWorkers"
        :key="worker.name"
        :worker="worker"
        @click="onWorkerClick"
      />
    </div>
    
    <div v-if="workers.length === 0" class="empty-state">
      <div class="empty-icon">🏭</div>
      <p class="empty-text">ワーカーが見つかりません</p>
      <p class="empty-subtext">システムが起動中です...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import WorkerCard from './WorkerCard.vue'
import type { Worker } from '@/types'

interface Props {
  workers: Worker[]
}

interface Emits {
  (e: 'worker-click', worker: Worker): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const sortedWorkers = computed(() => {
  return [...props.workers].sort((a, b) => {
    // ステータス順でソート (active > working > idle > inactive)
    const statusPriority = { active: 4, working: 3, idle: 2, inactive: 1 }
    const priorityA = statusPriority[a.status] || 0
    const priorityB = statusPriority[b.status] || 0
    
    if (priorityA !== priorityB) {
      return priorityB - priorityA
    }
    
    // 同じステータスの場合は名前順
    return a.name.localeCompare(b.name)
  })
})

const activeCount = computed(() => 
  props.workers.filter(w => w.status === 'active').length
)

const workingCount = computed(() =>
  props.workers.filter(w => w.status === 'working').length
)

const idleCount = computed(() =>
  props.workers.filter(w => w.status === 'idle').length
)

const inactiveCount = computed(() =>
  props.workers.filter(w => w.status === 'inactive').length
)

const onWorkerClick = (worker: Worker) => {
  emit('worker-click', worker)
}
</script>

<style scoped>
.workers-sidebar {
  width: 320px;
  height: 100vh;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 20px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.sidebar-title {
  margin: 0 0 16px 0;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}

.worker-count {
  font-size: 16px;
  font-weight: 500;
  color: #64748b;
}

.status-summary {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-item.active .status-dot {
  background: #10b981;
}

.status-item.working .status-dot {
  background: #3b82f6;
}

.status-item.idle .status-dot {
  background: #f59e0b;
}

.status-item.inactive .status-dot {
  background: #ef4444;
}

.workers-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.workers-list::-webkit-scrollbar {
  width: 6px;
}

.workers-list::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.workers-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.workers-list::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  text-align: center;
  color: #64748b;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.empty-subtext {
  font-size: 14px;
  opacity: 0.7;
}

@media (max-width: 768px) {
  .workers-sidebar {
    width: 100%;
    height: auto;
    max-height: 40vh;
  }
  
  .status-summary {
    justify-content: space-between;
  }
  
  .status-item {
    font-size: 12px;
  }
}
</style>