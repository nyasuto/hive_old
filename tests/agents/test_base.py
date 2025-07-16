"""
Base Agent Tests

BaseAgent, BaseCoordinator, BaseWorkerのテストです。
"""

import asyncio
from unittest.mock import Mock, patch

import pytest

from comb.message_router import MessagePriority, MessageType
from hive.agents.base import BaseAgent, BaseCoordinator, BaseWorker


class TestBaseAgent:
    """BaseAgentのテスト"""

    def test_init(self):
        """初期化テスト"""

        # テスト用の実装クラス
        class TestAgent(BaseAgent):
            async def process(self, input_data):
                return {"success": True, "data": input_data}

        agent = TestAgent("test_agent")

        assert agent.worker_id == "test_agent"
        assert agent.logger.name == "test_agent"
        assert agent.comb_api.worker_id == "test_agent"
        assert agent._running is False

    def test_init_with_custom_logger(self):
        """カスタムログ名での初期化テスト"""

        class TestAgent(BaseAgent):
            async def process(self, input_data):
                return {"success": True}

        agent = TestAgent("test_agent", logger_name="custom_logger")

        assert agent.logger.name == "custom_logger"

    @patch("hive.agents.base.CombAPI")
    def test_task_methods(self, mock_comb_api):
        """タスク関連メソッドのテスト"""
        mock_instance = Mock()
        mock_comb_api.return_value = mock_instance

        class TestAgent(BaseAgent):
            async def process(self, input_data):
                return {"success": True}

        agent = TestAgent("test_agent")

        # start_task
        mock_instance.start_task.return_value = "task_123"
        result = agent.start_task("Test Task")
        assert result == "task_123"
        mock_instance.start_task.assert_called_once_with("Test Task")

        # add_progress
        mock_instance.add_progress.return_value = True
        result = agent.add_progress("Progress update", "Details")
        assert result is True
        mock_instance.add_progress.assert_called_once_with("Progress update", "Details")

        # complete_task
        mock_instance.complete_task.return_value = True
        result = agent.complete_task("completed")
        assert result is True
        mock_instance.complete_task.assert_called_once_with("completed")

    @patch("hive.agents.base.CombAPI")
    def test_message_methods(self, mock_comb_api):
        """メッセージ関連メソッドのテスト"""
        mock_instance = Mock()
        mock_comb_api.return_value = mock_instance

        class TestAgent(BaseAgent):
            async def process(self, input_data):
                return {"success": True}

        agent = TestAgent("test_agent")

        # send_message
        mock_instance.send_message.return_value = True
        result = agent.send_message("target", {"test": "data"})
        assert result is True
        mock_instance.send_message.assert_called_once_with(
            "target", {"test": "data"}, MessageType.REQUEST, MessagePriority.MEDIUM
        )

        # receive_messages
        mock_messages = [Mock(), Mock()]
        mock_instance.receive_messages.return_value = mock_messages
        result = agent.receive_messages()
        assert result == mock_messages
        mock_instance.receive_messages.assert_called_once()


