# 🏗️ Hive 新アーキテクチャ設計書

## 概要

Hiveの新アーキテクチャは、**BeeKeeper-Queen-Worker協調**による分散エージェントシステムです。プロトコル定義システムを基盤として、自然言語指示による自律的なタスク実行を実現します。

## 🎯 設計思想

### 役割分担の明確化
```
Human (BeeKeeper) ←→ AI Queen ←→ AI Worker群
      ↓                ↓            ↓
   自然言語指示      戦略策定      専門実行
   成果物受取        結果統合      並列処理
```

### 従来システムとの違い
| 従来システム | 新アーキテクチャ |
|-------------|-----------------|
| Human → AI Tool | Human → AI Team |
| 人間が管理者 | 人間が依頼者 |
| 逐次処理 | 並列分散処理 |
| 技術的指示 | 自然言語指示 |

## 🏛️ システム構成

### 1. プロトコル定義システム
```
protocols/
├── message_protocol.py      # 統一メッセージ形式
├── protocol_validator.py    # メッセージ検証
└── message_router_integration.py  # 既存システム統合
```

**機能:**
- 統一メッセージ形式（MessageProtocol）
- 厳密なバリデーション（ProtocolValidator）
- バージョン管理・互換性チェック
- レガシーシステム統合

### 2. 分散エージェント基盤
```
hive/agents_distributed/
├── distributed.py           # 分散エージェント管理
├── tmux_manager.py         # tmux統合
└── claude_daemon.py        # 永続デーモン
```

**機能:**
- tmux統合による分散実行環境
- Claude永続デーモンによる長時間実行
- セッション管理・自動復旧
- Worker-paneマッピング

### 3. Issue解決エージェント
```
examples/poc/
├── issue_solver_agent.py   # メインエージェント
├── demo_issue_solver.py    # デモ実行
└── README_issue_solver.md  # ドキュメント
```

**機能:**
- 自然言語プロンプト解析
- GitHub Issue自動分析
- 優先度・複雑度判定
- 解決戦略策定・実行

## 🔄 メッセージフロー

### 1. プロトコルメッセージ
```python
# BeeKeeper → Queen
beekeeper_request = protocol.create_message(
    message_type=MessageType.REQUEST,
    sender_id="beekeeper",
    receiver_id="queen",
    content={
        "instruction": "Issue 64を解決してください",
        "priority": "high"
    }
)

# Queen → Workers (分散)
task_assignments = [
    protocol.create_task_assignment(
        sender_id="queen",
        receiver_id="worker-developer",
        task_type="implementation",
        task_data={"issue_id": 64}
    ),
    protocol.create_task_assignment(
        sender_id="queen",
        receiver_id="worker-tester", 
        task_type="testing",
        task_data={"issue_id": 64}
    )
]
```

### 2. 分散処理フロー
```
1. BeeKeeper指示 → Queen受信
2. Queen戦略策定 → タスク分散
3. Worker並列実行 → 進捗報告
4. Queen結果統合 → 品質チェック
5. 最終成果物 → BeeKeeper受取
```

## 🐝 エージェント設計

### BeeKeeper (Human)
- **役割**: 自然言語による指示・成果物受け取り
- **インターフェース**: CLI、自然言語プロンプト
- **責任範囲**: 要求明確化、最終確認

### Queen (AI Coordinator)
- **役割**: 戦略策定・タスク分散・結果統合
- **機能**: 
  - 自然言語プロンプト解析
  - 複雑度・優先度判定
  - Worker選択・タスク分散
  - 進捗監視・結果統合
- **通信**: プロトコルメッセージ

### Worker群 (AI Specialists)
- **役割**: 専門的な並列実行
- **種類**:
  - Developer Worker: 実装・開発
  - Tester Worker: テスト・品質保証
  - Analyzer Worker: 分析・調査
  - Documenter Worker: ドキュメント作成
- **通信**: プロトコルメッセージ

## 🔧 技術基盤

### tmux統合
```bash
# セッション構成例
┌─────────────────┬─────────────────┐
│   BeeKeeper     │     Queen       │
│   (Human)       │  (Coordinator)  │
├─────────────────┼─────────────────┤
│   Worker-1      │   Worker-2      │
│  (Developer)    │  (Analyzer)     │
├─────────────────┼─────────────────┤
│   Worker-3      │   Worker-4      │
│  (Tester)       │  (Documenter)   │
└─────────────────┴─────────────────┘
```

### Claude永続デーモン
- **長時間実行**: 複雑なタスクの継続処理
- **自動復旧**: 障害発生時の自動回復
- **状態管理**: 進捗・状態の永続化
- **監視機能**: ヘルスチェック・アラート

### プロトコル統合
- **メッセージ標準化**: 全エージェント間統一形式
- **バージョン管理**: 互換性保証
- **バリデーション**: 厳密な検証
- **ルーティング**: 適切な配信

## 🚀 実装例

### 自然言語Issue解決
```python
# 自然言語プロンプト
user_input = "Issue 64を解決してください"

# BeeKeeper → Queen
beekeeper = IssueSolverBeeKeeper()
result = await beekeeper.process_user_request(user_input)

# 期待される実行フロー
# 1. 自然言語解析
# 2. Issue詳細分析
# 3. 解決戦略策定
# 4. Worker分散実行
# 5. 結果統合・品質チェック
# 6. PR作成・成果物提供
```

### 分散エージェント管理
```python
# tmux管理システム
tmux_manager = TmuxManager()
await tmux_manager.start_agent_session("queen-coordinator", "queen")
await tmux_manager.start_agent_session("worker-developer", "developer")

# Claude永続デーモン
daemon = ClaudeDaemon("issue-solver")
await daemon.start_daemon()
health = await daemon.health_check()
```

## 📊 品質保証

### テスト体制
- **プロトコルテスト**: 79テスト実行
- **統合テスト**: エージェント間通信検証
- **品質チェック**: make quality実行
- **型チェック**: mypy静的解析

### 監視・運用
- **リアルタイム監視**: 進捗・状態把握
- **自動復旧**: 障害時の自動回復
- **ログ管理**: 作業履歴・学習基盤
- **メトリクス**: 性能・効率測定

## 🔮 拡張性

### 水平スケーリング
- Worker数の動的増減
- 負荷分散・リソース最適化
- 専門性に応じた動的配布

### 垂直スケーリング
- 複雑なタスクの分解
- 深い専門性の実現
- 学習・改善の継続

この新アーキテクチャにより、人間は管理者ではなく依頼者として、本来の創造的な仕事に集中できるようになります。