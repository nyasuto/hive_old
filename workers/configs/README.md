# Worker Configs

このディレクトリには各Worker用の設定ファイルが含まれます。

## 設定ファイル構成

- `base_config.json` - 全Worker共通の基本設定
- `queen_config.json` - Queen Worker専用設定
- `developer_config.json` - Developer Worker専用設定

## 設定項目

### 基本設定
- **worker_id**: Worker識別子
- **role**: Worker役割
- **comb_path**: Comb通信ディレクトリパス
- **log_level**: ログレベル

### 通信設定
- **message_check_interval**: メッセージチェック間隔（秒）
- **max_retries**: 通信失敗時の最大リトライ回数
- **timeout**: 通信タイムアウト（秒）

### 品質設定
- **code_standards**: コード品質基準
- **documentation_requirements**: ドキュメント要求事項
- **review_criteria**: レビュー基準