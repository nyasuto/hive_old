#!/bin/bash

# shutdown-hive.sh - Hive終了スクリプト
# Issue #3 - tmuxベースSmall Colony (2 Workers)システム

set -euo pipefail

# 設定
HIVE_SESSION="hive-small-colony"
HIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$HIVE_DIR/.hive/logs"
HONEY_DIR="$HIVE_DIR/.hive/honey"

# 色付きログ関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

log_step() {
    echo -e "\033[36m[STEP]\033[0m $1"
}

# ヘルプメッセージ
show_help() {
    cat << EOF
🛑 Hive Shutdown Script

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    -f, --force         Force shutdown without confirmation
    -k, --kill          Kill session immediately (no graceful shutdown)
    -c, --collect       Collect honey before shutdown
    -s, --save-logs     Save logs before shutdown
    -q, --quiet         Quiet mode (minimal output)

EXAMPLES:
    $0                  # Interactive shutdown with confirmation
    $0 --force          # Force shutdown without confirmation
    $0 --collect        # Collect honey before shutdown
    $0 --force --collect # Force shutdown with honey collection

DESCRIPTION:
    This script safely terminates the Hive Small Colony session,
    optionally collecting results and saving logs before shutdown.

EOF
}

# 引数解析
FORCE_SHUTDOWN=false
KILL_SESSION=false
COLLECT_HONEY=false
SAVE_LOGS=false
QUIET_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--force)
            FORCE_SHUTDOWN=true
            shift
            ;;
        -k|--kill)
            KILL_SESSION=true
            shift
            ;;
        -c|--collect)
            COLLECT_HONEY=true
            shift
            ;;
        -s|--save-logs)
            SAVE_LOGS=true
            shift
            ;;
        -q|--quiet)
            QUIET_MODE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# セッション存在チェック
check_session_exists() {
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_step "Checking for active Hive session..."
    fi
    
    if ! tmux has-session -t "$HIVE_SESSION" 2>/dev/null; then
        if [[ "$QUIET_MODE" == "false" ]]; then
            log_warn "No active Hive session found"
        fi
        exit 0
    fi
    
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_info "Active session found: $HIVE_SESSION"
    fi
}

# セッション情報の表示
show_session_info() {
    if [[ "$QUIET_MODE" == "true" ]]; then
        return
    fi
    
    log_step "Current session information:"
    
    # セッションの基本情報
    tmux display-message -t "$HIVE_SESSION" -p "Session: #S, Windows: #{session_windows}, Created: #{session_created}"
    
    # pane情報
    echo "Active panes:"
    tmux list-panes -t "$HIVE_SESSION" -F "  - Pane #{pane_index}: #{pane_title} (#{pane_width}x#{pane_height})"
    
    # 実行中のプロセス
    echo "Running processes:"
    tmux list-panes -t "$HIVE_SESSION" -F "  - Pane #{pane_index}: #{pane_current_command}"
}

# 確認プロンプト
confirm_shutdown() {
    if [[ "$FORCE_SHUTDOWN" == "true" ]]; then
        return 0
    fi
    
    echo
    echo "🛑 Are you sure you want to shutdown the Hive Small Colony?"
    echo "   This will terminate all workers and end the session."
    echo
    
    read -p "Proceed with shutdown? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Shutdown cancelled by user"
        exit 0
    fi
}

# Honey収集
collect_honey() {
    if [[ "$COLLECT_HONEY" == "false" ]]; then
        return
    fi
    
    log_step "Collecting honey before shutdown..."
    
    # Honey収集スクリプトの実行
    if [[ -f "$HIVE_DIR/scripts/collect-honey.sh" ]]; then
        "$HIVE_DIR/scripts/collect-honey.sh" --quiet
    else
        log_warn "Honey collection script not found"
        
        # 基本的なHoney収集
        local honey_backup="$HONEY_DIR/shutdown-$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$honey_backup"
        
        # 各Workerのタスク完了情報を収集
        python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from comb import CombAPI
import json

# 各WorkerのAPIを初期化
workers = ['queen', 'developer']
honey_data = {}

for worker in workers:
    try:
        api = CombAPI(worker)
        
        # 現在のタスク情報
        current_task = api.get_current_task()
        if current_task:
            honey_data[f'{worker}_current_task'] = current_task
        
        # ステータス情報
        status = api.get_status()
        honey_data[f'{worker}_status'] = status
        
        # 日次サマリー生成
        api.generate_daily_summary()
        
    except Exception as e:
        honey_data[f'{worker}_error'] = str(e)

# Honey保存
with open('$honey_backup/final_status.json', 'w') as f:
    json.dump(honey_data, f, indent=2, ensure_ascii=False)

print('Honey collected successfully')
"
    fi
    
    log_info "Honey collection completed"
}

