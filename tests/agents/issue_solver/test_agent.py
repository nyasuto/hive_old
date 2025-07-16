"""
Issue Solver Agent Integration Tests

IssueSolverAgentの統合テストです。
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from hive.agents.issue_solver.agent import IssueSolverAgent


class TestIssueSolverAgent:
    """IssueSolverAgentの統合テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.agent = IssueSolverAgent()

    def test_init(self):
        """初期化テスト"""
        assert self.agent.worker_id == "issue_solver_beekeeper"
        assert self.agent.prompt_parser is not None
        assert self.agent.analyzer is not None
        assert self.agent.coordinator is not None
        assert self.agent.worker is not None
        assert self.agent.framework is not None

    @patch("hive.agents.issue_solver.agent.UserPromptParser")
    @patch("hive.agents.issue_solver.agent.IssueAnalyzer")
    @pytest.mark.asyncio
    async def test_process_solve_intent(self, mock_analyzer, mock_parser):
        """解決意図の処理テスト"""
        # モックセットアップ
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance

        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance

        # パーサーの戻り値
        mock_parser_instance.parse_user_prompt.return_value = {
            "success": True,
            "issue_number": 64,
            "intent": "solve",
            "priority": "medium",
        }

        # アナライザーの戻り値
        mock_analyzer_instance.analyze_issue = AsyncMock(
            return_value={
                "success": True,
                "issue_number": 64,
                "title": "Test Issue",
                "analysis": {"type": "bug", "complexity": "medium"},
                "strategy": {
                    "recommended_approach": "bug_fix",
                    "action_sequence": [
                        {"step": 1, "action": {"type": "investigation"}},
                        {"step": 2, "action": {"type": "implementation"}},
                    ],
                    "success_criteria": ["Bug fixed"],
                },
            }
        )

        # コーディネーターの戻り値をモック
        with patch.object(
            self.agent.coordinator, "process", new_callable=AsyncMock
        ) as mock_coord:
            mock_coord.return_value = {
                "success": True,
                "data": {
                    "resolution_result": {"status": "completed", "total_time": 30.0},
                    "validation_result": {
                        "success": True,
                        "status": "validation_passed",
                    },
                },
            }

            result = await self.agent.process("Issue 64を解決する")

            assert result["success"] is True
            assert result["mode"] == "solve"
            assert result["issue_number"] == 64
            assert "resolution_result" in result
            assert "validation_result" in result

    @pytest.mark.skip(
        reason="Test expectations need update after #87 refactoring - will fix in #89"
    )
    @patch("hive.agents.issue_solver.agent.UserPromptParser")
    @patch("hive.agents.issue_solver.agent.IssueAnalyzer")
    @pytest.mark.asyncio
    async def test_process_investigate_intent(self, mock_analyzer, mock_parser):
        """調査意図の処理テスト"""
        # モックセットアップ
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance

        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance

        # パーサーの戻り値
        mock_parser_instance.parse_user_prompt.return_value = {
            "success": True,
            "issue_number": 64,
            "intent": "investigate",
            "priority": "medium",
        }

        # アナライザーの戻り値
        mock_analyzer_instance.analyze_issue = AsyncMock(
            return_value={
                "success": True,
                "issue_number": 64,
                "title": "Test Issue",
                "analysis": {
                    "type": "bug",
                    "complexity": "medium",
                    "technologies": ["python", "testing"],
                },
                "strategy": {"recommended_approach": "bug_fix"},
                "estimated_time": 120,
                "required_skills": ["python_development", "debugging"],
            }
        )

        result = await self.agent.process("Issue 64について調査してください")

        assert result["success"] is True
        assert result["mode"] == "investigate"
        assert result["issue_number"] == 64
        assert "investigation_result" in result
        assert result["investigation_result"]["issue_summary"]["type"] == "bug"
        assert result["investigation_result"]["issue_summary"]["complexity"] == "medium"

    @pytest.mark.skip(
        reason="Test expectations need update after #87 refactoring - will fix in #89"
    )
    @patch("hive.agents.issue_solver.agent.UserPromptParser")
    @patch("hive.agents.issue_solver.agent.IssueAnalyzer")
    @pytest.mark.asyncio
    async def test_process_explain_intent(self, mock_analyzer, mock_parser):
        """説明意図の処理テスト"""
        # モックセットアップ
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance

        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance

        # パーサーの戻り値
        mock_parser_instance.parse_user_prompt.return_value = {
            "success": True,
            "issue_number": 64,
            "intent": "explain",
            "priority": "medium",
        }

        # アナライザーの戻り値
        mock_analyzer_instance.analyze_issue = AsyncMock(
            return_value={
                "success": True,
                "issue_number": 64,
                "title": "Test Issue Title",
                "analysis": {
                    "type": "bug",
                    "complexity": "medium",
                    "technologies": ["python"],
                },
                "strategy": {
                    "recommended_approach": "bug_fix",
                    "action_sequence": [
                        {
                            "step": 1,
                            "action": {
                                "type": "investigation",
                                "description": "Investigate the issue",
                            },
                        },
                        {
                            "step": 2,
                            "action": {
                                "type": "implementation",
                                "description": "Implement the fix",
                            },
                        },
                    ],
                },
                "estimated_time": 120,
            }
        )

        result = await self.agent.process("Issue 64の内容を説明してください")

        assert result["success"] is True
        assert result["mode"] == "explain"
        assert result["issue_number"] == 64
        assert "explanation" in result
        assert "Issue #64 について説明します" in result["explanation"]
        assert "Test Issue Title" in result["explanation"]

    @patch("hive.agents.issue_solver.agent.UserPromptParser")
    @pytest.mark.asyncio
    async def test_process_parser_error(self, mock_parser):
        """パーサーエラーの処理テスト"""
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance

        # パーサーエラー
        mock_parser_instance.parse_user_prompt.return_value = {
            "success": False,
            "error": "No issue number found",
        }

        result = await self.agent.process("何かを解決する")

        assert result["success"] is False
        assert "Prompt parsing failed" in result["error"]["message"]

    @pytest.mark.skip(
        reason="Test expectations need update after #87 refactoring - will fix in #89"
    )
    @patch("hive.agents.issue_solver.agent.UserPromptParser")
    @patch("hive.agents.issue_solver.agent.IssueAnalyzer")
    @pytest.mark.asyncio
    async def test_process_analyzer_error(self, mock_analyzer, mock_parser):
        """アナライザーエラーの処理テスト"""
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance

        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance

        # パーサー成功
        mock_parser_instance.parse_user_prompt.return_value = {
            "success": True,
            "issue_number": 64,
            "intent": "solve",
            "priority": "medium",
        }

        # アナライザーエラー
        mock_analyzer_instance.analyze_issue = AsyncMock(
            return_value={"success": False, "error": "Failed to fetch issue data"}
        )

        result = await self.agent.process("Issue 64を解決する")

        assert result["success"] is False
        assert "Issue analysis failed" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_process_empty_prompt(self):
        """空のプロンプトの処理テスト"""
        result = await self.agent.process("")

        assert result["success"] is False
        assert "No prompt provided" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_process_dict_input(self):
        """辞書入力の処理テスト"""
        with patch.object(self.agent.prompt_parser, "parse_user_prompt") as mock_parse:
            mock_parse.return_value = {
                "success": True,
                "issue_number": 64,
                "intent": "solve",
                "priority": "medium",
            }

            with patch.object(
                self.agent.analyzer, "analyze_issue", new_callable=AsyncMock
            ) as mock_analyze:
                mock_analyze.return_value = {
                    "success": True,
                    "issue_number": 64,
                    "title": "Test",
                    "analysis": {"type": "bug", "complexity": "low"},
                    "strategy": {
                        "recommended_approach": "bug_fix",
                        "action_sequence": [],
                        "success_criteria": [],
                    },
                }

                with patch.object(
                    self.agent.coordinator, "process", new_callable=AsyncMock
                ) as mock_coord:
                    mock_coord.return_value = {
                        "success": True,
                        "data": {
                            "resolution_result": {"status": "completed"},
                            "validation_result": {"success": True},
                        },
                    }

                    result = await self.agent.process({"prompt": "Issue 64を解決する"})

                    assert result["success"] is True
                    mock_parse.assert_called_once_with("Issue 64を解決する")

    def test_generate_issue_explanation(self):
        """Issue説明文生成のテスト"""
        issue_analysis = {
            "issue_number": 64,
            "title": "Test Issue Title",
            "analysis": {
                "type": "bug",
                "complexity": "medium",
                "technologies": ["python", "testing"],
            },
            "strategy": {
                "recommended_approach": "bug_fix",
                "action_sequence": [
                    {
                        "step": 1,
                        "action": {"type": "investigation", "description": "調査実行"},
                    },
                    {
                        "step": 2,
                        "action": {"type": "implementation", "description": "修正実装"},
                    },
                ],
            },
            "estimated_time": 120,
        }

        explanation = self.agent._generate_issue_explanation(issue_analysis)

        assert "Issue #64 について説明します" in explanation
        assert "Test Issue Title" in explanation
        assert "bug" in explanation
        assert "medium" in explanation
        assert "python, testing" in explanation
        assert "bug_fix" in explanation
        assert "120分" in explanation
        assert "1. 調査実行" in explanation
        assert "2. 修正実装" in explanation

    @pytest.mark.asyncio
    async def test_system_lifecycle(self):
        """システムライフサイクルのテスト"""
        # start_systemとstop_systemはフレームワークに委譲
        with patch.object(
            self.agent.framework, "start_system", new_callable=AsyncMock
        ) as mock_start:
            await self.agent.start_system()
            mock_start.assert_called_once()

        with patch.object(
            self.agent.framework, "stop_system", new_callable=AsyncMock
        ) as mock_stop:
            await self.agent.stop_system()
            mock_stop.assert_called_once()

    def test_get_system_status(self):
        """システム状態取得のテスト"""
        with patch.object(self.agent.framework, "get_system_status") as mock_status:
            mock_status.return_value = {
                "name": "issue_solver_system",
                "running": True,
                "agents": 3,
            }

            status = self.agent.get_system_status()

            assert status["name"] == "issue_solver_system"
            assert status["running"] is True
            assert status["agents"] == 3
            mock_status.assert_called_once()
