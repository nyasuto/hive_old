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
        
        // 絵文字テキスト\n        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');\n        text.setAttribute('x', worker.x);\n        text.setAttribute('y', worker.y + 5);\n        text.setAttribute('text-anchor', 'middle');\n        text.setAttribute('font-size', '20');\n        text.setAttribute('class', 'worker-emoji');\n        text.textContent = worker.emoji;\n        \n        // 名前ラベル\n        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');\n        label.setAttribute('x', worker.x);\n        label.setAttribute('y', worker.y + this.config.nodeRadius + 20);\n        label.setAttribute('text-anchor', 'middle');\n        label.setAttribute('font-size', '12');\n        label.setAttribute('fill', '#cccccc');\n        label.setAttribute('class', 'worker-label');\n        label.textContent = worker.name;\n        \n        // グループに追加\n        group.appendChild(activityRing);\n        group.appendChild(circle);\n        group.appendChild(text);\n        group.appendChild(label);\n        \n        this.svg.appendChild(group);\n        \n        // ノード情報保存\n        this.workerNodes[worker.name] = {\n            element: group,\n            circle: circle,\n            activityRing: activityRing,\n            x: worker.x,\n            y: worker.y,\n            status: 'idle'\n        };\n    }\n    \n    // コントロール初期化\n    initializeControls() {\n        // 再生/一時停止ボタン\n        const playPauseBtn = document.getElementById('flow-play-pause');\n        if (playPauseBtn) {\n            playPauseBtn.addEventListener('click', () => {\n                this.togglePlayPause();\n            });\n        }\n        \n        // クリアボタン\n        const clearBtn = document.getElementById('flow-clear');\n        if (clearBtn) {\n            clearBtn.addEventListener('click', () => {\n                this.clearFlow();\n            });\n        }\n        \n        // スピード選択\n        const speedSelect = document.getElementById('flow-speed-select');\n        if (speedSelect) {\n            speedSelect.addEventListener('change', (e) => {\n                this.animationSpeed = parseFloat(e.target.value);\n                console.log(`🚀 Flow speed changed to ${this.animationSpeed}x`);\n            });\n        }\n    }\n    \n    // メッセージアニメーション追加\n    addMessage(message) {\n        if (!this.isPlaying) return;\n        \n        const sourceNode = this.workerNodes[message.source];\n        const targetNode = this.workerNodes[message.target];\n        \n        if (!sourceNode || !targetNode) {\n            console.warn(`⚠️  Unknown worker: ${message.source} -> ${message.target}`);\n            return;\n        }\n        \n        // メッセージキューに追加\n        this.messageQueue.push({\n            ...message,\n            id: Date.now() + Math.random(),\n            sourceNode,\n            targetNode\n        });\n        \n        // キューが長すぎる場合は古いメッセージを削除\n        if (this.messageQueue.length > this.config.maxMessages) {\n            this.messageQueue.shift();\n        }\n        \n        // アニメーション実行\n        this.animateMessage(this.messageQueue[this.messageQueue.length - 1]);\n    }\n    \n    // メッセージアニメーション実行\n    animateMessage(messageData) {\n        const { sourceNode, targetNode, message_type, message } = messageData;\n        \n        // パスを計算\n        const path = this.calculatePath(sourceNode, targetNode);\n        \n        // アニメーション要素作成\n        const animationGroup = this.createMessageAnimation(path, message_type, message);\n        \n        // アニメーション開始\n        this.startMessageAnimation(animationGroup, messageData);\n        \n        // Worker活動状態更新\n        this.updateWorkerActivity(sourceNode, targetNode, message_type);\n    }\n    \n    // パス計算\n    calculatePath(sourceNode, targetNode) {\n        const dx = targetNode.x - sourceNode.x;\n        const dy = targetNode.y - sourceNode.y;\n        const distance = Math.sqrt(dx * dx + dy * dy);\n        \n        // ノードの境界から開始・終了\n        const startX = sourceNode.x + (dx / distance) * this.config.nodeRadius;\n        const startY = sourceNode.y + (dy / distance) * this.config.nodeRadius;\n        const endX = targetNode.x - (dx / distance) * this.config.nodeRadius;\n        const endY = targetNode.y - (dy / distance) * this.config.nodeRadius;\n        \n        // ベジェ曲線の制御点\n        const midX = (startX + endX) / 2;\n        const midY = (startY + endY) / 2;\n        const controlX = midX + (Math.random() - 0.5) * 100;\n        const controlY = midY - 50;\n        \n        return {\n            startX, startY, endX, endY,\n            controlX, controlY,\n            pathString: `M ${startX} ${startY} Q ${controlX} ${controlY} ${endX} ${endY}`\n        };\n    }\n    \n    // メッセージアニメーション要素作成\n    createMessageAnimation(path, messageType, messageText) {\n        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');\n        group.setAttribute('class', 'message-animation');\n        \n        // パス\n        const pathElement = document.createElementNS('http://www.w3.org/2000/svg', 'path');\n        pathElement.setAttribute('d', path.pathString);\n        pathElement.setAttribute('stroke', this.colors[messageType] || this.colors.default);\n        pathElement.setAttribute('stroke-width', '2');\n        pathElement.setAttribute('fill', 'none');\n        pathElement.setAttribute('opacity', '0.6');\n        \n        // メッセージドット\n        const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');\n        dot.setAttribute('r', '6');\n        dot.setAttribute('fill', this.colors[messageType] || this.colors.default);\n        dot.setAttribute('stroke', '#ffffff');\n        dot.setAttribute('stroke-width', '2');\n        \n        // メッセージテキスト（ツールチップ用）\n        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');\n        title.textContent = `${messageType}: ${messageText.substring(0, 50)}...`;\n        \n        group.appendChild(pathElement);\n        group.appendChild(dot);\n        group.appendChild(title);\n        \n        this.svg.appendChild(group);\n        \n        return { group, pathElement, dot, path };\n    }\n    \n    // アニメーション開始\n    startMessageAnimation(animationElements, messageData) {\n        const { group, pathElement, dot, path } = animationElements;\n        const duration = this.config.animationDuration / this.animationSpeed;\n        \n        // パスアニメーション\n        const pathLength = pathElement.getTotalLength();\n        pathElement.setAttribute('stroke-dasharray', pathLength);\n        pathElement.setAttribute('stroke-dashoffset', pathLength);\n        \n        // CSS アニメーション\n        pathElement.style.animation = `drawPath ${duration}ms ease-out forwards`;\n        \n        // ドット移動アニメーション\n        let startTime = null;\n        \n        const animateDot = (timestamp) => {\n            if (!startTime) startTime = timestamp;\n            \n            const progress = Math.min((timestamp - startTime) / duration, 1);\n            const point = this.getPointAtProgress(path, progress);\n            \n            dot.setAttribute('cx', point.x);\n            dot.setAttribute('cy', point.y);\n            \n            if (progress < 1) {\n                requestAnimationFrame(animateDot);\n            } else {\n                // アニメーション完了\n                setTimeout(() => {\n                    if (group.parentNode) {\n                        group.parentNode.removeChild(group);\n                    }\n                }, 500); // 0.5秒後に削除\n            }\n        };\n        \n        requestAnimationFrame(animateDot);\n        \n        // アクティブアニメーション追跡\n        this.activeAnimations.push({\n            group,\n            startTime: Date.now(),\n            duration,\n            messageData\n        });\n    }\n    \n    // パス上の点を取得\n    getPointAtProgress(path, progress) {\n        // ベジェ曲線上の点を計算\n        const t = progress;\n        const x = Math.pow(1 - t, 2) * path.startX + \n                 2 * (1 - t) * t * path.controlX + \n                 Math.pow(t, 2) * path.endX;\n        const y = Math.pow(1 - t, 2) * path.startY + \n                 2 * (1 - t) * t * path.controlY + \n                 Math.pow(t, 2) * path.endY;\n        \n        return { x, y };\n    }\n    \n    // Worker活動状態更新\n    updateWorkerActivity(sourceNode, targetNode, messageType) {\n        // 送信側のアクティビティ表示\n        this.showWorkerActivity(sourceNode, 'sending');\n        \n        // 受信側のアクティビティ表示（少し遅延）\n        setTimeout(() => {\n            this.showWorkerActivity(targetNode, 'receiving');\n        }, 500);\n    }\n    \n    // Worker活動表示\n    showWorkerActivity(workerNode, activity) {\n        const ring = workerNode.activityRing;\n        const circle = workerNode.circle;\n        \n        // アクティビティリング表示\n        ring.setAttribute('opacity', '0.8');\n        \n        // 色設定\n        const color = activity === 'sending' ? '#f39c12' : '#27ae60';\n        ring.setAttribute('stroke', color);\n        circle.setAttribute('stroke', color);\n        \n        // パルスアニメーション\n        ring.style.animation = 'pulse 1s ease-out';\n        \n        // 1秒後にリセット\n        setTimeout(() => {\n            ring.setAttribute('opacity', '0');\n            circle.setAttribute('stroke', '#666666');\n            ring.style.animation = '';\n        }, 1000);\n    }\n    \n    // Worker状態更新\n    updateWorkerStatus(workerName, status) {\n        const worker = this.workerNodes[workerName];\n        if (!worker) return;\n        \n        worker.status = status;\n        const circle = worker.circle;\n        \n        // 状態に応じた色設定\n        const statusColors = {\n            'active': '#27ae60',\n            'working': '#f39c12',\n            'idle': '#666666',\n            'inactive': '#444444',\n            'error': '#e74c3c'\n        };\n        \n        circle.setAttribute('fill', statusColors[status] || statusColors.idle);\n    }\n    \n    // 再生/一時停止切り替え\n    togglePlayPause() {\n        this.isPlaying = !this.isPlaying;\n        const btn = document.getElementById('flow-play-pause');\n        \n        if (btn) {\n            btn.textContent = this.isPlaying ? '⏸️ Pause' : '▶️ Play';\n        }\n        \n        console.log(`📊 Flow visualization ${this.isPlaying ? 'resumed' : 'paused'}`);\n    }\n    \n    // フロークリア\n    clearFlow() {\n        // 全てのメッセージアニメーションを削除\n        const messageAnimations = this.svg.querySelectorAll('.message-animation');\n        messageAnimations.forEach(element => {\n            element.remove();\n        });\n        \n        this.messageQueue = [];\n        this.activeAnimations = [];\n        \n        console.log('🗑️  Flow visualization cleared');\n    }\n    \n    // 破棄\n    destroy() {\n        this.clearFlow();\n        this.workerNodes = {};\n    }\n}\n\n// CSS アニメーション定義\nconst style = document.createElement('style');\nstyle.textContent = `\n    @keyframes drawPath {\n        to {\n            stroke-dashoffset: 0;\n        }\n    }\n    \n    @keyframes pulse {\n        0% { \n            transform: scale(1);\n            opacity: 0.8;\n        }\n        50% { \n            transform: scale(1.1);\n            opacity: 1;\n        }\n        100% { \n            transform: scale(1);\n            opacity: 0.8;\n        }\n    }\n    \n    .worker-node {\n        cursor: pointer;\n        transition: all 0.3s ease;\n    }\n    \n    .worker-node:hover .worker-circle {\n        stroke-width: 3;\n        filter: brightness(1.2);\n    }\n    \n    .message-animation {\n        pointer-events: none;\n    }\n`;\ndocument.head.appendChild(style);