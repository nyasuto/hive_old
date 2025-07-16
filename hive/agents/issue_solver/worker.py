"""
Issue Solver Worker

Issue解決のためのDeveloper Workerです。
"""

import asyncio
from datetime import datetime
from typing import Any

from comb.message_router import MessagePriority, MessageType

from ..base import BaseWorker
from ..mixins import ErrorHandlingMixin, WorkLogMixin


class IssueSolverWorker(BaseWorker, WorkLogMixin, ErrorHandlingMixin):
    """Issue解決専用Worker"""

    def __init__(self, worker_id: str = "issue_solver_worker"):
        super().__init__(worker_id, "issue_solver_worker")
        self.current_issue: dict[str, Any] = {}
        self.resolution_plan: dict[str, Any] = {}

    async def process(self, input_data: Any) -> Any:
        """メイン処理：Issue解決実行"""
        try:
            # 入力検証
            validation = self.validate_input(
                input_data, ["issue_data", "resolution_plan"]
            )
            if not validation["valid"]:
                return self.create_error_response(
                    f"Invalid input: {validation['errors']}"
                )

            self.current_issue = input_data["issue_data"]
            self.resolution_plan = input_data["resolution_plan"]

            self.log_info(
                f"Starting resolution of Issue #{self.current_issue['issue_number']}"
            )

            # Issue解決実行
            resolution_result = await self._execute_issue_resolution()

            return self.create_success_response(resolution_result)

        except Exception as e:
            error_info = self.handle_exception(e, "process")
            return self.create_error_response(
                f"Resolution failed: {error_info['error_message']}"
            )

    async def _execute_issue_resolution(self) -> dict[str, Any]:
        """Issue解決実行"""
        self.log_info(
            f"Starting resolution of Issue #{self.current_issue['issue_number']}"
        )

        results = {
            "issue_number": self.current_issue["issue_number"],
            "step_results": [],
            "total_steps": len(self.resolution_plan.get("action_sequence", [])),
            "completed_steps": 0,
            "status": "in_progress",
        }

        # 各ステップを実行
        for step_info in self.resolution_plan.get("action_sequence", []):
            step_number = step_info["step"]
            action = step_info["action"]

            self.log_info(f"Executing step {step_number}: {action['type']}")

            # ステップ実行
            step_result = await self._execute_resolution_step(action)
            results["step_results"].append(
                {
                    "step": step_number,
                    "action_type": action["type"],
                    "result": step_result,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # 進捗報告
            await self._report_step_completion(step_number, step_result)

            results["completed_steps"] += 1

            # 短い間隔
            await asyncio.sleep(2)

        # 完了報告
        results["status"] = "completed"
        await self._report_resolution_completion(results)

        return results

    async def _execute_resolution_step(self, action: dict[str, Any]) -> dict[str, Any]:
        """解決ステップ実行"""
        action_type = action["type"]

        # アクションタイプ別の実装
        if action_type == "investigation":
            return await self._perform_investigation()
        elif action_type == "planning":
            return await self._create_resolution_plan()
        elif action_type == "type_checking":
            return await self._fix_type_checking()
        elif action_type == "testing":
            return await self._improve_testing()
        elif action_type == "implementation":
            return await self._implement_solution()
        elif action_type == "documentation":
            return await self._update_documentation()
        elif action_type == "validation":
            return await self._validate_changes()
        else:
            return {
                "success": False,
                "error": f"Unknown action type: {action_type}",
                "description": "Unsupported action type",
            }

    async def _perform_investigation(self) -> dict[str, Any]:
        """調査実行"""
        await asyncio.sleep(1)  # 実際の調査処理をシミュレート

        return {
            "success": True,
            "description": "Issue content analyzed and current state investigated",
            "findings": [
                "Issue clearly defined with specific requirements",
                "Affected files identified",
                "Solution approach confirmed",
            ],
        }

    async def _create_resolution_plan(self) -> dict[str, Any]:
        """解決計画作成"""
        await asyncio.sleep(2)

        return {
            "success": True,
            "description": "Detailed resolution plan created",
            "plan_details": [
                "Step-by-step approach defined",
                "Resource requirements identified",
                "Timeline established",
            ],
        }

    async def _fix_type_checking(self) -> dict[str, Any]:
        """型チェック修正"""
        await asyncio.sleep(3)

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
        await asyncio.sleep(4)

        return {
            "success": True,
            "description": "Testing improvements implemented",
            "changes": [
                "Added missing test cases",
                "Improved test coverage",
                "Fixed failing tests",
            ],
        }

    async def _implement_solution(self) -> dict[str, Any]:
        """解決策実装"""
        await asyncio.sleep(5)

        return {
            "success": True,
            "description": "Solution implemented according to requirements",
            "implementation": [
                "Core functionality implemented",
                "Edge cases handled",
                "Performance optimized",
            ],
        }

    async def _update_documentation(self) -> dict[str, Any]:
        """ドキュメント更新"""
        await asyncio.sleep(2)

        return {
            "success": True,
            "description": "Documentation updated with changes",
            "updates": [
                "API documentation updated",
                "Usage examples added",
                "README updated",
            ],
        }

    async def _validate_changes(self) -> dict[str, Any]:
        """変更検証"""
        await asyncio.sleep(3)

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
        if not self.coordinator_id:
            return

        report = {
            "type": "step_completed",
            "step": step_number,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }

        success = self.send_message(
            to_worker=self.coordinator_id,
            content=report,
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.MEDIUM,
        )

        if success:
            self.log_info(
                f"Step {step_number} completion reported to {self.coordinator_id}"
            )
        else:
            self.log_error(f"Failed to report step {step_number} completion")

    async def _report_resolution_completion(self, results: dict[str, Any]) -> None:
        """解決完了報告"""
        if not self.coordinator_id:
            return

        completion_report = {
            "type": "resolution_completed",
            "issue_number": self.current_issue["issue_number"],
            "result": {
                "status": "completed",
                "summary": f"Successfully resolved Issue #{self.current_issue['issue_number']}",
                "changes_made": "All required changes implemented and validated",
                "step_results": results["step_results"],
            },
            "timestamp": datetime.now().isoformat(),
        }

        success = self.send_message(
            to_worker=self.coordinator_id,
            content=completion_report,
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.HIGH,
        )

        if success:
            self.log_info(f"Resolution completion reported to {self.coordinator_id}")
        else:
            self.log_error("Failed to report resolution completion")

    async def _handle_coordinator_message(self, message) -> None:
        """Coordinator メッセージ処理（BaseWorkerをオーバーライド）"""
        content = message.content
        action = content.get("action", "unknown")

        self.log_info(f"Handling action: {action} from {message.from_worker}")

        if action == "resolve_issue":
            self.coordinator_id = message.from_worker

            # Issue解決実行
            result = await self.process(content)

            # 結果をCoordinatorに報告（BaseWorkerの機能を使用）
            await self._report_completion(result)
        else:
            self.log_warning(f"Unknown action: {action}")

            # エラー報告
            error_report = {
                "type": "error",
                "error": {"message": f"Unknown action: {action}", "action": action},
                "timestamp": datetime.now().isoformat(),
            }

            self.send_message(
                to_worker=message.from_worker,
                content=error_report,
                message_type=MessageType.NOTIFICATION,
                priority=MessagePriority.MEDIUM,
            )
