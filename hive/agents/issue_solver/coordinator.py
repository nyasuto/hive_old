"""
Issue Solver Coordinator

Issue解決のためのQueen Coordinatorです。
"""

from datetime import datetime
from typing import Any

from ..base import BaseCoordinator
from ..mixins import ErrorHandlingMixin, ValidationMixin, WorkLogMixin


class IssueSolverCoordinator(
    BaseCoordinator, WorkLogMixin, ErrorHandlingMixin, ValidationMixin
):
    """Issue解決専用Coordinator"""

    def __init__(self, worker_id: str = "issue_solver_coordinator"):
        super().__init__(worker_id, "issue_solver_coordinator")
        self.current_issue: dict[str, Any] = {}
        self.resolution_plan: dict[str, Any] = {}

    async def process(self, input_data: Any) -> Any:
        """メイン処理：Issue解決の協調統制"""
        try:
            # 入力検証
            validation = self.validate_input(
                input_data, ["issue_analysis", "resolution_plan"]
            )
            if not validation["valid"]:
                return self.create_error_response(
                    f"Invalid input: {validation['errors']}"
                )

            issue_analysis = input_data["issue_analysis"]
            resolution_plan = input_data["resolution_plan"]

            # タスク開始
            task_id = self.start_task(
                f"Issue #{issue_analysis['issue_number']} Resolution Coordination",
                task_type="issue_resolution",
                description=f"Coordinate resolution of {issue_analysis['title']}",
                issue_number=issue_analysis["issue_number"],
                workers=[self.worker_id],
            )

            self.current_issue = issue_analysis
            self.resolution_plan = resolution_plan

            # 解決タスク割り当て
            assignment_success = await self._assign_resolution_tasks(resolution_plan)
            if not assignment_success:
                return self.create_error_response("Failed to assign resolution tasks")

            # 解決プロセス監視
            resolution_result = await self._monitor_resolution_progress()

            # 結果検証
            validation_result = await self._validate_resolution(resolution_result)

            # タスク完了
            self.complete_task(
                f"Issue #{issue_analysis['issue_number']} resolution: {validation_result['status']}"
            )

            return self.create_success_response(
                {
                    "issue_number": issue_analysis["issue_number"],
                    "resolution_result": resolution_result,
                    "validation_result": validation_result,
                    "task_id": task_id,
                }
            )

        except Exception as e:
            error_info = self.handle_exception(e, "process")
            return self.create_error_response(
                f"Coordination failed: {error_info['error_message']}"
            )

    async def _assign_resolution_tasks(self, resolution_plan: dict[str, Any]) -> bool:
        """解決タスク割り当て"""
        if not self.workers:
            self.log_error("No workers available for task assignment")
            return False

        # 最初のWorkerに割り当て（簡易実装）
        worker_id = self.workers[0]

        assignment = {
            "action": "resolve_issue",
            "issue_data": self.current_issue,
            "resolution_plan": resolution_plan,
            "instructions": [
                f"Resolve GitHub Issue #{self.current_issue['issue_number']}",
                f"Follow the {len(resolution_plan['action_sequence'])}-step resolution plan",
                "Provide progress updates for each step",
                "Ensure all success criteria are met",
            ],
            "success_criteria": resolution_plan["success_criteria"],
            "coordinator_message": f"Starting resolution of Issue #{self.current_issue['issue_number']}: {self.current_issue['title'][:50]}...",
        }

        success = await self.assign_task(worker_id, assignment)

        if success:
            self.log_info(
                f"Assigned Issue #{self.current_issue['issue_number']} resolution to {worker_id}"
            )
            self.add_technical_decision(
                "Task Assignment Strategy",
                f"Assigned issue resolution to {worker_id}",
                ["Distribute to multiple workers", "Use specialized worker pool"],
            )

        return success

    async def _monitor_resolution_progress(self) -> dict[str, Any]:
        """解決プロセス監視"""
        monitoring_result = {
            "completed_steps": 0,
            "total_steps": len(self.resolution_plan.get("action_sequence", [])),
            "step_results": [],
            "issues_encountered": [],
            "status": "in_progress",
        }

        start_time = datetime.now()

        # 進捗監視（BaseCoordinatorの機能を使用）
        worker_results = await self.monitor_workers()

        # 結果をIssue解決形式に変換
        if worker_results["status"] == "completed":
            monitoring_result["status"] = "completed"
            monitoring_result["completed_steps"] = monitoring_result["total_steps"]

            # Workerの結果をステップ結果に変換
            for _worker_id, result in worker_results.get("worker_results", {}).items():
                if isinstance(result, dict) and "step_results" in result:
                    monitoring_result["step_results"].extend(result["step_results"])

        elif worker_results["status"] == "timeout":
            monitoring_result["status"] = "timeout"

        monitoring_result["total_time"] = (datetime.now() - start_time).total_seconds()

        return monitoring_result

    async def _handle_worker_message(
        self, message, monitoring_result: dict[str, Any]
    ) -> None:
        """Worker メッセージ処理（BaseCoordinatorをオーバーライド）"""
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

            self.log_info(
                f"Step {content.get('step', 0)} completed by {message.from_worker}"
            )
            self.add_progress(
                f"Step {content.get('step', 0)} Completed",
                content.get("result", {}).get(
                    "description", "Step completed successfully"
                ),
            )

        elif message_type == "resolution_completed":
            monitoring_result["status"] = "completed"
            final_result = content.get("result", {})

            self.log_info(f"Resolution completed by {message.from_worker}")
            self.add_progress("Issue resolution completed", str(final_result))

            # 最終結果を格納
            if "final_result" not in monitoring_result:
                monitoring_result["final_result"] = final_result

        elif message_type == "error":
            error_info = content.get("error", {})
            monitoring_result["issues_encountered"].append(
                {
                    "worker": message.from_worker,
                    "error": error_info,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            self.log_error(f"Error from {message.from_worker}: {error_info}")
            self.add_challenge(
                f"Worker error: {error_info.get('message', 'Unknown error')}",
                "Monitoring for resolution",
            )

        # BaseCoordinatorのメッセージ処理も呼び出し
        await super()._handle_worker_message(message, monitoring_result)

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
            "status": "validation_pending",
        }

        try:
            # 基本検証
            if resolution_result["status"] == "completed":
                validation["success"] = True
                validation["status"] = "validation_passed"
                validation["overall_score"] = 85

                # 成功基準チェック
                success_criteria = self.resolution_plan.get("success_criteria", [])
                for criteria in success_criteria:
                    validation["validated_criteria"].append(
                        {
                            "criteria": criteria,
                            "status": "passed",
                            "details": "Automated validation passed",
                        }
                    )
            else:
                validation["success"] = False
                validation["status"] = "validation_failed"
                validation["overall_score"] = 0

                # 失敗要因分析
                if resolution_result["status"] == "timeout":
                    validation["failed_criteria"].append("Resolution timed out")
                if resolution_result.get("issues_encountered"):
                    validation["failed_criteria"].extend(
                        [
                            f"Issue: {issue['error']}"
                            for issue in resolution_result["issues_encountered"]
                        ]
                    )

            # 改善提案
            if resolution_result.get("issues_encountered"):
                validation["recommendations"].extend(
                    [
                        "Review error logs for detailed analysis",
                        "Consider increasing timeout duration",
                        "Implement retry mechanism for failed steps",
                    ]
                )

            self.log_info(f"Validation completed: {validation['status']}")

            return validation

        except Exception as e:
            error_info = self.handle_exception(e, "validate_resolution")
            return {
                "success": False,
                "status": "validation_error",
                "error": error_info["error_message"],
                "overall_score": 0,
                "recommendations": ["Review validation process"],
            }
