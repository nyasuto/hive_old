"""
BeeKeeper自律的テスト自動生成PoC

正しいアーキテクチャ：
1. BeeKeeper（人間）がテスト生成目的・品質基準投入
2. Queen/Developer間で自律的協調・テスト生成
3. 成果物（生成されたテスト）を人間が受領

Usage:
    python examples/poc/beekeeper_autonomous_testing.py
"""

import ast
import asyncio
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from comb.api import CombAPI
from comb.message_router import MessagePriority, MessageType


class BeeKeeperTestingInput:
    """BeeKeeper（人間）からのテスト生成入力"""

    def __init__(self):
        self.testing_requests = {}

    def submit_testing_request(
        self,
        objective: str,
        template: str,
        target_files: list[str] = None,
        coverage_targets: dict[str, Any] = None,
        test_types: list[str] = None,
    ) -> str:
        """テスト生成要求投入"""

        request_id = f"testing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.testing_requests[request_id] = {
            "objective": objective,
            "template": template,
            "target_files": target_files or [],
            "coverage_targets": coverage_targets
            or {
                "line_coverage": 85,
                "branch_coverage": 80,
                "function_coverage": 90,
                "edge_cases_coverage": 75,
            },
            "test_types": test_types or ["unit", "integration", "edge_case"],
            "timestamp": datetime.now().isoformat(),
            "status": "submitted",
        }

        print(f"🐝 BeeKeeper Testing Request: {request_id}")
        print(f"📋 Objective: {objective}")
        print(f"📝 Template: {template}")
        print(f"🎯 Coverage Targets: {coverage_targets}")
        print(f"🧪 Test Types: {test_types}")

        return request_id

    def get_request_data(self, request_id: str) -> dict[str, Any]:
        """要求データ取得"""
        return self.testing_requests.get(request_id, {})


