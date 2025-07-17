#!/usr/bin/env python3
"""
Hive Watch - リアルタイム通信監視システム
Issue #125 - Phase 1: 基本監視機能実装

自作CLI経由の透過的な通信監視により、Worker間の通信を可視化・ログ記録する
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.worker_communication import WorkerCommunicator


class CommunicationLogger:
    """通信メッセージのログ記録"""

    def __init__(self, log_file: str = "logs/hive_communications.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def log_message(
        self,
        source: str,
        target: str,
        message: str,
        message_type: str = "task",
        additional_info: dict[str, Any] | None = None,
    ) -> None:
        """通信メッセージをログに記録"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "source": source,
            "target": target,
            "message_type": message_type,
            "message": message,
            "additional_info": additional_info or {},
        }

        # ログファイルに追記
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        # コンソールにも出力
        time_str = datetime.now().strftime("%H:%M:%S")
        arrow = "→" if message_type == "task" else "←"
        print(f"{time_str} | {source} {arrow} {target} | {message[:100]}...")

    def log_worker_result(
        self, worker_name: str, task_id: str, result: dict[str, Any]
    ) -> None:
        """Worker実行結果をログに記録"""
        self.log_message(
            source=worker_name,
            target="queen",
            message=f"WORKER_RESULT:{worker_name}:{task_id}",
            message_type="result",
            additional_info={
                "task_id": task_id,
                "processing_time": result.get("processing_time", 0),
                "status": result.get("status", "unknown"),
            },
        )


class MessageParser:
    """通信メッセージの解析"""

    def __init__(self) -> None:
        self.patterns = {
            "task_assignment": r"TASK_(\w+)_(\w+):",
            "worker_result": r"WORKER_RESULT:(\w+):(\w+):",
            "queen_report": r"QUEEN_FINAL_REPORT:(\w+):",
            "heartbeat": r"HEARTBEAT:(\w+)",
            "status_update": r"STATUS_UPDATE:(\w+):(\w+)",
        }

    def parse_message(self, content: str) -> dict[str, Any]:
        """メッセージを解析してタイプと内容を特定"""
        import re

        for pattern_name, pattern in self.patterns.items():
            match = re.search(pattern, content)
            if match:
                return {
                    "type": pattern_name,
                    "groups": match.groups(),
                    "full_match": match.group(0),
                    "content": content,
                }

        return {"type": "unknown", "groups": [], "full_match": "", "content": content}


