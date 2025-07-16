"""
Issue Solver Agent

統合されたIssue解決エージェントです。
"""

import asyncio
from typing import Any

from ..base import BaseAgent
from ..framework import AgentFramework
from ..mixins import ErrorHandlingMixin, LoggingMixin
from .analyzer import IssueAnalyzer
from .coordinator import IssueSolverCoordinator
from .parser import UserPromptParser
from .worker import IssueSolverWorker


class IssueSolverAgent(BaseAgent, LoggingMixin, ErrorHandlingMixin):
    """Issue解決の統合エージェント"""

    def __init__(self, worker_id: str = "issue_solver_beekeeper"):
        super().__init__(worker_id, "issue_solver_agent")

        # コンポーネント初期化
        self.prompt_parser = UserPromptParser()
        self.analyzer = IssueAnalyzer()

        # フレームワーク初期化
        self.framework = AgentFramework("issue_solver_system")

        # エージェント作成と登録
        self.coordinator = IssueSolverCoordinator("issue_solver_coordinator")
        self.worker = IssueSolverWorker("issue_solver_worker")

        # フレームワーク設定
        self.framework.register_beekeeper(self)
        self.framework.register_coordinator(self.coordinator)
        self.framework.register_worker(self.worker)

        # Worker割り当て
        self.coordinator.add_worker(self.worker.worker_id)

    async def process(self, input_data: Any) -> Any:
        """メイン処理：自然言語プロンプトからIssue解決まで"""
        try:
            # 入力が文字列の場合はプロンプトとして扱う
            if isinstance(input_data, str):
                user_prompt = input_data
            else:
                user_prompt = input_data.get("prompt", "")

            if not user_prompt:
                return self.create_error_response("No prompt provided")

            self.log_info(f"Processing user request: {user_prompt}")

            # タスク開始
            self.start_task(
                "Issue Resolution Request",
                task_type="issue_resolution",
                description=f"Process user request: {user_prompt}",
            )

            # Step 1: プロンプト解析
            self.add_progress("Parsing user prompt")
            parsed_prompt = self.prompt_parser.parse_user_prompt(user_prompt)

            if not parsed_prompt["success"]:
                return self.create_error_response(
                    f"Prompt parsing failed: {parsed_prompt['error']}"
                )

            # Step 2: Issue分析
            self.add_progress("Analyzing issue")
            issue_analysis = await self.analyzer.analyze_issue(
                parsed_prompt["issue_number"], parsed_prompt
            )

            if not issue_analysis["success"]:
                return self.create_error_response(
                    f"Issue analysis failed: {issue_analysis['error']}"
                )

            # Step 3: 意図に応じた処理分岐
            intent = parsed_prompt["intent"]

            if intent == "solve":
                result = await self._solve_issue(issue_analysis, parsed_prompt)
            elif intent == "investigate":
                result = await self._investigate_issue(issue_analysis, parsed_prompt)
            elif intent == "explain":
                result = await self._explain_issue(issue_analysis, parsed_prompt)
            else:
                result = await self._solve_issue(
                    issue_analysis, parsed_prompt
                )  # デフォルト

            # タスク完了
            self.complete_task(f"Request processed: {result.get('success', False)}")

            return result

        except Exception as e:
            error_info = self.handle_exception(e, "process")
            return self.create_error_response(
                f"Processing failed: {error_info['error_message']}"
            )

    async def _solve_issue(
        self, issue_analysis: dict[str, Any], prompt_info: dict[str, Any]
    ) -> dict[str, Any]:
        """Issue解決処理"""
        self.log_info(f"Starting resolution of Issue #{issue_analysis['issue_number']}")

        # Coordinatorに解決依頼
        coordination_input = {
            "issue_analysis": issue_analysis,
            "resolution_plan": issue_analysis["strategy"],
        }

        result = await self.coordinator.process(coordination_input)

        if result["success"]:
            return {
                "success": True,
                "mode": "solve",
                "issue_number": issue_analysis["issue_number"],
                "resolution_result": result["data"]["resolution_result"],
                "validation_result": result["data"]["validation_result"],
                "message": "Issue resolution completed successfully",
            }
        else:
            return {
                "success": False,
                "mode": "solve",
                "issue_number": issue_analysis["issue_number"],
                "error": result.get("error", {}).get("message", "Unknown error"),
                "message": "Issue resolution failed",
            }

    async def _investigate_issue(
        self, issue_analysis: dict[str, Any], prompt_info: dict[str, Any]
    ) -> dict[str, Any]:
        """Issue調査処理"""
        self.log_info(f"Investigating Issue #{issue_analysis['issue_number']}")

        # 調査結果の整理
        investigation_result = {
            "issue_summary": {
                "number": issue_analysis["issue_number"],
                "title": issue_analysis["title"],
                "type": issue_analysis["analysis"]["type"],
                "complexity": issue_analysis["analysis"]["complexity"],
                "technologies": issue_analysis["analysis"]["technologies"],
            },
            "analysis_details": issue_analysis["analysis"],
            "recommended_strategy": issue_analysis["strategy"],
            "estimated_time": issue_analysis["estimated_time"],
            "required_skills": issue_analysis["required_skills"],
        }

        return {
            "success": True,
            "mode": "investigate",
            "issue_number": issue_analysis["issue_number"],
            "investigation_result": investigation_result,
            "message": "Issue investigation completed",
        }

    async def _explain_issue(
        self, issue_analysis: dict[str, Any], prompt_info: dict[str, Any]
    ) -> dict[str, Any]:
        """Issue説明処理"""
        self.log_info(f"Explaining Issue #{issue_analysis['issue_number']}")

        # 説明文生成
        explanation = self._generate_issue_explanation(issue_analysis)

        return {
            "success": True,
            "mode": "explain",
            "issue_number": issue_analysis["issue_number"],
            "explanation": explanation,
            "message": "Issue explanation completed",
        }

    def _generate_issue_explanation(self, issue_analysis: dict[str, Any]) -> str:
        """Issue説明文生成"""
        analysis = issue_analysis["analysis"]
        strategy = issue_analysis["strategy"]

        explanation = f"""Issue #{issue_analysis["issue_number"]} について説明します：

【概要】
タイトル: {issue_analysis["title"]}
タイプ: {analysis["type"]}
複雑度: {analysis["complexity"]}

【技術要素】
関連技術: {", ".join(analysis["technologies"]) if analysis["technologies"] else "なし"}

【解決戦略】
推奨アプローチ: {strategy["recommended_approach"]}
推定工数: {issue_analysis["estimated_time"]}分

【必要なアクション】
"""

        for i, step in enumerate(strategy["action_sequence"], 1):
            action = step["action"]
            explanation += f"{i}. {action['description']} ({action['type']})\n"

        return explanation

    async def start_system(self) -> None:
        """システム開始"""
        self.log_info("Starting Issue Solver Agent system")
        await self.framework.start_system()

    async def stop_system(self) -> None:
        """システム停止"""
        self.log_info("Stopping Issue Solver Agent system")
        await self.framework.stop_system()

    def get_system_status(self) -> dict[str, Any]:
        """システム状態取得"""
        return self.framework.get_system_status()


# 簡単な使用例
async def main():
    """使用例"""
    agent = IssueSolverAgent()

    # Issue解決
    result = await agent.process("Issue 84を解決する")
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
