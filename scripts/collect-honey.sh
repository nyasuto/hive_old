#!/bin/bash

# =============================================================================
# Hive Honey Collection Script
# 
# Issue #5の実装: Honey成果物収集・品質管理システムのCLI
# 完了したNectarからHoney（成果物）を収集し、品質レポートを生成
# =============================================================================

set -euo pipefail

# =============================================================================
# 設定と初期化
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_CMD="uv run python"

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ログ設定
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
LOG_DIR="$PROJECT_ROOT/.hive/logs"
LOG_FILE="$LOG_DIR/collect-honey-$TIMESTAMP.log"

# =============================================================================
# ユーティリティ関数
# =============================================================================

print_header() {
    echo -e "${PURPLE}=================================${NC}"
    echo -e "${PURPLE}🍯 Hive Honey Collection System${NC}"
    echo -e "${PURPLE}=================================${NC}"
    echo
}

print_usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

🍯 Hive Honey Collection Commands:

COMMANDS:
    auto                    自動収集（完了したNectarから）
    manual [files...]       手動収集（指定ファイル）
    report                  品質レポート生成
    stats                   収集統計表示
    cleanup [days]          古いHoney清理（デフォルト: 30日）
    list [type]             Honey一覧表示
    help                    このヘルプを表示

OPTIONS:
    --nectar-id ID          関連Nectar ID指定（manual用）
    --type TYPE             Honeyタイプ指定（list用）
    --format FORMAT         出力形式（json|table）デフォルト: table
    --output FILE           出力ファイル指定
    --verbose               詳細ログ出力
    --dry-run               実行せずに予行演習
    --quality-threshold N   品質閾値指定（0-100）

HONEY TYPES:
    code                    コードファイル（.py, .js, .ts等）
    docs                    ドキュメント（.md, .txt, .pdf等）
    reports                 レポートファイル
    config                  設定ファイル（.json, .yaml等）
    data                    データファイル（.csv, .json等）

EXAMPLES:
    $0 auto                                      # 自動収集実行
    $0 manual src/main.py README.md             # 手動ファイル収集
    $0 report --format json --output report.json # JSON形式レポート
    $0 list code                                 # コードファイル一覧
    $0 cleanup 7                                # 7日より古いファイル削除
    $0 stats --verbose                          # 詳細統計表示

EOF
}

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    mkdir -p "$LOG_DIR"
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    case $level in
        "ERROR")
            echo -e "${RED}❌ Error: $message${NC}" >&2
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  Warning: $message${NC}"
            ;;
        "INFO")
            echo -e "${GREEN}ℹ️  $message${NC}"
            ;;
        "DEBUG")
            if [[ "${VERBOSE:-false}" == "true" ]]; then
                echo -e "${CYAN}🔍 $message${NC}"
            fi
            ;;
    esac
}

check_dependencies() {
    log "INFO" "Checking dependencies..."
    
    if ! command -v uv >/dev/null 2>&1; then
        log "ERROR" "uv is not installed. Please install uv first."
        exit 1
    fi
    
    # Python環境チェック
    if ! $PYTHON_CMD -c "import queen.honey_collector" >/dev/null 2>&1; then
        log "ERROR" "honey_collector module not found. Please install dependencies."
        exit 1
    fi
    
    log "INFO" "Dependencies check passed"
}

ensure_hive_structure() {
    log "DEBUG" "Ensuring Hive directory structure..."
    
    mkdir -p "$PROJECT_ROOT/.hive/honey"/{code,docs,reports,config,data,history}
    
    log "DEBUG" "Hive structure ready"
}

# =============================================================================
# コア機能関数
# =============================================================================

collect_auto() {
    log "INFO" "Starting automatic honey collection..."
    
    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        log "INFO" "DRY RUN: Would collect completed nectars"
        return 0
    fi
    
    local python_script="
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from queen.honey_collector import HoneyCollector

collector = HoneyCollector()
artifacts = collector.collect_completed_nectars()

print(f'Collected {len(artifacts)} artifacts:')
for artifact in artifacts:
    print(f'  - {artifact.honey_id}: {artifact.original_path} ({artifact.honey_type.value})')
"
    
    log "DEBUG" "Executing automatic collection..."
    if ! $PYTHON_CMD -c "$python_script"; then
        log "ERROR" "Automatic collection failed"
        return 1
    fi
    
    log "INFO" "Automatic collection completed"
}

