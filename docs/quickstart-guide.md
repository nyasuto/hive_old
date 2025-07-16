# 🚀 Hive Quick Start Guide - 5分で始める自律的マルチエージェント開発

Hiveシステムを最短5分で起動し、Queen + Developer Workerによる協調開発を体験できます。

## ⚡ 5分クイックスタート

### 1. 環境確認 (30秒)

```bash
# 必要な依存関係を確認
./scripts/check-dependencies.sh

# または手動確認
python3 --version  # 3.9+
tmux -V           # any version
git --version     # any version
```

### 2. 環境セットアップ (2分)

```bash
# 依存関係インストール
make install

# 開発環境セットアップ
make dev
```

### 3. Hive起動 (1分)

```bash
# Small Colony起動 (Queen + Developer Worker)
./scripts/start-small-hive.sh

# ✅ 成功メッセージが表示されたら完了！
```

### 4. 動作確認 (1分)

```bash
# tmuxセッションに接続
tmux attach-session -t hive-small-colony

# 通信状況確認 (別ターミナル)
./scripts/check-comb.sh

# 成果物確認
./scripts/collect-honey.sh
```

### 5. 終了 (30秒)

```bash
# セッションから切断: Ctrl+B → d
# または安全終了
./scripts/shutdown-hive.sh --collect
```

---

## 🎯 実際の使用例

### Example 1: コード品質改善

**Queen Workerで:**
```
タスク: このプロジェクトのコード品質を改善してください
- テストカバレッジを確認
- 型アノテーションの追加
- docstringの改善
```

**Developer Workerで:**
```
# Queen Workerからの指示を確認
make quality  # 品質チェック実行
make test     # テスト確認
```

### Example 2: 新機能実装

**Queen Workerで:**
```
新機能要件:
1. User認証機能の追加
2. JWT トークン管理
3. セキュリティテストの実装
```

**Developer Workerで:**
```
# 実装フローの実行
1. 要件分析
2. 設計検討
3. 実装
4. テスト作成
5. 品質チェック
```

### Example 3: 自動リファクタリング

```bash
# PoC実行例 - 自律的コード改善
python examples/poc/automated_worker_coordination.py auto

# 期待結果:
# - 品質スコア: 70 → 85 → 95 (3反復)
# - AI品質チェック自動実行
# - 約4.5秒で完了
```

---

## 🛠️ tmux基本操作

### セッション管理
```bash
# セッション一覧
tmux list-sessions

# セッション接続
tmux attach-session -t hive-small-colony

# セッション切断
Ctrl+B → d
```

### Pane操作
```bash
# Pane切り替え
Ctrl+B → 矢印キー
# または
Alt + ← / →

# Paneスクロール
Ctrl+B → [ (終了: q)
```

---

## 📊 動作確認コマンド

### システム状況確認
```bash
# 📊 通信システム確認
./scripts/check-comb.sh

# 📈 品質メトリクス
make quality

# 🧪 テスト実行 (カバレッジ73%)
make test

# 📋 環境情報
make env-info
```

### ログ確認
```bash
# 🐝 Hiveディレクトリ確認
ls -la .hive/

# 📝 通信ログ (Markdown形式)
ls -la .hive/comb/communication_logs/

# 📊 作業ログ
ls -la .hive/work_logs/

# 🍯 成果物
ls -la .hive/honey/
```

---

## 🎬 実用シナリオ

### シナリオ1: 🚀 完全自動化開発サイクル

```bash
# AI品質保証付き自動開発
python examples/poc/automated_worker_coordination.py auto
```

**自動実行される内容:**
- Queen: 高品質タスク指示 + AI品質レビュー
- Developer: 要件実装 + 自己品質チェック
- 3回反復で品質スコア自動改善
- 修正提案の自動生成・適用

### シナリオ2: 🤝 手動協調開発

**👈 左pane (Queen Worker):**
```python
# タスク管理と品質監視
python examples/poc/enhanced_feature_development.py queen
```

**👉 右pane (Developer Worker):**
```python
# 実装と品質チェック
python examples/poc/enhanced_feature_development.py developer
```

**👈 左pane (AI品質レビュー):**
```python
# AI による包括的品質評価
python examples/poc/enhanced_feature_development.py queen --review
```

### シナリオ3: 🧪 基本通信テスト

```bash
# 左pane
python examples/quickstart/01_basic_communication.py queen

# 右pane
python examples/quickstart/01_basic_communication.py developer
```

---

## ⚠️ トラブルシューティング

### よくある問題

#### Q1: tmuxセッションが見つからない
```bash
# セッション一覧確認
tmux list-sessions

# 強制再起動
./scripts/start-small-hive.sh --force
```

