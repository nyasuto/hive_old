# 🐝 Hive Comb API 仕様書

## 📋 目次

1. [概要](#概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [CombAPI クラス](#combapi-クラス)
4. [メッセージング](#メッセージング)
5. [Nectar管理](#nectar管理)
6. [同期機能](#同期機能)
7. [作業ログ](#作業ログ)
8. [エラーハンドリング](#エラーハンドリング)
9. [実用例](#実用例)

## 🎯 概要

Hive Comb APIは、Worker間の通信、タスク管理、同期機能を提供するファイルベース通信システムです。tmux環境でのClaude Code Worker間の協調作業を実現します。

### 主要機能
- **Worker間メッセージング**: リクエスト/レスポンス、通知、エラー処理
- **Nectar管理**: タスクの配布、実行、完了管理
- **同期機能**: リソースロック、排他制御
- **作業ログ**: 進捗追跡、技術的決定の記録
- **Markdownログ**: 人間可読な通信ログ生成

## 🏗️ アーキテクチャ

### ディレクトリ構造
```
.hive/
├── comb/                    # 通信システム
│   ├── messages/            # メッセージ交換
│   │   ├── inbox/           # 受信メッセージ
│   │   ├── outbox/          # 送信メッセージ
│   │   ├── pending/         # 保留中メッセージ
│   │   ├── sent/            # 送信完了メッセージ
│   │   └── failed/          # 失敗メッセージ
│   ├── locks/               # リソースロック
│   └── communication_logs/ # Markdownログ
├── nectar/                  # タスク管理
│   ├── pending/             # 未着手タスク
│   ├── active/              # 実行中タスク
│   └── completed/           # 完了タスク
├── honey/                   # 成果物
├── work_logs/               # 作業ログ
│   ├── daily/               # 日次ログ
│   └── projects/            # プロジェクト別ログ
└── locks/                   # 同期用ロック
```

## 🔧 CombAPI クラス

### 初期化

```python
from comb import CombAPI

# 基本初期化
api = CombAPI("worker_id")

# カスタム初期化
api = CombAPI(
    worker_id="developer",
    enable_markdown_logging=True
)
```

#### パラメータ
- `worker_id: str` - Worker識別子（必須）
- `file_handler: HiveFileHandler | None` - ファイルハンドラー（オプション）
- `message_router: MessageRouter | None` - メッセージルーター（オプション）
- `sync_manager: SyncManager | None` - 同期マネージャー（オプション）
- `work_log_manager: WorkLogManager | None` - 作業ログマネージャー（オプション）
- `enable_markdown_logging: bool` - Markdownログ機能（デフォルト: True）

## 📨 メッセージング

### メッセージタイプ

```python
from comb.message_router import MessageType, MessagePriority

# メッセージタイプ
MessageType.REQUEST            # リクエスト
MessageType.RESPONSE          # レスポンス
MessageType.NOTIFICATION      # 通知
MessageType.ERROR             # エラー
MessageType.NECTAR_DISTRIBUTION  # Nectar配布
MessageType.STATUS_REQUEST    # ステータス要求
MessageType.ALERT             # アラート
MessageType.URGENT_NOTIFICATION  # 緊急通知

# 優先度
MessagePriority.LOW           # 低優先度 (1)
MessagePriority.MEDIUM        # 中優先度 (2)
MessagePriority.HIGH          # 高優先度 (3)
MessagePriority.URGENT        # 緊急 (4)
```

### 基本メッセージ送信

```python
# 基本的なメッセージ送信
success = api.send_message(
    to_worker="developer",
    content={
        "task": "新機能の実装",
        "priority": "high",
        "deadline": "2024-01-15"
    },
    message_type=MessageType.REQUEST,
    priority=MessagePriority.HIGH,
    ttl_minutes=60  # 60分で期限切れ
)
```

### レスポンス送信

```python
# 受信したメッセージへの返信
messages = api.receive_messages()
for message in messages:
    if message.message_type == MessageType.REQUEST:
        success = api.send_response(
            original_message=message,
            response_content={
                "status": "accepted",
                "estimated_completion": "2024-01-14T15:00:00",
                "assigned_developer": "alice"
            },
            priority=MessagePriority.MEDIUM
        )
```

### 通知とエラー

```python
# 通知送信
api.send_notification(
    to_worker="queen",
    content={
        "status": "progress_update",
        "completed_features": ["authentication", "user_management"],
        "current_task": "database_integration"
    },
    priority="medium"  # 文字列でも指定可能
)

# エラー通知
api.send_error(
    to_worker="queen",
    error_message="Database connection failed",
    error_details={
        "error_code": "DB_CONN_001",
        "database": "postgresql://localhost:5432/hive",
        "retry_attempts": 3
    }
)
```

### Ping/Pong（ヘルスチェック）

```python
# Ping送信
api.ping("developer")

# Pong応答（受信したPingメッセージに対して）
messages = api.receive_messages()
for message in messages:
    if message.content.get("action") == "ping":
        api.pong(message)
```

## 🍯 Nectar管理

### Nectar送信（タスク作成）

```python
# タスクの作成と送信
success = api.send_nectar(
    nectar_type="feature_implementation",
    content={
        "title": "ユーザー認証機能の実装",
        "description": "JWT認証とパスワードハッシュ化を含む完全な認証システム",
        "requirements": [
            "JWT token生成/検証",
            "bcryptによるパスワードハッシュ化",
            "ログイン/ログアウトAPI",
            "ユーザー権限管理"
        ],
        "files_to_create": [
            "auth/jwt_handler.py",
            "auth/password_manager.py",
            "api/auth_routes.py"
        ],
        "estimated_hours": 8
    },
    priority="high"
)
```

### Nectar受信（タスク取得）

```python
# 待機中のタスクを取得
nectar = api.receive_nectar()
if nectar:
    print(f"新しいタスク: {nectar['content']['title']}")
    print(f"タスクID: {nectar['id']}")
    print(f"優先度: {nectar['priority']}")
    
    # タスクを開始...
```

### Nectar完了

```python
# タスク完了の報告
success = api.complete_nectar(
    nectar_id="nectar_1705123456789",
    result={
        "status": "completed",
        "files_created": [
            "auth/jwt_handler.py",
            "auth/password_manager.py",
            "api/auth_routes.py",
            "tests/test_auth.py"
        ],
        "test_coverage": "95%",
        "performance_notes": "JWT token validation: <1ms",
        "documentation": "API documentation updated in docs/auth.md"
    }
)
```

## 🔒 同期機能

### リソースロック

```python
# リソースの排他制御
resource_name = "database_schema"

# ロック取得
if api.acquire_lock(resource_name, timeout=10.0):
    try:
        # 排他的な処理を実行
        print("データベース スキーマを更新中...")
        # ... スキーマ更新処理 ...
        
    finally:
        # ロック解放
        api.release_lock(resource_name)
else:
    print("ロック取得に失敗しました")
```

### 実用的なロック例

```python
# 設定ファイル更新の排他制御
if api.acquire_lock("config_file", timeout=5.0):
    try:
        # 設定読み込み
        config = load_config()
        
        # 設定更新
        config['database']['port'] = 5433
        
        # 設定保存
        save_config(config)
        
        # 他のWorkerに変更を通知
        api.send_notification(
            to_worker="all",
            content={
                "config_updated": True,
                "changes": {"database.port": 5433}
            }
        )
        
    finally:
        api.release_lock("config_file")
```

## 📊 作業ログ

### タスク開始

```python
# 新しいタスクの開始
task_id = api.start_task(
    task_title="RESTful API実装",
    task_type="feature",
    description="ユーザー管理用のRESTful APIエンドポイントを実装",
    issue_number=42,
    workers=["developer", "tester"]
)
print(f"タスク開始: {task_id}")
```

### 進捗記録

```python
# 進捗の記録
api.add_progress(
    description="ユーザー登録APIの実装完了",
    details="POST /api/users エンドポイント実装。バリデーション、重複チェック、パスワードハッシュ化を含む"
)

api.add_progress(
    description="ユニットテスト作成完了",
    details="test_user_registration.py 作成。正常ケース、異常ケース、境界値テストを含む"
)
```

### 技術的決定の記録

```python
# 技術選択の記録
api.add_technical_decision(
    decision="FastAPIフレームワークの採用",
    reasoning="高性能、型安全性、自動API文書生成機能により開発効率が向上",
    alternatives=["Flask", "Django REST Framework", "Tornado"]
)

api.add_technical_decision(
    decision="PostgreSQL使用",
    reasoning="ACID特性、JSON型サポート、優れたパフォーマンス",
    alternatives=["MySQL", "SQLite", "MongoDB"]
)
```

### 課題と解決策

```python
# 技術的課題の記録
api.add_challenge(
    challenge="CORS設定でフロントエンドからのリクエストが拒否される",
    solution="FastAPIのCORSMiddleware設定を追加。開発環境では localhost:3000 を許可"
)

api.add_challenge(
    challenge="パスワードハッシュ化に時間がかかる",
    solution="bcryptのrounds数を12から10に調整。セキュリティを保ちつつレスポンス時間を改善"
)
```

### メトリクス記録

```python
# パフォーマンスメトリクスの記録
api.add_metrics({
    "response_time_ms": {
        "user_registration": 245,
        "user_login": 156,
        "user_profile": 89
    },
    "test_coverage": {
        "unit_tests": "94%",
        "integration_tests": "87%"
    },
    "code_quality": {
        "pylint_score": 9.2,
        "complexity_score": "low"
    }
})
```

### タスク完了

```python
# タスクの完了
api.complete_task("completed_successfully")

# 現在のタスク情報取得
current_task = api.get_current_task()
if current_task:
    print(f"現在のタスク: {current_task['title']}")
    print(f"開始時刻: {current_task['start_time']}")
```

## ⚠️ エラーハンドリング

### メッセージハンドラー登録

```python
# メッセージハンドラーの登録
def handle_request(message):
    try:
        # リクエスト処理
        result = process_request(message.content)
        
        # 成功レスポンス
        api.send_response(message, {
            "status": "success",
            "result": result
        })
        
    except Exception as e:
        # エラーレスポンス
        api.send_error(
            message.from_worker,
            f"Request processing failed: {str(e)}",
            {"request_id": message.id, "error_type": type(e).__name__}
        )

# ハンドラー登録
api.register_handler(MessageType.REQUEST, handle_request)

# 自動ポーリング開始
api.start_polling(interval=1.0)
```

### エラー処理パターン

```python
# タイムアウト処理
def send_with_retry(api, to_worker, content, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            success = api.send_message(
                to_worker=to_worker,
                content=content,
                ttl_minutes=5  # 短いTTL
            )
            if success:
                return True
                
        except Exception as e:
            print(f"送信試行 {attempt + 1} 失敗: {e}")
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)  # 指数バックオフ
                
    return False

# 接続状況確認
def check_worker_health(api, worker_id):
    try:
        api.ping(worker_id)
        
        # レスポンス待機
        start_time = time.time()
        while time.time() - start_time < 5:  # 5秒待機
            messages = api.receive_messages()
            for msg in messages:
                if msg.content.get("action") == "pong":
                    return True
            time.sleep(0.1)
            
    except Exception:
        pass
        
    return False
```

## 🛠️ 実用例

### Queen ↔ Developer Worker 協調

#### Queen Worker
```python
from comb import CombAPI

queen = CombAPI("queen")

# プロジェクト開始
task_id = queen.start_task(
    "Webアプリケーション開発",
    task_type="feature",
    issue_number=123,
    workers=["queen", "developer"]
)

# Developer Workerにタスク配布
queen.send_nectar(
    nectar_type="web_development",
    content={
        "project": "E-commerce Platform",
        "features": [
            "商品カタログ",
            "ショッピングカート",
            "決済システム"
        ],
        "technology_stack": {
            "backend": "FastAPI",
            "frontend": "React",
            "database": "PostgreSQL"
        },
        "timeline": "2週間"
    },
    priority="high"
)

# 進捗監視
def monitor_progress():
    messages = queen.receive_messages()
    for message in messages:
        if message.message_type == MessageType.NOTIFICATION:
            print(f"進捗更新: {message.content}")
            
# 定期的な進捗確認
queen.register_handler(MessageType.NOTIFICATION, monitor_progress)
queen.start_polling()
```

#### Developer Worker
```python
from comb import CombAPI

developer = CombAPI("developer")

# タスク受信と開始
nectar = developer.receive_nectar()
if nectar:
    task_id = developer.start_task(
        nectar['content']['project'],
        task_type="implementation"
    )
    
    # 実装開始の報告
    developer.send_notification(
        to_worker="queen",
        content={
            "status": "implementation_started",
            "nectar_id": nectar['id'],
            "estimated_completion": "2024-01-30"
        }
    )
    
    # 実装作業
    features = nectar['content']['features']
    for i, feature in enumerate(features):
        # 機能実装...
        implement_feature(feature)
        
        # 進捗報告
        developer.add_progress(
            f"{feature} 実装完了",
            f"進捗: {i+1}/{len(features)}"
        )
        
        developer.send_notification(
            to_worker="queen",
            content={
                "feature_completed": feature,
                "progress": f"{((i+1)/len(features)*100):.1f}%"
            }
        )
    
    # タスク完了
    developer.complete_nectar(nectar['id'], {
        "status": "completed",
        "features_implemented": features,
        "code_coverage": "92%",
        "performance_score": "A+"
    })
    
    developer.complete_task("implementation_completed")
```

### エラー処理と回復

```python
from comb import CombAPI
import time

api = CombAPI("robust_worker")

def robust_message_processing():
    """堅牢なメッセージ処理"""
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            messages = api.receive_messages()
            
            for message in messages:
                try:
                    process_message(message)
                    
                except Exception as e:
                    # メッセージ処理エラー
                    api.send_error(
                        message.from_worker,
                        f"Message processing failed: {str(e)}",
                        {
                            "message_id": message.id,
                            "error_details": str(e),
                            "retry_possible": True
                        }
                    )
                    
            retry_count = 0  # 成功時はリセット
            break
            
        except Exception as e:
            retry_count += 1
            print(f"Communication error (attempt {retry_count}): {e}")
            
            if retry_count < max_retries:
                time.sleep(2 ** retry_count)  # 指数バックオフ
            else:
                # 致命的エラーの報告
                api.send_error(
                    "queen",
                    "Worker communication failure",
                    {
                        "worker_id": api.worker_id,
                        "error": str(e),
                        "requires_restart": True
                    }
                )
                
def process_message(message):
    """メッセージ処理ロジック"""
    if message.message_type == MessageType.REQUEST:
        # リクエスト処理
        handle_request(message)
    elif message.message_type == MessageType.NOTIFICATION:
        # 通知処理
        handle_notification(message)
```

## 📈 ステータス監視

```python
# Worker状況の確認
status = api.get_status()
print(f"""
Worker Status: {status['worker_id']}
Polling Active: {status['polling']}
Messages: {status['messages']}
Locks: {status['locks']}
Work Logs: {status['work_logs']}
Timestamp: {status['timestamp']}
""")

# 日次サマリー生成
success = api.generate_daily_summary()
if success:
    print("日次サマリーが生成されました")
```

## 🔧 高度な使用方法

### カスタムメッセージハンドラー

```python
class AdvancedWorker:
    def __init__(self, worker_id):
        self.api = CombAPI(worker_id)
        self.setup_handlers()
        
    def setup_handlers(self):
        """カスタムハンドラーの設定"""
        self.api.register_handler(MessageType.REQUEST, self.handle_request)
        self.api.register_handler(MessageType.NOTIFICATION, self.handle_notification)
        self.api.register_handler(MessageType.ERROR, self.handle_error)
        
    def handle_request(self, message):
        """リクエスト処理"""
        request_type = message.content.get("type")
        
        if request_type == "code_review":
            self.perform_code_review(message)
        elif request_type == "deployment":
            self.perform_deployment(message)
        else:
            self.api.send_error(
                message.from_worker,
                f"Unknown request type: {request_type}"
            )
            
    def handle_notification(self, message):
        """通知処理"""
        self.api.add_progress(
            f"Received notification: {message.content.get('type', 'unknown')}"
        )
        
    def handle_error(self, message):
        """エラー処理"""
        print(f"Error received: {message.content}")
        # エラー処理ロジック...
```

この仕様書により、Hive Comb APIの完全な機能を理解し、効果的なWorker間協調システムを構築できます。

**🍯 Happy coding with Hive Comb API!**