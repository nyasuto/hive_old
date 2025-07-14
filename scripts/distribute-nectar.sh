#!/bin/bash

# distribute-nectar.sh - Nectar配布スクリプト
# Issue #4 - Nectarタスク管理システムのCLI配布機能

set -euo pipefail

# 設定
HIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NECTAR_TEMPLATES_DIR="$HIVE_DIR/templates/nectar-templates"
NECTAR_COMMON_TASKS_DIR="$NECTAR_TEMPLATES_DIR/common-tasks"
HIVE_NECTAR_DIR="$HIVE_DIR/.hive/nectar"
LOG_DIR="$HIVE_DIR/.hive/logs"
LOG_FILE="$LOG_DIR/nectar-distribution-$(date +%Y%m%d-%H%M%S).log"

# 色付きログ関数
log_info() {
    echo -e "\\033[32m[INFO]\\033[0m $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "\\033[33m[WARN]\\033[0m $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "\\033[31m[ERROR]\\033[0m $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "\\033[36m[STEP]\\033[0m $1" | tee -a "$LOG_FILE"
}

# ヘルプメッセージ
show_help() {
    cat << EOF
🍯 Nectar Distribution Script

Usage: $0 <COMMAND> [OPTIONS]

COMMANDS:
    create      Create new nectar from template
    distribute  Distribute nectar to worker
    status      Check nectar status
    list        List nectars by status
    batch       Batch distribute nectars
    monitor     Monitor nectar progress

CREATE OPTIONS:
    -t, --template TYPE     Template type (feature|bug-fix|refactoring|testing|documentation|custom)
    -w, --worker WORKER     Target worker ID (default: developer)
    -p, --priority PRIORITY Priority (low|medium|high|critical, default: medium)
    -e, --estimate HOURS    Estimated hours (default: 4)
    -d, --deadline HOURS    Deadline in hours (default: 24)
    --title TITLE           Task title
    --description DESC      Task description
    --interactive           Interactive mode for custom nectar

DISTRIBUTE OPTIONS:
    -n, --nectar-id ID      Nectar ID to distribute
    -w, --worker WORKER     Target worker ID
    -f, --force             Force distribution even if dependencies not met

STATUS OPTIONS:
    -n, --nectar-id ID      Nectar ID to check
    -w, --worker WORKER     Worker ID to check

LIST OPTIONS:
    -s, --status STATUS     Status filter (pending|active|completed|failed|all, default: all)
    -w, --worker WORKER     Worker ID filter

BATCH OPTIONS:
    -w, --worker WORKER     Target worker ID
    -m, --max-tasks NUM     Maximum tasks to distribute (default: 3)

MONITOR OPTIONS:
    -w, --worker WORKER     Worker ID to monitor
    -d, --dashboard         Show monitoring dashboard

GLOBAL OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Verbose output
    -q, --quiet             Quiet mode
    --dry-run               Dry run mode (show what would be done)

EXAMPLES:
    $0 create -t feature --title "新機能実装" --interactive
    $0 distribute -n nectar-20240714-143000-12345678 -w developer
    $0 status -w developer
    $0 list -s active
    $0 batch -w developer -m 2
    $0 monitor --dashboard

TEMPLATE TYPES:
    feature         New feature implementation
    bug-fix         Bug fix task
    refactoring     Code refactoring task
    testing         Test implementation task
    documentation   Documentation task
    custom          Custom task (interactive mode)

EOF
}

# 引数解析
if [[ $# -eq 0 ]]; then
    show_help
    exit 1
fi

COMMAND="$1"
shift

# グローバル変数
TEMPLATE_TYPE=""
WORKER_ID="developer"
PRIORITY="medium"
ESTIMATE_HOURS=4
DEADLINE_HOURS=24
TITLE=""
DESCRIPTION=""
NECTAR_ID=""
STATUS_FILTER="all"
MAX_TASKS=3
INTERACTIVE_MODE=false
VERBOSE=false
QUIET=false
DRY_RUN=false
FORCE=false
SHOW_DASHBOARD=false

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--template)
            TEMPLATE_TYPE="$2"
            shift 2
            ;;
        -w|--worker)
            WORKER_ID="$2"
            shift 2
            ;;
        -p|--priority)
            PRIORITY="$2"
            shift 2
            ;;
        -e|--estimate)
            ESTIMATE_HOURS="$2"
            shift 2
            ;;
        -d|--deadline)
            DEADLINE_HOURS="$2"
            shift 2
            ;;
        --title)
            TITLE="$2"
            shift 2
            ;;
        --description)
            DESCRIPTION="$2"
            shift 2
            ;;
        -n|--nectar-id)
            NECTAR_ID="$2"
            shift 2
            ;;
        -s|--status)
            STATUS_FILTER="$2"
            shift 2
            ;;
        -m|--max-tasks)
            MAX_TASKS="$2"
            shift 2
            ;;
        --interactive)
            INTERACTIVE_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --dashboard)
            SHOW_DASHBOARD=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# 詳細モード設定
