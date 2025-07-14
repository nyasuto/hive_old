#!/bin/bash

# wake-workers.sh - Worker起動管理スクリプト
# Issue #3 - tmuxベースSmall Colony (2 Workers)システム

set -euo pipefail

# 設定
HIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKERS_DIR="$HIVE_DIR/workers"
PROMPTS_DIR="$WORKERS_DIR/prompts"
COMB_DIR="$HIVE_DIR/.hive"
LOG_DIR="$HIVE_DIR/.hive/logs"

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
🔄 Hive Worker Startup Script

Usage: $0 WORKER_TYPE [OPTIONS]

WORKER_TYPE:
    queen       Start Queen Worker (project management)
    developer   Start Developer Worker (implementation)

OPTIONS:
    -h, --help      Show this help message
    -d, --debug     Enable debug mode
    -q, --quiet     Quiet mode (minimal output)

EXAMPLES:
    $0 queen        # Start Queen Worker
    $0 developer    # Start Developer Worker
    $0 queen --debug # Start Queen Worker with debug output

DESCRIPTION:
    This script initializes and starts individual workers with their
    specialized prompts and Comb communication capabilities.

EOF
}

# 引数解析
if [[ $# -eq 0 ]]; then
    log_error "Worker type required"
    show_help
    exit 1
fi

WORKER_TYPE="$1"
shift

DEBUG_MODE=false
QUIET_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--debug)
            DEBUG_MODE=true
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

# デバッグモード設定
if [[ "$DEBUG_MODE" == "true" ]]; then
    set -x
    log_info "Debug mode enabled"
fi

# ワーカータイプの検証
validate_worker_type() {
    case "$WORKER_TYPE" in
        queen|developer)
            log_info "Starting $WORKER_TYPE worker..."
            ;;
        *)
            log_error "Invalid worker type: $WORKER_TYPE"
            log_error "Valid types: queen, developer"
            exit 1
            ;;
    esac
}

# 環境確認
check_environment() {
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_step "Checking environment..."
    fi
    
    # 必要なディレクトリの確認
    local required_dirs=("$HIVE_DIR" "$WORKERS_DIR" "$PROMPTS_DIR" "$COMB_DIR")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_error "Required directory not found: $dir"
            exit 1
        fi
    done
    
    # プロンプトファイルの確認
    local prompt_file="$PROMPTS_DIR/${WORKER_TYPE}_worker.md"
    if [[ ! -f "$prompt_file" ]]; then
        log_error "Worker prompt not found: $prompt_file"
        exit 1
    fi
    
    # Python環境の確認
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not found"
        exit 1
    fi
    
    # Combモジュールの確認
    if ! python3 -c "import comb" 2>/dev/null; then
        log_error "Comb module not available"
        log_error "Run 'pip install -e .' in the hive directory"
        exit 1
    fi
    
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_info "Environment check passed"
    fi
}

# Worker固有の設定
setup_worker_config() {
    local worker_id="$WORKER_TYPE"
    local prompt_file="$PROMPTS_DIR/${WORKER_TYPE}_worker.md"
    
    # ワーカー固有のログディレクトリ
    local worker_log_dir="$LOG_DIR/$worker_id"
    mkdir -p "$worker_log_dir"
    
    # 環境変数の設定
    export HIVE_WORKER_ID="$worker_id"
    export HIVE_WORKER_TYPE="$WORKER_TYPE"
    export HIVE_PROMPT_FILE="$prompt_file"
    export HIVE_LOG_DIR="$worker_log_dir"
    export HIVE_COMB_DIR="$COMB_DIR"
    
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_info "Worker configuration:"
        log_info "  - ID: $worker_id"
        log_info "  - Type: $WORKER_TYPE"
        log_info "  - Prompt: $prompt_file"
        log_info "  - Log Dir: $worker_log_dir"
    fi
}

# Comb通信の初期化
initialize_comb() {
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_step "Initializing Comb communication..."
    fi
    
    # Combディレクトリ構造の確認
    python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from comb import CombAPI

# Worker API初期化
api = CombAPI('$WORKER_TYPE')

# 接続テスト
status = api.get_status()
print(f'Worker {status[\"worker_id\"]} initialized successfully')
"
    
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_info "Comb communication initialized"
    fi
}