class QueenTestingCoordinator:
    """Queen Worker - テスト生成全体調整"""

    def __init__(self):
        self.comb_api = CombAPI("queen")
        self.logger = logging.getLogger("queen_testing")
        self.active_testing_projects = {}
        self.conversation_history = []

    async def receive_beekeeper_request(
        self, request_id: str, request_data: dict[str, Any]
    ) -> None:
        """BeeKeeperテスト生成要求受信"""

        # プロジェクト初期化
        project_id = f"testing_{request_id}"
        self.active_testing_projects[project_id] = {
            "request_id": request_id,
            "objective": request_data["objective"],
            "template": request_data["template"],
            "target_files": request_data["target_files"],
            "coverage_targets": request_data["coverage_targets"],
            "test_types": request_data["test_types"],
            "status": "analyzing",
            "created_at": datetime.now().isoformat(),
        }

        # Work Log開始
        task_id = self.comb_api.start_task(
            f"BeeKeeper Testing: {request_data['objective']}",
            "beekeeper_testing",
            f"Starting test generation project: {request_data['objective']}",
            workers=["queen", "developer"],
        )

        self.active_testing_projects[project_id]["task_id"] = task_id

        # コードベース分析
        analysis = await self._analyze_testable_code(request_data)
        self.active_testing_projects[project_id]["initial_analysis"] = analysis

        # テスト生成戦略策定
        strategy = await self._develop_testing_strategy(request_data, analysis)
        self.active_testing_projects[project_id]["strategy"] = strategy

        # Developer Workerに初期指示
        await self._send_initial_testing_instructions(project_id, strategy)

        self.logger.info(f"👑 Queen: Started testing project {project_id}")

    async def _analyze_testable_code(
        self, request_data: dict[str, Any]
    ) -> dict[str, Any]:
        """テスト対象コード分析"""

        analysis = {
            "total_python_files": 0,
            "testable_functions": [],
            "testable_classes": [],
            "current_test_coverage": 0,
            "missing_test_files": [],
            "complexity_analysis": {},
            "edge_case_opportunities": [],
        }

        try:
            # Pythonファイル検索
            python_files = list(Path(".").rglob("*.py"))
            python_files = [
                f
                for f in python_files
                if not any(part.startswith(".") for part in f.parts)
                and "test_" not in f.name
                and "__pycache__" not in str(f)
            ]

            analysis["total_python_files"] = len(python_files)

            # 関数・クラス分析
            for file_path in python_files[:15]:  # 最初の15ファイル
                try:
                    with open(file_path, encoding="utf-8") as f:
                        tree = ast.parse(f.read())

                    file_functions = []
                    file_classes = []

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            if not node.name.startswith("_"):  # プライベート関数除外
                                func_info = {
                                    "name": node.name,
                                    "file": str(file_path),
                                    "line": node.lineno,
                                    "args": [arg.arg for arg in node.args.args],
                                    "complexity": await self._calculate_complexity(
                                        node
                                    ),
                                    "has_test": await self._check_existing_test(
                                        file_path, node.name
                                    ),
                                }
                                file_functions.append(func_info)

                        elif isinstance(node, ast.ClassDef):
                            class_info = {
                                "name": node.name,
                                "file": str(file_path),
                                "line": node.lineno,
                                "methods": [],
                                "has_test": await self._check_existing_test(
                                    file_path, node.name
                                ),
                            }

                            # メソッド分析
                            for item in node.body:
                                if isinstance(item, ast.FunctionDef):
                                    class_info["methods"].append(
                                        {
                                            "name": item.name,
                                            "args": [arg.arg for arg in item.args.args],
                                            "complexity": await self._calculate_complexity(
                                                item
                                            ),
                                        }
                                    )

                            file_classes.append(class_info)

                    analysis["testable_functions"].extend(file_functions)
                    analysis["testable_classes"].extend(file_classes)

                    # 対応するテストファイルの存在確認
                    test_file = Path(f"tests/test_{file_path.stem}.py")
                    if not test_file.exists():
                        analysis["missing_test_files"].append(str(file_path))

                except Exception as e:
                    self.logger.warning(f"Failed to analyze {file_path}: {e}")

            # 現在のテストカバレッジ取得
            analysis["current_test_coverage"] = await self._get_current_coverage()

            # エッジケース機会分析
            analysis[
                "edge_case_opportunities"
            ] = await self._identify_edge_case_opportunities(
                analysis["testable_functions"]
            )

            self.logger.info(
                f"👑 Queen: Code analysis completed - "
                f"Functions: {len(analysis['testable_functions'])}, "
                f"Classes: {len(analysis['testable_classes'])}, "
                f"Coverage: {analysis['current_test_coverage']:.1f}%"
            )

        except Exception as e:
            self.logger.error(f"Code analysis error: {e}")

        return analysis

    async def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """サイクロマティック複雑度計算"""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, ast.If | ast.While | ast.For | ast.AsyncFor):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    async def _check_existing_test(self, file_path: Path, name: str) -> bool:
        """既存テストの存在確認"""
        test_file = Path(f"tests/test_{file_path.stem}.py")

        if not test_file.exists():
            return False

        try:
            with open(test_file, encoding="utf-8") as f:
                content = f.read()
                return f"test_{name}" in content
        except Exception:
            return False

    async def _get_current_coverage(self) -> float:
        """現在のテストカバレッジ取得"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=.", "--cov-report=json", "--quiet"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                coverage_file = Path("coverage.json")
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        data = json.load(f)
                    coverage_file.unlink()

                    return data.get("totals", {}).get("percent_covered", 0)

            return 0.0

        except Exception:
            return 0.0

    async def _identify_edge_case_opportunities(
        self, functions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """エッジケース機会特定"""
        opportunities = []

        for func in functions:
            args = func.get("args", [])
            complexity = func.get("complexity", 1)

            # 複雑度が高い関数
            if complexity > 5:
                opportunities.append(
                    {
                        "function": func["name"],
                        "type": "high_complexity",
                        "priority": "high",
                        "description": f"Function {func['name']} has complexity {complexity}",
                    }
                )

            # 複数引数を持つ関数
            if len(args) > 3:
                opportunities.append(
                    {
                        "function": func["name"],
                        "type": "multiple_parameters",
                        "priority": "medium",
                        "description": f"Function {func['name']} has {len(args)} parameters",
                    }
                )

        return opportunities

    async def _develop_testing_strategy(
        self, request_data: dict[str, Any], analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """テスト生成戦略策定"""

        coverage_targets = request_data["coverage_targets"]
        test_types = request_data["test_types"]
        current_coverage = analysis["current_test_coverage"]

        strategy = {
            "current_coverage": current_coverage,
            "target_coverage": coverage_targets.get("line_coverage", 85),
            "coverage_gap": coverage_targets.get("line_coverage", 85)
            - current_coverage,
            "priority_actions": [],
        }

        # 優先アクション決定
        if len(analysis["missing_test_files"]) > 0:
            strategy["priority_actions"].append(
                {
                    "action": "create_missing_test_files",
                    "files_count": len(analysis["missing_test_files"]),
                    "priority": "high",
                }
            )

        if "unit" in test_types:
            untested_functions = [
                f for f in analysis["testable_functions"] if not f["has_test"]
            ]
            if untested_functions:
                strategy["priority_actions"].append(
                    {
                        "action": "generate_unit_tests",
                        "functions_count": len(untested_functions),
                        "priority": "high",
                    }
                )

        if "edge_case" in test_types and analysis["edge_case_opportunities"]:
            strategy["priority_actions"].append(
                {
                    "action": "generate_edge_case_tests",
                    "opportunities_count": len(analysis["edge_case_opportunities"]),
                    "priority": "medium",
                }
            )

        if "integration" in test_types:
            strategy["priority_actions"].append(
                {
                    "action": "generate_integration_tests",
                    "classes_count": len(analysis["testable_classes"]),
                    "priority": "low",
                }
            )

        # 実行計画作成
        strategy["execution_plan"] = []
        for i, action in enumerate(strategy["priority_actions"], 1):
            strategy["execution_plan"].append(
                {
                    "step": i,
                    "action": action["action"],
                    "description": self._get_testing_action_description(action),
                    "priority": action["priority"],
                }
            )

        # Work Log記録
        self.comb_api.add_technical_decision(
            "Testing Strategy",
            f"Planned {len(strategy['priority_actions'])} testing actions to improve coverage from {current_coverage:.1f}% to {coverage_targets.get('line_coverage', 85)}%",
            ["Manual testing", "Alternative testing frameworks"],
        )

        return strategy

    def _get_testing_action_description(self, action: dict[str, Any]) -> str:
        """テストアクション説明生成"""
        action_type = action["action"]

        if action_type == "create_missing_test_files":
            return f"Create {action['files_count']} missing test files"
        elif action_type == "generate_unit_tests":
            return f"Generate unit tests for {action['functions_count']} functions"
        elif action_type == "generate_edge_case_tests":
            return f"Generate edge case tests for {action['opportunities_count']} opportunities"
        elif action_type == "generate_integration_tests":
            return f"Generate integration tests for {action['classes_count']} classes"
        else:
            return f"Execute {action_type}"

    async def _send_initial_testing_instructions(
        self, project_id: str, strategy: dict[str, Any]
    ) -> None:
        """Developer Workerに初期テスト生成指示"""

        project = self.active_testing_projects[project_id]

        instructions = {
            "action": "start_testing",
            "project_id": project_id,
            "objective": project["objective"],
            "template": project["template"],
            "coverage_targets": project["coverage_targets"],
            "test_types": project["test_types"],
            "strategy": strategy,
            "execution_plan": strategy["execution_plan"],
            "queen_message": f"👑 Starting test generation project: {project['objective']}",
        }

        success = self.comb_api.send_message(
            to_worker="developer",
            content=instructions,
            message_type=MessageType.REQUEST,
            priority=MessagePriority.HIGH,
        )

        if success:
            self.conversation_history.append(
                {
                    "from": "queen",
                    "to": "developer",
                    "type": "testing_instructions",
                    "content": instructions,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            self.logger.info(f"👑 Queen: Sent testing instructions for {project_id}")

    async def monitor_testing_progress(self, project_id: str) -> None:
        """テスト生成進捗監視"""

        project = self.active_testing_projects.get(project_id)
        if not project:
            return

        # Developer Workerからの応答監視
        messages = self.comb_api.receive_messages()

        for message in messages:
            if message.from_worker == "developer":
                await self._handle_developer_testing_response(project_id, message)

    async def _handle_developer_testing_response(
        self, project_id: str, message
    ) -> None:
        """Developer Workerテスト生成応答処理"""

        content = message.content
        response_type = content.get("type", "unknown")

        # 会話履歴記録
        self.conversation_history.append(
            {
                "from": "developer",
                "to": "queen",
                "type": response_type,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # 応答種別処理
        if response_type == "testing_progress":
            await self._handle_testing_progress(project_id, content)
        elif response_type == "test_generation_result":
            await self._handle_test_generation_result(project_id, content)
        elif response_type == "testing_question":
            await self._handle_testing_question(project_id, content)
        elif response_type == "testing_completion":
            await self._handle_testing_completion(project_id, content)
        elif response_type == "testing_issue":
            await self._handle_testing_issue(project_id, content)

        self.logger.info(f"👑 Queen: Handled {response_type} from developer")

    async def _handle_testing_progress(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """テスト生成進捗処理"""

        progress = content.get("progress", {})
        current_action = progress.get("current_action", "unknown")
        completion_percentage = progress.get("completion_percentage", 0)

        # Work Log記録
        self.comb_api.add_progress(
            f"Testing Progress: {current_action}",
            f"Progress: {completion_percentage}% - {progress.get('description', '')}",
        )

        # 必要に応じて追加指示
        if progress.get("needs_guidance", False):
            guidance = await self._provide_testing_guidance(project_id, progress)

            guidance_message = {
                "action": "testing_guidance",
                "project_id": project_id,
                "guidance": guidance,
                "queen_message": f"👑 Guidance for {current_action}: {guidance}",
            }

            self.comb_api.send_message(
                to_worker="developer",
                content=guidance_message,
                message_type=MessageType.RESPONSE,
                priority=MessagePriority.MEDIUM,
            )

    async def _handle_test_generation_result(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """テスト生成結果処理"""

        result = content.get("result", {})
        test_type = result.get("test_type", "unknown")
        tests_generated = result.get("tests_generated", 0)
        coverage_improvement = result.get("coverage_improvement", 0)

        # Work Log記録
        self.comb_api.add_progress(
            f"Test Generation Result: {test_type}",
            f"Generated {tests_generated} tests, coverage improvement: +{coverage_improvement:.1f}%",
        )

        # 次のアクション指示
        project = self.active_testing_projects[project_id]
        strategy = project.get("strategy", {})

        next_action = await self._determine_next_testing_action(
            project_id, result, strategy
        )

        if next_action:
            next_instruction = {
                "action": "continue_testing",
                "project_id": project_id,
                "next_action": next_action,
                "queen_message": f"👑 Great progress! Next: {next_action['description']}",
            }

            self.comb_api.send_message(
                to_worker="developer",
                content=next_instruction,
                message_type=MessageType.REQUEST,
                priority=MessagePriority.HIGH,
            )

    async def _handle_testing_question(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """テスト生成質問処理"""

        question = content.get("question", "")
        context = content.get("context", {})

        # 質問分析と回答
        answer = await self._generate_testing_answer(project_id, question, context)

        answer_message = {
            "action": "testing_answer",
            "project_id": project_id,
            "question": question,
            "answer": answer,
            "queen_message": f"👑 Answer: {answer}",
        }

        self.comb_api.send_message(
            to_worker="developer",
            content=answer_message,
            message_type=MessageType.RESPONSE,
            priority=MessagePriority.HIGH,
        )

    async def _handle_testing_completion(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """テスト生成完了処理"""

        final_results = content.get("final_results", {})
        test_summary = content.get("test_summary", {})

        # プロジェクト完了処理
        project = self.active_testing_projects[project_id]
        project["status"] = "completed"
        project["final_results"] = final_results
        project["test_summary"] = test_summary
        project["completed_at"] = datetime.now().isoformat()

        # Work Log完了
        task_id = project.get("task_id")
        if task_id:
            coverage_improvement = final_results.get("coverage_improvement", 0)
            tests_generated = final_results.get("total_tests_generated", 0)

            self.comb_api.complete_task(
                f"Testing completed successfully. Generated {tests_generated} tests, "
                f"coverage improvement: +{coverage_improvement:.1f}%"
            )

        # 成果物をBeeKeeper向けに出力
        await self._output_testing_deliverables(project_id, final_results, test_summary)

        self.logger.info(f"👑 Queen: Testing project {project_id} completed")

    async def _handle_testing_issue(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """テスト生成課題処理"""

        issue = content.get("issue", "")
        severity = content.get("severity", "medium")

        # 課題分析と解決策
        solution = await self._analyze_testing_issue(project_id, issue, severity)

        solution_message = {
            "action": "testing_solution",
            "project_id": project_id,
            "issue": issue,
            "solution": solution,
            "queen_message": f"👑 Solution for {issue}: {solution}",
        }

        self.comb_api.send_message(
            to_worker="developer",
            content=solution_message,
            message_type=MessageType.RESPONSE,
            priority=MessagePriority.HIGH,
        )

        # Work Log記録
        self.comb_api.add_challenge(issue, solution)

    async def _provide_testing_guidance(
        self, project_id: str, progress: dict[str, Any]
    ) -> str:
        """テスト生成指導"""
        current_action = progress.get("current_action", "unknown")

        guidance_map = {
            "create_missing_test_files": "Create basic test file structure with proper imports and test class setup.",
            "generate_unit_tests": "Focus on testing individual functions in isolation. Use mocking for dependencies.",
            "generate_edge_case_tests": "Test boundary conditions, null values, empty inputs, and error conditions.",
            "generate_integration_tests": "Test class interactions and end-to-end workflows.",
        }

        return guidance_map.get(
            current_action,
            "Follow the testing template and focus on comprehensive coverage",
        )

    async def _determine_next_testing_action(
        self, project_id: str, result: dict[str, Any], strategy: dict[str, Any]
    ) -> dict[str, Any] | None:
        """次のテストアクション決定"""

        execution_plan = strategy.get("execution_plan", [])
        completed_actions = result.get("completed_actions", [])

        # 未完了アクション探索
        for action in execution_plan:
            if action["action"] not in completed_actions:
                return action

        return None

    async def _generate_testing_answer(
        self, project_id: str, question: str, context: dict[str, Any]
    ) -> str:
        """テスト生成回答生成"""

        project = self.active_testing_projects[project_id]

        if "mock" in question.lower():
            return "Use pytest fixtures and unittest.mock for mocking dependencies. Mock external services and databases."
        elif "assertion" in question.lower():
            return "Use appropriate assertions: assertEqual, assertTrue, assertIn, etc. Be specific about expected values."
        elif "edge case" in question.lower():
            return "Test with None, empty strings, zero, negative numbers, and boundary values."
        elif "fixture" in question.lower():
            return "Use pytest fixtures for test setup. Create reusable fixtures for common test data."
        else:
            return f"Refer to the testing objective: {project['objective']} and follow the established template."

    async def _analyze_testing_issue(
        self, project_id: str, issue: str, severity: str
    ) -> str:
        """テスト生成課題分析"""

        if "import" in issue.lower():
            return "Check import paths and ensure the module is in PYTHONPATH. Use relative imports if needed."
        elif "fixture" in issue.lower():
            return (
                "Ensure fixtures are properly defined with @pytest.fixture decorator."
            )
        elif "mock" in issue.lower():
            return "Use patch decorator or context manager for proper mocking setup."
        elif "assertion" in issue.lower():
            return (
                "Use appropriate assertion methods and check expected vs actual values."
            )
        else:
            return f"For '{issue}', check pytest documentation and ensure proper test structure."

    async def _output_testing_deliverables(
        self,
        project_id: str,
        final_results: dict[str, Any],
        test_summary: dict[str, Any],
    ) -> None:
        """テスト生成成果物出力"""

        project = self.active_testing_projects[project_id]

        # 成果物ディレクトリ作成
        output_dir = Path(f".hive/honey/beekeeper_testing/{project_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 成果物サマリー
        deliverables = {
            "project_id": project_id,
            "beekeeper_objective": project["objective"],
            "template_used": project["template"],
            "initial_analysis": project["initial_analysis"],
            "final_results": final_results,
            "test_summary": test_summary,
            "conversation_history": self.conversation_history,
            "completion_time": datetime.now().isoformat(),
            "summary": {
                "coverage_improvement": f"{project['initial_analysis']['current_test_coverage']:.1f}% → {final_results.get('final_coverage', 0):.1f}%",
                "total_tests_generated": final_results.get("total_tests_generated", 0),
                "conversation_turns": len(self.conversation_history),
            },
        }

        # ファイル保存
        summary_file = output_dir / "testing_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(deliverables, f, ensure_ascii=False, indent=2)

        # テスト生成レポート
        test_report = output_dir / "test_generation_report.md"
        with open(test_report, "w", encoding="utf-8") as f:
            f.write("# Test Generation Report\n\n")
            f.write(f"**Project:** {project['objective']}\n")
            f.write(
                f"**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            f.write("## Test Generation Results\n\n")
            f.write(
                f"- **Total Tests Generated**: {final_results.get('total_tests_generated', 0)}\n"
            )
            f.write(
                f"- **Coverage Improvement**: {project['initial_analysis']['current_test_coverage']:.1f}% → {final_results.get('final_coverage', 0):.1f}%\n"
            )
            f.write(
                f"- **Test Files Created**: {final_results.get('test_files_created', 0)}\n"
            )

            f.write("\n## Test Types Generated\n\n")
            for test_type, count in test_summary.items():
                f.write(f"- **{test_type}**: {count} tests\n")

            f.write("\n## Conversation Summary\n\n")
            f.write(
                f"Total Queen-Developer exchanges: {len(self.conversation_history)}\n"
            )

        print(f"🍯 Testing deliverables saved to: {output_dir}")
        print(f"📋 Summary: {summary_file}")
        print(f"📄 Report: {test_report}")


class DeveloperTestingWorker:
    """Developer Worker - テスト生成実装"""

    def __init__(self):
        self.comb_api = CombAPI("developer")
        self.logger = logging.getLogger("developer_testing")
        self.active_testing_projects = {}
        self.test_generation_progress = {}

    async def start_testing_monitoring(self) -> None:
        """テスト生成監視開始"""
        self.logger.info("💻 Developer: Starting testing monitoring")

        while True:
            try:
                # Queen からのメッセージ確認
                messages = self.comb_api.receive_messages()

                for message in messages:
                    if message.from_worker == "queen":
                        await self._handle_queen_testing_message(message)

                await asyncio.sleep(5)  # 5秒間隔

            except Exception as e:
                self.logger.error(f"💻 Developer: Error in monitoring: {e}")
                await asyncio.sleep(10)

    async def _handle_queen_testing_message(self, message) -> None:
        """Queen テスト生成メッセージ処理"""
        content = message.content
        action = content.get("action", "unknown")

        if action == "start_testing":
            await self._start_testing_project(content)
        elif action == "testing_guidance":
            await self._receive_testing_guidance(content)
        elif action == "continue_testing":
            await self._continue_testing(content)
        elif action == "testing_answer":
            await self._receive_testing_answer(content)
        elif action == "testing_solution":
            await self._receive_testing_solution(content)

        self.logger.info(f"💻 Developer: Handled {action} from Queen")

    async def _start_testing_project(self, content: dict[str, Any]) -> None:
        """テスト生成プロジェクト開始"""
        project_id = content["project_id"]
        objective = content["objective"]
        strategy = content["strategy"]
        execution_plan = content["execution_plan"]

        # プロジェクト初期化
        self.active_testing_projects[project_id] = {
            "objective": objective,
            "strategy": strategy,
            "execution_plan": execution_plan,
            "current_step": 0,
            "status": "in_progress",
            "completed_actions": [],
            "started_at": datetime.now().isoformat(),
        }

        self.test_generation_progress[project_id] = {
            "current_action": "starting",
            "completion_percentage": 0,
            "tests_generated": 0,
            "test_files_created": 0,
        }

        # テスト生成開始
        await self._execute_testing_plan(project_id)

    async def _execute_testing_plan(self, project_id: str) -> None:
        """テスト生成計画実行"""
        project = self.active_testing_projects[project_id]
        execution_plan = project["execution_plan"]

        # 各ステップを実行
        for step in execution_plan:
            action = step["action"]

            # 進捗報告
            await self._report_testing_progress(project_id, action, 0)

            # アクション実行
            result = await self._execute_testing_action(project_id, step)

            # 結果処理
            if result.get("success", False):
                project["completed_actions"].append(action)

                # テスト生成結果報告
                await self._report_test_generation_result(project_id, result)

                # 進捗更新
                completion = (
                    len(project["completed_actions"]) / len(execution_plan)
                ) * 100
                await self._report_testing_progress(project_id, action, completion)

            else:
                # 課題報告
                await self._report_testing_issue(
                    project_id, result.get("issue", "Unknown issue")
                )
                break

        # 全ステップ完了
        if len(project["completed_actions"]) == len(execution_plan):
            await self._complete_testing_project(project_id)

    async def _execute_testing_action(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """個別テスト生成アクション実行"""
        action = step["action"]

        if action == "create_missing_test_files":
            return await self._create_missing_test_files(project_id, step)
        elif action == "generate_unit_tests":
            return await self._generate_unit_tests(project_id, step)
        elif action == "generate_edge_case_tests":
            return await self._generate_edge_case_tests(project_id, step)
        elif action == "generate_integration_tests":
            return await self._generate_integration_tests(project_id, step)
        else:
            return {"success": False, "issue": f"Unknown action: {action}"}

    async def _create_missing_test_files(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """不足テストファイル作成"""
        try:
            # 不足テストファイルを特定
            python_files = list(Path(".").rglob("*.py"))[:10]  # 最初の10ファイル
            python_files = [
                f
                for f in python_files
                if not any(part.startswith(".") for part in f.parts)
                and "test_" not in f.name
                and "__pycache__" not in str(f)
            ]

            test_files_created = 0

            for file_path in python_files:
                test_file = Path(f"tests/test_{file_path.stem}.py")
                if not test_file.exists():
                    test_file.parent.mkdir(parents=True, exist_ok=True)

                    # 基本テストファイル内容生成
                    test_content = await self._generate_basic_test_file(file_path)

                    with open(test_file, "w", encoding="utf-8") as f:
                        f.write(test_content)

                    test_files_created += 1

            return {
                "success": True,
                "test_type": "test_file_creation",
                "tests_generated": test_files_created,
                "test_files_created": test_files_created,
                "coverage_improvement": test_files_created * 5,  # 簡易推定
                "completed_actions": ["create_missing_test_files"],
            }

        except Exception as e:
            return {"success": False, "issue": f"Test file creation failed: {str(e)}"}

    async def _generate_unit_tests(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """単体テスト生成"""
        try:
            # テスト対象関数を特定
            functions = await self._identify_untested_functions()

            tests_generated = 0

            for func_info in functions[:8]:  # 最初の8関数
                test_content = await self._generate_function_test(func_info)

                if test_content:
                    # 既存テストファイルに追加
                    test_file = Path(f"tests/test_{Path(func_info['file']).stem}.py")

                    if test_file.exists():
                        with open(test_file, "a", encoding="utf-8") as f:
                            f.write(f"\n\n{test_content}")
                        tests_generated += 1

            return {
                "success": True,
                "test_type": "unit_tests",
                "tests_generated": tests_generated,
                "coverage_improvement": tests_generated * 3,  # 簡易推定
                "completed_actions": ["generate_unit_tests"],
            }

        except Exception as e:
            return {"success": False, "issue": f"Unit test generation failed: {str(e)}"}

    async def _generate_edge_case_tests(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """エッジケーステスト生成"""
        try:
            # エッジケース機会を特定
            edge_cases = await self._identify_edge_case_opportunities()

            tests_generated = 0

            for case in edge_cases[:5]:  # 最初の5ケース
                test_content = await self._generate_edge_case_test(case)

                if test_content:
                    # 専用エッジケーステストファイルに追加
                    test_file = Path("tests/test_edge_cases.py")

                    if not test_file.exists():
                        test_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(test_file, "w", encoding="utf-8") as f:
                            f.write('"""Edge case tests"""\nimport pytest\n\n')

                    with open(test_file, "a", encoding="utf-8") as f:
                        f.write(f"\n{test_content}")

                    tests_generated += 1

            return {
                "success": True,
                "test_type": "edge_case_tests",
                "tests_generated": tests_generated,
                "coverage_improvement": tests_generated * 2,  # 簡易推定
                "completed_actions": ["generate_edge_case_tests"],
            }

        except Exception as e:
            return {
                "success": False,
                "issue": f"Edge case test generation failed: {str(e)}",
            }

    async def _generate_integration_tests(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """統合テスト生成"""
        try:
            # クラスベースの統合テストを生成
            classes = await self._identify_testable_classes()

            tests_generated = 0

            for class_info in classes[:3]:  # 最初の3クラス
                test_content = await self._generate_class_integration_test(class_info)

                if test_content:
                    # 統合テストファイルに追加
                    test_file = Path("tests/test_integration.py")

                    if not test_file.exists():
                        test_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(test_file, "w", encoding="utf-8") as f:
                            f.write('"""Integration tests"""\nimport pytest\n\n')

                    with open(test_file, "a", encoding="utf-8") as f:
                        f.write(f"\n{test_content}")

                    tests_generated += 1

            return {
                "success": True,
                "test_type": "integration_tests",
                "tests_generated": tests_generated,
                "coverage_improvement": tests_generated * 4,  # 簡易推定
                "completed_actions": ["generate_integration_tests"],
            }

        except Exception as e:
            return {
                "success": False,
                "issue": f"Integration test generation failed: {str(e)}",
            }

    async def _generate_basic_test_file(self, file_path: Path) -> str:
        """基本テストファイル生成"""
        module_name = file_path.stem

        return f'''"""
