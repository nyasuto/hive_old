# Hive Directory System

## 概要

Hive Directory Systemは、Hiveマルチエージェントシステムのローカルデータ管理と組織化を行うサブシステムです。`.hive/`ディレクトリを使用してセッション、設定、キャッシュ、テンプレートを管理します。

## 主要機能

### 1. ディレクトリ構造管理
- `.hive/`ディレクトリの初期化と管理
- 構造化されたファイル組織
- 自動的なバックアップと復旧

### 2. セッション管理
- セッションの作成、削除、一覧表示
- セッションファイルの管理（analysis.md, design.md, communication.log）
- ワーカー情報の追跡
- セッションステータスの管理

### 3. キャッシュ管理
- 共有キャッシュとワーカー専用キャッシュ
- 期限付きキャッシュのサポート
- バイナリデータの保存
- 自動クリーンアップ

### 4. 設定管理
- 階層的な設定システム
- YAML/JSON形式のサポート
- ドット記法での設定アクセス
- 設定の妥当性検証

### 5. テンプレート管理
- 分析テンプレート
- 設計テンプレート
- ロールテンプレート
- カスタムテンプレートのサポート

## ディレクトリ構造

```
.hive/
├── sessions/               # セッション記録
│   └── session_YYYYMMDD_HHMMSS/
│       ├── session_info.json
│       ├── analysis.md
│       ├── design.md
│       └── communication.log
├── templates/              # テンプレート
│   ├── analysis/
│   ├── design/
│   └── roles/
├── cache/                  # キャッシュ
│   ├── shared/            # 共有キャッシュ
│   └── worker/            # ワーカー専用キャッシュ
├── config/                 # 設定
│   ├── hive_config.yaml
│   ├── worker_config.yaml
│   └── session_config.yaml
├── logs/                   # ローカルログ
└── README.md
```

## 使用方法

### 初期化

```bash
# .hive/ディレクトリを初期化
python -m hive.hive_directory.cli init

# 強制的に再初期化
python -m hive.hive_directory.cli init --force
```

### ステータス確認

```bash
# 現在のステータスを表示
python -m hive.hive_directory.cli status

# JSON形式で出力
python -m hive.hive_directory.cli status --json
```

### セッション管理

```bash
# セッションを作成
python -m hive.hive_directory.cli session create [session_name]

# セッション一覧を表示
python -m hive.hive_directory.cli session list

# セッションの詳細を表示
python -m hive.hive_directory.cli session show <session_id>

# セッションを削除
python -m hive.hive_directory.cli session delete <session_id>
```

### キャッシュ管理

```bash
# キャッシュファイル一覧を表示
python -m hive.hive_directory.cli cache list

# 古いキャッシュをクリーンアップ
python -m hive.hive_directory.cli cache cleanup --days 7

# 全キャッシュをクリア
python -m hive.hive_directory.cli cache clear --confirm
```

### 設定管理

```bash
# 設定を表示
python -m hive.hive_directory.cli config show main
python -m hive.hive_directory.cli config show worker
python -m hive.hive_directory.cli config show session

# 設定値を取得
python -m hive.hive_directory.cli config get main hive.max_workers

# 設定値を変更
python -m hive.hive_directory.cli config set main hive.max_workers 10
```

## プログラムからの使用

### 基本的な使用例

```python
from hive.hive_directory import HiveDirectoryManager

# マネージャーを初期化
hive_manager = HiveDirectoryManager()

# .hive/ディレクトリを初期化
hive_manager.initialize()

# セッションを作成
session_id = hive_manager.session_manager.create_session("my_project")

# セッションファイルに書き込み
hive_manager.session_manager.write_session_file(
    session_id, "analysis", "## 分析結果\\n..."
)

# 共有キャッシュにデータを保存
hive_manager.cache_manager.set_shared_cache(
    "project_data", {"key": "value"}, expire_minutes=60
)

# 設定を取得
max_workers = hive_manager.config_manager.get_config_value(
    "main", "hive.max_workers"
)
```

### セッション操作