#### Q2: Worker間通信ができない
```bash
# Combディレクトリ確認
ls -la .hive/comb/messages/

# 通信診断と修復
./scripts/check-comb.sh --fix
```

#### Q3: 依存関係エラー
```bash
# クリーン再インストール
make clean
make install

# Combモジュール確認
pip install -e .
```

#### Q4: Python スクリプトエラー
```bash
# プロジェクトディレクトリ確認
pwd  # /path/to/hive であることを確認

# 詳細エラー確認
python examples/quickstart/01_basic_communication.py queen
```

### ログ確認
```bash
# 📄 起動ログ
ls -la .hive/logs/hive-startup-*.log

# 📄 Worker個別ログ
ls -la .hive/logs/queen/
ls -la .hive/logs/developer/

# 📄 通信ログ (Markdown)
cat .hive/comb/communication_logs/$(date +%Y-%m-%d)/summary_*.md
```

---

## 🔄 開発ワークフロー

### 1. 日常的な開発フロー
```bash
# 🌅 朝の起動
./scripts/start-small-hive.sh

# 💼 作業実行
tmux attach-session -t hive-small-colony
# ... 協調開発作業 ...

# 🌙 夕方の終了 (成果物自動収集)
./scripts/shutdown-hive.sh --collect
```

### 2. 品質保証フロー
```bash
# ✅ コミット前チェック
make pr-ready

# 🔍 詳細テスト
make test-cov

# 📝 品質レポート
./scripts/collect-honey.sh
```

### 3. 継続的改善フロー
```bash
# 📈 メトリクス確認
./scripts/check-comb.sh

# 🚀 自律的品質改善
python examples/poc/automated_worker_coordination.py auto
```

---

## 📈 システム機能概要

### 🧠 Queen Coordinator (63% カバレッジ)
- 全体調整・負荷分散・緊急対応
- AI品質レビュー・修正提案
- タスク配布・優先度管理

### 💻 Developer Worker
- 要件実装・品質チェック
- 自己診断・改善提案
- テスト作成・実行

### 💬 Comb Communication (85% カバレッジ)
- ファイルベース非同期メッセージング
- Markdown形式通信ログ
- リアルタイム監視

### 📝 Work Log Manager (95% カバレッジ)
- 作業履歴・技術決定記録
- AI学習・改善基盤
- 日次サマリー生成

---

## 🎯 次のステップ

### 初心者向け
1. **[Setup Guide](setup-guide.md)** - 詳細セットアップ
2. **[Comb API](comb-api.md)** - Worker間通信の詳細
3. **[Troubleshooting](troubleshooting.md)** - 問題解決

### 上級者向け
1. **[PoC Guide](poc-guide.md)** - 自律的エージェント開発開始
2. カスタムWorker作成
3. 独自タスクフロー実装

### 開発者向け
1. コード貢献ガイド
2. アーキテクチャ深堀り
3. パフォーマンス最適化

---

## 💡 Tips & Best Practices

### 効率的な使い方
- **定期的な成果物収集**: `./scripts/collect-honey.sh`
- **通信状況の監視**: `./scripts/check-comb.sh`
- **品質チェックの習慣化**: `make quality`
- **自動化の活用**: PoC例で協調開発パターン学習

### 推奨環境
- **ターミナル**: iTerm2, Windows Terminal, Gnome Terminal
- **エディタ**: VS Code, Neovim, Emacs
- **Git**: 最新版推奨
- **Python**: 3.11+ (型チェック最適化)

### セキュリティ注意事項
- 機密情報をWorker間で共有しない
- ログファイルに認証情報を記録しない
- `.hive` ディレクトリを `.gitignore` に追加

---

## 🏆 成功指標

### 基本動作確認
- ✅ tmuxセッション正常起動
- ✅ Worker間通信確立
- ✅ 基本タスク実行成功

### 協調開発確認
- ✅ Queen→Developer指示伝達
- ✅ Developer→Queen進捗報告
- ✅ 品質チェック自動実行

### 自律化確認
- ✅ AI品質レビュー動作
- ✅ 修正提案自動生成
- ✅ 反復改善サイクル動作

---

**🎉 これでHiveシステムの基本的な使い方をマスターしました！**  
**自律的マルチエージェント開発の世界をお楽しみください！**

---

## 📞 ヘルプが必要な場合

- **GitHub Issues**: バグ報告・質問
- **Documentation**: [完全なREADME](README.md)
- **Examples**: `examples/` ディレクトリ
- **Logs**: `.hive/logs/` で詳細ログを確認