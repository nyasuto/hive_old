# 🐝 Hive - Template-Driven Claude Code Collaboration System

## 🚀 プロジェクト概要

**Hive**は、Claude Code インスタンス間でリアルタイム通信を実現し、テンプレートベースの役割定義により長期間の協調作業を支援するマルチエージェント協調システムです。

**核心機能**：
- **1コマンド通信**: `hive send backend "メッセージ"`
- **テンプレート初期化**: `hive bootstrap web-app "プロジェクト名"`
- **役割保持**: `hive who-am-i` で常に自分の役割を確認
- **即時通信**: メッセージが瞬間的に相手の画面に表示

## 🎯 設計哲学

### **シンプルさと確実性**
- **学習コスト最小**: 基本コマンド5つで完結
- **即時配信**: 複雑な受信管理は不要
- **確実な通信**: 構文エラーによる通信失敗を排除

### **役割の一貫性**
- **テンプレート駆動**: プロジェクトタイプに応じた役割定義
- **長期間の保持**: ロールファイルによる役割忘却防止
- **専門性の活用**: 各Workerが得意分野に集中

### **段階的成長**
- **Phase 1**: 基本通信と役割定義
- **Phase 2**: 履歴管理と高度機能
- **Phase 3**: 学習・最適化機能

## 🏠 Hive構成

### **Worker編成**
```
Human Beekeeper (あなた)
└── tmux session: "hive"
    ├── Queen          (pane 0) - プロジェクト管理・統括
    ├── Architect      (pane 1) - システム設計・技術判断
    ├── Frontend       (pane 2) - UI/UX・フロントエンド開発
    ├── Backend        (pane 3) - API/DB・バックエンド開発
    ├── DevOps         (pane 4) - インフラ・運用・デプロイ
    └── Tester         (pane 5) - 品質保証・テスト
```

### **通信システム**
```
全通信は hive CLI 経由:
├── hive send <worker> <message>    # 基本通信
├── hive urgent <worker> <message>  # 緊急通信
├── hive broadcast <message>        # 全体通知
└── hive who-am-i                  # 役割確認
```

## 📋 システム要件

### **必須環境**
- **tmux**: 3.0+
- **Claude Code**: 最新版
- **Python**: 3.9+ (CLI実行用)
- **OS**: macOS, Linux

### **インストール**
```bash
# 1. Hive のクローン
git clone <repository-url> hive
cd hive

# 2. CLI のインストール
chmod +x bin/hive
export PATH="$PWD/bin:$PATH"

# 3. 動作確認
hive --help
```

## 🚀 プロジェクト開始

### **クイックスタート（推奨）**
```bash
# 1. Hive システムの自動起動
./scripts/start-cozy-hive.sh

# 2. ブラウザダッシュボードで監視
python3 scripts/web_dashboard.py
# → http://localhost:8000 でダッシュボードを確認

# 3. 各 Worker で作業開始
# tmux session "cozy-hive" に接続
tmux attach-session -t cozy-hive
# pane間移動: Ctrl+B → 数字キー (0-6)
```

### **手動セットアップ（従来方式）**
```bash
# プロジェクト初期化
hive init "my-project"

# tmux session作成
tmux new-session -d -s hive
# 必要な数のpaneを作成

# 各paneでClaude Code起動
# pane 0: claude --dangerously-skip-permissions  (Queen)
# pane 1: claude --dangerously-skip-permissions  (Architect)
# pane 2: claude --dangerously-skip-permissions  (Frontend)
# pane 3: claude --dangerously-skip-permissions  (Backend)
# pane 4: claude --dangerously-skip-permissions  (DevOps)
# pane 5: claude --dangerously-skip-permissions  (Tester)

# テンプレートベース初期化
hive bootstrap web-app "タスク管理アプリ"
```

### **🌐 ブラウザダッシュボード（Issue #132 実装済み）**
```bash
# 基本起動
python3 scripts/web_dashboard.py

# カスタマイズ
python3 scripts/web_dashboard.py --port 9000 --no-browser

# アクセス先
# 📊 ダッシュボード: http://localhost:8000
# 📡 API仕様書: http://localhost:8000/docs
# 🔌 WebSocket: ws://localhost:8000/ws
```

