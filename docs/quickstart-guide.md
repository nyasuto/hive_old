# 🐝 Hive - クイックスタートガイド（10分で開始）

## 🚀 簡単3ステップ

### ステップ1: 環境確認（2分）
```bash
# 必要なツールがインストール済みか確認
which tmux python3 git
```

**必要な環境：**
- macOS または Linux
- tmux 3.0+
- Python 3.9+
- Claude Code（Claude Pro推奨）

### ステップ2: Hive起動（3分）
```bash
# Hiveをクローン
git clone https://github.com/nyasuto/hive.git
cd hive

# Small Colony（2 Workers）を起動
./scripts/start-small-hive.sh
```

### ステップ3: Hiveに接続（1分）
```bash
# tmuxセッションに接続
tmux attach-session -t hive-small-colony
```

**✅ 成功の確認：**
- 画面が左右2つのpaneに分割されている
- 左pane: Queen Worker（プロジェクト管理担当）
- 右pane: Developer Worker（実装担当）
- 両paneでClaude Codeが起動している

**🚨 うまくいかない場合：**
```bash
# セッション状態を確認
tmux list-sessions

# 強制再起動
./scripts/shutdown-hive.sh --force
./scripts/start-small-hive.sh
```

## 🎯 最初にやってみること（5分）

**💡 ここからはtmuxセッション内での操作です。左右のpaneを切り替えながら作業します。**

### オプション1: 🚀 自動協調システム（推奨・最新機能）

**完全自動化されたAI品質保証付き開発サイクルを体験：**

```bash
# 自動協調システムの実行（どのpaneからでもOK）
python examples/poc/automated_worker_coordination.py auto
```

**🎯 期待する結果：** 
- 3回の反復で品質スコア 70 → 85 → 95 に自動改善
- AI品質チェックと修正提案が自動実行
- 約4.5秒で完全自動化されたWorker協調完了

**複数シナリオのテスト：**
```bash
python examples/poc/automated_worker_coordination.py test
```

### オプション2: 🤝 手動協調システム（学習目的）

**AI品質チェック機能付きのWorker協調を手動で体験：**

**👈 左pane（Queen Worker）での操作：**

```bash
# タスク作成
python examples/poc/enhanced_feature_development.py queen
```

**👉 右pane（Developer Worker）での操作：**

`Alt + →` でDeveloper Workerのpaneに移動し：

```bash
# 実装作業
python examples/poc/enhanced_feature_development.py developer
```

**👈 左pane（Queen Worker）に戻って：**

```bash
# AI品質レビュー実行
python examples/poc/enhanced_feature_development.py queen --review
```

**🎯 期待する結果：** 
- Queen Worker: AI品質チェック付きタスク管理完了
- Developer Worker: 自己品質チェック付き実装完了
- AI による品質スコア評価と修正提案の確認

### オプション3: 🧪 個別機能テスト

**AI機能の個別テスト：**

```bash
# AI品質チェック機能テスト
python examples/poc/enhanced_feature_development.py test-ai

# 自動修正提案システムテスト
python examples/poc/enhanced_feature_development.py test-fix

# 協調システム監視
python examples/poc/automated_worker_coordination.py monitor
```

**🎯 期待する結果：** 
- ✅ AI品質チェック機能の動作確認
- ✅ 修正提案生成機能の確認  
- ✅ Worker間通信の監視機能確認

### 従来機能（基本通信テスト）

**基本的なWorker間通信をテストしたい場合：**

```bash
# 左pane
python examples/quickstart/01_basic_communication.py queen

# 右pane  
python examples/quickstart/01_basic_communication.py developer
```

**💡 ヒント：** 新機能（オプション1）から始めることを強く推奨します！

## 🔧 基本操作

### tmux操作
- **pane切り替え**: `Alt + ← / →` (楽！) または `Ctrl+B` → 矢印キー  
- **マウス移動**: クリックでpane移動
- **セッション終了**: `Ctrl+B` → `d` (デタッチ)
- **セッション復帰**: `tmux attach-session -t hive-small-colony`

### Hive操作
```bash
# 通信状況確認
./scripts/check-comb.sh

# タスク配布
./scripts/distribute-nectar.sh examples/simple-task.json

# 成果物収集
./scripts/collect-honey.sh auto

# Hive終了
./scripts/shutdown-hive.sh
```

## 🎬 実用例：AI品質保証付きWebアプリ開発

### 方法1: 🚀 完全自動化（推奨）

```bash
# カスタムタスクで自動協調実行
python examples/poc/automated_worker_coordination.py auto
```

**自動で実行される内容：**
- Queen: 高品質なタスク指示とAI品質レビュー
- Developer: 要件に基づく実装と自己品質チェック
- 3回の反復で品質スコア自動改善
- 修正提案の自動生成と適用

### 方法2: 🤝 手動協調（学習・カスタマイズ用）

### Queen Worker (左pane) - AI品質チェック付き
```python
# Enhanced PoCを使用
python examples/poc/enhanced_feature_development.py queen
```

