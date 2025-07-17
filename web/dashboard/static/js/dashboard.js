// Hive Dashboard JavaScript - Real-time WebSocket Client
// Issue #132 - Phase 3A: Browser Dashboard Frontend

class HiveDashboard {
    constructor() {
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 2000;
        this.lastUpdateTime = null;
        
        // Chart.js integration
        this.charts = null;
        
        // Flow visualization
        this.flowViz = null;
        
        this.initializeWebSocket();
        this.initializeUI();
        this.initializeCharts();
        this.initializeFlowVisualization();
        this.startHeartbeat();
    }
    
    // WebSocket接続管理
    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        console.log('🔌 Connecting to WebSocket:', wsUrl);
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = (event) => {
            console.log('✅ WebSocket connected');
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
            
            // 接続確認メッセージ送信
            this.sendMessage({ type: 'ping', timestamp: new Date().toISOString() });
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleDashboardUpdate(data);
            } catch (error) {
                console.error('❌ WebSocket message parse error:', error);
            }
        };
        
        this.websocket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
        
        this.websocket.onclose = (event) => {
            console.log('🔌 WebSocket disconnected:', event.code, event.reason);
            this.updateConnectionStatus(false);
            this.scheduleReconnect();
        };
    }
    
    // 再接続処理
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.initializeWebSocket();
            }, this.reconnectInterval * this.reconnectAttempts);
        } else {
            console.error('❌ Max reconnection attempts reached');
            this.showReconnectionError();
        }
    }
    
    // メッセージ送信
    sendMessage(message) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        }
    }
    
    // ダッシュボードデータ更新処理
    handleDashboardUpdate(data) {
        // 詳細ログは開発時のみ有効化
        if (window.location.search.includes('debug=true')) {
            console.log('📊 Dashboard update received:', data.timestamp);
        }
        this.lastUpdateTime = new Date();
        
        // Worker状態更新
        this.updateWorkers(data.workers || []);
        
        // Chart.js Worker活動更新
        if (this.charts) {
            this.charts.updateWorkerActivity(data.workers || []);
        }
        
        // フロー可視化 Worker状態更新
        if (this.flowViz && data.workers) {
            data.workers.forEach(worker => {
                this.flowViz.updateWorkerStatus(worker.name, worker.status);
            });
        }
        
        // 通信メッセージ更新
        this.updateCommunications(data.recent_messages || []);
        
        // フロー可視化更新（新しいメッセージがあれば）
        if (this.flowViz && data.recent_messages && data.recent_messages.length > 0) {
            // 最新のメッセージをフロー可視化に追加
            const latestMessage = data.recent_messages[data.recent_messages.length - 1];
            this.flowViz.addMessage(latestMessage);
        }
        
        // パフォーマンス指標更新
        this.updatePerformanceMetrics(data.performance_metrics || {});
        
        // セッション情報更新
        this.updateSessionInfo(data.current_session);
        
        // 最終更新時刻表示
        this.updateLastUpdateTime();
    }
    
    // Worker状態表示更新
    updateWorkers(workers) {
        const workersContainer = document.getElementById('workers-container');
        if (!workersContainer) return;
        
        // アクティブなWorker数を計算
        const activeCount = workers.filter(w => w.status === 'active').length;
        this.updateActiveWorkerCount(activeCount, workers.length);
        
        // Worker一覧を更新
        workersContainer.innerHTML = workers.map(worker => `
            <div class="worker-card ${worker.status}" data-worker="${worker.name}">
                <div class="worker-info">
                    <div class="worker-avatar">${worker.emoji}</div>
                    <div class="worker-details">
                        <h3>${worker.name}</h3>
                        <span class="worker-status ${worker.status}">${worker.status}</span>
                        ${worker.current_task ? `<p class="worker-task">${worker.current_task}</p>` : ''}
                        ${worker.last_activity ? `<small>Last: ${worker.last_activity}</small>` : ''}
                    </div>
                </div>
                ${worker.progress ? `
                    <div class="worker-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${worker.progress}%"></div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        // Worker詳細クリックイベント
        this.attachWorkerClickEvents();
    }
    
    // 通信メッセージ表示更新
    updateCommunications(messages) {
        const messagesContainer = document.getElementById('messages-container');
        if (!messagesContainer) return;
        
        messagesContainer.innerHTML = messages.map(message => {
            const arrow = this.getMessageArrow(message.message_type);
            const timestamp = new Date(message.timestamp).toLocaleTimeString();
            
            return `
                <div class="message-item fade-in" data-type="${message.message_type}">
                    <div class="message-header">
                        <div class="message-meta">
                            <span class="message-time">${timestamp}</span>
                            <span class="message-type">${message.message_type}</span>
                        </div>
                        <div class="message-flow">
                            <span class="message-source">${message.source}</span>
                            <span class="message-arrow">${arrow}</span>
                            <span class="message-target">${message.target}</span>
                        </div>
                    </div>
                    <div class="message-content">${message.message}</div>
                </div>
            `;
        }).join('');
        
        // 自動スクロール（最新メッセージ表示）
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // パフォーマンス指標更新
    updatePerformanceMetrics(metrics) {
        this.updateMetricValue('efficiency', metrics.efficiency || 0, '%');
        this.updateMetricValue('response-time', metrics.avg_response_time || 0, 's');
        this.updateMetricValue('message-rate', metrics.message_rate || 0, '/min');
        this.updateMetricValue('active-workers', metrics.active_workers || 0, '');
        
        // Chart.js更新
        if (this.charts) {
            this.charts.updatePerformanceData(metrics);
        }
    }
    
    // セッション情報更新
    updateSessionInfo(session) {
        const sessionElement = document.getElementById('current-session');
        if (!sessionElement) return;
        
        if (session) {
            sessionElement.innerHTML = `
                <div class="session-active">
                    <h3>🟢 Active Session</h3>
                    <p>ID: ${session.session_id}</p>
                    <p>Started: ${session.start_time}</p>
                    <p>Workers: ${session.active_workers.join(', ')}</p>
                    <p>Messages: ${session.message_count}</p>
                </div>
            `;
        } else {
            sessionElement.innerHTML = `
                <div class="session-inactive">
                    <h3>🔴 No Active Session</h3>
                    <p>Start Hive system to begin monitoring</p>
                </div>
            `;
        }
    }
    
    // UI初期化
    initializeUI() {
        // DOM要素の存在確認と初期化
        this.createDashboardHTML();
        
        // リフレッシュボタン
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.manualRefresh());
        }
        
        // タブ切り替え機能
        this.initializeTabs();
    }
    
    // ダッシュボードHTML構造作成
    createDashboardHTML() {
        const app = document.getElementById('app');
        if (!app) return;
        
        app.innerHTML = `
            <div class="dashboard-container">
                <!-- Header -->
                <div class="dashboard-header">
                    <div class="header-title">
                        <h1>🐝 Hive Dashboard</h1>
                        <div id="connection-status" class="status-indicator status-inactive">Connecting...</div>
                    </div>
                    <div class="header-status">
                        <div id="active-worker-count" class="metric">
                            <span id="active-count">0</span>/<span id="total-count">0</span> Workers
                        </div>
                        <button id="refresh-btn" class="btn-refresh">🔄 Refresh</button>
                        <div id="last-update" class="last-update">Never</div>
                    </div>
                </div>
                
                <!-- Workers Sidebar -->
                <div class="workers-sidebar">
                    <div class="workers-header">
                        <h2>👥 Workers</h2>
                        <div id="worker-summary"></div>
                    </div>
                    <div id="workers-container" class="loading">
                        Loading workers...
                    </div>
                </div>
                
                <!-- Main Content -->
                <div class="main-content">
                    <h2>📊 Communication Flow</h2>
                    <div class="flow-visualization" id="flow-visualization">
                        <div class="flow-controls">
                            <button id="flow-play-pause" class="flow-btn">⏸️ Pause</button>
                            <button id="flow-clear" class="flow-btn">🗑️ Clear</button>
                            <span class="flow-speed">Speed: 
                                <select id="flow-speed-select">
                                    <option value="0.5">0.5x</option>
                                    <option value="1" selected>1x</option>
                                    <option value="2">2x</option>
                                    <option value="5">5x</option>
                                </select>
                            </span>
                        </div>
                        <div class="flow-canvas-container">
                            <svg id="flow-canvas" width="100%" height="400">
                                <!-- Worker nodes will be added dynamically -->
                            </svg>
                        </div>
                        <div class="flow-legend">
                            <div class="legend-item">
                                <span class="legend-icon" style="color: #f39c12;">→</span> Task Assignment
                            </div>
                            <div class="legend-item">
                                <span class="legend-icon" style="color: #27ae60;">←</span> Result Return
                            </div>
                            <div class="legend-item">
                                <span class="legend-icon" style="color: #3498db;">⚡</span> Parallel Operation
                            </div>
                            <div class="legend-item">
                                <span class="legend-icon" style="color: #e74c3c;">❌</span> Error
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Communications Panel -->
                <div class="communications-panel">
                    <div class="communications-header">
                        <h2>💬 Communications</h2>
                        <div class="message-count">
                            <span id="message-count">0</span> messages
                        </div>
                    </div>
                    <div id="messages-container" class="message-list loading">
                        Loading messages...
                    </div>
                </div>
                
                <!-- Performance Panel -->
                <div class="performance-panel">
                    <div class="performance-header">
                        <h2>⚡ Performance & Analytics</h2>
                    </div>
                    
                    <!-- Quick Metrics -->
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div id="efficiency-value" class="metric-value">0%</div>
                            <div class="metric-label">Efficiency</div>
                        </div>
                        <div class="metric-card">
                            <div id="response-time-value" class="metric-value">0s</div>
                            <div class="metric-label">Avg Response</div>
                        </div>
                        <div class="metric-card">
                            <div id="message-rate-value" class="metric-value">0/min</div>
                            <div class="metric-label">Message Rate</div>
                        </div>
                        <div class="metric-card">
                            <div id="active-workers-value" class="metric-value">0</div>
                            <div class="metric-label">Active Workers</div>
                        </div>
                    </div>
                    
                    <!-- Chart Tabs -->
                    <div class="chart-tabs">
                        <div class="chart-tab active" data-chart="performance">📊 Performance</div>
                        <div class="chart-tab" data-chart="activity">👥 Activity</div>
                        <div class="chart-tab" data-chart="flow">💬 Flow</div>
                        <div class="chart-tab" data-chart="health">⚡ Health</div>
                    </div>
                    
                    <!-- Chart Content -->
                    <div class="chart-content active" id="performance-chart-content">
                        <div id="performance-chart-container" class="chart-container">
                            <div class="chart-loading">Loading performance chart...</div>
                        </div>
                    </div>
                    
                    <div class="chart-content" id="activity-chart-content">
                        <div id="worker-activity-container" class="chart-container">
                            <div class="chart-loading">Loading activity chart...</div>
                        </div>
                    </div>
                    
                    <div class="chart-content" id="flow-chart-content">
                        <div id="message-flow-container" class="chart-container">
                            <div class="chart-loading">Loading message flow chart...</div>
                        </div>
                    </div>
                    
                    <div class="chart-content" id="health-chart-content">
                        <div id="system-metrics-container" class="chart-container">
                            <div class="chart-loading">Loading health radar...</div>
                        </div>
                    </div>
                    
                    <!-- Session Info -->
                    <div id="current-session" class="session-info">
                        <div class="session-inactive">
                            <h3>🔴 No Active Session</h3>
                            <p>Waiting for connection...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // ヘルパーメソッド
    getMessageArrow(messageType) {
        const arrows = {
            'task': '→',
            'direct': '→',
            'task_start': '→',
            'result': '←',
            'response': '←',
            'task_complete': '←',
            'parallel_start': '⚡',
            'parallel_complete': '⚡',
            'error': '❌'
        };
        return arrows[messageType] || '•';
    }
    
    updateMetricValue(metricId, value, unit) {
        const element = document.getElementById(`${metricId}-value`);
        if (element) {
            element.textContent = `${value}${unit}`;
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            if (connected) {
                statusElement.textContent = 'Connected';
                statusElement.className = 'status-indicator status-active';
            } else {
                statusElement.textContent = 'Disconnected';
                statusElement.className = 'status-indicator status-inactive';
            }
        }
    }
    
    updateActiveWorkerCount(active, total) {
        const activeElement = document.getElementById('active-count');
        const totalElement = document.getElementById('total-count');
        
        if (activeElement) activeElement.textContent = active;
        if (totalElement) totalElement.textContent = total;
    }
    
    updateLastUpdateTime() {
        const element = document.getElementById('last-update');
        if (element && this.lastUpdateTime) {
            element.textContent = `Updated: ${this.lastUpdateTime.toLocaleTimeString()}`;
        }
    }
    
    attachWorkerClickEvents() {
        const workerCards = document.querySelectorAll('.worker-card');
        workerCards.forEach(card => {
            card.addEventListener('click', () => {
                const workerName = card.dataset.worker;
                this.showWorkerDetails(workerName);
            });
        });
    }
    
    showWorkerDetails(workerName) {
        // Worker詳細モーダル表示（後で実装）
        console.log(`📋 Worker details: ${workerName}`);
        alert(`Worker Details: ${workerName}\n\nDetailed view will be implemented in Phase 3B`);
    }
    
    manualRefresh() {
        console.log('🔄 Manual refresh requested');
        this.sendMessage({ type: 'refresh', timestamp: new Date().toISOString() });
    }
    
    showReconnectionError() {
        const app = document.getElementById('app');
        if (app) {
            app.innerHTML = `
                <div class="error-container">
                    <h1>❌ Connection Lost</h1>
                    <p>Unable to connect to Hive Dashboard server.</p>
                    <button onclick="location.reload()">🔄 Retry</button>
                </div>
            `;
        }
    }
    
    // ハートビート（接続維持）
    startHeartbeat() {
        setInterval(() => {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.sendMessage({ type: 'heartbeat', timestamp: new Date().toISOString() });
            }
        }, 30000); // 30秒間隔
    }
    
    // チャート初期化
    initializeCharts() {
        // Chart.jsスクリプト読み込み確認
        if (typeof HiveCharts === 'undefined') {
            console.log('📊 Loading charts module...');
            const script = document.createElement('script');
            script.src = '/static/js/charts.js';
            script.onload = () => {
                this.charts = new HiveCharts();
                console.log('✅ Charts initialized');
            };
            document.head.appendChild(script);
        } else {
            this.charts = new HiveCharts();
        }
    }
    
    // フロー可視化初期化
    initializeFlowVisualization() {
        if (typeof FlowVisualization === 'undefined') {
            console.log('🌊 Loading flow visualization module...');
            const script = document.createElement('script');
            script.src = '/static/js/flow-visualization.js';
            script.onload = () => {
                this.flowViz = new FlowVisualization();
                console.log('✅ Flow visualization initialized');
            };
            document.head.appendChild(script);
        } else {
            this.flowViz = new FlowVisualization();
        }
    }
    
    initializeTabs() {
        // チャートタブ機能
        const chartTabs = document.querySelectorAll('.chart-tab');
        const chartContents = document.querySelectorAll('.chart-content');
        
        chartTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const chartType = tab.dataset.chart;
                
                // アクティブタブ切り替え
                chartTabs.forEach(t => t.classList.remove('active'));
                chartContents.forEach(c => c.classList.remove('active'));
                
                tab.classList.add('active');
                const targetContent = document.getElementById(`${chartType}-chart-content`);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
                
                console.log(`📊 Switched to ${chartType} chart`);
            });
        });
    }
}

// アプリケーション初期化
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Hive Dashboard initializing...');
    window.hiveDashboard = new HiveDashboard();
});

// グローバルエラーハンドリング
window.addEventListener('error', (event) => {
    console.error('❌ Global error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('❌ Unhandled promise rejection:', event.reason);
});