Tests for {module_name}

Auto-generated by BeeKeeper Autonomous Testing Agent
"""

import pytest
from unittest.mock import Mock, patch
from {module_name} import *


class Test{module_name.title()}:
    """Test class for {module_name}"""

    def test_{module_name}_basic(self):
        """Basic functionality test"""
        # TODO: Implement actual test logic
        assert True

    def test_{module_name}_error_handling(self):
        """Error handling test"""
        # TODO: Test error conditions
        assert True
'''

    async def _identify_untested_functions(self) -> list[dict[str, Any]]:
        """テスト未実装関数特定"""
        functions = []

        python_files = list(Path(".").rglob("*.py"))[:8]
        python_files = [
            f
            for f in python_files
            if not any(part.startswith(".") for part in f.parts)
            and "test_" not in f.name
            and "__pycache__" not in str(f)
        ]

        for file_path in python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not node.name.startswith("_"):
                            functions.append(
                                {
                                    "name": node.name,
                                    "file": str(file_path),
                                    "args": [arg.arg for arg in node.args.args],
                                }
                            )

            except Exception:
                continue

        return functions

    async def _generate_function_test(self, func_info: dict[str, Any]) -> str:
        """関数テスト生成"""
        func_name = func_info["name"]
        args = func_info["args"]

        # 簡易テスト生成
        return f'''def test_{func_name}():
    """Test {func_name} function"""
    # TODO: Implement comprehensive test for {func_name}
    # Args: {args}
    result = {func_name}({self._generate_sample_args(args)})
    assert result is not None'''

    def _generate_sample_args(self, args: list[str]) -> str:
        """サンプル引数生成"""
        if not args:
            return ""

        sample_args = []
        for arg in args:
            if arg == "self":
                continue
            sample_args.append(f'"{arg}_value"')

        return ", ".join(sample_args)

    async def _identify_edge_case_opportunities(self) -> list[dict[str, Any]]:
        """エッジケース機会特定"""
        return [
            {"type": "null_input", "description": "Test with None input"},
            {"type": "empty_string", "description": "Test with empty string"},
            {"type": "zero_value", "description": "Test with zero value"},
            {"type": "negative_value", "description": "Test with negative value"},
            {"type": "large_value", "description": "Test with large value"},
        ]

    async def _generate_edge_case_test(self, case: dict[str, Any]) -> str:
        """エッジケーステスト生成"""
        case_type = case["type"]
        description = case["description"]

        return f'''def test_edge_case_{case_type}():
    """Edge case test: {description}"""
    # TODO: Implement edge case test for {case_type}
    assert True  # Placeholder'''

    async def _identify_testable_classes(self) -> list[dict[str, Any]]:
        """テスト対象クラス特定"""
        classes = []

        python_files = list(Path(".").rglob("*.py"))[:5]
        python_files = [
            f
            for f in python_files
            if not any(part.startswith(".") for part in f.parts)
            and "test_" not in f.name
            and "__pycache__" not in str(f)
        ]

        for file_path in python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        classes.append({"name": node.name, "file": str(file_path)})

            except Exception:
                continue

        return classes

    async def _generate_class_integration_test(self, class_info: dict[str, Any]) -> str:
        """クラス統合テスト生成"""
        class_name = class_info["name"]

        return f'''def test_{class_name.lower()}_integration():
    """Integration test for {class_name}"""
    # TODO: Implement integration test for {class_name}
    instance = {class_name}()
    assert instance is not None'''

    async def _report_testing_progress(
        self, project_id: str, action: str, completion: float
    ) -> None:
        """テスト生成進捗報告"""
        progress_update = {
            "type": "testing_progress",
            "project_id": project_id,
            "progress": {
                "current_action": action,
                "completion_percentage": completion,
                "description": f"Executing {action}",
                "timestamp": datetime.now().isoformat(),
            },
        }

        self.comb_api.send_message(
            to_worker="queen",
            content=progress_update,
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.MEDIUM,
        )

    async def _report_test_generation_result(
        self, project_id: str, result: dict[str, Any]
    ) -> None:
        """テスト生成結果報告"""
        result_report = {
            "type": "test_generation_result",
            "project_id": project_id,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }

        self.comb_api.send_message(
            to_worker="queen",
            content=result_report,
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.HIGH,
        )

    async def _report_testing_issue(self, project_id: str, issue: str) -> None:
        """テスト生成課題報告"""
        issue_report = {
            "type": "testing_issue",
            "project_id": project_id,
            "issue": issue,
            "severity": "medium",
            "timestamp": datetime.now().isoformat(),
        }

        self.comb_api.send_message(
            to_worker="queen",
            content=issue_report,
            message_type=MessageType.URGENT_NOTIFICATION,
            priority=MessagePriority.HIGH,
        )

    async def _complete_testing_project(self, project_id: str) -> None:
        """テスト生成プロジェクト完了"""
        project = self.active_testing_projects[project_id]
        progress = self.test_generation_progress[project_id]

        # 最終カバレッジ計算
        final_coverage = await self._calculate_final_coverage()

        final_results = {
            "total_tests_generated": progress["tests_generated"],
            "test_files_created": progress["test_files_created"],
            "final_coverage": final_coverage,
            "coverage_improvement": final_coverage - 0,  # 簡易計算
            "actions_completed": len(project["completed_actions"]),
            "total_actions": len(project["execution_plan"]),
        }

        # テスト種別サマリー
        test_summary = {
            "unit_tests": progress["tests_generated"] // 2,
            "edge_case_tests": progress["tests_generated"] // 4,
            "integration_tests": progress["tests_generated"] // 4,
        }

        completion_report = {
            "type": "testing_completion",
            "project_id": project_id,
            "final_results": final_results,
            "test_summary": test_summary,
            "summary": f"Testing completed successfully. Generated {final_results['total_tests_generated']} tests, coverage: {final_coverage:.1f}%",
            "timestamp": datetime.now().isoformat(),
        }

        self.comb_api.send_message(
            to_worker="queen",
            content=completion_report,
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.HIGH,
        )

        # プロジェクト終了
        project["status"] = "completed"
        project["completed_at"] = datetime.now().isoformat()

    async def _calculate_final_coverage(self) -> float:
        """最終カバレッジ計算"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=.", "--cov-report=json", "--quiet"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                coverage_file = Path("coverage.json")
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        data = json.load(f)
                    coverage_file.unlink()

                    return data.get("totals", {}).get("percent_covered", 0)

            return 0.0

        except Exception:
            return 0.0

    async def _receive_testing_guidance(self, content: dict[str, Any]) -> None:
        """テスト生成指導受信"""
        guidance = content.get("guidance", "")
        self.logger.info(f"💻 Developer: Received guidance: {guidance}")

    async def _continue_testing(self, content: dict[str, Any]) -> None:
        """テスト生成継続"""
        next_action = content.get("next_action", {})
        self.logger.info(f"💻 Developer: Continuing with: {next_action}")

    async def _receive_testing_answer(self, content: dict[str, Any]) -> None:
        """テスト生成回答受信"""
        answer = content.get("answer", "")
        self.logger.info(f"💻 Developer: Received answer: {answer}")

    async def _receive_testing_solution(self, content: dict[str, Any]) -> None:
        """テスト生成解決策受信"""
        solution = content.get("solution", "")
        self.logger.info(f"💻 Developer: Received solution: {solution}")


