"""
Comb API中心の自律的エージェントテンプレート

現在のHiveアーキテクチャに完全準拠し、Comb APIを統一インターフェースとして
使用する自律的エージェントの実装テンプレート。

重要なアーキテクチャ原則:
- 全ての通信はComb API経由
- Queen ⟷ Developer Worker協調パターン
- Work Log Manager活用による学習機能
- 直接インポート禁止

Usage:
    cp examples/templates/comb_api_autonomous_agent.py \
       examples/poc/my_comb_autonomous_agent.py
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

# 現在のアーキテクチャ準拠: Comb API のみ使用
from comb.api import CombAPI
from comb.message_router import MessagePriority, MessageType


class CombAutonomousAgent:
    """
    Comb API中心の自律的エージェント基底クラス

    現在のHiveアーキテクチャに完全準拠:
    - 🧠 Queen Coordinator (63%カバレッジ) 協調
    - 💬 Comb Communication (85%カバレッジ) 使用
    - 📝 Work Log Manager (95%カバレッジ) 活用
    """

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

        # 現在のアーキテクチャ準拠: Comb API統一インターフェース
        self.comb_api = CombAPI(agent_id)

        # ログ設定
        self.logger = logging.getLogger(f"comb_autonomous_agent.{agent_id}")

        # 状態管理
        self.is_running = False
        self.cycle_count = 0
        self.current_task_id = None

        # パフォーマンス指標
        self.performance_metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "tasks_completed": 0,
            "queen_collaborations": 0,
            "developer_collaborations": 0,
            "work_log_entries": 0,
            "automation_level": 0.0,
        }

        # 学習データ (Work Log Manager活用)
        self.collaboration_patterns = []
        self.success_patterns = []
        self.improvement_suggestions = []

    async def start_autonomous_cycle(self) -> None:
        """自律的実行サイクル開始"""
        self.logger.info(f"🤖 Starting Comb API autonomous cycle for {self.agent_id}")
        self.is_running = True

        try:
            # 初期化
            await self._initialize_agent()

            # Queen Workerとの初期協調
            await self._establish_queen_collaboration()

            # メイン自律ループ
            while self.is_running:
                self.cycle_count += 1
                self.logger.info(f"🔄 Starting cycle #{self.cycle_count}")

                # 1. 現在状況をQueenに報告・分析要求
                situation_analysis = await self._request_queen_analysis()

                # 2. 分析結果に基づく自律的行動決定
                actions = await self._decide_autonomous_actions(situation_analysis)

                # 3. Worker間協調でアクション実行
                results = await self._execute_collaborative_actions(actions)

                # 4. 結果をWork Log Managerに記録・学習
                await self._learn_from_collaboration(results)

                # 5. 次のサイクル準備
                await self._prepare_next_cycle()

                # 休憩間隔
                await asyncio.sleep(self.config.get("cycle_interval", 90))

        except Exception as e:
            self.logger.error(f"❌ Error in autonomous cycle: {e}")
            await self._handle_cycle_error(e)
        finally:
            await self._cleanup_agent()

    async def stop_autonomous_cycle(self) -> None:
        """自律的実行サイクル停止"""
        self.logger.info(f"⏹️ Stopping autonomous cycle for {self.agent_id}")
        self.is_running = False

    async def _initialize_agent(self) -> None:
        """エージェント初期化処理"""
        # Work Log Manager活用: タスク開始
        self.current_task_id = self.comb_api.start_task(
            f"Autonomous Agent {self.agent_id} Operation",
            "autonomous_collaboration",
            f"Starting autonomous {self.specialization} operation with Comb API",
            workers=[self.agent_id, "queen", "developer"],
        )

        # 進捗記録
        self.comb_api.add_progress(
            "Agent Initialization",
            f"Initialized {self.specialization} agent with Comb API integration",
        )

        # 技術決定記録
        self.comb_api.add_technical_decision(
            "Comb API Unified Interface",
            "Using Comb API as unified interface for all communications",
            ["Direct imports", "Individual component access"],
        )

        self.performance_metrics["work_log_entries"] += 3
        self.logger.info("✅ Agent initialization with Work Log Manager completed")

    async def _establish_queen_collaboration(self) -> None:
        """Queen Workerとの協調関係確立"""
        try:
            # Queen Workerに自己紹介
            introduction = {
                "agent_id": self.agent_id,
                "specialization": self.specialization,
                "capabilities": await self._get_agent_capabilities(),
                "collaboration_request": True,
            }

            success = self.comb_api.send_message(
                to_worker="queen",
                content=introduction,
                message_type=MessageType.REQUEST,
                priority=MessagePriority.HIGH,
            )

            if success:
                self.performance_metrics["messages_sent"] += 1
                self.performance_metrics["queen_collaborations"] += 1

                # Work Log記録
                self.comb_api.add_progress(
                    "Queen Collaboration Established",
                    "Successfully established collaboration with Queen Worker",
                )

                self.logger.info("👑 Queen collaboration established")
            else:
                self.logger.warning("⚠️ Failed to establish Queen collaboration")

        except Exception as e:
            self.logger.error(f"❌ Error establishing Queen collaboration: {e}")

    async def _request_queen_analysis(self) -> dict[str, Any]:
        """Queen Workerに状況分析要求"""
        try:
            # 現在の状況データ収集
            current_situation = {
                "agent_id": self.agent_id,
                "cycle_count": self.cycle_count,
                "performance_metrics": self.performance_metrics.copy(),
                "specialization": self.specialization,
                "analysis_request": {
                    "type": "situation_analysis",
                    "focus_areas": await self._get_analysis_focus_areas(),
                    "priority": "high",
                },
            }

            # Queen Workerに分析要求
            success = self.comb_api.send_message(
                to_worker="queen",
                content=current_situation,
                message_type=MessageType.REQUEST,
                priority=MessagePriority.HIGH,
            )

            if success:
                self.performance_metrics["messages_sent"] += 1
                self.performance_metrics["queen_collaborations"] += 1

                # 応答待機 (簡易実装)
                await asyncio.sleep(2)

                # Queen Workerからの応答を確認
                messages = self.comb_api.receive_messages()
                queen_response = None

                for message in messages:
                    if (
                        message.from_worker == "queen"
                        and message.content.get("type") == "analysis_response"
                    ):
                        queen_response = message.content
                        self.performance_metrics["messages_received"] += 1
                        break

                if queen_response:
                    self.logger.info("👑 Received Queen analysis response")
                    return queen_response
                else:
                    self.logger.warning("⚠️ No Queen analysis response received")
                    return await self._generate_fallback_analysis()

            return await self._generate_fallback_analysis()

        except Exception as e:
            self.logger.error(f"❌ Error requesting Queen analysis: {e}")
            return await self._generate_fallback_analysis()

    async def _decide_autonomous_actions(
        self, analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """分析結果に基づく自律的行動決定"""
        actions = []

        try:
            # 品質改善アクション
            quality_score = analysis.get("quality_metrics", {}).get("score", 75)
            if quality_score < 80:
                actions.append(
                    {
                        "type": "quality_improvement",
                        "target_worker": "developer",
                        "priority": "high",
                        "details": {
                            "current_score": quality_score,
                            "target_score": 85,
                            "improvement_areas": analysis.get("improvement_areas", []),
                        },
                    }
                )

            # 専門分野別アクション
            specialized_actions = await self._get_specialized_actions(analysis)
            actions.extend(specialized_actions)

            # コラボレーション促進アクション
            if len(self.collaboration_patterns) > 5:
                actions.append(
                    {
                        "type": "collaboration_optimization",
                        "target_worker": "queen",
                        "priority": "medium",
                        "details": {
                            "patterns": self.collaboration_patterns[-3:],
                            "suggestions": await self._generate_collaboration_improvements(),
                        },
                    }
                )

            self.logger.info(f"🎯 Decided on {len(actions)} autonomous actions")
            return actions

        except Exception as e:
            self.logger.error(f"❌ Error in action decision: {e}")
            return []

    async def _execute_collaborative_actions(
        self, actions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Worker間協調でアクション実行"""
        results = {
            "successful_actions": 0,
            "failed_actions": 0,
            "collaborations": [],
            "improvements": [],
        }

        for action in actions:
            try:
                result = await self._execute_collaborative_action(action)

                if result.get("success", False):
                    results["successful_actions"] += 1
                    results["improvements"].append(result)
                    self.performance_metrics["tasks_completed"] += 1

                    # 成功パターン記録
                    self.success_patterns.append(
                        {
                            "action": action,
                            "result": result,
                            "timestamp": datetime.now().isoformat(),
                            "cycle": self.cycle_count,
                        }
                    )
                else:
                    results["failed_actions"] += 1

                # コラボレーション記録
                results["collaborations"].append(
                    {
                        "action": action,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            except Exception as e:
                self.logger.error(f"❌ Error executing action {action}: {e}")
                results["failed_actions"] += 1

        # 自動化レベル更新
        total_actions = results["successful_actions"] + results["failed_actions"]
        if total_actions > 0:
            self.performance_metrics["automation_level"] = (
                results["successful_actions"] / total_actions
            )

        self.logger.info(
            f"⚡ Executed {total_actions} collaborative actions: "
            f"{results['successful_actions']} successful, "
            f"{results['failed_actions']} failed"
        )

        return results

    async def _execute_collaborative_action(
        self, action: dict[str, Any]
    ) -> dict[str, Any]:
        """単一協調アクション実行"""
        action_type = action.get("type")
        target_worker = action.get("target_worker", "developer")

        try:
            if action_type == "quality_improvement":
                return await self._collaborate_quality_improvement(
                    action, target_worker
                )
            elif action_type == "collaboration_optimization":
                return await self._collaborate_optimization(action, target_worker)
            else:
                # 専門分野別アクション実行
                return await self._execute_specialized_collaboration(
                    action, target_worker
                )

        except Exception as e:
            return {"success": False, "error": str(e), "action": action}

    async def _collaborate_quality_improvement(
        self, action: dict[str, Any], target_worker: str
    ) -> dict[str, Any]:
        """品質改善協調"""
        try:
            # Developer Workerに品質改善要求
            improvement_request = {
                "action": "quality_improvement",
                "agent_id": self.agent_id,
                "details": action["details"],
                "collaboration_id": f"quality_{self.cycle_count}_{datetime.now().strftime('%H%M%S')}",
            }

            success = self.comb_api.send_message(
                to_worker=target_worker,
                content=improvement_request,
                message_type=MessageType.REQUEST,
                priority=MessagePriority.HIGH,
            )

            if success:
                self.performance_metrics["messages_sent"] += 1
                self.performance_metrics["developer_collaborations"] += 1

                # Work Log記録
                self.comb_api.add_progress(
                    "Quality Improvement Collaboration",
                    f"Requested quality improvement from {target_worker}",
                )

                return {
                    "success": True,
                    "type": "quality_improvement",
                    "target_worker": target_worker,
                    "improvement": "Quality improvement request sent",
                }

            return {
                "success": False,
                "error": "Failed to send quality improvement request",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _collaborate_optimization(
        self, action: dict[str, Any], target_worker: str
    ) -> dict[str, Any]:
        """コラボレーション最適化"""
        try:
            # Queen Workerに最適化提案
            optimization_request = {
                "action": "collaboration_optimization",
                "agent_id": self.agent_id,
                "patterns": action["details"]["patterns"],
                "suggestions": action["details"]["suggestions"],
                "collaboration_id": f"opt_{self.cycle_count}_{datetime.now().strftime('%H%M%S')}",
            }

            success = self.comb_api.send_message(
                to_worker=target_worker,
                content=optimization_request,
                message_type=MessageType.NOTIFICATION,
                priority=MessagePriority.MEDIUM,
            )

            if success:
                self.performance_metrics["messages_sent"] += 1
                self.performance_metrics["queen_collaborations"] += 1

                return {
                    "success": True,
                    "type": "collaboration_optimization",
                    "improvement": "Collaboration optimization suggestions sent",
                }

            return {
                "success": False,
                "error": "Failed to send optimization suggestions",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _learn_from_collaboration(self, results: dict[str, Any]) -> None:
        """協調結果からの学習 (Work Log Manager活用)"""
        try:
            # コラボレーションパターン記録
            for collaboration in results.get("collaborations", []):
                self.collaboration_patterns.append(
                    {
                        "pattern": collaboration,
                        "success": collaboration.get("result", {}).get(
                            "success", False
                        ),
                        "timestamp": datetime.now().isoformat(),
                        "cycle": self.cycle_count,
                    }
                )

            # Work Log Manager記録
            learning_summary = {
                "cycle": self.cycle_count,
                "successful_actions": results["successful_actions"],
                "failed_actions": results["failed_actions"],
                "automation_level": self.performance_metrics["automation_level"],
                "collaboration_count": len(results["collaborations"]),
            }

            # 進捗記録
            self.comb_api.add_progress(
                f"Learning from Cycle #{self.cycle_count}",
                f"Processed {len(results['collaborations'])} collaborations, "
                f"automation level: {self.performance_metrics['automation_level']:.2%}",
            )

            # メトリクス記録
            self.comb_api.add_metrics(learning_summary)

            # 改善提案生成
            if self.cycle_count % 3 == 0:  # 3サイクルごと
                improvements = await self._generate_learning_improvements()
                if improvements:
                    self.improvement_suggestions.extend(improvements)

                    # 技術決定記録
                    self.comb_api.add_technical_decision(
                        "Autonomous Learning Improvements",
                        f"Generated {len(improvements)} improvement suggestions based on collaboration patterns",
                        [],
                    )

            self.performance_metrics["work_log_entries"] += 2
            self.logger.info("🧠 Learning from collaboration completed")

        except Exception as e:
            self.logger.error(f"❌ Error in learning process: {e}")

    async def _prepare_next_cycle(self) -> None:
        """次のサイクル準備"""
        try:
            # パフォーマンス記録
            self.comb_api.add_progress(
                f"Cycle #{self.cycle_count} Completed",
                f"Automation: {self.performance_metrics['automation_level']:.2%}, "
                f"Messages: {self.performance_metrics['messages_sent']}/{self.performance_metrics['messages_received']}, "
                f"Collaborations: Q{self.performance_metrics['queen_collaborations']}/D{self.performance_metrics['developer_collaborations']}",
            )

            # 学習データクリーンアップ
            if len(self.collaboration_patterns) > 20:
                self.collaboration_patterns = self.collaboration_patterns[-15:]

            if len(self.success_patterns) > 15:
                self.success_patterns = self.success_patterns[-10:]

            self.logger.info(f"🔄 Prepared for cycle #{self.cycle_count + 1}")

        except Exception as e:
            self.logger.error(f"❌ Error preparing next cycle: {e}")

    # カスタマイズポイント: 以下のメソッドを継承クラスでオーバーライド

    async def _get_agent_capabilities(self) -> list[str]:
        """エージェント能力取得 (カスタマイズ可能)"""
        return ["autonomous_operation", "comb_api_integration", "worker_collaboration"]

    async def _get_analysis_focus_areas(self) -> list[str]:
        """分析フォーカス領域 (カスタマイズ可能)"""
        return ["quality_metrics", "collaboration_efficiency", "automation_level"]

    async def _get_specialized_actions(
        self, analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """専門分野別アクション (カスタマイズ必須)"""
        return []

    async def _execute_specialized_collaboration(
        self, action: dict[str, Any], target_worker: str
    ) -> dict[str, Any]:
        """専門分野別協調実行 (カスタマイズ必須)"""
        return {"success": False, "error": "Not implemented"}

    async def _generate_collaboration_improvements(self) -> list[dict[str, Any]]:
        """コラボレーション改善提案生成 (カスタマイズ可能)"""
        return []

    async def _generate_learning_improvements(self) -> list[dict[str, Any]]:
        """学習改善提案生成 (カスタマイズ可能)"""
        return []

    async def _generate_fallback_analysis(self) -> dict[str, Any]:
        """フォールバック分析 (カスタマイズ可能)"""
        return {
            "quality_metrics": {"score": 75},
            "improvement_areas": ["general_quality"],
            "status": "fallback_analysis",
        }

    async def _handle_cycle_error(self, error: Exception) -> None:
        """サイクルエラー処理"""
        self.comb_api.add_challenge(
            f"Autonomous cycle error: {str(error)}",
            "Implementing error recovery and fallback mechanisms",
        )

    async def _cleanup_agent(self) -> None:
        """エージェント終了処理"""
        try:
            # 最終学習データ記録
            final_metrics = {
                "total_cycles": self.cycle_count,
                "final_automation_level": self.performance_metrics["automation_level"],
                "total_collaborations": (
                    self.performance_metrics["queen_collaborations"]
                    + self.performance_metrics["developer_collaborations"]
                ),
                "work_log_entries": self.performance_metrics["work_log_entries"],
            }

            self.comb_api.add_metrics(final_metrics)

            # タスク完了
            if self.current_task_id:
                self.comb_api.complete_task(
                    f"Autonomous operation completed after {self.cycle_count} cycles. "
                    f"Final automation level: {self.performance_metrics['automation_level']:.2%}"
                )

            self.logger.info("🧹 Agent cleanup completed")

        except Exception as e:
            self.logger.error(f"❌ Error in cleanup: {e}")

    def get_performance_report(self) -> dict[str, Any]:
        """パフォーマンスレポート取得"""
        return {
            "agent_id": self.agent_id,
            "specialization": self.specialization,
            "cycle_count": self.cycle_count,
            "is_running": self.is_running,
            "performance_metrics": self.performance_metrics.copy(),
            "collaboration_patterns_count": len(self.collaboration_patterns),
            "success_patterns_count": len(self.success_patterns),
            "improvement_suggestions_count": len(self.improvement_suggestions),
            "current_task_id": self.current_task_id,
            "timestamp": datetime.now().isoformat(),
        }


# デモ実行関数


async def demo_comb_autonomous_agent():
    """Comb API自律エージェントのデモ実行"""

    # エージェント作成
    agent = CombAutonomousAgent(
        agent_id="demo_comb_agent",
        specialization="comb_api_demonstration",
        config={
            "cycle_interval": 30,  # 30秒間隔
            "max_cycles": 4,  # 4サイクルで停止
        },
    )

    print("🤖 Starting Comb API Autonomous Agent Demo...")
    print("🏗️ Architecture: Comb API + Queen/Developer Collaboration + Work Log Manager")

    try:
        # 短時間のデモ実行
        demo_task = asyncio.create_task(agent.start_autonomous_cycle())

        # 2分間実行
        await asyncio.sleep(120)
        await agent.stop_autonomous_cycle()

        # 結果レポート
        report = agent.get_performance_report()
        print("\n📊 Performance Report:")
        print(json.dumps(report, indent=2, ensure_ascii=False))

        # Work Log Manager確認
        work_log_summary = agent.comb_api.get_current_task()
        if work_log_summary:
            print("\n📝 Work Log Summary:")
            print(json.dumps(work_log_summary, indent=2, ensure_ascii=False))

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
    asyncio.run(demo_comb_autonomous_agent())
