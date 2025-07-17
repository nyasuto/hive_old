// Hive Flow Visualization - SVG-based Real-time Communication Flow
// Issue #132 - Phase 3B: Communication Flow Visualization

class FlowVisualization {
    constructor() {
        this.svg = null;
        this.isPlaying = true;
        this.animationSpeed = 1;
        this.messageQueue = [];
        this.activeAnimations = [];
        this.workerNodes = {};
        
        // 設定
        this.config = {
            nodeRadius: 30,
            canvasWidth: 800,
            canvasHeight: 400,
            animationDuration: 2000,
            maxMessages: 50
        };
        
        // カラー設定
        this.colors = {
            'task': '#f39c12',
            'direct': '#f39c12',
            'task_start': '#f39c12',
            'result': '#27ae60',
            'response': '#27ae60',
            'task_complete': '#27ae60',
            'parallel_start': '#3498db',
            'parallel_complete': '#3498db',
            'error': '#e74c3c',
            'default': '#888888'
        };
        
        this.initializeFlow();
    }
    
    // フロー可視化初期化
    initializeFlow() {
        this.svg = document.getElementById('flow-canvas');
        if (!this.svg) {
            console.warn('⚠️  Flow canvas not found');
            return;
        }
        
        // SVG設定
        this.svg.setAttribute('viewBox', `0 0 ${this.config.canvasWidth} ${this.config.canvasHeight}`);
        
        // Worker ノード配置
        this.createWorkerNodes();
        
        // コントロール設定
        this.initializeControls();
        
        console.log('✅ Flow visualization initialized');
    }
    
    // Worker ノード作成
    createWorkerNodes() {
        const workers = [
            { name: 'beekeeper', emoji: '📋', x: 150, y: 200 },
            { name: 'queen', emoji: '👑', x: 400, y: 100 },
            { name: 'developer', emoji: '👨‍💻', x: 650, y: 150 },
            { name: 'tester', emoji: '🧪', x: 650, y: 250 },
            { name: 'analyzer', emoji: '🔍', x: 550, y: 350 },
            { name: 'documenter', emoji: '📝', x: 350, y: 350 },
            { name: 'reviewer', emoji: '👀', x: 250, y: 280 }
        ];
        
        workers.forEach(worker => {
            this.createWorkerNode(worker);
        });
    }
    
    // 個別Worker ノード作成
    createWorkerNode(worker) {
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('id', `worker-${worker.name}`);
        group.setAttribute('class', 'worker-node');
        
        // 背景円
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', worker.x);
        circle.setAttribute('cy', worker.y);
        circle.setAttribute('r', this.config.nodeRadius);
        circle.setAttribute('fill', '#404040');
        circle.setAttribute('stroke', '#666666');
        circle.setAttribute('stroke-width', '2');
        circle.setAttribute('class', 'worker-circle');
        
        // アクティビティリング（状態表示用）
        const activityRing = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        activityRing.setAttribute('cx', worker.x);
        activityRing.setAttribute('cy', worker.y);
        activityRing.setAttribute('r', this.config.nodeRadius + 5);
        activityRing.setAttribute('fill', 'none');
        activityRing.setAttribute('stroke', '#27ae60');
        activityRing.setAttribute('stroke-width', '3');
        activityRing.setAttribute('opacity', '0');
        activityRing.setAttribute('class', 'activity-ring');
        
        // 絵文字テキスト
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', worker.x);
        text.setAttribute('y', worker.y + 5);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('font-size', '20');
        text.setAttribute('class', 'worker-emoji');
        text.textContent = worker.emoji;
        
        // 名前ラベル
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', worker.x);
        label.setAttribute('y', worker.y + this.config.nodeRadius + 20);
        label.setAttribute('text-anchor', 'middle');
        label.setAttribute('font-size', '12');
        label.setAttribute('fill', '#cccccc');
        label.setAttribute('class', 'worker-label');
        label.textContent = worker.name;
        
        // グループに追加
        group.appendChild(activityRing);
        group.appendChild(circle);
        group.appendChild(text);
        group.appendChild(label);
        
        this.svg.appendChild(group);
        
        // ノード情報保存
        this.workerNodes[worker.name] = {
            element: group,
            circle: circle,
            activityRing: activityRing,
            x: worker.x,
            y: worker.y,
            status: 'idle'
        };
    }
    
