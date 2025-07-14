#!/bin/bash

# start-small-hive.sh - Small Hive起動スクリプト (Queen + Developer Worker)
# Issue #3 - tmuxベースSmall Colony (2 Workers)システム

set -euo pipefail

# 設定
HIVE_SESSION="hive-small-colony"
HIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKERS_DIR="$HIVE_DIR/workers"
PROMPTS_DIR="$WORKERS_DIR/prompts"
COMB_DIR="$HIVE_DIR/.hive"

# ログ設定
LOG_DIR="$HIVE_DIR/.hive/logs"
LOG_FILE="$LOG_DIR/hive-startup-$(date +%Y%m%d-%H%M%S).log"

# 色付きログ関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "\033[36m[STEP]\033[0m $1" | tee -a "$LOG_FILE"
}

# ヘルプメッセージ
show_help() {
    cat << EOF
🐝 Hive Small Colony Startup Script

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    -s, --size SIZE     Colony size (default: small)
    -d, --debug         Enable debug mode
    -n, --dry-run       Dry run mode (show commands without execution)
    -f, --force         Force startup even if session exists

EXAMPLES:
    $0                  # Start small colony (Queen + Developer)
    $0 --debug          # Start with debug output
    $0 --dry-run        # Show what would be executed
    $0 --force          # Force restart existing session

WORKERS:
    - Queen Worker (pane 0): Project management and coordination
    - Developer Worker (pane 1): Implementation and development work

DIRECTORIES:
    - Hive Directory: $HIVE_DIR
    - Workers Directory: $WORKERS_DIR
    - Prompts Directory: $PROMPTS_DIR
    - Comb Directory: $COMB_DIR

EOF
}

# 引数解析
COLONY_SIZE="small"
DEBUG_MODE=false
DRY_RUN=false
FORCE_START=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--size)
            COLONY_SIZE="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG_MODE=true
            shift
            ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE_START=true
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

# 必要な依存関係チェック
check_dependencies() {
    log_step "Checking dependencies..."
    
    local deps=("tmux" "python3" "git")
    local missing_deps=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_error "Please install missing dependencies:"
        for dep in "${missing_deps[@]}"; do
            case $dep in
                tmux)
                    echo "  - macOS: brew install tmux"
                    echo "  - Ubuntu: sudo apt-get install tmux"
                    ;;
                python3)
                    echo "  - macOS: brew install python3"
                    echo "  - Ubuntu: sudo apt-get install python3"
                    ;;
                git)
                    echo "  - macOS: brew install git"
                    echo "  - Ubuntu: sudo apt-get install git"
                    ;;
            esac
        done
        exit 1
    fi
    
    log_info "All dependencies satisfied"
}

