# 🆕 新アーキテクチャ Issue解決ガイド

## 🎯 新プロトコルシステムによるIssue解決手順

### 前提条件
- プロトコル定義システム（Issue #101）実装完了 ✅
- 分散エージェント環境起動済み
- 新プロトコル通信確立済み

---

## 🚀 実行手順

### Step 1: 新プロトコルシステム動作確認 (5分)

```bash
# 新プロトコルシステムテスト実行
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

### Step 2: 分散エージェント状態確認 (3分)

```bash
# 分散環境通信確認
./scripts/check-comb.sh

# 必要に応じて分散エージェント再起動
./scripts/start_hive_distributed.sh
```

### Step 3: 新アーキテクチャ Issue解決実行 (10分)

#### 3-1. 自然言語プロンプト実行

```bash
# 自然言語でIssue解決を指示
python examples/poc/issue_solver_agent.py "Issue 64を解決する"

# または緊急度指定
python examples/poc/issue_solver_agent.py "緊急でissue 64を直してほしい"
```

#### 3-2. デモモード実行

```bash
# 一括デモ実行
python examples/poc/demo_issue_solver.py

# インタラクティブモード
python examples/poc/issue_solver_agent.py
```

#### 3-3. 実行例

```python
# 自然言語プロンプト例
user_prompts = [
    "Issue 64を解決する",
    "バグ修正をお願いします issue 84", 
    "Issue 75について調査してください",
    "緊急でissue 64を直してほしい"
]

# BeeKeeper: 自然言語プロンプト解析
beekeeper = IssueSolverBeeKeeper()
result = await beekeeper.process_user_request(user_prompt)

# 意図認識 → 適切な処理実行
# solve: 実際の解決処理
# investigate: 調査・分析のみ
# explain: 詳細説明生成
```

---

## 🔧 新アーキテクチャの特徴

### 1. プロトコル定義システム活用
- **統一メッセージ形式**: MessageProtocol による標準化
- **厳密バリデーション**: ProtocolValidator による検証
- **バージョン管理**: 互換性チェック機能

### 2. 分散エージェント協調
- **Queen-Worker協調**: 新プロトコル通信による効率化
- **タスク分散**: 複数Worker間の自動負荷分散
- **リアルタイム監視**: 進捗・状態の即座把握

### 3. 自然言語処理強化
- **意図認識**: 自然言語プロンプト解析
- **優先度判定**: 緊急・重要・通常・低の自動分類
- **適応的実行**: 状況に応じた最適手法選択

---

## 📋 実行時のポイント

### ✅ 成功パターン
1. **明確な指示**: "Issue 64を解決する"
2. **緊急度指定**: "緊急でissue 64を直してほしい"
3. **調査要求**: "Issue 75について調査してください"

### ⚠️ 注意点
- 新プロトコルシステムが正常動作していることを確認
- 分散エージェントが起動済みであることを確認
- GitHub APIアクセス権限が適切に設定されていることを確認

### 🔍 トラブルシューティング

**プロトコルエラーの場合:**
```bash
# プロトコルテスト再実行
python examples/tests/protocols_test.py

# 設定確認
cat config/protocol_config.yaml
```

**分散エージェントエラーの場合:**
```bash
# 状態確認
./scripts/check-comb.sh

# 再起動
./scripts/stop_hive_distributed.sh
./scripts/start_hive_distributed.sh
```

---

## 🎯 期待される結果

### 自動実行内容
1. **Issue分析**: GitHub APIを使用した詳細分析
2. **解決戦略策定**: 複雑度・優先度に応じた計画作成
3. **実装実行**: 適切なWorkerによる自動実装
4. **品質チェック**: テスト・リント・型チェック実行
5. **PR作成**: 解決内容のプルリクエスト自動作成

### 出力例
```
🎯 Issue解決開始: Issue 64
📊 複雑度: 中 | 優先度: 高
🔧 解決戦略: 機能追加 + テスト強化
✅ 実装完了
✅ 品質チェック通過
🚀 PR作成: #111
```

---

## 🚀 次のステップ

### 継続的改善
1. **解決結果の分析**: 成功・失敗パターンの学習
2. **プロトコル最適化**: 通信効率の向上
3. **エージェント特化**: 専門性の強化

### 拡張可能性
- **複数Issue同時解決**: 並列処理による効率化
- **関連Issue自動検出**: 依存関係の自動分析
- **予防的改善**: 潜在的問題の事前発見

このガイドに従って、新アーキテクチャの威力を体験してください！