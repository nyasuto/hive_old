# 🐝 Hive - Claude Code Multi-Agent System

## 🚀 プロジェクト概要

**Hive**は、Claude Codeを複数並列実行し、各インスタンスに専門的な役割を与えて協調的にタスクを遂行するマルチエージェントシステムです。蜂の巣（Hive）のように、各Worker（エージェント）が専門性を活かしながらQueen（中央管理）の下で組織的に働き、美しいHoney（成果物）を生み出します。

tmuxとComb（ファイルベース通信システム）を使用してAIチームを組織化し、大規模プロジェクトの効率的な開発を実現します。

## 🏠 Hiveの構造

### エージェント構成（The Colony）
```
Human Beekeeper (あなた)
└── Hive Session: "hive"
    ├── Queen Worker       (pane 0) - プロジェクト管理・調整
    ├── Architect Worker   (pane 1) - システム設計・アーキテクチャ
    ├── Frontend Worker    (pane 2) - UI/UX開発・フロントエンド
    ├── Backend Worker     (pane 3) - API/DB開発・バックエンド
    ├── DevOps Worker      (pane 4) - インフラ・CI/CD・運用
    └── Tester Worker      (pane 5) - テスト・品質保証
```

### Comb Architecture（通信システム）
```
Comb（ファイルベース通信）
├── .hive/
│   ├── nectar/              # 入力データ・要件
│   │   ├── pending/         # 未着手タスク
│   │   ├── active/          # 実行中タスク  
│   │   └── completed/       # 完了タスク
│   ├── comb/               # Worker間通信
│   │   ├── messages/        # メッセージ交換
│   │   ├── shared/          # 共有リソース
│   │   └── cells/           # 通信セル
│   ├── honey/              # 成果物
│   │   ├── code/            # 生成されたコード
│   │   ├── docs/            # ドキュメント
│   │   └── reports/         # レポート・分析結果
│   └── logs/               # 活動ログ
└── project/               # 実際の開発プロジェクト
```

## 📋 システム要件

### 必須環境
- **OS**: macOS, Linux (tmux対応)
- **Python**: 3.9+ 
- **Claude Code**: 最新版
- **tmux**: 3.0+
- **Shell**: bash/zsh

### 推奨環境
- **プラン**: Claude Pro ($20/月) または Claude for Work
- **メモリ**: 8GB以上
- **ターミナル**: 大画面推奨 (複数pane表示)

## 🎯 開発ロードマップ

### Phase 1: Small Colony (最小実行可能Hive)
**目標**: 基本的な2-Worker協調システム
**期間**: 1-2週間

#### 必須機能
- [ ] tmuxによる2つのClaude Code Workerの起動
- [ ] Combによる基本的なNectar（タスク）交換機能  
- [ ] Queen ↔ Developer Worker の基本ワークフロー
- [ ] シンプルなNectarテンプレート
- [ ] 基本的なHoney（成果物）収集機能

#### 成果物
- `start-small-hive.sh` - 基本Hive起動スクリプト
- `nectar-template.json` - タスク定義テンプレート
- `collect-honey.sh` - 成果物収集スクリプト
- `README-basic.md` - 基本使用方法

### Phase 2: Full Colony (完全なHive体制)
**目標**: 6-Worker体制の構築
**期間**: 3-4週間

#### 拡張機能
- [ ] 6-Worker並列実行
- [ ] 専門化されたWorkerプロンプト
- [ ] 複雑なNectar分解機能
- [ ] Worker間の依存関係管理
- [ ] Queenによる自動進捗チェック機能

### Phase 3: Intelligent Hive (自律的協調システム)
**目標**: 自律的な協調と最適化
**期間**: 5-8週間

#### 高度機能
- [ ] リアルタイムComb同期
- [ ] 自動コンフリクト解決
- [ ] Hiveパフォーマンス分析・最適化
- [ ] Webベース監視ダッシュボード
- [ ] 機械学習による効率改善

## 🛠️ 実装仕様

### Nectar管理システム（タスク管理）

