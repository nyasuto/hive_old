"""
Agent Mixins Tests

エージェントMixinクラスのテストスイート
"""

import unittest
from unittest.mock import patch

from hive.agents.mixins import ErrorHandlingMixin, ValidationMixin, WorkLogMixin


class TestMixinImplementation(ValidationMixin, ErrorHandlingMixin, WorkLogMixin):
    """テスト用のMixin実装クラス"""

    def __init__(self):
        self.worker_id = "test_worker"
        self.tasks = []
        self.technical_decisions = []
        self.challenges = []
        self.progress_updates = []


class TestValidationMixin(unittest.TestCase):
    """ValidationMixinのテスト"""

    def setUp(self):
        self.mixin = TestMixinImplementation()

    def test_validate_input_success(self):
        """入力検証成功テスト"""
        input_data = {"field1": "value1", "field2": "value2"}
        required_fields = ["field1", "field2"]

        result = self.mixin.validate_input(input_data, required_fields)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_input_missing_fields(self):
        """必須フィールド不足テスト"""
        input_data = {"field1": "value1"}
        required_fields = ["field1", "field2", "field3"]

        result = self.mixin.validate_input(input_data, required_fields)

        assert result["valid"] is False
        assert len(result["errors"]) == 2
        assert "field2" in str(result["errors"])
        assert "field3" in str(result["errors"])

    def test_validate_input_none_data(self):
        """None入力テスト"""
        input_data = None
        required_fields = ["field1"]

        result = self.mixin.validate_input(input_data, required_fields)

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_input_empty_required_fields(self):
        """必須フィールドなしテスト"""
        input_data = {"field1": "value1"}
        required_fields = []

        result = self.mixin.validate_input(input_data, required_fields)

        assert result["valid"] is True
        assert len(result["errors"]) == 0


class TestErrorHandlingMixin(unittest.TestCase):
    """ErrorHandlingMixinのテスト"""

    def setUp(self):
        self.mixin = TestMixinImplementation()

    def test_handle_exception(self):
        """例外処理テスト"""
        test_exception = ValueError("Test error message")
        context = "test_method"

        result = self.mixin.handle_exception(test_exception, context)

        assert result["error_type"] == "ValueError"
        assert result["error_message"] == "Test error message"
        assert result["context"] == "test_method"
        assert "timestamp" in result

    def test_create_error_response(self):
        """エラーレスポンス作成テスト"""
        error_message = "Test error occurred"

        result = self.mixin.create_error_response(error_message)

        assert result["success"] is False
        assert result["error"]["message"] == error_message
        assert result["error"]["type"] == "processing_error"
        assert "timestamp" in result["error"]

    def test_create_success_response(self):
        """成功レスポンス作成テスト"""
        data = {"result": "success", "value": 42}

        result = self.mixin.create_success_response(data)

        assert result["success"] is True
        assert result["data"]["result"] == "success"
        assert result["data"]["value"] == 42
        assert "timestamp" in result

    def test_create_success_response_none_data(self):
        """成功レスポンス作成テスト（データなし）"""
        result = self.mixin.create_success_response(None)

        assert result["success"] is True
        assert result["data"] is None
        assert "timestamp" in result


class TestWorkLogMixin(unittest.TestCase):
    """WorkLogMixinのテスト"""

    def setUp(self):
        self.mixin = TestMixinImplementation()

    def test_start_task(self):
        """タスク開始テスト"""
        task_id = self.mixin.start_task(
            "Test Task",
            task_type="test",
            description="A test task",
            issue_number=64,
            workers=["worker1", "worker2"],
        )

        assert task_id is not None
        assert len(self.mixin.tasks) == 1

        task = self.mixin.tasks[0]
        assert task["title"] == "Test Task"
        assert task["task_type"] == "test"
        assert task["description"] == "A test task"
        assert task["issue_number"] == 64
        assert task["workers"] == ["worker1", "worker2"]
        assert task["status"] == "in_progress"

    def test_complete_task(self):
        """タスク完了テスト"""
        # まずタスクを開始
        task_id = self.mixin.start_task("Test Task")

        # タスクを完了
        self.mixin.complete_task("Task completed successfully")

        # 最新のタスクが完了状態になっていることを確認
        task = self.mixin.tasks[-1]
        assert task["status"] == "completed"
        assert task["completion_notes"] == "Task completed successfully"
        assert "completed_at" in task

    def test_add_technical_decision(self):
        """技術的決定追加テスト"""
        self.mixin.add_technical_decision(
            "Database Choice",
            "Selected PostgreSQL for data persistence",
            ["MySQL", "MongoDB", "SQLite"],
        )

        assert len(self.mixin.technical_decisions) == 1

        decision = self.mixin.technical_decisions[0]
        assert decision["decision"] == "Database Choice"
        assert decision["reasoning"] == "Selected PostgreSQL for data persistence"
        assert decision["alternatives"] == ["MySQL", "MongoDB", "SQLite"]
        assert "timestamp" in decision

    def test_add_challenge(self):
        """課題追加テスト"""
        self.mixin.add_challenge(
            "Performance bottleneck in data processing",
            "Investigating optimization strategies",
        )

        assert len(self.mixin.challenges) == 1

        challenge = self.mixin.challenges[0]
        assert challenge["challenge"] == "Performance bottleneck in data processing"
        assert challenge["approach"] == "Investigating optimization strategies"
        assert challenge["status"] == "investigating"
        assert "timestamp" in challenge

    def test_add_progress(self):
        """進捗追加テスト"""
        self.mixin.add_progress(
            "API Implementation", "Completed user authentication endpoints"
        )

        assert len(self.mixin.progress_updates) == 1

        progress = self.mixin.progress_updates[0]
        assert progress["milestone"] == "API Implementation"
        assert progress["details"] == "Completed user authentication endpoints"
        assert "timestamp" in progress

    def test_log_info(self):
        """情報ログテスト"""
        with patch("builtins.print") as mock_print:
            self.mixin.log_info("Test information message")
            mock_print.assert_called_once()

    def test_log_error(self):
        """エラーログテスト"""
        with patch("builtins.print") as mock_print:
            self.mixin.log_error("Test error message")
            mock_print.assert_called_once()


if __name__ == "__main__":
    unittest.main()
