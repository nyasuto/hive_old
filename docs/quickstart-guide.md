# 🐝 Hive - クイックスタートガイド（10分で開始）

## 🚀 簡単3ステップ

### ステップ1: 環境確認（2分）
```bash
# 必要なツールがインストール済みか確認
which tmux python3 git
```

**必要な環境：**
- macOS または Linux
- tmux 3.0+
- Python 3.9+
- Claude Code（Claude Pro推奨）

### ステップ2: Hive起動（3分）
```bash
# Hiveをクローン
git clone https://github.com/nyasuto/hive.git
cd hive

# Small Colony（2 Workers）を起動
./scripts/start-small-hive.sh
```

### ステップ3: Hiveに接続（1分）
```bash
# tmuxセッションに接続
tmux attach-session -t hive-small-colony
```

## 🎯 最初にやってみること（4分）

### 1. Worker間の通信テスト
```bash
# 左pane (Queen Worker) で実行：
from comb import CombAPI
queen = CombAPI("queen")
queen.send_message(
    to_worker="developer",
    content={"task": "Hello from Queen!", "priority": "low"},
    message_type="request"
)

# 右pane (Developer Worker) で実行：
from comb import CombAPI
dev = CombAPI("developer")
messages = dev.receive_messages()
print(f"受信メッセージ: {len(messages)}件")
```

### 2. 簡単なタスク実行
```bash
# Queen Worker で：
task_id = queen.start_task("テスト機能実装", task_type="feature")
print(f"タスク開始: {task_id}")

# Developer Worker で：
progress = dev.add_progress("環境確認完了", "実装準備中")
print("進捗を報告しました")
```

### 3. 成果物の確認
```bash
# 新しいターミナルで：
./scripts/collect-honey.sh stats
```

## 🔧 基本操作

### tmux操作
- **pane切り替え**: `Ctrl+B` → 矢印キー
- **セッション終了**: `Ctrl+B` → `d` (デタッチ)
- **セッション復帰**: `tmux attach-session -t hive-small-colony`

### Hive操作
```bash
# 通信状況確認
./scripts/check-comb.sh

# タスク配布
./scripts/distribute-nectar.sh examples/simple-task.json

# 成果物収集
./scripts/collect-honey.sh auto

# Hive終了
./scripts/shutdown-hive.sh
```

## 🎬 実用例：簡単なWebアプリ作成

### Queen Worker (左pane)
```python
from comb import CombAPI

queen = CombAPI("queen")

# プロジェクト開始
task_id = queen.start_task(
    "Flask Hello World アプリ",
    task_type="feature",
    workers=["queen", "developer"]
)

# Developer Workerに指示
queen.send_message(
    to_worker="developer",
    content={
        "task": "簡単なFlask Webアプリを作成",
        "requirements": [
            "Hello World ページ",
            "ポート5000で起動",
            "簡単なHTML テンプレート"
        ]
    },
    message_type="request",
    priority="medium"
)
```

### Developer Worker (右pane)
```python
from comb import CombAPI

dev = CombAPI("developer")

# タスク受信
messages = dev.receive_messages()
for msg in messages:
    print(f"新しいタスク: {msg.content}")

# 実装作業（実際のコード作成）
# app.py を作成...
# templates/index.html を作成...

# 進捗報告
dev.add_progress(
    "Flask アプリ基本構造作成完了",
    "HTML テンプレート実装中"
)

# 完了報告
dev.send_response(msg, {
    "status": "completed",
    "files_created": ["app.py", "templates/index.html"],
    "next_steps": ["テスト実行", "エラーチェック"]
})
```

## ⚠️ よくある問題と解決方法

### 問題1: tmuxセッションが起動しない
```bash
# 既存セッションがある場合
tmux kill-session -t hive-small-colony
./scripts/start-small-hive.sh --force
```

### 問題2: Worker間の通信ができない
```bash
# Combディレクトリの権限確認
ls -la .hive/
chmod -R 755 .hive/

# ディレクトリ構造の再作成
./scripts/start-small-hive.sh --force
```

### 問題3: Python モジュールが見つからない
```bash
# プロジェクトディレクトリから実行することを確認
pwd  # /path/to/hive になっているはず
export PYTHONPATH="$PWD:$PYTHONPATH"
```

## 📚 次のステップ

### 詳細を学ぶ
- [セットアップガイド](docs/setup-guide.md) - 詳細な環境構築
- [Comb API仕様](docs/comb-api.md) - 通信システムの詳細
- [トラブルシューティング](docs/troubleshooting.md) - 問題解決

### 実践してみる
- [Web アプリ開発例](examples/web-app-hive/) - Flask/FastAPI
- [API 開発例](examples/api-development-hive/) - REST API
- [データ分析例](examples/data-analysis-hive/) - Pandas/Jupyter

### システムを拡張する
```bash
# 完全なHive (6 Workers) を試す
./scripts/start-hive.sh --size=full

# カスタムWorkerの追加
cp workers/prompts/developer_worker.md workers/prompts/my_worker.md
# プロンプトを編集...
```

## 🎉 成功！

これでHive Small Colonyが動作しています！Queen WorkerとDeveloper Workerが協調して開発作業を行う準備が整いました。

次の目標：
- [ ] Worker間での実際のプロジェクト協調
- [ ] 成果物（Honey）の品質確認
- [ ] 作業ログ（Work Log）の確認
- [ ] より複雑なタスクの実行

**🍯 Sweet coding with Hive!**

---

## 📞 ヘルプが必要な場合

- **GitHub Issues**: バグ報告・質問
- **Documentation**: [完全なREADME](README.md)
- **Examples**: `examples/` ディレクトリ
- **Logs**: `.hive/logs/` で詳細ログを確認

このガイドで10分以内にHiveを使い始めることができます。より詳細な情報は各ドキュメントをご参照ください！