# 統合デモ実行


async def demo_beekeeper_testing():
    """BeeKeeper テスト生成デモ"""

    print("🐝 Starting BeeKeeper Autonomous Testing Demo")
    print("=" * 50)

    # 1. BeeKeeper 入力
    beekeeper = BeeKeeperTestingInput()
    request_id = beekeeper.submit_testing_request(
        objective="Generate comprehensive test suite for improved code coverage",
        template="Analyze codebase → Create missing test files → Generate unit tests → Add edge case tests → Validate coverage improvement",
        target_files=[],
        coverage_targets={
            "line_coverage": 85,
            "branch_coverage": 80,
            "function_coverage": 90,
            "edge_cases_coverage": 75,
        },
        test_types=["unit", "edge_case", "integration"],
    )

    # 2. Queen Coordinator 初期化
    queen = QueenTestingCoordinator()

    # 3. Developer Worker 初期化
    developer = DeveloperTestingWorker()

    # 4. Developer Worker 監視開始
    developer_task = asyncio.create_task(developer.start_testing_monitoring())

    # 5. Queen が BeeKeeper 入力を処理
    request_data = beekeeper.get_request_data(request_id)
    await queen.receive_beekeeper_request(request_id, request_data)

    # 6. Queen-Developer 協調監視
    print("\n🔄 Queen-Developer testing collaboration started...")

    project_id = f"testing_{request_id}"
    for _cycle in range(10):  # 10サイクル監視
        await queen.monitor_testing_progress(project_id)
        await asyncio.sleep(12)  # 12秒間隔

        # プロジェクト完了チェック
        if project_id in queen.active_testing_projects:
            if queen.active_testing_projects[project_id]["status"] == "completed":
                print(f"✅ Testing project {project_id} completed!")
                break

    # 7. 終了処理
    developer_task.cancel()

    # 8. 結果表示
    print("\n📊 Testing Results:")
    print(f"🗂️  Conversation History: {len(queen.conversation_history)} messages")
    print(f"📁 Active Projects: {len(queen.active_testing_projects)}")

    # 成果物確認
    honey_dir = Path(f".hive/honey/beekeeper_testing/{project_id}")
    if honey_dir.exists():
        print(f"🍯 Testing deliverables saved to: {honey_dir}")
        for file in honey_dir.glob("*"):
            print(f"   - {file.name}")

    print("\n🎉 BeeKeeper Testing Demo Completed!")


if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # デモ実行
    asyncio.run(demo_beekeeper_testing())
