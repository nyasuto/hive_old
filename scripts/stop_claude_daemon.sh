#!/bin/bash

# Claude Code永続デーモン停止スクリプト
# Issue #97: Claude Code永続デーモン統合

set -e

SESSION_NAME="hive"
BASE_DIR="/Users/yast/git/hive"

echo "🛑 Stopping Claude Code Daemons..."

# セッションの存在確認
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "⚠️  Tmux session '$SESSION_NAME' not found"
    echo "Daemons may already be stopped"
    exit 0
fi

# 関数: paneのClaude Codeデーモンを停止
stop_claude_in_pane() {
    local pane_name=$1
    
    echo "🔄 Stopping Claude daemon in $pane_name..."
    
    # paneの存在確認
    if ! tmux list-windows -t "$SESSION_NAME" | grep -q "$pane_name"; then
        echo "⚠️  Pane '$pane_name' not found, skipping..."
        return 0
    fi
    
    # 停止メッセージ
    tmux send-keys -t "$SESSION_NAME:$pane_name" "echo '🛑 Stopping Claude daemon...'" C-m
    
    # 優雅な終了を試行
    echo "  📤 Sending exit command to $pane_name..."
    tmux send-keys -t "$SESSION_NAME:$pane_name" "exit" C-m
    
    # 少し待機
    sleep 2
    
    # 強制終了 (Ctrl+C)
    echo "  ⚡ Sending interrupt signal to $pane_name..."
    tmux send-keys -t "$SESSION_NAME:$pane_name" C-c
    
    # さらに待機
    sleep 1
    
    # 強制終了 (Ctrl+D)
    echo "  🔚 Sending EOF signal to $pane_name..."
    tmux send-keys -t "$SESSION_NAME:$pane_name" C-d
    
    # 最終確認
    sleep 1
    
    # paneをクリア
    tmux send-keys -t "$SESSION_NAME:$pane_name" "clear" C-m
    
    echo "✅ Claude daemon stopped in $pane_name"
}

# 関数: paneの停止確認
verify_pane_stopped() {
    local pane_name=$1
    
    echo "🔍 Verifying $pane_name is stopped..."
    
    # paneの内容を取得
    content=$(tmux capture-pane -t "$SESSION_NAME:$pane_name" -p -S -3 2>/dev/null || echo "")
    
    if echo "$content" | grep -q -E "(claude|Assistant|Human)"; then
        echo "⚠️  $pane_name may still be running Claude"
        return 1
    else
        echo "✅ $pane_name appears to be stopped"
        return 0
    fi
}

# 関数: 強制停止（必要に応じて）
force_stop_pane() {
    local pane_name=$1
    
    echo "⚡ Force stopping $pane_name..."
    
    # 複数回のCtrl+C
    for i in {1..3}; do
        tmux send-keys -t "$SESSION_NAME:$pane_name" C-c
        sleep 0.5
    done
    
    # killコマンドを試行
    tmux send-keys -t "$SESSION_NAME:$pane_name" "pkill -f claude" C-m
    sleep 1
    
    # paneをリセット
    tmux send-keys -t "$SESSION_NAME:$pane_name" "reset" C-m
    
    echo "🔄 Force stop completed for $pane_name"
}

# メイン処理
main() {
    echo "📋 Claude daemon shutdown sequence:"
    echo "  1. Developer1 pane"
    echo "  2. Queen pane"
    echo "  3. Verification"
    echo ""
    
    # Developer1 paneのClaude停止
    stop_claude_in_pane "developer1"
    
    # Queen paneのClaude停止
    stop_claude_in_pane "queen"
    
    # 停止確認
    echo ""
    echo "🔍 Verifying daemon shutdown..."
    
    sleep 2
    
    # 各paneの停止確認
    declare -a failed_panes=()
    
    if ! verify_pane_stopped "developer1"; then
        failed_panes+=("developer1")
    fi
    
    if ! verify_pane_stopped "queen"; then
        failed_panes+=("queen")
    fi
    
    # 強制停止が必要な場合
    if [ ${#failed_panes[@]} -gt 0 ]; then
        echo ""
        echo "⚠️  Some daemons may still be running. Attempting force stop..."
        
        for pane in "${failed_panes[@]}"; do
            force_stop_pane "$pane"
        done
        
        # 最終確認
        sleep 2
        echo ""
        echo "🔍 Final verification..."
        
        for pane in "${failed_panes[@]}"; do
            verify_pane_stopped "$pane"
        done
    fi
    
    echo ""
    echo "✅ Claude daemon shutdown completed!"
    echo ""
    echo "📋 Final status:"
    echo "  👑 Queen:      Stopped"
    echo "  👨‍💻 Developer1: Stopped"
    echo ""
    echo "🔄 To restart daemons:"
    echo "  ./scripts/start_claude_daemon.sh"
    echo ""
    echo "🛑 To stop the entire Hive system:"
    echo "  ./scripts/stop_hive_distributed.sh"
}

# エラーハンドリング
trap 'echo "❌ Shutdown script interrupted"; exit 1' INT TERM

# 実行
main "$@"