**ダッシュボード機能**：
- **リアルタイム監視**: Worker状態を1秒間隔で自動更新
- **通信フロー可視化**: SVGアニメーションで Worker間通信を表示
- **パフォーマンス分析**: Chart.js による性能指標可視化
- **レスポンシブデザイン**: モバイル・デスクトップ対応

### **利用可能なプロジェクトテンプレート**
```bash
# フルスタックWebアプリケーション
hive bootstrap web-app "タスク管理アプリ"

# REST API専用開発
hive bootstrap api-only "ユーザー管理API"

# データ分析プロジェクト
hive bootstrap data-analysis "売上データ分析"

# シンプルな静的サイト
hive bootstrap simple-site "会社ホームページ"
```

## 🛠️ コマンドリファレンス

### **基本通信**
```bash
# メッセージ送信
hive send <recipient> "<message>"

# 実例
hive send backend "ユーザー認証APIを実装してください"
hive send frontend "ログイン画面のUIを作成してください"
hive send queen "データベース設計が完了しました"
```

### **特殊通信**
```bash
# 緊急メッセージ（赤色強調表示）
hive urgent <recipient> "<message>"
hive urgent queen "本番サーバーでエラーが発生しています"

# 全体通知
hive broadcast "<message>"
hive broadcast "本日の作業を開始します"
hive broadcast "コードレビューの時間です"
```

### **役割管理**
```bash
# 自分の役割確認
hive who-am-i              # 役割の要約表示
hive my-role               # 詳細な役割説明表示
hive remind-me             # 役割 + 現在のタスク

# システム状況確認
hive status                # 全Worker状況
hive who                   # アクティブWorker一覧

# ブラウザダッシュボード（Issue #132）
hive dashboard             # ダッシュボード起動（scripts/web_dashboard.py のエイリアス）
hive monitor               # リアルタイム監視モード
```

### **Worker識別子**
```
queen      - Queen Worker (プロジェクト管理・統括)
architect  - Architect Worker (システム設計・技術判断)
frontend   - Frontend Worker (UI/UX・フロントエンド開発)
backend    - Backend Worker (API/DB・バックエンド開発)
devops     - DevOps Worker (インフラ・運用・デプロイ)
tester     - Tester Worker (品質保証・テスト)
all        - 全Worker（broadcastと同じ）
```

## 📁 プロジェクト構造

```
hive/
├── bin/
│   └── hive                        # メインCLIスクリプト
├── templates/                      # テンプレート集
│   └── roles/                      # Worker役割テンプレート
│       ├── queen.md               # Queen役割定義
│       ├── architect.md           # Architect役割定義
│       ├── frontend.md            # Frontend役割定義
│       ├── backend.md             # Backend役割定義
│       ├── devops.md              # DevOps役割定義
│       └── tester.md              # Tester役割定義
├── .hive/                         # 実行時データ
│   ├── config.json                # Hive設定
│   ├── workers.json               # Worker-paneマッピング
│   ├── workers/                   # Worker個別データ
│   │   ├── queen/
│   │   │   ├── ROLE.md           # 役割定義（常時参照）
│   │   │   ├── tasks.md          # 現在のタスク
│   │   │   └── context.md        # プロジェクト文脈
│   │   ├── backend/
│   │   │   ├── ROLE.md
│   │   │   └── ...
│   │   └── ...
│   └── logs/                      # 通信ログ
├── src/
├── docs/
└── tests/
└── README.md                      # このファイル
```

## 🎭 役割定義システム

### **ロールファイル（ROLE.md）**
各Workerには専用のロールファイルが自動生成され、以下の情報が含まれます：

```markdown
# 🐝 Backend Worker - Role Definition

## 🎯 基本的な役割
- API開発・設計
- データベース設計・最適化
- 認証・認可システム
- 外部API連携

## 🚫 担当外の領域
- フロントエンド開発（Frontend担当）
- UI/UX設計（Frontend担当）
- インフラ・デプロイ（DevOps担当）

## 🛠️ 使用技術
- Node.js, TypeScript
- Express.js, PostgreSQL
- JWT認証

## 👥 主な連携相手
- Frontend Worker（API仕様共有）
- Architect Worker（設計相談）
- DevOps Worker（環境設定）
```

