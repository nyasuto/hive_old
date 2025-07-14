# 🛠️ Hive セットアップガイド

## 📋 目次

1. [システム要件](#システム要件)
2. [環境構築](#環境構築)
3. [Claude Code設定](#claude-code設定)
4. [Hive設定](#hive設定)
5. [動作確認](#動作確認)
6. [トラブルシューティング](#トラブルシューティング)
7. [カスタマイズ](#カスタマイズ)

## 📱 システム要件

### 必須要件
- **OS**: macOS 10.15+ または Linux (Ubuntu 18.04+)
- **Python**: 3.9 以上
- **tmux**: 3.0 以上
- **Git**: 2.20 以上
- **Claude Code**: 最新版
- **メモリ**: 8GB 以上推奨

### 推奨要件
- **Claude プラン**: Claude Pro ($20/月) または Claude for Work
- **CPU**: マルチコア (4コア以上推奨)
- **ディスク**: 1GB 以上の空き容量
- **ネットワーク**: 安定したインターネット接続
- **ターミナル**: 大画面ディスプレイ (複数pane表示のため)

## 🔧 環境構築

### macOS での環境構築

#### 1. Homebrewのインストール
```bash
# Homebrewがない場合
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. 必要なツールのインストール
```bash
# 基本ツール
brew install tmux python3 git

# オプション（開発効率向上）
brew install tree htop jq

# Pythonのバージョン確認
python3 --version  # 3.9+ であることを確認
```

#### 3. tmux設定
```bash
# tmux設定ファイルの作成（オプション）
cat > ~/.tmux.conf << 'EOF'
# Hive用tmux設定
set -g default-terminal "screen-256color"
set -g mouse on
set -g base-index 1
setw -g pane-base-index 1

# pane切り替えをvi風に
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# ステータスバーの設定
set -g status-bg blue
set -g status-fg white
set -g status-left '#[fg=green]🐝 Hive '
set -g status-right '#[fg=yellow]%Y-%m-%d %H:%M'
EOF

# 設定の再読み込み
tmux source-file ~/.tmux.conf
```

### Linux (Ubuntu) での環境構築

#### 1. システムの更新
```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. 必要なツールのインストール
```bash
# 基本ツール
sudo apt install -y tmux python3 python3-pip git curl

# 開発ツール
sudo apt install -y build-essential software-properties-common

# Python バージョン確認
python3 --version
```

#### 3. Python環境の設定
```bash
# pip の更新
python3 -m pip install --upgrade pip

# 仮想環境ツール（オプション）
python3 -m pip install virtualenv

# Hive用仮想環境作成（オプション）
python3 -m venv hive-env
source hive-env/bin/activate
```

## 🤖 Claude Code設定

### 1. Claude Codeのインストール

#### 公式インストーラー使用
```bash
# 最新版のダウンロードとインストール
curl -fsSL https://claude.ai/install.sh | sh

# パスの確認
which claude-code
claude-code --version
```

#### 手動インストール（代替方法）
```bash
# Claude Code公式サイトからダウンロード
# https://claude.ai/code

# インストール後、パスを追加
echo 'export PATH="/path/to/claude-code:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Claude Code認証設定

#### API認証
```bash
# Claude Code初回起動時に認証
claude-code auth login

# 認証状況の確認
claude-code auth status
```

#### 設定ファイルの確認
```bash
# Claude Code設定ディレクトリ
ls -la ~/.claude/

# 設定ファイルの内容確認
cat ~/.claude/config.json
```

### 3. Claude Code動作確認
```bash
# 基本動作テスト
claude-code --help

# 簡単な対話テスト
claude-code
# → "Hello, how can I help you today?" のような応答を確認
# → "/exit" で終了
```

## 🐝 Hive設定

### 1. Hiveのクローン
```bash
# プロジェクトのクローン
git clone https://github.com/nyasuto/hive.git
cd hive

# ディレクトリ構造の確認
tree -L 2  # treeがない場合は ls -la
```

### 2. Python依存関係のインストール
```bash
# プロジェクトディレクトリで実行
cd hive

# 仮想環境の作成（推奨）
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS

# 依存関係のインストール
pip install -r requirements.txt

# 開発依存関係（オプション）
pip install -r requirements-dev.txt
```

### 3. スクリプトの実行権限設定
```bash
# 全スクリプトに実行権限を付与
chmod +x scripts/*.sh

# 個別確認
ls -la scripts/
```

### 4. 環境変数の設定
```bash
# .envファイルの作成（オプション）
cat > .env << 'EOF'
# Hive環境設定
HIVE_LOG_LEVEL=INFO
HIVE_MAX_WORKERS=6
HIVE_TIMEOUT=3600
CLAUDE_MODEL_NAME=claude-3-sonnet
EOF

# 環境変数の読み込み設定
echo 'export PYTHONPATH="$PWD:$PYTHONPATH"' >> ~/.bashrc
source ~/.bashrc
```

### 5. 初期ディレクトリ構造の作成
```bash
# Hiveディレクトリ構造の初期化
./scripts/init-hive.sh

# 作成されたディレクトリの確認
ls -la .hive/
```

## ✅ 動作確認

### 1. 基本機能テスト

#### 依存関係の確認
```bash
# 自動チェックスクリプト実行
./scripts/check-dependencies.sh

# 手動確認
python3 -c "import sys; print(f'Python: {sys.version}')"
tmux -V
git --version
claude-code --version
```

#### Pythonモジュールのテスト
```bash
# Hiveモジュールのインポートテスト
python3 -c "
from comb import CombAPI
from queen import TaskDistributor
print('✅ All modules imported successfully')
"
```

### 2. Small Colony起動テスト
```bash
# テスト起動
./scripts/start-small-hive.sh --dry-run

# 実際の起動
./scripts/start-small-hive.sh

# セッション確認
tmux list-sessions
tmux list-panes -t hive-small-colony
```

### 3. 通信テスト
```bash
# Comb通信システムのテスト
./scripts/check-comb.sh

# 基本的な通信テスト
python3 << 'EOF'
from comb import CombAPI
import json

# テストメッセージの送信
api = CombAPI("test_worker")
result = api.send_message(
    to_worker="test_target",
    content={"test": "hello"},
    message_type="test"
)
print(f"✅ Communication test: {result}")
EOF
```

### 4. Honey収集システムテスト
```bash
# Honey収集の動作確認
./scripts/collect-honey.sh --help

# テスト用ファイルで動作確認
echo "print('Hello Hive')" > test_honey.py
./scripts/collect-honey.sh manual test_honey.py
./scripts/collect-honey.sh stats
```

## 🔧 カスタマイズ

### 1. Worker設定のカスタマイズ

#### 新しいWorkerプロンプトの作成
```bash
# テンプレートをコピー
cp workers/prompts/developer_worker.md workers/prompts/my_worker.md

# プロンプトをカスタマイズ
vim workers/prompts/my_worker.md
```

#### カスタムWorkerの追加
```bash
# start-small-hive.sh を編集してWorkerを追加
vim scripts/start-small-hive.sh

# 新しいWorker用のpaneを追加する設定を記述
```

### 2. Comb通信のカスタマイズ

#### メッセージフォーマットの拡張
```python
# comb/message_router.py をカスタマイズ
# 新しいメッセージタイプや優先度の追加
```

#### ログレベルの調整
```bash
# ログレベルの設定
export HIVE_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARN, ERROR

# カスタムログ設定
cat > logging.conf << 'EOF'
[loggers]
keys=root,hive

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_hive]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=hive
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=simpleFormatter
args=('.hive/logs/hive.log',)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
EOF
```

### 3. プロジェクトテンプレートの作成
```bash
# 新しいプロジェクトタイプの追加
mkdir examples/my-project-hive
cp -r examples/web-app-hive/* examples/my-project-hive/

# Nectarテンプレートの作成
cat > templates/nectar-templates/my-task-template.json << 'EOF'
{
  "nectar_id": "nectar-{timestamp}-{random}",
  "title": "カスタムタスク",
  "description": "詳細な作業内容",
  "assigned_to": "my_worker",
  "created_by": "queen_worker",
  "priority": "medium",
  "status": "pending",
  "dependencies": [],
  "expected_honey": [
    "期待される成果物"
  ],
  "estimated_time": 2,
  "created_at": "{current_time}",
  "deadline": "{deadline}"
}
EOF
```

## 🚨 初期設定でよくある問題

### 問題1: Claude Code認証エラー
```bash
# 認証情報のリセット
claude-code auth logout
claude-code auth login

# 設定ファイルの確認
cat ~/.claude/config.json

# 権限の確認
ls -la ~/.claude/
chmod 600 ~/.claude/config.json
```

### 問題2: tmux起動失敗
```bash
# tmux設定の確認
tmux info

# セッションの強制終了
tmux kill-server

# 設定ファイルのチェック
tmux source-file ~/.tmux.conf
```

### 問題3: Python モジュールエラー
```bash
# パスの確認
echo $PYTHONPATH
export PYTHONPATH="$PWD:$PYTHONPATH"

# 仮想環境の確認
which python3
python3 -m site

# 依存関係の再インストール
pip install --force-reinstall -r requirements.txt
```

### 問題4: 権限エラー
```bash
# ディレクトリ権限の修正
chmod -R 755 .hive/
chmod +x scripts/*.sh

# SELinuxの確認（Linux）
sestatus  # Enabled の場合は設定調整が必要
```

## 📊 設定確認スクリプト

設定が正しく完了しているかを確認するスクリプト：

```bash
# 設定確認スクリプトの作成
cat > check-setup.sh << 'EOF'
#!/bin/bash

echo "🐝 Hive Setup Verification"
echo "=========================="

# 基本ツールの確認
echo "📋 Basic Tools:"
for tool in tmux python3 git claude-code; do
    if command -v $tool >/dev/null 2>&1; then
        version=$($tool --version 2>/dev/null | head -1)
        echo "  ✅ $tool: $version"
    else
        echo "  ❌ $tool: Not found"
    fi
done

# Python モジュールの確認
echo "🐍 Python Modules:"
for module in comb queen; do
    if python3 -c "import $module" 2>/dev/null; then
        echo "  ✅ $module: Available"
    else
        echo "  ❌ $module: Not found"
    fi
done

# ディレクトリ構造の確認
echo "📁 Directory Structure:"
for dir in .hive scripts workers queen comb; do
    if [[ -d "$dir" ]]; then
        echo "  ✅ $dir/: Exists"
    else
        echo "  ❌ $dir/: Missing"
    fi
done

# 実行権限の確認
echo "🔧 Script Permissions:"
for script in scripts/*.sh; do
    if [[ -x "$script" ]]; then
        echo "  ✅ $script: Executable"
    else
        echo "  ❌ $script: Not executable"
    fi
done

echo "=========================="
echo "Setup verification completed!"
EOF

chmod +x check-setup.sh
./check-setup.sh
```

## 🎯 次のステップ

設定が完了したら：

1. **[クイックスタートガイド](../README-basic.md)** で基本操作を確認
2. **[Comb API仕様](comb-api.md)** でWorker間通信を学習
3. **[実用例](../examples/)** でプロジェクト開発を実践
4. **[トラブルシューティング](troubleshooting.md)** で問題解決方法を確認

**🍯 Happy coding with Hive!**