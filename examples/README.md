# Hive Examples

このディレクトリにはHiveシステムの使用例が含まれます。

## サンプルプロジェクト

### Web App Hive (`web-app-hive/`)
Webアプリケーション開発でのHive使用例：
- React + Express.js アプリケーション
- Frontend Worker + Backend Worker協調
- 完全なフロントエンド〜バックエンド開発フロー

### API Development Hive (`api-development-hive/`)
API開発でのHive使用例：
- REST API開発
- OpenAPI仕様書生成
- テスト駆動開発（TDD）

### Data Analysis Hive (`data-analysis-hive/`)
データ分析でのHive使用例：
- Python データ分析パイプライン
- Jupyter Notebook + スクリプト生成
- レポート自動生成

## サンプル実行方法

```bash
# サンプルプロジェクトの実行
cd examples/web-app-hive
../../scripts/start-small-hive.sh --project=web-app

# または Makefile 経由
make run-example EXAMPLE=web-app-hive
```

## カスタムプロジェクト作成

1. **テンプレート選択**: 最も近いサンプルをコピー
2. **設定カスタマイズ**: Nectar、Worker prompts を調整
3. **ワークフロー定義**: プロジェクト固有のタスクフローを定義
4. **品質基準設定**: プロジェクト要件に応じた品質基準を設定