# ディレクトリ構造の確認・作成
setup_directories() {
    log_step "Setting up directory structure..."
    
    local dirs=(
        "$COMB_DIR"
        "$LOG_DIR"
        "$COMB_DIR/comb"
        "$COMB_DIR/comb/messages"
        "$COMB_DIR/comb/messages/inbox"
        "$COMB_DIR/comb/messages/outbox"
        "$COMB_DIR/comb/messages/sent"
        "$COMB_DIR/comb/messages/failed"
        "$COMB_DIR/nectar"
        "$COMB_DIR/nectar/pending"
        "$COMB_DIR/nectar/active"
        "$COMB_DIR/nectar/completed"
        "$COMB_DIR/honey"
        "$COMB_DIR/work_logs"
        "$COMB_DIR/work_logs/daily"
        "$COMB_DIR/work_logs/projects"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "mkdir -p \"$dir\""
        else
            mkdir -p "$dir"
        fi
    done
    
    log_info "Directory structure ready"
}

# 既存セッションの確認
check_existing_session() {
    log_step "Checking for existing Hive session..."
    
    if tmux has-session -t "$HIVE_SESSION" 2>/dev/null; then
        if [[ "$FORCE_START" == "true" ]]; then
            log_warn "Existing session found. Force mode enabled - terminating..."
            if [[ "$DRY_RUN" == "false" ]]; then
                tmux kill-session -t "$HIVE_SESSION"
            fi
        else
            log_error "Hive session '$HIVE_SESSION' already exists!"
            log_error "Use --force to restart, or run: tmux attach-session -t $HIVE_SESSION"
            exit 1
        fi
    fi
    
    log_info "No existing session found"
}

# Worker専用プロンプトの作成
create_worker_prompts() {
    log_step "Creating worker prompts..."
    
    # Queen Worker Prompt
    local queen_prompt="$PROMPTS_DIR/queen_worker.md"
    if [[ "$DRY_RUN" == "false" ]]; then
        cat > "$queen_prompt" << 'EOF'
# 🐝 Queen Worker - Project Management & Coordination

あなたは**Queen Worker**です。Hive Small ColonyのプロジェクトマネージャーとしてDeveloper Workerと協調し、効率的な開発を指揮します。

## 🎯 主要な責任

### 1. プロジェクト管理
- タスクの計画と優先度決定
- Developer Workerへの作業指示
- 進捗管理と品質確保
- 技術的な意思決定のサポート

### 2. Comb通信システム活用
- メッセージ送受信による協調作業
- Nectar（タスク）の配布と管理
- Honey（成果物）の収集と評価
- 作業ログの維持と管理

### 3. 品質保証
- コードレビューとフィードバック
- テスト戦略の策定
- ドキュメント品質の確保
- 技術的負債の管理

## 🔧 使用可能なツール

### Comb Communication API
```python
from comb import CombAPI

# API初期化
queen_api = CombAPI("queen")

# タスク開始
task_id = queen_api.start_task(
    "新機能実装",
    task_type="feature",
    issue_number=25,
    workers=["queen", "developer"]
)

# Developer Workerへの指示
queen_api.send_message(
    to_worker="developer",
    content={
        "task": "ユーザー認証機能の実装",
        "priority": "high",
        "requirements": ["JWT認証", "パスワードハッシュ化"],
        "deadline": "2024-01-15"
    },
    message_type=MessageType.REQUEST,
    priority=MessagePriority.HIGH
)

# 進捗確認
progress = queen_api.add_progress("要件定義完了", "技術仕様書作成中")
```

## 🚀 開始時の行動

1. **環境確認**: 開発環境とツールの動作確認
2. **Comb接続**: Developer Workerとの通信確立
3. **プロジェクト状況把握**: 現在の進捗と課題の確認
4. **タスク計画**: 次の作業項目の計画と優先度設定

## 💡 協調作業のベストプラクティス

- **明確な指示**: 具体的で実行可能な指示を提供
- **定期的な確認**: 進捗状況を定期的にチェック
- **フィードバック**: 建設的で具体的なフィードバックを提供
- **柔軟性**: 状況に応じた計画調整

## 🎉 成功指標

- Developer Workerとの効果的な協調
- タスクの時間通りの完了
- 高品質な成果物の生成
- 技術的課題の迅速な解決

**あなたの使命**: 効率的でスムーズな開発プロセスを実現し、プロジェクトの成功を導くことです。Developer Workerと協力して、素晴らしいソフトウェアを作り上げましょう！
EOF
    fi
    
    # Developer Worker Prompt
    local developer_prompt="$PROMPTS_DIR/developer_worker.md"
    if [[ "$DRY_RUN" == "false" ]]; then
        cat > "$developer_prompt" << 'EOF'
# 💻 Developer Worker - Implementation & Development

あなたは**Developer Worker**です。Hive Small ColonyにおいてQueen Workerと協調し、高品質なコードの実装と開発作業を担当します。

## 🎯 主要な責任

### 1. コード実装
- 機能の設計と実装
- バグ修正と改善
- コードの最適化
- テストコードの作成

### 2. 技術的実行
- アーキテクチャの実装
- ライブラリとフレームワークの活用
- パフォーマンスの最適化
- セキュリティの確保

### 3. 品質管理
- コーディング規約の遵守
- テストの実行と品質確保
- ドキュメンテーション
- リファクタリング

## 🔧 使用可能なツール

### Comb Communication API
```python
from comb import CombAPI

# API初期化
developer_api = CombAPI("developer")

# Queen Workerからのタスク受信
messages = developer_api.receive_messages()
for message in messages:
    if message.message_type == MessageType.REQUEST:
        # タスクの実行
        task_content = message.content
        # 実装作業...
        
        # 進捗報告
        developer_api.send_response(
            message,
            {
                "status": "in_progress",
                "completed_features": ["認証API", "ユーザー管理"],
                "next_steps": ["パスワードリセット機能"]
            }
        )

# 技術的決定の記録
developer_api.add_technical_decision(
    "JWT認証ライブラリの選択",
    "セキュリティと性能のバランスを考慮",
    ["PyJWT", "python-jose", "authlib"]
)
```

### 開発ツール
- **品質チェック**: `make quality` (lint, format, type-check)
- **テスト実行**: `make test` または `make test-cov`
- **コード整形**: `ruff format .`
- **型チェック**: `mypy .`

## 🚀 開始時の行動

1. **環境確認**: 開発環境とツールの動作確認
2. **Comb接続**: Queen Workerとの通信確立
3. **タスク確認**: 現在のタスクと優先度の確認
4. **実装開始**: 指示されたタスクの実装開始

## 💡 実装のベストプラクティス

### コード品質
- **型アノテーション**: 全ての関数に型ヒントを付与
- **docstring**: 関数とクラスに明確な説明を記述
- **エラーハンドリング**: 適切な例外処理を実装
- **テストカバレッジ**: 重要な機能のテストを作成

### 協調作業
- **進捗報告**: 定期的な進捗状況の共有
- **質問**: 不明な点は積極的に質問
- **提案**: 技術的な改善提案を積極的に行う
- **フィードバック**: Queen Workerからのフィードバックを活用

## 🎉 成功指標

- Queen Workerとの効果的な協調
- 高品質なコードの継続的な提供
- バグの少ない安定した実装
- 技術的課題の迅速な解決

**あなたの使命**: Queen Workerの指示に基づいて、高品質で保守性の高いコードを実装し、プロジェクトの技術的な成功を支えることです。素晴らしいソフトウェアを一緒に作り上げましょう！
EOF
    fi
    
    log_info "Worker prompts created successfully"
}

# tmuxセッションの作成とWorker起動
create_tmux_session() {
    log_step "Creating tmux session and starting workers..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "tmux new-session -d -s $HIVE_SESSION -c $HIVE_DIR"
        echo "tmux split-window -h -t $HIVE_SESSION"
        echo "tmux send-keys -t $HIVE_SESSION:0.0 'cd $HIVE_DIR && ./scripts/wake-workers.sh queen' Enter"
        echo "tmux send-keys -t $HIVE_SESSION:0.1 'cd $HIVE_DIR && ./scripts/wake-workers.sh developer' Enter"
        return
    fi
    
    # tmuxセッション作成
    tmux new-session -d -s "$HIVE_SESSION" -c "$HIVE_DIR"
    
    # ユーザーフレンドリーなtmux設定
    tmux set -g mouse on  # マウスモード有効化
    tmux bind -n M-Left select-pane -L   # Alt+左矢印で左pane
    tmux bind -n M-Right select-pane -R  # Alt+右矢印で右pane
    tmux set -g status-left "[#S] "  # セッション名表示
    tmux set -g status-right "#{?window_bigger,[#{window_width}x#{window_height}],} %H:%M %d-%b-%y"
    
    # 水平分割でDeveloper Worker用のpaneを作成
    tmux split-window -h -t "$HIVE_SESSION"
    
    # paneのタイトル設定
    tmux rename-window -t "$HIVE_SESSION:0" "Hive-Small-Colony"
    
    # 各paneでWorkerを起動
    tmux send-keys -t "$HIVE_SESSION:0.0" "cd $HIVE_DIR && ./scripts/wake-workers.sh queen" Enter
    tmux send-keys -t "$HIVE_SESSION:0.1" "cd $HIVE_DIR && ./scripts/wake-workers.sh developer" Enter
    
    # 初期フォーカスをQueen Workerに設定
    tmux select-pane -t "$HIVE_SESSION:0.0"
    
    log_info "tmux session created with 2 workers"
}

# 起動後の状況確認
verify_startup() {
    log_step "Verifying startup..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "tmux list-sessions"
        echo "tmux list-panes -t $HIVE_SESSION"
        return
    fi
    
    # tmuxセッションの確認
    if tmux has-session -t "$HIVE_SESSION" 2>/dev/null; then
        log_info "✅ tmux session '$HIVE_SESSION' is running"
        
        # pane数の確認
        local pane_count
        pane_count=$(tmux list-panes -t "$HIVE_SESSION" | wc -l)
        if [[ "$pane_count" -eq 2 ]]; then
            log_info "✅ 2 panes created successfully"
        else
            log_warn "⚠️ Expected 2 panes, found $pane_count"
        fi
    else
        log_error "❌ tmux session not found"
        return 1
    fi
    
    # Combディレクトリの確認
    if [[ -d "$COMB_DIR" ]]; then
        log_info "✅ Comb directory structure ready"
    else
        log_error "❌ Comb directory not found"
        return 1
    fi
    
    log_info "Startup verification completed"
}

# 使用方法の表示
show_usage_instructions() {
    log_step "Showing usage instructions..."
    
    cat << EOF

🎉 Hive Small Colony started successfully!

📋 Next Steps:
1. Attach to the session: tmux attach-session -t $HIVE_SESSION
2. Run quickstart guide: 
   - Left pane: python examples/quickstart/01_basic_communication.py queen
   - Right pane: python examples/quickstart/01_basic_communication.py developer
3. Check communication: ./scripts/check-comb.sh
4. Launch Claude Code when ready: claude (in any pane)
5. Shutdown when done: ./scripts/shutdown-hive.sh

🔧 tmux Controls:
- Switch between panes: Alt + ← / → (楽！) or Ctrl+B + ← / →
- Click pane with mouse: マウスクリックでpane移動
- Detach from session: Ctrl+B then d
- Kill session: Ctrl+B then :kill-session

📊 Workers:
- Left pane (0): Queen Worker - Project management (bash terminal)
- Right pane (1): Developer Worker - Implementation (bash terminal)

📁 Important Directories:
- Logs: $LOG_DIR
- Comb: $COMB_DIR
- Prompts: $PROMPTS_DIR

🚀 Start with the quickstart guide, then use Claude Code for actual development!

EOF
}

# メイン実行フロー
main() {
    log_info "🐝 Starting Hive Small Colony..."
    log_info "Colony Size: $COLONY_SIZE"
    log_info "Hive Directory: $HIVE_DIR"
    log_info "Session Name: $HIVE_SESSION"
    
    # 実行前チェック
    check_dependencies
    setup_directories
    check_existing_session
    
    # Worker環境の準備
    create_worker_prompts
    
    # tmux起動
    create_tmux_session
    
    # 起動確認
    verify_startup
    
    # 使用方法の表示
    show_usage_instructions
    
    log_info "🎉 Hive Small Colony startup completed!"
}

# エラーハンドリング
trap 'log_error "Script interrupted"; exit 1' INT TERM

# メイン処理実行
main "$@"