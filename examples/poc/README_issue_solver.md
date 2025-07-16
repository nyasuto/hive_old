# Issue Solver Agent - 自然言語プロンプト対応Issue解決エージェント

## 概要

ユーザーが自然な日本語で「Issue 64を解決する」「バグ修正をお願いします issue 84」などのプロンプトを入力すると、BeeKeeper-Queen-Worker協調でGitHub Issueの解決を行う実用的なPoCです。

## 特徴

### 🎯 自然言語プロンプト対応
- 「Issue 64を解決する」
- 「バグ修正をお願いします issue 84」
- 「https://github.com/nyasuto/hive/issues/84 を修正して」
- 「緊急でissue 64を直してほしい」

### 🧠 意図認識
- **solve**: 解決・修正
- **investigate**: 調査・確認
- **explain**: 説明・理解
- **implement**: 実装・開発

### ⚡ 優先度自動推定
- **high**: 緊急、重要、クリティカル
- **medium**: 通常（デフォルト）
- **low**: 後で、時間があるとき

### 🤖 BeeKeeper-Queen-Worker協調
- **BeeKeeper**: 人間のプロンプト解析・結果提示
- **Queen**: 全体統制・計画策定・進捗管理
- **Worker**: 実際の解決作業実行

## 使用方法

### 基本実行
```bash
# 直接プロンプト指定
python examples/poc/issue_solver_agent.py "Issue 64を解決する"

# デモモード
python examples/poc/issue_solver_agent.py --demo

# インタラクティブモード
python examples/poc/issue_solver_agent.py
```

### デモスクリプト
```bash
# 一括デモ（複数プロンプトパターン）
python examples/poc/demo_issue_solver.py

# インタラクティブデモ
python examples/poc/demo_issue_solver.py --interactive
```

## 対応プロンプト例

### 解決モード
- "Issue 64を解決する"
- "バグ修正をお願いします issue 84"
- "https://github.com/nyasuto/hive/issues/84 を修正して"
- "緊急でissue 64を直してほしい"

### 調査モード
- "Issue 75について調査してください"
- "issue 84の状況を確認して"
- "バグの原因を調べてください issue 64"

### 説明モード
- "Issue 84の内容を説明してください"
- "issue 64について詳しく教えて"
- "このバグはなぜ発生しているのですか issue 84"

## アーキテクチャ

### UserPromptParser
```python
class UserPromptParser:
    """ユーザープロンプト解析器"""
    
    def parse_user_prompt(self, prompt: str) -> dict[str, Any]:
        """プロンプトを解析してアクションを特定"""
        # Issue番号抽出
        # 意図分析（solve/investigate/explain/implement）
        # 優先度推定（high/medium/low）
        # 追加情報抽出
```

### IssueSolverBeeKeeper
```python
class IssueSolverBeeKeeper:
    """Issue解決BeeKeeper（人間インターフェース）"""
    
    async def process_user_request(self, user_prompt: str):
        """ユーザーリクエスト処理"""
        # 1. プロンプト解析
        # 2. 意図に応じた処理分岐
        # 3. 結果提示
```

### IssueSolverQueenCoordinator
```python
class IssueSolverQueenCoordinator:
    """Issue解決専用Queen Coordinator"""
    
    async def coordinate_issue_resolution(self, issue_analysis):
        """Issue解決の協調統制"""
        # 1. 解決計画策定
        # 2. Developer Worker割り当て
        # 3. 進捗監視
        # 4. 結果検証
```

### IssueSolverDeveloperWorker
```python
class IssueSolverDeveloperWorker:
    """Issue解決専用Developer Worker"""
    
    async def start_issue_resolution_monitoring(self):
        """Issue解決監視開始"""
        # 1. Queen指示受信
        # 2. 解決ステップ実行
        # 3. 進捗報告
        # 4. 完了報告
```

## 実行例

### 基本的な解決フロー
```bash
$ python examples/poc/issue_solver_agent.py "Issue 64を解決する"

🐝 BeeKeeper: Processing user request: "Issue 64を解決する"
🔍 Parsed intent: solve
🏷️  Priority: medium
📋 Issue number: 64
📊 Analyzing issue...
📋 Issue #64: Worker Role Template System Implementation
🏷️  Type: feature
⚡ Complexity: medium
🔧 Strategy: implementation
💻 Starting developer worker monitoring...
👑 Queen coordinating issue resolution...
⚡ Executed 5 actions: 4 successful, 1 failed
✅ Issue resolution completed successfully!
💾 Results saved to: .hive/honey/user_request_20250116_143022.json
```

### 調査モード
```bash
$ python examples/poc/issue_solver_agent.py "Issue 84について調査してください"

🐝 BeeKeeper: Processing user request: "Issue 84について調査してください"
🔍 Parsed intent: investigate
🏷️  Priority: medium
📋 Issue number: 84
🔍 BeeKeeper: Investigating Issue 84
📋 Issue #84: fix: examples/poc と examples/templates の型チェックエラー修正
🏷️  Type: bug
⚡ Complexity: low
🔧 Suggested Strategy: bug_fix
📝 Required Actions: 4
✅ Request processed successfully
🔧 Mode: investigation
```

### 説明モード
```bash
$ python examples/poc/issue_solver_agent.py "Issue 84の内容を説明してください"

💬 BeeKeeper: Explaining Issue 84

📝 Issue Explanation:
Issue #84 について説明します：

【概要】
タイトル: fix: examples/poc と examples/templates の型チェックエラー修正
タイプ: bug
複雑度: low

【技術要素】
関連技術: python, type_checking

【解決戦略】
推奨アプローチ: bug_fix
推定工数: 2時間

【必要なアクション】
1. Issue内容の詳細調査と現状分析 (30分)
2. 型チェック関連の修正 (60分)
3. 解決策の検証とテスト (45分)
```

## 成果物

実行結果は `.hive/honey/` ディレクトリに以下の形式で保存されます：

```json
{
  "success": true,
  "mode": "solve",
  "issue_number": "64",
  "resolution_plan": {
    "issue_summary": {...},
    "resolution_strategy": {...},
    "action_sequence": [...],
    "estimated_total_time": 300
  },
  "resolution_result": {
    "completed_steps": 4,
    "total_steps": 5,
    "step_results": [...],
    "total_time": 145.2,
    "status": "completed"
  },
  "validation": {
    "success": true,
    "overall_score": 85,
    "validated_criteria": [...]
  }
}
```

## 今後の展開

1. **GitHub API連携強化**: 実際のIssue操作
2. **コード修正自動化**: 実際のファイル編集
3. **テスト自動実行**: 修正結果の検証
4. **コミット自動化**: 修正内容の自動コミット
5. **PR作成**: 修正内容のPull Request作成

## 注意事項

- 現在は**デモ実装**のため、実際のファイル修正は行いません
- GitHub CLI (`gh`) が必要です
- 実際のIssue情報取得にはGitHub認証が必要です
- 型チェックエラーは examples ディレクトリでスキップされます

## 関連ファイル

- `issue_solver_agent.py`: メインエージェント実装
- `demo_issue_solver.py`: デモスクリプト
- `README_issue_solver.md`: このドキュメント

これにより、「Issue 64を解決する」のような自然な日本語プロンプトから具体的な問題解決まで、実用的なワークフローが実現されます。