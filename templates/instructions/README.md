# Queen指示テンプレート集

## 📋 概要

Hiveマルチエージェントシステムにおいて、ユーザーがQueenに対して効果的な指示を行うためのテンプレート集です。

## 📁 ファイル構成

### 詳細テンプレート
- **`detailed_templates.md`**: 包括的なテンプレート集
  - バグ修正テンプレート
  - 新機能実装テンプレート
  - コードレビューテンプレート
  - 調査・分析テンプレート
  - 文書化テンプレート

### 簡易テンプレート
- **`quick_templates.md`**: コピー＆ペースト用の簡易版
  - クイックバグ修正
  - クイック新機能実装
  - クイックレビュー
  - 緊急対応テンプレート

## 🚀 使い方

### 1. CLIでテンプレート表示
```bash
# 利用可能なテンプレート一覧を表示
python3 scripts/hive_cli.py template show

# 特定のテンプレートを表示
python3 scripts/hive_cli.py template show --type quick

# 詳細テンプレートを表示
python3 scripts/hive_cli.py template show --type detailed
```

### 2. テンプレート選択の指針
- **緊急時**: `quick_templates.md` の緊急対応テンプレート
- **詳細な指示が必要**: `detailed_templates.md` の対応テンプレート
- **シンプルなタスク**: `quick_templates.md` の各種クイック版

### 3. カスタマイズ方法
1. 適切なテンプレートをコピー
2. プロジェクト固有の情報に置換
3. 不要な項目を削除
4. Queenに送信

## 🔧 CLI統合機能

このテンプレート集は、Hive CLIの`template`サブコマンドから直接アクセス可能です：

```bash
# テンプレート検知機能
python3 scripts/hive_cli.py template detect "TASK:BUG_FIX_001:..."

# テンプレート形式での送信
python3 scripts/hive_cli.py template send queen "TASK:..." --ui
```

## 📊 テンプレートパターン対応

以下のテンプレートパターンに対応しています：

- `TASK:[ID]:[INSTRUCTION]` - タスク指示
- `WORKER_RESULT:[WORKER]:[TASK_ID]:[RESULT]` - 作業結果報告
- `QUEEN_FINAL_REPORT:[SESSION_ID]:[REPORT]` - 最終報告
- `URGENT:[DESCRIPTION]` - 緊急対応
- `MULTI:[ID]:[DESCRIPTION]` - 複合タスク

---

*このテンプレート集は継続的に更新・改善されます。新しいシナリオや改善提案があれば随時追加してください。*