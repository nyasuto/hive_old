#!/usr/bin/env python3
"""
Claude Daemon Demo

Issue #97 Claude Code永続デーモン統合の動作確認用デモ
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hive.agents_distributed.distributed.claude_daemon import (
    ClaudeCommandBuilder,
    ClaudeDaemon,
)
from hive.agents_distributed.distributed.tmux_manager import TmuxManager


async def main():
    """メイン実行関数"""
    print("🤖 Claude Daemon Demo - Issue #97")
    print("=" * 50)

    # TmuxManagerとClaudeDaemonを初期化
    print("1. Initializing managers...")
    tmux_manager = TmuxManager("hive_claude_demo")
    claude_daemon = ClaudeDaemon(tmux_manager)

    try:
        # tmuxセッションを作成
        print("2. Creating tmux session...")
        success = tmux_manager.create_hive_session()
        if not success:
            print("❌ Failed to create tmux session")
            return

        print("✅ Tmux session created successfully")

        # デーモンを起動
        print("\\n3. Starting Claude daemons...")

        # Queen paneでデーモン起動
        print("  🤖 Starting Claude daemon in Queen pane...")
        success = await claude_daemon.start_daemon("queen")
        if success:
            print("  ✅ Queen daemon started successfully")
        else:
            print("  ❌ Failed to start Queen daemon")
            return

        # Developer1 paneでデーモン起動
        print("  🤖 Starting Claude daemon in Developer1 pane...")
        success = await claude_daemon.start_daemon("developer1")
        if success:
            print("  ✅ Developer1 daemon started successfully")
        else:
            print("  ❌ Failed to start Developer1 daemon")
            return

        # デーモン状態確認
        print("\\n4. Checking daemon status...")
        status = claude_daemon.get_all_daemon_status()
        print(f"  📊 Total daemons: {status['total_daemons']}")
        print(f"  🟢 Running daemons: {status['running_daemons']}")

        # ヘルスチェック
        print("\\n5. Performing health checks...")

        for pane_id in ["queen", "developer1"]:
            health = await claude_daemon.health_check(pane_id)
            status_icon = "✅" if health["healthy"] else "❌"
            print(f"  {status_icon} {pane_id}: {health}")

        # コマンド送信テスト
        print("\\n6. Testing command sending...")

        # Queen paneにコマンド送信
        print("  📤 Sending greeting to Queen...")
        result = await claude_daemon.send_claude_prompt(
            "queen", "Hello! Please respond with a brief greeting."
        )

        if result["success"]:
            print("  ✅ Queen responded successfully")
            print(f"  📝 Response: {result['response'][:100]}...")
        else:
            print(f"  ❌ Queen failed to respond: {result['error']}")

        # Developer1 paneにファイル読み込みコマンド送信
        print("  📤 Sending file read command to Developer1...")
        file_command = ClaudeCommandBuilder.create_file_read_command("README.md")
        result = await claude_daemon.send_command("developer1", file_command)

        if result["success"]:
            print("  ✅ Developer1 responded successfully")
            print(f"  📝 Response: {result['response'][:100]}...")
        else:
            print(f"  ❌ Developer1 failed to respond: {result['error']}")

        # 統計情報表示
        print("\\n7. Daemon statistics...")
        final_status = claude_daemon.get_all_daemon_status()
        print(f"  📊 Total commands sent: {final_status['total_commands']}")
        print(f"  ❌ Total errors: {final_status['total_errors']}")

        for pane_id, daemon_status in final_status["daemons"].items():
            print(
                f"  🤖 {pane_id}: {daemon_status['command_count']} commands, {daemon_status['error_count']} errors"
            )

        print("\\n🎉 Demo completed successfully!")

        # セッション情報表示
        print("\\n📋 Session information:")
        print("  📺 To view the session: tmux attach-session -t hive_claude_demo")
        print("  🛑 To stop daemons: [use stop_claude_daemon.sh or manual exit]")
        print(f"  🔄 To restart demo: python {__file__}")

        # 確認プロンプト
        input("\\nPress Enter to clean up demo session and stop daemons...")

    except Exception as e:
        print(f"❌ Error during demo: {e}")

    finally:
        # クリーンアップ
        print("\\n🧹 Cleaning up...")

        # デーモンを停止
        print("  🛑 Stopping all daemons...")
        stop_results = await claude_daemon.stop_all_daemons()

        for pane_id, success in stop_results.items():
            status_icon = "✅" if success else "❌"
            print(f"  {status_icon} {pane_id} daemon stopped")

        # tmuxセッションを終了
        print("  🔥 Destroying tmux session...")
        tmux_manager.destroy_session()

        print("✅ Demo cleanup completed")


async def interactive_demo():
    """インタラクティブデモモード"""
    print("🤖 Claude Daemon Interactive Demo")
    print("=" * 50)

    tmux_manager = TmuxManager("hive_claude_interactive")
    claude_daemon = ClaudeDaemon(tmux_manager)

    try:
        # セッション作成
        success = tmux_manager.create_hive_session()
        if not success:
            print("❌ Failed to create tmux session")
            return

        # デーモン起動
        success = await claude_daemon.start_daemon("queen")
        if not success:
            print("❌ Failed to start Queen daemon")
            return

        print("✅ Interactive demo ready!")
        print("Commands:")
        print("  'help' - Show available commands")
        print("  'status' - Show daemon status")
        print("  'health' - Check daemon health")
        print("  'quit' - Exit demo")
        print("  Or enter any prompt to send to Claude")

        while True:
            try:
                user_input = input("\\n🤖 > ")

                if user_input.lower() == "quit":
                    break
                elif user_input.lower() == "help":
                    print("Available commands: help, status, health, quit")
                    print("Or enter any text to send as a prompt to Claude")
                elif user_input.lower() == "status":
                    status = claude_daemon.get_all_daemon_status()
                    print(f"Running daemons: {status['running_daemons']}")
                    print(f"Total commands: {status['total_commands']}")
                elif user_input.lower() == "health":
                    health = await claude_daemon.health_check("queen")
                    print(f"Queen health: {health}")
                elif user_input.strip():
                    print("📤 Sending to Queen...")
                    result = await claude_daemon.send_claude_prompt("queen", user_input)

                    if result["success"]:
                        print(f"📝 Response: {result['response']}")
                    else:
                        print(f"❌ Error: {result['error']}")

            except KeyboardInterrupt:
                print("\\n👋 Exiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    finally:
        # クリーンアップ
        print("\\n🧹 Cleaning up...")
        await claude_daemon.stop_all_daemons()
        tmux_manager.destroy_session()
        print("✅ Interactive demo ended")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_demo())
    else:
        asyncio.run(main())
