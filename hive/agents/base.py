"""
Base Agent Classes

全てのエージェントが継承する基底クラスを提供します。
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from comb.api import CombAPI
from comb.message_router import Message, MessagePriority, MessageType


class BaseAgent(ABC):
    """全エージェントの基底クラス"""

    def __init__(self, worker_id: str, logger_name: str | None = None):
        """
        Args:
            worker_id: Worker識別子
            logger_name: ログ名（未指定時はworker_idを使用）
        """
        self.worker_id = worker_id
        self.logger = logging.getLogger(logger_name or worker_id)
        self.comb_api = CombAPI(worker_id)
        self._running = False

    def start_task(self, task_title: str, **kwargs) -> str:
        """タスク開始"""
        return self.comb_api.start_task(task_title, **kwargs)

    def add_progress(self, description: str, details: str | None = None) -> bool:
        """進捗追加"""
        return self.comb_api.add_progress(description, details)

    def complete_task(self, result: str = "completed") -> bool:
        """タスク完了"""
        return self.comb_api.complete_task(result)

    def send_message(
        self,
        to_worker: str,
        content: dict[str, Any],
        message_type: MessageType = MessageType.REQUEST,
        priority: MessagePriority = MessagePriority.MEDIUM,
    ) -> bool:
        """メッセージ送信"""
        return self.comb_api.send_message(to_worker, content, message_type, priority)

    def receive_messages(self) -> list[Message]:
        """メッセージ受信"""
        return self.comb_api.receive_messages()

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """メイン処理（サブクラスで実装）"""
        pass


class BaseCoordinator(BaseAgent):
    """Coordinatorエージェントの基底クラス"""

    def __init__(self, worker_id: str, logger_name: str | None = None):
        super().__init__(worker_id, logger_name)
        self.workers: list[str] = []
        self.monitoring_cycles = 10
        self.monitoring_interval = 5  # seconds

    def add_worker(self, worker_id: str) -> None:
        """Worker追加"""
        if worker_id not in self.workers:
            self.workers.append(worker_id)

    def remove_worker(self, worker_id: str) -> None:
        """Worker削除"""
        if worker_id in self.workers:
            self.workers.remove(worker_id)

    async def assign_task(self, worker_id: str, task_data: dict[str, Any]) -> bool:
        """Workerにタスク割り当て"""
        assignment = {
            "action": "execute_task",
            "task_data": task_data,
            "coordinator_id": self.worker_id,
            "timestamp": asyncio.get_event_loop().time(),
        }

        success = self.send_message(
            to_worker=worker_id,
            content=assignment,
            message_type=MessageType.REQUEST,
            priority=MessagePriority.HIGH,
        )

        if success:
            self.logger.info(f"Task assigned to {worker_id}")
            self.add_progress(f"Task assigned to {worker_id}")
        else:
            self.logger.error(f"Failed to assign task to {worker_id}")

        return success

    async def monitor_workers(self) -> dict[str, Any]:
        """Worker監視"""
        monitoring_result = {
            "completed_tasks": 0,
            "total_tasks": len(self.workers),
            "worker_results": {},
            "status": "in_progress",
        }

        for cycle in range(self.monitoring_cycles):
            self.logger.info(f"Monitoring cycle {cycle + 1}/{self.monitoring_cycles}")
            await asyncio.sleep(self.monitoring_interval)

            try:
                messages = self.receive_messages()
                self.logger.info(f"Received {len(messages)} messages")

                for message in messages:
                    if message.from_worker in self.workers:
                        await self._handle_worker_message(message, monitoring_result)

            except Exception as e:
                self.logger.error(f"Error in monitoring: {e}")

            # 完了チェック
            if monitoring_result["status"] == "completed":
                self.logger.info("All tasks completed, stopping monitoring")
                break

        if monitoring_result["status"] != "completed":
            self.logger.warning(
                f"Monitoring timed out after {self.monitoring_cycles} cycles"
            )
            monitoring_result["status"] = "timeout"

        return monitoring_result

    async def _handle_worker_message(
        self, message: Message, monitoring_result: dict[str, Any]
    ) -> None:
        """Worker メッセージ処理（サブクラスで実装）"""
        content = message.content
        message_type = content.get("type", "unknown")

        if message_type == "task_completed":
            monitoring_result["completed_tasks"] += 1
            monitoring_result["worker_results"][message.from_worker] = content.get(
                "result", {}
            )

            if monitoring_result["completed_tasks"] >= monitoring_result["total_tasks"]:
                monitoring_result["status"] = "completed"

        self.logger.info(
            f"Handled message type: {message_type} from {message.from_worker}"
        )


class BaseWorker(BaseAgent):
    """Workerエージェントの基底クラス"""

    def __init__(self, worker_id: str, logger_name: str | None = None):
        super().__init__(worker_id, logger_name)
        self.coordinator_id: str | None = None
        self.current_task: dict[str, Any] | None = None

    async def start_monitoring(self) -> None:
        """監視開始"""
        self.logger.info(f"Starting monitoring for {self.worker_id}")
        self._running = True

        monitoring_cycles = 0
        while self._running:
            try:
                monitoring_cycles += 1
                self.logger.info(f"Monitoring cycle {monitoring_cycles}")

                messages = self.receive_messages()
                self.logger.info(f"Received {len(messages)} messages")

                for message in messages:
                    await self._handle_coordinator_message(message)

                await asyncio.sleep(3)  # 監視間隔

            except Exception as e:
                self.logger.error(f"Error in monitoring: {e}")
                await asyncio.sleep(5)

    def stop_monitoring(self) -> None:
        """監視停止"""
        self._running = False
        self.logger.info(f"Stopping monitoring for {self.worker_id}")

    async def _handle_coordinator_message(self, message: Message) -> None:
        """Coordinator メッセージ処理"""
        content = message.content
        action = content.get("action", "unknown")

        self.logger.info(f"Handling action: {action} from {message.from_worker}")

        if action == "execute_task":
            self.coordinator_id = content.get("coordinator_id")
            self.current_task = content.get("task_data")

            # タスク実行
            result = await self.process(self.current_task)

            # 結果報告
            await self._report_completion(result)

    async def _report_completion(self, result: Any) -> None:
        """完了報告"""
        if not self.coordinator_id:
            self.logger.warning("No coordinator to report to")
            return

        report = {
            "type": "task_completed",
            "worker_id": self.worker_id,
            "result": result,
            "timestamp": asyncio.get_event_loop().time(),
        }

        success = self.send_message(
            to_worker=self.coordinator_id,
            content=report,
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.HIGH,
        )

        if success:
            self.logger.info(f"Completion reported to {self.coordinator_id}")
        else:
            self.logger.error(f"Failed to report completion to {self.coordinator_id}")