class HiveWatchCommunicator(WorkerCommunicator):
    """通信監視機能を追加したWorkerCommunicator"""

    def __init__(self, session_name: str = "cozy-hive"):
        super().__init__(session_name)
        self.logger = CommunicationLogger()
        self.parser = MessageParser()
        self.active_tasks: dict[str, dict[str, Any]] = {}

    async def send_task_to_worker(
        self, worker_name: str, task: dict[str, Any]
    ) -> dict[str, Any]:
        """監視機能付きでタスクをWorkerに送信"""
        # タスク送信前のログ記録
        task_id = task.get("task_id", "unknown")
        instruction = task.get("instruction", "")

        self.logger.log_message(
            source="beekeeper",
            target=worker_name,
            message=f"TASK_{task_id}: {instruction}",
            message_type="task",
            additional_info={"task_id": task_id, "worker_name": worker_name},
        )

        # アクティブタスクに追加
        self.active_tasks[task_id] = {
            "worker_name": worker_name,
            "start_time": time.time(),
            "task": task,
        }

        try:
            # 実際のタスク実行
            result = await super().send_task_to_worker(worker_name, task)

            # タスク完了のログ記録
            self.logger.log_worker_result(worker_name, task_id, result)

            # アクティブタスクから削除
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

            return result

        except Exception as e:
            # エラーログ記録
            self.logger.log_message(
                source=worker_name,
                target="beekeeper",
                message=f"ERROR: {str(e)}",
                message_type="error",
                additional_info={"task_id": task_id, "error": str(e)},
            )

            # アクティブタスクから削除
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

            raise

    async def send_parallel_tasks(
        self, tasks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """並列タスクの監視機能付き実行"""
        # 並列タスク開始をログ記録
        task_ids = [task.get("task_id", "unknown") for task in tasks]
        worker_names = [task.get("worker_name", "unknown") for task in tasks]

        self.logger.log_message(
            source="beekeeper",
            target="multiple_workers",
            message=f"PARALLEL_TASKS: {len(tasks)} tasks to {', '.join(set(worker_names))}",
            message_type="parallel_start",
            additional_info={
                "task_ids": task_ids,
                "worker_count": len(set(worker_names)),
            },
        )

        # 実際の並列実行
        results = await super().send_parallel_tasks(tasks)

        # 並列タスク完了をログ記録
        completed_count = sum(1 for r in results if r.get("status") == "completed")
        error_count = sum(1 for r in results if r.get("status") == "error")

        self.logger.log_message(
            source="multiple_workers",
            target="beekeeper",
            message=f"PARALLEL_RESULTS: {completed_count} completed, {error_count} errors",
            message_type="parallel_complete",
            additional_info={"completed": completed_count, "errors": error_count},
        )

        return results

    def get_active_tasks_status(self) -> dict[str, Any]:
        """アクティブタスクの状態を取得"""
        current_time = time.time()
        status = {}

        for task_id, task_info in self.active_tasks.items():
            elapsed_time = current_time - task_info["start_time"]
            status[task_id] = {
                "worker_name": task_info["worker_name"],
                "elapsed_time": elapsed_time,
                "task_type": task_info["task"].get("task_type", "unknown"),
                "instruction": task_info["task"].get("instruction", "")[:50] + "...",
            }

        return status


class HiveWatch:
    """Hive Watch メインクラス"""

    def __init__(self, session_name: str = "cozy-hive"):
        self.communicator = HiveWatchCommunicator(session_name)
        self.session_name = session_name
        self.monitoring = False

    async def start_monitoring(self, interval: float = 2.0) -> None:
        """リアルタイム監視を開始"""
        print("⌚ Hive Watch 監視開始")
        print(f"📊 Session: {self.session_name}")
        print(f"⏱️  Check interval: {interval} seconds")
        print("=" * 50)

        self.monitoring = True

        while self.monitoring:
            try:
                # Worker状態確認
                worker_status = self.communicator.monitor_worker_status()

                # アクティブタスク状態確認
                active_tasks = self.communicator.get_active_tasks_status()

                # 状態表示
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n📊 [{timestamp}] Hive Status:")

                # Worker状態
                if worker_status.get("session_active", False):
                    workers = worker_status.get("workers", {})
                    active_workers = [
                        name
                        for name, info in workers.items()
                        if info.get("pane_active", False)
                    ]
                    print(f"  🟢 Active workers: {len(active_workers)}/{len(workers)}")

                    for worker_name, worker_info in workers.items():
                        status_icon = (
                            "🟢" if worker_info.get("pane_active", False) else "🔴"
                        )
                        print(f"    {status_icon} {worker_name}")
                else:
                    print("  🔴 Session not active")

                # アクティブタスク
                if active_tasks:
                    print(f"  🔄 Active tasks: {len(active_tasks)}")
                    for task_id, task_info in active_tasks.items():
                        elapsed = int(task_info["elapsed_time"])
                        worker = task_info["worker_name"]
                        instruction = task_info["instruction"]
                        print(
                            f"    ⏱️  {task_id[:8]}... ({elapsed}s) {worker}: {instruction}"
                        )

                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"⚠️  Error during monitoring: {e}")
                await asyncio.sleep(interval)

        self.monitoring = False

    def stop_monitoring(self) -> None:
        """監視を停止"""
        self.monitoring = False

    def display_logs(self, tail_lines: int = 20) -> None:
        """ログを表示"""
        log_file = Path("logs/hive_communications.log")

        if not log_file.exists():
            print("📝 No logs found")
            return

        print(f"📝 Recent communications (last {tail_lines} lines):")
        print("=" * 50)

        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()
            recent_lines = lines[-tail_lines:] if len(lines) > tail_lines else lines

            for line in recent_lines:
                try:
                    log_entry = json.loads(line.strip())
                    timestamp = datetime.fromisoformat(log_entry["timestamp"]).strftime(
                        "%H:%M:%S"
                    )
                    source = log_entry["source"]
                    target = log_entry["target"]
                    message = log_entry["message"]

                    # message_type と event_type の両方に対応
                    msg_type = log_entry.get("message_type") or log_entry.get(
                        "event_type", "unknown"
                    )

                    arrow = (
                        "→"
                        if msg_type in ["task", "direct", "task_start"]
                        else "←"
                        if msg_type in ["result", "response", "task_complete"]
                        else "⚡"
                        if msg_type in ["parallel_start", "parallel_complete"]
                        else "•"
                    )
                    print(
                        f"{timestamp} | {source} {arrow} {target} | {message[:80]}..."
                    )

                except json.JSONDecodeError:
                    continue


async def main() -> None:
    """メイン実行関数"""
    parser = argparse.ArgumentParser(
        description="Hive Watch - リアルタイム通信監視システム"
    )
    parser.add_argument("--monitor", action="store_true", help="監視モード開始")
    parser.add_argument("--log", action="store_true", help="ログ表示")
    parser.add_argument("--tail", type=int, default=20, help="表示するログ行数")
    parser.add_argument("--session", default="cozy-hive", help="tmuxセッション名")
    parser.add_argument("--interval", type=float, default=2.0, help="監視間隔（秒）")

    args = parser.parse_args()

    hive_watch = HiveWatch(args.session)

    if args.log:
        hive_watch.display_logs(args.tail)
    elif args.monitor:
        await hive_watch.start_monitoring(args.interval)
    else:
        # デフォルト動作：状態表示
        print("🐝 Hive Watch - リアルタイム通信監視システム")
        print("=" * 50)

        # セッション状態確認
        status = hive_watch.communicator.monitor_worker_status()
        if status.get("session_active", False):
            print("✅ Hive session is active")
            workers = status.get("workers", {})
            for worker_name, worker_info in workers.items():
                status_icon = "🟢" if worker_info.get("pane_active", False) else "🔴"
                print(f"  {status_icon} {worker_name}")
        else:
            print("❌ Hive session not found")
            print("💡 Start with: ./scripts/start-cozy-hive.sh")

        print("\n使用方法:")
        print("  --monitor    リアルタイム監視開始")
        print("  --log        ログ表示")
        print("  --tail N     最新N行のログ表示")


if __name__ == "__main__":
    asyncio.run(main())
