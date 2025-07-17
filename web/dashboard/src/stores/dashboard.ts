import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { DashboardData, Worker, Message } from '@/types'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const data = ref<DashboardData>()
  const isLoading = ref(false)
  const error = ref<string>()
  
  // Getters
  const workers = computed(() => data.value?.workers || [])
  const recentMessages = computed(() => data.value?.recent_messages || [])
  const performanceMetrics = computed(() => data.value?.performance_metrics)
  const currentSession = computed(() => data.value?.current_session)
  
  const activeWorkers = computed(() => 
    workers.value.filter(w => w.status === 'active')
  )
  
  const workingWorkers = computed(() =>
    workers.value.filter(w => w.status === 'working')
  )
  
  const idleWorkers = computed(() =>
    workers.value.filter(w => w.status === 'idle')
  )
  
  const inactiveWorkers = computed(() =>
    workers.value.filter(w => w.status === 'inactive')
  )
  
  const totalWorkers = computed(() => workers.value.length)
  
  const messageCount = computed(() => recentMessages.value.length)
  
  const lastUpdateTime = computed(() => data.value?.timestamp)
  
  // Actions
  const updateData = (newData: DashboardData) => {
    data.value = newData
    error.value = undefined
  }
  
  const setError = (errorMessage: string) => {
    error.value = errorMessage
  }
  
  const clearError = () => {
    error.value = undefined
  }
  
  const setLoading = (loading: boolean) => {
    isLoading.value = loading
  }
  
  const getWorkerByName = (name: string): Worker | undefined => {
    return workers.value.find(w => w.name === name)
  }
  
  const getMessagesByType = (messageType: string): Message[] => {
    return recentMessages.value.filter(m => m.message_type === messageType)
  }
  
  const getMessagesByWorker = (workerName: string): Message[] => {
    return recentMessages.value.filter(
      m => m.source === workerName || m.target === workerName
    )
  }
  
  return {
    // State
    data,
    isLoading,
    error,
    
    // Getters
    workers,
    recentMessages,
    performanceMetrics,
    currentSession,
    activeWorkers,
    workingWorkers,
    idleWorkers,
    inactiveWorkers,
    totalWorkers,
    messageCount,
    lastUpdateTime,
    
    // Actions
    updateData,
    setError,
    clearError,
    setLoading,
    getWorkerByName,
    getMessagesByType,
    getMessagesByWorker,
  }
})