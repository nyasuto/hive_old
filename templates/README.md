# Hive Templates

このディレクトリにはテンプレートファイルが含まれます。

## Template Categories

### Nectar Templates (`nectar-templates/`)
- `nectar-template.json` - 基本Nectarテンプレート
- `common-tasks/` - よくあるタスクのテンプレート
- `validation-schema.json` - Nectar形式検証スキーマ

### Project Templates (`project-templates/`)
- `web-app/` - Webアプリケーション開発テンプレート
- `api-service/` - API開発テンプレート
- `data-analysis/` - データ分析テンプレート

### Honey Formats (`honey-formats/`)
- `code-format.json` - コード成果物テンプレート
- `docs-format.json` - ドキュメント成果物テンプレート
- `report-format.json` - レポート成果物テンプレート

## テンプレート使用方法

```bash
# Nectarテンプレートからタスク作成
cp templates/nectar-templates/nectar-template.json .hive/nectar/pending/task-001.json

# プロジェクトテンプレートの適用
./scripts/init-project.sh --template=web-app
```

## カスタムテンプレート作成

1. **構造定義**: JSON スキーマに従った構造
2. **バリデーション**: スキーマ検証の実装
3. **ドキュメント**: 使用方法とサンプルの提供
4. **テスト**: テンプレートの動作確認