collect_manual() {
    local files=("$@")
    
    if [[ ${#files[@]} -eq 0 ]]; then
        log "ERROR" "No files specified for manual collection"
        print_usage
        return 1
    fi
    
    log "INFO" "Starting manual honey collection for ${#files[@]} files..."
    
    # ファイル存在チェック
    for file in "${files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log "ERROR" "File not found: $file"
            return 1
        fi
    done
    
    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        log "INFO" "DRY RUN: Would collect files: ${files[*]}"
        return 0
    fi
    
    local files_json=$(printf '%s\n' "${files[@]}" | python3 -c "import json, sys; print(json.dumps([line.strip() for line in sys.stdin]))")
    local nectar_id="${NECTAR_ID:-manual}"
    
    local python_script="
import sys
import json
sys.path.insert(0, '$PROJECT_ROOT')
from queen.honey_collector import HoneyCollector

collector = HoneyCollector()
files = json.loads('$files_json')
artifacts = collector.collect_manual_artifacts(files, '$nectar_id')

print(f'Manually collected {len(artifacts)} artifacts:')
for artifact in artifacts:
    print(f'  - {artifact.honey_id}: {artifact.original_path} ({artifact.honey_type.value}, score: {artifact.quality_score:.1f})')
"
    
    log "DEBUG" "Executing manual collection..."
    if ! $PYTHON_CMD -c "$python_script"; then
        log "ERROR" "Manual collection failed"
        return 1
    fi
    
    log "INFO" "Manual collection completed"
}

generate_report() {
    log "INFO" "Generating quality report..."
    
    local format="${FORMAT:-table}"
    local output_file="${OUTPUT_FILE:-}"
    
    local python_script="
import sys
import json
sys.path.insert(0, '$PROJECT_ROOT')
from queen.honey_collector import HoneyCollector

collector = HoneyCollector()
report = collector.generate_quality_report()

if '$format' == 'json':
    output = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
else:
    # テーブル形式
    output = f'''
🍯 Honey Quality Report
========================

📊 Summary:
  Total Artifacts: {report.total_artifacts}
  Average Quality: {report.average_quality:.1f}/100

📈 Quality Distribution:
'''
    for level, count in report.quality_distribution.items():
        percentage = (count / report.total_artifacts * 100) if report.total_artifacts > 0 else 0
        output += f'  {level.title()}: {count} ({percentage:.1f}%)\n'
    
    output += '\n📁 Type Distribution:\n'
    for type_name, count in report.type_distribution.items():
        percentage = (count / report.total_artifacts * 100) if report.total_artifacts > 0 else 0
        output += f'  {type_name.title()}: {count} ({percentage:.1f}%)\n'
    
    if report.recommendations:
        output += '\n💡 Recommendations:\n'
        for rec in report.recommendations:
            output += f'  • {rec}\n'
    
    if report.issues:
        output += '\n⚠️  Issues Found:\n'
        for issue in report.issues:
            output += f'  • {issue}\n'
    
    output += f'\nGenerated at: {report.generated_at.strftime(\"%Y-%m-%d %H:%M:%S\")}'

print(output)
"
    
    local output
    if ! output=$($PYTHON_CMD -c "$python_script"); then
        log "ERROR" "Report generation failed"
        return 1
    fi
    
    if [[ -n "$output_file" ]]; then
        echo "$output" > "$output_file"
        log "INFO" "Report saved to: $output_file"
    else
        echo "$output"
    fi
    
    log "INFO" "Quality report generated"
}

show_stats() {
    log "INFO" "Displaying collection statistics..."
    
    local python_script="
import sys
import json
sys.path.insert(0, '$PROJECT_ROOT')
from queen.honey_collector import HoneyCollector

collector = HoneyCollector()
stats = collector.get_collection_stats()

print('🍯 Honey Collection Statistics')
print('==============================')
print()
print(f'📊 Overview:')
print(f'  Total Artifacts: {stats[\"total_artifacts\"]}')
print(f'  Average Quality: {stats[\"average_quality\"]:.1f}/100')
print(f'  Total Size: {stats[\"total_size_mb\"]:.2f} MB')
print(f'  Unique Nectars: {stats[\"unique_nectars\"]}')
print(f'  Collection History: {stats[\"collection_history_files\"]} files')
print()

print('📁 Type Distribution:')
for type_name, count in stats['type_distribution'].items():
    if count > 0:
        percentage = (count / stats['total_artifacts'] * 100) if stats['total_artifacts'] > 0 else 0
        print(f'  {type_name.title()}: {count} ({percentage:.1f}%)')
print()

print('🎯 Quality Distribution:')
for quality, count in stats['quality_distribution'].items():
    if count > 0:
        percentage = (count / stats['total_artifacts'] * 100) if stats['total_artifacts'] > 0 else 0
        emoji = {'excellent': '🟢', 'good': '🔵', 'acceptable': '🟡', 'poor': '🔴'}.get(quality, '⚪')
        print(f'  {emoji} {quality.title()}: {count} ({percentage:.1f}%)')
"
    
    if ! $PYTHON_CMD -c "$python_script"; then
        log "ERROR" "Statistics display failed"
        return 1
    fi
    
    log "INFO" "Statistics displayed"
}

list_honey() {
    local honey_type="${HONEY_TYPE:-}"
    
    log "INFO" "Listing honey artifacts..."
    
    local python_script="
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from queen.honey_collector import HoneyCollector, HoneyType

collector = HoneyCollector()

if '$honey_type':
    try:
        honey_type_enum = HoneyType('$honey_type')
        artifacts = collector.get_honey_by_type(honey_type_enum)
        print(f'🍯 {honey_type.title()} Artifacts ({len(artifacts)}):')
    except ValueError:
        print(f'Error: Invalid honey type: $honey_type')
        print(f'Valid types: {[t.value for t in HoneyType]}')
        sys.exit(1)
else:
    artifacts = collector._load_all_artifacts()
    print(f'🍯 All Artifacts ({len(artifacts)}):')

print('=' * 80)

for artifact in sorted(artifacts, key=lambda a: a.collected_at, reverse=True):
    quality_emoji = {'excellent': '🟢', 'good': '🔵', 'acceptable': '🟡', 'poor': '🔴'}
    emoji = quality_emoji.get(artifact.quality_level.value, '⚪')
    
    print(f'{emoji} {artifact.honey_id}')
    print(f'   Type: {artifact.honey_type.value} | Quality: {artifact.quality_score:.1f}/100')
    print(f'   Original: {artifact.original_path}')
    print(f'   Size: {artifact.file_size:,} bytes | Collected: {artifact.collected_at.strftime(\"%Y-%m-%d %H:%M\")}')
    print(f'   Nectar: {artifact.nectar_id} | Worker: {artifact.worker_id}')
    print()
"
    
    if ! $PYTHON_CMD -c "$python_script"; then
        log "ERROR" "Listing failed"
        return 1
    fi
    
    log "INFO" "Listing completed"
}

cleanup_honey() {
    local days_to_keep="${1:-30}"
    
    if ! [[ "$days_to_keep" =~ ^[0-9]+$ ]]; then
        log "ERROR" "Days must be a positive integer"
        return 1
    fi
    
    log "INFO" "Cleaning up honey artifacts older than $days_to_keep days..."
    
    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        log "INFO" "DRY RUN: Would cleanup artifacts older than $days_to_keep days"
        return 0
    fi
    
    local python_script="
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from queen.honey_collector import HoneyCollector

collector = HoneyCollector()
deleted_count = collector.cleanup_old_honey($days_to_keep)

print(f'Cleaned up {deleted_count} old honey artifacts')
"
    
    if ! $PYTHON_CMD -c "$python_script"; then
        log "ERROR" "Cleanup failed"
        return 1
    fi
    
    log "INFO" "Cleanup completed"
}

# =============================================================================
# オプション解析
# =============================================================================

parse_args() {
    COMMAND=""
    FILES=()
    NECTAR_ID=""
    HONEY_TYPE=""
    FORMAT="table"
    OUTPUT_FILE=""
    VERBOSE=false
    DRY_RUN=false
    QUALITY_THRESHOLD=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            auto|manual|report|stats|list|cleanup|help)
                COMMAND="$1"
                shift
                ;;
            --nectar-id)
                NECTAR_ID="$2"
                shift 2
                ;;
            --type)
                HONEY_TYPE="$2"
                shift 2
                ;;
            --format)
                FORMAT="$2"
                shift 2
                ;;
            --output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            --quality-threshold)
                QUALITY_THRESHOLD="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help)
                print_usage
                exit 0
                ;;
            -*)
                log "ERROR" "Unknown option: $1"
                print_usage
                exit 1
                ;;
            *)
                FILES+=("$1")
                shift
                ;;
        esac
    done
    
    if [[ -z "$COMMAND" ]]; then
        COMMAND="help"
    fi
}

# =============================================================================
# メイン実行
# =============================================================================

main() {
    parse_args "$@"
    
    print_header
    
    case $COMMAND in
        auto)
            check_dependencies
            ensure_hive_structure
            collect_auto
            ;;
        manual)
            check_dependencies
            ensure_hive_structure
            collect_manual "${FILES[@]}"
            ;;
        report)
            check_dependencies
            generate_report
            ;;
        stats)
            check_dependencies
            show_stats
            ;;
        list)
            check_dependencies
            list_honey
            ;;
        cleanup)
            check_dependencies
            cleanup_honey "${FILES[0]:-30}"
            ;;
        help)
            print_usage
            ;;
        *)
            log "ERROR" "Unknown command: $COMMAND"
            print_usage
            exit 1
            ;;
    esac
    
    log "INFO" "Command completed successfully"
    
    if [[ "${VERBOSE:-false}" == "true" ]]; then
        echo -e "\n${CYAN}📝 Log file: $LOG_FILE${NC}"
    fi
}

# スクリプトが直接実行された場合のみmainを呼び出し
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi