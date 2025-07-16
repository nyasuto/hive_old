"""
BeeKeeper-Queen-Worker協調フローテンプレート

正しいHiveアーキテクチャ：
1. BeeKeeper（人間）が目的・テンプレート投入
2. Queen/Worker間で自律的会話・協調
3. 成果物出力

Usage:
    # BeeKeeper投入
    python examples/templates/beekeeper_queen_worker_flow.py --input "目的とテンプレート"

    # Queen/Worker自律協調開始
    # 成果物自動出力
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from comb.api import CombAPI
from comb.message_router import MessagePriority, MessageType


class BeeKeeperInput:
    """BeeKeeper（人間）からの入力処理"""

    def __init__(self):
        self.input_data = {}
        self.templates = {}
        self.objectives = {}

    def receive_input(
        self, objective: str, template: str, context: dict[str, Any] = None
    ) -> str:
        """BeeKeeperからの入力受信"""
        input_id = f"input_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.input_data[input_id] = {
            "objective": objective,
            "template": template,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "status": "received",
        }

        print(f"🐝 BeeKeeper Input Received: {input_id}")
        print(f"📋 Objective: {objective}")
        print(f"📝 Template: {template}")

        return input_id

    def get_input_data(self, input_id: str) -> dict[str, Any]:
        """入力データ取得"""
        return self.input_data.get(input_id, {})


class QueenWorkerCoordinator:
    """Queen Worker - 全体調整と指示"""

    def __init__(self):
        self.comb_api = CombAPI("queen")
        self.logger = logging.getLogger("queen_coordinator")
        self.active_projects = {}
        self.conversation_history = []

    async def receive_beekeeper_input(
        self, input_id: str, input_data: dict[str, Any]
    ) -> None:
        """BeeKeeper入力を受信し、プロジェクト開始"""

        # プロジェクト初期化
        project_id = f"project_{input_id}"
        self.active_projects[project_id] = {
            "input_id": input_id,
            "objective": input_data["objective"],
            "template": input_data["template"],
            "context": input_data["context"],
            "status": "planning",
            "created_at": datetime.now().isoformat(),
        }

        # Work Log開始
        task_id = self.comb_api.start_task(
            f"BeeKeeper Project: {input_data['objective']}",
            "beekeeper_project",
            f"Starting project based on BeeKeeper input: {input_data['objective']}",
            workers=["queen", "developer"],
        )

        self.active_projects[project_id]["task_id"] = task_id

        # 初期分析と計画
        plan = await self._analyze_and_plan(input_data)
        self.active_projects[project_id]["plan"] = plan

        # Developer Workerに初期指示
        await self._send_initial_instructions(project_id, plan)

        self.logger.info(f"👑 Queen: Started project {project_id}")

    async def _analyze_and_plan(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """BeeKeeper入力の分析と計画策定"""

        objective = input_data["objective"]
        template = input_data["template"]
        # context = input_data["context"]  # 現在未使用

        # 目的分析
        plan = {
            "objective": objective,
            "template": template,
            "analysis": {
                "complexity": "medium",  # 簡易分析
                "estimated_steps": 3,
                "required_skills": ["implementation", "testing", "documentation"],
            },
            "execution_plan": [
                {
                    "step": 1,
                    "action": "initial_implementation",
                    "description": f"Implement core functionality for: {objective}",
                    "template_section": template,
                },
                {
                    "step": 2,
                    "action": "quality_check",
                    "description": "Validate implementation quality and completeness",
                },
                {
                    "step": 3,
                    "action": "documentation",
                    "description": "Create documentation and finalize deliverables",
                },
            ],
            "success_criteria": [
                "Objective fulfilled",
                "Template properly applied",
                "Quality standards met",
            ],
        }

        # Work Log記録
        self.comb_api.add_progress(
            "Project Analysis Completed",
            f"Analyzed BeeKeeper input and created {len(plan['execution_plan'])}-step plan",
        )

        self.comb_api.add_technical_decision(
            "Project Execution Strategy",
            f"Planned {len(plan['execution_plan'])} steps for objective: {objective}",
            ["Direct implementation", "Alternative approaches"],
        )

        return plan

    async def _send_initial_instructions(
        self, project_id: str, plan: dict[str, Any]
    ) -> None:
        """Developer Workerに初期指示送信"""

        project = self.active_projects[project_id]

        instructions = {
            "action": "start_project",
            "project_id": project_id,
            "objective": project["objective"],
            "template": project["template"],
            "context": project["context"],
            "execution_plan": plan["execution_plan"],
            "success_criteria": plan["success_criteria"],
            "queen_message": f"🐝 Starting project based on BeeKeeper input: {project['objective']}",
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
                    "type": "initial_instructions",
                    "content": instructions,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            self.logger.info(f"👑 Queen: Sent initial instructions for {project_id}")

    async def monitor_and_coordinate(self, project_id: str) -> None:
        """プロジェクト監視と協調"""

        project = self.active_projects.get(project_id)
        if not project:
            return

        # Developer Workerからの応答を監視
        messages = self.comb_api.receive_messages()

        for message in messages:
            if message.from_worker == "developer":
                await self._handle_developer_response(project_id, message)

    async def _handle_developer_response(self, project_id: str, message) -> None:
        """Developer Worker応答処理"""

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

        # 応答種別に応じた処理
        if response_type == "progress_update":
            await self._handle_progress_update(project_id, content)
        elif response_type == "question":
            await self._handle_developer_question(project_id, content)
        elif response_type == "completion":
            await self._handle_project_completion(project_id, content)
        elif response_type == "issue":
            await self._handle_developer_issue(project_id, content)

        self.logger.info(f"👑 Queen: Handled {response_type} from developer")

    async def _handle_progress_update(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """進捗更新処理"""

        progress = content.get("progress", {})

        # Work Log記録
        self.comb_api.add_progress(
            f"Developer Progress: {progress.get('current_step', 'Unknown')}",
            progress.get("description", "Progress update received"),
        )

        # 必要に応じて追加指示
        if progress.get("needs_guidance", False):
            guidance = await self._provide_guidance(project_id, progress)

            guidance_message = {
                "action": "guidance",
                "project_id": project_id,
                "guidance": guidance,
                "queen_message": "👑 Here's guidance for your current step",
            }

            self.comb_api.send_message(
                to_worker="developer",
                content=guidance_message,
                message_type=MessageType.RESPONSE,
                priority=MessagePriority.MEDIUM,
            )

    async def _handle_developer_question(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """Developer質問処理"""

        question = content.get("question", "")
        context = content.get("context", {})

        # 質問分析と回答生成
        answer = await self._generate_answer(project_id, question, context)

        answer_message = {
            "action": "answer",
            "project_id": project_id,
            "question": question,
            "answer": answer,
            "queen_message": f"👑 Answer to your question: {question}",
        }

        self.comb_api.send_message(
            to_worker="developer",
            content=answer_message,
            message_type=MessageType.RESPONSE,
            priority=MessagePriority.HIGH,
        )

        # Work Log記録
        self.comb_api.add_progress(
            "Developer Question Answered", f"Q: {question}, A: {answer}"
        )

    async def _handle_project_completion(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """プロジェクト完了処理"""

        deliverables = content.get("deliverables", {})
        # summary = content.get("summary", "")  # 現在未使用

        # プロジェクト終了処理
        project = self.active_projects[project_id]
        project["status"] = "completed"
        project["deliverables"] = deliverables
        project["completed_at"] = datetime.now().isoformat()

        # Work Log完了
        task_id = project.get("task_id")
        if task_id:
            self.comb_api.complete_task(
                f"Project completed successfully. Deliverables: {list(deliverables.keys())}"
            )

        # 成果物を BeeKeeper 向けに出力
        await self._output_deliverables(project_id, deliverables)

        self.logger.info(f"👑 Queen: Project {project_id} completed")

    async def _handle_developer_issue(
        self, project_id: str, content: dict[str, Any]
    ) -> None:
        """Developer課題処理"""

        issue = content.get("issue", "")
        severity = content.get("severity", "medium")

        # 課題分析と解決策提案
        solution = await self._analyze_and_solve_issue(project_id, issue, severity)

        solution_message = {
            "action": "issue_solution",
            "project_id": project_id,
            "issue": issue,
            "solution": solution,
            "queen_message": f"👑 Solution for issue: {issue}",
        }

        self.comb_api.send_message(
            to_worker="developer",
            content=solution_message,
            message_type=MessageType.RESPONSE,
            priority=MessagePriority.HIGH,
        )

        # Work Log記録
        self.comb_api.add_challenge(issue, solution)

    async def _provide_guidance(self, project_id: str, progress: dict[str, Any]) -> str:
        """指導提供"""
        current_step = progress.get("current_step", "unknown")
        project = self.active_projects[project_id]

        # 実行計画から適切な指導を生成
        plan = project.get("plan", {})
        execution_plan = plan.get("execution_plan", [])

        for step in execution_plan:
            if step["action"] == current_step:
                return f"For {current_step}: {step['description']}"

        return f"Continue with {current_step} according to the original plan"

    async def _generate_answer(
        self, project_id: str, question: str, context: dict[str, Any]
    ) -> str:
        """回答生成"""
        project = self.active_projects[project_id]

        # 簡易回答生成（実際にはより複雑な処理）
        if "objective" in question.lower():
            return f"The main objective is: {project['objective']}"
        elif "template" in question.lower():
            return f"Please follow this template: {project['template']}"
        else:
            return "Please refer to the original BeeKeeper input and project plan for guidance"

    async def _analyze_and_solve_issue(
        self, project_id: str, issue: str, severity: str
    ) -> str:
        """課題分析と解決策"""
        # 簡易解決策生成
        if severity == "high":
            return f"High priority issue: {issue}. Please escalate or seek immediate assistance."
        else:
            return f"For issue '{issue}', try breaking it down into smaller steps or refer to the template."

    async def _output_deliverables(
        self, project_id: str, deliverables: dict[str, Any]
    ) -> None:
        """成果物出力"""
        project = self.active_projects[project_id]

        # 成果物ファイル保存
        output_dir = Path(f".hive/honey/beekeeper_projects/{project_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 成果物サマリー
        summary = {
            "project_id": project_id,
            "beekeeper_objective": project["objective"],
            "template_used": project["template"],
            "deliverables": deliverables,
            "conversation_history": self.conversation_history,
            "completion_time": datetime.now().isoformat(),
        }

        # ファイル保存
        summary_file = output_dir / "project_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        # 各成果物保存
        for name, content in deliverables.items():
            deliverable_file = output_dir / f"{name}.txt"
            with open(deliverable_file, "w", encoding="utf-8") as f:
                f.write(str(content))

        print(f"🍯 Deliverables saved to: {output_dir}")
        print(f"📋 Project Summary: {summary_file}")


class DeveloperWorker:
    """Developer Worker - 実装担当"""

    def __init__(self):
        self.comb_api = CombAPI("developer")
        self.logger = logging.getLogger("developer_worker")
        self.active_projects = {}
        self.work_progress = {}

    async def start_monitoring(self) -> None:
        """Queen からの指示監視開始"""
        self.logger.info("💻 Developer: Starting monitoring for Queen instructions")

        while True:
            try:
                # Queen からのメッセージ確認
                messages = self.comb_api.receive_messages()

                for message in messages:
                    if message.from_worker == "queen":
                        await self._handle_queen_message(message)

                await asyncio.sleep(5)  # 5秒間隔で監視

            except Exception as e:
                self.logger.error(f"💻 Developer: Error in monitoring: {e}")
                await asyncio.sleep(10)

    async def _handle_queen_message(self, message) -> None:
        """Queen メッセージ処理"""
        content = message.content
        action = content.get("action", "unknown")

        if action == "start_project":
            await self._start_project(content)
        elif action == "guidance":
            await self._receive_guidance(content)
        elif action == "answer":
            await self._receive_answer(content)
        elif action == "issue_solution":
            await self._receive_solution(content)

        self.logger.info(f"💻 Developer: Handled {action} from Queen")

    async def _start_project(self, content: dict[str, Any]) -> None:
        """プロジェクト開始"""
        project_id = content["project_id"]
        objective = content["objective"]
        template = content["template"]
        execution_plan = content["execution_plan"]

        # プロジェクト初期化
        self.active_projects[project_id] = {
            "objective": objective,
            "template": template,
            "execution_plan": execution_plan,
            "current_step": 1,
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
        }

        # 進捗開始
        self.work_progress[project_id] = {
            "steps_completed": 0,
            "current_task": "initial_implementation",
            "issues": [],
        }

        # 実行開始
        await self._execute_project(project_id)

    async def _execute_project(self, project_id: str) -> None:
        """プロジェクト実行"""
        project = self.active_projects[project_id]
        execution_plan = project["execution_plan"]

        # 各ステップを実行
        for step in execution_plan:
            step_number = step["step"]
            action = step["action"]
            description = step["description"]

            # 進捗報告
            await self._report_progress(project_id, step_number, action, description)

            # ステップ実行
            result = await self._execute_step(project_id, step)

            # 結果に応じた処理
            if result.get("success", False):
                self.work_progress[project_id]["steps_completed"] += 1
            else:
                # 課題発生時の処理
                await self._report_issue(
                    project_id, result.get("issue", "Unknown issue")
                )
                break

        # 全ステップ完了時
        if self.work_progress[project_id]["steps_completed"] == len(execution_plan):
            await self._complete_project(project_id)

    async def _execute_step(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """個別ステップ実行"""
        action = step["action"]
        # description = step["description"]  # 現在未使用

        # 実際の実装 (簡易版)
        if action == "initial_implementation":
            return await self._implement_core_functionality(project_id, step)
        elif action == "quality_check":
            return await self._perform_quality_check(project_id, step)
        elif action == "documentation":
            return await self._create_documentation(project_id, step)
        else:
            return {"success": False, "issue": f"Unknown action: {action}"}

    async def _implement_core_functionality(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """コア機能実装"""
        project = self.active_projects[project_id]

        # 実装 (デモ用)
        implementation = {
            "objective": project["objective"],
            "template_applied": project["template"],
            "implementation_details": "Core functionality implemented according to BeeKeeper specifications",
            "code_structure": "Modular design with proper separation of concerns",
            "status": "completed",
        }

        return {"success": True, "implementation": implementation}

    async def _perform_quality_check(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """品質チェック"""
        # 品質チェック実行 (デモ用)
        quality_report = {
            "code_quality": "Good",
            "test_coverage": "85%",
            "performance": "Acceptable",
            "security": "No issues found",
            "maintainability": "High",
        }

        return {"success": True, "quality_report": quality_report}

    async def _create_documentation(
        self, project_id: str, step: dict[str, Any]
    ) -> dict[str, Any]:
        """ドキュメント作成"""
        project = self.active_projects[project_id]

        # ドキュメント生成 (デモ用)
        documentation = {
            "user_guide": f"User guide for {project['objective']}",
            "api_documentation": "API endpoints and usage examples",
            "setup_instructions": "Installation and configuration steps",
            "troubleshooting": "Common issues and solutions",
        }

        return {"success": True, "documentation": documentation}

    async def _report_progress(
        self, project_id: str, step_number: int, action: str, description: str
    ) -> None:
        """進捗報告"""
        progress_update = {
            "type": "progress_update",
            "project_id": project_id,
            "progress": {
                "current_step": step_number,
                "action": action,
                "description": description,
                "timestamp": datetime.now().isoformat(),
            },
        }

        self.comb_api.send_message(
            to_worker="queen",
            content=progress_update,
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.MEDIUM,
        )

    async def _report_issue(self, project_id: str, issue: str) -> None:
        """課題報告"""
        issue_report = {
            "type": "issue",
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

    async def _complete_project(self, project_id: str) -> None:
        """プロジェクト完了"""
        project = self.active_projects[project_id]

        # 最終成果物作成
        deliverables = {
            "implementation": "Core functionality completed",
            "quality_report": "All quality checks passed",
            "documentation": "Complete user and technical documentation",
            "summary": f"Successfully completed: {project['objective']}",
        }

        completion_report = {
            "type": "completion",
            "project_id": project_id,
            "deliverables": deliverables,
            "summary": "Project completed successfully according to BeeKeeper specifications",
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

    async def _receive_guidance(self, content: dict[str, Any]) -> None:
        """指導受信"""
        guidance = content.get("guidance", "")
        self.logger.info(f"💻 Developer: Received guidance: {guidance}")

    async def _receive_answer(self, content: dict[str, Any]) -> None:
        """回答受信"""
        answer = content.get("answer", "")
        self.logger.info(f"💻 Developer: Received answer: {answer}")

    async def _receive_solution(self, content: dict[str, Any]) -> None:
        """解決策受信"""
        solution = content.get("solution", "")
        self.logger.info(f"💻 Developer: Received solution: {solution}")


# 統合デモ実行


async def demo_beekeeper_queen_worker_flow():
    """BeeKeeper-Queen-Worker フローデモ"""

    print("🐝 Starting BeeKeeper-Queen-Worker Flow Demo")
    print("=" * 50)

    # 1. BeeKeeper 入力
    beekeeper = BeeKeeperInput()
    input_id = beekeeper.receive_input(
        objective="Create a simple task management system",
        template="Web application with CRUD operations for tasks",
        context={"technology": "Python", "framework": "Flask"},
    )

    # 2. Queen Coordinator 初期化
    queen = QueenWorkerCoordinator()

    # 3. Developer Worker 初期化
    developer = DeveloperWorker()

    # 4. Developer Worker 監視開始
    developer_task = asyncio.create_task(developer.start_monitoring())

    # 5. Queen が BeeKeeper 入力を処理
    input_data = beekeeper.get_input_data(input_id)
    await queen.receive_beekeeper_input(input_id, input_data)

    # 6. Queen-Developer 協調監視
    print("\n🔄 Queen-Developer collaboration started...")

    project_id = f"project_{input_id}"
    for _cycle in range(5):  # 5サイクル監視
        await queen.monitor_and_coordinate(project_id)
        await asyncio.sleep(10)  # 10秒間隔

        # プロジェクト完了チェック
        if project_id in queen.active_projects:
            if queen.active_projects[project_id]["status"] == "completed":
                print(f"✅ Project {project_id} completed!")
                break

    # 7. 終了処理
    developer_task.cancel()

    # 8. 結果表示
    print("\n📊 Final Results:")
    print(f"🗂️  Conversation History: {len(queen.conversation_history)} messages")
    print(f"📁 Active Projects: {len(queen.active_projects)}")

    # 成果物確認
    honey_dir = Path(f".hive/honey/beekeeper_projects/{project_id}")
    if honey_dir.exists():
        print(f"🍯 Deliverables saved to: {honey_dir}")
        for file in honey_dir.glob("*"):
            print(f"   - {file.name}")


if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # デモ実行
    asyncio.run(demo_beekeeper_queen_worker_flow())
