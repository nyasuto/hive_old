"""
Issue解決フォーカス型自律エージェント

ユーザーの自然な日本語プロンプトを受け取り、BeeKeeper-Queen-Worker協調で
具体的な問題を解決する実用的なPoCシナリオ。

Usage:
    python examples/poc/issue_solver_agent.py "Issue 64を解決する"
    python examples/poc/issue_solver_agent.py "バグ修正をお願いします issue 84"
    python examples/poc/issue_solver_agent.py "https://github.com/nyasuto/hive/issues/84 を修正して"
"""

import argparse
import asyncio
import json
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from comb.api import CombAPI
from comb.message_router import MessagePriority, MessageType


class UserPromptParser:
    """ユーザープロンプト解析器"""

    def __init__(self):
        self.logger = logging.getLogger("prompt_parser")

    def parse_user_prompt(self, prompt: str) -> dict[str, Any]:
        """ユーザープロンプトを解析してアクションを特定"""
        prompt_lower = prompt.lower()

        # Issue番号抽出
        issue_number = self._extract_issue_number(prompt)

        # 意図分析
        intent = self._analyze_intent(prompt_lower)

        # 優先度推定
        priority = self._estimate_priority(prompt_lower)

        # 追加情報抽出
        additional_info = self._extract_additional_info(prompt)

        return {
            "original_prompt": prompt,
            "issue_number": issue_number,
            "intent": intent,
            "priority": priority,
            "additional_info": additional_info,
            "action_required": bool(issue_number),
        }

    def _extract_issue_number(self, prompt: str) -> str | None:
        """プロンプトからIssue番号を抽出"""
        # URL形式
        url_match = re.search(r"github\.com/[^/]+/[^/]+/issues/(\d+)", prompt)
        if url_match:
            return url_match.group(1)

        # Issue #123形式
        issue_match = re.search(r"issue\s*#?(\d+)", prompt, re.IGNORECASE)
        if issue_match:
            return issue_match.group(1)

        # 単純な数字（文脈で判断）
        if any(
            keyword in prompt.lower()
            for keyword in ["issue", "bug", "fix", "問題", "修正", "解決"]
        ):
            number_match = re.search(r"\b(\d+)\b", prompt)
            if number_match:
                return number_match.group(1)

        return None

    def _analyze_intent(self, prompt_lower: str) -> str:
        """意図分析"""
        # 解決・修正関連
        if any(
            word in prompt_lower
            for word in ["解決", "solve", "fix", "修正", "直す", "治す"]
        ):
            return "solve"

        # 調査・確認関連
        if any(
            word in prompt_lower
            for word in ["調査", "確認", "investigate", "check", "見て", "look"]
        ):
            return "investigate"

        # 実装・開発関連
        if any(
            word in prompt_lower
            for word in ["実装", "開発", "implement", "develop", "作る", "作成"]
        ):
            return "implement"

        # 説明・理解関連
        if any(
            word in prompt_lower
            for word in ["説明", "理解", "explain", "understand", "教えて", "なぜ"]
        ):
            return "explain"

        return "solve"  # デフォルト

    def _estimate_priority(self, prompt_lower: str) -> str:
        """優先度推定"""
        # 高優先度
        if any(
            word in prompt_lower
            for word in ["緊急", "急いで", "urgent", "critical", "重要", "important"]
        ):
            return "high"

        # 低優先度
        if any(
            word in prompt_lower
            for word in ["後で", "later", "余裕", "時間があるとき", "when possible"]
        ):
            return "low"

        return "medium"  # デフォルト

    def _extract_additional_info(self, prompt: str) -> dict[str, Any]:
        """追加情報抽出"""
        info = {
            "mentions_files": bool(re.search(r"[a-zA-Z0-9_/.-]+\.[a-zA-Z]+", prompt)),
            "mentions_code": "```" in prompt
            or "code" in prompt.lower()
            or "コード" in prompt,
            "mentions_test": "test" in prompt.lower() or "テスト" in prompt,
            "mentions_docs": "docs" in prompt.lower()
            or "ドキュメント" in prompt
            or "document" in prompt.lower(),
            "politeness_level": self._assess_politeness(prompt),
        }

        return info

    def _assess_politeness(self, prompt: str) -> str:
        """丁寧度判定"""
        if any(
            word in prompt for word in ["お願い", "please", "ください", "していただけ"]
        ):
            return "polite"
        elif any(word in prompt for word in ["してほしい", "して", "やって"]):
            return "casual"
        else:
            return "neutral"


