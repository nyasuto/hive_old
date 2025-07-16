# 🔧 新アーキテクチャ トラブルシューティング

## 📋 目次

1. [新プロトコルシステム問題](#新プロトコルシステム問題)
2. [分散エージェント問題](#分散エージェント問題)
3. [Issue解決エージェント問題](#Issue解決エージェント問題)
4. [tmux統合問題](#tmux統合問題)
5. [Claude永続デーモン問題](#Claude永続デーモン問題)
6. [品質チェック問題](#品質チェック問題)
7. [緊急時対応](#緊急時対応)

## 🚨 新プロトコルシステム問題

### 問題1: プロトコルテストが失敗する

#### 症状
```bash
python examples/tests/protocols_test.py
# ❌ 一部のテストが失敗しました
```

#### 原因と対処法

**原因1: 型不整合エラー**
```bash
# 確認
python examples/tests/protocols_test.py
# AttributeError: 'str' object has no attribute 'value'

# 対処
# protocols/message_protocol.py の修正が必要
# MessageHeader.to_dict() での型チェック実装
```

**原因2: バリデーションエラー**
```bash
# 確認
python -c "
from protocols import MessageProtocol, ProtocolValidator
protocol = MessageProtocol()
validator = ProtocolValidator()
# メッセージ作成・検証テスト
"

# 対処
# config/protocol_config.yaml の設定確認
cat config/protocol_config.yaml
```

### 問題2: プロトコルメッセージ送信失敗

#### 症状
```python
# integration_success = False
```

#### 対処法
```bash
# 統合レイヤー確認
python -c "
from protocols import default_integration
result = default_integration.validate_integration()
print(f'Integration valid: {result.valid}')
if not result.valid:
    for error in result.errors:
        print(f'Error: {error}')
"
```

## 🔄 分散エージェント問題

### 問題1: 分散環境が起動しない

#### 症状
```bash
./scripts/start_hive_distributed.sh
# エラーで終了、またはセッションが作成されない
```

#### 原因と対処法

**原因1: tmux未インストール**
```bash
# 確認
tmux -V

# 対処（macOS）
brew install tmux

# 対処（Ubuntu）
sudo apt-get install tmux
```

**原因2: スクリプト権限問題**
```bash
# 確認
ls -la scripts/start_hive_distributed.sh

# 対処
chmod +x scripts/start_hive_distributed.sh
```

### 問題2: 通信確認が失敗する

#### 症状
```bash
./scripts/check-comb.sh
# ❌ Queen-Worker通信異常
```

#### 対処法
```bash
# セッション状態確認
tmux ls

# 手動セッション確認
tmux attach-session -t hive-distributed

# 再起動
./scripts/stop_hive_distributed.sh
./scripts/start_hive_distributed.sh
```

## 🎯 Issue解決エージェント問題

### 問題1: 自然言語指示が認識されない

#### 症状
```bash
python examples/poc/issue_solver_agent.py "Issue 64を解決する"
# 意図認識に失敗
```

#### 対処法
```bash
# デモモード実行
python examples/poc/demo_issue_solver.py

# インタラクティブモード
python examples/poc/issue_solver_agent.py
# プロンプト入力で詳細確認
```

### 問題2: GitHub API認証エラー

#### 症状
```
GitHub API authentication failed
```

#### 対処法
```bash
# 環境変数確認
echo $GITHUB_TOKEN

# 設定方法
export GITHUB_TOKEN="your_token_here"

# または .env ファイル作成
echo "GITHUB_TOKEN=your_token_here" > .env
```

## 🎪 tmux統合問題

### 問題1: tmuxセッションが作成されない

#### 症状
```bash
python examples/poc/tmux_demo.py
# セッション作成失敗
```

#### 対処法
```bash
# tmux 確認
tmux ls

# 既存セッション削除
tmux kill-session -t hive-test

# 手動セッション作成
tmux new-session -d -s hive-test
```

### 問題2: ペイン分割エラー

#### 症状
```
can't split a pane with no window
```

#### 対処法
```bash
# セッション存在確認
tmux has-session -t hive-test 2>/dev/null

# 手動ペイン分割
tmux split-window -h
tmux split-window -v
```

## 🔄 Claude永続デーモン問題

### 問題1: デーモンが起動しない

#### 症状
```bash
python examples/poc/claude_daemon_demo.py
# デーモン起動失敗
```

#### 対処法
```bash
# プロセス確認
ps aux | grep claude

# ポート確認
netstat -an | grep 8080

# 手動起動
python -c "
from examples.poc.claude_daemon_demo import ClaudeDaemon
daemon = ClaudeDaemon('test')
daemon.start()
"
```

### 問題2: ヘルスチェック失敗

#### 症状
```
Health check failed
```

#### 対処法
```bash
# デーモン状態確認
curl -s http://localhost:8080/health

# ログ確認
tail -f logs/claude_daemon.log

# 再起動
./scripts/stop_claude_daemon.sh
./scripts/start_claude_daemon.sh
```

## ✅ 品質チェック問題

### 問題1: make quality 失敗

#### 症状
```bash
make quality
# Error: mypy type check failed
```

#### 対処法
```bash
# 個別実行
make lint
make format
make type-check

# 具体的エラー確認
mypy --show-error-codes protocols/
```

### 問題2: テスト失敗

#### 症状
```bash
make test
# Some tests failed
```

#### 対処法
```bash
# 個別テスト実行
python -m pytest tests/protocols/ -v

# 特定テストクラス
python -m pytest tests/protocols/test_message_protocol.py::TestMessageProtocol -v

# カバレッジ確認
make test-cov
```

## 🆘 緊急時対応

### 完全リセット手順
```bash
# 1. 全セッション終了
tmux kill-server

# 2. プロセス確認・終了
ps aux | grep claude
kill -9 <pid>

# 3. 環境クリーンアップ
make clean

# 4. 再インストール
make install

# 5. 基盤確認
python examples/tests/protocols_test.py

# 6. 分散環境再起動
./scripts/start_hive_distributed.sh
```

### ログ確認方法
```bash
# システムログ
tail -f logs/system.log

# プロトコルログ
tail -f logs/protocol.log

# エージェントログ
tail -f logs/agents.log

# tmuxログ
tmux capture-pane -t hive-distributed -p
```

### 診断スクリプト
```bash
# 包括的診断
python -c "
import sys
print(f'Python: {sys.version}')

try:
    from protocols import MessageProtocol
    print('✅ Protocols import OK')
except Exception as e:
    print(f'❌ Protocols import failed: {e}')

try:
    import tmux
    print('✅ tmux available')
except ImportError:
    print('❌ tmux not available')
"
```

## 📞 サポート

### 問題報告
1. **エラーログ**: 完全なエラーメッセージ
2. **環境情報**: OS、Python バージョン
3. **実行コマンド**: 失敗したコマンド
4. **再現手順**: 問題の再現方法

### 問題解決のヒント
1. **段階的確認**: 基盤から順次確認
2. **ログ分析**: エラーメッセージの詳細確認
3. **環境切り分け**: 最小構成での動作確認
4. **リセット**: 完全リセット後の再試行

新アーキテクチャでは、問題の多くがプロトコルレベルで発生します。まずプロトコルテストの成功を確認してください。