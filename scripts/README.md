# Hive Scripts

このディレクトリには自動化スクリプトが含まれます。

## Phase 1 Scripts

- `start-small-hive.sh` - Small Hive起動（Queen + Developer Worker）
- `wake-workers.sh` - Worker起動管理
- `shutdown-hive.sh` - Hive終了
- `check-comb.sh` - Comb通信確認
- `collect-honey.sh` - 成果物収集
- `distribute-nectar.sh` - タスク配布

## 使用方法

```bash
# 基本的なワークフロー
./scripts/start-small-hive.sh     # Hive起動
./scripts/check-comb.sh           # 通信確認
./scripts/collect-honey.sh        # 成果物収集
./scripts/shutdown-hive.sh        # 終了

# 開発時の便利コマンド
make hive-start                   # 起動（Makefile経由）
make hive-status                  # 状況確認
make hive-collect                 # 収集
make hive-stop                    # 終了
```

## スクリプト開発ガイドライン

1. **エラーハンドリング**: 適切なエラー処理と復旧機能
2. **ログ出力**: 実行状況の詳細ログ
3. **tmux統合**: tmux session管理の考慮
4. **依存関係**: 必要なツール・設定の確認