class TestBaseCoordinator:
    """BaseCoordinatorのテスト"""

    def test_init(self):
        """初期化テスト"""

        class TestCoordinator(BaseCoordinator):
            async def process(self, input_data):
                return {"success": True}

        coordinator = TestCoordinator("test_coordinator")

        assert coordinator.worker_id == "test_coordinator"
        assert coordinator.workers == []
        assert coordinator.monitoring_cycles == 10
        assert coordinator.monitoring_interval == 5

    def test_worker_management(self):
        """Worker管理のテスト"""

        class TestCoordinator(BaseCoordinator):
            async def process(self, input_data):
                return {"success": True}

        coordinator = TestCoordinator("test_coordinator")

        # add_worker
        coordinator.add_worker("worker1")
        coordinator.add_worker("worker2")
        assert coordinator.workers == ["worker1", "worker2"]

        # 重複追加
        coordinator.add_worker("worker1")
        assert coordinator.workers == ["worker1", "worker2"]

        # remove_worker
        coordinator.remove_worker("worker1")
        assert coordinator.workers == ["worker2"]

        # 存在しないWorkerの削除
        coordinator.remove_worker("worker3")
        assert coordinator.workers == ["worker2"]

    @patch("hive.agents.base.CombAPI")
    @pytest.mark.asyncio
    async def test_assign_task(self, mock_comb_api):
        """タスク割り当てのテスト"""
        mock_instance = Mock()
        mock_comb_api.return_value = mock_instance

        class TestCoordinator(BaseCoordinator):
            async def process(self, input_data):
                return {"success": True}

        coordinator = TestCoordinator("test_coordinator")

        # 成功ケース
        mock_instance.send_message.return_value = True
        mock_instance.add_progress.return_value = True

        result = await coordinator.assign_task("worker1", {"task": "test"})

        assert result is True
        mock_instance.send_message.assert_called_once()
        mock_instance.add_progress.assert_called_once()

        # 失敗ケース
        mock_instance.send_message.return_value = False

        result = await coordinator.assign_task("worker1", {"task": "test"})

        assert result is False

    @patch("hive.agents.base.CombAPI")
    @pytest.mark.asyncio
    async def test_monitor_workers(self, mock_comb_api):
        """Worker監視のテスト"""
        mock_instance = Mock()
        mock_comb_api.return_value = mock_instance

        class TestCoordinator(BaseCoordinator):
            async def process(self, input_data):
                return {"success": True}

            async def _handle_worker_message(self, message, monitoring_result):
                # テスト用に即座に完了状態にする
                monitoring_result["status"] = "completed"

        coordinator = TestCoordinator("test_coordinator")
        coordinator.monitoring_cycles = 2  # テスト用に短縮
        coordinator.monitoring_interval = 0.1  # テスト用に短縮
        coordinator.add_worker("worker1")

        # メッセージ受信をモック
        mock_message = Mock()
        mock_message.from_worker = "worker1"
        mock_instance.receive_messages.return_value = [mock_message]

        result = await coordinator.monitor_workers()

        assert result["status"] == "completed"
        assert result["total_tasks"] == 1
        assert "worker_results" in result


class TestBaseWorker:
    """BaseWorkerのテスト"""

    def test_init(self):
        """初期化テスト"""

        class TestWorker(BaseWorker):
            async def process(self, input_data):
                return {"success": True}

        worker = TestWorker("test_worker")

        assert worker.worker_id == "test_worker"
        assert worker.coordinator_id is None
        assert worker.current_task is None
        assert worker._running is False

    @patch("hive.agents.base.CombAPI")
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, mock_comb_api):
        """監視開始・停止のテスト"""
        mock_instance = Mock()
        mock_comb_api.return_value = mock_instance

        class TestWorker(BaseWorker):
            async def process(self, input_data):
                return {"success": True}

        worker = TestWorker("test_worker")

        # モニタリングを短時間で終了させるため
        async def mock_start_monitoring():
            worker._running = True
            await asyncio.sleep(0.1)  # 短時間待機
            worker._running = False

        worker.start_monitoring = mock_start_monitoring

        # 監視開始
        task = asyncio.create_task(worker.start_monitoring())
        await asyncio.sleep(0.05)  # 開始を待つ

        assert worker._running is True

        # 監視停止
        worker.stop_monitoring()
        await task

        assert worker._running is False

    @patch("hive.agents.base.CombAPI")
    @pytest.mark.asyncio
    async def test_report_completion(self, mock_comb_api):
        """完了報告のテスト"""
        mock_instance = Mock()
        mock_comb_api.return_value = mock_instance

        class TestWorker(BaseWorker):
            async def process(self, input_data):
                return {"success": True, "result": "test_result"}

        worker = TestWorker("test_worker")
        worker.coordinator_id = "test_coordinator"

        # 成功ケース
        mock_instance.send_message.return_value = True

        await worker._report_completion({"result": "test"})

        mock_instance.send_message.assert_called_once()
        call_args = mock_instance.send_message.call_args
        # send_messageは位置引数で呼ばれる
        assert call_args[0][0] == "test_coordinator"  # to_worker
        assert call_args[0][1]["type"] == "task_completed"  # content
        assert call_args[0][1]["result"] == {"result": "test"}

        # coordinator_idが未設定のケース
        worker.coordinator_id = None
        mock_instance.send_message.reset_mock()

        await worker._report_completion({"result": "test"})

        mock_instance.send_message.assert_not_called()
