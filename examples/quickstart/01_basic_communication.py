#!/usr/bin/env python3
"""
Hive Quickstart - Basic Communication Test
クイックスタートガイド Step 1: Worker間の通信テスト

使用方法:
  Queen Worker (左pane): python examples/quickstart/01_basic_communication.py queen
  Developer Worker (右pane): python examples/quickstart/01_basic_communication.py developer
"""

import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from comb import CombAPI, MessagePriority, MessageType  # noqa: E402


def queen_worker() -> None:
    """Queen Workerの通信テスト"""
    print("👑 Queen Worker: 通信テストを開始します")

    # CombAPI初期化
    queen = CombAPI("queen")
    print("✅ Queen Worker CombAPI初期化完了")

    # Developer Workerにメッセージを送信
    success = queen.send_message(
        to_worker="developer",
        content={
            "task": "Hello from Queen!",
            "message": "基本通信テストです",
        },
        priority=MessagePriority.LOW,
        message_type=MessageType.REQUEST,
    )

    if success:
        print("📤 メッセージを送信しました")
        print("💡 次に右pane (Developer Worker) でこのスクリプトを実行してください:")
        print("   python examples/quickstart/01_basic_communication.py developer")
    else:
        print("❌ メッセージ送信に失敗しました")
        print("🔧 トラブルシューティング:")
        print("   - Hiveが起動していることを確認: ./scripts/check-comb.sh")
        print("   - ディレクトリ構造を確認: ls -la .hive/")


def developer_worker() -> None:
    """Developer Workerの通信テスト"""
    print("💻 Developer Worker: メッセージ受信テストを開始します")

    # CombAPI初期化
    dev = CombAPI("developer")
    print("✅ Developer Worker CombAPI初期化完了")

    # Queen Workerからのメッセージを受信
    messages = dev.receive_messages()
    print(f"📬 受信メッセージ: {len(messages)}件")

    if messages:
        for i, msg in enumerate(messages, 1):
            print(f"\n📝 メッセージ {i}:")
            print(f"   送信者: {msg.from_worker}")
            print(f"   タイプ: {msg.message_type.value}")
            print(f"   優先度: {msg.priority.name}")
            print(f"   内容: {msg.content}")

        print("\n🎉 通信テスト成功！")
        print("💡 次のステップ:")
        print("   python examples/quickstart/02_task_management.py")
    else:
        print("📭 メッセージがありません")
        print("🔧 トラブルシューティング:")
        print("   - Queen Workerでメッセージを送信しましたか？")
        print("   - しばらく待ってから再実行してみてください")


def main() -> None:
    """メイン実行関数"""
    if len(sys.argv) != 2:
        print("🐝 Hive Quickstart - Basic Communication Test")
        print("")
        print("使用方法:")
        print("  Queen Worker (左pane):")
        print("    python examples/quickstart/01_basic_communication.py queen")
        print("")
        print("  Developer Worker (右pane):")
        print("    python examples/quickstart/01_basic_communication.py developer")
        print("")
        print("📋 手順:")
        print("  1. 左paneで queen を実行")
        print("  2. 右paneで developer を実行")
        print("  3. メッセージのやり取りを確認")
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
