#!/bin/bash

# Hive分散システム起動スクリプト
# Issue #96: tmux統合基盤システム
# Issue #125: Hive Watch監視システム統合

set -e

SESSION_NAME="cozy-hive"
BASE_DIR="/Users/yast/git/hive"
CONFIG_FILE="$BASE_DIR/config/tmux_config.yaml"

# オプション解析
ENABLE_WATCH=true
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-watch)
            ENABLE_WATCH=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --no-watch    Hive Watch監視を無効化"
            echo "  -h, --help    ヘルプを表示"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo "🐝 Starting Cozy Hive System..."
if [[ "$ENABLE_WATCH" == "true" ]]; then
    echo "⌚ Hive Watch monitoring enabled"
else
    echo "⌚ Hive Watch monitoring disabled"
fi

# 既存セッションをチェック
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "⚠️  Session '$SESSION_NAME' already exists"
    read -p "Do you want to kill it and restart? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Killing existing session..."
        tmux kill-session -t "$SESSION_NAME"
    else
        echo "📋 Attaching to existing session..."
        tmux attach-session -t "$SESSION_NAME"
        exit 0
    fi
fi

# 作業ディレクトリに移動
cd "$BASE_DIR"

echo "🔧 Creating tmux session: $SESSION_NAME"

# BeeKeeperウィンドウでセッション作成
tmux new-session -d -s "$SESSION_NAME" -n "beekeeper" -c "$BASE_DIR"

# 初期化メッセージ
tmux send-keys -t "$SESSION_NAME:beekeeper" "echo '🐝 BeeKeeper Pane Initialized'" C-m
tmux send-keys -t "$SESSION_NAME:beekeeper" "echo 'Ready to receive user requests...'" C-m

# Worker定義配列
declare -a WORKERS=("queen" "developer" "tester" "analyzer" "documenter" "reviewer")
declare -a WORKER_EMOJIS=("👑" "👨‍💻" "🧪" "🔍" "📝" "👀")
declare -a WORKER_NAMES=("Queen" "Developer" "Tester" "Analyzer" "Documenter" "Reviewer")

echo "🚀 Creating all workers in parallel..."

# 全Workerを並列で作成・起動
for i in "${!WORKERS[@]}"; do
    worker="${WORKERS[i]}"
    emoji="${WORKER_EMOJIS[i]}"
    name="${WORKER_NAMES[i]}"
    window_num=$((i + 1))
    
    echo "$emoji Creating $name pane..."
    
    # tmuxウィンドウ作成
    tmux new-window -t "$SESSION_NAME:$window_num" -n "$worker" -c "$BASE_DIR"
    
    # 初期化メッセージ
    tmux send-keys -t "$SESSION_NAME:$worker" "echo '$emoji $name Worker Initialized'" C-m
    tmux send-keys -t "$SESSION_NAME:$worker" "echo 'Starting Claude Code daemon...'" C-m
    
    # Claude起動（バックグラウンドで並列実行）
    # C-mを2回送信してClaude Codeでの確実な起動
    tmux send-keys -t "$SESSION_NAME:$worker" "claude --dangerously-skip-permissions" C-m
done

echo "⏳ Waiting for all Claude instances to initialize (20 seconds)..."
sleep 20

echo "📋 Loading role templates via Hive CLI..."
# 全Workerにroleテンプレートを並列ロード（hive_cli使用）
for worker in "${WORKERS[@]}"; do
    echo "📝 Loading $worker role template..."
    
    # ファイル内容をスクリプト内で読み込み変数に格納
    if [[ -f "$BASE_DIR/templates/roles/$worker.md" ]]; then
        role_content=$(cat "$BASE_DIR/templates/roles/$worker.md")
        echo "  └─ Template size: $(echo "$role_content" | wc -c) characters"
        
        # hive_cli経由でroleテンプレートを送信
        instruction_text="以下があなたの役割です。理解して実行してください：

$role_content

これで役割の理解は完了です。今後はhive_cli.pyを使ってメッセージパッシングを行ってください。"
        
        # hive_cli経由で送信（確実な配信）
        python3 "$BASE_DIR/scripts/hive_cli.py" send "$worker" "$instruction_text" --type direct --no-wait
        
        echo "  ✅ Role template sent to $worker via hive_cli"
        sleep 1

    else
        echo "⚠️  Warning: Role template not found for $worker"
        python3 "$BASE_DIR/scripts/hive_cli.py" send "$worker" "⚠️ Role template not found for $worker. Please request your role definition." --type direct --no-wait
        sleep 1
    fi
