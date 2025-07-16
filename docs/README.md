# 🐝 Hive - Multi-Agent Development System Documentation

Hiveは、Claude Codeを複数並列実行し、各インスタンスに専門的な役割を与えて協調的にタスクを遂行するマルチエージェントシステムです。

## 📋 ドキュメント構成

### 🚀 Getting Started
- **[Quick Start Guide](quickstart-guide.md)** - 5分で始めるHive
- **[Setup Guide](setup-guide.md)** - 詳細な環境構築手順
- **[PoC Guide](poc-guide.md)** - 自律的エージェント開発PoC開始ガイド

### 🔧 API & Technical Reference
- **[Comb API Reference](comb-api.md)** - Worker間通信システム完全ガイド
- **[Architecture Overview](#architecture)** - システム全体設計
- **[Testing Guide](#testing)** - テスト実行とカバレッジ

### 🛠️ Operations & Maintenance
- **[Troubleshooting](troubleshooting.md)** - 問題解決ガイド
- **[Best Practices](#best-practices)** - 運用ベストプラクティス

## 🏗️ System Architecture

### Current Implementation Status

| Component | Status | Coverage | Description |
|-----------|--------|----------|-------------|
| 🧠 **Queen Coordinator** | ✅ Complete | 63% | 全体調整・負荷分散・緊急対応 |
| 📊 **Status Monitor** | ✅ Complete | 68% | リアルタイム監視・ボトルネック検出 |
| 🎯 **Task Distributor** | ✅ Complete | 72% | タスク配布・優先度管理 |
| 🍯 **Honey Collector** | ✅ Complete | 82% | 成果物収集・品質評価 |
| 💬 **Comb Communication** | ✅ Complete | 85% | ファイルベース非同期メッセージング |
| 📝 **Work Log Manager** | ✅ Complete | 95% | Markdown作業履歴・技術決定記録 |
| 🔄 **tmux Integration** | ✅ Complete | 90% | マルチワーカー実行環境 |

### 🎯 **Current Capabilities**

#### Phase 1: Small Colony (2 Workers) ✅
- **Queen Worker**: プロジェクト管理・調整・品質保証
- **Developer Worker**: 実装・開発・技術実行
- **Automation Scripts**: 完全自動化された起動・終了・監視

#### Phase 2: Full Colony (5+ Workers) 🚧
- **Architect Worker**: システム設計・アーキテクチャ
- **Frontend Worker**: UI/UX開発
- **Backend Worker**: API/DB開発
- **DevOps Worker**: インフラ・CI/CD
- **Tester Worker**: テスト・品質保証

## 🚀 Quick Commands

```bash
# 🐝 Hive起動 (Queen + Developer)
./scripts/start-small-hive.sh

# 📊 通信状況確認
./scripts/check-comb.sh

# 🍯 成果物収集
./scripts/collect-honey.sh

# 🛑 安全終了
./scripts/shutdown-hive.sh

# 🧪 品質チェック
make quality

# 🧪 テスト実行 (カバレッジ73%)
make test
```

## 🎯 Autonomous Agent PoC Ready

### 基盤技術完成度
- ✅ **Inter-Agent Communication**: Comb APIによる非同期メッセージング
- ✅ **Task Coordination**: Queen Coordinatorによる自律的タスク管理
- ✅ **Real-time Monitoring**: Status Monitorによる状況把握
- ✅ **Work History**: MarkdownLoggerによる学習・改善基盤
- ✅ **Quality Assurance**: 包括的テストと品質チェック体制

### すぐに開始可能なPoC例
1. **コード自動リファクタリング**: Queen→Developerでの品質改善指示
2. **テスト自動生成**: 既存コードから包括的テストケース生成  
3. **ドキュメント自動更新**: コード変更に連動したドキュメント同期
4. **継続的品質改善**: AIによる自律的コード品質監視・改善

## 📊 Testing & Quality

### Test Coverage: **73%** (55%→73% +18pt向上)
```bash
# テスト実行
make test           # 全テスト実行
make test-cov       # カバレッジ付きテスト

# 品質チェック
make quality        # lint + format + type-check
make pr-ready       # テスト + 品質チェック
```

### 主要モジュールカバレッジ
- **Queen Coordinator**: 63% (+36pt)
- **Status Monitor**: 68% (+39pt)  
- **Task Distributor**: 72%
- **Honey Collector**: 82%
- **Comb Communication**: 85%

## 🔄 Development Workflow

### Branch Strategy
```bash
# 機能開発
git checkout -b feat/issue-X-feature-name

# 品質チェック
make quality

# PR作成
git push -u origin feat/issue-X-feature-name
gh pr create
```

### CI/CD Pipeline
- ✅ **Quality**: ruff (lint + format) + mypy (type-check)
- ✅ **Testing**: pytest with coverage reporting
- ✅ **Build**: uv build validation
- ✅ **Integration**: All checks required for merge

## 📁 Project Structure

```
hive/
├── queen/              # Queen Worker システム
│   ├── coordinator.py  # 全体調整システム
│   ├── status_monitor.py # 監視システム
│   ├── task_distributor.py # タスク配布
│   └── honey_collector.py # 成果物収集
├── comb/               # Worker間通信システム
│   ├── api.py          # 統一API
│   ├── message_router.py # メッセージング
│   ├── sync_manager.py # 同期管理
│   ├── work_log_manager.py # 作業ログ
│   └── markdown_logger.py # Markdownログ
├── workers/            # Worker設定
│   ├── prompts/        # Worker専用プロンプト
│   └── configs/        # Worker設定
├── scripts/            # 自動化スクリプト
│   ├── start-small-hive.sh # Hive起動
│   ├── check-comb.sh   # 通信確認
│   ├── collect-honey.sh # 成果物収集
│   └── shutdown-hive.sh # 安全終了
├── tests/              # 包括的テストスイート (73%カバレッジ)
├── docs/               # ドキュメント
└── examples/           # 使用例・デモ
```

## 🌟 Next Steps

1. **[PoC Guide](poc-guide.md)** を確認して自律的エージェント開発を開始
2. **[Quick Start Guide](quickstart-guide.md)** でHiveを実際に動かしてみる
3. **[Comb API](comb-api.md)** でWorker間通信をマスター
4. カスタムWorkerやタスクを実装してシステムを拡張

---

**🚀 Hiveで自律的マルチエージェント開発の未来を体験しましょう！**