# ログの保存
save_logs() {
    if [[ "$SAVE_LOGS" == "false" ]]; then
        return
    fi
    
    log_step "Saving logs before shutdown..."
    
    local log_backup="$LOG_DIR/shutdown-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$log_backup"
    
    # tmux paneのhistoryを保存
    tmux list-panes -t "$HIVE_SESSION" -F "#{pane_index}" | while read -r pane; do
        local pane_title
        pane_title=$(tmux display-message -t "$HIVE_SESSION:0.$pane" -p "#{pane_title}")
        
        # paneのhistoryを保存
        tmux capture-pane -t "$HIVE_SESSION:0.$pane" -p > "$log_backup/pane_${pane}_${pane_title}.log"
    done
    
    # 現在のログファイルをバックアップ
    if [[ -d "$LOG_DIR" ]]; then
        find "$LOG_DIR" -name "*.log" -mtime -1 -exec cp {} "$log_backup/" \;
    fi
    
    log_info "Logs saved to: $log_backup"
}

# Workerの優雅な終了
graceful_worker_shutdown() {
    if [[ "$KILL_SESSION" == "true" ]]; then
        return
    fi
    
    log_step "Sending shutdown signal to workers..."
    
    # 各paneにCtrl+Cを送信
    tmux list-panes -t "$HIVE_SESSION" -F "#{pane_index}" | while read -r pane; do
        # Claude Codeセッションの終了
        tmux send-keys -t "$HIVE_SESSION:0.$pane" C-c
        sleep 1
        tmux send-keys -t "$HIVE_SESSION:0.$pane" "exit" Enter
    done
    
    # 少し待機
    sleep 2
    
    log_info "Graceful shutdown signals sent"
}

# セッションの終了
terminate_session() {
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_step "Terminating tmux session..."
    fi
    
    if [[ "$KILL_SESSION" == "true" ]]; then
        # 即座に終了
        tmux kill-session -t "$HIVE_SESSION"
        log_info "Session killed immediately"
    else
        # 優雅な終了
        graceful_worker_shutdown
        
        # セッションがまだ存在する場合は強制終了
        if tmux has-session -t "$HIVE_SESSION" 2>/dev/null; then
            tmux kill-session -t "$HIVE_SESSION"
        fi
        
        log_info "Session terminated gracefully"
    fi
}

# 終了後のクリーンアップ
cleanup() {
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_step "Performing cleanup..."
    fi
    
    # 一時ファイルのクリーンアップ
    if [[ -d "$HIVE_DIR/.hive/tmp" ]]; then
        rm -rf "$HIVE_DIR/.hive/tmp"
    fi
    
    # 古いログファイルのクリーンアップ（7日以上古いもの）
    if [[ -d "$LOG_DIR" ]]; then
        find "$LOG_DIR" -name "*.log" -mtime +7 -delete 2>/dev/null || true
    fi
    
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_info "Cleanup completed"
    fi
}

# シャットダウン統計の表示
show_shutdown_stats() {
    if [[ "$QUIET_MODE" == "true" ]]; then
        return
    fi
    
    log_step "Shutdown statistics:"
    
    # セッション実行時間の計算
    local session_duration="unknown"
    if [[ -f "$LOG_DIR/session_start_time" ]]; then
        local start_time
        start_time=$(cat "$LOG_DIR/session_start_time")
        local end_time
        end_time=$(date +%s)
        local duration=$((end_time - start_time))
        session_duration="${duration}s"
    fi
    
    echo "  - Session duration: $session_duration"
    
    # ファイル統計
    if [[ -d "$HONEY_DIR" ]]; then
        local honey_files
        honey_files=$(find "$HONEY_DIR" -name "*.json" | wc -l)
        echo "  - Honey files collected: $honey_files"
    fi
    
    if [[ -d "$LOG_DIR" ]]; then
        local log_files
        log_files=$(find "$LOG_DIR" -name "*.log" | wc -l)
        echo "  - Log files: $log_files"
    fi
}

# 使用方法の表示
show_restart_instructions() {
    if [[ "$QUIET_MODE" == "true" ]]; then
        return
    fi
    
    echo
    echo "🔄 To restart the Hive Small Colony:"
    echo "   ./scripts/start-small-hive.sh"
    echo
    echo "🔧 To check if any sessions are still running:"
    echo "   tmux list-sessions"
    echo
    echo "📊 To view collected honey:"
    echo "   ls -la $HONEY_DIR"
    echo
    echo "📝 To view logs:"
    echo "   ls -la $LOG_DIR"
    echo
}

# エラーハンドリング
handle_error() {
    local exit_code=$?
    log_error "Shutdown failed with exit code: $exit_code"
    
    # 緊急時のセッション強制終了
    if tmux has-session -t "$HIVE_SESSION" 2>/dev/null; then
        log_warn "Attempting emergency session termination..."
        tmux kill-session -t "$HIVE_SESSION" 2>/dev/null || true
    fi
    
    exit "$exit_code"
}

# メイン実行フロー
main() {
    # エラーハンドリング設定
    trap handle_error ERR
    
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_info "🛑 Initiating Hive Small Colony shutdown..."
    fi
    
    # 実行フロー
    check_session_exists
    show_session_info
    confirm_shutdown
    collect_honey
    save_logs
    terminate_session
    cleanup
    show_shutdown_stats
    show_restart_instructions
    
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_info "🎉 Hive Small Colony shutdown completed successfully!"
    fi
}

# セッション開始時刻の記録（起動時のみ）
if [[ "${1:-}" == "--record-start" ]]; then
    mkdir -p "$LOG_DIR"
    date +%s > "$LOG_DIR/session_start_time"
    exit 0
fi

# メイン処理実行
main "$@"