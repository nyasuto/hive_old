#!/usr/bin/env python3
"""
Hive CLI - 透過的な通信監視機能付きCLI
Issue #125 - 特殊処理ラッパーとしての自作CLI実装

tmux通信の複雑な処理（sleep、改行確認等）を透過的にラップし、
同時に通信監視とログ機能を提供する統合CLI
"""

import argparse
import asyncio
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# 循環importを避けるため、HiveWatchCommunicatorを動的にimport
import importlib.util
import sys
from pathlib import Path

from scripts.worker_communication import WorkerCommunicationError


def _get_hive_watch_communicator() -> Any:
    """HiveWatchCommunicatorを動的にimportして取得"""
    spec = importlib.util.spec_from_file_location(
        "hive_watch_module", Path(__file__).parent / "hive_watch.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("Failed to load hive_watch module")
    hive_watch_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hive_watch_module)
    return hive_watch_module.HiveWatchCommunicator


class HiveCLI:
    """Hive統合CLIツール"""

    def __init__(self, session_name: str = "cozy-hive"):
        self.session_name = session_name
        HiveWatchCommunicator = _get_hive_watch_communicator()
        self.communicator = HiveWatchCommunicator(session_name)
        self.cli_version = "1.0.0-alpha"
        
        # Worker名一覧を初期化
        self.known_workers = {
            "queen", "developer", "tester", "analyzer", 
            "documenter", "reviewer", "beekeeper"
        }

    async def send_message(
        self,
        worker: str,
        message: str,
        message_type: str = "direct",
        wait_for_response: bool = True,
    ) -> dict[str, Any]:
        """
        メッセージ送信の透過的ラッパー

        複雑な送信処理（sleep、改行確認等）をラップし、
        監視機能を付加した統一インターフェース
        """
        # 送信前処理
        task_id = str(uuid4())[:8]

        # 実際の送信者を特定してログ記録
        actual_source, actual_target = self._parse_worker_communication(message)
        
        self.communicator.logger.log_message(
            source=actual_source or "hive_cli",
            target=actual_target or worker,
            message=f"CLI_MESSAGE: {message}",
            message_type=message_type,
            additional_info={
                "task_id": task_id,
                "wait_for_response": wait_for_response,
                "cli_version": self.cli_version,
                "original_source": "hive_cli",
                "original_target": worker,
            },
        )

        try:
            if message_type == "direct":
                # 直接メッセージ送信（現在のsleep+改行処理をラップ）
                result = await self._send_direct_message(worker, message, task_id)
            elif message_type == "task":
                # タスク形式での送信
                task = {
                    "task_id": task_id,
                    "instruction": message,
                    "task_type": "cli_task",
                }
                result = await self.communicator.send_task_to_worker(worker, task)
            else:
                raise ValueError(f"Unknown message type: {message_type}")

            # 成功ログ（実際の送信者を記録）
            actual_source, actual_target = self._parse_worker_communication(message)
            
            self.communicator.logger.log_message(
                source=actual_target or worker,
                target=actual_source or "hive_cli",
                message="CLI_RESPONSE: Success",
                message_type="response",
                additional_info={
                    "task_id": task_id,
                    "processing_time": result.get("processing_time", 0),
                    "original_source": worker,
                    "original_target": "hive_cli",
                },
            )

            return result

        except Exception as e:
            # エラーログ（実際の送信者を記録）
            actual_source, actual_target = self._parse_worker_communication(message)
            
            self.communicator.logger.log_message(
                source=actual_target or worker,
                target=actual_source or "hive_cli",
                message=f"CLI_ERROR: {str(e)}",
                message_type="error",
                additional_info={
                    "task_id": task_id, 
                    "error": str(e),
                    "original_source": worker,
                    "original_target": "hive_cli",
                },
            )
            raise

    def _parse_worker_communication(self, message: str) -> tuple[str | None, str | None]:
        """
        メッセージ内容から実際のWorker間通信を特定
        
        Returns:
            tuple[source, target]: 実際の送信者と宛先。特定できない場合はNone
        """
        # TASK: パターンを特定してWorker間通信を記録
        # 例: "TASK:001:Issue #84のバグを修正してください"
        if message.startswith("TASK:"):
            # 通常はqueenからの指示と推定
            return "queen", None
        
        # WORKER_RESULT: パターンを特定してWorkerからの結果を記録
        # 例: "WORKER_RESULT:developer:TASK_001:[修正完了...]"
        if message.startswith("WORKER_RESULT:"):
            parts = message.split(":", 3)
            if len(parts) >= 3:
                worker_name = parts[1]
                if worker_name in self.known_workers:
                    return worker_name, "queen"  # 通常はqueenに報告
        
        # COLLABORATION: パターンを特定してWorker間の協力を記録
        # 例: "COLLABORATE:001:Testerと連携して..."
        if message.startswith("COLLABORATE:"):
            return "queen", None  # 通常はqueenからの協力指示
        
        # QUEEN_FINAL_REPORT: パターンを特定してQueenからの最終報告を記録
        if message.startswith("QUEEN_FINAL_REPORT:"):
            return "queen", "beekeeper"
        
        # APPROVAL: パターンを特定してWorkerからの承認を記録
        # 例: "APPROVAL:reviewer:TASK_002:..."
        if message.startswith("APPROVAL:"):
            parts = message.split(":", 3)
            if len(parts) >= 3:
                worker_name = parts[1]
                if worker_name in self.known_workers:
                    return worker_name, "queen"  # 通常はqueenに報告
        
        # 特定できない場合はNoneを返す
        return None, None

    async def _send_direct_message(
        self, worker: str, message: str, task_id: str
    ) -> dict[str, Any]:
        """
        直接メッセージ送信の内部実装

        worker_config.yamlのdelivery_method設定に基づいて送信方式を選択：
        - echo: echo方式（コンソール表示）
        - claude_interactive: Claude Code方式（対話型）
        """
        if not self.communicator.check_worker_pane(worker):
            raise WorkerCommunicationError(f"Worker pane '{worker}' not found")

        worker_config = self.communicator.config["workers"][worker]
        pane_name = worker_config["tmux_pane"]
        delivery_method = worker_config.get("delivery_method", "claude_interactive")
        start_time = time.time()

        if delivery_method == "echo":
            # echo方式（コンソール表示）
            return await self._send_to_console(
                pane_name, worker, message, task_id, start_time
            )
        else:
            # Claude Code方式（対話型通信）
            return await self._send_to_claude_worker(
                pane_name, worker, message, task_id, start_time
            )

    async def _send_to_console(
        self, pane_name: str, worker: str, message: str, task_id: str, start_time: float
    ) -> dict[str, Any]:
        """コンソールペインへのecho方式送信"""
        print(f"📤 Sending to {worker} (echo): {message[:50]}...")

        # timestamp付きメッセージとしてecho
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] 📨 {message}"

        subprocess.run(
            [
                "tmux",
                "send-keys",
                "-t",
                pane_name,
                f"echo '{formatted_message}'",
                "Enter",
            ],
            check=True,
        )

        processing_time = time.time() - start_time

        return {
            "task_id": task_id,
            "worker_name": worker,
            "status": "completed",
            "result": {
                "content": f"Message displayed on {worker} console: {message}",
                "processing_time": processing_time,
                "message_sent": message,
                "delivery_method": "echo",
            },
            "timestamp": datetime.now().isoformat(),
        }

    async def _send_to_claude_worker(
        self, pane_name: str, worker: str, message: str, task_id: str, start_time: float
    ) -> dict[str, Any]:
        """Claude Codeワーカーへの対話型送信"""
        # Step 1: メッセージ送信 + Enter
        print(f"📤 Sending to {worker}: {message[:50]}...")
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_name, message, "Enter"], check=True
        )

        # Step 2: 処理時間確保（1秒待機）
        await asyncio.sleep(1)

        # Step 3: 確認用Enter送信
        subprocess.run(["tmux", "send-keys", "-t", pane_name, "Enter"], check=True)

        # Step 4: レスポンス待機（オプション）
        response_content = ""
        if True:  # wait_for_responseがTrueの場合
            timeout = 30  # 簡単なメッセージなので短いタイムアウト
            response_content = await self._wait_for_simple_response(pane_name, timeout)

        processing_time = time.time() - start_time

        return {
            "task_id": task_id,
            "worker_name": worker,
            "status": "completed",
            "result": {
                "content": response_content,
                "processing_time": processing_time,
                "message_sent": message,
                "delivery_method": "claude_interactive",
            },
            "timestamp": datetime.now().isoformat(),
        }

    async def _wait_for_simple_response(self, pane_name: str, timeout: int) -> str:
        """シンプルなレスポンス待機（[TASK_COMPLETED]は期待しない）"""
        start_time = time.time()
        initial_content = ""

        # 初期コンテンツを取得
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", pane_name, "-p"],
                capture_output=True,
                text=True,
                check=True,
            )
            initial_content = result.stdout
        except subprocess.SubprocessError:
            pass

        # 変化を待機
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    ["tmux", "capture-pane", "-t", pane_name, "-p"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                current_content = result.stdout

                # コンテンツが変化したら応答とみなす
                if current_content != initial_content:
                    # 新しい部分を抽出
                    new_lines = current_content.split("\n")
                    initial_lines = initial_content.split("\n")

                    # 差分を取得
                    if len(new_lines) > len(initial_lines):
                        response_lines = new_lines[len(initial_lines) :]
                        return "\n".join(response_lines).strip()
                    else:
                        return current_content.strip()

                await asyncio.sleep(0.5)

            except subprocess.SubprocessError:
                await asyncio.sleep(0.5)

        return "Response timeout"

    async def list_workers(self) -> dict[str, Any]:
        """Worker一覧と状態を取得"""
        status: dict[str, Any] = self.communicator.monitor_worker_status()
        return status

    async def get_worker_history(self, worker: str, lines: int = 20) -> str:
        """Worker履歴を取得"""
        if not self.communicator.check_worker_pane(worker):
            return f"Worker '{worker}' not found"

        pane_name = self.communicator.config["workers"][worker]["tmux_pane"]

        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", pane_name, "-p", "-S", f"-{lines}"],
                capture_output=True,
                text=True,
                check=True,
            )

            return result.stdout
        except subprocess.SubprocessError as e:
            return f"Error capturing history: {e}"

    def show_status(self) -> None:
        """現在の状態を表示"""
        print(f"🐝 Hive CLI v{self.cli_version}")
        print(f"📊 Session: {self.session_name}")
        print("=" * 50)

        # セッション状態
        status = self.communicator.monitor_worker_status()
        if status.get("session_active", False):
            print("✅ Hive session is active")
            workers = status.get("workers", {})
            active_count = sum(
                1 for w in workers.values() if w.get("pane_active", False)
            )
            print(f"👥 Workers: {active_count}/{len(workers)} active")

            for worker_name, worker_info in workers.items():
                status_icon = "🟢" if worker_info.get("pane_active", False) else "🔴"
                print(f"   {status_icon} {worker_name}")
        else:
            print("❌ Hive session not active")
            print("💡 Start with: ./scripts/start-cozy-hive.sh")

        # アクティブタスク
        active_tasks = self.communicator.get_active_tasks_status()
        if active_tasks:
            print(f"🔄 Active tasks: {len(active_tasks)}")
            for task_id, task_info in active_tasks.items():
                elapsed = int(task_info["elapsed_time"])
                worker = task_info["worker_name"]
                print(f"   ⏱️  {task_id} ({elapsed}s) → {worker}")


