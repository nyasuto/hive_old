#!/usr/bin/env python3
"""
Hive Quickstart - Task Management Test
クイックスタートガイド Step 2: タスク管理機能のテスト

使用方法:
  Queen Worker (左pane): python examples/quickstart/02_task_management.py queen
  Developer Worker (右pane): python examples/quickstart/02_task_management.py developer
"""

import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from comb import CombAPI, MessagePriority, MessageType  # noqa: E402


def queen_worker() -> None:
    """Queen Workerのタスク管理テスト"""
    print("👑 Queen Worker: タスク管理機能をテストします")

    # CombAPI初期化
    queen = CombAPI("queen")
    print("✅ Queen Worker CombAPI初期化完了")

    # 新しいタスクを開始
    task_id = queen.start_task(
        "クイックスタート機能テスト",
        task_type="feature",
        description="Hiveの基本機能を確認するテストタスク",
        workers=["queen", "developer"],
    )
    print(f"🚀 タスク開始: {task_id}")

    # タスクの進捗を記録
    queen.add_progress(
        "通信テスト完了", "Queen-Developer間の基本通信が正常に動作することを確認"
    )
    print("📊 進捗を記録しました")

    # 技術的決定を記録
    queen.add_technical_decision(
        "Combシステムでの協調作業採用",
        "ファイルベース通信により確実なメッセージ配信が可能",
        ["直接API通信", "データベース経由", "Redis Pub/Sub"],
    )
    print("🔧 技術決定を記録しました")

    # Developer Workerにタスクを依頼
    success = queen.send_message(
        to_worker="developer",
        content={
            "task_id": task_id,
            "action": "implement_feature",
            "details": "テスト機能の実装を開始してください",
            "requirements": ["進捗報告の実装", "技術決定の記録", "課題があれば報告"],
        },
        message_type=MessageType.REQUEST,
        priority=MessagePriority.MEDIUM,
    )

    if success:
        print("📤 Developer Workerにタスクを依頼しました")
        print("💡 右pane (Developer Worker) でこのスクリプトを実行してください:")
        print("   python examples/quickstart/02_task_management.py developer")
    else:
        print("❌ タスク依頼の送信に失敗しました")


def developer_worker() -> None:
    """Developer Workerのタスク管理テスト"""
    print("💻 Developer Worker: タスク作業を開始します")

    # CombAPI初期化
    dev = CombAPI("developer")
    print("✅ Developer Worker CombAPI初期化完了")

    # Queen Workerからのタスクを確認
    messages = dev.receive_messages()
    print(f"📬 受信メッセージ: {len(messages)}件")

    task_message = None
    for msg in messages:
        if "task_id" in msg.content:
            task_message = msg
            break

    if task_message:
        task_id = task_message.content["task_id"]
        print(f"\n📋 タスク受信: {task_id}")
        print(f"   詳細: {task_message.content['details']}")

        # 作業進捗を報告
        dev.add_progress("環境確認完了", "開発環境とCombシステムの動作確認済み")
        print("📋 進捗を報告しました")

        # 技術的決定を記録
        dev.add_technical_decision(
            "Pythonでの実装継続",
            "既存のCombAPIを活用し、学習コストを最小限に抑制",
            ["JavaScript", "Go", "Rust"],
        )
        print("🔧 技術決定を記録しました")

        # 課題を記録
        dev.add_challenge("初回学習の複雑性", "クイックスタートガイドの改善により解決")
        print("🚧 課題と解決策を記録しました")

        # Queen Workerに完了報告
        success = dev.send_response(
            task_message,
            {
                "status": "completed",
                "result": "テスト機能の実装完了",
                "deliverables": ["進捗報告システム", "技術決定記録", "課題管理機能"],
                "metrics": {
                    "completion_time": "5分",
                    "complexity": "低",
                    "satisfaction": "高",
                },
            },
        )

        if success:
            print("📤 完了報告を送信しました")

        print("\n🎉 タスク管理テスト成功！")
        print("💡 次のステップ:")
        print("   python examples/quickstart/03_check_results.py")
    else:
        print("📭 タスクメッセージがありません")
        print("🔧 Queen Workerでタスクを作成してから実行してください")


def main() -> None:
    """メイン実行関数"""
    if len(sys.argv) != 2:
        print("🐝 Hive Quickstart - Task Management Test")
        print("")
        print("使用方法:")
        print("  Queen Worker (左pane):")
        print("    python examples/quickstart/02_task_management.py queen")
        print("")
        print("  Developer Worker (右pane):")
        print("    python examples/quickstart/02_task_management.py developer")
        print("")
        print("📋 手順:")
        print("  1. 左paneで queen を実行（タスク作成・進捗記録）")
        print("  2. 右paneで developer を実行（タスク実施・完了報告）")
        print("  3. タスク管理機能の動作を確認")
        sys.exit(1)

    worker_type = sys.argv[1].lower()

    if worker_type == "queen":
        queen_worker()
    elif worker_type == "developer":
        developer_worker()
    else:
        print(f"❌ 不正なworker type: {worker_type}")
        print("正しい値: queen または developer")
        sys.exit(1)


if __name__ == "__main__":
    main()
