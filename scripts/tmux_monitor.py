#!/usr/bin/env python3
"""
TMux Monitor - Hive Watch Phase 1

tmux セッション内のWorker pane内容を監視・キャプチャする基本システム
Issue #125 - Phase 1: Hive Watch基本監視機能実装
"""

import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))


class TMuxMonitor:
    """tmux セッションの監視とpaneコンテンツ取得"""

    def __init__(self, session_name: str = "cozy-hive"):
        self.session_name = session_name
        self.workers = [
            "beekeeper",
            "queen",
            "analyzer",
            "documenter",
            "developer",
            "tester",
            "reviewer",
        ]
        self.last_content: dict[str, str] = {}

    def check_session_exists(self) -> bool:
        """tmuxセッションの存在確認"""
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", self.session_name],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False

    def get_pane_list(self) -> list[str]:
        """セッション内のpane一覧を取得"""
        if not self.check_session_exists():
            return []

        try:
            result = subprocess.run(
                ["tmux", "list-panes", "-t", self.session_name, "-F", "#{pane_title}"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return [
                    line.strip() for line in result.stdout.split("\n") if line.strip()
                ]
            return []
        except subprocess.SubprocessError:
            return []

    def capture_pane_content(self, worker: str, lines: int = 20) -> str | None:
        """指定Workerのpaneコンテンツを取得"""
        if not self.check_session_exists():
            return None

        try:
            result = subprocess.run(
                [
                    "tmux",
                    "capture-pane",
                    "-t",
                    f"{self.session_name}:{worker}",
                    "-p",
                    "-S",
                    f"-{lines}",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return result.stdout
            return None
        except subprocess.SubprocessError:
            return None

    def get_all_pane_contents(self, lines: int = 20) -> dict[str, str]:
        """全Workerのpaneコンテンツを取得"""
        contents = {}

        for worker in self.workers:
            content = self.capture_pane_content(worker, lines)
            if content:
                contents[worker] = content

        return contents

    def get_pane_changes(self, lines: int = 20) -> dict[str, str]:
        """前回取得時からの変更があったpaneのみを取得"""
        current_contents = self.get_all_pane_contents(lines)
        changes = {}

        for worker, content in current_contents.items():
            if worker not in self.last_content or self.last_content[worker] != content:
                changes[worker] = content
                self.last_content[worker] = content

        return changes

    async def monitor_all_workers(self, interval: float = 2.0) -> None:
        """全Worker paneの継続的監視"""
        print(f"🔍 Starting tmux monitoring for session: {self.session_name}")
        print(f"👥 Monitoring workers: {', '.join(self.workers)}")
        print(f"⏱️  Check interval: {interval} seconds")

        if not self.check_session_exists():
            print(f"❌ Session '{self.session_name}' not found!")
            return

        while True:
            try:
                changes = self.get_pane_changes()

                if changes:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"\n📊 [{timestamp}] Content changes detected:")

                    for worker, content in changes.items():
                        print(f"  🤖 {worker}: {len(content.split())} words")
                        # 最新の数行のみ表示
                        lines = content.strip().split("\n")
                        recent_lines = lines[-3:] if len(lines) > 3 else lines
                        for line in recent_lines:
                            if line.strip():
                                print(f"    {line[:80]}...")

                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"⚠️  Error during monitoring: {e}")
                await asyncio.sleep(interval)


class TMuxSessionInfo:
    """tmuxセッション情報の取得"""

    def __init__(self, session_name: str = "cozy-hive"):
        self.session_name = session_name

    def get_session_status(self) -> dict[str, any]:
        """セッション状態の詳細取得"""
        try:
            # セッション存在確認
            has_session = (
                subprocess.run(
                    ["tmux", "has-session", "-t", self.session_name],
                    capture_output=True,
                ).returncode
                == 0
            )

            if not has_session:
                return {
                    "session_name": self.session_name,
                    "exists": False,
                    "panes": {},
                    "windows": [],
                }

            # pane情報取得
            panes_result = subprocess.run(
                [
                    "tmux",
                    "list-panes",
                    "-t",
                    self.session_name,
                    "-F",
                    "#{pane_title}:#{pane_id}:#{pane_current_command}",
                ],
                capture_output=True,
                text=True,
            )

            panes = {}
            if panes_result.returncode == 0:
                for line in panes_result.stdout.split("\n"):
                    if line.strip():
                        parts = line.split(":")
                        if len(parts) >= 3:
                            pane_title = parts[0]
                            pane_id = parts[1]
                            command = ":".join(parts[2:])
                            panes[pane_title] = {"id": pane_id, "command": command}

            return {
                "session_name": self.session_name,
                "exists": True,
                "panes": panes,
                "pane_count": len(panes),
            }

        except subprocess.SubprocessError as e:
            return {
                "session_name": self.session_name,
                "exists": False,
                "error": str(e),
                "panes": {},
            }


async def main():
    """デモ実行"""
    print("🔍 TMux Monitor - Hive Watch Phase 1")
    print("=" * 50)

    monitor = TMuxMonitor()
    session_info = TMuxSessionInfo()

    # セッション状態確認
    status = session_info.get_session_status()
    print(f"📊 Session Status: {status['session_name']}")
    print(f"   Exists: {status['exists']}")

    if status["exists"]:
        print(f"   Panes: {status['pane_count']}")
        for pane_name, info in status["panes"].items():
            print(f"     🤖 {pane_name}: {info['command']}")

    if not status["exists"]:
        print("❌ Session not found. Please start the hive session first:")
        print("   ./scripts/start-cozy-hive.sh")
        return

    print("\n🚀 Starting monitoring...")
    print("Press Ctrl+C to stop")

    try:
        await monitor.monitor_all_workers(interval=2.0)
    except KeyboardInterrupt:
        print("\n✅ Monitoring stopped")


if __name__ == "__main__":
    asyncio.run(main())
