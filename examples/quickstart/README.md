# 🐝 Hive Quickstart Examples

このディレクトリには、Hiveクイックスタートガイド用の実行可能なサンプルスクリプトが含まれています。

## 📁 ファイル構成

- `01_basic_communication.py` - Worker間の基本通信テスト
- `02_task_management.py` - タスク管理機能のテスト
- `03_check_results.py` - 成果物と動作確認

## 🚀 使用方法

### 前提条件
1. Hive Small Colonyが起動していること:
   ```bash
   ./scripts/start-small-hive.sh
   tmux attach-session -t hive-small-colony
   ```

### Step 1: 基本通信テスト

**左pane (Queen Worker):**
```bash
python examples/quickstart/01_basic_communication.py queen
```

**右pane (Developer Worker):**
```bash
python examples/quickstart/01_basic_communication.py developer
```

### Step 2: タスク管理テスト

**左pane (Queen Worker):**
```bash
python examples/quickstart/02_task_management.py queen
```

**右pane (Developer Worker):**
```bash
python examples/quickstart/02_task_management.py developer
```

### Step 3: 結果確認

**新しいターミナル:**
```bash
python examples/quickstart/03_check_results.py
```

## 🎯 期待する動作

### 01_basic_communication.py
- Queen Workerからメッセージ送信
- Developer Workerでメッセージ受信
- 基本的なWorker間通信の確認

### 02_task_management.py
- タスクの作成と管理
- 進捗報告と技術決定の記録
- Worker間でのタスク協調

### 03_check_results.py
- Combシステムの動作確認
- 生成されたログファイルの確認
- 成果物の統計表示

## 🔧 トラブルシューティング

### ImportError: No module named 'comb'
```bash
# プロジェクトルートで実行していることを確認
pwd  # /path/to/hive になっているはず

# パッケージをインストール
pip install -e .
```

### メッセージが送受信されない
```bash
# Combシステムの確認
./scripts/check-comb.sh --verbose

# ディレクトリ権限の確認
ls -la .hive/comb/messages/
```

### tmuxセッションが見つからない
```bash
# セッション一覧確認
tmux list-sessions

# 強制再起動
./scripts/shutdown-hive.sh --force
./scripts/start-small-hive.sh
```

## 📚 学習リソース

これらのサンプルを理解したら、次のステップに進みましょう:

- [Comb API仕様](../../docs/comb-api.md)
- [実用的な開発例](../web-app-hive/)
- [Full Colony設定](../../docs/setup-guide.md#full-colony)

## 💡 カスタマイズ

これらのスクリプトをベースに、独自の用途に合わせてカスタマイズできます:

1. **メッセージ内容の変更**: `content` パラメータを修正
2. **Worker数の追加**: 新しいworker_typeを追加
3. **タスクの複雑化**: より詳細なタスクフローを実装

Happy coding with Hive! 🍯