```python
# セッション一覧を取得
sessions = hive_manager.session_manager.list_sessions()

# セッション情報を取得
session_info = hive_manager.session_manager.get_session(session_id)

# ワーカーをセッションに追加
worker_info = {
    "worker_id": "analyzer_001",
    "role": "analyzer",
    "status": "active"
}
hive_manager.session_manager.add_worker_to_session(session_id, worker_info)

# セッションファイルに追記
hive_manager.session_manager.append_session_file(
    session_id, "communication", "Worker analyzer_001 started analysis"
)
```

### キャッシュ操作

```python
# 共有キャッシュの操作
hive_manager.cache_manager.set_shared_cache("analysis_result", data)
result = hive_manager.cache_manager.get_shared_cache("analysis_result")

# ワーカー専用キャッシュの操作
hive_manager.cache_manager.set_worker_cache("worker_001", "temp_data", data)
temp_data = hive_manager.cache_manager.get_worker_cache("worker_001", "temp_data")

# バイナリデータの操作
hive_manager.cache_manager.set_binary_cache("image_data", binary_data)
binary_data = hive_manager.cache_manager.get_binary_cache("image_data")
```

## 設定システム

### 設定ファイル

1. **hive_config.yaml** - メイン設定
   - プロジェクト設定
   - ワーカー制限
   - ログ設定

2. **worker_config.yaml** - ワーカー設定
   - ワーカー定義
   - タスク制限
   - 通信設定

3. **session_config.yaml** - セッション設定
   - セッション管理
   - ファイル設定
   - テンプレート設定

### 設定例

```yaml
# hive_config.yaml
hive:
  version: "1.0.0"
  project_name: "my_project"
  max_workers: 8
  session_timeout_minutes: 120
  log_level: "INFO"
  cache_cleanup_days: 7

tmux:
  session_prefix: "hive"
  window_prefix: "worker"
  base_port: 8000

logging:
  enable_file_logging: true
  max_log_size_mb: 10
  log_rotation_count: 5
```

## Git統合

`.gitignore`は自動的に更新され、以下のルールが適用されます：

- `sessions/` - セッションデータは無視
- `cache/` - キャッシュファイルは無視
- `logs/` - ログファイルは無視
- `templates/` - テンプレートは追跡
- `config/` - 設定ファイルは追跡
- `README.md` - READMEは追跡

## API リファレンス

### HiveDirectoryManager

- `initialize(force=False)` - ディレクトリ初期化
- `status()` - ステータス取得
- `cleanup(older_than_days=7)` - クリーンアップ
- `reset()` - ディレクトリリセット

### SessionManager

- `create_session(name=None)` - セッション作成
- `get_session(session_id)` - セッション取得
- `list_sessions()` - セッション一覧
- `delete_session(session_id)` - セッション削除
- `write_session_file(session_id, file_type, content)` - ファイル書き込み
- `append_session_file(session_id, file_type, content)` - ファイル追記

### CacheManager

- `set_shared_cache(key, value, expire_minutes=None)` - 共有キャッシュ設定
- `get_shared_cache(key)` - 共有キャッシュ取得
- `set_worker_cache(worker_id, key, value, expire_minutes=None)` - ワーカーキャッシュ設定
- `get_worker_cache(worker_id, key)` - ワーカーキャッシュ取得
- `clear_all_cache()` - 全キャッシュクリア

### ConfigManager

- `get_main_config()` - メイン設定取得
- `get_worker_config()` - ワーカー設定取得
- `get_session_config()` - セッション設定取得
- `get_config_value(config_type, key_path, default=None)` - 設定値取得
- `set_config_value(config_type, key_path, value)` - 設定値設定

## トラブルシューティング

### よくある問題

1. **初期化エラー**
   - 権限を確認
   - ディスク容量を確認
   - `--force`オプションを使用

2. **セッション作成エラー**
   - `.hive/`ディレクトリが初期化されているか確認
   - 書き込み権限を確認

3. **キャッシュアクセスエラー**
   - ディスク容量を確認
   - ファイルロックを確認

### デバッグ

```bash
# 詳細ログを有効化
python -m hive.hive_directory.cli --verbose status

# 設定の妥当性を検証
python -c "from hive.hive_directory import HiveDirectoryManager; m = HiveDirectoryManager(); print(m.config_manager.validate_config())"
```

## 今後の拡張

- WebUIでの管理機能
- 外部ストレージとの連携
- 自動バックアップ機能
- 分散キャッシュのサポート
- セッション共有機能