if [[ "$VERBOSE" == "true" ]]; then
    set -x
fi

# 環境確認
check_environment() {
    if [[ "$QUIET" == "false" ]]; then
        log_step "Checking environment..."
    fi
    
    # 必要なディレクトリの確認
    local required_dirs=("$HIVE_DIR" "$NECTAR_TEMPLATES_DIR" "$HIVE_NECTAR_DIR")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_error "Required directory not found: $dir"
            exit 1
        fi
    done
    
    # Python環境確認
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not found"
        exit 1
    fi
    
    # Hiveモジュール確認
    if ! python3 -c "import sys; sys.path.insert(0, '$HIVE_DIR'); import queen.task_distributor" 2>/dev/null; then
        log_error "Hive queen module not available"
        log_error "Run 'pip install -e .' in the hive directory"
        exit 1
    fi
    
    if [[ "$QUIET" == "false" ]]; then
        log_info "Environment check passed"
    fi
}

# Nectar作成
create_nectar() {
    log_step "Creating nectar..."
    
    # テンプレートタイプの検証
    if [[ -z "$TEMPLATE_TYPE" ]]; then
        log_error "Template type required (-t/--template)"
        exit 1
    fi
    
    # インタラクティブモードでの入力収集
    if [[ "$INTERACTIVE_MODE" == "true" ]]; then
        collect_interactive_input
    fi
    
    # 必要な情報の確認
    if [[ -z "$TITLE" ]]; then
        log_error "Title required (--title)"
        exit 1
    fi
    
    if [[ -z "$DESCRIPTION" ]]; then
        log_error "Description required (--description)"
        exit 1
    fi
    
    # Python経由でNectar作成
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "Would create nectar: $TITLE"
        echo "  Template: $TEMPLATE_TYPE"
        echo "  Worker: $WORKER_ID"
        echo "  Priority: $PRIORITY"
        echo "  Estimate: $ESTIMATE_HOURS hours"
        echo "  Deadline: $DEADLINE_HOURS hours"
        return
    fi
    
    python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from queen.task_distributor import TaskDistributor, Priority

# TaskDistributor初期化
distributor = TaskDistributor()

# Priority列挙型に変換
priority_map = {
    'low': Priority.LOW,
    'medium': Priority.MEDIUM,
    'high': Priority.HIGH,
    'critical': Priority.CRITICAL
}

# Nectar作成
nectar = distributor.create_nectar(
    title='$TITLE',
    description='$DESCRIPTION',
    assigned_to='$WORKER_ID',
    priority=priority_map['$PRIORITY'],
    estimated_time=$ESTIMATE_HOURS,
    deadline_hours=$DEADLINE_HOURS
)

print(f'Created nectar: {nectar.nectar_id}')
print(f'Title: {nectar.title}')
print(f'Assigned to: {nectar.assigned_to}')
print(f'Priority: {nectar.priority.value}')
print(f'Deadline: {nectar.deadline}')
"
    
    log_info "Nectar created successfully"
}

# インタラクティブ入力収集
collect_interactive_input() {
    echo "🍯 Interactive Nectar Creation"
    echo
    
    if [[ -z "$TITLE" ]]; then
        read -p "Enter task title: " TITLE
    fi
    
    if [[ -z "$DESCRIPTION" ]]; then
        echo "Enter task description (end with empty line):"
        DESCRIPTION=""
        while IFS= read -r line; do
            [[ -z "$line" ]] && break
            DESCRIPTION+="$line\n"
        done
    fi
    
    read -p "Worker ID [$WORKER_ID]: " input_worker
    [[ -n "$input_worker" ]] && WORKER_ID="$input_worker"
    
    read -p "Priority [$PRIORITY]: " input_priority
    [[ -n "$input_priority" ]] && PRIORITY="$input_priority"
    
    read -p "Estimated hours [$ESTIMATE_HOURS]: " input_estimate
    [[ -n "$input_estimate" ]] && ESTIMATE_HOURS="$input_estimate"
    
    read -p "Deadline hours [$DEADLINE_HOURS]: " input_deadline
    [[ -n "$input_deadline" ]] && DEADLINE_HOURS="$input_deadline"
    
    echo
    echo "Summary:"
    echo "  Title: $TITLE"
    echo "  Worker: $WORKER_ID"
    echo "  Priority: $PRIORITY"
    echo "  Estimate: $ESTIMATE_HOURS hours"
    echo "  Deadline: $DEADLINE_HOURS hours"
    echo
    
    read -p "Create this nectar? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Nectar creation cancelled"
        exit 0
    fi
}

