#!/usr/bin/env python3
"""
分散Issue解決エージェント - 実際のtmux Worker連携版

BeeKeeper-Queen-Worker協調による自然言語Issue解決システム
実際のtmux環境でのWorker連携を実現
"""

import argparse
import asyncio
import re
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

# Import worker communication system
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))
from worker_communication import WorkerCommunicationError, WorkerCommunicator


class MessageType(Enum):
    """メッセージタイプ"""

    REQUEST = "request"
    RESPONSE = "response"
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETION = "task_completion"
    SYSTEM_ALERT = "system_alert"


class MessagePriority(Enum):
    """メッセージ優先度"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class WorkerRole(Enum):
    """Workerの役割"""

    DEVELOPER = "developer"
    TESTER = "tester"
    ANALYZER = "analyzer"
    DOCUMENTER = "documenter"
    REVIEWER = "reviewer"


class UserPromptParser:
    """ユーザープロンプト解析器"""

    def parse_user_prompt(self, prompt: str) -> dict[str, Any]:
        """ユーザープロンプトを解析"""
        prompt_lower = prompt.lower()

        # Issue番号抽出
        issue_number = self._extract_issue_number(prompt)

        # 意図認識
        intent = self._detect_intent(prompt_lower)

        # 優先度推定
        priority = self._estimate_priority(prompt_lower)

        # 複雑度推定
        complexity = self._estimate_complexity(prompt_lower)

        return {
            "original_prompt": prompt,
            "issue_number": issue_number,
            "intent": intent,
            "priority": priority,
            "complexity": complexity,
            "timestamp": datetime.now().isoformat(),
            "requires_investigation": "調査" in prompt or "investigate" in prompt_lower,
            "mentions_urgency": any(
                word in prompt_lower for word in ["緊急", "急いで", "urgent"]
            ),
            "mentions_files": bool(re.search(r"[a-zA-Z0-9_/.-]+\.[a-zA-Z]+", prompt)),
            "mentions_code": "コード" in prompt or "code" in prompt_lower,
            "mentions_test": "テスト" in prompt or "test" in prompt_lower,
        }

    def _extract_issue_number(self, prompt: str) -> str | None:
        """Issue番号抽出"""
        # GitHub URL形式
        url_match = re.search(r"/issues/(\d+)", prompt)
        if url_match:
            return url_match.group(1)

        # Issue #64 形式
        issue_match = re.search(r"issue\s*[#]?(\d+)", prompt.lower())
        if issue_match:
            return issue_match.group(1)

        return None

    def _detect_intent(self, prompt_lower: str) -> str:
        """意図認識"""
        if any(
            word in prompt_lower for word in ["解決", "修正", "fix", "solve", "直す"]
        ):
            return "solve"
        elif any(
            word in prompt_lower for word in ["調査", "確認", "investigate", "analyze"]
        ):
            return "investigate"
        elif any(
            word in prompt_lower for word in ["説明", "理解", "explain", "教えて"]
        ):
            return "explain"
        elif any(
            word in prompt_lower for word in ["実装", "開発", "implement", "develop"]
        ):
            return "implement"
        elif any(word in prompt_lower for word in ["テスト", "test", "testing"]):
            return "test"
        else:
            return "solve"  # デフォルト

    def _estimate_priority(self, prompt_lower: str) -> str:
        """優先度推定"""
        if any(
            word in prompt_lower for word in ["緊急", "急いで", "urgent", "critical"]
        ):
            return "high"
        elif any(
            word in prompt_lower for word in ["後で", "later", "余裕", "when possible"]
        ):
            return "low"
        else:
            return "medium"

    def _estimate_complexity(self, prompt_lower: str) -> str:
        """複雑度推定"""
        complexity_score = 0

        # 複雑度を上げる要因
        if any(word in prompt_lower for word in ["refactor", "architecture", "design"]):
            complexity_score += 2
        if any(word in prompt_lower for word in ["multiple", "複数", "all", "全て"]):
            complexity_score += 1
        if any(word in prompt_lower for word in ["integration", "統合", "system"]):
            complexity_score += 1
        if any(word in prompt_lower for word in ["breaking", "major", "大きな"]):
            complexity_score += 2

        if complexity_score >= 3:
            return "high"
        elif complexity_score >= 1:
            return "medium"
        else:
            return "low"


class DistributedQueenCoordinator:
    """分散Queen協調システム - 実際のWorker連携版"""

    def __init__(self):
        self.agent_id = "distributed-queen-coordinator"
        self.worker_communicator = WorkerCommunicator()
        self.current_session = None

        # Available workers
        self.available_workers = {
            WorkerRole.DEVELOPER: "developer",
            WorkerRole.TESTER: "tester",
            WorkerRole.ANALYZER: "analyzer",
            WorkerRole.DOCUMENTER: "documenter",
            WorkerRole.REVIEWER: "reviewer",
        }

    async def coordinate_issue_resolution(
        self, parsed_request: dict[str, Any]
    ) -> dict[str, Any]:
        """Issue解決の分散協調統制"""
        print("👑 Queen: 承知しました。分散Issue解決を開始します...")

        # セッション開始
        session_id = str(uuid4())
        self.current_session = {
            "session_id": session_id,
            "user_request": parsed_request,
            "start_time": datetime.now().isoformat(),
            "status": "active",
        }

        # 1. Worker状態確認
        print("👑 Queen: Worker状態を確認中...")
        worker_status = self.worker_communicator.monitor_worker_status()

        if not worker_status["session_active"]:
            return {
                "session_id": session_id,
                "status": "error",
                "error": "Tmux session not active. Please run: ./scripts/start-cozy-hive.sh",
                "timestamp": datetime.now().isoformat(),
            }

        # 2. Issue分析
        print("👑 Queen: Issue分析中...")
        issue_analysis = await self._analyze_issue(parsed_request)

        # 3. 解決戦略策定
        print("👑 Queen: 解決戦略を策定中...")
        strategy = await self._create_resolution_strategy(issue_analysis)

        # 4. 実際のWorker分散実行
        print(f"👑 Queen: {len(strategy['workers'])}つのWorkerで分散実行します")
        worker_results = await self._execute_distributed_tasks(strategy, parsed_request)

        # 5. 結果統合
        print("👑 Queen: 結果を統合中...")
        final_result = await self._integrate_results(worker_results, strategy)

        # 6. 品質チェック
        print("👑 Queen: 品質チェック実行中...")
        quality_result = await self._perform_quality_check(final_result)

        # 7. 成果物生成
        deliverables = self._generate_deliverables(final_result, quality_result)

        print("👑 Queen: 全分散タスク完了！実際の成果物を準備しました")

        return {
            "session_id": session_id,
            "status": "completed",
            "issue_analysis": issue_analysis,
            "strategy": strategy,
            "worker_results": worker_results,
            "quality_result": quality_result,
            "deliverables": deliverables,
            "completion_time": datetime.now().isoformat(),
            "summary": self._generate_summary(parsed_request, final_result),
            "distributed_execution": True,
        }

    async def _analyze_issue(self, parsed_request: dict[str, Any]) -> dict[str, Any]:
        """Issue分析"""
        await asyncio.sleep(0.5)  # 分析時間

        complexity_map = {"low": 1, "medium": 2, "high": 3}
        priority_map = {"low": 1, "medium": 2, "high": 3}

        return {
            "issue_number": parsed_request["issue_number"],
            "intent": parsed_request["intent"],
            "complexity": parsed_request["complexity"],
            "priority": parsed_request["priority"],
            "complexity_score": complexity_map.get(parsed_request["complexity"], 2),
            "priority_score": priority_map.get(parsed_request["priority"], 2),
            "estimated_duration": self._estimate_duration(parsed_request),
            "risk_level": self._assess_risk(parsed_request),
            "requires_review": parsed_request["complexity"] in ["medium", "high"],
            "distributed_execution": True,
        }

    async def _create_resolution_strategy(
        self, issue_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """解決戦略策定"""
        await asyncio.sleep(0.3)  # 戦略策定時間

        intent = issue_analysis["intent"]
        complexity = issue_analysis["complexity"]

        # 必要なWorkerを決定
        workers = []
        if intent in ["solve", "implement"]:
            workers.append(WorkerRole.DEVELOPER)
            if complexity in ["medium", "high"]:
                workers.append(WorkerRole.TESTER)

        if intent == "investigate":
            workers.append(WorkerRole.ANALYZER)

        if intent == "explain":
            workers.append(WorkerRole.DOCUMENTER)

        if complexity == "high" or issue_analysis["requires_review"]:
            workers.append(WorkerRole.REVIEWER)

        # デフォルトでDocumenterを含める（説明要求の場合）
        if not workers or intent == "explain":
            workers.append(WorkerRole.DOCUMENTER)

        return {
            "approach": f"{intent}_focused_distributed",
            "workers": workers,
            "parallel_execution": len(workers) > 1,
            "estimated_time": sum(
                self._estimate_worker_time(w, issue_analysis) for w in workers
            ),
            "quality_gates": ["distributed_review", "integration_test", "documentation"]
            if complexity == "high"
            else ["integration_test"],
            "deliverable_format": "comprehensive_distributed"
            if complexity == "high"
            else "standard_distributed",
            "distributed_execution": True,
        }

    async def _execute_distributed_tasks(
        self, strategy: dict[str, Any], parsed_request: dict[str, Any]
    ) -> dict[str, Any]:
        """実際の分散タスク実行"""
        tasks = []

        for worker_role in strategy["workers"]:
            worker_name = self.available_workers[worker_role]

            # Create task for real worker
            task = {
                "worker_name": worker_name,
                "task_id": str(uuid4()),
                "task_type": self._get_task_type(worker_role, parsed_request["intent"]),
                "issue_number": parsed_request["issue_number"],
                "instruction": parsed_request["original_prompt"],
                "intent": parsed_request["intent"],
                "priority": parsed_request["priority"],
                "complexity": parsed_request["complexity"],
                "estimated_time": self._estimate_worker_time(worker_role, {}),
                "timestamp": datetime.now().isoformat(),
            }
            tasks.append(task)

        # Execute tasks in parallel using real workers
        try:
            worker_results = await self.worker_communicator.send_parallel_tasks(tasks)

            # Organize results by worker role
            organized_results = {}
            for result in worker_results:
                if result["status"] == "completed":
                    worker_name = result["worker_name"]
                    organized_results[worker_name] = result
                else:
                    # Handle error cases
                    organized_results[f"error_{result.get('task_id', 'unknown')}"] = (
                        result
                    )

            return organized_results

        except WorkerCommunicationError as e:
            print(f"⚠️ Worker communication error: {e}")
            return {
                "error": {
                    "status": "error",
                    "error_type": "worker_communication",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            }

    def _get_task_type(self, worker_role: WorkerRole, intent: str) -> str:
        """Get task type based on worker role and intent"""
        if worker_role == WorkerRole.DOCUMENTER:
            return "explain_issue" if intent == "explain" else "document_solution"
        elif worker_role == WorkerRole.DEVELOPER:
            return "implement_solution" if intent == "solve" else "analyze_code"
        elif worker_role == WorkerRole.TESTER:
            return "test_solution"
        elif worker_role == WorkerRole.ANALYZER:
            return "investigate_issue"
        elif worker_role == WorkerRole.REVIEWER:
            return "review_solution"
        else:
            return "general_task"

    async def _integrate_results(
        self, worker_results: dict[str, Any], strategy: dict[str, Any]
    ) -> dict[str, Any]:
        """結果統合"""
        await asyncio.sleep(0.3)  # 統合時間

        all_deliverables = []
        all_outputs = []
        successful_workers = []
        failed_workers = []

        for worker_name, result in worker_results.items():
            if result["status"] == "completed":
                successful_workers.append(worker_name)
                if "result" in result and "output" in result["result"]:
                    all_outputs.append(result["result"]["output"])
                    if "content" in result["result"]:
                        all_deliverables.append(result["result"]["content"])
            else:
                failed_workers.append(worker_name)

        return {
            "integration_status": "success"
            if not failed_workers
            else "partial_success",
            "successful_workers": successful_workers,
            "failed_workers": failed_workers,
            "combined_outputs": all_outputs,
            "combined_deliverables": all_deliverables,
            "worker_coordination": "distributed_success",
            "conflicts_resolved": len(failed_workers) == 0,
            "distributed_execution": True,
        }

    async def _perform_quality_check(
        self, integrated_result: dict[str, Any]
    ) -> dict[str, Any]:
        """品質チェック"""
        await asyncio.sleep(0.4)  # 品質チェック時間

        success_rate = (
            len(integrated_result["successful_workers"])
            / (
                len(integrated_result["successful_workers"])
                + len(integrated_result["failed_workers"])
            )
            if (
                integrated_result["successful_workers"]
                or integrated_result["failed_workers"]
            )
            else 1.0
        )

        return {
            "overall_quality": "excellent"
            if success_rate >= 0.8
            else "good"
            if success_rate >= 0.6
            else "needs_improvement",
            "distributed_execution": True,
            "worker_success_rate": f"{success_rate:.1%}",
            "successful_workers": len(integrated_result["successful_workers"]),
            "failed_workers": len(integrated_result["failed_workers"]),
            "integration_quality": "seamless"
            if integrated_result["conflicts_resolved"]
            else "partial",
            "ready_for_deployment": success_rate >= 0.8,
            "distributed_quality_score": success_rate,
        }

    def _generate_deliverables(
        self, final_result: dict[str, Any], quality_result: dict[str, Any]
    ) -> list[str]:
        """成果物生成"""
        deliverables = [
            "✅ 分散Issue解決完了",
            "📡 実際のWorker連携結果",
            "🔄 分散処理統合レポート",
            "📊 Worker成功率レポート",
            "🏗️ 実行Worker一覧",
            "📋 分散実行ログ",
        ]

        if quality_result["ready_for_deployment"]:
            deliverables.append("🚀 分散処理デプロイ準備完了")

        return deliverables

    def _generate_summary(
        self, parsed_request: dict[str, Any], final_result: dict[str, Any]
    ) -> str:
        """サマリー生成"""
        issue_num = parsed_request["issue_number"] or "N/A"
        intent = parsed_request["intent"]
        complexity = parsed_request["complexity"]

        return f"Issue #{issue_num} ({intent}) - 複雑度: {complexity} - 分散処理完了"

    def _estimate_duration(self, parsed_request: dict[str, Any]) -> str:
        """期間推定"""
        complexity_time = {"low": 15, "medium": 30, "high": 60}
        base_time = complexity_time.get(parsed_request["complexity"], 30)

        if parsed_request["mentions_urgency"]:
            base_time = int(base_time * 0.8)  # 緊急時は短縮

        return f"{base_time}分"

    def _assess_risk(self, parsed_request: dict[str, Any]) -> str:
        """リスク評価"""
        risk_score = 0

        if parsed_request["complexity"] == "high":
            risk_score += 2
        if parsed_request["mentions_files"]:
            risk_score += 1
        if parsed_request["mentions_code"]:
            risk_score += 1

        if risk_score >= 3:
            return "high"
        elif risk_score >= 1:
            return "medium"
        else:
            return "low"

    def _estimate_worker_time(
        self, worker_role: WorkerRole, analysis: dict[str, Any]
    ) -> int:
        """Worker作業時間推定"""
        base_times = {
            WorkerRole.DEVELOPER: 3,
            WorkerRole.TESTER: 2,
            WorkerRole.ANALYZER: 2,
            WorkerRole.DOCUMENTER: 1,
            WorkerRole.REVIEWER: 2,
        }
        return base_times.get(worker_role, 1)


class DistributedBeeKeeperAgent:
    """分散BeeKeeper エージェント"""

    def __init__(self):
        self.parser = UserPromptParser()
        self.queen = DistributedQueenCoordinator()
        self.session_history = []

    async def process_user_request(self, user_prompt: str) -> dict[str, Any]:
        """ユーザー要求処理 - 分散実行版"""
        print(f"🐝 BeeKeeper: 「{user_prompt}」")

        # 1. プロンプト解析
        parsed_request = self.parser.parse_user_prompt(user_prompt)
        print(
            f"📋 解析結果: Intent={parsed_request['intent']}, Priority={parsed_request['priority']}, Complexity={parsed_request['complexity']}"
        )

        # 2. 分散Queen協調
        queen_result = await self.queen.coordinate_issue_resolution(parsed_request)

        # 3. セッション履歴記録
        session_record = {
            "user_prompt": user_prompt,
            "parsed_request": parsed_request,
            "queen_result": queen_result,
            "timestamp": datetime.now().isoformat(),
            "execution_type": "distributed",
        }
        self.session_history.append(session_record)

        # 4. 結果表示
        self._display_results(queen_result)

        return {
            "status": "success",
            "session_id": queen_result["session_id"],
            "user_request": parsed_request,
            "resolution_result": queen_result,
            "summary": queen_result["summary"],
            "execution_type": "distributed",
        }

    def _display_results(self, queen_result: dict[str, Any]):
        """結果表示"""
        print("\n" + "=" * 60)
        print("🎉 分散Issue解決完了!")
        print("=" * 60)

        print(f"📊 サマリー: {queen_result['summary']}")
        print(f"⏱️ 処理時間: {queen_result['strategy']['estimated_time']}秒")
        print(f"👥 使用Worker: {len(queen_result['strategy']['workers'])}個")

        if queen_result.get("distributed_execution"):
            print("🌐 実行タイプ: 分散実行 (実際のWorker連携)")

        print("\n📦 成果物:")
        for deliverable in queen_result["deliverables"]:
            print(f"  {deliverable}")

        print(f"\n✅ 品質評価: {queen_result['quality_result']['overall_quality']}")
        print(
            f"📡 Worker成功率: {queen_result['quality_result']['worker_success_rate']}"
        )

        if queen_result["quality_result"]["ready_for_deployment"]:
            print("🚀 分散処理デプロイ準備完了")

        # Show worker results if available
        if "worker_results" in queen_result:
            print("\n🏗️ Worker実行結果:")
            for worker_name, result in queen_result["worker_results"].items():
                if result["status"] == "completed":
                    print(
                        f"  ✅ {worker_name.capitalize()}: {result['result']['output']}"
                    )
                else:
                    print(
                        f"  ❌ {worker_name.capitalize()}: {result.get('error', 'Unknown error')}"
                    )


async def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="分散アーキテクチャ Issue解決エージェント"
    )
    parser.add_argument("prompt", nargs="?", help="自然言語による指示")
    parser.add_argument("--demo", action="store_true", help="デモモード")
    parser.add_argument(
        "--interactive", action="store_true", help="インタラクティブモード"
    )

    args = parser.parse_args()

    beekeeper = DistributedBeeKeeperAgent()

    if args.demo:
        # デモモード
        demo_prompts = [
            "Issue 84の内容を教えて",
            "緊急でissue 64を直してほしい",
            "Issue 101について詳しく調査してください",
            "Issue 95の実装方法を説明してください",
        ]

        print("🎪 分散アーキテクチャ Issue解決エージェント デモ")
        print("=" * 60)

        for i, prompt in enumerate(demo_prompts, 1):
            print(f"\n🎭 デモ {i}/{len(demo_prompts)}")
            print("-" * 40)

            await beekeeper.process_user_request(prompt)

            if i < len(demo_prompts):
                print("\n⏳ 次のデモまで3秒待機...")
                await asyncio.sleep(3)

        print("\n🎉 全デモ完了!")

    elif args.interactive:
        # インタラクティブモード
        print("🐝 分散アーキテクチャ Issue解決エージェント")
        print("=" * 60)
        print("自然言語で指示してください")
        print("例: 'Issue 84の内容を教えて', '緊急でissue 64を直してほしい'")
        print("終了: 'quit', 'exit', 'q'")
        print("=" * 60)

        while True:
            try:
                user_input = input("\n🐝 BeeKeeper> ").strip()

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("👋 Issue解決エージェントを終了します")
                    break

                if user_input:
                    await beekeeper.process_user_request(user_input)

            except KeyboardInterrupt:
                print("\n👋 中断されました")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")

    elif args.prompt:
        # 単発実行
        await beekeeper.process_user_request(args.prompt)

    else:
        # デフォルト: 簡単なデモを実行
        print("🐝 分散アーキテクチャ Issue解決エージェント")
        print("使用方法:")
        print('  python issue_solver_agent_distributed.py "Issue 84の内容を教えて"')
        print("  python issue_solver_agent_distributed.py --demo")
        print("  python issue_solver_agent_distributed.py --interactive")
        print("\n簡単なデモを実行します...\n")

        await beekeeper.process_user_request("Issue 84の内容を教えて")


if __name__ == "__main__":
    asyncio.run(main())
