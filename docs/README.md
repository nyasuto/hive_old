# 🐝 Hive - 新アーキテクチャ Multi-Agent Development System

## 概要

Hiveは、**BeeKeeper-Queen-Worker協調**による新アーキテクチャ分散エージェントシステムです。プロトコル定義システムと永続デーモンを基盤として、自然言語指示による自律的Issue解決を実現します。

## 🎯 新アーキテクチャの特徴

### 🐝 役割分担
- **BeeKeeper (Human)**: 自然言語による指示・成果物受け取り
- **Queen**: AI戦略策定・タスク分散・結果統合
- **Worker群**: 専門的な並列実行

### 🔧 技術基盤
- **プロトコル定義システム**: 統一メッセージ形式・バージョン管理
- **Claude永続デーモン**: 長時間実行・自動復旧
- **tmux統合**: セッション管理・分散実行環境
- **Worker Role Template**: 役割ベースエージェント

## 📋 ドキュメント構成

### 🚀 Getting Started
- **[新アーキテクチャ Issue解決ガイド](new_architecture_issue_guide.md)** - メインガイド
- **[クイックスタート](quickstart.md)** - 5分で始める新アーキテクチャ
- **[アーキテクチャ設計](architecture.md)** - システム全体設計
- **[PoC実装ガイド](poc-guide.md)** - 自律エージェント開発PoC

### 🔧 運用・保守
- **[トラブルシューティング](troubleshooting.md)** - 問題解決ガイド

## 🚀 クイックスタート

### 1. 基盤確認
```bash
# 新プロトコルシステムテスト
python examples/tests/protocols_test.py
```

### 2. 分散エージェント起動
```bash
# 分散環境起動
./scripts/start_hive_distributed.sh

# 通信確認
./scripts/check-comb.sh
```

### 3. Issue解決デモ
```bash
# 自然言語でIssue解決
python examples/poc/issue_solver_agent.py "Issue 64を解決する"

# またはデモモード
python examples/poc/demo_issue_solver.py
```

## 🎯 実現される体験

### BeeKeeper視点
```
BeeKeeper: "Issue 64を解決する"
Queen: "承知しました。分析中..."
Queen: "3つのWorkerで並列実行します"
Queen: "実装完了、テスト通過、PR準備完了"
BeeKeeper: "ありがとう！確認します"
```

### 分散処理フロー
```
BeeKeeper → Queen → Worker群 → Queen → BeeKeeper
   ↓         ↓        ↓         ↓         ↓
  指示    戦略策定   並列実行   結果統合   成果受取
```

## 🔄 開発フロー

1. **プロトコル確認**: 新プロトコルシステムの動作確認
2. **分散環境起動**: tmux統合による分散エージェント起動
3. **自然言語指示**: BeeKeeperとしての直感的な指示
4. **成果物受け取り**: Queen統合による高品質な結果

## 🆕 新アーキテクチャの利点

### 従来の問題
- 人間が詳細な指示・管理をする必要
- 並列タスクの調整を人間が担当
- 結果的に人間が「管理者」として疲弊

### 新アーキテクチャの解決
- 人間は「依頼者」として本来の創造的な仕事に集中
- AI Queenが戦略策定・管理を担当
- 自然な役割分担による効率的な協調

## 📊 実装状況

### ✅ 完成した基盤技術
- プロトコル定義システム (Issue #101) - 100%
- tmux統合基盤 - 100%
- Claude永続デーモン - 100%
- Worker Role Template - 100%
- Issue解決エージェント - 100%

### 🎯 利用可能な機能
- 自然言語Issue解決
- 分散エージェント協調
- 永続監視・自動復旧
- 品質保証・テスト統合
- PR自動作成

---

**注意**: このドキュメントは新アーキテクチャ専用です。旧実装の情報は含まれていません。