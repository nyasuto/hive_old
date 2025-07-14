#!/bin/bash

# check-comb.sh - Comb通信確認スクリプト
# Hive Small ColonyのComb通信システムの動作確認とヘルスチェック

set -euo pipefail

# 設定
HIVE_SESSION="hive-small-colony"
HIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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

log_success() {
    echo -e "\033[32m[✅]\033[0m $1"
}

log_fail() {
    echo -e "\033[31m[❌]\033[0m $1"
}

# ヘルプメッセージ
show_help() {
    cat << EOF
🔍 Hive Comb Communication Check Script

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    -v, --verbose       Verbose output with detailed checks
    -q, --quiet         Quiet mode (minimal output)
    -f, --fix           Attempt to fix detected issues
    -t, --test          Run communication test between workers
    -s, --stats         Show detailed statistics

EXAMPLES:
    $0                  # Basic communication check
    $0 --verbose        # Detailed diagnostic output
    $0 --test           # Run communication test
    $0 --fix            # Check and fix issues

DESCRIPTION:
    This script verifies the Comb communication system health,
    checks worker connectivity, and validates the message infrastructure.

EOF
}

# 引数解析
VERBOSE_MODE=false
QUIET_MODE=false
FIX_MODE=false
TEST_MODE=false
STATS_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE_MODE=true
            shift
            ;;
        -q|--quiet)
            QUIET_MODE=true
            shift
            ;;
        -f|--fix)
            FIX_MODE=true
            shift
            ;;
        -t|--test)
            TEST_MODE=true
            shift
            ;;
        -s|--stats)
            STATS_MODE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# 静寂モード用のログ関数
verbose_log() {
    if [[ "$VERBOSE_MODE" == "true" ]]; then
        log_info "$1"
    fi
}

quiet_log() {
    if [[ "$QUIET_MODE" == "false" ]]; then
        log_info "$1"
    fi
}

# tmuxセッションの確認
check_hive_session() {
    log_step "Checking Hive session..."
    
    if ! tmux has-session -t "$HIVE_SESSION" 2>/dev/null; then
        log_fail "Hive session '$HIVE_SESSION' not found"
        log_error "Please start the Hive first: ./scripts/start-small-hive.sh"
        return 1
    fi
    
    # pane数の確認
    local pane_count
    pane_count=$(tmux list-panes -t "$HIVE_SESSION" | wc -l)
    
    if [[ "$pane_count" -lt 2 ]]; then
        log_fail "Expected 2 panes (Queen + Developer), found $pane_count"
        return 1
    fi
    
    log_success "Hive session active with $pane_count panes"
    
    if [[ "$VERBOSE_MODE" == "true" ]]; then
        echo "Session details:"
        tmux list-panes -t "$HIVE_SESSION" -F "  - Pane #{pane_index}: #{pane_title} (#{pane_current_command})"
    fi
    
    return 0
}

