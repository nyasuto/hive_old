"""
自律的エージェント開発テンプレート

このテンプレートを使用して、Hiveの基盤技術を活用した
自律的エージェントを効率的に実装できます。

Usage:
    cp examples/templates/autonomous_agent_template.py \
       examples/poc/my_autonomous_agent.py
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from comb.api import CombAPI
from queen.coordinator import QueenCoordinator
from queen.honey_collector import HoneyCollector
from queen.status_monitor import StatusMonitor
from queen.task_distributor import TaskDistributor


class AutonomousAgent:
    """自律的エージェントの基底クラス"""

    def __init__(
        self,
        agent_id: str,
        specialization: str = "general",
        config: dict[str, Any] | None = None,
    ):
        """
        エージェント初期化

        Args:
            agent_id: エージェント識別子
            specialization: 専門分野
            config: 設定パラメータ
        """
        self.agent_id = agent_id
        self.specialization = specialization
        self.config = config or {}

        # Core Hive Components
        self.comb_api = CombAPI(agent_id)
        self.queen_coordinator = QueenCoordinator(agent_id)
        self.status_monitor = StatusMonitor(agent_id)
        self.task_distributor = TaskDistributor(agent_id)
        self.honey_collector = HoneyCollector(agent_id)

        # ログ設定
        self.logger = logging.getLogger(f"autonomous_agent.{agent_id}")

        # 状態管理
        self.is_running = False
        self.cycle_count = 0
        self.performance_metrics = {
            "tasks_completed": 0,
            "quality_improvements": 0,
            "automation_level": 0.0,
            "error_count": 0,
        }

        # 学習データ
        self.knowledge_base = {}
        self.success_patterns = []
        self.failure_patterns = []

    async def start_autonomous_cycle(self) -> None:
        """自律的実行サイクル開始"""
        self.logger.info(f"Starting autonomous cycle for {self.agent_id}")
        self.is_running = True

        try:
            # 初期化
            await self._initialize_agent()

            # メイン自律ループ
            while self.is_running:
                self.cycle_count += 1
                self.logger.info(f"Starting cycle #{self.cycle_count}")

                # 1. 状況分析
                analysis = await self._analyze_current_state()

                # 2. 行動決定
                actions = await self._decide_actions(analysis)

                # 3. 実行
                results = await self._execute_actions(actions)

                # 4. 学習・改善
                await self._learn_and_improve(results)

                # 5. 次のサイクル準備
                await self._prepare_next_cycle()

                # 休憩間隔
                await asyncio.sleep(self.config.get("cycle_interval", 60))

        except Exception as e:
            self.logger.error(f"Error in autonomous cycle: {e}")
            self.performance_metrics["error_count"] += 1
        finally:
            await self._cleanup()

    async def stop_autonomous_cycle(self) -> None:
        """自律的実行サイクル停止"""
        self.logger.info(f"Stopping autonomous cycle for {self.agent_id}")
        self.is_running = False

    async def _initialize_agent(self) -> None:
        """エージェント初期化処理"""
        # Combディレクトリ構造確保
        self.comb_api.file_handler.ensure_hive_structure()

        # ワークログ開始
        task_id = self.comb_api.start_task(
            f"Autonomous Agent {self.agent_id} Cycle",
            "autonomous_operation",
            f"Starting autonomous operation for {self.specialization} agent",
        )
        self.current_task_id = task_id

        # Queen Coordinator起動
        self.queen_coordinator.start_coordination()

        self.logger.info("Agent initialization completed")

    async def _analyze_current_state(self) -> dict[str, Any]:
        """現在状況の分析"""
        try:
            # プロジェクト状況取得
            project_status = await self._get_project_status()

            # 品質メトリクス取得
            quality_metrics = await self._get_quality_metrics()

            # Worker状況取得
            worker_status = await self._get_worker_status()

            # 監視ダッシュボード取得
            dashboard = self.status_monitor.get_monitoring_dashboard()

            analysis = {
                "timestamp": datetime.now().isoformat(),
                "cycle_count": self.cycle_count,
                "project_status": project_status,
                "quality_metrics": quality_metrics,
                "worker_status": worker_status,
                "monitoring_dashboard": dashboard,
                "performance_metrics": self.performance_metrics.copy(),
            }

            self.logger.info("Current state analysis completed")
            return analysis

        except Exception as e:
            self.logger.error(f"Error in state analysis: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _decide_actions(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """分析結果に基づく行動決定"""
        actions = []

        try:
            # 品質改善が必要な場合
            quality_score = analysis.get("quality_metrics", {}).get("overall_score", 0)
            if quality_score < 80:
                actions.append(
                    {
                        "type": "quality_improvement",
                        "target_score": 90,
                        "priority": "high",
                    }
                )

            # テストカバレッジが低い場合
            coverage = analysis.get("quality_metrics", {}).get("test_coverage", 0)
            if coverage < 80:
                actions.append(
                    {
                        "type": "test_generation",
                        "target_coverage": 85,
                        "priority": "medium",
                    }
                )

            # ボトルネックが検出された場合
            bottlenecks = analysis.get("monitoring_dashboard", {}).get(
                "bottlenecks", []
            )
            if bottlenecks:
                actions.append(
                    {
                        "type": "bottleneck_resolution",
                        "bottlenecks": bottlenecks,
                        "priority": "high",
                    }
                )

            # カスタマイズポイント: 専門分野別の行動決定
            custom_actions = await self._get_specialized_actions(analysis)
            actions.extend(custom_actions)

            self.logger.info(f"Decided on {len(actions)} actions")
            return actions

        except Exception as e:
            self.logger.error(f"Error in action decision: {e}")
            return []

    async def _execute_actions(self, actions: list[dict[str, Any]]) -> dict[str, Any]:
        """アクション実行"""
        results = {
            "successful_actions": 0,
            "failed_actions": 0,
            "improvements": [],
            "errors": [],
        }

        for action in actions:
            try:
                result = await self._execute_single_action(action)
                if result.get("success", False):
                    results["successful_actions"] += 1
                    results["improvements"].append(result)
                    self.performance_metrics["tasks_completed"] += 1
                else:
                    results["failed_actions"] += 1
                    results["errors"].append(result)

            except Exception as e:
                self.logger.error(f"Error executing action {action}: {e}")
                results["failed_actions"] += 1
                results["errors"].append({"action": action, "error": str(e)})

        self.logger.info(
            f"Executed {len(actions)} actions: "
            f"{results['successful_actions']} successful, "
            f"{results['failed_actions']} failed"
        )
        return results

    async def _execute_single_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """単一アクション実行"""
        action_type = action.get("type")

        if action_type == "quality_improvement":
            return await self._improve_code_quality(action)
        elif action_type == "test_generation":
            return await self._generate_tests(action)
        elif action_type == "bottleneck_resolution":
            return await self._resolve_bottlenecks(action)
        else:
            # カスタマイズポイント: 専門分野別のアクション実行
            return await self._execute_specialized_action(action)

    async def _learn_and_improve(self, results: dict[str, Any]) -> None:
        """結果からの学習と改善"""
        try:
            # 成功パターンの学習
            for improvement in results.get("improvements", []):
                self.success_patterns.append(
                    {
                        "pattern": improvement,
                        "timestamp": datetime.now().isoformat(),
                        "cycle": self.cycle_count,
                    }
                )

            # 失敗パターンの学習
            for error in results.get("errors", []):
                self.failure_patterns.append(
                    {
                        "pattern": error,
                        "timestamp": datetime.now().isoformat(),
                        "cycle": self.cycle_count,
                    }
                )

            # パフォーマンス指標更新
            success_rate = results["successful_actions"] / max(
                results["successful_actions"] + results["failed_actions"], 1
            )
            self.performance_metrics["automation_level"] = success_rate

            # 改善提案生成
            improvements = await self._generate_improvements()
            if improvements:
                await self._apply_improvements(improvements)

            # 学習データ保存
            await self._save_learning_data()

            self.logger.info("Learning and improvement cycle completed")

        except Exception as e:
            self.logger.error(f"Error in learning cycle: {e}")

    async def _prepare_next_cycle(self) -> None:
        """次のサイクル準備"""
        try:
            # 進捗記録
            self.comb_api.add_progress(
                f"Cycle #{self.cycle_count} completed",
                f"Automation level: {self.performance_metrics['automation_level']:.2%}, "
                f"Tasks completed: {self.performance_metrics['tasks_completed']}",
            )

            # 一時データクリーンアップ
            await self._cleanup_temporary_data()

            self.logger.info(f"Prepared for next cycle (#{self.cycle_count + 1})")

        except Exception as e:
            self.logger.error(f"Error preparing next cycle: {e}")

    # カスタマイズポイント: 以下のメソッドを継承クラスでオーバーライド

    async def _get_project_status(self) -> dict[str, Any]:
        """プロジェクト状況取得 (カスタマイズ可能)"""
        return {"status": "active", "files_count": 0}

    async def _get_quality_metrics(self) -> dict[str, Any]:
        """品質メトリクス取得 (カスタマイズ可能)"""
        return {"overall_score": 75, "test_coverage": 70}

    async def _get_worker_status(self) -> dict[str, Any]:
        """Worker状況取得 (カスタマイズ可能)"""
        return {"active_workers": 1, "load": "medium"}

    async def _get_specialized_actions(
        self, analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """専門分野別アクション決定 (カスタマイズ必須)"""
        return []

    async def _execute_specialized_action(
        self, action: dict[str, Any]
    ) -> dict[str, Any]:
        """専門分野別アクション実行 (カスタマイズ必須)"""
        return {"success": False, "error": "Not implemented"}

    async def _improve_code_quality(self, action: dict[str, Any]) -> dict[str, Any]:
        """コード品質改善 (カスタマイズ可能)"""
        return {"success": True, "improvement": "Code quality improved"}

    async def _generate_tests(self, action: dict[str, Any]) -> dict[str, Any]:
        """テスト生成 (カスタマイズ可能)"""
        return {"success": True, "improvement": "Tests generated"}

    async def _resolve_bottlenecks(self, action: dict[str, Any]) -> dict[str, Any]:
        """ボトルネック解決 (カスタマイズ可能)"""
        return {"success": True, "improvement": "Bottlenecks resolved"}

    async def _generate_improvements(self) -> list[dict[str, Any]]:
        """改善提案生成 (カスタマイズ可能)"""
        return []

    async def _apply_improvements(self, improvements: list[dict[str, Any]]) -> None:
        """改善適用 (カスタマイズ可能)"""
        pass

    async def _save_learning_data(self) -> None:
        """学習データ保存"""
        try:
            learning_data = {
                "agent_id": self.agent_id,
                "specialization": self.specialization,
                "cycle_count": self.cycle_count,
                "performance_metrics": self.performance_metrics,
                "success_patterns": self.success_patterns[-10:],  # 最新10件
                "failure_patterns": self.failure_patterns[-10:],  # 最新10件
                "knowledge_base": self.knowledge_base,
                "timestamp": datetime.now().isoformat(),
            }

            learning_file = Path(f".hive/learning/{self.agent_id}_learning.json")
            learning_file.parent.mkdir(parents=True, exist_ok=True)

            with open(learning_file, "w", encoding="utf-8") as f:
                json.dump(learning_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving learning data: {e}")

    async def _cleanup_temporary_data(self) -> None:
        """一時データクリーンアップ"""
        pass

    async def _cleanup(self) -> None:
        """終了処理"""
        try:
            # タスク完了
            if hasattr(self, "current_task_id"):
                self.comb_api.complete_task(
                    f"Autonomous cycle completed after {self.cycle_count} cycles"
                )

            # 調整停止
            self.queen_coordinator.stop_coordination()

            # 最終学習データ保存
            await self._save_learning_data()

            self.logger.info("Agent cleanup completed")

        except Exception as e:
            self.logger.error(f"Error in cleanup: {e}")

    def get_performance_report(self) -> dict[str, Any]:
        """パフォーマンスレポート取得"""
        return {
            "agent_id": self.agent_id,
            "specialization": self.specialization,
            "cycle_count": self.cycle_count,
            "is_running": self.is_running,
            "performance_metrics": self.performance_metrics.copy(),
            "success_patterns_count": len(self.success_patterns),
            "failure_patterns_count": len(self.failure_patterns),
            "knowledge_base_size": len(self.knowledge_base),
            "timestamp": datetime.now().isoformat(),
        }


# 使用例とデモ関数


async def demo_autonomous_agent():
    """自律的エージェントのデモ実行"""

    # エージェント作成
    agent = AutonomousAgent(
        agent_id="demo_agent",
        specialization="general_development",
        config={
            "cycle_interval": 30,  # 30秒間隔
            "max_cycles": 3,  # 3サイクルで停止
        },
    )

    print("🤖 Starting Autonomous Agent Demo...")

    try:
        # 短時間のデモ実行
        demo_task = asyncio.create_task(agent.start_autonomous_cycle())

        # 3サイクル後に停止
        await asyncio.sleep(90)  # 3 * 30秒
        await agent.stop_autonomous_cycle()

        # 結果レポート
        report = agent.get_performance_report()
        print("\n📊 Performance Report:")
        print(json.dumps(report, indent=2, ensure_ascii=False))

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
        await agent.stop_autonomous_cycle()


if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # デモ実行
    asyncio.run(demo_autonomous_agent())
