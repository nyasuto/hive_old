"""
Queen Coordinator System

Issue #4の実装: Queen Worker全体調整システム
全体の進捗管理、Worker負荷分散、緊急時対応を統合的に管理
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from comb.api import CombAPI
from comb.message_router import MessagePriority, MessageType
from queen.status_monitor import StatusMonitor
from queen.task_distributor import Nectar, Priority, TaskDistributor, TaskStatus


class CoordinationMode(Enum):
    """調整モード"""

    NORMAL = "normal"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"
    OPTIMIZING = "optimizing"


class LoadBalancingStrategy(Enum):
    """負荷分散戦略"""

    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    PRIORITY_BASED = "priority_based"
    SKILL_BASED = "skill_based"


@dataclass
class CoordinationReport:
    """調整レポート"""

    timestamp: datetime
    mode: CoordinationMode
    total_nectars: int
    active_workers: int
    completion_rate: float
    bottlenecks: list[str]
    recommendations: list[str]
    next_actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["mode"] = self.mode.value
        return data


class QueenCoordinator:
    """
    Queen Worker全体調整システム

    TaskDistributorとStatusMonitorを統合し、
    Hive全体の効率的な運用を実現する
    """

    def __init__(self, queen_worker_id: str = "queen"):
        self.queen_worker_id = queen_worker_id
        self.comb_api = CombAPI(queen_worker_id)
        self.task_distributor = TaskDistributor(queen_worker_id)
        self.status_monitor = StatusMonitor(queen_worker_id)
        self.logger = logging.getLogger(__name__)

        # 調整データ保存ディレクトリ
        self.coordination_dir = Path(".hive/coordination")
        self.coordination_dir.mkdir(parents=True, exist_ok=True)

        # 現在の調整状態
        self.current_mode = CoordinationMode.NORMAL
        self.load_balancing_strategy = LoadBalancingStrategy.LEAST_LOADED
        self.coordination_active = False

        # 設定
        self.config = {
            "coordination_interval": 60,  # 調整間隔（秒）
            "load_balance_threshold": 0.7,  # 負荷分散閾値
            "emergency_threshold": 0.9,  # 緊急事態閾値
            "auto_redistribute": True,  # 自動再配布
            "max_worker_tasks": 5,  # Worker最大タスク数
            "priority_boost_hours": 2,  # 優先度上昇時間
            "completion_target": 0.8,  # 完了率目標
        }

        # 既知のWorkerリスト
        self.known_workers: set[str] = set()
        self.worker_capabilities: dict[str, list[str]] = {}

        # 統計情報
        self.coordination_stats = {
            "total_coordinations": 0,
            "emergency_interventions": 0,
            "load_balancing_operations": 0,
            "redistributions": 0,
            "bottlenecks_resolved": 0,
        }

    def start_coordination(self) -> None:
        """調整開始"""
        self.coordination_active = True
        self.logger.info("Queen coordination started")

        # 非同期調整ループ
        asyncio.create_task(self._coordination_loop())

    def stop_coordination(self) -> None:
        """調整停止"""
        self.coordination_active = False
        self.logger.info("Queen coordination stopped")

    async def _coordination_loop(self) -> None:
        """調整ループ"""
        while self.coordination_active:
            try:
                await self._coordination_cycle()
                await asyncio.sleep(self.config["coordination_interval"])
            except Exception as e:
                self.logger.error(f"Coordination error: {e}")
                await asyncio.sleep(5)

    async def _coordination_cycle(self) -> None:
        """1回の調整サイクル"""
        self.coordination_stats["total_coordinations"] += 1

        # 現在状況の評価
        situation = await self._assess_situation()

        # 調整モードの決定
        new_mode = self._determine_coordination_mode(situation)
        if new_mode != self.current_mode:
            self.logger.info(
                f"Coordination mode changed: {self.current_mode.value} → {new_mode.value}"
            )
            self.current_mode = new_mode

        # モード別の調整実行
        if self.current_mode == CoordinationMode.EMERGENCY:
            await self._handle_emergency_mode(situation)
        elif self.current_mode == CoordinationMode.OPTIMIZING:
            await self._handle_optimizing_mode(situation)
        else:
            await self._handle_normal_mode(situation)

        # 調整レポート生成
        report = self._generate_coordination_report(situation)
        await self._save_coordination_report(report)

        # 次のアクションのスケジューリング
        await self._schedule_next_actions(report)

    async def _assess_situation(self) -> dict[str, Any]:
        """現在状況の評価"""
        # 基本統計
        active_nectars = self.task_distributor.get_active_nectars()
        pending_nectars = self.task_distributor.get_pending_nectars()
        completed_nectars = self.task_distributor.get_completed_nectars()

        # Worker状態取得
        self._update_known_workers()
        worker_workloads = {}
        for worker_id in self.known_workers:
            workload = self.task_distributor.get_worker_workload(worker_id)
            worker_workloads[worker_id] = workload

        # 監視ダッシュボード
        dashboard = self.status_monitor.get_monitoring_dashboard()

        return {
            "timestamp": datetime.now(),
            "active_nectars": active_nectars,
            "pending_nectars": pending_nectars,
            "completed_nectars": completed_nectars,
            "worker_workloads": worker_workloads,
            "monitoring_dashboard": dashboard,
            "total_active_tasks": len(active_nectars),
            "total_pending_tasks": len(pending_nectars),
            "completion_rate": self._calculate_completion_rate(),
            "average_workload": self._calculate_average_workload(worker_workloads),
            "bottlenecks": self._identify_bottlenecks(dashboard),
            "urgent_tasks": self._identify_urgent_tasks(
                active_nectars + pending_nectars
            ),
        }

    def _determine_coordination_mode(
        self, situation: dict[str, Any]
    ) -> CoordinationMode:
        """調整モードの決定"""
        avg_workload = situation["average_workload"]
        bottlenecks = situation["bottlenecks"]
        completion_rate = situation["completion_rate"]

        # 緊急事態の判定
        if (
            avg_workload > self.config["emergency_threshold"]
            or len(bottlenecks) > 3
            or completion_rate < 0.5
        ):
            return CoordinationMode.EMERGENCY

        # 最適化モードの判定
        if avg_workload > self.config["load_balance_threshold"] or len(bottlenecks) > 0:
            return CoordinationMode.OPTIMIZING

        return CoordinationMode.NORMAL

    async def _handle_emergency_mode(self, situation: dict[str, Any]) -> None:
        """緊急事態モード処理"""
        self.logger.warning("Emergency mode activated")
        self.coordination_stats["emergency_interventions"] += 1

        # 緊急時の対応
        await self._emergency_load_redistribution(situation)
        await self._escalate_urgent_tasks(situation["urgent_tasks"])
        await self._notify_emergency_status()

    async def _handle_optimizing_mode(self, situation: dict[str, Any]) -> None:
        """最適化モード処理"""
        self.logger.info("Optimizing mode activated")

        # 負荷分散の実行
        await self._perform_load_balancing(situation)

        # ボトルネックの解決
        await self._resolve_bottlenecks(situation["bottlenecks"])

        # 優先度の調整
        # Task priority adjustment is handled in escalate_urgent_tasks
        pass

    async def _handle_normal_mode(self, situation: dict[str, Any]) -> None:
        """通常モード処理"""
        # 日常的な最適化
        await self._routine_optimization(situation)

        # 予防的な対応
        await self._preventive_measures(situation)

    async def _emergency_load_redistribution(self, situation: dict[str, Any]) -> None:
        """緊急時負荷再配布"""
        worker_workloads = situation["worker_workloads"]

        # 最も負荷の高いWorkerを特定
        overloaded_workers = [
            worker_id
            for worker_id, workload in worker_workloads.items()
            if workload["total_estimated_time"] > 8  # 8時間以上
        ]

        # 負荷の少ないWorkerを特定
        underloaded_workers = [
            worker_id
            for worker_id, workload in worker_workloads.items()
            if workload["total_estimated_time"] < 4  # 4時間未満
        ]

        # 緊急再配布
        for overloaded_worker in overloaded_workers:
            active_nectars = self.task_distributor.get_active_nectars(overloaded_worker)

            # 優先度の低いタスクを他のWorkerに移動
            for nectar in active_nectars:
                if (
                    nectar.priority in [Priority.LOW, Priority.MEDIUM]
                    and underloaded_workers
                ):
                    target_worker = underloaded_workers[0]

                    # ステータスをPENDINGに戻して再配布
                    self.task_distributor.update_nectar_status(
                        nectar.nectar_id, TaskStatus.PENDING
                    )
                    nectar.assigned_to = target_worker

                    if self.task_distributor.distribute_nectar(nectar):
                        self.logger.info(
                            f"Emergency redistribution: {nectar.nectar_id} -> {target_worker}"
                        )
                        self.coordination_stats["redistributions"] += 1
                        break

    async def _perform_load_balancing(self, situation: dict[str, Any]) -> None:
        """負荷分散実行"""
        self.coordination_stats["load_balancing_operations"] += 1

        pending_nectars = situation["pending_nectars"]
        worker_workloads = situation["worker_workloads"]

        # 負荷分散戦略に基づいてタスクを配布
        for nectar in pending_nectars:
            target_worker = self._select_target_worker(nectar, worker_workloads)

            if target_worker and target_worker != nectar.assigned_to:
                nectar.assigned_to = target_worker

                if self.task_distributor.distribute_nectar(nectar):
                    self.logger.info(
                        f"Load balancing: {nectar.nectar_id} -> {target_worker}"
                    )

    async def _resolve_bottlenecks(self, bottlenecks: list[str]) -> None:
        """ボトルネック解決"""
        for bottleneck in bottlenecks:
            # ボトルネックの種類に応じた解決策
            if "overload" in bottleneck:
                await self._resolve_overload_bottleneck(bottleneck)
            elif "deadline" in bottleneck:
                await self._resolve_deadline_bottleneck(bottleneck)
            elif "stuck" in bottleneck:
                await self._resolve_stuck_task_bottleneck(bottleneck)

            self.coordination_stats["bottlenecks_resolved"] += 1

    async def _escalate_urgent_tasks(self, urgent_tasks: list[Nectar]) -> None:
        """緊急タスクのエスカレーション"""
        for nectar in urgent_tasks:
            # 優先度をCRITICALに上げる
            if nectar.priority != Priority.CRITICAL:
                nectar.priority = Priority.CRITICAL
                self.task_distributor.update_nectar_status(
                    nectar.nectar_id, nectar.status
                )

                # 担当Workerに緊急通知
                await self._send_urgent_notification(nectar)

    async def _send_urgent_notification(self, nectar: Nectar) -> None:
        """緊急通知送信"""
        self.comb_api.send_message(
            to_worker=nectar.assigned_to,
            content={
                "nectar_id": nectar.nectar_id,
                "urgent": True,
                "message": f"Task {nectar.nectar_id} has been escalated to CRITICAL priority",
                "deadline": nectar.deadline.isoformat(),
            },
            message_type=MessageType.URGENT_NOTIFICATION,
            priority=MessagePriority.HIGH,
        )

    def _select_target_worker(
        self, nectar: Nectar, worker_workloads: dict[str, dict]
    ) -> str | None:
        """最適なWorkerを選択"""
        if self.load_balancing_strategy == LoadBalancingStrategy.LEAST_LOADED:
            return self._select_least_loaded_worker(worker_workloads)
        elif self.load_balancing_strategy == LoadBalancingStrategy.SKILL_BASED:
            return self._select_skill_based_worker(nectar, worker_workloads)
        else:
            return self._select_round_robin_worker(worker_workloads)

    def _select_least_loaded_worker(
        self, worker_workloads: dict[str, dict]
    ) -> str | None:
        """最も負荷の少ないWorkerを選択"""
        if not worker_workloads:
            return None

        min_workload = float("inf")
        selected_worker = None

        for worker_id, workload in worker_workloads.items():
            if workload["total_estimated_time"] < min_workload:
                min_workload = workload["total_estimated_time"]
                selected_worker = worker_id

        return selected_worker

    def _select_skill_based_worker(
        self, nectar: Nectar, worker_workloads: dict[str, dict]
    ) -> str | None:
        """スキルベースWorker選択"""
        # 簡易実装: タグベースでの選択
        suitable_workers = []

        for worker_id in worker_workloads:
            worker_skills = self.worker_capabilities.get(worker_id, [])

            # タスクのタグとWorkerのスキルをマッチング
            if nectar.tags and any(tag in worker_skills for tag in nectar.tags):
                suitable_workers.append(worker_id)

        if suitable_workers:
            return self._select_least_loaded_worker(
                {wid: worker_workloads[wid] for wid in suitable_workers}
            )

        return self._select_least_loaded_worker(worker_workloads)

    def _select_round_robin_worker(
        self, worker_workloads: dict[str, dict]
    ) -> str | None:
        """ラウンドロビン選択"""
        workers = list(worker_workloads.keys())
        if not workers:
            return None

        # 簡易実装: 最初のWorkerを選択
        return workers[0]

    def _update_known_workers(self) -> None:
        """既知のWorkerリストの更新"""
        all_nectars = (
            self.task_distributor.get_active_nectars()
            + self.task_distributor.get_pending_nectars()
            + self.task_distributor.get_completed_nectars()
        )

        for nectar in all_nectars:
            self.known_workers.add(nectar.assigned_to)

    def _calculate_completion_rate(self) -> float:
        """完了率計算"""
        completed = len(self.task_distributor.get_completed_nectars())
        total = (
            len(self.task_distributor.get_active_nectars())
            + len(self.task_distributor.get_pending_nectars())
            + completed
        )

        return completed / total if total > 0 else 0.0

    def _calculate_average_workload(self, worker_workloads: dict[str, dict]) -> float:
        """平均ワークロード計算"""
        if not worker_workloads:
            return 0.0

        total_workload = sum(
            w["total_estimated_time"] for w in worker_workloads.values()
        )
        return float(total_workload / len(worker_workloads))

    def _identify_bottlenecks(self, dashboard: dict[str, Any]) -> list[str]:
        """ボトルネック特定"""
        bottlenecks = []

        for alert in dashboard.get("recent_alerts", []):
            if not alert.get("resolved", False):
                bottlenecks.append(alert["alert_type"])

        return bottlenecks

    def _identify_urgent_tasks(self, nectars: list[Nectar]) -> list[Nectar]:
        """緊急タスク特定"""
        urgent_threshold = datetime.now() + timedelta(hours=2)

        return [
            nectar
            for nectar in nectars
            if nectar.deadline < urgent_threshold
            and nectar.status != TaskStatus.COMPLETED
        ]

    def _generate_coordination_report(
        self, situation: dict[str, Any]
    ) -> CoordinationReport:
        """調整レポート生成"""
        total_nectars = (
            len(situation["active_nectars"])
            + len(situation["pending_nectars"])
            + len(situation["completed_nectars"])
        )

        active_workers = len(
            [
                w
                for w in situation["worker_workloads"]
                if situation["worker_workloads"][w]["active_tasks"] > 0
            ]
        )

        recommendations = self._generate_recommendations(situation)
        next_actions = self._generate_next_actions(situation)

        return CoordinationReport(
            timestamp=situation["timestamp"],
            mode=self.current_mode,
            total_nectars=total_nectars,
            active_workers=active_workers,
            completion_rate=situation["completion_rate"],
            bottlenecks=situation["bottlenecks"],
            recommendations=recommendations,
            next_actions=next_actions,
        )

    def _generate_recommendations(self, situation: dict[str, Any]) -> list[str]:
        """推奨事項生成"""
        recommendations = []

        if situation["average_workload"] > 6:
            recommendations.append("Consider adding more workers to reduce workload")

        if situation["completion_rate"] < 0.7:
            recommendations.append("Review task complexity and estimation accuracy")

        if len(situation["bottlenecks"]) > 2:
            recommendations.append("Implement proactive bottleneck prevention measures")

        return recommendations

    def _generate_next_actions(self, situation: dict[str, Any]) -> list[str]:
        """次のアクション生成"""
        actions = []

        if situation["urgent_tasks"]:
            actions.append(f"Address {len(situation['urgent_tasks'])} urgent tasks")

        if situation["average_workload"] > self.config["load_balance_threshold"]:
            actions.append("Execute load balancing operation")

        if len(situation["bottlenecks"]) > 0:
            actions.append("Resolve identified bottlenecks")

        return actions

    async def _save_coordination_report(self, report: CoordinationReport) -> None:
        """調整レポート保存"""
        try:
            report_file = (
                self.coordination_dir
                / f"coordination-{report.timestamp.strftime('%Y%m%d-%H%M%S')}.json"
            )

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save coordination report: {e}")

    async def _schedule_next_actions(self, report: CoordinationReport) -> None:
        """次のアクションスケジューリング"""
        for action in report.next_actions:
            self.logger.info(f"Scheduled action: {action}")
            # 実際のスケジューリング実装は省略

    async def _routine_optimization(self, situation: dict[str, Any]) -> None:
        """日常的な最適化"""
        # 予防的な負荷分散
        if situation["average_workload"] > 0.6:
            await self._perform_load_balancing(situation)

    async def _preventive_measures(self, situation: dict[str, Any]) -> None:
        """予防的措置"""
        # 期限が近いタスクの優先度上昇
        for nectar in situation["urgent_tasks"]:
            if nectar.priority == Priority.LOW:
                nectar.priority = Priority.MEDIUM
                self.task_distributor.update_nectar_status(
                    nectar.nectar_id, nectar.status
                )

    async def _resolve_overload_bottleneck(self, bottleneck: str) -> None:
        """過負荷ボトルネック解決"""
        # 実装省略: 負荷再配布
        pass

    async def _resolve_deadline_bottleneck(self, bottleneck: str) -> None:
        """期限ボトルネック解決"""
        # 実装省略: 期限延長or優先度調整
        pass

    async def _resolve_stuck_task_bottleneck(self, bottleneck: str) -> None:
        """停滞タスクボトルネック解決"""
        # 実装省略: タスクの再配布or分割
        pass

    async def _notify_emergency_status(self) -> None:
        """緊急状態通知"""
        self.comb_api.add_progress(
            "Emergency Mode Activated",
            "Queen coordinator has activated emergency mode due to system overload",
        )

    def get_coordination_summary(self) -> dict[str, Any]:
        """調整サマリー取得"""
        return {
            "current_mode": self.current_mode.value,
            "coordination_active": self.coordination_active,
            "load_balancing_strategy": self.load_balancing_strategy.value,
            "known_workers": list(self.known_workers),
            "statistics": self.coordination_stats,
            "config": self.config,
        }

    def update_load_balancing_strategy(self, strategy: LoadBalancingStrategy) -> None:
        """負荷分散戦略更新"""
        self.load_balancing_strategy = strategy
        self.logger.info(f"Load balancing strategy updated to: {strategy.value}")

    def update_worker_capabilities(
        self, worker_id: str, capabilities: list[str]
    ) -> None:
        """Workerスキル更新"""
        self.worker_capabilities[worker_id] = capabilities
        self.logger.info(f"Updated capabilities for {worker_id}: {capabilities}")

    def force_emergency_mode(self) -> None:
        """緊急モード強制起動"""
        self.current_mode = CoordinationMode.EMERGENCY
        self.logger.warning("Emergency mode forced by operator")

    def reset_to_normal_mode(self) -> None:
        """通常モードリセット"""
        self.current_mode = CoordinationMode.NORMAL
        self.logger.info("Mode reset to normal by operator")