done

# ロード完了を待機
echo "⏳ Waiting for role templates to load..."
sleep 5

# Hive Watch監視システム起動
if [[ "$ENABLE_WATCH" == "true" ]]; then
    echo "⌚ Starting Hive Watch monitoring system..."
    
    # Hive Watch専用ウィンドウ作成
    tmux new-window -t "$SESSION_NAME:7" -n "hive-watch" -c "$BASE_DIR"
    
    # Hive Watch初期化
    tmux send-keys -t "$SESSION_NAME:hive-watch" "echo '⌚ Hive Watch - リアルタイム監視システム'" C-m
    tmux send-keys -t "$SESSION_NAME:hive-watch" "echo '📊 監視対象: hive_cli.py + worker_communication.py 統合通信'" C-m
    tmux send-keys -t "$SESSION_NAME:hive-watch" "echo '🔗 通信方式: Worker→hive_cli→tmux→Worker (透過監視)'" C-m
    tmux send-keys -t "$SESSION_NAME:hive-watch" "echo '⏱️  監視間隔: 2秒'" C-m
    tmux send-keys -t "$SESSION_NAME:hive-watch" "echo '🚀 Starting monitoring...'" C-m
    tmux send-keys -t "$SESSION_NAME:hive-watch" "" C-m
    
    # Python監視システム起動
    tmux send-keys -t "$SESSION_NAME:hive-watch" "python3 scripts/hive_watch.py --monitor --interval 2.0" C-m
    
    echo "✅ Hive Watch started on window 7 (hive_cli integrated monitoring)"
    sleep 2
fi

# BeeKeeperウィンドウに戻る
tmux select-window -t "$SESSION_NAME:beekeeper"

echo "✅ Cozy Hive System started successfully!"
echo ""
echo "📋 Available panes:"
echo "  - beekeeper  (window 0) - User request handling"
echo "  - queen      (window 1) - Task management and coordination"
echo "  - developer  (window 2) - Development tasks"
echo "  - tester     (window 3) - Testing and quality assurance"
echo "  - analyzer   (window 4) - Analysis and investigation"
echo "  - documenter (window 5) - Documentation creation"
echo "  - reviewer   (window 6) - Code review and validation"
if [[ "$ENABLE_WATCH" == "true" ]]; then
    echo "  - hive-watch (window 7) - Real-time monitoring system ⌚"
fi
echo ""
echo "🔗 To attach to the cozy session:"
echo "  tmux attach-session -t $SESSION_NAME"
echo ""
echo "🔄 To switch between panes:"
echo "  Ctrl+b + 0  (BeeKeeper)"
echo "  Ctrl+b + 1  (Queen)"
echo "  Ctrl+b + 2  (Developer)"
echo "  Ctrl+b + 3  (Tester)"
echo "  Ctrl+b + 4  (Analyzer)"
echo "  Ctrl+b + 5  (Documenter)"
echo "  Ctrl+b + 6  (Reviewer)"
if [[ "$ENABLE_WATCH" == "true" ]]; then
    echo "  Ctrl+b + 7  (Hive Watch) ⌚"
fi
echo ""
echo "🔄 Hive CLI Commands (Worker Communication):"
echo "  - Send message: python3 scripts/hive_cli.py send [worker] '[message]'"
echo "  - Check status: python3 scripts/hive_cli.py status"
echo "  - View history: python3 scripts/hive_cli.py history [worker]"
echo ""
if [[ "$ENABLE_WATCH" == "true" ]]; then
    echo "⌚ Hive Watch Commands (Monitoring):"
    echo "  - View logs: python3 scripts/hive_watch.py --log"
    echo "  - Manual monitoring: python3 scripts/hive_watch.py --monitor"
    echo ""
fi
echo "🛑 To stop the cozy system:"
echo "  ./scripts/stop-cozy-hive.sh"
echo ""
echo "💡 Pro tip: Use 'Ctrl+b + 7' to quickly check Hive Watch monitoring!"

# セッションにアタッチ
tmux attach-session -t "$SESSION_NAME"