### **役割忘却の防止**
長時間の作業中に役割を忘れないよう、以下のコマンドで確認できます：

```bash
# 自分の役割を思い出す
hive who-am-i
# 出力例: 🐝 あなたは **Backend Worker** です
#         - API開発・設計を担当
#         - データベース設計・最適化を担当
#         - 認証・認可システムを担当

# 詳細な役割説明を確認
hive my-role
# 出力: ROLE.mdの全文表示

# 現在のタスクと役割を確認
hive remind-me
# 出力: 役割要約 + 現在のタスクリスト
```

## 🎬 実際の使用例

### **プロジェクト開始フロー**
```bash
# 1. Webアプリプロジェクトの初期化
hive bootstrap web-app "タスク管理アプリ"

# 2. Queen からプロジェクト開始宣言
hive broadcast "タスク管理アプリプロジェクトを開始します"

# 3. 各Workerが役割を確認
hive who-am-i

# 4. Queen から初期タスクの配布
hive send architect "システム全体の設計をお願いします"
hive send backend "ユーザー認証APIの実装をお願いします"
hive send frontend "ログイン画面のUIを作成してください"
```

### **典型的な協調作業**
```bash
# Architect → Backend（設計相談）
hive send backend "データベーススキーマについて相談したいです"

# Backend → Frontend（API仕様共有）
hive send frontend "認証APIの仕様を共有します"

# Frontend → Queen（進捗報告）
hive send queen "ログイン画面のプロトタイプが完成しました"

# Backend → DevOps（環境相談）
hive send devops "PostgreSQLの設定について相談があります"

# 問題発生時の緊急報告
hive urgent queen "データベース接続エラーが発生しています"
```

### **役割確認の活用**
```bash
# 作業中に迷った時
hive who-am-i
# → 自分の専門分野を思い出す

# 担当外の質問を受けた時
hive my-role
# → 担当外であることを確認して適切にリダイレクト

# 新しいタスクを受けた時
hive remind-me
# → 現在のタスクとの整合性を確認
```

## 🔧 カスタマイズ

### **ブラウザダッシュボードの設定**
```bash
# カスタムポート（デフォルト: 8000）
python3 scripts/web_dashboard.py --port 9000

# セキュリティ強化（localhost のみ）
python3 scripts/web_dashboard.py --host localhost

# 自動ブラウザ起動を無効
python3 scripts/web_dashboard.py --no-browser

# 開発モード無効（本番用）
python3 scripts/web_dashboard.py --no-reload

# Hive システム未起動でも強制起動
python3 scripts/web_dashboard.py --force
```

### **新しいWorkerの追加**
```bash
# 新Worker用pane作成
tmux new-window -t hive -n ml-engineer

# Claude Code起動後、Workerを追加
hive add-worker ml-engineer "Machine Learning Engineer"

# 新しいWorkerとの通信開始
hive send ml-engineer "データ分析をお願いします"
```

### **カスタムプロジェクトテンプレート**
```yaml
# templates/projects/mobile-app.yaml
project_type: "mobile-app"
description: "モバイルアプリケーション開発"
tech_stack: "React Native + Firebase"

workers:
  queen:
    template: "queen"
    project_specifics:
      - "アプリストア申請管理"
      - "ユーザーフィードバック対応"
    first_tasks:
      - "アプリ要件定義"
      - "開発スケジュール策定"
  
  mobile-dev:
    template: "mobile-dev"
    project_specifics:
      - "React Native開発"
      - "iOS/Android両対応"
    first_tasks:
      - "プロジェクト環境セットアップ"
      - "基本画面構成の実装"
```

## 💡 効果的な使い方

### **良いメッセージの書き方**
```bash
# ✅ 具体的で行動を促す
hive send backend "ユーザー認証APIを /api/auth/login エンドポイントで実装してください"

# ✅ 簡潔で理解しやすい
hive send frontend "ログイン画面のレスポンシブデザインをお願いします"

# ✅ 感謝と励ましを込めて
hive send tester "テストお疲れ様です。修正版をデプロイしました"
```

### **避けるべきメッセージ**
```bash
# ❌ 曖昧すぎる
hive send backend "よろしく"

# ❌ 担当外の指示
hive send backend "UIの色を変更してください"  # Frontend担当

# ❌ 感情的すぎる
hive urgent all "なんでエラーになるんだ！"
```

