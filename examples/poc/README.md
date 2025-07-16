# 🎯 新アーキテクチャ PoC (Proof of Concept)

## 概要

新アーキテクチャ（プロトコル定義システム + 分散エージェント）によるPoC実装です。BeeKeeper-Queen-Worker協調による自然言語Issue解決を実現します。

## 📁 ファイル構成

### 🚀 メインデモ
- **`demo_issue_solver.py`**: Issue解決デモ（一括実行）
- **`issue_solver_agent.py`**: Issue解決エージェント（自然言語対応）

### 🔧 基盤デモ
- **`claude_daemon_demo.py`**: Claude永続デーモンデモ
- **`tmux_demo.py`**: tmux統合デモ

### 📖 ドキュメント
- **`README_issue_solver.md`**: Issue解決エージェントの詳細ドキュメント

## 🚀 実行方法

### 1. 基盤確認
```bash
# 新プロトコルテスト
python examples/tests/protocols_test.py

# 分散エージェント起動
./scripts/start_hive_distributed.sh
```

### 2. メインデモ実行
```bash
# 一括デモ実行
python examples/poc/demo_issue_solver.py

# 自然言語指示
python examples/poc/issue_solver_agent.py "Issue 64を解決する"
```

### 3. 個別デモ実行
```bash
# Claude永続デーモン
python examples/poc/claude_daemon_demo.py

# tmux統合
python examples/poc/tmux_demo.py
```

## 🎯 新アーキテクチャの実現内容

### BeeKeeper体験
```bash
# 自然言語でIssue解決指示
python examples/poc/issue_solver_agent.py "緊急でissue 64を直してほしい"

# 期待される体験フロー
BeeKeeper: "Issue 64を解決する"
Queen: "承知しました。分析中..."
Queen: "3つのWorkerで並列実行します"
Queen: "実装完了、テスト通過、PR準備完了"
BeeKeeper: "ありがとう！確認します"
```

### 分散処理の実現
- **Queen**: 戦略策定・タスク分散・結果統合
- **Worker群**: 並列実行（実装・テスト・品質チェック）
- **プロトコル**: 統一メッセージ形式による通信

### 永続化・監視
- **tmux統合**: セッション永続化
- **Claude永続デーモン**: 常駐プロセス
- **リアルタイム監視**: 進捗・状態の即座把握

## 📖 詳細ドキュメント

- [Issue解決エージェント詳細](README_issue_solver.md)
- [新アーキテクチャ Issue解決ガイド](../../docs/new_architecture_issue_guide.md)
- [PoC実装ガイド](../../docs/poc-guide.md)

## 🔄 開発フロー

1. **プロトコル確認**: `examples/tests/protocols_test.py`
2. **分散環境起動**: `./scripts/start_hive_distributed.sh`
3. **デモ実行**: `examples/poc/demo_issue_solver.py`
4. **自然言語指示**: `examples/poc/issue_solver_agent.py`

---

**注意**: このディレクトリは新アーキテクチャ専用のPoC実装です。