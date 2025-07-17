// Hive Dashboard Charts - Chart.js Integration
// Issue #132 - Phase 3B: Advanced Data Visualization

class HiveCharts {
    constructor() {
        this.charts = {};
        this.chartConfig = {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        color: '#ffffff'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#f39c12',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#cccccc'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#cccccc'
                    }
                }
            }
        };
        
        this.colors = {
            primary: '#f39c12',
            secondary: '#e67e22',
            success: '#27ae60',
            warning: '#f1c40f',
            danger: '#e74c3c',
            info: '#3498db',
            gradient: {
                primary: 'linear-gradient(135deg, #f39c12, #e67e22)',
                success: 'linear-gradient(135deg, #27ae60, #2ecc71)',
                info: 'linear-gradient(135deg, #3498db, #2980b9)'
            }
        };
        
        this.dataHistory = {
            efficiency: [],
            responseTime: [],
            messageRate: [],
            workerActivity: [],
            timestamps: []
        };
        
        this.maxDataPoints = 50; // 50ポイントの履歴保持
        this.initializeCharts();
    }
    
    // Chart.js初期化
    initializeCharts() {
        // Chart.jsが利用可能かチェック
        if (typeof Chart === 'undefined') {
            console.warn('⚠️  Chart.js not loaded, loading from CDN...');
            this.loadChartJS().then(() => {
                this.createCharts();
            });
        } else {
            this.createCharts();
        }
    }
    
    // Chart.js動的ロード
    async loadChartJS() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js';
            script.onload = () => {
                console.log('✅ Chart.js loaded successfully');
                resolve();
            };
            script.onerror = () => {
                console.error('❌ Failed to load Chart.js');
                reject(new Error('Chart.js load failed'));
            };
            document.head.appendChild(script);
        });
    }
    
    // チャート作成
    createCharts() {
        this.createPerformanceChart();
        this.createWorkerActivityChart();
        this.createMessageFlowChart();
        this.createSystemMetricsChart();
    }
    
    // パフォーマンス総合チャート
    createPerformanceChart() {
        const canvas = this.createChartCanvas('performance-chart', 'performance-chart-container');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        this.charts.performance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Efficiency (%)',
                        data: [],
                        borderColor: this.colors.primary,
                        backgroundColor: this.colors.primary + '20',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Response Time (s)',
                        data: [],
                        borderColor: this.colors.info,
                        backgroundColor: this.colors.info + '20',
                        fill: false,
                        tension: 0.4,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                ...this.chartConfig,
                scales: {
                    ...this.chartConfig.scales,
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false,
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#cccccc'
                        }
                    }
                },
                plugins: {
                    ...this.chartConfig.plugins,
                    title: {
                        display: true,
                        text: '📊 System Performance Overview',
                        color: '#ffffff',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    }
                }
            }
        });
    }
    
    // Worker活動チャート
    createWorkerActivityChart() {
        const canvas = this.createChartCanvas('worker-activity-chart', 'worker-activity-container');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        this.charts.workerActivity = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Active', 'Idle', 'Working', 'Inactive'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        this.colors.success,
                        this.colors.warning,
                        this.colors.primary,
                        '#555555'
                    ],
                    borderColor: '#2c2c2c',
                    borderWidth: 2,
                    hoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#ffffff',
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    title: {
                        display: true,
                        text: '👥 Worker Status Distribution',
                        color: '#ffffff',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    }
                }
            }
        });
    }
    
    // メッセージフローチャート
    createMessageFlowChart() {
        const canvas = this.createChartCanvas('message-flow-chart', 'message-flow-container');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        this.charts.messageFlow = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Messages/min',
                        data: [],
                        backgroundColor: this.colors.primary,
                        borderColor: this.colors.secondary,
                        borderWidth: 1,
                        borderRadius: 4
                    }
                ]
            },
            options: {
                ...this.chartConfig,
                plugins: {
                    ...this.chartConfig.plugins,
                    title: {
                        display: true,
                        text: '💬 Message Flow Rate',
                        color: '#ffffff',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#cccccc',
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#cccccc'
                        }
                    }
                }
            }
        });
    }
    
    // システム指標チャート
    createSystemMetricsChart() {
        const canvas = this.createChartCanvas('system-metrics-chart', 'system-metrics-container');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        this.charts.systemMetrics = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Efficiency', 'Response Time', 'Message Rate', 'Worker Utilization', 'System Health'],
                datasets: [{
                    label: 'Current Performance',
                    data: [0, 0, 0, 0, 0],
                    borderColor: this.colors.primary,
                    backgroundColor: this.colors.primary + '30',
                    pointBackgroundColor: this.colors.primary,
                    pointBorderColor: '#ffffff',
                    pointRadius: 5,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: '⚡ System Health Radar',
                        color: '#ffffff',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.2)'
                        },
                        angleLines: {
                            color: 'rgba(255, 255, 255, 0.2)'
                        },
                        pointLabels: {
                            color: '#ffffff',
                            font: {
                                size: 11
                            }
                        },
                        ticks: {
                            color: '#cccccc',
                            backdropColor: 'transparent'
                        }
                    }
                }
            }
        });
    }
    
    // Chart canvas要素作成ヘルパー
    createChartCanvas(canvasId, containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`⚠️  Chart container not found: ${containerId}`);
            return null;
        }
        
        // 既存のcanvasがあれば削除
        const existingCanvas = container.querySelector('canvas');
        if (existingCanvas) {
            existingCanvas.remove();
        }
        
        const canvas = document.createElement('canvas');
        canvas.id = canvasId;
        canvas.style.width = '100%';
        canvas.style.height = '300px';
        container.appendChild(canvas);
        
        return canvas;
    }
    
    // パフォーマンスデータ更新
    updatePerformanceData(metrics) {
        const timestamp = new Date().toLocaleTimeString();
        
        // データ履歴を更新
        this.addDataPoint('efficiency', metrics.efficiency || 0);
        this.addDataPoint('responseTime', metrics.avg_response_time || 0);
        this.addDataPoint('messageRate', metrics.message_rate || 0);
        this.addDataPoint('timestamps', timestamp);
        
        // パフォーマンスチャート更新
        if (this.charts.performance) {
            this.charts.performance.data.labels = this.dataHistory.timestamps;
            this.charts.performance.data.datasets[0].data = this.dataHistory.efficiency;
            this.charts.performance.data.datasets[1].data = this.dataHistory.responseTime;
            this.charts.performance.update('none');
        }
        
        // メッセージフローチャート更新
        if (this.charts.messageFlow) {
            const recentData = this.dataHistory.messageRate.slice(-10);
            const recentLabels = this.dataHistory.timestamps.slice(-10);
            
            this.charts.messageFlow.data.labels = recentLabels;
            this.charts.messageFlow.data.datasets[0].data = recentData;
            this.charts.messageFlow.update('none');
        }
        
        // システム指標レーダーチャート更新
        if (this.charts.systemMetrics) {
            const radarData = [
                metrics.efficiency || 0,
                Math.max(0, 100 - (metrics.avg_response_time || 0) * 20), // 応答時間逆算
                Math.min(100, (metrics.message_rate || 0) * 10),
                (metrics.active_workers || 0) * 100 / 7, // 7 workers max
                this.calculateSystemHealth(metrics)
            ];
            
            this.charts.systemMetrics.data.datasets[0].data = radarData;
            this.charts.systemMetrics.update('none');
        }
    }
    
    // Worker活動データ更新
    updateWorkerActivity(workers) {
        if (!this.charts.workerActivity || !workers) return;
        
        const statusCounts = {
            active: 0,
            idle: 0,
            working: 0,
            inactive: 0
        };
        
        workers.forEach(worker => {
            const status = worker.status.toLowerCase();
            if (statusCounts.hasOwnProperty(status)) {
                statusCounts[status]++;
            } else {
                statusCounts.inactive++;
            }
        });
        
        this.charts.workerActivity.data.datasets[0].data = [
            statusCounts.active,
            statusCounts.idle,
            statusCounts.working,
            statusCounts.inactive
        ];
        
        this.charts.workerActivity.update('none');
    }
    
    // データポイント追加（履歴管理）
    addDataPoint(key, value) {
        if (!this.dataHistory[key]) {
            this.dataHistory[key] = [];
        }
        
        this.dataHistory[key].push(value);
        
        // 最大データポイント数を超えたら古いデータを削除
        if (this.dataHistory[key].length > this.maxDataPoints) {
            this.dataHistory[key].shift();
        }
    }
    
    // システムヘルス計算
    calculateSystemHealth(metrics) {
        const efficiency = metrics.efficiency || 0;
        const responseTime = metrics.avg_response_time || 0;
        const messageRate = metrics.message_rate || 0;
        const activeWorkers = metrics.active_workers || 0;
        
        // 総合ヘルススコア計算
        const efficiencyScore = efficiency;
        const responseScore = Math.max(0, 100 - responseTime * 10);
        const activityScore = Math.min(100, messageRate * 20);
        const workerScore = (activeWorkers / 7) * 100;
        
        return Math.round((efficiencyScore + responseScore + activityScore + workerScore) / 4);
    }
    
    // チャートリサイズ処理
    handleResize() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    }
    
    // チャート破棄
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }
    
    // データエクスポート
    exportData() {
        return {
            timestamp: new Date().toISOString(),
            dataHistory: this.dataHistory,
            chartTypes: Object.keys(this.charts)
        };
    }
    
    // チャート設定取得
    getChartConfig(type) {
        const chart = this.charts[type];
        return chart ? chart.config : null;
    }
}

// リサイズイベントリスナー
window.addEventListener('resize', () => {
    if (window.hiveCharts) {
        window.hiveCharts.handleResize();
    }
});

// チャートテーマ切り替え
function toggleChartTheme(isDark = true) {
    const textColor = isDark ? '#ffffff' : '#333333';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    
    if (window.hiveCharts) {
        Object.values(window.hiveCharts.charts).forEach(chart => {
            if (chart.options.plugins && chart.options.plugins.legend) {
                chart.options.plugins.legend.labels.color = textColor;
            }
            if (chart.options.scales) {
                Object.values(chart.options.scales).forEach(scale => {
                    if (scale.ticks) scale.ticks.color = textColor;
                    if (scale.grid) scale.grid.color = gridColor;
                });
            }
            chart.update();
        });
    }
}

// ダッシュボード初期化時のチャート設定
document.addEventListener('DOMContentLoaded', () => {
    console.log('📊 Initializing Hive Charts...');
    
    // Chart.js設定
    if (typeof Chart !== 'undefined') {
        Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#ffffff';
    }
});