#!/usr/bin/env python3
"""
Tmux Manager Demo

Issue #96 tmux統合基盤システムの動作確認用デモ
"""

import sys
import time
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hive.agents_distributed.distributed.tmux_manager import PaneMessenger, TmuxManager


def main():
    """メイン実行関数"""
    print("🐝 Tmux Manager Demo - Issue #96")
    print("=" * 50)

    # TmuxManagerを初期化
    tmux_manager = TmuxManager("hive_demo")

    try:
        print("1. Creating tmux session...")
        success = tmux_manager.create_hive_session()
        if not success:
            print("❌ Failed to create session")
            return

        print("✅ Session created successfully")

        print("\\n2. Checking session status...")
        status = tmux_manager.get_session_status()
        print(f"Session: {status['session_name']}")
        print(f"Exists: {status['exists']}")
        print(f"Panes: {list(status['panes'].keys())}")

        print("\\n3. Testing pane communication...")
        messenger = PaneMessenger(tmux_manager)

        # BeeKeeper → Queen メッセージ送信
        print("  📤 Sending message from BeeKeeper to Queen...")
        success = messenger.send_task_message(
            "beekeeper",
            "queen",
            "demo_task_001",
            {"action": "process_request", "data": "Hello from BeeKeeper!"},
        )

        if success:
            print("  ✅ Message sent successfully")
        else:
            print("  ❌ Message failed")

        time.sleep(2)

        # Queen → BeeKeeper 応答送信
        print("  📤 Sending response from Queen to BeeKeeper...")
        success = messenger.send_response_message(
            "queen",
            "beekeeper",
            "demo_task_001",
            {"status": "completed", "result": "Task processed successfully"},
        )

        if success:
            print("  ✅ Response sent successfully")
        else:
            print("  ❌ Response failed")

        print("\\n4. Testing heartbeat...")
        success = messenger.send_heartbeat("beekeeper", "queen")
        if success:
            print("  ✅ Heartbeat sent successfully")
        else:
            print("  ❌ Heartbeat failed")

        print("\\n5. Getting pane content...")
        content = tmux_manager.get_pane_content("queen", 5)
        if content:
            print("  📄 Queen pane content (last 5 lines):")
            print(f"  {content}")
        else:
            print("  ⚠️  Could not retrieve pane content")

        print("\\n🎉 Demo completed successfully!")
        print("\\n📋 To view the session:")
        print("  tmux attach-session -t hive_demo")
        print("\\n🛑 To stop the demo session:")
        print("  tmux kill-session -t hive_demo")

        # 確認プロンプト
        input("\\nPress Enter to clean up the demo session...")

    except Exception as e:
        print(f"❌ Error during demo: {e}")

    finally:
        # クリーンアップ
        print("\\n🧹 Cleaning up...")
        tmux_manager.destroy_session()
        print("✅ Demo session cleaned up")


if __name__ == "__main__":
    main()
