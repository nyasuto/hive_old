# 🚀 新アーキテクチャ クイックスタート

## 概要

新アーキテクチャのHiveシステムを5分で起動し、BeeKeeper-Queen-Worker協調による自然言語Issue解決を体験できます。

## ⚡ 5分クイックスタート

### 1. 基盤確認 (1分)

```bash
# 新プロトコルシステムテスト
python examples/tests/protocols_test.py
```

**期待される出力:**
```
🎉 全テスト成功！新プロトコルシステムは正常に動作しています。

次のステップ:
1. python examples/poc/demo_issue_solver.py
2. ./scripts/check-comb.sh
3. python examples/poc/claude_daemon_demo.py
```

### 2. 分散エージェント起動 (2分)

```bash
# 分散環境起動
./scripts/start_hive_distributed.sh

# 通信確認
./scripts/check-comb.sh
```

**期待される出力:**
```
✅ 分散エージェント起動完了
✅ Queen-Worker通信正常
✅ プロトコルシステム稼働中
```

### 3. Issue解決デモ (2分)

```bash
# メインデモ実行
python examples/poc/demo_issue_solver.py

# または自然言語指示
python examples/poc/issue_solver_agent.py "Issue 64を解決する"
```

**期待される体験:**
```
🎯 Issue解決開始: Issue 64
📊 複雑度: 中 | 優先度: 高
🔧 解決戦略: 機能追加 + テスト強化
✅ 実装完了
✅ 品質チェック通過
🚀 PR作成: #112
```

## 🎯 BeeKeeper体験

### 自然言語による指示
```bash
# 基本的な指示
python examples/poc/issue_solver_agent.py "Issue 64を解決する"

# 緊急度指定
python examples/poc/issue_solver_agent.py "緊急でissue 64を直してほしい"

# 調査要求
python examples/poc/issue_solver_agent.py "Issue 75について調査してください"
```

### 期待される対話フロー
```
BeeKeeper: "Issue 64を解決する"
Queen: "承知しました。Issue 64を分析中..."
Queen: "複雑度：中、優先度：高と判定しました"
Queen: "3つのWorkerで並列実行を開始します"
  - Developer Worker: 実装作業
  - Tester Worker: テスト作成
  - Analyzer Worker: 品質チェック
Queen: "全Worker完了。結果を統合中..."
Queen: "品質チェック通過、PR #112を作成しました"
BeeKeeper: "ありがとう！確認します"
```

## 🔧 個別機能デモ

### Claude永続デーモン
```bash
# 永続デーモンデモ
python examples/poc/claude_daemon_demo.py
```

### tmux統合
```bash
# tmux統合デモ
python examples/poc/tmux_demo.py
```

### プロトコル詳細テスト
```bash
# 包括的プロトコルテスト
python examples/tests/protocols_test.py
```

## 🎪 tmux環境での体験

### セッション構成
```bash
# tmux セッション起動
tmux new-session -d -s hive

# ペイン分割例
┌─────────────────┬─────────────────┐
│   BeeKeeper     │     Queen       │
│   (Human)       │  (Coordinator)  │
├─────────────────┼─────────────────┤
│   Worker-1      │   Worker-2      │
│  (Developer)    │  (Tester)       │
└─────────────────┴─────────────────┘
```

### 実際の使用方法
1. **BeeKeeper pane**: 自然言語で指示
2. **Queen pane**: 戦略策定・進捗監視
3. **Worker panes**: 並列実行・専門作業

## 🔍 トラブルシューティング

### プロトコルエラー
```bash
# プロトコルテスト再実行
python examples/tests/protocols_test.py

# 設定確認
cat config/protocol_config.yaml
```

### 分散エージェントエラー
```bash
# 状態確認
./scripts/check-comb.sh

# 再起動
./scripts/stop_hive_distributed.sh
./scripts/start_hive_distributed.sh
```

### 依存関係エラー
```bash
# 依存関係確認
./scripts/check-dependencies.sh

# 環境再構築
make install
```

## 🎯 次のステップ

### 詳細な理解
1. **[アーキテクチャ設計書](architecture.md)** - システム全体の設計
2. **[新アーキテクチャ Issue解決ガイド](new_architecture_issue_guide.md)** - 詳細な使用方法
3. **[PoC実装ガイド](poc-guide.md)** - 自律エージェント開発

### 実用的な活用
1. **実際のIssue解決**: プロジェクトの実際の課題に適用
2. **カスタマイズ**: 専門Workerの追加・調整
3. **拡張**: 新機能・新プロトコルの開発

## 🌟 新アーキテクチャの価値

### 人間の役割変化
- **従来**: 技術的な管理者・指示者
- **新アーキテクチャ**: 創造的な依頼者・確認者

### 効率性の向上
- **従来**: 逐次処理、人間ボトルネック
- **新アーキテクチャ**: 並列処理、AI自動管理

### 体験の質向上
- **従来**: 複雑な技術的指示が必要
- **新アーキテクチャ**: 自然言語による直感的な指示

この新アーキテクチャにより、真の「BeeKeeper」として、Hiveの力を最大限に活用できます！