export interface Worker {
  name: string;
  status: 'active' | 'idle' | 'working' | 'inactive';
  emoji: string;
  last_activity: string;
  current_task?: string;
  performance?: {
    tasks_completed: number;
    avg_response_time: number;
    success_rate: number;
  };
}

export interface Message {
  id: string;
  timestamp: string;
  source: string;
  target: string;
  message_type: string;
  event_type?: string;
  message: string;
  priority?: 'high' | 'medium' | 'low';
}

export interface PerformanceMetrics {
  total_tasks: number;
  completed_tasks: number;
  success_rate: number;
  avg_response_time: number;
  active_workers: number;
  memory_usage?: {
    used: number;
    total: number;
    percentage: number;
  };
  cpu_usage?: number;
}

export interface Session {
  id: string;
  start_time: string;
  duration: number;
  status: 'active' | 'paused' | 'completed';
  total_messages: number;
  total_workers: number;
}

export interface DashboardData {
  workers: Worker[];
  recent_messages: Message[];
  performance_metrics: PerformanceMetrics;
  current_session: Session;
  timestamp: string;
}

export interface WorkerPosition {
  x: number;
  y: number;
}

export interface CommunicationFlow {
  id: string;
  source: string;
  target: string;
  message_type: string;
  timestamp: string;
  status: 'sending' | 'delivered' | 'failed';
}

export interface ChartConfig {
  canvasWidth: number;
  canvasHeight: number;
  nodeRadius: number;
  animationDuration: number;
  maxVisibleMessages: number;
}

export interface ConnectionStatus {
  isConnected: boolean;
  lastHeartbeat?: string;
  reconnectAttempts: number;
  error?: string;
}