"""
Agent Framework

BeeKeeper-Queen-Worker協調システムの標準化されたフレームワークです。
"""

import asyncio
import logging
from typing import Any

from .base import BaseAgent, BaseCoordinator, BaseWorker


class AgentFramework:
    """エージェントフレームワーク"""

    def __init__(self, name: str = "agent_framework"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.beekeeper: BaseAgent | None = None
        self.coordinators: dict[str, BaseCoordinator] = {}
        self.workers: dict[str, BaseWorker] = {}
        self._running = False

    def register_beekeeper(self, beekeeper: BaseAgent) -> None:
        """BeeKeeper登録"""
        self.beekeeper = beekeeper
        self.logger.info(f"BeeKeeper registered: {beekeeper.worker_id}")

    def register_coordinator(self, coordinator: BaseCoordinator) -> None:
        """Coordinator登録"""
        self.coordinators[coordinator.worker_id] = coordinator
        self.logger.info(f"Coordinator registered: {coordinator.worker_id}")

    def register_worker(self, worker: BaseWorker) -> None:
        """Worker登録"""
        self.workers[worker.worker_id] = worker
        self.logger.info(f"Worker registered: {worker.worker_id}")

    def auto_assign_workers(self) -> None:
        """Workerの自動割り当て"""
        for coordinator in self.coordinators.values():
            for worker_id in self.workers.keys():
                coordinator.add_worker(worker_id)

        self.logger.info("Workers auto-assigned to coordinators")

    async def start_system(self) -> None:
        """システム開始"""
        self.logger.info(f"Starting {self.name} system")
        self._running = True

        # Workerの監視開始
        worker_tasks = []
        for worker in self.workers.values():
            task = asyncio.create_task(worker.start_monitoring())
            worker_tasks.append(task)

        self.logger.info(f"Started {len(worker_tasks)} workers")

        # システムが停止されるまで待機
        try:
            await asyncio.gather(*worker_tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(f"System error: {e}")

    async def stop_system(self) -> None:
        """システム停止"""
        self.logger.info(f"Stopping {self.name} system")
        self._running = False

        # 全Workerの停止
        for worker in self.workers.values():
            worker.stop_monitoring()

        self.logger.info("System stopped")

    async def process_request(self, request: Any) -> Any:
        """リクエスト処理"""
        if not self.beekeeper:
            raise ValueError("BeeKeeper not registered")

        self.logger.info("Processing request through BeeKeeper")

        # BeeKeeperでリクエスト処理
        result = await self.beekeeper.process(request)

        self.logger.info("Request processed")
        return result

    def get_system_status(self) -> dict[str, Any]:
        """システム状態取得"""
        return {
            "name": self.name,
            "running": self._running,
            "beekeeper": self.beekeeper.worker_id if self.beekeeper else None,
            "coordinators": list(self.coordinators.keys()),
            "workers": list(self.workers.keys()),
            "total_agents": len(self.coordinators)
            + len(self.workers)
            + (1 if self.beekeeper else 0),
        }


class AgentFactory:
    """エージェント作成ファクトリー"""

    @staticmethod
    def create_coordinator(
        coordinator_class: type[BaseCoordinator], worker_id: str, **kwargs
    ) -> BaseCoordinator:
        """Coordinator作成"""
        return coordinator_class(worker_id, **kwargs)

    @staticmethod
    def create_worker(
        worker_class: type[BaseWorker], worker_id: str, **kwargs
    ) -> BaseWorker:
        """Worker作成"""
        return worker_class(worker_id, **kwargs)

    @staticmethod
    def create_beekeeper(
        beekeeper_class: type[BaseAgent], worker_id: str, **kwargs
    ) -> BaseAgent:
        """BeeKeeper作成"""
        return beekeeper_class(worker_id, **kwargs)


class SimpleBeeKeeper(BaseAgent):
    """シンプルなBeeKeeper実装"""

    def __init__(
        self, worker_id: str = "simple_beekeeper", coordinator_id: str = "coordinator"
    ):
        super().__init__(worker_id)
        self.coordinator_id = coordinator_id

    async def process(self, input_data: Any) -> Any:
        """リクエスト処理"""
        self.logger.info(f"Processing request: {input_data}")

        # タスク開始
        task_id = self.start_task(f"Process request: {input_data}")

        # Coordinatorに処理依頼
        request_data = {
            "action": "process_request",
            "input_data": input_data,
            "task_id": task_id,
        }

        success = self.send_message(self.coordinator_id, request_data)

        if success:
            self.add_progress("Request sent to coordinator")

            # 結果待機（簡易実装）
            await asyncio.sleep(1)

            # 完了
            self.complete_task("Request processed")

            return {
                "success": True,
                "message": "Request processed successfully",
                "task_id": task_id,
            }
        else:
            self.complete_task("Request failed")
            return {
                "success": False,
                "message": "Failed to send request to coordinator",
            }
