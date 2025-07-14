# 🔧 Hive トラブルシューティングガイド

## 📋 目次

1. [一般的な問題](#一般的な問題)
2. [環境・インストール問題](#環境インストール問題)
3. [tmux関連の問題](#tmux関連の問題)
4. [通信・Comb問題](#通信comb問題)
5. [パフォーマンス問題](#パフォーマンス問題)
6. [ログ分析](#ログ分析)
7. [緊急時対応](#緊急時対応)

## 🚨 一般的な問題

### 問題1: Hiveが起動しない

#### 症状
```bash
./scripts/start-small-hive.sh
# エラーで終了、またはセッションが作成されない
```

#### 原因と対処法

**原因1: 依存関係不足**
```bash
# 確認
./scripts/check-dependencies.sh

# 対処
# macOS
brew install tmux python3 git
# Ubuntu
sudo apt install tmux python3 git
```

**原因2: 実行権限なし**
```bash
# 確認
ls -la scripts/

# 対処
chmod +x scripts/*.sh
```

**原因3: ディレクトリ権限問題**
```bash
# 確認
ls -la .hive/

# 対処
chmod -R 755 .hive/
mkdir -p .hive/{comb,nectar,honey,logs}
```

### 問題2: Claude Code認証エラー

#### 症状
```
Authentication failed: Invalid credentials
Claude Code API key not found
```

#### 対処法
```bash
# 認証リセット
claude-code auth logout
claude-code auth login

# 設定確認
claude-code auth status
cat ~/.claude/config.json

# 手動設定ファイル修正
vim ~/.claude/config.json
chmod 600 ~/.claude/config.json
```

### 問題3: Worker間通信が機能しない

#### 症状
- メッセージが送受信されない
- `receive_messages()` が空のリストを返す
- Worker間でタスクが共有されない

#### 診断手順
```bash
# 1. Combディレクトリ構造確認
ls -la .hive/comb/messages/
ls -la .hive/comb/messages/{inbox,outbox,sent,failed}/

# 2. 権限確認
chmod -R 755 .hive/

# 3. 通信テスト
python3 << 'EOF'
from comb import CombAPI
api = CombAPI("test")
print("API初期化成功")

# テストメッセージ
result = api.send_message(
    to_worker="test_target",
    content={"test": "hello"},
    message_type="request"
)
print(f"メッセージ送信: {result}")
EOF
```

## 🌍 環境・インストール問題

### Python環境問題

#### 問題: ImportError - モジュールが見つからない
```python
ImportError: No module named 'comb'
ModuleNotFoundError: No module named 'queen'
```

#### 対処法
```bash
# 1. パスの確認・設定
echo $PYTHONPATH
export PYTHONPATH="$PWD:$PYTHONPATH"
echo 'export PYTHONPATH="$PWD:$PYTHONPATH"' >> ~/.bashrc

# 2. 仮想環境の確認
which python3
python3 -m venv --help

# 3. 依存関係の再インストール
pip install --force-reinstall -r requirements.txt

# 4. モジュールの手動確認
python3 -c "import sys; print('\n'.join(sys.path))"
```

#### 問題: Python バージョン不整合
```bash
# 現在のバージョン確認
python3 --version
which python3

# 正しいバージョンのインストール (macOS)
brew install python@3.9

# パスの調整
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Claude Code インストール問題

#### 問題: claude-code コマンドが見つからない
```bash
# 1. インストール状況確認
which claude-code
echo $PATH

# 2. 手動パス追加
export PATH="/Applications/Claude\ Code.app/Contents/MacOS:$PATH"

# 3. 再インストール
curl -fsSL https://claude.ai/install.sh | sh

# 4. システム再起動後の確認
source ~/.bashrc
source ~/.zshrc
```

## 📺 tmux関連の問題

### tmux セッション管理問題

#### 問題: セッションが既に存在する
```bash
# エラー: session already exists
tmux: duplicate session: hive-small-colony
```

#### 対処法
```bash
# 1. 既存セッションの確認
tmux list-sessions

# 2. セッションの強制終了
tmux kill-session -t hive-small-colony

# 3. すべてのセッション終了
tmux kill-server

# 4. 強制再起動
./scripts/start-small-hive.sh --force
```

#### 問題: tmux pane分割失敗
```bash
# エラー: can't split window
```

#### 対処法
```bash
# 1. tmux設定確認
tmux info | grep -E "(version|config)"

# 2. 最小ウィンドウサイズ確認
# ターミナルサイズを80x24以上に調整

# 3. tmux設定リセット
mv ~/.tmux.conf ~/.tmux.conf.backup
tmux source-file ~/.tmux.conf
```

### tmux操作問題

#### 問題: pane間の移動ができない
```bash
# 基本操作の確認
# Ctrl+B → 矢印キー (pane移動)
# Ctrl+B → d (セッション終了)
# Ctrl+B → ? (ヘルプ)

# カスタムキーバインド追加
cat >> ~/.tmux.conf << 'EOF'
# vi風pane移動
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R
EOF

tmux source-file ~/.tmux.conf
```

## 🔗 通信・Comb問題

### メッセージ配信問題

#### 問題: メッセージが届かない

#### 診断手順
```bash
# 1. メッセージディレクトリの確認
find .hive/comb/messages -name "*.json" | head -10

# 2. メッセージ内容の確認
cat .hive/comb/messages/outbox/*.json | jq .

# 3. 権限問題の確認
ls -la .hive/comb/messages/
chmod -R 755 .hive/comb/

# 4. ディスク容量の確認
df -h .
du -sh .hive/
```

#### 手動メッセージテスト
```python
import json
from pathlib import Path
from datetime import datetime

# テストメッセージ作成
test_message = {
    "id": "test-123",
    "from_worker": "test_sender",
    "to_worker": "test_receiver",
    "message_type": "request",
    "priority": 2,
    "content": {"test": "manual_message"},
    "timestamp": datetime.now().isoformat()
}

# 手動でメッセージファイル作成
outbox_dir = Path(".hive/comb/messages/outbox")
outbox_dir.mkdir(parents=True, exist_ok=True)

with open(outbox_dir / "test-message.json", "w") as f:
    json.dump(test_message, f, indent=2)

print("テストメッセージを作成しました")
```

### Nectar管理問題

#### 問題: Nectarが処理されない

#### 診断と対処
```bash
# 1. Nectarディレクトリ状況確認
ls -la .hive/nectar/{pending,active,completed}/

# 2. Nectar処理状況の確認
find .hive/nectar -name "*.json" -exec basename {} \; | sort

# 3. 手動Nectar処理テスト
python3 << 'EOF'
from comb import CombAPI

api = CombAPI("debug_worker")

# Nectar送信テスト
result = api.send_nectar(
    nectar_type="test_task",
    content={"test": "debug_nectar"},
    priority="low"
)
print(f"Nectar送信: {result}")

# Nectar受信テスト
nectar = api.receive_nectar()
print(f"Nectar受信: {nectar}")
EOF
```

## ⚡ パフォーマンス問題

### 応答速度低下

#### 症状
- メッセージ送受信が遅い
- Worker起動に時間がかかる
- ファイル操作が重い

#### 対処法

**1. ファイルシステム最適化**
```bash
# 古いログファイルの削除
find .hive/logs -name "*.log" -mtime +7 -delete

# 古いメッセージファイルの削除
find .hive/comb/messages/sent -name "*.json" -mtime +1 -delete

# ディスク使用量の確認
du -sh .hive/*
```

**2. メッセージキューの最適化**
```python
# メッセージ清理スクリプト
from pathlib import Path
from datetime import datetime, timedelta
import json

def cleanup_old_messages(days_to_keep=3):
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    message_dirs = [
        Path(".hive/comb/messages/sent"),
        Path(".hive/comb/messages/failed")
    ]
    
    deleted_count = 0
    for msg_dir in message_dirs:
        for msg_file in msg_dir.glob("*.json"):
            try:
                # ファイルのタイムスタンプ確認
                file_time = datetime.fromtimestamp(msg_file.stat().st_mtime)
                if file_time < cutoff_date:
                    msg_file.unlink()
                    deleted_count += 1
            except Exception as e:
                print(f"ファイル削除エラー {msg_file}: {e}")
    
    print(f"古いメッセージファイル {deleted_count} 件を削除しました")

cleanup_old_messages()
```

**3. メモリ使用量最適化**
```bash
# プロセス監視
ps aux | grep python
ps aux | grep tmux

# メモリ使用量確認
free -h  # Linux
vm_stat | head -10  # macOS

# 不要なプロセスの終了
pkill -f "python.*comb"
tmux kill-server
```

### CPU使用率問題

#### 対処法
```bash
# CPU使用率の監視
top -p $(pgrep -f python)

# ポーリング間隔の調整
python3 << 'EOF'
from comb import CombAPI

api = CombAPI("optimized_worker")
# デフォルト1秒から2秒に変更
api.start_polling(interval=2.0)
EOF
```

## 📊 ログ分析

### ログファイルの場所
```bash
# 主要ログディレクトリ
.hive/logs/                     # 一般ログ
.hive/comb/communication_logs/  # 通信ログ
.hive/work_logs/               # 作業ログ
```

### ログ分析コマンド

#### エラーログの抽出
```bash
# エラーメッセージの検索
grep -r "ERROR" .hive/logs/ | tail -20

# 通信エラーの検索
grep -r "failed\|error" .hive/comb/communication_logs/

# タイムスタンプ順でのエラー確認
find .hive/logs -name "*.log" -exec grep -H "ERROR" {} \; | sort
```

#### パフォーマンス分析
```bash
# メッセージ統計
find .hive/comb/messages -name "*.json" | wc -l

# ファイルサイズ分析
du -sh .hive/comb/messages/*

# 最近のアクティビティ
find .hive -name "*.json" -mtime -1 | head -10
```

### ログレベルの調整
```python
import logging

# デバッグレベルの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.hive/logs/debug.log'),
        logging.StreamHandler()
    ]
)

# 環境変数での制御
import os
os.environ['HIVE_LOG_LEVEL'] = 'DEBUG'
```

## 🆘 緊急時対応

### 完全リセット手順

#### 全てをリセットして再開
```bash
# 1. すべてのプロセス終了
tmux kill-server
pkill -f python
pkill -f claude-code

# 2. Hiveデータのバックアップ
mv .hive .hive.backup.$(date +%Y%m%d_%H%M%S)

# 3. 設定リセット
rm -rf .hive/
./scripts/start-small-hive.sh --force

# 4. 動作確認
./scripts/check-comb.sh
```

### データ復旧

#### 重要なデータの復旧
```bash
# 1. バックアップから作業ログを復旧
cp -r .hive.backup.*/work_logs/ .hive/

# 2. 完了したHoneyの復旧
cp -r .hive.backup.*/honey/ .hive/

# 3. 重要な設定の復旧
cp .hive.backup.*/comb/config.json .hive/comb/ 2>/dev/null || true
```

### ヘルスチェックスクリプト

```bash
#!/bin/bash
# health-check.sh - Hive全体のヘルスチェック

echo "🐝 Hive Health Check"
echo "==================="

# 1. tmux セッション確認
if tmux has-session -t hive-small-colony 2>/dev/null; then
    echo "✅ tmux session: OK"
    pane_count=$(tmux list-panes -t hive-small-colony | wc -l)
    echo "   Panes: $pane_count"
else
    echo "❌ tmux session: NOT FOUND"
fi

# 2. ディレクトリ構造確認
for dir in .hive .hive/comb .hive/nectar .hive/honey .hive/logs; do
    if [[ -d "$dir" ]]; then
        echo "✅ Directory $dir: OK"
    else
        echo "❌ Directory $dir: MISSING"
    fi
done

# 3. 通信テスト
python3 << 'EOF'
try:
    from comb import CombAPI
    api = CombAPI("health_check")
    print("✅ CombAPI: OK")
    
    # 基本機能テスト
    result = api.send_message(
        to_worker="test",
        content={"health_check": True},
        message_type="request"
    )
    if result:
        print("✅ Message sending: OK")
    else:
        print("❌ Message sending: FAILED")
        
except Exception as e:
    print(f"❌ CombAPI: ERROR - {e}")
EOF

# 4. ディスク容量確認
disk_usage=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
if [[ $disk_usage -lt 90 ]]; then
    echo "✅ Disk usage: OK ($disk_usage%)"
else
    echo "⚠️ Disk usage: HIGH ($disk_usage%)"
fi

echo "==================="
echo "Health check completed"
```

### 問題報告テンプレート

問題が解決しない場合は、以下の情報を含めてIssueを作成してください：

```markdown
## 🐛 Bug Report

### 環境情報
- OS: [macOS/Linux/バージョン]
- Python: [バージョン]
- tmux: [バージョン]
- Claude Code: [バージョン]

### 問題の詳細
[発生している問題の詳細な説明]

### 再現手順
1. 
2. 
3. 

### 期待される動作
[期待していた動作]

### 実際の動作
[実際に起こった動作]

### ログ出力
```
[関連するログ出力]
```

### 試行した対処法
[試行済みの対処法があれば記載]

### 追加情報
[その他の関連情報]
```

## 📚 その他のリソース

- **[セットアップガイド](setup-guide.md)** - 環境構築の詳細
- **[Comb API仕様](comb-api.md)** - 通信システムの詳細
- **[クイックスタート](../README-basic.md)** - 基本操作
- **GitHub Issues** - コミュニティサポート

**🍯 問題解決でより良いHive体験を！**