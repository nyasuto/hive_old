#!/bin/bash

# Hive分散システム起動スクリプト
# Issue #96: tmux統合基盤システム

set -e

SESSION_NAME="hive"
BASE_DIR="/Users/yast/git/hive"
CONFIG_FILE="$BASE_DIR/config/tmux_config.yaml"

echo "🐝 Starting Hive Distributed System..."

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

# 短い待機
sleep 2

# Queenウィンドウを作成
echo "👑 Creating Queen pane..."
tmux new-window -t "$SESSION_NAME:1" -n "queen" -c "$BASE_DIR"
tmux send-keys -t "$SESSION_NAME:queen" "echo '👑 Queen Pane Initialized'" C-m
tmux send-keys -t "$SESSION_NAME:queen" "echo 'Ready to manage tasks and coordinate workers...'" C-m

# 短い待機
sleep 3

# Developer1ウィンドウを作成
echo "👨‍💻 Creating Developer1 pane..."
tmux new-window -t "$SESSION_NAME:2" -n "developer1" -c "$BASE_DIR"
tmux send-keys -t "$SESSION_NAME:developer1" "echo '👨‍💻 Developer1 Pane Initialized'" C-m
tmux send-keys -t "$SESSION_NAME:developer1" "echo 'Ready to execute tasks...'" C-m

# 短い待機
sleep 3

# BeeKeeperウィンドウに戻る
tmux select-window -t "$SESSION_NAME:beekeeper"

echo "✅ Hive Distributed System started successfully!"
echo ""
echo "📋 Available panes:"
echo "  - beekeeper  (window 0) - User request handling"
echo "  - queen      (window 1) - Task management"
echo "  - developer1 (window 2) - Code execution"
echo ""
echo "🔗 To attach to the session:"
echo "  tmux attach-session -t $SESSION_NAME"
echo ""
echo "🔄 To switch between panes:"
echo "  Ctrl+b + 0  (BeeKeeper)"
echo "  Ctrl+b + 1  (Queen)"
echo "  Ctrl+b + 2  (Developer1)"
echo ""
echo "🛑 To stop the system:"
echo "  ./scripts/stop_hive_distributed.sh"

# セッションにアタッチ
tmux attach-session -t "$SESSION_NAME"