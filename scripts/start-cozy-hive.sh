#!/bin/bash

# Hive分散システム起動スクリプト
# Issue #96: tmux統合基盤システム

set -e

SESSION_NAME="cozy-hive"
BASE_DIR="/Users/yast/git/hive"
CONFIG_FILE="$BASE_DIR/config/tmux_config.yaml"

echo "🐝 Starting Cozy Hive System..."

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

echo "📋 Loading role templates..."
# 全Workerにroleテンプレートを並列ロード
for worker in "${WORKERS[@]}"; do
    echo "📝 Loading $worker role template..."
    
    # ファイル内容をスクリプト内で読み込み変数に格納
    if [[ -f "$BASE_DIR/templates/roles/$worker.md" ]]; then
        role_content=$(cat "$BASE_DIR/templates/roles/$worker.md")
        echo "  └─ Template size: $(echo "$role_content" | wc -c) characters"
        
        # テンプレート内容を明示的な指示付きで送信
        instruction_text="以下があなたの役割です。理解して実行してください：
        $role_content
        "
        
        tmux send-keys -t "$SESSION_NAME:$worker" "$instruction_text" Enter 
        Sleep 1
        tmux send-keys -t "$SESSION_NAME:$worker"  Enter 

    else
        echo "⚠️  Warning: Role template not found for $worker"
        tmux send-keys -t "$SESSION_NAME:$worker" "echo 'Role template not found for $worker'" Enter
        sleep 1
    fi
done

# ロード完了を待機
echo "⏳ Waiting for role templates to load..."
sleep 5

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
echo ""
echo "🛑 To stop the cozy system:"
echo "  ./scripts/stop-cozy-hive.sh"

# セッションにアタッチ
tmux attach-session -t "$SESSION_NAME"