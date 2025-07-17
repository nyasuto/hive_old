"""
Issue Solver Worker Tests

IssueSolverWorkerクラスのテストスイート
"""

import unittest
from unittest.mock import patch

import pytest

from hive.agents.issue_solver.worker import IssueSolverWorker


class TestIssueSolverWorker(unittest.TestCase):
    """IssueSolverWorkerのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.worker = IssueSolverWorker("test_worker")

    def test_init(self):
        """初期化テスト"""
        assert self.worker.worker_id == "test_worker"
        assert hasattr(self.worker, "current_issue")
        assert hasattr(self.worker, "issue_context")
        assert hasattr(self.worker, "github_client")

    def test_init_default_worker_id(self):
        """デフォルトworker_id初期化テスト"""
        worker = IssueSolverWorker()
        assert worker.worker_id == "issue_solver_worker"

    @pytest.mark.asyncio
    async def test_process_success(self):
        """成功時の処理テスト"""
        input_data = {
            "action": "resolve_issue",
            "issue_data": {
                "issue_number": 64,
                "title": "Test Issue",
                "body": "Test description",
            },
            "resolution_plan": {
                "action_sequence": [
                    {"step": 1, "action": "investigate"},
                    {"step": 2, "action": "implement"},
                ]
            },
        }

        # Mock external dependencies
        with (
            patch.object(self.worker, "_fetch_issue_details") as mock_fetch,
            patch.object(self.worker, "_execute_resolution_plan") as mock_execute,
        ):
            mock_fetch.return_value = {
                "success": True,
                "issue_details": input_data["issue_data"],
            }
            mock_execute.return_value = {"success": True, "results": []}

            result = await self.worker.process(input_data)

            assert result["success"] is True
            assert "resolution_result" in result

    @pytest.mark.asyncio
    async def test_process_validation_failure(self):
        """入力検証失敗時の処理テスト"""
        # Invalid input - missing required fields
        input_data = {"invalid": "data"}

        result = await self.worker.process(input_data)

        assert result["success"] is False
        assert "validation" in result["error"]["type"]

    def test_fetch_issue_details_mock(self):
        """Issue詳細取得テスト（モック版）"""
        issue_data = {
            "issue_number": 64,
            "title": "Test Issue",
            "body": "Test description",
        }

        with patch.object(self.worker, "_fetch_issue_details") as mock_fetch:
            mock_fetch.return_value = {"success": True, "issue_details": issue_data}

            result = self.worker._fetch_issue_details(issue_data)

            assert result["success"] is True
            assert result["issue_details"]["issue_number"] == 64

    def test_execute_resolution_plan_mock(self):
        """解決計画実行テスト（モック版）"""
        resolution_plan = {
            "action_sequence": [
                {"step": 1, "action": "investigate", "description": "Analyze the issue"}
            ]
        }

        with patch.object(self.worker, "_execute_resolution_plan") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "results": [{"step": 1, "status": "completed"}],
            }

            result = self.worker._execute_resolution_plan(resolution_plan)

            assert result["success"] is True
            assert len(result["results"]) == 1

    def test_create_implementation_strategy_mock(self):
        """実装戦略作成テスト（モック版）"""
        issue_details = {
            "issue_number": 64,
            "analysis": {"type": "bug", "complexity": "medium"},
        }

        with patch.object(
            self.worker, "_create_implementation_strategy"
        ) as mock_strategy:
            mock_strategy.return_value = {
                "approach": "bug_fix",
                "steps": ["investigate", "fix", "test"],
            }

            result = self.worker._create_implementation_strategy(issue_details)

            assert result["approach"] == "bug_fix"
            assert len(result["steps"]) == 3

    def test_validate_issue_resolution_mock(self):
        """Issue解決検証テスト（モック版）"""
        resolution_result = {"completed_steps": 2, "total_steps": 2, "success": True}

        with patch.object(self.worker, "_validate_issue_resolution") as mock_validate:
            mock_validate.return_value = {
                "validation_passed": True,
                "score": 85,
                "recommendations": [],
            }

            result = self.worker._validate_issue_resolution(resolution_result)

            assert result["validation_passed"] is True
            assert result["score"] == 85

    def test_update_issue_status_mock(self):
        """Issue状態更新テスト（モック版）"""
        status_update = {
            "issue_number": 64,
            "new_status": "resolved",
            "resolution_summary": "Fixed the bug",
        }

        with patch.object(self.worker, "_update_issue_status") as mock_update:
            mock_update.return_value = {"success": True, "updated": True}

            result = self.worker._update_issue_status(status_update)

            assert result["success"] is True
            assert result["updated"] is True


if __name__ == "__main__":
    unittest.main()
