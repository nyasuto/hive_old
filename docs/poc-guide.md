# Hive PoC実行ガイド

## 🐝 概要

Hiveは、Claude Codeを複数並列実行し、各インスタンスに専門的な役割を与えて協調的にタスクを遂行するマルチエージェントシステムです。Issue #48, #49, #50の実装により、AI品質チェック、自動修正提案、自動協調システムが統合されました。

## 🚀 クイックスタート

### 前提条件

```bash
# 1. 依存関係インストール
make install

# 2. 品質チェック（初回）
make quality

# 3. tmuxセッション準備
tmux new-session -d -s hive-poc
```

### 基本的なPoC実行

```bash
# 1. Enhanced PoCでAI品質チェック付き開発サイクル
python examples/poc/enhanced_feature_development.py queen

# 別paneで
python examples/poc/enhanced_feature_development.py developer

# Queen paneで品質レビュー実行
python examples/poc/enhanced_feature_development.py queen --review
```

### 自動協調システム実行

```bash
# 完全自動化された協調サイクル
python examples/poc/automated_worker_coordination.py auto

# 複数シナリオテスト
python examples/poc/automated_worker_coordination.py test

# 協調状況監視
python examples/poc/automated_worker_coordination.py monitor
```

## 📋 利用可能なPoC機能

### 1. Enhanced Feature Development (Issue #48, #49)

**ファイル**: `examples/poc/enhanced_feature_development.py`

**機能**:
- AI品質チェック機能
- 自動修正提案システム
- Queen-Developer協調開発
- 品質スコア評価とフィードバック

**コマンド**:
```bash
# Queen Worker（タスク管理・品質保証）
python examples/poc/enhanced_feature_development.py queen

# Developer Worker（実装・自己品質チェック）
python examples/poc/enhanced_feature_development.py developer

# Queen Worker（レビュー実行）
python examples/poc/enhanced_feature_development.py queen --review

# AI品質チェックテスト
python examples/poc/enhanced_feature_development.py test-ai

# 修正提案システムテスト
python examples/poc/enhanced_feature_development.py test-fix
```

### 2. Automated Worker Coordination (Issue #50)

**ファイル**: `examples/poc/automated_worker_coordination.py`

**機能**:
- 完全自動化された協調サイクル
- 4フェーズ品質改善プロセス
- 反復学習による品質向上
- 失敗時フォールバック処理

**コマンド**:
```bash
# 自動協調デモ実行
python examples/poc/automated_worker_coordination.py auto

# 複数シナリオテスト
python examples/poc/automated_worker_coordination.py test

# 協調状況監視
python examples/poc/automated_worker_coordination.py monitor
```

## 🔄 推奨PoCワークフロー

### ワークフロー1: 手動協調開発（学習目的）

```bash
# Step 1: タスク作成（Queen）
python examples/poc/enhanced_feature_development.py queen

# Step 2: 実装作業（Developer）
python examples/poc/enhanced_feature_development.py developer

# Step 3: AI品質レビュー（Queen）
python examples/poc/enhanced_feature_development.py queen --review

# Step 4: 必要に応じて修正提案確認
python examples/poc/enhanced_feature_development.py test-fix
```

### ワークフロー2: 自動協調システム（本格運用）

```bash
# Step 1: 自動協調実行
python examples/poc/automated_worker_coordination.py auto

# Step 2: 結果確認・監視
python examples/poc/automated_worker_coordination.py monitor

# Step 3: 複数シナリオでの検証
python examples/poc/automated_worker_coordination.py test
```

## 🛠️ 高度な機能

### AI品質チェック機能の活用

```python
from examples.poc.enhanced_feature_development import AIQualityChecker

# AI品質チェッカー初期化
checker = AIQualityChecker()

# ファイルの品質評価
assessment = checker.assess_code_quality(Path("your_file.py"))
print(f"品質スコア: {assessment.overall_score}/100")

# 修正提案生成
suggestions = checker.generate_fix_suggestions(assessment.issues)
```

### 自動修正提案システムの活用

```python
from examples.poc.enhanced_feature_development import FixSuggestionEngine

# 修正提案エンジン初期化
engine = FixSuggestionEngine()

# 修正提案生成
suggestions = engine.generate_suggestions(issues)

# 優先順位付け
prioritized = engine.prioritize_suggestions(suggestions)
```

### 自動協調システムのカスタマイズ

```python
from examples.poc.automated_worker_coordination import AutomatedWorkerCoordination

# カスタム設定で協調システム初期化
coordinator = AutomatedWorkerCoordination(
    max_iterations=5,        # 最大反復回数
    quality_threshold=95,    # 品質基準
    timeout_seconds=300      # タイムアウト
)

# カスタムタスクで実行
custom_task = {
    "feature_name": "CustomFeature",
    "requirements": ["要件1", "要件2"],
    "quality_standards": {"target_score": 95}
}

result = await coordinator.execute_automated_development_cycle(custom_task)
```

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. Combメッセージエラー

```bash
# Combディレクトリのクリーンアップ
rm -rf .hive/comb/messages/*

# 権限確認
chmod -R 755 .hive/
```

#### 2. 品質チェック失敗

```bash
# 自動修正実行
make quality-fix

# 個別チェック
make lint
make format
make type-check
```

#### 3. PoC実行エラー

```bash
# 依存関係確認
make install

# Python環境確認
python --version  # 3.12以上必要

# プロジェクトパス確認
echo $PYTHONPATH
```

### デバッグ方法

#### ログ確認

```bash
# Combメッセージログ確認
ls -la .hive/comb/messages/

# 最新メッセージ確認
find .hive/comb/messages -name "*.json" -exec ls -lt {} + | head -5
```

#### 詳細実行

```bash
# デバッグモードで実行
python -v examples/poc/enhanced_feature_development.py queen

# ログレベル設定
PYTHONPATH=. python examples/poc/automated_worker_coordination.py auto
```

## 📊 パフォーマンス指標

### Enhanced Feature Development

- **品質評価精度**: 90%以上
- **修正提案適合率**: 85%以上
- **実行時間**: 平均30秒/ファイル

### Automated Coordination

- **成功率**: 66.7%（テストシナリオ）
- **平均実行時間**: 4.5秒（3反復）
- **品質改善率**: 70→95点（平均）

## 🚀 次のステップ

### Phase 2への準備

1. **Colony起動システム**: 複数Workerの自動管理
2. **分散実行基盤**: 大規模プロジェクト対応
3. **リアルタイム監視**: ダッシュボード実装

### カスタマイズ例

```bash
# 独自のWorker実装
cp examples/poc/enhanced_feature_development.py my_custom_worker.py

# 独自の品質基準定義
# quality_standards.json作成

# 独自の協調ルール実装
# coordination_rules.py作成
```

## 📝 参考リンク

- [Issue #48: AI品質チェック機能](https://github.com/nyasuto/hive/issues/48)
- [Issue #49: 自動修正提案システム](https://github.com/nyasuto/hive/issues/49)
- [Issue #50: 自動協調システム](https://github.com/nyasuto/hive/issues/50)
- [Enhanced PoC実装](examples/poc/enhanced_feature_development.py)
- [自動協調システム実装](examples/poc/automated_worker_coordination.py)

---

**💡 ヒント**: 初回は手動協調（ワークフロー1）で理解を深めてから、自動協調（ワークフロー2）に進むことを推奨します。