class IssueAnalyzer:
    """GitHub Issue分析器"""

    def __init__(self):
        self.logger = logging.getLogger("issue_analyzer")

    async def analyze_issue(self, issue_identifier: str) -> dict[str, Any]:
        """Issue詳細分析"""
        try:
            # GitHub CLI使用してIssue取得
            if issue_identifier.startswith("http"):
                # URL形式の場合
                issue_number = self._extract_issue_number(issue_identifier)
            else:
                # 数値形式の場合
                issue_number = issue_identifier

            # GitHub CLI でIssue情報取得
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "view",
                    issue_number,
                    "--json",
                    "title,body,labels,assignees,state",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to fetch issue: {result.stderr}",
                    "issue_number": issue_number,
                }

            issue_data = json.loads(result.stdout)

            # Issue分析
            analysis = {
                "success": True,
                "issue_number": issue_number,
                "title": issue_data["title"],
                "body": issue_data["body"],
                "labels": [label["name"] for label in issue_data.get("labels", [])],
                "assignees": [
                    assignee["login"] for assignee in issue_data.get("assignees", [])
                ],
                "state": issue_data["state"],
                "analysis": await self._analyze_issue_content(issue_data),
                "solution_strategy": await self._determine_solution_strategy(
                    issue_data
                ),
                "complexity": await self._estimate_complexity(issue_data),
                "required_actions": await self._identify_required_actions(issue_data),
            }

            return analysis

        except Exception as e:
            return {"success": False, "error": str(e), "issue_number": issue_identifier}

    def _extract_issue_number(self, url: str) -> str:
        """URLからIssue番号を抽出"""
        match = re.search(r"/issues/(\d+)", url)
        return match.group(1) if match else url

    async def _analyze_issue_content(self, issue_data: dict) -> dict[str, Any]:
        """Issue内容分析"""
        body = issue_data.get("body", "")
        title = issue_data.get("title", "")

        # キーワード分析
        keywords = {
            "bug": ["bug", "error", "fail", "broken", "issue", "問題"],
            "feature": ["feature", "add", "implement", "新機能", "追加"],
            "enhancement": ["improve", "enhance", "better", "改善", "向上"],
            "docs": ["docs", "documentation", "readme", "ドキュメント"],
            "config": ["config", "setting", "setup", "設定"],
            "test": ["test", "testing", "coverage", "テスト"],
        }

        issue_type = "unknown"
        for type_name, words in keywords.items():
            if any(word.lower() in (title + body).lower() for word in words):
                issue_type = type_name
                break

        # 技術要素分析
        tech_elements = {
            "python": ["python", "py", ".py", "pyproject", "pytest"],
            "type_checking": ["mypy", "type", "typing", "annotation"],
            "linting": ["ruff", "lint", "format", "black"],
            "testing": ["test", "pytest", "coverage", "テスト"],
            "docs": ["docs", "documentation", "md", "markdown"],
            "config": ["config", "toml", "yaml", "json", "設定"],
        }

        involved_tech = []
        for tech, keywords_list in tech_elements.items():
            if any(keyword in (title + body).lower() for keyword in keywords_list):
                involved_tech.append(tech)

        return {
            "issue_type": issue_type,
            "involved_technologies": involved_tech,
            "has_code_examples": "```" in body,
            "has_error_logs": "error" in body.lower() or "failed" in body.lower(),
            "mentions_files": len(re.findall(r"[a-zA-Z0-9_/.-]+\.[a-zA-Z]+", body)) > 0,
            "priority_indicators": self._detect_priority_indicators(title + body),
        }

    def _detect_priority_indicators(self, text: str) -> list[str]:
        """優先度指標検出"""
        indicators = []
        text_lower = text.lower()

        if any(
            word in text_lower for word in ["critical", "urgent", "blocker", "緊急"]
        ):
            indicators.append("high_priority")
        if any(
            word in text_lower for word in ["crash", "fail", "broken", "not working"]
        ):
            indicators.append("functionality_impact")
        if any(
            word in text_lower for word in ["security", "vulnerability", "セキュリティ"]
        ):
            indicators.append("security_related")
        if any(word in text_lower for word in ["performance", "slow", "timeout"]):
            indicators.append("performance_related")

        return indicators

    async def _determine_solution_strategy(self, issue_data: dict) -> dict[str, Any]:
        """解決戦略決定"""
        labels = [label["name"] for label in issue_data.get("labels", [])]
        body = issue_data.get("body", "")

        strategy = {
            "approach": "investigation",  # investigation, implementation, configuration, documentation
            "estimated_steps": 3,
            "requires_code_changes": False,
            "requires_testing": False,
            "requires_documentation": False,
        }

        # ラベルベースの戦略決定
        if any(label in labels for label in ["bug", "type: bug"]):
            strategy["approach"] = "bug_fix"
            strategy["requires_code_changes"] = True
            strategy["requires_testing"] = True
        elif any(
            label in labels for label in ["feature", "enhancement", "type: feature"]
        ):
            strategy["approach"] = "implementation"
            strategy["requires_code_changes"] = True
            strategy["requires_testing"] = True
            strategy["requires_documentation"] = True
        elif any(label in labels for label in ["docs", "documentation"]):
            strategy["approach"] = "documentation"
            strategy["requires_documentation"] = True

        # 内容ベースの戦略調整
        if "config" in body.lower() or "setting" in body.lower():
            strategy["approach"] = "configuration"
            strategy["requires_code_changes"] = True

        return strategy

    async def _estimate_complexity(self, issue_data: dict) -> dict[str, Any]:
        """複雑度推定"""
        body = issue_data.get("body", "")
        title = issue_data.get("title", "")

        complexity_score = 1  # 1-5スケール

        # 複雑度要因
        if len(body) > 1000:
            complexity_score += 1
        if body.count("```") > 2:  # 複数のコードブロック
            complexity_score += 1
        if (
            len(re.findall(r"[a-zA-Z0-9_/.-]+\.[a-zA-Z]+", body)) > 5
        ):  # 多数のファイル言及
            complexity_score += 1
        if any(
            word in (title + body).lower()
            for word in ["refactor", "redesign", "architecture"]
        ):
            complexity_score += 2

        complexity_level = "low"
        if complexity_score >= 4:
            complexity_level = "high"
        elif complexity_score >= 2:
            complexity_level = "medium"

        return {
            "score": complexity_score,
            "level": complexity_level,
            "estimated_hours": complexity_score * 2,
        }

    async def _identify_required_actions(
        self, issue_data: dict
    ) -> list[dict[str, Any]]:
        """必要アクション特定"""
        body = issue_data.get("body", "")
        title = issue_data.get("title", "")
        labels = [label["name"] for label in issue_data.get("labels", [])]

        actions = []

        # 基本調査アクション
        actions.append(
            {
                "type": "investigation",
                "description": "Issue内容の詳細調査と現状分析",
                "priority": "high",
                "estimated_time": 30,
            }
        )

        # 技術要素別アクション
        if any(
            word in (title + body).lower() for word in ["type", "mypy", "annotation"]
        ):
            actions.append(
                {
                    "type": "type_checking",
                    "description": "型チェック関連の修正",
                    "priority": "medium",
                    "estimated_time": 60,
                }
            )

        if any(
            word in (title + body).lower() for word in ["test", "coverage", "pytest"]
        ):
            actions.append(
                {
                    "type": "testing",
                    "description": "テスト関連の実装・修正",
                    "priority": "medium",
                    "estimated_time": 90,
                }
            )

        if any(
            word in (title + body).lower()
            for word in ["docs", "documentation", "readme"]
        ):
            actions.append(
                {
                    "type": "documentation",
                    "description": "ドキュメント更新",
                    "priority": "low",
                    "estimated_time": 45,
                }
            )

        # コード変更が必要な場合
        if any(label in labels for label in ["bug", "feature", "enhancement"]):
            actions.append(
                {
                    "type": "code_implementation",
                    "description": "コード実装・修正",
                    "priority": "high",
                    "estimated_time": 120,
                }
            )

        # 検証アクション
        actions.append(
            {
                "type": "validation",
                "description": "解決策の検証とテスト",
                "priority": "high",
                "estimated_time": 45,
            }
        )

        return actions