#### Nectarの構造
```json
{
  "nectar_id": "nectar-{timestamp}-{random}",
  "title": "タスクタイトル",
  "description": "詳細な作業内容",
  "assigned_to": "backend_worker",
  "created_by": "queen_worker", 
  "priority": "high|medium|low",
  "status": "pending|active|completed|failed",
  "dependencies": ["nectar-id-1", "nectar-id-2"],
  "expected_honey": [
    "期待される成果物1",
    "期待される成果物2"
  ],
  "estimated_time": 4,
  "created_at": "2025-07-13T10:00:00Z",
  "deadline": "2025-07-14T18:00:00Z"
}
```

#### Hiveワークフロー
1. **Nectar Creation**: Queen が大きなタスクを分解
2. **Nectar Distribution**: 各Workerの専門性に基づいて配布
3. **Worker Processing**: Workerが自律的にNectarを処理
4. **Progress Reports**: 定期的な状況報告
5. **Honey Collection**: 成果物の品質チェックと収集

### Comb通信システム（Worker間通信）

#### Comb Cellメッセージ形式
```json
{
  "from": "backend_worker",
  "to": "frontend_worker", 
  "cell_type": "request|response|notification|error",
  "subject": "API仕様の確認",
  "content": "ユーザー認証APIの仕様を共有します...",
  "attachments": ["api-spec.json"],
  "timestamp": "2025-07-13T10:30:00Z",
  "requires_response": true
}
```

#### 通信パターン
- **Direct Communication**: 特定Worker間での技術相談
- **Queen Broadcast**: Queen から全Workerへの重要情報共有
- **Status Updates**: 進捗・完了報告
- **Emergency Signals**: 問題発生時の緊急通知

## 📁 プロジェクト構造

```
hive/
├── README.md                        # このファイル
├── queen/                          # 中央管理システム
│   ├── coordinator.py              # 全体調整
│   ├── task_distributor.py         # タスク配布
│   ├── status_monitor.py           # 状況監視
│   └── honey_collector.py          # 成果物収集
├── workers/                        # Workerテンプレート・設定
│   ├── prompts/                    # Worker別プロンプト
│   │   ├── queen_worker.md
│   │   ├── architect_worker.md
│   │   ├── frontend_worker.md
│   │   ├── backend_worker.md
│   │   ├── devops_worker.md
│   │   └── tester_worker.md
│   └── configs/                    # Worker設定
├── comb/                           # 通信システム
│   ├── api.py                      # Worker間API
│   ├── file_handler.py             # ファイル操作
│   ├── message_router.py           # メッセージルーティング
│   └── sync_manager.py             # 同期管理
├── scripts/                        # 自動化スクリプト
│   ├── start-hive.sh              # Hive起動
│   ├── wake-workers.sh            # Worker起動
│   ├── distribute-nectar.sh       # タスク配布
│   ├── check-comb.sh              # 通信確認
│   ├── collect-honey.sh           # 成果物収集
│   └── shutdown-hive.sh           # Hive終了
├── tools/                          # ユーティリティ
│   ├── cli/                        # コマンドライン
│   ├── monitor/                    # 監視ツール
│   ├── analyzer.py                 # 分析ツール
│   └── dashboard/                  # Webダッシュボード
├── templates/                      # テンプレート集
│   ├── nectar-templates/           # タスクテンプレート
│   ├── project-templates/          # プロジェクトテンプレート
│   └── honey-formats/              # 成果物フォーマット
├── docs/                           # ドキュメント
│   ├── setup-guide.md             # セットアップガイド
│   ├── worker-roles.md            # Worker役割定義
│   ├── comb-api.md                # 通信API仕様
│   └── troubleshooting.md         # トラブルシューティング
└── examples/                       # 使用例
    ├── web-app-hive/              # Webアプリ開発例
    ├── api-development-hive/       # API開発例
    └── data-analysis-hive/         # データ分析例
```

## 🎬 使用方法

### クイックスタート

```bash
# 1. Hiveのクローンと初期化
git clone <repository-url> hive
cd hive
chmod +x scripts/*.sh

# 2. 小さなHiveの起動
./scripts/start-hive.sh --size=small

# 3. サンプルプロジェクトの実行
./scripts/run-example.sh web-app-hive

# 4. Combの状況確認
./scripts/check-comb.sh

# 5. Honeyの収集
./scripts/collect-honey.sh

# 6. Hiveの終了
./scripts/shutdown-hive.sh
```

