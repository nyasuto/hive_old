# 🐝 Hive GitHub Issue 自動作成機能

## 概要

Hiveシステムで検討結果をGitHub Issueとして自動作成する機能です。Queen WorkerやDeveloper Workerの検討結果を構造化されたIssueとして記録し、プロジェクト管理を効率化します。

## 機能一覧

### 1. 基本機能
- **GitHub Issue自動作成**: gh CLIを使用したIssue作成
- **構造化テンプレート**: 統一されたIssueフォーマット
- **自動分類**: 内容に基づく優先度・タイプの自動判定
- **ラベル自動付与**: 設定に基づくラベル管理

### 2. Hive統合機能
- **セッション情報記録**: セッションID、参加ワーカー、実行時間
- **ワーカー別結果**: 各ワーカーの検討結果を構造化
- **品質メトリクス**: 検討時間、提案数、参加者数の記録
- **関連リソース**: 関連ファイル、ドキュメントへのリンク

### 3. 運用機能
- **プレビュー機能**: 作成前の内容確認
- **バッチ処理**: 複数Issue一括作成
- **ログ解析**: ログファイルからの情報抽出
- **設定管理**: YAML設定ファイルによる柔軟な設定

## ファイル構成

```
hive/
├── config/
│   └── github_settings.yaml          # GitHub設定ファイル
├── templates/
│   └── github/
│       └── issue_template.md         # Issueテンプレート
├── scripts/
│   ├── create_github_issue.py        # メインスクリプト
│   ├── github_issue_helper.py        # ヘルパー関数
│   └── test_github_issue_creation.py # テストスクリプト
└── docs/
    └── github_issue_automation.md    # このドキュメント
```

## 使用方法

### 1. 基本的な使用方法

#### コマンドライン使用
```bash
# プレビュー表示
python scripts/create_github_issue.py --preview \
  --title "新機能検討結果" \
  --summary "API機能の拡張について検討" \
  --workers "Queen,Developer"

# Issue作成
python scripts/create_github_issue.py \
  --title "新機能検討結果" \
  --summary "API機能の拡張について検討" \
  --actions "プロトタイプ作成とテスト実施" \
  --workers "Queen,Developer,Analyst"
```

#### JSONファイル使用
```bash
# 検討結果データをJSONファイルに保存
cat > result.json << 'EOF'
{
  "title": "データベース最適化検討",
  "summary": "パフォーマンス改善のための検討結果",
  "details": "インデックス最適化とクエリ改善を実施",
  "actions": "実装とベンチマーク測定",
  "workers": ["Queen", "Developer", "Analyst"],
  "session_id": "session_20240115_001"
}
EOF

# JSONファイルからIssue作成
python scripts/create_github_issue.py --data result.json
```

### 2. Queen Workerからの使用

#### 簡易関数使用
```python
from scripts.github_issue_helper import create_issue_from_queen_worker

# 検討結果からIssue作成
issue_url = create_issue_from_queen_worker(
    session_id="queen_session_001",
    title="UI/UX改善提案",
    summary="ユーザビリティ向上のための検討結果",
    details="ダッシュボード改善とレスポンシブ対応",
    actions="モックアップ作成とユーザーテスト実施",
    workers=["Queen", "Developer", "Designer"]
)

if issue_url:
    print(f"Issue作成完了: {issue_url}")
```

#### 詳細情報付きIssue作成
```python
from scripts.github_issue_helper import HiveGitHubHelper

helper = HiveGitHubHelper()

# 詳細な検討結果データ
additional_data = {
    'duration': '3時間15分',
    'proposal_count': 8,
    'item_count': 15,
    'worker_results': {
        'Queen': {
            'summary': 'プロジェクト全体の統括',
            'recommendations': '段階的な実装を推奨',
            'tasks': ['進捗管理', '品質保証', 'リソース調整']
        },
        'Developer': {
            'summary': '技術実装の検討',
            'recommendations': 'TypeScript移行を推奨',
            'tasks': ['API設計', '実装', 'テスト']
        }
    },
    'related_resources': '- 要件定義書 v2.1\n- 既存システム分析',
    'completion_criteria': '- [ ] プロトタイプ完成\n- [ ] テスト実施',
    'impact': '高 - 全ユーザーに影響'
}

issue_url = helper.create_issue_from_hive_session(
    session_id="detailed_session_001",
    title="包括的システム改善提案",
    summary="システム全体の改善提案",
    details="パフォーマンス、セキュリティ、ユーザビリティの向上",
    actions="段階的実装と継続的改善",
    workers=["Queen", "Developer", "Analyst", "Designer"],
    additional_data=additional_data
)
```

### 3. ログファイルからの自動生成

```python
from scripts.github_issue_helper import HiveGitHubHelper

helper = HiveGitHubHelper()

# ログファイルからIssue作成
issue_url = helper.create_issue_from_log_file(
    log_file_path="logs/hive_session_001.log",
    session_id="session_001"
)
```

### 4. バッチ処理