# プロンプトの表示
display_prompt() {
    local prompt_file="$PROMPTS_DIR/${WORKER_TYPE}_worker.md"
    
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_step "Loading worker prompt..."
        echo
        echo "=================================================================================="
        cat "$prompt_file"
        echo "=================================================================================="
        echo
    fi
}

# 初期タスクの設定
setup_initial_task() {
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_step "Setting up initial task..."
    fi
    
    # Worker固有の初期タスク
    case "$WORKER_TYPE" in
        queen)
            python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from comb import CombAPI

api = CombAPI('queen')
task_id = api.start_task(
    'Hive Small Colony Initialization',
    'setup',
    'Initialize Small Colony with Queen and Developer Workers',
    workers=['queen', 'developer']
)
api.add_progress('Queen Worker started', 'Ready for project management')
print(f'Initial task created: {task_id}')
"
            ;;
        developer)
            python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from comb import CombAPI

api = CombAPI('developer')
task_id = api.start_task(
    'Developer Worker Initialization',
    'setup',
    'Initialize Developer Worker for implementation tasks',
    workers=['developer']
)
api.add_progress('Developer Worker started', 'Ready for implementation')
print(f'Initial task created: {task_id}')
"
            ;;
    esac
    
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_info "Initial task configured"
    fi
}

# 対話モードの開始
start_interactive_mode() {
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_step "Starting interactive mode..."
        echo
        echo "🐝 $WORKER_TYPE Worker is now active!"
        echo "💡 Available commands:"
        echo "   - Type 'help' for assistance"
        echo "   - Type 'status' to check Comb communication"
        echo "   - Type 'exit' to shutdown worker"
        echo "   - Use normal Claude Code interactions for development"
        echo
    fi
    
    # Claude Code起動コマンドの構築
    local claude_cmd="claude"
    
    # プロンプトファイルがあれば読み込み
    if [[ -f "$PROMPTS_DIR/${WORKER_TYPE}_worker.md" ]]; then
        if [[ "$QUIET_MODE" == "false" ]]; then
            echo "🔄 Loading worker-specific prompt..."
        fi
        
        # プロンプトを環境変数に設定
        export CLAUDE_WORKER_PROMPT="$(cat "$PROMPTS_DIR/${WORKER_TYPE}_worker.md")"
    fi
    
    # 初期メッセージの表示
    if [[ "$QUIET_MODE" == "false" ]]; then
        echo "🚀 Launching Claude Code with $WORKER_TYPE worker configuration..."
        echo "   Working directory: $HIVE_DIR"
        echo "   Worker ID: $WORKER_TYPE"
        echo "   Comb directory: $COMB_DIR"
        echo
    fi
    
    # Claude Code起動
    exec claude
}

# ヘルスチェック
health_check() {
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_step "Performing health check..."
    fi
    
    # 基本的な動作確認
    local health_status="healthy"
    
    # Comb通信テスト
    if ! python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from comb import CombAPI
api = CombAPI('$WORKER_TYPE')
status = api.get_status()
assert status['worker_id'] == '$WORKER_TYPE'
" 2>/dev/null; then
        health_status="unhealthy"
        log_error "Comb communication test failed"
    fi
    
    # ディレクトリ構造チェック
    if [[ ! -d "$COMB_DIR" ]]; then
        health_status="unhealthy"
        log_error "Comb directory not accessible"
    fi
    
    if [[ "$health_status" == "healthy" ]]; then
        if [[ "$QUIET_MODE" == "false" ]]; then
            log_info "✅ Health check passed"
        fi
    else
        log_error "❌ Health check failed"
        exit 1
    fi
}

# エラーハンドリング
handle_error() {
    local exit_code=$?
    log_error "Worker startup failed with exit code: $exit_code"
    
    # クリーンアップ処理
    if [[ -n "${HIVE_WORKER_ID:-}" ]]; then
        log_info "Performing cleanup for worker: $HIVE_WORKER_ID"
    fi
    
    exit "$exit_code"
}

# メイン実行フロー
main() {
    # エラーハンドリングの設定
    trap handle_error ERR
    
    # 実行フロー
    validate_worker_type
    check_environment
    setup_worker_config
    initialize_comb
    health_check
    display_prompt
    setup_initial_task
    start_interactive_mode
}

# メイン処理実行
main "$@"