# Combディレクトリ構造の確認
check_comb_structure() {
    log_step "Checking Comb directory structure..."
    
    local required_dirs=(
        "$COMB_DIR"
        "$COMB_DIR/comb"
        "$COMB_DIR/comb/messages"
        "$COMB_DIR/comb/messages/inbox"
        "$COMB_DIR/comb/messages/outbox"
        "$COMB_DIR/comb/messages/sent"
        "$COMB_DIR/comb/messages/failed"
        "$COMB_DIR/nectar"
        "$COMB_DIR/honey"
        "$COMB_DIR/work_logs"
    )
    
    local missing_dirs=()
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            missing_dirs+=("$dir")
        fi
    done
    
    if [[ ${#missing_dirs[@]} -gt 0 ]]; then
        log_fail "Missing directories:"
        for dir in "${missing_dirs[@]}"; do
            echo "  - $dir"
        done
        
        if [[ "$FIX_MODE" == "true" ]]; then
            log_info "Attempting to create missing directories..."
            for dir in "${missing_dirs[@]}"; do
                mkdir -p "$dir"
                verbose_log "Created: $dir"
            done
            log_success "Missing directories created"
        else
            log_error "Use --fix to create missing directories"
            return 1
        fi
    else
        log_success "Comb directory structure complete"
    fi
    
    return 0
}

# Python環境とCombモジュールの確認
check_python_environment() {
    log_step "Checking Python environment..."
    
    # Python確認
    if ! command -v python3 &> /dev/null; then
        log_fail "Python3 not found"
        return 1
    fi
    
    local python_version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    verbose_log "Python version: $python_version"
    
    # Combモジュール確認
    local comb_test_result
    comb_test_result=$(python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
try:
    import comb
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)
    
    if [[ "$comb_test_result" != "SUCCESS" ]]; then
        log_fail "Comb module not available"
        if [[ "$VERBOSE_MODE" == "true" ]]; then
            echo "Error details: $comb_test_result"
        fi
        log_error "Python version compatibility issue detected"
        log_error "Note: Some Hive features require Python 3.10+ for union type syntax"
        return 1
    fi
    
    log_success "Python environment ready"
    
    # 基本的なComb API テスト
    local api_test_result
    api_test_result=$(python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
try:
    from comb import CombAPI
    # 基本的なAPI初期化テスト
    api = CombAPI('check-comb')
    status = api.get_status()
    print(f'SUCCESS: Worker ID {status[\"worker_id\"]}')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)
    
    if [[ "$api_test_result" =~ ^SUCCESS: ]]; then
        log_success "Comb API functional"
        if [[ "$VERBOSE_MODE" == "true" ]]; then
            echo "API test result: $api_test_result"
        fi
    else
        log_fail "Comb API initialization failed"
        if [[ "$VERBOSE_MODE" == "true" ]]; then
            echo "API error: $api_test_result"
        fi
        return 1
    fi
    
    return 0
}

# Worker間通信テスト
test_worker_communication() {
    log_step "Testing worker communication..."
    
    local test_result
    test_result=$(python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from comb import CombAPI
import time
import json

# テスト用API
test_api = CombAPI('test-checker')

# Queen Workerにpingメッセージ送信
ping_sent = test_api.send_notification(
    'queen',
    {'action': 'ping', 'timestamp': time.time(), 'test_id': 'comb-check'},
    priority='normal'
)

if not ping_sent:
    print('ERROR: Failed to send ping message')
    sys.exit(1)

# 少し待機
time.sleep(1)

# メッセージ統計取得
stats = test_api.get_status()
print(json.dumps({
    'ping_sent': ping_sent,
    'messages_sent': stats.get('messages', {}).get('sent', 0),
    'test_passed': True
}))
" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        local result_json
        result_json=$(echo "$test_result" | tail -n 1)
        
        if echo "$result_json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('test_passed', False):
    print('Communication test passed')
    sys.exit(0)
else:
    print('Communication test failed')
    sys.exit(1)
" 2>/dev/null; then
            log_success "Worker communication test passed"
            if [[ "$VERBOSE_MODE" == "true" ]]; then
                echo "Test results: $result_json"
            fi
        else
            log_fail "Communication test failed"
            return 1
        fi
    else
        log_fail "Communication test error"
        return 1
    fi
    
    return 0
}

# メッセージファイルの確認
check_message_files() {
    log_step "Checking message files..."
    
    local message_dirs=(
        "$COMB_DIR/comb/messages/inbox"
        "$COMB_DIR/comb/messages/outbox"
        "$COMB_DIR/comb/messages/sent"
        "$COMB_DIR/comb/messages/failed"
    )
    
    local total_messages=0
    
    for dir in "${message_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            local count
            count=$(find "$dir" -name "*.json" | wc -l)
            total_messages=$((total_messages + count))
            
            if [[ "$VERBOSE_MODE" == "true" ]]; then
                local dirname
                dirname=$(basename "$dir")
                verbose_log "$dirname: $count messages"
            fi
        fi
    done
    
    quiet_log "Total messages found: $total_messages"
    
    # 失敗メッセージの確認
    local failed_count
    failed_count=$(find "$COMB_DIR/comb/messages/failed" -name "*.json" 2>/dev/null | wc -l)
    
    if [[ "$failed_count" -gt 0 ]]; then
        log_warn "$failed_count failed messages detected"
        if [[ "$VERBOSE_MODE" == "true" ]]; then
            echo "Failed messages:"
            find "$COMB_DIR/comb/messages/failed" -name "*.json" -exec basename {} \; | head -5
        fi
    fi
    
    return 0
}

# Work Log確認
check_work_logs() {
    log_step "Checking work logs..."
    
    local daily_logs
    daily_logs=$(find "$COMB_DIR/work_logs/daily" -name "*.md" 2>/dev/null | wc -l)
    
    local project_logs
    project_logs=$(find "$COMB_DIR/work_logs/projects" -name "*.md" 2>/dev/null | wc -l)
    
    if [[ "$daily_logs" -eq 0 && "$project_logs" -eq 0 ]]; then
        log_warn "No work logs found (workers may not be active yet)"
    else
        log_success "Work logs found: $daily_logs daily, $project_logs project"
    fi
    
    return 0
}

# 統計情報の表示
show_statistics() {
    if [[ "$STATS_MODE" == "false" ]]; then
        return
    fi
    
    log_step "Comb communication statistics:"
    
    python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from comb import CombAPI
import json

# 統計情報収集
api = CombAPI('stats-checker')
status = api.get_status()

print('📊 System Status:')
print(f'  - Worker ID: {status.get(\"worker_id\", \"unknown\")}')
print(f'  - Timestamp: {status.get(\"timestamp\", \"unknown\")}')

if 'messages' in status:
    msg_stats = status['messages']
    print('📬 Message Statistics:')
    for key, value in msg_stats.items():
        print(f'  - {key.title()}: {value}')

if 'work_logs' in status:
    work_stats = status['work_logs']
    print('📝 Work Log Statistics:')
    for key, value in work_stats.items():
        print(f'  - {key.title()}: {value}')
" 2>/dev/null || log_warn "Could not retrieve detailed statistics"
}

# 全体のヘルスチェック
perform_health_check() {
    log_info "🔍 Performing Comb communication health check..."
    echo
    
    local check_count=0
    local pass_count=0
    
    # 各チェックを実行
    local checks=(
        "check_hive_session"
        "check_comb_structure" 
        "check_python_environment"
        "check_message_files"
        "check_work_logs"
    )
    
    if [[ "$TEST_MODE" == "true" ]]; then
        checks+=("test_worker_communication")
    fi
    
    for check in "${checks[@]}"; do
        check_count=$((check_count + 1))
        if $check; then
            pass_count=$((pass_count + 1))
        fi
        echo
    done
    
    # 統計表示
    show_statistics
    
    # 結果サマリー
    echo
    log_step "Health check summary:"
    echo "  - Checks performed: $check_count"
    echo "  - Checks passed: $pass_count"
    echo "  - Checks failed: $((check_count - pass_count))"
    
    if [[ "$pass_count" -eq "$check_count" ]]; then
        log_success "🎉 All Comb communication checks passed!"
        echo
        echo "📋 Next steps:"
        echo "  - Run tasks in the Hive session: tmux attach-session -t $HIVE_SESSION"
        echo "  - Collect results: ./scripts/collect-honey.sh"
        echo "  - Shutdown when done: ./scripts/shutdown-hive.sh"
        return 0
    else
        log_fail "❌ Some checks failed"
        echo
        echo "🔧 Troubleshooting:"
        echo "  - Run with --verbose for detailed output"
        echo "  - Run with --fix to attempt automatic fixes"
        echo "  - Check the Hive session: tmux attach-session -t $HIVE_SESSION"
        return 1
    fi
}

# エラーハンドリング
handle_error() {
    local exit_code=$?
    log_error "Comb check failed with exit code: $exit_code"
    
    echo
    echo "🔧 Troubleshooting tips:"
    echo "  1. Ensure Hive is started: ./scripts/start-small-hive.sh"
    echo "  2. Check tmux session: tmux list-sessions"
    echo "  3. Verify Python environment: python3 -c 'import comb'"
    echo "  4. Run with --verbose for detailed diagnostics"
    
    exit "$exit_code"
}

# メイン実行フロー
main() {
    # エラーハンドリング設定
    trap handle_error ERR
    
    if [[ "$QUIET_MODE" == "false" ]]; then
        echo "🐝 Hive Comb Communication Check"
        echo "================================"
        echo
    fi
    
    # ヘルスチェック実行
    perform_health_check
}

# メイン処理実行
main "$@"