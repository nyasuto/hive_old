<template>
  <g class="communication-line">
    <!-- メインライン -->
    <line
      :x1="sourcePosition.x"
      :y1="sourcePosition.y"
      :x2="targetPosition.x"
      :y2="targetPosition.y"
      :stroke="lineColor"
      :stroke-width="lineWidth"
      stroke-opacity="0.3"
      class="base-line"
    />
    
    <!-- アニメーション用ライン -->
    <line
      :x1="sourcePosition.x"
      :y1="sourcePosition.y"
      :x2="targetPosition.x"
      :y2="targetPosition.y"
      :stroke="lineColor"
      :stroke-width="lineWidth + 1"
      stroke-opacity="0.8"
      stroke-linecap="round"
      class="animated-line"
    >
      <animate
        attributeName="stroke-dasharray"
        :values="`0,${lineLength};${lineLength},0`"
        :dur="`${animationDuration}ms`"
        fill="freeze"
      />
    </line>
    
    <!-- メッセージタイプラベル -->
    <g
      v-if="showLabel"
      class="message-label"
    >
      <rect
        :x="labelPosition.x - labelWidth / 2"
        :y="labelPosition.y - 8"
        :width="labelWidth"
        :height="16"
        rx="8"
        :fill="lineColor"
        fill-opacity="0.9"
      />
      <text
        :x="labelPosition.x"
        :y="labelPosition.y + 3"
        text-anchor="middle"
        fill="white"
        font-size="10"
        font-weight="500"
      >
        {{ flow.message_type }}
      </text>
    </g>
    
    <!-- 矢印 -->
    <polygon
      :points="arrowPoints"
      :fill="lineColor"
      class="arrow-head"
    >
      <animateTransform
        attributeName="transform"
        type="translate"
        :values="`${sourcePosition.x},${sourcePosition.y};${targetPosition.x},${targetPosition.y}`"
        :dur="`${animationDuration}ms`"
        fill="freeze"
      />
    </polygon>
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CommunicationFlow, WorkerPosition } from '@/types'

interface Props {
  flow: CommunicationFlow
  sourcePosition: WorkerPosition
  targetPosition: WorkerPosition
  animationSpeed: number
  showLabel?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showLabel: true
})

const lineLength = computed(() => {
  const dx = props.targetPosition.x - props.sourcePosition.x
  const dy = props.targetPosition.y - props.sourcePosition.y
  return Math.sqrt(dx * dx + dy * dy)
})

const lineColor = computed(() => {
  const colors: Record<string, string> = {
    'task_assignment': '#3b82f6',
    'task_result': '#10b981',
    'coordination': '#8b5cf6',
    'status_update': '#f59e0b',
    'error': '#ef4444',
    'default': '#6b7280'
  }
  return colors[props.flow.message_type] || colors.default
})

const lineWidth = computed(() => {
  const widths: Record<string, number> = {
    'task_assignment': 3,
    'task_result': 3,
    'coordination': 2,
    'status_update': 2,
    'error': 4,
    'default': 2
  }
  return widths[props.flow.message_type] || widths.default
})

const animationDuration = computed(() => {
  return 2000 / props.animationSpeed
})

const labelPosition = computed(() => {
  return {
    x: (props.sourcePosition.x + props.targetPosition.x) / 2,
    y: (props.sourcePosition.y + props.targetPosition.y) / 2
  }
})

const labelWidth = computed(() => {
  return Math.max(60, props.flow.message_type.length * 6)
})

// 矢印の座標計算
const arrowPoints = computed(() => {
  const angle = Math.atan2(
    props.targetPosition.y - props.sourcePosition.y,
    props.targetPosition.x - props.sourcePosition.x
  )
  
  const arrowLength = 8
  
  // 矢印の先端は target position から少し手前
  const tipX = props.targetPosition.x - Math.cos(angle) * 25
  const tipY = props.targetPosition.y - Math.sin(angle) * 25
  
  const leftX = tipX - Math.cos(angle - Math.PI / 6) * arrowLength
  const leftY = tipY - Math.sin(angle - Math.PI / 6) * arrowLength
  
  const rightX = tipX - Math.cos(angle + Math.PI / 6) * arrowLength
  const rightY = tipY - Math.sin(angle + Math.PI / 6) * arrowLength
  
  return `${tipX},${tipY} ${leftX},${leftY} ${rightX},${rightY}`
})
</script>

<style scoped>
.communication-line {
  pointer-events: none;
}

.base-line {
  stroke-dasharray: 5,5;
  animation: dash 1s linear infinite;
}

.animated-line {
  filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.3));
}

.message-label {
  animation: fadeIn 0.5s ease;
}

.arrow-head {
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

@keyframes dash {
  to {
    stroke-dashoffset: -10;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>