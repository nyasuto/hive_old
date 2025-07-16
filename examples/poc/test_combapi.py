#!/usr/bin/env python3
"""
CombAPI 動作確認スクリプト

tmux通信システムが正常に動作するかテストする。
"""

import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from comb.api import CombAPI

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_basic_comb_api():
    """基本的なCombAPI動作テスト"""
    print("🔍 Testing basic CombAPI functionality...")

    try:
        # 1. CombAPI インスタンス作成
        test_api = CombAPI("test_worker")
        print(f"✅ CombAPI instance created: {test_api.worker_id}")

        # 2. 現在のタスク取得テスト
        current_task = test_api.get_current_task()
        print(f"📋 Current task: {current_task}")

        # 3. メッセージ送信テスト
        test_message = {
            "type": "test",
            "content": "Hello from test_combapi.py",
            "timestamp": "2025-07-16T17:30:00",
        }

        result = test_api.send_message("test_target", test_message)
        print(f"📤 Message sent result: {result}")

        # 4. メッセージ受信テスト
        received_messages = test_api.receive_messages()
        print(f"📥 Received messages: {received_messages}")

        return True

    except Exception as e:
        print(f"❌ CombAPI test failed: {e}")
        logger.error(f"CombAPI test error: {e}", exc_info=True)
        return False


async def test_work_log_functionality():
    """WorkLog機能動作テスト"""
    print("\n🔍 Testing WorkLog functionality...")

    try:
        # 1. CombAPI インスタンス作成
        test_api = CombAPI("test_worklog_worker")
        print(f"✅ CombAPI instance created: {test_api.worker_id}")

        # 2. タスク開始テスト
        task_id = test_api.start_task(
            task_title="Test Task",
            task_type="test",
            description="Testing WorkLog functionality",
            issue_number=None,
            workers=["test_worklog_worker"],
        )
        print(f"📋 Task started with ID: {task_id}")

        # 3. 進捗追加テスト
        progress_result = test_api.add_progress(
            description="Test progress step", details="Testing progress tracking"
        )
        print(f"📊 Progress added: {progress_result}")

        # 4. 技術的決定記録テスト
        decision_result = test_api.add_technical_decision(
            decision="Use file-based communication",
            reasoning="Simple and reliable for testing",
            alternatives=["TCP sockets", "Message queues"],
        )
        print(f"🎯 Technical decision recorded: {decision_result}")

        # 5. 現在のタスク情報取得
        current_task = test_api.get_current_task()
        print(f"📋 Current task: {current_task}")

        # 6. タスク完了テスト
        completion_result = test_api.complete_task("test_completed")
        print(f"✅ Task completed: {completion_result}")

        return True

    except Exception as e:
        print(f"❌ WorkLog test failed: {e}")
        logger.error(f"WorkLog test error: {e}", exc_info=True)
        return False


async def test_tmux_communication():
    """tmux通信システムテスト"""
    print("\n🔍 Testing tmux communication system...")

    try:
        # 1. Queen APIとDeveloper API作成
        queen_api = CombAPI("test_queen")
        developer_api = CombAPI("test_developer")

        print(f"✅ Queen API created: {queen_api.worker_id}")
        print(f"✅ Developer API created: {developer_api.worker_id}")

        # 2. Queen→Developer メッセージ送信テスト
        queen_message = {
            "type": "task_assignment",
            "task_id": "test_task_002",
            "instructions": "Please execute this test task",
            "priority": "medium",
        }

        send_result = queen_api.send_message("test_developer", queen_message)
        print(f"📤 Queen→Developer message sent: {send_result}")

        # 3. Developer メッセージ受信テスト
        await asyncio.sleep(1)  # 少し待つ
        received_messages = developer_api.receive_messages()
        print(f"📥 Developer received messages: {received_messages}")

        # 4. Developer→Queen 返答テスト
        developer_response = {
            "type": "task_progress",
            "task_id": "test_task_002",
            "status": "received",
            "message": "Task received and processing started",
        }

        response_result = developer_api.send_message("test_queen", developer_response)
        print(f"📤 Developer→Queen response sent: {response_result}")

        # 5. Queen 返答受信テスト
        await asyncio.sleep(1)  # 少し待つ
        queen_received = queen_api.receive_messages()
        print(f"📥 Queen received messages: {queen_received}")

        return True

    except Exception as e:
        print(f"❌ tmux communication test failed: {e}")
        logger.error(f"tmux communication test error: {e}", exc_info=True)
        return False


async def test_tmux_session_status():
    """tmuxセッション状態確認"""
    print("\n🔍 Checking tmux session status...")

    try:
        import subprocess

        # tmuxセッション一覧取得
        result = subprocess.run(
            ["tmux", "list-sessions"], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ tmux is running")
            print(f"📋 Active sessions:\n{result.stdout}")

            # Hive関連セッション確認
            hive_sessions = [
                line for line in result.stdout.split("\n") if "hive" in line.lower()
            ]
            if hive_sessions:
                print(f"🐝 Hive sessions found: {len(hive_sessions)}")
                for session in hive_sessions:
                    print(f"  - {session}")
            else:
                print("⚠️  No Hive sessions found")

        else:
            print("❌ tmux is not running or not accessible")
            print(f"Error: {result.stderr}")

        return result.returncode == 0

    except Exception as e:
        print(f"❌ tmux session check failed: {e}")
        logger.error(f"tmux session check error: {e}", exc_info=True)
        return False


async def main():
    """メイン実行関数"""
    print("🧪 CombAPI 動作確認テスト開始")
    print("=" * 50)

    test_results = {}

    # 1. tmuxセッション状態確認
    test_results["tmux_status"] = await test_tmux_session_status()

    # 2. 基本CombAPI動作テスト
    test_results["basic_comb_api"] = await test_basic_comb_api()

    # 3. WorkLog機能動作テスト
    test_results["work_log_functionality"] = await test_work_log_functionality()

    # 4. tmux通信システムテスト
    test_results["tmux_communication"] = await test_tmux_communication()

    # 結果サマリー
    print("\n" + "=" * 50)
    print("🎯 テスト結果サマリー:")

    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False

    print(
        f"\n🎉 総合結果: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}"
    )

    if not all_passed:
        print("\n💡 次のステップ:")
        print("  1. tmuxが起動していることを確認: tmux list-sessions")
        print("  2. Hiveセッションを起動: ./scripts/start-small-hive.sh")
        print("  3. CombAPI設定を確認: comb/api.py")
        print("  4. Issue解決エージェントを再実行")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
