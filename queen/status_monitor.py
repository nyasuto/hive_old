"""
Status Monitoring System

Issue #4の実装: Nectar進捗監視システム
Worker状態とNectar進捗をリアルタイムで監視し、ボトルネックを検出する
"""

import json
import logging
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from comb.api import CombAPI
from comb.message_router import MessagePriority, MessageType
from queen.task_distributor import Nectar, TaskDistributor


class WorkerState(Enum):
    """Worker状態"""
    IDLE = "idle"
    WORKING = "working"
    OVERLOADED = "overloaded"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass
class WorkerStatus:
    """Worker状態情報"""
    worker_id: str
    state: WorkerState
    current_tasks: list[str]
    last_seen: datetime
    total_tasks_completed: int
    average_completion_time: float
    current_workload: float
    error_count: int
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data['state'] = self.state.value
        data['last_seen'] = self.last_seen.isoformat()
        return data


@dataclass
class BottleneckAlert:
    """ボトルネック警告"""
    alert_id: str
    worker_id: str
    nectar_id: str
    alert_type: str
    severity: str
    message: str
    detected_at: datetime
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data['detected_at'] = self.detected_at.isoformat()
        return data


class StatusMonitor:
    """
    Nectar進捗監視システム

    Worker状態とNectar進捗をリアルタイムで監視し、
    問題を早期発見してQueen Workerに報告する
    """

    def __init__(self, queen_worker_id: str = "queen"):
        self.queen_worker_id = queen_worker_id
        self.comb_api = CombAPI(queen_worker_id)
        self.task_distributor = TaskDistributor(queen_worker_id)
        self.logger = logging.getLogger(__name__)

        # 監視データ保存ディレクトリ
        self.monitor_dir = Path(".hive/monitor")
        self.monitor_dir.mkdir(parents=True, exist_ok=True)

        # 状態管理
        self.worker_states: dict[str, WorkerStatus] = {}
        self.bottleneck_alerts: list[BottleneckAlert] = []
        self.monitoring_enabled = True

        # 設定
        self.config = {
            "worker_timeout": 300,  # 5分間応答なしでタイムアウト
            "overload_threshold": 0.8,  # 80%以上でオーバーロード
            "deadline_warning_hours": 2,  # 期限2時間前で警告
            "max_retry_attempts": 3,  # 最大再試行回数
            "monitoring_interval": 30,  # 監視間隔（秒）
        }

    def start_monitoring(self) -> None:
        """監視開始"""
        self.monitoring_enabled = True
        self.logger.info("Status monitoring started")

        while self.monitoring_enabled:
            try:
                self._monitor_cycle()
                time.sleep(self.config["monitoring_interval"])
            except KeyboardInterrupt:
                self.logger.info("Monitoring interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(5)  # エラー時は少し待機

    def stop_monitoring(self) -> None:
        """監視停止"""
        self.monitoring_enabled = False
        self.logger.info("Status monitoring stopped")

    def _monitor_cycle(self) -> None:
        """1回の監視サイクル"""
        # Worker状態更新
        self._update_worker_states()

        # Nectar進捗チェック
        self._check_nectar_progress()

        # ボトルネック検出
        self._detect_bottlenecks()

        # 期限警告チェック
        self._check_deadline_warnings()

        # 状態保存
        self._save_monitoring_data()

    def _update_worker_states(self) -> None:
        """Worker状態更新"""
        # 既知のWorkerリスト取得
        known_workers = set()
        for nectar in (self.task_distributor.get_active_nectars() +
                      self.task_distributor.get_pending_nectars()):
            known_workers.add(nectar.assigned_to)

        for worker_id in known_workers:
            try:
                # Worker状態取得
                worker_status = self._get_worker_status(worker_id)

                if worker_status:
                    self.worker_states[worker_id] = worker_status
                else:
                    # 応答なしの場合
                    self._handle_worker_timeout(worker_id)

            except Exception as e:
                self.logger.error(f"Failed to update status for {worker_id}: {e}")
                self._handle_worker_error(worker_id, str(e))

    def _get_worker_status(self, worker_id: str) -> WorkerStatus | None:
        """Worker状態取得"""
        try:
            # Comb APIでWorker状態を問い合わせ
            response = self.comb_api.send_message(
                to_worker=worker_id,
                content={"request": "status_check"},
                message_type=MessageType.STATUS_REQUEST,
                priority=MessagePriority.MEDIUM
            )

            if response:
                # 現在のアクティブタスク取得
                active_nectars = self.task_distributor.get_active_nectars(worker_id)
                current_tasks = [n.nectar_id for n in active_nectars]

                # ワークロード計算
                workload = self._calculate_workload(worker_id)

                # 状態判定
                state = self._determine_worker_state(worker_id, workload)

                return WorkerStatus(
                    worker_id=worker_id,
                    state=state,
                    current_tasks=current_tasks,
                    last_seen=datetime.now(),
                    total_tasks_completed=self._get_completed_task_count(worker_id),
                    average_completion_time=self._calculate_average_completion_time(worker_id),
                    current_workload=workload,
                    error_count=self._get_error_count(worker_id)
                )

        except Exception as e:
            self.logger.error(f"Failed to get status for {worker_id}: {e}")
            return None
        return None

    def _check_nectar_progress(self) -> None:
        """Nectar進捗チェック"""
        active_nectars = self.task_distributor.get_active_nectars()

        for nectar in active_nectars:
            try:
                # 長時間実行中のタスクをチェック
                if self._is_nectar_stuck(nectar):
                    self._create_bottleneck_alert(
                        nectar.assigned_to,
                        nectar.nectar_id,
                        "stuck_task",
                        "warning",
                        f"Nectar {nectar.nectar_id} has been active for too long"
                    )

                # 期限超過チェック
                if datetime.now() > nectar.deadline:
                    self._create_bottleneck_alert(
                        nectar.assigned_to,
                        nectar.nectar_id,
                        "deadline_exceeded",
                        "critical",
                        f"Nectar {nectar.nectar_id} has exceeded its deadline"
                    )

            except Exception as e:
                self.logger.error(f"Failed to check progress for {nectar.nectar_id}: {e}")

    def _detect_bottlenecks(self) -> None:
        """ボトルネック検出"""
        for worker_id, status in self.worker_states.items():
            try:
                # オーバーロード検出
                if status.current_workload > self.config["overload_threshold"]:
                    self._create_bottleneck_alert(
                        worker_id,
                        "",
                        "worker_overload",
                        "warning",
                        f"Worker {worker_id} is overloaded ({status.current_workload:.1%})"
                    )

                # エラー頻発検出
                if status.error_count > self.config["max_retry_attempts"]:
                    self._create_bottleneck_alert(
                        worker_id,
                        "",
                        "frequent_errors",
                        "critical",
                        f"Worker {worker_id} has frequent errors ({status.error_count})"
                    )

            except Exception as e:
                self.logger.error(f"Failed to detect bottlenecks for {worker_id}: {e}")

    def _check_deadline_warnings(self) -> None:
        """期限警告チェック"""
        active_nectars = self.task_distributor.get_active_nectars()
        warning_threshold = datetime.now() + timedelta(hours=self.config["deadline_warning_hours"])

        for nectar in active_nectars:
            if nectar.deadline < warning_threshold:
                self._create_bottleneck_alert(
                    nectar.assigned_to,
                    nectar.nectar_id,
                    "deadline_warning",
                    "info",
                    f"Nectar {nectar.nectar_id} deadline approaching in {self.config['deadline_warning_hours']} hours"
                )

    def _create_bottleneck_alert(self, worker_id: str, nectar_id: str, alert_type: str,
                                severity: str, message: str) -> None:
        """ボトルネック警告作成"""
        alert_id = f"alert-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(self.bottleneck_alerts)}"

        alert = BottleneckAlert(
            alert_id=alert_id,
            worker_id=worker_id,
            nectar_id=nectar_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            detected_at=datetime.now()
        )

        self.bottleneck_alerts.append(alert)
        self.logger.warning(f"Bottleneck alert: {message}")

        # 重要度が高い場合は即座に通知
        if severity in ["critical", "warning"]:
            self._send_alert_notification(alert)

    def _send_alert_notification(self, alert: BottleneckAlert) -> None:
        """警告通知送信"""
        try:
            # Queen Workerに通知
            self.comb_api.add_progress(
                f"Bottleneck Alert: {alert.alert_type}",
                alert.message
            )

            # 該当Workerにも通知
            if alert.worker_id:
                self.comb_api.send_message(
                    to_worker=alert.worker_id,
                    content={
                        "alert": alert.to_dict(),
                        "action_required": True
                    },
                    message_type=MessageType.ALERT,
                    priority=MessagePriority.HIGH if alert.severity == "critical" else MessagePriority.MEDIUM
                )

        except Exception as e:
            self.logger.error(f"Failed to send alert notification: {e}")

    def get_monitoring_dashboard(self) -> dict[str, Any]:
        """監視ダッシュボード情報取得"""
        active_nectars = self.task_distributor.get_active_nectars()
        pending_nectars = self.task_distributor.get_pending_nectars()
        completed_nectars = self.task_distributor.get_completed_nectars()

        return {
            "timestamp": datetime.now().isoformat(),
            "overview": {
                "active_nectars": len(active_nectars),
                "pending_nectars": len(pending_nectars),
                "completed_nectars": len(completed_nectars),
                "active_workers": len([w for w in self.worker_states.values() if w.state == WorkerState.WORKING]),
                "total_alerts": len(self.bottleneck_alerts),
                "unresolved_alerts": len([a for a in self.bottleneck_alerts if not a.resolved])
            },
            "worker_states": {wid: status.to_dict() for wid, status in self.worker_states.items()},
            "recent_alerts": [a.to_dict() for a in self.bottleneck_alerts[-10:]],
            "nectar_by_priority": self._get_nectar_priority_breakdown(),
            "completion_statistics": self._get_completion_statistics()
        }

    def resolve_alert(self, alert_id: str) -> bool:
        """警告解決"""
        for alert in self.bottleneck_alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                self.logger.info(f"Alert {alert_id} resolved")
                return True
        return False

    def get_worker_performance_report(self, worker_id: str) -> dict[str, Any]:
        """Worker性能レポート取得"""
        status = self.worker_states.get(worker_id)
        if not status:
            return {"error": f"Worker {worker_id} not found"}

        completed_nectars = self.task_distributor.get_completed_nectars(worker_id)

        return {
            "worker_id": worker_id,
            "current_status": status.to_dict(),
            "performance_metrics": {
                "total_completed": len(completed_nectars),
                "average_completion_time": status.average_completion_time,
                "success_rate": self._calculate_success_rate(worker_id),
                "workload_history": self._get_workload_history(worker_id)
            },
            "recent_tasks": [n.to_dict() for n in completed_nectars[-5:]],
            "alerts": [a.to_dict() for a in self.bottleneck_alerts if a.worker_id == worker_id][-5:]
        }

    def _calculate_workload(self, worker_id: str) -> float:
        """ワークロード計算"""
        active_nectars = self.task_distributor.get_active_nectars(worker_id)
        if not active_nectars:
            return 0.0

        total_estimated_time = sum(n.estimated_time for n in active_nectars)
        # 最大8時間を100%として計算
        max_capacity = 8.0
        return min(total_estimated_time / max_capacity, 1.0)

    def _determine_worker_state(self, worker_id: str, workload: float) -> WorkerState:
        """Worker状態判定"""
        if workload == 0:
            return WorkerState.IDLE
        elif workload > self.config["overload_threshold"]:
            return WorkerState.OVERLOADED
        else:
            return WorkerState.WORKING

    def _is_nectar_stuck(self, nectar: Nectar) -> bool:
        """Nectarが停滞しているかチェック"""
        # 推定時間の2倍以上経過している場合は停滞と判定
        time_elapsed = (datetime.now() - nectar.created_at).total_seconds() / 3600
        return time_elapsed > nectar.estimated_time * 2

    def _handle_worker_timeout(self, worker_id: str) -> None:
        """Workerタイムアウト処理"""
        if worker_id in self.worker_states:
            self.worker_states[worker_id].state = WorkerState.UNAVAILABLE

        self._create_bottleneck_alert(
            worker_id,
            "",
            "worker_timeout",
            "critical",
            f"Worker {worker_id} is not responding"
        )

    def _handle_worker_error(self, worker_id: str, error_message: str) -> None:
        """Workerエラー処理"""
        if worker_id in self.worker_states:
            self.worker_states[worker_id].state = WorkerState.ERROR
            self.worker_states[worker_id].error_count += 1
            self.worker_states[worker_id].last_error = error_message

    def _get_completed_task_count(self, worker_id: str) -> int:
        """完了タスク数取得"""
        return len(self.task_distributor.get_completed_nectars(worker_id))

    def _calculate_average_completion_time(self, worker_id: str) -> float:
        """平均完了時間計算"""
        completed_nectars = self.task_distributor.get_completed_nectars(worker_id)
        if not completed_nectars:
            return 0.0

        total_time = sum(n.estimated_time for n in completed_nectars)
        return total_time / len(completed_nectars)

    def _get_error_count(self, worker_id: str) -> int:
        """エラー数取得"""
        return len([a for a in self.bottleneck_alerts
                   if a.worker_id == worker_id and a.alert_type in ["worker_error", "frequent_errors"]])

    def _get_nectar_priority_breakdown(self) -> dict[str, int]:
        """優先度別Nectar内訳"""
        all_nectars = (self.task_distributor.get_active_nectars() +
                      self.task_distributor.get_pending_nectars())

        breakdown: dict[str, int] = defaultdict(int)
        for nectar in all_nectars:
            breakdown[nectar.priority.value] += 1

        return dict(breakdown)

    def _get_completion_statistics(self) -> dict[str, Any]:
        """完了統計情報"""
        completed_nectars = self.task_distributor.get_completed_nectars()

        if not completed_nectars:
            return {"total_completed": 0}

        total_time = sum(n.estimated_time for n in completed_nectars)
        average_time = total_time / len(completed_nectars)

        return {
            "total_completed": len(completed_nectars),
            "average_completion_time": average_time,
            "completion_rate_today": self._calculate_today_completion_rate(),
            "most_productive_worker": self._find_most_productive_worker()
        }

    def _calculate_success_rate(self, worker_id: str) -> float:
        """成功率計算"""
        completed = len(self.task_distributor.get_completed_nectars(worker_id))
        failed = len(list(self.task_distributor._load_nectars_from_dir(
            self.task_distributor.failed_dir, worker_id)))

        total = completed + failed
        return completed / total if total > 0 else 0.0

    def _get_workload_history(self, worker_id: str) -> list[dict[str, Any]]:
        """ワークロード履歴取得"""
        # 簡易実装: 現在の値のみ
        return [{"timestamp": datetime.now().isoformat(),
                "workload": self._calculate_workload(worker_id)}]

    def _calculate_today_completion_rate(self) -> float:
        """今日の完了率計算"""
        today = datetime.now().date()
        completed_today = [n for n in self.task_distributor.get_completed_nectars()
                          if n.created_at.date() == today]

        total_today = len(completed_today) + len(self.task_distributor.get_active_nectars())
        return len(completed_today) / total_today if total_today > 0 else 0.0

    def _find_most_productive_worker(self) -> str:
        """最も生産性の高いWorker取得"""
        worker_productivity = {}

        for worker_id in self.worker_states:
            completed = len(self.task_distributor.get_completed_nectars(worker_id))
            worker_productivity[worker_id] = completed

        if worker_productivity:
            return max(worker_productivity, key=lambda k: worker_productivity[k])
        return ""

    def _save_monitoring_data(self) -> None:
        """監視データ保存"""
        try:
            # 現在の状態を保存
            monitoring_data = {
                "timestamp": datetime.now().isoformat(),
                "worker_states": {wid: status.to_dict() for wid, status in self.worker_states.items()},
                "alerts": [alert.to_dict() for alert in self.bottleneck_alerts[-100:]]  # 最新100件
            }

            # ファイルに保存
            data_file = self.monitor_dir / f"monitoring-{datetime.now().strftime('%Y%m%d')}.json"
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(monitoring_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save monitoring data: {e}")