# Nectar配布
distribute_nectar() {
    log_step "Distributing nectar..."
    
    if [[ -z "$NECTAR_ID" ]]; then
        log_error "Nectar ID required (-n/--nectar-id)"
        exit 1
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "Would distribute nectar: $NECTAR_ID"
        echo "  To worker: $WORKER_ID"
        echo "  Force: $FORCE"
        return
    fi
    
    python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from queen.task_distributor import TaskDistributor

# TaskDistributor初期化
distributor = TaskDistributor()

# Nectar取得
nectar = distributor.get_nectar_by_id('$NECTAR_ID')
if not nectar:
    print('Error: Nectar not found')
    sys.exit(1)

# Worker IDが指定されている場合は変更
if '$WORKER_ID' != 'developer':
    nectar.assigned_to = '$WORKER_ID'

# 配布実行
success = distributor.distribute_nectar(nectar)

if success:
    print(f'Successfully distributed nectar {nectar.nectar_id} to {nectar.assigned_to}')
else:
    print(f'Failed to distribute nectar {nectar.nectar_id}')
    if not '$FORCE' == 'true':
        print('Use --force to override dependency checks')
    sys.exit(1)
"
    
    log_info "Nectar distributed successfully"
}

# Nectar状態確認
check_nectar_status() {
    log_step "Checking nectar status..."
    
    if [[ -n "$NECTAR_ID" ]]; then
        # 特定のNectar状態確認
        python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from queen.task_distributor import TaskDistributor

distributor = TaskDistributor()
nectar = distributor.get_nectar_by_id('$NECTAR_ID')

if nectar:
    print(f'Nectar ID: {nectar.nectar_id}')
    print(f'Title: {nectar.title}')
    print(f'Status: {nectar.status.value}')
    print(f'Assigned to: {nectar.assigned_to}')
    print(f'Priority: {nectar.priority.value}')
    print(f'Created: {nectar.created_at}')
    print(f'Deadline: {nectar.deadline}')
    print(f'Estimated time: {nectar.estimated_time}h')
    print(f'Dependencies: {nectar.dependencies}')
    print(f'Expected honey: {nectar.expected_honey}')
else:
    print('Error: Nectar not found')
    sys.exit(1)
"
    elif [[ -n "$WORKER_ID" ]]; then
        # Worker状態確認
        python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from queen.task_distributor import TaskDistributor

distributor = TaskDistributor()
workload = distributor.get_worker_workload('$WORKER_ID')

print(f'Worker: {workload[\"worker_id\"]}')
print(f'Active tasks: {workload[\"active_tasks\"]}')
print(f'Pending tasks: {workload[\"pending_tasks\"]}')
print(f'Total estimated time: {workload[\"total_estimated_time\"]}h')
print(f'Tasks by priority: {workload[\"tasks_by_priority\"]}')
"
    else
        log_error "Either nectar ID (-n) or worker ID (-w) required"
        exit 1
    fi
}

# Nectar一覧表示
list_nectars() {
    log_step "Listing nectars..."
    
    python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from queen.task_distributor import TaskDistributor

distributor = TaskDistributor()

# 状態別にNectar取得
status_filter = '$STATUS_FILTER'
worker_filter = '$WORKER_ID' if '$WORKER_ID' != 'developer' else None

if status_filter == 'all':
    nectars = (distributor.get_pending_nectars(worker_filter) +
              distributor.get_active_nectars(worker_filter) +
              distributor.get_completed_nectars(worker_filter))
elif status_filter == 'pending':
    nectars = distributor.get_pending_nectars(worker_filter)
elif status_filter == 'active':
    nectars = distributor.get_active_nectars(worker_filter)
elif status_filter == 'completed':
    nectars = distributor.get_completed_nectars(worker_filter)
else:
    print(f'Invalid status filter: {status_filter}')
    sys.exit(1)

# 一覧表示
print(f'Status: {status_filter.upper()}')
if worker_filter:
    print(f'Worker: {worker_filter}')
print(f'Total: {len(nectars)} nectars')
print()

for nectar in nectars:
    print(f'[{nectar.status.value.upper()}] {nectar.nectar_id}')
    print(f'  Title: {nectar.title}')
    print(f'  Worker: {nectar.assigned_to}')
    print(f'  Priority: {nectar.priority.value}')
    print(f'  Deadline: {nectar.deadline}')
    print()
"
}