    // コントロール初期化
    initializeControls() {
        // 再生/一時停止ボタン
        const playPauseBtn = document.getElementById('flow-play-pause');
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', () => {
                this.togglePlayPause();
            });
        }
        
        // クリアボタン
        const clearBtn = document.getElementById('flow-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearFlow();
            });
        }
        
        // スピード選択
        const speedSelect = document.getElementById('flow-speed-select');
        if (speedSelect) {
            speedSelect.addEventListener('change', (e) => {
                this.animationSpeed = parseFloat(e.target.value);
                console.log(`🚀 Flow speed changed to ${this.animationSpeed}x`);
            });
        }
    }
    
    // メッセージアニメーション追加
    addMessage(message) {
        if (!this.isPlaying) return;
        
        const sourceNode = this.workerNodes[message.source];
        const targetNode = this.workerNodes[message.target];
        
        if (!sourceNode || !targetNode) {
            console.warn(`⚠️  Unknown worker: ${message.source} -> ${message.target}`);
            return;
        }
        
        // メッセージキューに追加
        this.messageQueue.push({
            ...message,
            id: Date.now() + Math.random(),
            sourceNode,
            targetNode
        });
        
        // キューが長すぎる場合は古いメッセージを削除
        if (this.messageQueue.length > this.config.maxMessages) {
            this.messageQueue.shift();
        }
        
        // アニメーション実行
        this.animateMessage(this.messageQueue[this.messageQueue.length - 1]);
    }
    
    // メッセージアニメーション実行
    animateMessage(messageData) {
        const { sourceNode, targetNode, message_type, message } = messageData;
        
        // パスを計算
        const path = this.calculatePath(sourceNode, targetNode);
        
        // アニメーション要素作成
        const animationGroup = this.createMessageAnimation(path, message_type, message);
        
        // アニメーション開始
        this.startMessageAnimation(animationGroup, messageData);
        
        // Worker活動状態更新
        this.updateWorkerActivity(sourceNode, targetNode, message_type);
    }
    
    // パス計算
    calculatePath(sourceNode, targetNode) {
        const dx = targetNode.x - sourceNode.x;
        const dy = targetNode.y - sourceNode.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // ノードの境界から開始・終了
        const startX = sourceNode.x + (dx / distance) * this.config.nodeRadius;
        const startY = sourceNode.y + (dy / distance) * this.config.nodeRadius;
        const endX = targetNode.x - (dx / distance) * this.config.nodeRadius;
        const endY = targetNode.y - (dy / distance) * this.config.nodeRadius;
        
        // ベジェ曲線の制御点
        const midX = (startX + endX) / 2;
        const midY = (startY + endY) / 2;
        const controlX = midX + (Math.random() - 0.5) * 100;
        const controlY = midY - 50;
        
        return {
            startX, startY, endX, endY,
            controlX, controlY,
            pathString: `M ${startX} ${startY} Q ${controlX} ${controlY} ${endX} ${endY}`
        };
    }
    
    // メッセージアニメーション要素作成
    createMessageAnimation(path, messageType, messageText) {
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', 'message-animation');
        
        // パス
        const pathElement = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        pathElement.setAttribute('d', path.pathString);
        pathElement.setAttribute('stroke', this.colors[messageType] || this.colors.default);
        pathElement.setAttribute('stroke-width', '2');
        pathElement.setAttribute('fill', 'none');
        pathElement.setAttribute('opacity', '0.6');
        
        // メッセージドット
        const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        dot.setAttribute('r', '6');
        dot.setAttribute('fill', this.colors[messageType] || this.colors.default);
        dot.setAttribute('stroke', '#ffffff');
        dot.setAttribute('stroke-width', '2');
        
        // メッセージテキスト（ツールチップ用）
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        title.textContent = `${messageType}: ${messageText.substring(0, 50)}...`;
        
        group.appendChild(pathElement);
        group.appendChild(dot);
        group.appendChild(title);
        
        this.svg.appendChild(group);
        
        return { group, pathElement, dot, path };
    }
    
    // アニメーション開始
    startMessageAnimation(animationElements, messageData) {
        const { group, pathElement, dot, path } = animationElements;
        const duration = this.config.animationDuration / this.animationSpeed;
        
        // パスアニメーション
        const pathLength = pathElement.getTotalLength();
        pathElement.setAttribute('stroke-dasharray', pathLength);
        pathElement.setAttribute('stroke-dashoffset', pathLength);
        
        // CSS アニメーション
        pathElement.style.animation = `drawPath ${duration}ms ease-out forwards`;
        
        // ドット移動アニメーション
        let startTime = null;
        
        const animateDot = (timestamp) => {
            if (!startTime) startTime = timestamp;
            
            const progress = Math.min((timestamp - startTime) / duration, 1);
            const point = this.getPointAtProgress(path, progress);
            
            dot.setAttribute('cx', point.x);
            dot.setAttribute('cy', point.y);
            
            if (progress < 1) {
                requestAnimationFrame(animateDot);
            } else {
                // アニメーション完了
                setTimeout(() => {
                    if (group.parentNode) {
                        group.parentNode.removeChild(group);
                    }
                }, 500); // 0.5秒後に削除
            }
        };
        
        requestAnimationFrame(animateDot);
        
        // アクティブアニメーション追跡
        this.activeAnimations.push({
            group,
            startTime: Date.now(),
            duration,
            messageData
        });
    }
    
    // パス上の点を取得
    getPointAtProgress(path, progress) {
        // ベジェ曲線上の点を計算
        const t = progress;
        const x = Math.pow(1 - t, 2) * path.startX + 
                 2 * (1 - t) * t * path.controlX + 
                 Math.pow(t, 2) * path.endX;
        const y = Math.pow(1 - t, 2) * path.startY + 
                 2 * (1 - t) * t * path.controlY + 
                 Math.pow(t, 2) * path.endY;
        
        return { x, y };
    }
    
    // Worker活動状態更新
    updateWorkerActivity(sourceNode, targetNode, messageType) {
        // 送信側のアクティビティ表示
        this.showWorkerActivity(sourceNode, 'sending');
        
        // 受信側のアクティビティ表示（少し遅延）
        setTimeout(() => {
            this.showWorkerActivity(targetNode, 'receiving');
        }, 500);
    }
    
    // Worker活動表示
    showWorkerActivity(workerNode, activity) {
        const ring = workerNode.activityRing;
        const circle = workerNode.circle;
        
        // アクティビティリング表示
        ring.setAttribute('opacity', '0.8');
        
        // 色設定
        const color = activity === 'sending' ? '#f39c12' : '#27ae60';
        ring.setAttribute('stroke', color);
        circle.setAttribute('stroke', color);
        
        // パルスアニメーション
        ring.style.animation = 'pulse 1s ease-out';
        
        // 1秒後にリセット
        setTimeout(() => {
            ring.setAttribute('opacity', '0');
            circle.setAttribute('stroke', '#666666');
            ring.style.animation = '';
        }, 1000);
    }
    
    // Worker状態更新
    updateWorkerStatus(workerName, status) {
        const worker = this.workerNodes[workerName];
        if (!worker) return;
        
        worker.status = status;
        const circle = worker.circle;
        
        // 状態に応じた色設定
        const statusColors = {
            'active': '#27ae60',
            'working': '#f39c12',
            'idle': '#666666',
            'inactive': '#444444',
            'error': '#e74c3c'
        };
        
        circle.setAttribute('fill', statusColors[status] || statusColors.idle);
    }
    
    // 再生/一時停止切り替え
    togglePlayPause() {
        this.isPlaying = !this.isPlaying;
        const btn = document.getElementById('flow-play-pause');
        
        if (btn) {
            btn.textContent = this.isPlaying ? '⏸️ Pause' : '▶️ Play';
        }
        
        console.log(`📊 Flow visualization ${this.isPlaying ? 'resumed' : 'paused'}`);
    }
    
    // フロークリア
    clearFlow() {
        // 全てのメッセージアニメーションを削除
        const messageAnimations = this.svg.querySelectorAll('.message-animation');
        messageAnimations.forEach(element => {
            element.remove();
        });
        
        this.messageQueue = [];
        this.activeAnimations = [];
        
        console.log('🗑️  Flow visualization cleared');
    }
    
    // 破棄
    destroy() {
        this.clearFlow();
        this.workerNodes = {};
    }
}

// CSS アニメーション定義
const style = document.createElement('style');
style.textContent = `
    @keyframes drawPath {
        to {
            stroke-dashoffset: 0;
        }
    }
    
    @keyframes pulse {
        0% { 
            transform: scale(1);
            opacity: 0.8;
        }
        50% { 
            transform: scale(1.1);
            opacity: 1;
        }
        100% { 
            transform: scale(1);
            opacity: 0.8;
        }
    }
    
    .worker-node {
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .worker-node:hover .worker-circle {
        stroke-width: 3;
        filter: brightness(1.2);
    }
    
    .message-animation {
        pointer-events: none;
    }
`;
document.head.appendChild(style);