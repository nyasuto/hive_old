#!/bin/bash

# Hive分散システム停止スクリプト
# Issue #96: tmux統合基盤システム

set -e

SESSION_NAME="hive"

echo "🛑 Stopping Hive Distributed System..."

# セッションの存在チェック
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "⚠️  Session '$SESSION_NAME' does not exist"
    exit 0
fi

# 確認プロンプト
echo "📋 Current session status:"
tmux list-sessions | grep "$SESSION_NAME" || echo "No sessions found"

read -p "Are you sure you want to stop the Hive system? (y/N): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Operation cancelled"
    exit 0
fi

echo "🔄 Shutting down Hive components..."

# 各paneに終了メッセージを送信
if tmux list-windows -t "$SESSION_NAME" | grep -q "beekeeper"; then
    echo "  🐝 Stopping BeeKeeper..."
    tmux send-keys -t "$SESSION_NAME:beekeeper" "echo 'BeeKeeper shutting down...'" C-m
fi

if tmux list-windows -t "$SESSION_NAME" | grep -q "queen"; then
    echo "  👑 Stopping Queen..."
    tmux send-keys -t "$SESSION_NAME:queen" "echo 'Queen shutting down...'" C-m
fi

if tmux list-windows -t "$SESSION_NAME" | grep -q "developer1"; then
    echo "  👨‍💻 Stopping Developer1..."
    tmux send-keys -t "$SESSION_NAME:developer1" "echo 'Developer1 shutting down...'" C-m
fi

# 短い待機
sleep 2

# セッションを終了
echo "🔥 Killing tmux session..."
tmux kill-session -t "$SESSION_NAME"

echo "✅ Hive Distributed System stopped successfully!"
echo ""
echo "🔄 To restart:"
echo "  ./scripts/start_hive_distributed.sh"