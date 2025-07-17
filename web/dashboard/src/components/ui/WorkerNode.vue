<template>
  <g 
    class="worker-node"
    :class="[worker.status, { highlighted: isHighlighted }]"
    @click="onClick"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
  >
    <!-- ノードの影 -->
    <circle
      :cx="position.x + 2"
      :cy="position.y + 2"
      :r="nodeRadius"
      fill="rgba(0, 0, 0, 0.1)"
    />
    
    <!-- メインノード -->
    <circle
      :cx="position.x"
      :cy="position.y"
      :r="nodeRadius"
      :fill="nodeColor"
      :stroke="strokeColor"
      :stroke-width="strokeWidth"
      class="node-circle"
    />
    
    <!-- ステータスインジケーター -->
    <circle
      :cx="position.x + nodeRadius - 8"
      :cy="position.y - nodeRadius + 8"
      r="6"
      :fill="statusColor"
      :stroke="statusStrokeColor"
      stroke-width="2"
      class="status-indicator"
    >
      <animate
        v-if="worker.status === 'working'"
        attributeName="r"
        values="4;8;4"
        dur="2s"
        repeatCount="indefinite"
      />
    </circle>
    
    <!-- ワーカー絵文字 -->
    <text
      :x="position.x"
      :y="position.y + 6"
      text-anchor="middle"
      :font-size="emojiSize"
      class="worker-emoji"
    >
      {{ worker.emoji }}
    </text>
    
    <!-- ワーカー名（ホバー時表示） -->
    <g v-if="isHovered" class="worker-label">
      <rect
        :x="position.x - labelWidth / 2"
        :y="position.y + nodeRadius + 8"
        :width="labelWidth"
        :height="24"
        rx="4"
        fill="rgba(0, 0, 0, 0.8)"
      />
      <text
        :x="position.x"
        :y="position.y + nodeRadius + 22"
        text-anchor="middle"
        fill="white"
        font-size="12"
        font-weight="500"
      >
        {{ worker.name }}
      </text>
    </g>
    
    <!-- タスクアイコン（current_taskがある場合） -->
    <g v-if="worker.current_task" class="task-indicator">
      <circle
        :cx="position.x - nodeRadius + 8"
        :cy="position.y - nodeRadius + 8"
        r="8"
        fill="#3b82f6"
        stroke="white"
        stroke-width="2"
      />
      <text
        :x="position.x - nodeRadius + 8"
        :y="position.y - nodeRadius + 12"
        text-anchor="middle"
        fill="white"
        font-size="10"
        font-weight="bold"
      >
        ⚡
      </text>
    </g>
    
    <!-- パフォーマンス表示（highlighted時） -->
    <g v-if="isHighlighted && worker.performance" class="performance-display">
      <rect
        :x="position.x - 60"
        :y="position.y - nodeRadius - 60"
        width="120"
        height="40"
        rx="6"
        fill="rgba(255, 255, 255, 0.95)"
        stroke="#e2e8f0"
        stroke-width="1"
      />
      <text
        :x="position.x"
        :y="position.y - nodeRadius - 45"
        text-anchor="middle"
        font-size="10"
        fill="#374151"
      >
        Tasks: {{ worker.performance.tasks_completed }}
      </text>
      <text
        :x="position.x"
        :y="position.y - nodeRadius - 32"
        text-anchor="middle"
        font-size="10"
        fill="#374151"
      >
        Success: {{ Math.round(worker.performance.success_rate * 100) }}%
      </text>
    </g>
  </g>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Worker, WorkerPosition } from '@/types'

interface Props {
  worker: Worker
  position: WorkerPosition
  isHighlighted?: boolean
}

interface Emits {
  (e: 'click', worker: Worker): void
  (e: 'hover', workerName: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const isHovered = ref(false)

const nodeRadius = computed(() => {
  return props.isHighlighted ? 35 : 30
})

const emojiSize = computed(() => {
  return props.isHighlighted ? 24 : 20
})

const labelWidth = computed(() => {
  return Math.max(80, props.worker.name.length * 8)
})

const nodeColor = computed(() => {
  const colors = {
    active: '#ecfdf5',
    working: '#eff6ff',
    idle: '#fffbeb',
    inactive: '#fef2f2'
  }
  return colors[props.worker.status] || '#f9fafb'
})

const strokeColor = computed(() => {
  const colors = {
    active: '#10b981',
    working: '#3b82f6',
    idle: '#f59e0b',
    inactive: '#ef4444'
  }
  return colors[props.worker.status] || '#9ca3af'
})

const strokeWidth = computed(() => {
  return props.isHighlighted ? 4 : 2
})

const statusColor = computed(() => {
  const colors = {
    active: '#10b981',
    working: '#3b82f6',
    idle: '#f59e0b',
    inactive: '#ef4444'
  }
  return colors[props.worker.status] || '#9ca3af'
})

const statusStrokeColor = computed(() => {
  return props.worker.status === 'working' ? 'white' : statusColor.value
})

const onClick = () => {
  emit('click', props.worker)
}

const onMouseEnter = () => {
  isHovered.value = true
  emit('hover', props.worker.name)
}

const onMouseLeave = () => {
  isHovered.value = false
}
</script>

<style scoped>
.worker-node {
  cursor: pointer;
  transition: all 0.2s ease;
}

.worker-node:hover .node-circle {
  filter: brightness(1.1);
}

.worker-node.highlighted .node-circle {
  filter: drop-shadow(0 0 10px rgba(59, 130, 246, 0.5));
}

.worker-emoji {
  pointer-events: none;
  user-select: none;
}

.status-indicator {
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
}

.worker-label {
  pointer-events: none;
  animation: fadeIn 0.2s ease;
}

.task-indicator {
  animation: pulse 2s infinite;
}

.performance-display {
  pointer-events: none;
  animation: slideDown 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>