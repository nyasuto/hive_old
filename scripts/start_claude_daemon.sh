#!/bin/bash

# Claude Code永続デーモン起動スクリプト
# Issue #97: Claude Code永続デーモン統合

set -e

SESSION_NAME="hive"
BASE_DIR="/Users/yast/git/hive"
CONFIG_FILE="$BASE_DIR/config/claude_config.yaml"
LOG_FILE="$BASE_DIR/logs/claude_daemon.log"

echo "🤖 Starting Claude Code Daemons..."

# ログディレクトリ作成
mkdir -p "$BASE_DIR/logs"

# セッションの存在確認
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "❌ Tmux session '$SESSION_NAME' not found"
    echo "Please run './scripts/start_hive_distributed.sh' first"
    exit 1
fi

# 設定ファイルの確認
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

# 関数: paneでClaude Codeデーモンを起動
start_claude_in_pane() {
    local pane_name=$1
    local delay=$2
    
    echo "🚀 Starting Claude daemon in $pane_name (delay: ${delay}s)..."
    
    # paneの存在確認
    if ! tmux list-windows -t "$SESSION_NAME" | grep -q "$pane_name"; then
        echo "⚠️  Pane '$pane_name' not found, skipping..."
        return 1
    fi
    
    # 初期化メッセージ
    tmux send-keys -t "$SESSION_NAME:$pane_name" "echo '🤖 Starting Claude Code daemon...'" C-m
    
    # 遅延
    sleep "$delay"
    
    # Claude Codeデーモンを起動
    tmux send-keys -t "$SESSION_NAME:$pane_name" "claude --dangerously-skip-permissions" C-m
    
    # 起動完了を待機
    echo "⏳ Waiting for Claude daemon startup in $pane_name..."
    sleep 5
    
    # 起動確認メッセージ
    tmux send-keys -t "$SESSION_NAME:$pane_name" "echo '✅ Claude daemon ready in $pane_name'" C-m
    
    echo "✅ Claude daemon started in $pane_name"
}

# 関数: paneの健康状態チェック
check_pane_health() {
    local pane_name=$1
    
    echo "🔍 Checking health of $pane_name..."
    
    # paneの内容を取得
    content=$(tmux capture-pane -t "$SESSION_NAME:$pane_name" -p -S -5 2>/dev/null || echo "")
    
    if echo "$content" | grep -q -E "(claude|Assistant|Human|>)"; then
        echo "✅ $pane_name is healthy"
        return 0
    else
        echo "⚠️  $pane_name may not be responding properly"
        return 1
    fi
}

# メイン処理
main() {
    echo "📋 Claude daemon startup sequence:"
    echo "  1. Queen pane (high priority)"
    echo "  2. Developer1 pane (medium priority)"
    echo ""
    
    # Queen paneでClaude起動
    if start_claude_in_pane "queen" 5; then
        echo "👑 Queen Claude daemon started"
    else
        echo "❌ Failed to start Queen Claude daemon"
        exit 1
    fi
    
    # Developer1 paneでClaude起動
    if start_claude_in_pane "developer1" 8; then
        echo "👨‍💻 Developer1 Claude daemon started"
    else
        echo "❌ Failed to start Developer1 Claude daemon"
        exit 1
    fi
    
    # 起動完了後の健康状態チェック
    echo ""
    echo "🔍 Performing health checks..."
    
    sleep 3
    
    check_pane_health "queen"
    check_pane_health "developer1"
    
    echo ""
    echo "🎉 Claude daemon startup completed!"
    echo ""
    echo "📋 Daemon status:"
    echo "  👑 Queen:      Running ($(tmux display-message -t "$SESSION_NAME:queen" -p "#{pane_active}" 2>/dev/null || echo "unknown"))"
    echo "  👨‍💻 Developer1: Running ($(tmux display-message -t "$SESSION_NAME:developer1" -p "#{pane_active}" 2>/dev/null || echo "unknown"))"
    echo ""
    echo "🔗 To interact with daemons:"
    echo "  tmux attach-session -t $SESSION_NAME"
    echo "  # Then switch to desired pane with Ctrl+b + [0-2]"
    echo ""
    echo "🛑 To stop daemons:"
    echo "  ./scripts/stop_claude_daemon.sh"
    echo ""
    echo "📊 Monitor logs:"
    echo "  tail -f $LOG_FILE"
}

# エラーハンドリング
trap 'echo "❌ Script interrupted"; exit 1' INT TERM

# 実行
main "$@"