### 典型的なワークフロー

1. **Hive初期化**
   ```bash
   ./scripts/init-hive.sh "新しいWebアプリプロジェクト"
   ```

2. **Planning Phase（計画フェーズ）**
   - Queen: 要件整理とNectar分解
   - Architect: 技術選定とシステム設計

3. **Development Phase（開発フェーズ）**
   - Frontend Worker: UI/UX実装
   - Backend Worker: API/データベース開発
   - DevOps Worker: インフラ構築

4. **Quality Assurance Phase（品質保証フェーズ）**  
   - Tester Worker: 品質保証
   - DevOps Worker: 本番デプロイ
   - Queen: 最終確認とHoney収集

## 🔧 カスタマイズ

### 新しいWorkerの追加
```bash
# 1. Workerプロンプトの作成
cp workers/prompts/template.md workers/prompts/ml_engineer_worker.md

# 2. tmux設定の更新  
vim scripts/start-hive.sh

# 3. Queen調整ツールの更新
vim queen/coordinator.py
```

### プロジェクトテンプレートの作成
```bash
# 新しいHiveタイプの追加
mkdir examples/mobile-app-hive
cp -r examples/web-app-hive/* examples/mobile-app-hive/
# カスタマイズ...
```

## 📊 Hive Analytics（分析・監視）

### Hiveパフォーマンス指標
- **Honey Production Rate**: 時間内完了タスクの割合
- **Comb Efficiency**: Worker間通信の有効性
- **Worker Error Rate**: 失敗タスクの発生頻度
- **Honey Quality Score**: 生成された成果物の品質

### 分析ツール
```bash
# 日次Hive活動サマリー
python tools/analyzer.py --report=daily

# Worker別パフォーマンス
python tools/analyzer.py --worker=backend_worker --period=week

# Combボトルネック分析
python tools/analyzer.py --comb-analysis

# Honey品質レポート
python tools/analyzer.py --honey-quality
```

## ⚠️ 注意事項・制限

### コスト管理
- **推奨**: Claude Pro ($20/月) 以上のプラン
- **注意**: 複数Worker並列実行でAPI使用量増加
- **監視**: 定期的な`/clear`実行でトークン使用量管理

### 技術的制限
- tmux環境でのClaude Code動作が前提
- Combファイル競合状態の可能性（同時書き込み）
- ネットワーク不安定時の通信エラー

### セキュリティ
- `--dangerously-skip-permissions`の使用は自己責任
- 重要なHoneyは別途バックアップ推奨
- 外部API呼び出し時の認証情報管理

## 🤝 コントリビューション

### 貢献方法
1. Issueでの問題報告・機能提案
2. Pull Requestでの改善提案
3. ドキュメントの改善
4. 新しいWorkerタイプの追加
5. Hive使用例の共有

### 開発ガイドライン
- Hiveのアナロジーを大切にしたコード
- エラーハンドリングの徹底
- Worker間の協調を重視した設計
- ドキュメントの継続的更新

## 📈 Hiveの進化予定

### 近期目標 (3ヶ月)
- [ ] Web UI Queen Dashboard の開発
- [ ] Docker化による環境構築簡素化
- [ ] Worker学習機能（過去のHoney経験活用）

### 中期目標 (6ヶ月)
- [ ] 他のAIモデル（GPT-4、Gemini）Worker統合
- [ ] リアルタイムComb協調開発機能
- [ ] 自動テスト・デプロイメント機能

### 長期目標 (1年)
- [ ] AIエージェント市場との連携
- [ ] 大規模開発プロジェクトでの実績構築
- [ ] オープンソースHiveコミュニティの形成

## 🐝 コミュニティ・サポート

- **GitHub Issues**: バグ報告・機能要求
- **Discussions**: Hive運用の質問・アイデア共有
- **Discord**: リアルタイム相談 (準備中)
- **Wiki**: Hive運用ベストプラクティス集

---

**🍯 Sweet Development with Hive!**

このシステムはClaude Codeの実験的な使用方法です。Anthropicの利用規約を遵守し、責任を持って美しいHoneyを生み出してください。