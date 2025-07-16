# 🐝 Hive Examples - 新アーキテクチャ

## 概要

新アーキテクチャ（プロトコル定義システム + 分散エージェント）に基づくPoC実装とテストスクリプトを提供します。

## 📁 ディレクトリ構成

```
examples/
├── tests/                    # テストスクリプト
│   ├── protocols_test.py     # 新プロトコルシステムテスト
│   └── README.md
└── poc/                      # 新アーキテクチャPoC
    ├── demo_issue_solver.py  # Issue解決デモ（メイン）
    ├── issue_solver_agent.py # Issue解決エージェント
    ├── claude_daemon_demo.py # Claude永続デーモンデモ
    ├── tmux_demo.py          # tmux統合デモ
    └── README_issue_solver.md # Issue解決ドキュメント
```

## 🚀 クイックスタート

### 1. 新プロトコルシステム確認
```bash
# 新プロトコルの動作確認
python examples/tests/protocols_test.py
```

### 2. 分散エージェント環境起動
```bash
# 分散エージェント起動
./scripts/start_hive_distributed.sh

# 通信確認
./scripts/check-comb.sh
```

### 3. Issue解決デモ実行
```bash
# メインデモ実行
python examples/poc/demo_issue_solver.py

# 自然言語指示
python examples/poc/issue_solver_agent.py "Issue 64を解決する"
```

## 🎯 新アーキテクチャの特徴

### BeeKeeper - Queen - Worker 協調
- **BeeKeeper**: 自然言語による指示・成果物受け取り
- **Queen**: 戦略策定・タスク分散・結果統合
- **Worker**: 専門的な並列実行

### プロトコル定義システム
- **統一メッセージ形式**: MessageProtocol
- **厳密バリデーション**: ProtocolValidator
- **バージョン管理**: 互換性チェック

### 分散処理基盤
- **tmux統合**: セッション管理・永続化
- **Claude永続デーモン**: 常駐プロセス
- **Worker-paneマッピング**: 効率的な分散実行

## 📖 関連ドキュメント

- [新アーキテクチャ Issue解決ガイド](../docs/new_architecture_issue_guide.md)
- [PoC実装ガイド](../docs/poc-guide.md)
- [Issue解決エージェントドキュメント](poc/README_issue_solver.md)

## 🔧 トラブルシューティング

### プロトコルエラー
```bash
python examples/tests/protocols_test.py
```

### 分散エージェントエラー
```bash
./scripts/check-comb.sh
./scripts/start_hive_distributed.sh
```

---

**注意**: このディレクトリは新アーキテクチャ専用です。旧実装は削除されています。