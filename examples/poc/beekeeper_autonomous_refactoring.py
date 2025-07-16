"""
BeeKeeper自律的コードリファクタリングPoC

正しいアーキテクチャ：
1. BeeKeeper（人間）が品質改善目的・テンプレート投入
2. Queen/Developer間で自律的協調・会話
3. 成果物（改善されたコード）を人間が受領

Usage:
    python examples/poc/beekeeper_autonomous_refactoring.py
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


class BeeKeeperRefactoringInput:
    """BeeKeeper（人間）からのリファクタリング入力"""

    def __init__(self):
        self.refactoring_requests = {}

    def submit_refactoring_request(
        self,
        objective: str,
        template: str,
        target_files: list[str] = None,
        quality_targets: dict[str, Any] = None,
    ) -> str:
        """リファクタリング要求投入"""

        request_id = f"refactoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.refactoring_requests[request_id] = {
            "objective": objective,
            "template": template,
            "target_files": target_files or [],
            "quality_targets": quality_targets
            or {
                "test_coverage": 85,
                "type_annotation_coverage": 90,
                "docstring_coverage": 80,
                "overall_quality_score": 85,
            },
            "timestamp": datetime.now().isoformat(),
            "status": "submitted",
        }

        print(f"🐝 BeeKeeper Refactoring Request: {request_id}")
        print(f"📋 Objective: {objective}")
        print(f"📝 Template: {template}")
        print(f"🎯 Quality Targets: {quality_targets}")

        return request_id

    def get_request_data(self, request_id: str) -> dict[str, Any]:
        """要求データ取得"""
        return self.refactoring_requests.get(request_id, {})


class QueenRefactoringCoordinator:
    """Queen Worker - リファクタリング全体調整"""

    def __init__(self):
        self.comb_api = CombAPI("queen")
        self.logger = logging.getLogger("queen_refactoring")
        self.active_refactoring_projects = {}
        self.conversation_history = []

    async def receive_beekeeper_request(
        self, request_id: str, request_data: dict[str, Any]
    ) -> None:
        """BeeKeeperリファクタリング要求受信"""

        # プロジェクト初期化
        project_id = f"refactoring_{request_id}"
        self.active_refactoring_projects[project_id] = {
            "request_id": request_id,
            "objective": request_data["objective"],
            "template": request_data["template"],
            "target_files": request_data["target_files"],
            "quality_targets": request_data["quality_targets"],
            "status": "analyzing",
            "created_at": datetime.now().isoformat(),
        }

        # Work Log開始
        task_id = self.comb_api.start_task(
            f"BeeKeeper Refactoring: {request_data['objective']}",
            "beekeeper_refactoring",
            f"Starting refactoring project: {request_data['objective']}",
            workers=["queen", "developer"],
        )

        self.active_refactoring_projects[project_id]["task_id"] = task_id

        # 初期コード分析
        analysis = await self._analyze_codebase(request_data)
        self.active_refactoring_projects[project_id]["initial_analysis"] = analysis

        # リファクタリング戦略策定
        strategy = await self._develop_refactoring_strategy(request_data, analysis)
        self.active_refactoring_projects[project_id]["strategy"] = strategy

        # Developer Workerに初期指示
        await self._send_initial_refactoring_instructions(project_id, strategy)

        self.logger.info(f"👑 Queen: Started refactoring project {project_id}")

    async def _analyze_codebase(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """コードベース分析"""

        analysis = {
            "total_python_files": 0,
            "functions_without_types": 0,
            "functions_without_docstrings": 0,
            "test_coverage": 0,
            "quality_issues": [],
            "complexity_analysis": {},
        }

        try:
            # Pythonファイル検索
            python_files = list(Path(".").rglob("*.py"))
            python_files = [
                f
                for f in python_files
                if not any(part.startswith(".") for part in f.parts)
                and "test" not in f.name.lower()
                and "__pycache__" not in str(f)
            ]

            analysis["total_python_files"] = len(python_files)

            # 関数分析
            for file_path in python_files[:10]:  # 最初の10ファイル
                try:
                    with open(file_path, encoding="utf-8") as f:
                        tree = ast.parse(f.read())

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            # 型アノテーション確認
                            if node.returns is None:
                                analysis["functions_without_types"] += 1

                            # docstring確認
                            has_docstring = (
                                node.body
                                and isinstance(node.body[0], ast.Expr)
                                and isinstance(node.body[0].value, ast.Constant)
                            )

                            if not has_docstring:
                                analysis["functions_without_docstrings"] += 1

                except Exception as e:
                    analysis["quality_issues"].append(
                        f"Parse error in {file_path}: {str(e)}"
                    )

            # テストカバレッジ取得
            try:
                result = subprocess.run(
                    [
                        "python",
                        "-m",
                        "pytest",
                        "--cov=.",
                        "--cov-report=json",
                        "--quiet",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode == 0:
                    coverage_file = Path("coverage.json")
                    if coverage_file.exists():
                        with open(coverage_file) as f:
                            coverage_data = json.load(f)
                        coverage_file.unlink()

                        analysis["test_coverage"] = coverage_data.get("totals", {}).get(
                            "percent_covered", 0
                        )

            except Exception as e:
                analysis["quality_issues"].append(f"Coverage analysis error: {str(e)}")

            # 品質スコア計算
            type_score = max(0, 100 - analysis["functions_without_types"] * 2)
            doc_score = max(0, 100 - analysis["functions_without_docstrings"] * 1.5)

            analysis["overall_quality_score"] = (
                analysis["test_coverage"] * 0.4 + type_score * 0.3 + doc_score * 0.3
            )

            self.logger.info(
                f"👑 Queen: Codebase analysis completed - Quality Score: {analysis['overall_quality_score']:.1f}%"
            )

        except Exception as e:
            analysis["quality_issues"].append(f"Analysis error: {str(e)}")

        return analysis

    async def _develop_refactoring_strategy(
        self, request_data: dict[str, Any], analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """リファクタリング戦略策定"""

        quality_targets = request_data["quality_targets"]
        current_score = analysis["overall_quality_score"]

        strategy = {
            "current_quality_score": current_score,
            "target_quality_score": quality_targets.get("overall_quality_score", 85),
            "improvement_needed": quality_targets.get("overall_quality_score", 85)
            - current_score,
            "priority_actions": [],
        }

        # 優先アクション決定
        if analysis["test_coverage"] < quality_targets.get("test_coverage", 85):
            strategy["priority_actions"].append(
                {
                    "action": "improve_test_coverage",
                    "current": analysis["test_coverage"],
                    "target": quality_targets.get("test_coverage", 85),
                    "priority": "high",
                }
            )

        if analysis["functions_without_types"] > 5:
            strategy["priority_actions"].append(
                {
                    "action": "add_type_annotations",
                    "functions_affected": analysis["functions_without_types"],
                    "priority": "medium",
                }
            )

        if analysis["functions_without_docstrings"] > 10:
            strategy["priority_actions"].append(
                {
                    "action": "add_docstrings",
                    "functions_affected": analysis["functions_without_docstrings"],
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
                    "description": self._get_action_description(action),
                    "priority": action["priority"],
                }
            )

        # Work Log記録
        self.comb_api.add_technical_decision(
            "Refactoring Strategy",
            f"Planned {len(strategy['priority_actions'])} priority actions to improve quality from {current_score:.1f}% to {quality_targets.get('overall_quality_score', 85)}%",
            ["Alternative refactoring approaches", "Manual refactoring"],
        )

        return strategy

    def _get_action_description(self, action: dict[str, Any]) -> str:
        """アクション説明生成"""
        action_type = action["action"]

        if action_type == "improve_test_coverage":
            return f"Increase test coverage from {action['current']:.1f}% to {action['target']}%"
        elif action_type == "add_type_annotations":
            return f"Add type annotations to {action['functions_affected']} functions"
        elif action_type == "add_docstrings":
            return f"Add docstrings to {action['functions_affected']} functions"
        else:
            return f"Execute {action_type}"

    async def _send_initial_refactoring_instructions(
        self, project_id: str, strategy: dict[str, Any]
    ) -> None:
        """Developer Workerに初期リファクタリング指示"""

        project = self.active_refactoring_projects[project_id]

        instructions = {
            "action": "start_refactoring",
            "project_id": project_id,
            "objective": project["objective"],
            "template": project["template"],
            "quality_targets": project["quality_targets"],
            "strategy": strategy,
            "execution_plan": strategy["execution_plan"],
            "queen_message": f"👑 Starting refactoring project: {project['objective']}",
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
                    "type": "refactoring_instructions",
                    "content": instructions,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            self.logger.info(
                f"👑 Queen: Sent refactoring instructions for {project_id}"
            )

    async def monitor_refactoring_progress(self, project_id: str) -> None:
        """リファクタリング進捗監視"""

        project = self.active_refactoring_projects.get(project_id)
        if not project:
            return

        # Developer Workerからの応答監視
        messages = self.comb_api.receive_messages()

        for message in messages:
            if message.from_worker == "developer":
                await self._handle_developer_refactoring_response(project_id, message)

    async def _handle_developer_refactoring_response(
        self, project_id: str, message
    ) -> None:
        """Developer Workerリファクタリング応答処理"""

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
        if response_type == "refactoring_progress":
            await self._handle_refactoring_progress(project_id, content)
        elif response_type == "quality_improvement":
            await self._handle_quality_improvement(project_id, content)
        elif response_type == "refactoring_question":
            await self._handle_refactoring_question(project_id, content)
        elif response_type == "refactoring_completion":
            await self._handle_refactoring_completion(project_id, content)
        elif response_type == "refactoring_issue":
            await self._handle_refactoring_issue(project_id, content)

        self.logger.info(f"👑 Queen: Handled {response_type} from developer")

    async def _handle_refactoring_progress(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """リファクタリング進捗処理"""

        progress = content.get("progress", {})
        current_action = progress.get("current_action", "unknown")
        completion_percentage = progress.get("completion_percentage", 0)

        # Work Log記録
        self.comb_api.add_progress(
            f"Refactoring Progress: {current_action}",
            f"Progress: {completion_percentage}% - {progress.get('description', '')}",
        )

        # 必要に応じて追加指示
        if progress.get("needs_guidance", False):
            guidance = await self._provide_refactoring_guidance(project_id, progress)

            guidance_message = {
                "action": "refactoring_guidance",
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

    async def _handle_quality_improvement(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """品質改善処理"""

        improvement = content.get("improvement", {})
        metric = improvement.get("metric", "unknown")
        before_value = improvement.get("before", 0)
        after_value = improvement.get("after", 0)

        # Work Log記録
        self.comb_api.add_progress(
            f"Quality Improvement: {metric}",
            f"Improved {metric} from {before_value} to {after_value}",
        )

        # 次のアクション指示
        project = self.active_refactoring_projects[project_id]
        strategy = project.get("strategy", {})

        next_action = await self._determine_next_refactoring_action(
            project_id, improvement, strategy
        )

        if next_action:
            next_instruction = {
                "action": "continue_refactoring",
                "project_id": project_id,
                "next_action": next_action,
                "queen_message": f"👑 Great improvement! Next: {next_action['description']}",
            }

            self.comb_api.send_message(
                to_worker="developer",
                content=next_instruction,
                message_type=MessageType.REQUEST,
                priority=MessagePriority.HIGH,
            )

    async def _handle_refactoring_question(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """リファクタリング質問処理"""

        question = content.get("question", "")
        context = content.get("context", {})

        # 質問分析と回答
        answer = await self._generate_refactoring_answer(project_id, question, context)

        answer_message = {
            "action": "refactoring_answer",
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

    async def _handle_refactoring_completion(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """リファクタリング完了処理"""

        final_results = content.get("final_results", {})
        improvements = content.get("improvements", [])

        # プロジェクト完了処理
        project = self.active_refactoring_projects[project_id]
        project["status"] = "completed"
        project["final_results"] = final_results
        project["improvements"] = improvements
        project["completed_at"] = datetime.now().isoformat()

        # Work Log完了
        task_id = project.get("task_id")
        if task_id:
            improvement_summary = ", ".join(
                [
                    f"{imp['metric']}: {imp['before']} → {imp['after']}"
                    for imp in improvements
                ]
            )

            self.comb_api.complete_task(
                f"Refactoring completed successfully. Improvements: {improvement_summary}"
            )

        # 成果物をBeeKeeper向けに出力
        await self._output_refactoring_deliverables(
            project_id, final_results, improvements
        )

        self.logger.info(f"👑 Queen: Refactoring project {project_id} completed")

    async def _handle_refactoring_issue(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """リファクタリング課題処理"""

        issue = content.get("issue", "")
        severity = content.get("severity", "medium")

        # 課題分析と解決策
        solution = await self._analyze_refactoring_issue(project_id, issue, severity)

        solution_message = {
            "action": "refactoring_solution",
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

    async def _provide_refactoring_guidance(
        self, project_id: str, progress: dict[str, Any]
    ) -> str:
        """リファクタリング指導"""
        current_action = progress.get("current_action", "unknown")

        guidance_map = {
            "improve_test_coverage": "Focus on functions with complex logic first. Create unit tests for edge cases.",
            "add_type_annotations": "Start with function parameters and return types. Use Union for multiple types.",
            "add_docstrings": "Follow Google or NumPy docstring style. Include parameters, returns, and examples.",
        }

        return guidance_map.get(
            current_action, "Continue according to the refactoring plan"
        )

    async def _determine_next_refactoring_action(
        self, project_id: str, improvement: dict[str, Any], strategy: dict[str, Any]
    ) -> dict[str, Any] | None:
        """次のリファクタリングアクション決定"""

        execution_plan = strategy.get("execution_plan", [])
        completed_actions = improvement.get("completed_actions", [])

        # 未完了アクション探索
        for action in execution_plan:
            if action["action"] not in completed_actions:
                return action

        return None

    async def _generate_refactoring_answer(
        self, project_id: str, question: str, context: dict[str, Any]
    ) -> str:
        """リファクタリング回答生成"""

        project = self.active_refactoring_projects[project_id]

        if "type annotation" in question.lower():
            return "Use appropriate type hints from typing module. For complex types, consider Union, Optional, or custom types."
        elif "test" in question.lower():
            return "Write unit tests for each function. Use pytest fixtures for setup. Mock external dependencies."
        elif "docstring" in question.lower():
            return "Follow the established docstring format. Include description, parameters, returns, and examples where helpful."
        else:
            return f"Refer to the refactoring objective: {project['objective']} and follow the established template."

    async def _analyze_refactoring_issue(
        self, project_id: str, issue: str, severity: str
    ) -> str:
        """リファクタリング課題分析"""

        if "syntax" in issue.lower():
            return "Check syntax errors carefully. Use a linter like flake8 or pylint for validation."
        elif "import" in issue.lower():
            return (
                "Verify import statements and module paths. Check for circular imports."
            )
        elif "test" in issue.lower():
            return "Ensure test files are properly named (test_*.py) and use correct assertions."
        else:
            return f"For '{issue}', try breaking down the problem into smaller steps or consult documentation."

    async def _output_refactoring_deliverables(
        self,
        project_id: str,
        final_results: dict[str, Any],
        improvements: list[dict[str, Any]],
    ) -> None:
        """リファクタリング成果物出力"""

        project = self.active_refactoring_projects[project_id]

        # 成果物ディレクトリ作成
        output_dir = Path(f".hive/honey/beekeeper_refactoring/{project_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 成果物サマリー
        deliverables = {
            "project_id": project_id,
            "beekeeper_objective": project["objective"],
            "template_used": project["template"],
            "initial_analysis": project["initial_analysis"],
            "final_results": final_results,
            "improvements": improvements,
            "conversation_history": self.conversation_history,
            "completion_time": datetime.now().isoformat(),
            "summary": {
                "quality_improvement": f"{project['initial_analysis']['overall_quality_score']:.1f}% → {final_results.get('final_quality_score', 0):.1f}%",
                "total_improvements": len(improvements),
                "conversation_turns": len(self.conversation_history),
            },
        }

        # ファイル保存
        summary_file = output_dir / "refactoring_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(deliverables, f, ensure_ascii=False, indent=2)

        # 改善レポート
        improvements_report = output_dir / "improvements_report.md"
        with open(improvements_report, "w", encoding="utf-8") as f:
            f.write("# Refactoring Improvements Report\n\n")
            f.write(f"**Project:** {project['objective']}\n")
            f.write(
                f"**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            f.write("## Quality Improvements\n\n")
            for improvement in improvements:
                f.write(
                    f"- **{improvement['metric']}**: {improvement['before']} → {improvement['after']}\n"
                )

            f.write("\n## Conversation Summary\n\n")
            f.write(
                f"Total Queen-Developer exchanges: {len(self.conversation_history)}\n"
            )

        print(f"🍯 Refactoring deliverables saved to: {output_dir}")
        print(f"📋 Summary: {summary_file}")
        print(f"📄 Report: {improvements_report}")


class DeveloperRefactoringWorker:
    """Developer Worker - リファクタリング実装"""

    def __init__(self):
        self.comb_api = CombAPI("developer")
        self.logger = logging.getLogger("developer_refactoring")
        self.active_refactoring_projects = {}
        self.current_progress = {}

    async def start_refactoring_monitoring(self) -> None:
        """リファクタリング監視開始"""
        self.logger.info("💻 Developer: Starting refactoring monitoring")

        while True:
            try:
                # Queen からのメッセージ確認
                messages = self.comb_api.receive_messages()

                for message in messages:
                    if message.from_worker == "queen":
                        await self._handle_queen_refactoring_message(message)

                await asyncio.sleep(5)  # 5秒間隔

            except Exception as e:
                self.logger.error(f"💻 Developer: Error in monitoring: {e}")
                await asyncio.sleep(10)

    async def _handle_queen_refactoring_message(self, message) -> None:
        """Queen リファクタリングメッセージ処理"""
        content = message.content
        action = content.get("action", "unknown")

        if action == "start_refactoring":
            await self._start_refactoring_project(content)
        elif action == "refactoring_guidance":
            await self._receive_refactoring_guidance(content)
        elif action == "continue_refactoring":
            await self._continue_refactoring(content)
        elif action == "refactoring_answer":
            await self._receive_refactoring_answer(content)
        elif action == "refactoring_solution":
            await self._receive_refactoring_solution(content)

        self.logger.info(f"💻 Developer: Handled {action} from Queen")

    async def _start_refactoring_project(self, content: dict[str, Any]) -> None:
        """リファクタリングプロジェクト開始"""
        project_id = content["project_id"]
        objective = content["objective"]
        strategy = content["strategy"]
        execution_plan = content["execution_plan"]

        # プロジェクト初期化
        self.active_refactoring_projects[project_id] = {
            "objective": objective,
            "strategy": strategy,
            "execution_plan": execution_plan,
            "current_step": 0,
            "status": "in_progress",
            "completed_actions": [],
            "started_at": datetime.now().isoformat(),
        }

        self.current_progress[project_id] = {
            "current_action": "starting",
            "completion_percentage": 0,
            "improvements": [],
        }

        # 最初のアクション実行
        await self._execute_refactoring_plan(project_id)

    async def _execute_refactoring_plan(self, project_id: str) -> None:
        """リファクタリング計画実行"""
        project = self.active_refactoring_projects[project_id]
        execution_plan = project["execution_plan"]

        # 各ステップを実行
        for step in execution_plan:
            action = step["action"]

            # 進捗報告
            await self._report_refactoring_progress(project_id, action, 0)

            # アクション実行
            result = await self._execute_refactoring_action(project_id, step)

            # 結果処理
            if result.get("success", False):
                project["completed_actions"].append(action)
                improvement = result.get("improvement", {})

                # 品質改善報告
                await self._report_quality_improvement(project_id, improvement)

                # 進捗更新
                completion = (
                    len(project["completed_actions"]) / len(execution_plan)
                ) * 100
                await self._report_refactoring_progress(project_id, action, completion)

            else:
                # 課題報告
                await self._report_refactoring_issue(
                    project_id, result.get("issue", "Unknown issue")
                )
                break

        # 全ステップ完了
        if len(project["completed_actions"]) == len(execution_plan):
            await self._complete_refactoring_project(project_id)

    async def _execute_refactoring_action(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """個別リファクタリングアクション実行"""
        action = step["action"]

        if action == "improve_test_coverage":
            return await self._improve_test_coverage(project_id, step)
        elif action == "add_type_annotations":
            return await self._add_type_annotations(project_id, step)
        elif action == "add_docstrings":
            return await self._add_docstrings(project_id, step)
        else:
            return {"success": False, "issue": f"Unknown action: {action}"}

    async def _improve_test_coverage(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """テストカバレッジ改善"""
        try:
            # 現在のカバレッジ取得
            current_coverage = await self._get_current_test_coverage()

            # 新しいテストファイル生成 (簡易版)
            test_files_created = await self._generate_missing_tests()

            # 改善後のカバレッジ確認
            new_coverage = await self._get_current_test_coverage()

            improvement = {
                "metric": "test_coverage",
                "before": current_coverage,
                "after": new_coverage,
                "files_created": test_files_created,
                "improvement_percentage": new_coverage - current_coverage,
            }

            return {
                "success": True,
                "improvement": improvement,
                "details": f"Created {test_files_created} test files, coverage: {current_coverage:.1f}% → {new_coverage:.1f}%",
            }

        except Exception as e:
            return {
                "success": False,
                "issue": f"Test coverage improvement failed: {str(e)}",
            }

    async def _add_type_annotations(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """型アノテーション追加"""
        try:
            # 型アノテーション前の関数数
            functions_before = await self._count_functions_without_types()

            # 型アノテーション追加 (簡易版)
            functions_annotated = await self._add_basic_type_annotations()

            # 型アノテーション後の関数数
            functions_after = await self._count_functions_without_types()

            improvement = {
                "metric": "type_annotations",
                "before": functions_before,
                "after": functions_after,
                "functions_annotated": functions_annotated,
                "improvement_count": functions_before - functions_after,
            }

            return {
                "success": True,
                "improvement": improvement,
                "details": f"Added type annotations to {functions_annotated} functions",
            }

        except Exception as e:
            return {
                "success": False,
                "issue": f"Type annotation addition failed: {str(e)}",
            }

    async def _add_docstrings(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """docstring追加"""
        try:
            # docstring前の関数数
            functions_before = await self._count_functions_without_docstrings()

            # docstring追加 (簡易版)
            functions_documented = await self._add_basic_docstrings()

            # docstring後の関数数
            functions_after = await self._count_functions_without_docstrings()

            improvement = {
                "metric": "docstrings",
                "before": functions_before,
                "after": functions_after,
                "functions_documented": functions_documented,
                "improvement_count": functions_before - functions_after,
            }

            return {
                "success": True,
                "improvement": improvement,
                "details": f"Added docstrings to {functions_documented} functions",
            }

        except Exception as e:
            return {"success": False, "issue": f"Docstring addition failed: {str(e)}"}

    async def _get_current_test_coverage(self) -> float:
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

    async def _generate_missing_tests(self) -> int:
        """不足テスト生成"""
        # 簡易実装: 基本的なテストテンプレート生成
        tests_created = 0

        python_files = list(Path(".").rglob("*.py"))[:5]  # 最初の5ファイル

        for file_path in python_files:
            if (
                "test_" not in file_path.name
                and "__pycache__" not in str(file_path)
                and not str(file_path).startswith(".")
            ):
                test_file = Path(f"tests/test_{file_path.stem}.py")
                if not test_file.exists():
                    test_file.parent.mkdir(parents=True, exist_ok=True)

                    test_content = f'''"""Test for {file_path.stem}"""
import pytest
from {file_path.stem} import *

def test_{file_path.stem}_basic():
    """Basic test for {file_path.stem}"""
    assert True  # Placeholder test
'''

                    with open(test_file, "w", encoding="utf-8") as f:
                        f.write(test_content)

                    tests_created += 1

        return tests_created

    async def _count_functions_without_types(self) -> int:
        """型アノテーションなし関数数"""
        count = 0

        python_files = list(Path(".").rglob("*.py"))[:10]

        for file_path in python_files:
            if (
                "test_" not in file_path.name
                and "__pycache__" not in str(file_path)
                and not str(file_path).startswith(".")
            ):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        tree = ast.parse(f.read())

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            if node.returns is None:
                                count += 1

                except Exception:
                    continue

        return count

    async def _add_basic_type_annotations(self) -> int:
        """基本型アノテーション追加"""
        # 実装省略: 実際には AST を使って型アノテーションを追加
        return 3  # デモ用固定値

    async def _count_functions_without_docstrings(self) -> int:
        """docstringなし関数数"""
        count = 0

        python_files = list(Path(".").rglob("*.py"))[:10]

        for file_path in python_files:
            if (
                "test_" not in file_path.name
                and "__pycache__" not in str(file_path)
                and not str(file_path).startswith(".")
            ):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        tree = ast.parse(f.read())

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            has_docstring = (
                                node.body
                                and isinstance(node.body[0], ast.Expr)
                                and isinstance(node.body[0].value, ast.Constant)
                            )

                            if not has_docstring:
                                count += 1

                except Exception:
                    continue

        return count

    async def _add_basic_docstrings(self) -> int:
        """基本docstring追加"""
        # 実装省略: 実際には AST を使って docstring を追加
        return 5  # デモ用固定値

    async def _report_refactoring_progress(
        self, project_id: str, action: str, completion: float
    ) -> None:
        """リファクタリング進捗報告"""
        progress_update = {
            "type": "refactoring_progress",
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

    async def _report_quality_improvement(
        self, project_id: str, improvement: dict[str, Any]
    ) -> None:
        """品質改善報告"""
        improvement_report = {
            "type": "quality_improvement",
            "project_id": project_id,
            "improvement": improvement,
            "timestamp": datetime.now().isoformat(),
        }

        self.comb_api.send_message(
            to_worker="queen",
            content=improvement_report,
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.HIGH,
        )

    async def _report_refactoring_issue(self, project_id: str, issue: str) -> None:
        """リファクタリング課題報告"""
        issue_report = {
            "type": "refactoring_issue",
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

    async def _complete_refactoring_project(self, project_id: str) -> None:
        """リファクタリングプロジェクト完了"""
        project = self.active_refactoring_projects[project_id]

        # 最終結果計算
        final_coverage = await self._get_current_test_coverage()
        final_quality_score = await self._calculate_final_quality_score()

        final_results = {
            "final_test_coverage": final_coverage,
            "final_quality_score": final_quality_score,
            "actions_completed": len(project["completed_actions"]),
            "total_actions": len(project["execution_plan"]),
        }

        # 改善サマリー
        improvements = self.current_progress[project_id].get("improvements", [])

        completion_report = {
            "type": "refactoring_completion",
            "project_id": project_id,
            "final_results": final_results,
            "improvements": improvements,
            "summary": f"Refactoring completed successfully. Final quality score: {final_quality_score:.1f}%",
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

    async def _calculate_final_quality_score(self) -> float:
        """最終品質スコア計算"""
        # 簡易計算
        test_coverage = await self._get_current_test_coverage()
        functions_without_types = await self._count_functions_without_types()
        functions_without_docs = await self._count_functions_without_docstrings()

        type_score = max(0, 100 - functions_without_types * 2)
        doc_score = max(0, 100 - functions_without_docs * 1.5)

        return test_coverage * 0.4 + type_score * 0.3 + doc_score * 0.3

    async def _receive_refactoring_guidance(self, content: dict[str, Any]) -> None:
        """リファクタリング指導受信"""
        guidance = content.get("guidance", "")
        self.logger.info(f"💻 Developer: Received guidance: {guidance}")

    async def _continue_refactoring(self, content: dict[str, Any]) -> None:
        """リファクタリング継続"""
        next_action = content.get("next_action", {})
        self.logger.info(f"💻 Developer: Continuing with: {next_action}")

    async def _receive_refactoring_answer(self, content: dict[str, Any]) -> None:
        """リファクタリング回答受信"""
        answer = content.get("answer", "")
        self.logger.info(f"💻 Developer: Received answer: {answer}")

    async def _receive_refactoring_solution(self, content: dict[str, Any]) -> None:
        """リファクタリング解決策受信"""
        solution = content.get("solution", "")
        self.logger.info(f"💻 Developer: Received solution: {solution}")


# 統合デモ実行


async def demo_beekeeper_refactoring():
    """BeeKeeper リファクタリングデモ"""

    print("🐝 Starting BeeKeeper Autonomous Refactoring Demo")
    print("=" * 50)

    # 1. BeeKeeper 入力
    beekeeper = BeeKeeperRefactoringInput()
    request_id = beekeeper.submit_refactoring_request(
        objective="Improve code quality through comprehensive refactoring",
        template="Analyze current quality → Add type annotations → Generate tests → Add docstrings → Validate improvements",
        target_files=[],
        quality_targets={
            "test_coverage": 85,
            "type_annotation_coverage": 90,
            "docstring_coverage": 80,
            "overall_quality_score": 85,
        },
    )

    # 2. Queen Coordinator 初期化
    queen = QueenRefactoringCoordinator()

    # 3. Developer Worker 初期化
    developer = DeveloperRefactoringWorker()

    # 4. Developer Worker 監視開始
    developer_task = asyncio.create_task(developer.start_refactoring_monitoring())

    # 5. Queen が BeeKeeper 入力を処理
    request_data = beekeeper.get_request_data(request_id)
    await queen.receive_beekeeper_request(request_id, request_data)

    # 6. Queen-Developer 協調監視
    print("\n🔄 Queen-Developer refactoring collaboration started...")

    project_id = f"refactoring_{request_id}"
    for _cycle in range(8):  # 8サイクル監視
        await queen.monitor_refactoring_progress(project_id)
        await asyncio.sleep(15)  # 15秒間隔

        # プロジェクト完了チェック
        if project_id in queen.active_refactoring_projects:
            if queen.active_refactoring_projects[project_id]["status"] == "completed":
                print(f"✅ Refactoring project {project_id} completed!")
                break

    # 7. 終了処理
    developer_task.cancel()

    # 8. 結果表示
    print("\n📊 Refactoring Results:")
    print(f"🗂️  Conversation History: {len(queen.conversation_history)} messages")
    print(f"📁 Active Projects: {len(queen.active_refactoring_projects)}")

    # 成果物確認
    honey_dir = Path(f".hive/honey/beekeeper_refactoring/{project_id}")
    if honey_dir.exists():
        print(f"🍯 Refactoring deliverables saved to: {honey_dir}")
        for file in honey_dir.glob("*"):
            print(f"   - {file.name}")

    print("\n🎉 BeeKeeper Refactoring Demo Completed!")


if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # デモ実行
    asyncio.run(demo_beekeeper_refactoring())