### **役割の効果的な活用**
```bash
# 専門外の質問を受けた時
hive who-am-i  # 自分の担当を確認
hive send frontend "UI関連は Frontend Worker が詳しいです"

# 新しいタスクを受けた時
hive remind-me  # 現在のタスクと整合性を確認
hive send queen "現在のタスクとの優先順位を確認したいです"
```

## 📊 Phase 1 成功目標

### **技術的成功基準**
- [ ] メッセージ送信成功率 95%以上
- [ ] 役割認識の維持（定期確認で測定）
- [ ] Worker間の適切な連携（専門分野の遵守）
- [ ] プロジェクト完成率 80%以上

### **協調的成功基準**
- [ ] Claude Code同士の自然な会話
- [ ] 専門性を活かした高品質な成果物
- [ ] 効率的なタスク分担と進行
- [ ] 問題発生時の迅速な情報共有

### **プロジェクト例**
- **Webアプリ**: シンプルなTODO管理アプリ
- **API**: 基本的なユーザー管理API
- **データ分析**: 売上データの可視化
- **静的サイト**: 会社紹介ページ

## ⚠️ 注意事項・運用Tips

### **コスト管理**
- 複数Claude Code並列実行でAPI使用量増加
- 長時間の会話は定期的に `/clear` でリセット
- 役割確認コマンドは適度に使用（頻繁すぎない）

### **効果的な運用**
- **明確な指示**: 何をしてほしいか具体的に伝える
- **定期的な確認**: `hive status` でWorker状況をチェック
- **役割の尊重**: 専門外の作業を無理に依頼しない
- **感謝の表現**: 協力への感謝を忘れずに

### **トラブルシューティング**
```bash
# メッセージが届かない
hive status                    # Worker状況確認
tmux list-panes               # pane状況確認

# 役割を忘れた時
hive who-am-i                 # 簡潔な役割確認
hive my-role                  # 詳細な役割確認

# CLI動作不良
hive --help                   # ヘルプ確認
hive status --debug           # デバッグ情報

# ダッシュボード接続不良
python3 scripts/web_dashboard.py --check-only  # 依存関係確認
python3 scripts/web_dashboard.py --port 8001   # 別ポートで起動
pkill -f web_dashboard.py                      # プロセス強制終了
```

## 🌱 将来の発展

### **Phase 2: 履歴・分析機能（3-4週間後）**
- `hive history` - メッセージ履歴確認
- `hive search` - 過去のやり取り検索
- ファイル添付機能
- 通信パターン分析

### **Phase 3: ブラウザダッシュボード（✅ 実装完了 - Issue #132）**
- ✅ **FastAPI + WebSocket** リアルタイム通信基盤
- ✅ **Vue.js スタイル** フロントエンド環境
- ✅ **Chart.js 統合** パフォーマンス可視化
- ✅ **SVG アニメーション** 通信フロー表示
- ✅ **レスポンシブデザイン** モバイル・デスクトップ対応

### **Phase 4: 学習・最適化機能（2-3ヶ月後）**
- Worker間協調パターンの学習
- 効率的なタスク分担の提案
- 自動的な役割調整
- プロジェクト成功パターンの蓄積

### **Phase 5: エンタープライズ機能（6ヶ月後）**
- 大規模チーム対応（複数Hive並列実行）
- 外部システム連携（GitHub/Slack/JIRA統合）
- セキュリティ強化（認証・認可システム）
- クラウドデプロイ対応

## 🤝 コミュニティ

### **サポート・フィードバック**
- **GitHub Issues**: バグ報告・機能要求
- **Discussions**: 使用方法・成功事例の共有
- **Examples**: 実プロジェクトでの活用例
- **Templates**: カスタムテンプレートの共有

### **コントリビューション歓迎**
- CLI機能の改善
- 新しいプロジェクトテンプレート
- Worker役割定義の改善
- ドキュメント・使用例の追加

---

**🍯 Template-Driven, Role-Aware Collaboration!**

テンプレートベースの役割定義により、各Claude Codeが専門性を保ちながら美しく協調する、新しいAIチーム開発を体験してください。