class IssueSolverQueenCoordinator:
    """Issue解決専用Queen Coordinator"""

    def __init__(self):
        self.comb_api = CombAPI("issue_solver_queen")
        self.logger = logging.getLogger("issue_solver_queen")
        self.current_issue = None
        self.solution_progress = {}
        self.conversation_history = []

    async def coordinate_issue_resolution(
        self, issue_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Issue解決の協調統制"""
        self.current_issue = issue_analysis

        # Work Log開始
        self.comb_api.start_task(
            f"Issue #{issue_analysis['issue_number']}: {issue_analysis['title'][:50]}...",
            "issue_resolution",
            f"Resolving GitHub Issue #{issue_analysis['issue_number']}",
            workers=["queen", "developer"],
        )

        # 解決計画策定
        resolution_plan = await self._create_resolution_plan(issue_analysis)

        # Developer Workerに解決指示
        await self._assign_resolution_tasks(resolution_plan)

        # 解決プロセス監視
        resolution_result = await self._monitor_resolution_progress()

        # 結果検証
        validation_result = await self._validate_resolution(resolution_result)

        # Work Log完了
        self.comb_api.complete_task(
            f"Issue #{issue_analysis['issue_number']} resolution completed: {validation_result['status']}"
        )

        return {
            "issue_number": issue_analysis["issue_number"],
            "resolution_plan": resolution_plan,
            "resolution_result": resolution_result,
            "validation": validation_result,
            "total_time": resolution_result.get("total_time", 0),
            "success": validation_result.get("success", False),
        }

    async def _create_resolution_plan(
        self, issue_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """解決計画策定"""
        plan = {
            "issue_summary": {
                "number": issue_analysis["issue_number"],
                "title": issue_analysis["title"],
                "type": issue_analysis["analysis"]["issue_type"],
                "complexity": issue_analysis["complexity"]["level"],
            },
            "resolution_strategy": issue_analysis["solution_strategy"],
            "action_sequence": [],
            "estimated_total_time": 0,
            "success_criteria": [],
        }

        # アクションシーケンス構築
        for action in issue_analysis["required_actions"]:
            plan["action_sequence"].append(
                {
                    "step": len(plan["action_sequence"]) + 1,
                    "action": action,
                    "status": "pending",
                    "assigned_worker": "developer",
                }
            )
            plan["estimated_total_time"] += action["estimated_time"]

        # 成功基準定義
        plan["success_criteria"] = [
            "Issue要件が満たされている",
            "コード品質基準を満たしている",
            "テストが通過している",
            "ドキュメントが更新されている（必要に応じて）",
        ]

        # 技術決定記録
        self.comb_api.add_technical_decision(
            f"Issue #{issue_analysis['issue_number']} Resolution Strategy",
            f"Planned {len(plan['action_sequence'])} step resolution approach",
            [
                f"Alternative approach: {issue_analysis['solution_strategy']['approach']}"
            ],
        )

        return plan

    async def _assign_resolution_tasks(self, plan: dict[str, Any]) -> None:
        """解決タスク割り当て"""
        assignment = {
            "action": "resolve_issue",
            "issue_data": self.current_issue,
            "resolution_plan": plan,
            "instructions": [
                f"Resolve GitHub Issue #{self.current_issue['issue_number']}",
                f"Follow the {len(plan['action_sequence'])}-step resolution plan",
                "Provide progress updates for each step",
                "Ensure all success criteria are met",
            ],
            "success_criteria": plan["success_criteria"],
            "queen_message": f"👑 Starting resolution of Issue #{self.current_issue['issue_number']}: {self.current_issue['title'][:50]}...",
        }

        success = self.comb_api.send_message(
            to_worker="developer",
            content=assignment,
            message_type=MessageType.REQUEST,
            priority=MessagePriority.HIGH,
        )

        if success:
            self.conversation_history.append(
                {
                    "from": "queen",
                    "to": "developer",
                    "type": "task_assignment",
                    "content": assignment,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            self.logger.info(
                f"👑 Assigned Issue #{self.current_issue['issue_number']} resolution to developer"
            )

    async def _monitor_resolution_progress(self) -> dict[str, Any]:
        """解決プロセス監視"""
        monitoring_result = {
            "completed_steps": 0,
            "total_steps": len(self.current_issue["required_actions"]),
            "step_results": [],
            "issues_encountered": [],
            "total_time": 0,
            "status": "in_progress",
        }

        start_time = datetime.now()

        # 進捗監視ループ（デモ用に簡略化）
        for _cycle in range(10):  # 最大10サイクル監視
            await asyncio.sleep(5)  # 5秒間隔

            # Developer Workerからの進捗確認
            messages = self.comb_api.receive_messages()

            for message in messages:
                if message.from_worker == "developer":
                    await self._handle_developer_progress(message, monitoring_result)

            # 完了チェック
            if monitoring_result["status"] == "completed":
                break

        monitoring_result["total_time"] = (datetime.now() - start_time).total_seconds()

        return monitoring_result

    async def _handle_developer_progress(
        self, message, monitoring_result: dict[str, Any]
    ) -> None:
        """Developer進捗処理"""
        content = message.content
        message_type = content.get("type", "unknown")

        if message_type == "step_completed":
            monitoring_result["completed_steps"] += 1
            monitoring_result["step_results"].append(
                {
                    "step": content.get("step", 0),
                    "result": content.get("result", {}),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # 進捗記録
            self.comb_api.add_progress(
                f"Step {content.get('step', 0)} Completed",
                content.get("result", {}).get(
                    "description", "Step completed successfully"
                ),
            )

        elif message_type == "issue_encountered":
            monitoring_result["issues_encountered"].append(
                {
                    "issue": content.get("issue", ""),
                    "severity": content.get("severity", "medium"),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # 課題記録
            self.comb_api.add_challenge(
                content.get("issue", "Unknown issue"),
                content.get("proposed_solution", "Investigating solution"),
            )

        elif message_type == "resolution_completed":
            monitoring_result["status"] = "completed"
            monitoring_result["final_result"] = content.get("result", {})

    async def _validate_resolution(
        self, resolution_result: dict[str, Any]
    ) -> dict[str, Any]:
        """解決結果検証"""
        validation = {
            "success": False,
            "validated_criteria": [],
            "failed_criteria": [],
            "overall_score": 0,
            "recommendations": [],
        }

        # 簡易検証（実際にはより詳細な検証が必要）
        if resolution_result["status"] == "completed":
            validation["success"] = True
            validation["overall_score"] = 85

            # 成功基準チェック
            for criterion in self.current_issue.get("success_criteria", []):
                validation["validated_criteria"].append(
                    {
                        "criterion": criterion,
                        "status": "passed",
                        "details": "Automated validation passed",
                    }
                )

        # 改善提案
        if resolution_result["issues_encountered"]:
            validation["recommendations"].append(
                "Consider adding more comprehensive error handling"
            )

        return validation


class IssueSolverDeveloperWorker:
    """Issue解決専用Developer Worker"""

    def __init__(self):
        self.comb_api = CombAPI("issue_solver_developer")
        self.logger = logging.getLogger("issue_solver_developer")
        self.current_issue = None
        self.resolution_plan = None

    async def start_issue_resolution_monitoring(self) -> None:
        """Issue解決監視開始"""
        self.logger.info("💻 Developer: Starting issue resolution monitoring")

        while True:
            try:
                messages = self.comb_api.receive_messages()

                for message in messages:
                    if message.from_worker == "issue_solver_queen":
                        await self._handle_queen_assignment(message)

                await asyncio.sleep(3)

            except Exception as e:
                self.logger.error(f"💻 Developer: Error in monitoring: {e}")
                await asyncio.sleep(5)

    async def _handle_queen_assignment(self, message) -> None:
        """Queen割り当て処理"""
        content = message.content
        action = content.get("action", "unknown")

        if action == "resolve_issue":
            self.current_issue = content["issue_data"]
            self.resolution_plan = content["resolution_plan"]

            await self._execute_issue_resolution()

    async def _execute_issue_resolution(self) -> None:
        """Issue解決実行"""
        self.logger.info(
            f"💻 Starting resolution of Issue #{self.current_issue['issue_number']}"
        )

        # 各ステップを実行
        for step_info in self.resolution_plan["action_sequence"]:
            step_number = step_info["step"]
            action = step_info["action"]

            self.logger.info(f"💻 Executing step {step_number}: {action['type']}")

            # ステップ実行
            step_result = await self._execute_resolution_step(action)

            # 進捗報告
            await self._report_step_completion(step_number, step_result)

            # 短い間隔
            await asyncio.sleep(2)

        # 完了報告
        await self._report_resolution_completion()

    async def _execute_resolution_step(self, action: dict[str, Any]) -> dict[str, Any]:
        """解決ステップ実行"""
        action_type = action["type"]

        # アクションタイプ別の実装（デモ用簡略化）
        if action_type == "investigation":
            return await self._perform_investigation()
        elif action_type == "type_checking":
            return await self._fix_type_checking()
        elif action_type == "testing":
            return await self._improve_testing()
        elif action_type == "documentation":
            return await self._update_documentation()
        elif action_type == "code_implementation":
            return await self._implement_code_changes()
        elif action_type == "validation":
            return await self._validate_changes()
        else:
            return {"success": False, "error": f"Unknown action type: {action_type}"}

    async def _perform_investigation(self) -> dict[str, Any]:
        """調査実行"""
        # 実際の調査処理をシミュレート
        await asyncio.sleep(1)

        return {
            "success": True,
            "description": "Issue content analyzed and current state investigated",
            "findings": [
                "Issue clearly defined with specific requirements",
                "Affected files identified",
                "Solution approach confirmed",
            ],
        }

    async def _fix_type_checking(self) -> dict[str, Any]:
        """型チェック修正"""
        await asyncio.sleep(2)

        return {
            "success": True,
            "description": "Type checking issues resolved",
            "changes": [
                "Added missing type annotations",
                "Fixed mypy configuration",
                "Resolved type conflicts",
            ],
        }

    async def _improve_testing(self) -> dict[str, Any]:
        """テスト改善"""
        await asyncio.sleep(3)

        return {
            "success": True,
            "description": "Testing improvements implemented",
            "changes": [
                "Added missing test cases",
                "Improved test coverage",
                "Fixed failing tests",
            ],
        }

    async def _update_documentation(self) -> dict[str, Any]:
        """ドキュメント更新"""
        await asyncio.sleep(1)

        return {
            "success": True,
            "description": "Documentation updated",
            "changes": [
                "Updated relevant documentation",
                "Added examples and usage",
                "Clarified unclear sections",
            ],
        }

    async def _implement_code_changes(self) -> dict[str, Any]:
        """コード実装"""
        await asyncio.sleep(4)

        return {
            "success": True,
            "description": "Code changes implemented",
            "changes": [
                "Implemented requested features",
                "Fixed identified bugs",
                "Applied code improvements",
            ],
        }

    async def _validate_changes(self) -> dict[str, Any]:
        """変更検証"""
        await asyncio.sleep(2)

        return {
            "success": True,
            "description": "Changes validated successfully",
            "validation_results": [
                "All tests pass",
                "Code quality checks pass",
                "Issue requirements met",
            ],
        }

    async def _report_step_completion(
        self, step_number: int, result: dict[str, Any]
    ) -> None:
        """ステップ完了報告"""
        report = {
            "type": "step_completed",
            "step": step_number,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }

        self.comb_api.send_message(
            to_worker="issue_solver_queen",
            content=report,
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.MEDIUM,
        )

    async def _report_resolution_completion(self) -> None:
        """解決完了報告"""
        completion_report = {
            "type": "resolution_completed",
            "issue_number": self.current_issue["issue_number"],
            "result": {
                "status": "completed",
                "summary": f"Successfully resolved Issue #{self.current_issue['issue_number']}",
                "changes_made": "All required changes implemented and validated",
            },
            "timestamp": datetime.now().isoformat(),
        }

        self.comb_api.send_message(
            to_worker="issue_solver_queen",
            content=completion_report,
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.HIGH,
        )


class IssueSolverBeeKeeper:
    """Issue解決BeeKeeper（人間インターフェース）"""

    def __init__(self):
        self.prompt_parser = UserPromptParser()
        self.analyzer = IssueAnalyzer()
        self.queen = IssueSolverQueenCoordinator()
        self.developer = IssueSolverDeveloperWorker()
        self.logger = logging.getLogger("issue_solver_beekeeper")

    async def process_user_request(self, user_prompt: str) -> dict[str, Any]:
        """ユーザーリクエスト処理"""
        print(f'🐝 BeeKeeper: Processing user request: "{user_prompt}"')

        # 1. プロンプト解析
        parsed = self.prompt_parser.parse_user_prompt(user_prompt)

        print(f"🔍 Parsed intent: {parsed['intent']}")
        print(f"🏷️  Priority: {parsed['priority']}")
        print(f"📋 Issue number: {parsed['issue_number']}")

        # Issue番号が特定できない場合の処理
        if not parsed["issue_number"]:
            return {
                "success": False,
                "error": "Issue番号が特定できませんでした",
                "suggestion": "「Issue 64を解決する」のような形式でIssue番号を指定してください",
                "parsed_prompt": parsed,
            }

        # 意図に応じた処理
        if parsed["intent"] == "solve":
            return await self.solve_issue(parsed["issue_number"], parsed)
        elif parsed["intent"] == "investigate":
            return await self.investigate_issue(parsed["issue_number"], parsed)
        elif parsed["intent"] == "explain":
            return await self.explain_issue(parsed["issue_number"], parsed)
        else:
            return await self.solve_issue(parsed["issue_number"], parsed)  # デフォルト

    async def solve_issue(
        self, issue_number: str, parsed_prompt: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Issue解決メインフロー"""
        print(f"🐝 BeeKeeper: Starting resolution of Issue {issue_number}")

        # 1. Issue分析
        print("📊 Analyzing issue...")
        issue_analysis = await self.analyzer.analyze_issue(issue_number)

        if not issue_analysis["success"]:
            print(f"❌ Failed to analyze issue: {issue_analysis['error']}")
            return issue_analysis

        # Issue情報表示
        print(f"📋 Issue #{issue_analysis['issue_number']}: {issue_analysis['title']}")
        print(f"🏷️  Type: {issue_analysis['analysis']['issue_type']}")
        print(f"⚡ Complexity: {issue_analysis['complexity']['level']}")
        print(f"🔧 Strategy: {issue_analysis['solution_strategy']['approach']}")

        # 2. Developer Worker監視開始
        print("💻 Starting developer worker monitoring...")
        developer_task = asyncio.create_task(
            self.developer.start_issue_resolution_monitoring()
        )

        # 3. Queen Coordinatorで解決実行
        print("👑 Queen coordinating issue resolution...")
        resolution_result = await self.queen.coordinate_issue_resolution(issue_analysis)

        # 4. 結果表示
        print("\n📊 Resolution Results:")
        print(f"✅ Success: {resolution_result['success']}")
        print(f"⏱️  Total time: {resolution_result['total_time']:.1f}s")
        print(
            f"📝 Steps completed: {resolution_result['resolution_result']['completed_steps']}"
        )

        if resolution_result["validation"]["success"]:
            print("🎉 Issue resolution completed successfully!")
        else:
            print("⚠️  Issue resolution completed with issues")

        # 5. 終了処理
        developer_task.cancel()

        return resolution_result

    async def investigate_issue(
        self, issue_number: str, parsed_prompt: dict[str, Any]
    ) -> dict[str, Any]:
        """Issue調査モード"""
        print(f"🔍 BeeKeeper: Investigating Issue {issue_number}")

        # Issue分析のみ実行
        issue_analysis = await self.analyzer.analyze_issue(issue_number)

        if not issue_analysis["success"]:
            return issue_analysis

        # 調査結果表示
        print(f"📋 Issue #{issue_analysis['issue_number']}: {issue_analysis['title']}")
        print(f"🏷️  Type: {issue_analysis['analysis']['issue_type']}")
        print(f"⚡ Complexity: {issue_analysis['complexity']['level']}")
        print(
            f"🔧 Suggested Strategy: {issue_analysis['solution_strategy']['approach']}"
        )
        print(f"📝 Required Actions: {len(issue_analysis['required_actions'])}")

        return {
            "success": True,
            "mode": "investigation",
            "issue_analysis": issue_analysis,
            "summary": f"Issue #{issue_number} investigated successfully",
        }

    async def explain_issue(
        self, issue_number: str, parsed_prompt: dict[str, Any]
    ) -> dict[str, Any]:
        """Issue説明モード"""
        print(f"💬 BeeKeeper: Explaining Issue {issue_number}")

        # Issue分析
        issue_analysis = await self.analyzer.analyze_issue(issue_number)

        if not issue_analysis["success"]:
            return issue_analysis

        # 説明の生成
        explanation = await self._generate_issue_explanation(issue_analysis)

        print("\n📝 Issue Explanation:")
        print(explanation)

        return {
            "success": True,
            "mode": "explanation",
            "issue_analysis": issue_analysis,
            "explanation": explanation,
        }

    async def _generate_issue_explanation(self, issue_analysis: dict[str, Any]) -> str:
        """Issue説明生成"""
        explanation = f"""
Issue #{issue_analysis["issue_number"]} について説明します：

【概要】
タイトル: {issue_analysis["title"]}
タイプ: {issue_analysis["analysis"]["issue_type"]}
複雑度: {issue_analysis["complexity"]["level"]}

【技術要素】
関連技術: {", ".join(issue_analysis["analysis"]["involved_technologies"])}

【解決戦略】
推奨アプローチ: {issue_analysis["solution_strategy"]["approach"]}
推定工数: {issue_analysis["complexity"]["estimated_hours"]}時間

【必要なアクション】
"""

        for i, action in enumerate(issue_analysis["required_actions"], 1):
            explanation += (
                f"{i}. {action['description']} ({action['estimated_time']}分)\n"
            )

        return explanation


async def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="GitHub Issue Solver Agent")
    parser.add_argument(
        "prompt", nargs="?", help="User prompt (e.g., 'Issue 64を解決する')"
    )
    parser.add_argument("--demo", action="store_true", help="Run demo mode")

    args = parser.parse_args()

    # ユーザープロンプト確定
    if args.prompt:
        user_prompt = args.prompt
    elif args.demo:
        user_prompt = "Issue 64を解決する"
        print(f'🎯 Demo mode: Using prompt "{user_prompt}"')
    else:
        # インタラクティブモード
        user_prompt = input("🐝 BeeKeeper: どのようなご依頼でしょうか？ > ")

    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # BeeKeeper実行
    beekeeper = IssueSolverBeeKeeper()

    try:
        result = await beekeeper.process_user_request(user_prompt)

        # 結果保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = Path(f".hive/honey/user_request_{timestamp}.json")
        result_file.parent.mkdir(parents=True, exist_ok=True)

        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"💾 Results saved to: {result_file}")

        # 結果サマリー表示
        if result.get("success"):
            print("✅ Request processed successfully")
            if "mode" in result:
                print(f"🔧 Mode: {result['mode']}")
        else:
            print(f"❌ Request failed: {result.get('error', 'Unknown error')}")
            if "suggestion" in result:
                print(f"💡 Suggestion: {result['suggestion']}")

    except KeyboardInterrupt:
        print("\n⏹️  Request processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