```python
from scripts.github_issue_helper import HiveGitHubHelper

helper = HiveGitHubHelper()

# 複数の検討結果を一括処理
results_data = [
    {
        'session_id': 'batch_001',
        'title': 'セキュリティ強化提案',
        'summary': '認証システムの改善',
        'workers': ['Queen', 'Security']
    },
    {
        'session_id': 'batch_002', 
        'title': 'パフォーマンス最適化',
        'summary': 'データベース最適化',
        'workers': ['Queen', 'Developer']
    }
]

issue_urls = helper.batch_create_issues(results_data)
```

## 設定ファイル

### config/github_settings.yaml

```yaml
# GitHub設定
github:
  repository:
    auto_detect: true  # git remoteから自動検出
    
  issue:
    title_prefix: "[Hive検討結果]"
    labels:
      default:
        - "hive-result"
        - "type:proposal"
      priority:
        critical: "priority:critical"
        high: "priority:high"
        medium: "priority:medium"
        low: "priority:low"

# Hive設定
hive:
  session:
    include_id: true
    include_timestamp: true
    include_workers: true
    
  results:
    structure:
      summary: true
      details: true
      actions: true
      workers: true
      
# 実行設定
execution:
  mode: "interactive"
  confirmation:
    preview: true
    confirm_create: true
```

## テンプレート

### templates/github/issue_template.md

Issue作成時に使用されるMarkdownテンプレートです。以下の変数が自動置換されます：

- `{{session_id}}`: セッションID
- `{{timestamp}}`: 作成日時
- `{{workers}}`: 参加ワーカー
- `{{title}}`: Issueタイトル
- `{{summary}}`: 概要
- `{{details}}`: 詳細
- `{{actions}}`: 推奨アクション
- `{{priority}}`: 優先度
- `{{type}}`: タイプ

## 動作確認

### テスト実行

```bash
# 基本テスト実行
python scripts/test_github_issue_creation.py

# 実際のプレビュー確認
python scripts/create_github_issue.py --preview \
  --title "テスト検討結果" \
  --summary "機能テストの実施" \
  --workers "Queen,Developer"
```

### 前提条件

1. **GitHub CLI**: `gh` コマンドがインストールされている
2. **認証**: GitHub CLIで認証済み (`gh auth login`)
3. **リポジトリ**: 正しいGitHubリポジトリ内で実行
4. **権限**: Issue作成権限がある

### 認証確認

```bash
# GitHub CLI認証状態確認
gh auth status

# 認証（必要に応じて）
gh auth login
```

## トラブルシューティング

### よくある問題

1. **GitHub CLI未インストール**
   ```bash
   # macOS
   brew install gh
   
   # Ubuntu/Debian
   sudo apt install gh
   ```

2. **認証エラー**
   ```bash
   gh auth login
   ```

3. **リポジトリ検出エラー**
   - `config/github_settings.yaml`でリポジトリを手動設定
   - `auto_detect: false`に設定し、`owner`と`name`を指定

4. **テンプレートエラー**
   - `templates/github/issue_template.md`の存在確認
   - パーミッション確認

### ログ確認

```bash
# ログファイル確認
tail -f logs/github_issue_creation.log

# 詳細ログ（DEBUG）
# config/github_settings.yamlでlevel: "DEBUG"に設定
```

## 拡張機能

### カスタムテンプレート

プロジェクト固有のテンプレートを作成可能：

```bash
# カスタムテンプレート作成
cp templates/github/issue_template.md templates/github/custom_template.md
# 編集...

# カスタムテンプレート使用
# config/github_settings.yamlでfile: "templates/github/custom_template.md"
```

### 自動分類設定

```yaml
# config/github_settings.yaml
hive:
  results:
    classification:
      keywords:
        critical: ["緊急", "障害", "セキュリティ"]
        high: ["重要", "バグ", "機能追加"]
        medium: ["改善", "提案", "検討"]
        low: ["ドキュメント", "メンテナンス"]
```

## 統合例

### Makefileターゲット

```makefile
# Makefile
.PHONY: hive-issue-preview hive-issue-create

hive-issue-preview:
	python scripts/create_github_issue.py --preview \
	  --title "$(TITLE)" --summary "$(SUMMARY)" --workers "$(WORKERS)"

hive-issue-create:
	python scripts/create_github_issue.py \
	  --title "$(TITLE)" --summary "$(SUMMARY)" \
	  --actions "$(ACTIONS)" --workers "$(WORKERS)"
```

### 使用例

```bash
# Makefile経由でIssue作成
make hive-issue-create \
  TITLE="新機能検討" \
  SUMMARY="API拡張の検討結果" \
  ACTIONS="プロトタイプ作成" \
  WORKERS="Queen,Developer"
```

## まとめ

この機能により、Hiveシステムの検討結果を効率的にGitHub Issueとして記録でき、プロジェクト管理の透明性と追跡性が向上します。Queen WorkerやDeveloper Workerの協調作業結果を構造化された形で保存し、継続的な改善に役立てることができます。