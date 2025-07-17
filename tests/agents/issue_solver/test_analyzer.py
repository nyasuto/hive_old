"""
Issue Analyzer Tests

IssueAnalyzerクラスのテストスイート
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from hive.agents.issue_solver.analyzer import IssueAnalyzer


class TestIssueAnalyzer(unittest.TestCase):
    """IssueAnalyzerのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.analyzer = IssueAnalyzer()

    def test_init(self):
        """初期化テスト"""
        assert hasattr(self.analyzer, "tech_keywords")
        assert hasattr(self.analyzer, "complexity_indicators")
        assert "python" in self.analyzer.tech_keywords
        assert "high" in self.analyzer.complexity_indicators

    def test_tech_keywords(self):
        """技術キーワードマッピングテスト"""
        assert "python" in self.analyzer.tech_keywords["python"]
        assert "pytest" in self.analyzer.tech_keywords["python"]
        assert "javascript" in self.analyzer.tech_keywords["javascript"]
        assert "test" in self.analyzer.tech_keywords["testing"]

    def test_complexity_indicators(self):
        """複雑度指標テスト"""
        assert "refactor" in self.analyzer.complexity_indicators["high"]
        assert "feature" in self.analyzer.complexity_indicators["medium"]
        assert "bug" in self.analyzer.complexity_indicators["low"]

    def test_calculate_keyword_density(self):
        """キーワード密度計算テスト"""
        content = "This is a Python testing issue with pytest and mypy Python"
        density = self.analyzer._calculate_keyword_density(content)

        assert isinstance(density, dict)
        assert density.get("python", 0) > 0

    def test_estimate_complexity(self):
        """複雑度評価テスト"""
        # High complexity
        high_content = "Need to refactor the entire architecture"
        assert self.analyzer._estimate_complexity(high_content) == "high"

        # Medium complexity
        medium_content = "Add new feature to enhance user experience"
        assert self.analyzer._estimate_complexity(medium_content) == "medium"

        # Low complexity
        low_content = "Fix a small bug in documentation"
        assert self.analyzer._estimate_complexity(low_content) == "low"

    def test_determine_issue_type(self):
        """Issue種別判定テスト"""
        # Bug
        bug_labels = [{"name": "bug"}]
        assert self.analyzer._determine_issue_type("Fix error", bug_labels) == "bug"

        # Feature
        feature_labels = [{"name": "enhancement"}]
        assert (
            self.analyzer._determine_issue_type("Add feature", feature_labels)
            == "feature"
        )

        # No labels - default to feature
        assert self.analyzer._determine_issue_type("Some title", []) == "feature"

    def test_estimate_time(self):
        """時間見積もりテスト"""
        # High complexity
        high_analysis = {"complexity": "high", "technologies": ["python", "testing"]}
        assert self.analyzer._estimate_time(high_analysis) == 240  # 4 hours

        # Medium complexity
        medium_analysis = {"complexity": "medium", "technologies": ["python"]}
        assert self.analyzer._estimate_time(medium_analysis) == 120  # 2 hours

        # Low complexity
        low_analysis = {"complexity": "low", "technologies": ["documentation"]}
        assert self.analyzer._estimate_time(low_analysis) == 60  # 1 hour

        # Many technologies (multiplier effect)
        complex_analysis = {
            "complexity": "medium",
            "technologies": ["python", "testing", "ci_cd", "docs"],
        }
        assert (
            self.analyzer._estimate_time(complex_analysis) == 180
        )  # 3 hours (120 * 1.5)

    def test_identify_required_skills(self):
        """必要スキル特定テスト"""
        analysis = {
            "type": "bug",
            "technologies": ["python", "testing"],
            "complexity": "medium",
        }

        skills = self.analyzer._identify_required_skills(analysis)

        assert "python_development" in skills
        assert "test_writing" in skills
        assert "problem_solving" in skills
        assert "code_review" in skills

    def test_create_error_analysis(self):
        """エラー分析作成テスト"""
        error_msg = "Test error message"
        result = self.analyzer._create_error_analysis(error_msg)

        assert result["success"] is False
        assert result["error"] == error_msg

    @patch("subprocess.run")
    @pytest.mark.asyncio
    async def test_fetch_issue_data_success(self, mock_run):
        """Issue データ取得成功テスト"""
        # Mock successful gh command
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = (
            '{"number": 64, "title": "Test Issue", "body": "Test body"}'
        )
        mock_run.return_value = mock_result

        result = await self.analyzer._fetch_issue_data(64)

        assert result is not None
        assert result["number"] == 64
        assert result["title"] == "Test Issue"

    @patch("subprocess.run")
    @pytest.mark.asyncio
    async def test_fetch_issue_data_failure(self, mock_run):
        """Issue データ取得失敗テスト"""
        # Mock failed gh command
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: Issue not found"
        mock_run.return_value = mock_result

        result = await self.analyzer._fetch_issue_data(64)

        assert result is None

    def test_analyze_issue_content(self):
        """Issue内容分析テスト"""
        issue_data = {
            "title": "Fix Python testing bug",
            "body": "There is a bug in our pytest setup that needs fixing",
        }
        prompt_info = {"priority": "high"}

        result = self.analyzer._analyze_issue_content(issue_data, prompt_info)

        assert result["type"] == "bug"
        assert result["complexity"] in ["low", "medium", "high"]
        assert "python" in result["technologies"]
        assert "testing" in result["technologies"]

    def test_propose_resolution_strategy(self):
        """解決戦略提案テスト"""
        analysis = {
            "type": "bug",
            "complexity": "medium",
            "technologies": ["python", "testing"],
        }

        strategy = self.analyzer._propose_resolution_strategy(analysis)

        assert "recommended_approach" in strategy
        assert "action_sequence" in strategy
        assert strategy["recommended_approach"] == "bug_fix"

    @patch("hive.agents.issue_solver.analyzer.IssueAnalyzer._fetch_issue_data")
    @pytest.mark.asyncio
    async def test_analyze_issue_success(self, mock_fetch):
        """Issue分析成功テスト"""
        # Mock issue data
        mock_fetch.return_value = {
            "number": 64,
            "title": "Fix Python bug",
            "body": "Bug in Python code needs fixing",
        }

        prompt_info = {"priority": "medium", "intent": "solve"}

        result = await self.analyzer.analyze_issue(64, prompt_info)

        assert result["success"] is True
        assert result["issue_number"] == 64
        assert "analysis" in result
        assert "strategy" in result
        assert "estimated_time" in result

    @patch("hive.agents.issue_solver.analyzer.IssueAnalyzer._fetch_issue_data")
    @pytest.mark.asyncio
    async def test_analyze_issue_fetch_failure(self, mock_fetch):
        """Issue分析データ取得失敗テスト"""
        # Mock failed fetch
        mock_fetch.return_value = None

        prompt_info = {"priority": "medium", "intent": "solve"}

        result = await self.analyzer.analyze_issue(64, prompt_info)

        assert result["success"] is False
        assert "Failed to fetch issue data" in result["error"]


if __name__ == "__main__":
    unittest.main()