**実行されること：**
- タスク作成と要件定義
- 品質基準の設定（型ヒント、docstring、エラーハンドリング）
- AI品質チェック機能の準備

### Developer Worker (右pane) - 自動修正対応
```python
# Enhanced PoCを使用
python examples/poc/enhanced_feature_development.py developer
```

**実行されること：**
- 要件に基づくFlask アプリ実装
- 自己品質チェック実行
- 完了報告の送信

### Queen Worker (左pane) - AI品質レビュー
```python
# AI品質レビュー実行
python examples/poc/enhanced_feature_development.py queen --review
```

**実行されること：**
- AI による包括的品質評価（スコア算出）
- 問題の自動検出（型ヒント不足、docstring不足等）
- 修正提案の自動生成
- 改善必要事項のフィードバック

### 生成される成果物例

```python
# examples/poc/quality_calculator.py (自動生成)
from typing import Union

Number = Union[int, float]

def add(a: Number, b: Number) -> Number:
    """
    加算を実行します
    
    Args:
        a: 第一オペランド（数値）
        b: 第二オペランド（数値）
    
    Returns:
        Number: a + b の計算結果
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("引数は数値である必要があります")
    return a + b
```

**🎯 品質保証された成果物の特徴：**
- ✅ 完全な型アノテーション
- ✅ Google Style docstrings
- ✅ 適切なエラーハンドリング
- ✅ 包括的なテストスイート
- ✅ AI による品質スコア90点以上

## ⚠️ よくある問題と解決方法

### 問題1: tmuxセッションが起動しない
```bash
# 既存セッションがある場合
tmux kill-session -t hive-small-colony
./scripts/start-small-hive.sh --force
```

### 問題2: Python スクリプトでエラーが発生する
```bash
# Combモジュールが見つからない場合
pip install -e .

# プロジェクトディレクトリから実行することを確認
pwd  # /path/to/hive になっているはず

# 詳細なエラー確認
python examples/quickstart/01_basic_communication.py queen
```

### 問題3: Worker間の通信ができない
```bash
# Combシステムの診断
./scripts/check-comb.sh --verbose

# ディレクトリ構造の確認・修復
./scripts/check-comb.sh --fix

# 強制再起動
./scripts/start-small-hive.sh --force
```

### 問題4: スクリプトの実行でヘルプが表示される
```bash
# 引数を正しく指定してください
python examples/quickstart/01_basic_communication.py queen  # Queen Worker用
python examples/quickstart/01_basic_communication.py developer  # Developer Worker用

# 引数なしでヘルプを確認
python examples/quickstart/01_basic_communication.py
```

## 📚 次のステップ

### 🚀 新機能をさらに活用する
- **[PoC実行ガイド](poc-guide.md)** - 全機能の詳細解説（推奨）
- **自動協調システム**: より複雑なプロジェクトでのテスト
- **AI品質チェック**: カスタム品質基準の設定
- **修正提案システム**: 独自のエラーパターン追加

### 詳細を学ぶ
- [セットアップガイド](setup-guide.md) - 詳細な環境構築
- [Comb API仕様](comb-api.md) - 通信システムの詳細
- [トラブルシューティング](troubleshooting.md) - 問題解決
- [Enhanced PoC仕様](../examples/poc/enhanced_feature_development.py) - AI機能詳細

### 実践してみる
```bash
# AI品質保証付きプロジェクト開発
python examples/poc/enhanced_feature_development.py queen
python examples/poc/enhanced_feature_development.py developer  
python examples/poc/enhanced_feature_development.py queen --review

# 完全自動化プロジェクト
python examples/poc/automated_worker_coordination.py auto

# 複数難易度でのテスト
python examples/poc/automated_worker_coordination.py test
```

### システムを拡張する
```bash
# カスタム協調設定
# automated_worker_coordination.py をコピーして設定変更

# カスタム品質基準
# enhanced_feature_development.py の quality_standards をカスタマイズ

# 独自の修正パターン追加
# PythonFixPatterns クラスに新しいパターンメソッド追加
```

### Phase 2 機能（準備中）
- **Colony管理システム**: 複数Workerの自動スケーリング
- **分散実行基盤**: 大規模プロジェクト対応
- **リアルタイム監視ダッシュボード**: Web UI での進捗確認

## 🎉 成功！

これでHive Small Colonyが動作しています！Queen WorkerとDeveloper Workerが協調して開発作業を行う準備が整いました。

次の目標：
- [ ] Worker間での実際のプロジェクト協調
- [ ] 成果物（Honey）の品質確認
- [ ] 作業ログ（Work Log）の確認
- [ ] より複雑なタスクの実行

**🍯 Sweet coding with Hive!**

---

## 📞 ヘルプが必要な場合

- **GitHub Issues**: バグ報告・質問
- **Documentation**: [完全なREADME](README.md)
- **Examples**: `examples/` ディレクトリ
- **Logs**: `.hive/logs/` で詳細ログを確認

このガイドで10分以内にHiveを使い始めることができます。より詳細な情報は各ドキュメントをご参照ください！