# バッチ配布
batch_distribute() {
    log_step "Batch distributing nectars..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "Would batch distribute to worker: $WORKER_ID"
        echo "  Max tasks: $MAX_TASKS"
        return
    fi
    
    python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from queen.task_distributor import TaskDistributor

distributor = TaskDistributor()

# バッチ配布実行
distributed = distributor.batch_distribute('$WORKER_ID', $MAX_TASKS)

print(f'Batch distributed {len(distributed)} nectars to $WORKER_ID')
for nectar_id in distributed:
    print(f'  - {nectar_id}')
"
    
    log_info "Batch distribution completed"
}

# 進捗監視
monitor_progress() {
    log_step "Monitoring nectar progress..."
    
    if [[ "$SHOW_DASHBOARD" == "true" ]]; then
        python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from queen.status_monitor import StatusMonitor

monitor = StatusMonitor()
dashboard = monitor.get_monitoring_dashboard()

print('🍯 Nectar Monitoring Dashboard')
print('=' * 50)
print(f'Timestamp: {dashboard[\"timestamp\"]}')
print()

overview = dashboard['overview']
print('📊 Overview:')
print(f'  Active nectars: {overview[\"active_nectars\"]}')
print(f'  Pending nectars: {overview[\"pending_nectars\"]}')
print(f'  Completed nectars: {overview[\"completed_nectars\"]}')
print(f'  Active workers: {overview[\"active_workers\"]}')
print(f'  Total alerts: {overview[\"total_alerts\"]}')
print()

print('👥 Worker States:')
for worker_id, state in dashboard['worker_states'].items():
    print(f'  {worker_id}: {state[\"state\"]} ({state[\"current_workload\"]:.1%} load)')
print()

print('🚨 Recent Alerts:')
for alert in dashboard['recent_alerts']:
    print(f'  [{alert[\"severity\"].upper()}] {alert[\"message\"]}')
"
    else
        if [[ -n "$WORKER_ID" ]]; then
            python3 -c "
import sys
sys.path.insert(0, '$HIVE_DIR')
from queen.status_monitor import StatusMonitor

monitor = StatusMonitor()
report = monitor.get_worker_performance_report('$WORKER_ID')

print(f'🍯 Worker Performance Report: {report[\"worker_id\"]}')
print('=' * 50)
print()

status = report['current_status']
print(f'Current Status: {status[\"state\"]}')
print(f'Current Tasks: {len(status[\"current_tasks\"])}')
print(f'Workload: {status[\"current_workload\"]:.1%}')
print(f'Last Seen: {status[\"last_seen\"]}')
print()

metrics = report['performance_metrics']
print('📈 Performance Metrics:')
print(f'  Total Completed: {metrics[\"total_completed\"]}')
print(f'  Average Completion Time: {metrics[\"average_completion_time\"]:.1f}h')
print(f'  Success Rate: {metrics[\"success_rate\"]:.1%}')
"
        else
            log_error "Worker ID required for monitoring (-w/--worker)"
            exit 1
        fi
    fi
}

# メイン実行フロー
main() {
    # ログディレクトリ作成
    mkdir -p "$LOG_DIR"
    
    if [[ "$QUIET" == "false" ]]; then
        log_info "🍯 Starting nectar distribution script..."
        log_info "Command: $COMMAND"
    fi
    
    # 環境確認
    check_environment
    
    # コマンド実行
    case "$COMMAND" in
        create)
            create_nectar
            ;;
        distribute)
            distribute_nectar
            ;;
        status)
            check_nectar_status
            ;;
        list)
            list_nectars
            ;;
        batch)
            batch_distribute
            ;;
        monitor)
            monitor_progress
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
    
    if [[ "$QUIET" == "false" ]]; then
        log_info "🎉 Nectar distribution script completed successfully!"
    fi
}

# エラーハンドリング
trap 'log_error "Script interrupted"; exit 1' INT TERM

# メイン処理実行
main "$@"