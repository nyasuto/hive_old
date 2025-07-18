<template>
  <div class="communication-flow">
    <div class="flow-header">
      <h2 class="flow-title">
        📡 Communication Flow
      </h2>
      
      <div class="flow-controls">
        <button 
          class="control-btn"
          :class="{ active: isPlaying }"
          @click="togglePlayPause"
        >
          {{ isPlaying ? '⏸️ Pause' : '▶️ Play' }}
        </button>
        
        <button 
          class="control-btn"
          @click="clearFlow"
        >
          🗑️ Clear
        </button>
        
        <select 
          v-model="animationSpeed" 
          class="speed-select"
          @change="updateAnimationSpeed"
        >
          <option value="0.5">
            0.5x
          </option>
          <option value="1">
            1x
          </option>
          <option value="2">
            2x
          </option>
          <option value="5">
            5x
          </option>
        </select>
        
        <button 
          class="control-btn"
          @click="toggleFullscreen"
        >
          🔍 {{ isFullscreen ? 'Exit' : 'Expand' }}
        </button>
      </div>
    </div>
    
    <div 
      ref="flowContainer"
      class="flow-container"
      :class="{ fullscreen: isFullscreen }"
    >
      <svg
        ref="flowCanvas"
        class="flow-canvas"
        :viewBox="`0 0 ${config.canvasWidth} ${config.canvasHeight}`"
      >
        <!-- 背景グリッド -->
        <defs>
          <pattern
            id="grid"
            width="50"
            height="50"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 50 0 L 0 0 0 50"
              fill="none"
              stroke="#e2e8f0"
              stroke-width="1"
              opacity="0.3"
            />
          </pattern>
        </defs>
        <rect
          width="100%"
          height="100%"
          fill="url(#grid)"
        />
        
        <!-- ワーカーノード -->
        <WorkerNode
          v-for="worker in workers"
          :key="worker.name"
          :worker="worker"
          :position="getWorkerPosition(worker.name)"
          :is-highlighted="highlightedWorker === worker.name"
          @click="onWorkerClick"
          @hover="onWorkerHover"
        />
        
        <!-- 通信フロー線 -->
        <CommunicationLine
          v-for="flow in activeFlows"
          :key="flow.id"
          :flow="flow"
          :source-position="getWorkerPosition(flow.source)"
          :target-position="getWorkerPosition(flow.target)"
          :animation-speed="animationSpeed"
        />
      </svg>
      
      <!-- フロー統計 -->
      <div class="flow-stats">
        <div class="stat-item">
          <span class="stat-label">アクティブフロー:</span>
          <span class="stat-value">{{ activeFlows.length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">総メッセージ:</span>
          <span class="stat-value">{{ totalMessages }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">最終更新:</span>
          <span class="stat-value">{{ lastUpdate }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import WorkerNode from './ui/WorkerNode.vue'
import CommunicationLine from './ui/CommunicationLine.vue'
import type { Worker, Message, WorkerPosition, CommunicationFlow as Flow } from '@/types'

interface Props {
  workers: Worker[]
  messages: Message[]
}

const props = defineProps<Props>()

const isPlaying = ref(true)
const animationSpeed = ref(1)
const isFullscreen = ref(false)
const highlightedWorker = ref<string>('')
const flowContainer = ref<HTMLElement>()
const flowCanvas = ref<SVGElement>()

const config = reactive({
  canvasWidth: 800,
  canvasHeight: 400,
  nodeRadius: 30,
  animationDuration: 2000,
  maxActiveFlows: 20,
})

const activeFlows = ref<Flow[]>([])
const flowIdCounter = ref(0)

const totalMessages = computed(() => props.messages.length)

const lastUpdate = computed(() => {
  if (props.messages.length === 0) return '--'
  const latest = props.messages[0]?.timestamp
  if (!latest) return '--'
  
  try {
    return new Date(latest).toLocaleTimeString('ja-JP')
  } catch {
    return '--'
  }
})

// ワーカー位置計算
const getWorkerPosition = (workerName: string): WorkerPosition => {
  const workerPositions: Record<string, WorkerPosition> = {
    beekeeper: { x: 150, y: 200 },
    queen: { x: 400, y: 100 },
    developer: { x: 650, y: 150 },
    researcher: { x: 200, y: 300 },
    coordinator: { x: 500, y: 280 },
    specialist: { x: 600, y: 320 },
  }
  
  // 定義されていないワーカーは動的に配置
  if (!workerPositions[workerName]) {
    const index = props.workers.findIndex(w => w.name === workerName)
    const angle = (index * 2 * Math.PI) / props.workers.length
    const radius = 150
    const centerX = config.canvasWidth / 2
    const centerY = config.canvasHeight / 2
    
    workerPositions[workerName] = {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    }
  }
  
  return workerPositions[workerName] || { x: 0, y: 0 }
}

// 新しいメッセージを監視してフローを作成
watch(
  () => props.messages,
  (newMessages, oldMessages) => {
    if (!isPlaying.value) return
    
    const newMsgCount = newMessages.length - (oldMessages?.length || 0)
    if (newMsgCount <= 0) return
    
    // 新しいメッセージからフローを作成
    const latestMessages = newMessages.slice(0, newMsgCount)
    latestMessages.forEach(message => {
      if (message.source && message.target && message.source !== message.target) {
        addCommunicationFlow({
          id: `flow-${flowIdCounter.value++}`,
          source: message.source,
          target: message.target,
          message_type: message.message_type,
          timestamp: message.timestamp,
          status: 'sending',
        })
      }
    })
  },
  { deep: true }
)

const addCommunicationFlow = (flow: Flow) => {
  activeFlows.value.push(flow)
  
  // 最大フロー数を超えた場合は古いものを削除
  if (activeFlows.value.length > config.maxActiveFlows) {
    activeFlows.value = activeFlows.value.slice(-config.maxActiveFlows)
  }
  
  // 一定時間後にフローを削除
  setTimeout(() => {
    const index = activeFlows.value.findIndex(f => f.id === flow.id)
    if (index !== -1) {
      activeFlows.value.splice(index, 1)
    }
  }, config.animationDuration * animationSpeed.value)
}

const togglePlayPause = () => {
  isPlaying.value = !isPlaying.value
}

const clearFlow = () => {
  activeFlows.value = []
}

const updateAnimationSpeed = () => {
  // アニメーション速度の変更をすべてのフローに適用
  config.animationDuration = 2000 / animationSpeed.value
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  
  if (isFullscreen.value) {
    config.canvasWidth = 1200
    config.canvasHeight = 600
  } else {
    config.canvasWidth = 800
    config.canvasHeight = 400
  }
}

const onWorkerClick = (worker: Worker) => {
  console.log('Worker clicked:', worker.name)
  highlightedWorker.value = highlightedWorker.value === worker.name ? '' : worker.name
}

const onWorkerHover = (workerName: string) => {
  // ホバー時の処理（必要に応じて実装）
  console.log('Worker hovered:', workerName)
}

// レスポンシブ対応
const handleResize = () => {
  if (!isFullscreen.value && flowContainer.value) {
    const rect = flowContainer.value.getBoundingClientRect()
    config.canvasWidth = Math.max(800, rect.width - 40)
    config.canvasHeight = Math.max(400, rect.height - 80)
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.communication-flow {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.flow-header {
  padding: 16px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.flow-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.flow-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.control-btn {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.control-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.control-btn.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.speed-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.flow-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: #fafbfc;
}

.flow-container.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  background: white;
}

.flow-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.flow-stats {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(255, 255, 255, 0.95);
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 14px;
}

.stat-item:last-child {
  margin-bottom: 0;
}

.stat-label {
  color: #6b7280;
  margin-right: 8px;
}

.stat-value {
  font-weight: 600;
  color: #1f2937;
}

@media (max-width: 768px) {
  .flow-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .flow-controls {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .control-btn,
  .speed-select {
    font-size: 12px;
    padding: 6px 10px;
  }
  
  .flow-stats {
    position: static;
    margin: 16px;
    margin-top: 0;
  }
}
</style>