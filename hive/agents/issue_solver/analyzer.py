"""
Issue Analyzer

GitHub Issueの内容を分析して解決戦略を提案します。
"""

import json
import subprocess
from typing import Any

from ..mixins import ErrorHandlingMixin, LoggingMixin, ValidationMixin


class IssueAnalyzer(LoggingMixin, ValidationMixin, ErrorHandlingMixin):
    """GitHub Issue分析器"""

    def __init__(self):
        self.setup_logger("issue_analyzer")

        # 技術要素マッピング
        self.tech_keywords = {
            "python": ["python", "py", "pytest", "pip", "pyproject"],
            "javascript": ["javascript", "js", "npm", "node", "react"],
            "typescript": ["typescript", "ts", "tsc", "type"],
            "testing": ["test", "spec", "pytest", "jest", "coverage"],
            "ci_cd": ["ci", "cd", "github actions", "workflow", "pipeline"],
            "documentation": ["docs", "readme", "documentation", "md"],
            "type_checking": ["type", "mypy", "typing", "annotation"],
        }

        # 複雑度判定キーワード
        self.complexity_indicators = {
            "high": ["refactor", "architecture", "breaking change", "migration"],
            "medium": ["feature", "enhancement", "improvement", "update"],
            "low": ["fix", "bug", "typo", "documentation", "format"],
        }

    async def analyze_issue(
        self, issue_number: int, prompt_info: dict[str, Any]
    ) -> dict[str, Any]:
        """
        GitHub Issue分析

        Args:
            issue_number: Issue番号
            prompt_info: プロンプト解析結果

        Returns:
            分析結果
        """
        self.log_info(f"Analyzing issue #{issue_number}")

        try:
            # GitHub CLI でIssue情報取得
            issue_data = await self._fetch_issue_data(issue_number)

            if not issue_data:
                return self._create_error_analysis("Failed to fetch issue data")

            # Issue内容分析
            analysis = self._analyze_issue_content(issue_data, prompt_info)

            # 解決戦略提案
            strategy = self._propose_resolution_strategy(analysis)

            # 結果統合
            result = {
                "success": True,
                "issue_number": issue_number,
                "title": issue_data.get("title", ""),
                "body": issue_data.get("body", ""),
                "labels": issue_data.get("labels", []),
                "state": issue_data.get("state", "open"),
                "analysis": analysis,
                "strategy": strategy,
                "estimated_time": self._estimate_time(analysis),
                "required_skills": self._identify_required_skills(analysis),
            }

            self.log_info(f"Analysis completed for issue #{issue_number}")
            return result

        except Exception as e:
            error_info = self.handle_exception(e, f"analyze_issue_{issue_number}")
            return self._create_error_analysis(
                f"Analysis failed: {error_info['error_message']}"
            )

    async def _fetch_issue_data(self, issue_number: int) -> dict[str, Any] | None:
        """GitHub CLI でIssue情報取得"""
        try:
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "view",
                    str(issue_number),
                    "--json",
                    "title,body,labels,state",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            issue_data = json.loads(result.stdout)
            self.log_info(f"Successfully fetched issue #{issue_number} data")
            return issue_data

        except subprocess.CalledProcessError as e:
            self.log_error(f"Failed to fetch issue #{issue_number}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.log_error(f"Failed to parse issue #{issue_number} JSON: {e}")
            return None

    def _analyze_issue_content(
        self, issue_data: dict[str, Any], prompt_info: dict[str, Any]
    ) -> dict[str, Any]:
        """Issue内容分析"""
        title = issue_data.get("title", "").lower()
        body = issue_data.get("body", "").lower()
        content = f"{title} {body}"

        # 技術要素特定
        technologies = []
        for tech, keywords in self.tech_keywords.items():
            if any(keyword in content for keyword in keywords):
                technologies.append(tech)

        # 複雑度判定
        complexity = self._estimate_complexity(content)

        # Issue種類判定
        issue_type = self._determine_issue_type(title, issue_data.get("labels", []))

        return {
            "type": issue_type,
            "complexity": complexity,
            "technologies": technologies,
            "content_analysis": {
                "title_length": len(title),
                "body_length": len(body),
                "has_code_blocks": "```" in body,
                "has_links": "http" in body,
                "keyword_density": self._calculate_keyword_density(content),
            },
            "user_intent": prompt_info.get("intent", "solve"),
            "priority": prompt_info.get("priority", "medium"),
        }

    def _estimate_complexity(self, content: str) -> str:
        """複雑度推定"""
        complexity_scores = dict.fromkeys(self.complexity_indicators.keys(), 0)

        for level, keywords in self.complexity_indicators.items():
            for keyword in keywords:
                if keyword in content:
                    complexity_scores[level] += 1

        # 最高スコアの複雑度を選択
        max_score = max(complexity_scores.values())
        if max_score > 0:
            for level, score in complexity_scores.items():
                if score == max_score:
                    return level

        return "medium"  # デフォルト

    def _determine_issue_type(self, title: str, labels: list[dict[str, Any]]) -> str:
        """Issue種類判定"""
        # ラベルベースの判定
        label_names = [label.get("name", "").lower() for label in labels]

        type_mapping = {
            "bug": ["bug", "error", "issue"],
            "feature": ["feature", "enhancement", "improvement"],
            "documentation": ["documentation", "docs"],
            "test": ["test", "testing"],
            "refactor": ["refactor", "cleanup", "tech debt"],
        }

        for issue_type, keywords in type_mapping.items():
            if any(keyword in label_names for keyword in keywords):
                return issue_type

        # タイトルベースの判定
        if any(keyword in title for keyword in ["fix", "bug", "error"]):
            return "bug"
        elif any(keyword in title for keyword in ["feat", "add", "implement"]):
            return "feature"
        elif any(keyword in title for keyword in ["docs", "readme"]):
            return "documentation"

        return "unknown"

    def _propose_resolution_strategy(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """解決戦略提案"""
        issue_type = analysis["type"]
        complexity = analysis["complexity"]
        technologies = analysis["technologies"]

        # 基本戦略
        base_strategies = {
            "bug": "bug_fix",
            "feature": "implementation",
            "documentation": "documentation_update",
            "test": "test_improvement",
            "refactor": "code_refactoring",
        }

        strategy = base_strategies.get(issue_type, "investigation")

        # アクションシーケンス生成
        action_sequence = self._generate_action_sequence(
            issue_type, complexity, technologies
        )

        return {
            "recommended_approach": strategy,
            "action_sequence": action_sequence,
            "success_criteria": self._define_success_criteria(issue_type),
            "estimated_steps": len(action_sequence),
            "risk_factors": self._identify_risk_factors(complexity, technologies),
        }

    def _generate_action_sequence(
        self, issue_type: str, complexity: str, technologies: list[str]
    ) -> list[dict[str, Any]]:
        """アクションシーケンス生成"""
        base_sequence = [
            {
                "step": 1,
                "action": {
                    "type": "investigation",
                    "description": "Issue content analysis",
                },
            },
            {
                "step": 2,
                "action": {
                    "type": "planning",
                    "description": "Resolution plan creation",
                },
            },
            {
                "step": 3,
                "action": {
                    "type": "implementation",
                    "description": "Solution implementation",
                },
            },
            {
                "step": 4,
                "action": {"type": "validation", "description": "Solution validation"},
            },
        ]

        # 技術特有のステップ追加
        if "type_checking" in technologies:
            base_sequence.insert(
                2,
                {
                    "step": 2.5,
                    "action": {
                        "type": "type_checking",
                        "description": "Type checking fixes",
                    },
                },
            )

        if "testing" in technologies:
            base_sequence.insert(
                -1,
                {
                    "step": 3.5,
                    "action": {"type": "testing", "description": "Test improvements"},
                },
            )

        return base_sequence

    def _define_success_criteria(self, issue_type: str) -> list[str]:
        """成功基準定義"""
        base_criteria = [
            "Issue requirements met",
            "Code quality maintained",
            "No breaking changes introduced",
        ]

        type_specific = {
            "bug": ["Bug completely fixed", "Regression tests added"],
            "feature": ["Feature fully implemented", "Tests cover new functionality"],
            "documentation": ["Documentation updated", "Examples provided"],
            "test": ["Test coverage improved", "Tests pass consistently"],
        }

        return base_criteria + type_specific.get(issue_type, [])

    def _identify_risk_factors(
        self, complexity: str, technologies: list[str]
    ) -> list[str]:
        """リスク要因特定"""
        risks = []

        if complexity == "high":
            risks.append("High complexity may require extensive testing")

        if "type_checking" in technologies:
            risks.append("Type checking changes may affect multiple files")

        if "ci_cd" in technologies:
            risks.append("CI/CD changes may impact deployment pipeline")

        return risks

    def _estimate_time(self, analysis: dict[str, Any]) -> int:
        """作業時間推定（分）"""
        base_time = {"low": 60, "medium": 120, "high": 240}

        complexity = analysis["complexity"]
        time_estimate = base_time.get(complexity, 120)

        # 技術要素による調整
        if len(analysis["technologies"]) > 3:
            time_estimate *= 1.5

        return int(time_estimate)

    def _identify_required_skills(self, analysis: dict[str, Any]) -> list[str]:
        """必要スキル特定"""
        skills = ["problem_solving", "code_review"]

        tech_skills = {
            "python": "python_development",
            "javascript": "javascript_development",
            "typescript": "typescript_development",
            "testing": "test_writing",
            "ci_cd": "devops",
            "documentation": "technical_writing",
        }

        for tech in analysis["technologies"]:
            if tech in tech_skills:
                skills.append(tech_skills[tech])

        return list(set(skills))

    def _calculate_keyword_density(self, content: str) -> dict[str, int]:
        """キーワード密度計算"""
        density = {}

        for category, keywords in self.tech_keywords.items():
            count = sum(content.count(keyword) for keyword in keywords)
            density[category] = count

        return density

    def _create_error_analysis(self, error_message: str) -> dict[str, Any]:
        """エラー分析結果作成"""
        return {
            "success": False,
            "error": error_message,
            "issue_number": None,
            "title": "",
            "analysis": {},
            "strategy": {},
            "estimated_time": 0,
            "required_skills": [],
        }