async def main() -> None:
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="Hive CLI - 透過的通信監視機能付きCLI")
    parser.add_argument("--session", default="cozy-hive", help="tmuxセッション名")

    subparsers = parser.add_subparsers(dest="command", help="利用可能なコマンド")

    # send コマンド
    send_parser = subparsers.add_parser("send", help="Workerにメッセージ送信")
    send_parser.add_argument("worker", help="送信先Worker名")
    send_parser.add_argument("message", help="送信するメッセージ")
    send_parser.add_argument(
        "--type", choices=["direct", "task"], default="direct", help="メッセージタイプ"
    )
    send_parser.add_argument("--no-wait", action="store_true", help="応答を待機しない")

    # list コマンド
    subparsers.add_parser("list", help="Worker一覧表示")

    # history コマンド
    history_parser = subparsers.add_parser("history", help="Worker履歴表示")
    history_parser.add_argument("worker", help="Worker名")
    history_parser.add_argument("--lines", type=int, default=20, help="表示行数")

    # status コマンド
    subparsers.add_parser("status", help="現在の状態表示")

    # monitor コマンド
    monitor_parser = subparsers.add_parser("monitor", help="リアルタイム監視開始")
    monitor_parser.add_argument(
        "--interval", type=float, default=2.0, help="監視間隔（秒）"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = HiveCLI(args.session)

    try:
        if args.command == "send":
            wait_for_response = not args.no_wait
            result = await cli.send_message(
                args.worker, args.message, args.type, wait_for_response
            )
            print("✅ Message sent successfully")
            if result.get("result", {}).get("content"):
                print(f"📝 Response: {result['result']['content']}")

        elif args.command == "list":
            status = await cli.list_workers()
            print("👥 Worker Status:")
            if status.get("session_active", False):
                for worker_name, worker_info in status.get("workers", {}).items():
                    status_icon = (
                        "🟢" if worker_info.get("pane_active", False) else "🔴"
                    )
                    print(f"  {status_icon} {worker_name}")
            else:
                print("  ❌ Session not active")

        elif args.command == "history":
            history = await cli.get_worker_history(args.worker, args.lines)
            print(f"📄 {args.worker} History (last {args.lines} lines):")
            print("=" * 50)
            print(history)

        elif args.command == "status":
            cli.show_status()

        elif args.command == "monitor":
            # 循環importを避けるため、動的import
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "hive_watch", Path(__file__).parent / "hive_watch.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError("Failed to load hive_watch module")
            hive_watch_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(hive_watch_module)

            hive_watch = hive_watch_module.HiveWatch(args.session)
            await hive_watch.start_monitoring(args.interval)

    except WorkerCommunicationError as e:
        print(f"❌ Communication error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
