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

**✅ 成功の確認：**
- 画面が左右2つのpaneに分割されている
- 左pane: Queen Worker（プロジェクト管理担当）
- 右pane: Developer Worker（実装担当）
- 両paneでClaude Codeが起動している

**🚨 うまくいかない場合：**
```bash
# セッション状態を確認
tmux list-sessions

# 強制再起動
./scripts/shutdown-hive.sh --force
./scripts/start-small-hive.sh
```

## 🎯 最初にやってみること（4分）

**💡 ここからはtmuxセッション内での操作です。左右のpaneを切り替えながら作業します。**

### 1. Worker間の通信テスト

**👈 左pane（Queen Worker）での操作：**

```bash
python examples/quickstart/01_basic_communication.py queen
```

**👉 右pane（Developer Worker）での操作：**

`Ctrl+B` → 右矢印でDeveloper Workerのpaneに移動し：

```bash
python examples/quickstart/01_basic_communication.py developer
```

**🎯 期待する結果：** 
- Queen Worker: "メッセージを送信しました" と表示
- Developer Worker: "受信メッセージ: 1件" と表示され、メッセージ内容が確認できる

### 2. タスク管理機能のテスト

**👈 左pane（Queen Worker）での操作：**

```bash
python examples/quickstart/02_task_management.py queen
```

**👉 右pane（Developer Worker）での操作：**

```bash
python examples/quickstart/02_task_management.py developer
```

**🎯 期待する結果：** 
- Queen Worker: タスク作成、進捗記録、技術決定の記録が完了
- Developer Worker: タスク受信、作業実施、完了報告が完了

### 3. 成果物の確認

**🖥️ 新しいターミナルを開いて確認：**

```bash
# Hiveディレクトリに移動（必要に応じて）
cd /path/to/hive

# 包括的な結果確認
python examples/quickstart/03_check_results.py
```

**🎯 期待する結果：** 
- ✅ Combシステム正常動作確認
- ✅ 作業ログファイルの生成確認
- ✅ メッセージファイルの送受信確認
- ✅ 通信ログ（Markdown）の生成確認

**💡 ヒント：** 生成されたファイルには、Worker間のやり取りが人間が読めるMarkdown形式で記録されています！

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

### 問題2: Python スクリプトでエラーが発生する
```bash
# Combモジュールが見つからない場合
pip install -e .

# プロジェクトディレクトリから実行することを確認
pwd  # /path/to/hive になっているはず

# 詳細なエラー確認
python examples/quickstart/01_basic_communication.py queen
```

### 問題3: Worker間の通信ができない
```bash
# Combシステムの診断
./scripts/check-comb.sh --verbose

# ディレクトリ構造の確認・修復
./scripts/check-comb.sh --fix

# 強制再起動
./scripts/start-small-hive.sh --force
```

### 問題4: スクリプトの実行でヘルプが表示される
```bash
# 引数を正しく指定してください
python examples/quickstart/01_basic_communication.py queen  # Queen Worker用
python examples/quickstart/01_basic_communication.py developer  # Developer Worker用

# 引数なしでヘルプを確認
python examples/quickstart/01_basic_communication.py
```

## 📚 次のステップ

### 詳細を学ぶ
- [セットアップガイド](setup-guide.md) - 詳細な環境構築
- [Comb API仕様](comb-api.md) - 通信システムの詳細
- [トラブルシューティング](troubleshooting.md) - 問題解決
- [クイックスタートサンプル](../examples/quickstart/README.md) - スクリプトの詳細説明

### 実践してみる
- [Web アプリ開発例](../examples/web-app-hive/) - Flask/FastAPI
- [API 開発例](../examples/api-development-hive/) - REST API
- [データ分析例](../examples/data-analysis-hive/) - Pandas/Jupyter

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