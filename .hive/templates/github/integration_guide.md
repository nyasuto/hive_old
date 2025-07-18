# 🐝 Hive GitHub Issue-PR統合ガイド

## 概要

HiveシステムでGitHub IssueとPull Requestを自動連携させる機能の使用方法を説明します。

## 機能概要

### 1. 統合ワークフロー機能
- 分析結果からIssue自動作成
- 実装完了後のPR自動作成
- Issue-PR自動連携（Closes #xx）
- セッション追跡とレポート生成

### 2. 提供スクリプト

#### メインスクリプト
- `create_github_issue.py` - Issue作成機能
- `create_github_pr.py` - PR作成機能
- `github_issue_pr_integration.py` - Issue-PR統合機能
- `queen_github_integration.py` - Queen Worker統合ヘルパー

#### テストスクリプト
- `test_github_pr_integration.py` - 統合機能テスト
- `test_github_issue_creation.py` - Issue作成テスト

## 使用方法

### 1. Queen Workerからの統合利用

```python
from queen_github_integration import QueenGitHubIntegration

# 統合ヘルパーを初期化
integration = QueenGitHubIntegration()

# 分析結果からIssue-PR統合ワークフロー実行
analysis_result = {
    'title': '新機能の実装',
    'summary': '新機能の分析と実装提案',
    'details': '詳細な実装内容...',
    'recommended_actions': '実装とテストの実行',
    'participants': ['Queen', 'Developer'],
    'completion_criteria': '- 実装完了\n- テスト通過'
}

# 統合ワークフロー実行
result = integration.process_hive_analysis_to_github(
    session_id='session_001',
    analysis_result=analysis_result
)

print(f"Issue URL: {result.get('issue_url')}")
print(f"PR URL: {result.get('pr_url')}")
```

### 2. 段階的な使用

```python
# 1. Issue作成のみ
result = integration.process_hive_analysis_to_github(
    session_id='session_001',
    analysis_result=analysis_result,
    auto_create_pr=False  # PR作成を無効化
)

# 2. 実装完了後にPR作成
pr_result = integration.create_implementation_pr(
    session_id='session_001',
    implementation_summary='新機能の実装完了',
    technical_details='実装の詳細...',
    test_results='テスト結果...'
)
```

### 3. セッション管理

```python
# セッション状態確認
status = integration.get_session_status('session_001')
print(f"Status: {status['status']}")

# アクティブセッション一覧
sessions = integration.list_active_sessions()
for session in sessions:
    print(f"{session['session_id']}: {session['status']}")

# セッションレポート生成
report = integration.format_session_report('session_001')
print(report)
```

## コマンドライン使用方法

### 1. Issue作成

```bash
# 分析結果からIssue作成
python scripts/create_github_issue.py \
    --title "新機能の実装" \
    --summary "新機能の概要" \
    --details "詳細な実装内容" \
    --workers "Queen,Developer" \
    --session-id "session_001"

# プレビューモード
python scripts/create_github_issue.py \
    --title "新機能の実装" \
    --summary "新機能の概要" \
    --preview
```

### 2. PR作成

```bash
# 実装結果からPR作成
python scripts/create_github_pr.py \
    --title "新機能の実装" \
    --summary "実装の概要" \
    --issues "123" \
    --session-id "session_001"

# プレビューモード
python scripts/create_github_pr.py \
    --title "新機能の実装" \
    --summary "実装の概要" \
    --preview
```

### 3. 統合テスト

```bash
# 統合機能テスト実行
python scripts/test_github_pr_integration.py
```

## 設定ファイル

### GitHub設定 (`config/github_settings.yaml`)

```yaml
github:
  repository:
    auto_detect: true
    owner: ""
    name: ""
  
  issue:
    title_prefix: "[Hive検討結果]"
    labels:
      default: ["hive-generated"]
      priority:
        critical: "priority: critical"
        high: "priority: high"
        medium: "priority: medium"
        low: "priority: low"
      type:
        feature: "type: feature"
        bug: "type: bug"
        enhancement: "type: enhancement"
    assignees:
      auto_assign: false
      default_assignee: ""
    milestone:
      auto_detect: false
      default: ""
  
  pr:
    auto_push: true
    draft: false
    labels:
      default: ["hive-generated"]
      type:
        feat: "type: feature"
        fix: "type: bug"
        enhancement: "type: enhancement"
    reviewers:
      auto_assign: false
      default_reviewers: []
    template:
      file: ".hive/templates/github/pr_template.md"

execution:
  logging:
    level: "INFO"
    file: "logs/github_integration.log"
  confirmation:
    confirm_create: true
```

## テンプレート

### Issue テンプレート

`.hive/templates/github/issue_template.md` を使用

### PR テンプレート

`.hive/templates/github/pr_template.md` を使用

## ワークフロー例

### 1. 分析→Issue作成→実装→PR作成

```
1. Hive分析実行
   ↓
2. 分析結果をGitHub Issue作成
   ↓
3. 実装作業
   ↓
4. 実装完了後PR作成
   ↓
5. Issue-PR自動連携（Closes #xx）
```

### 2. フォローアップ開発

```
1. 元のセッションから派生Issue作成
   ↓
2. 追加実装作業
   ↓
3. フォローアップPR作成
   ↓
4. 元のIssueとの関連付け（Relates to #xx）
```

## セッションデータ構造

```json
{
  "session_id": "session_001",
  "issue_url": "https://github.com/owner/repo/issues/123",
  "issue_number": 123,
  "pr_url": "https://github.com/owner/repo/pull/456",
  "created_at": "2024-01-01T12:00:00",
  "analysis_result": {
    "title": "新機能の実装",
    "summary": "概要",
    "details": "詳細",
    "participants": ["Queen", "Developer"]
  },
  "implementation_data": {
    "title": "実装タイトル",
    "technical_changes": "技術的変更点",
    "test_info": "テスト情報"
  }
}
```

## トラブルシューティング

### 1. GitHub CLI未設定

```bash
# GitHub CLI インストール
brew install gh

# 認証設定
gh auth login
```

### 2. テンプレートファイルが見つからない

```bash
# テンプレートディレクトリを確認
ls -la .hive/templates/github/

# テンプレートファイルを確認
cat .hive/templates/github/pr_template.md
```

### 3. 権限エラー

```bash
# リポジトリのアクセス権限を確認
gh api repos/:owner/:repo

# 認証状態を確認
gh auth status
```

## ベストプラクティス

1. **セッションID命名**: 日時を含む一意な名前を使用
2. **分析結果の品質**: 詳細で構造化された分析結果を作成
3. **テンプレートのカスタマイズ**: プロジェクトに合わせてテンプレートを調整
4. **段階的実装**: 必要に応じてIssue作成とPR作成を分離
5. **レビュー観点**: 技術的な変更点を明確に記載

## 拡張機能

### 1. カスタムテンプレート

プロジェクト固有のテンプレートを作成可能

### 2. 自動ラベル付け

内容に応じた自動ラベル付けのカスタマイズ

### 3. 通知連携

Slack等への通知機能の追加

### 4. レポート機能

セッションレポートの自動生成と配信

---

*🤖 このガイドはHive Multi-Agent Systemにより自動生成されました*