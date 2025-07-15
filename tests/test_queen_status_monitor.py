"""
Queen Status Monitor テスト

StatusMonitorクラスの包括的なテストカバレージ
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from queen.status_monitor import (
    BottleneckAlert,
    StatusMonitor,
    WorkerState,
    WorkerStatus,
)
from queen.task_distributor import Nectar, Priority, TaskStatus


class TestWorkerStatus:
    """WorkerStatus データクラステスト"""

    def test_worker_status_creation(self) -> None:
        """WorkerStatus作成テスト"""
        timestamp = datetime.now()
        status = WorkerStatus(
            worker_id="worker1",
            state=WorkerState.WORKING,
            current_tasks=["task1", "task2"],
            last_seen=timestamp,
            total_tasks_completed=5,
            average_completion_time=2.5,
            current_workload=0.6,
            error_count=1,
            last_error="Connection timeout",
        )

        assert status.worker_id == "worker1"
        assert status.state == WorkerState.WORKING
        assert status.current_tasks == ["task1", "task2"]
        assert status.last_seen == timestamp
        assert status.total_tasks_completed == 5
        assert status.average_completion_time == 2.5
        assert status.current_workload == 0.6
        assert status.error_count == 1
        assert status.last_error == "Connection timeout"

    def test_worker_status_to_dict(self) -> None:
        """WorkerStatus辞書変換テスト"""
        timestamp = datetime.now()
        status = WorkerStatus(
            worker_id="worker1",
            state=WorkerState.IDLE,
            current_tasks=[],
            last_seen=timestamp,
            total_tasks_completed=10,
            average_completion_time=3.0,
            current_workload=0.0,
            error_count=0,
        )

        status_dict = status.to_dict()

        assert status_dict["worker_id"] == "worker1"
        assert status_dict["state"] == "idle"
        assert status_dict["current_tasks"] == []
        assert status_dict["last_seen"] == timestamp.isoformat()
        assert status_dict["total_tasks_completed"] == 10


class TestBottleneckAlert:
    """BottleneckAlert データクラステスト"""

    def test_bottleneck_alert_creation(self) -> None:
        """BottleneckAlert作成テスト"""
        timestamp = datetime.now()
        alert = BottleneckAlert(
            alert_id="alert-001",
            worker_id="worker1",
            nectar_id="nectar-123",
            alert_type="overload",
            severity="warning",
            message="Worker is overloaded",
            detected_at=timestamp,
            resolved=False,
        )

        assert alert.alert_id == "alert-001"
        assert alert.worker_id == "worker1"
        assert alert.nectar_id == "nectar-123"
        assert alert.alert_type == "overload"
        assert alert.severity == "warning"
        assert alert.message == "Worker is overloaded"
        assert alert.detected_at == timestamp
        assert alert.resolved is False

    def test_bottleneck_alert_to_dict(self) -> None:
        """BottleneckAlert辞書変換テスト"""
        timestamp = datetime.now()
        alert = BottleneckAlert(
            alert_id="alert-002",
            worker_id="worker2",
            nectar_id="nectar-456",
            alert_type="deadline_warning",
            severity="info",
            message="Deadline approaching",
            detected_at=timestamp,
            resolved=True,
        )

        alert_dict = alert.to_dict()

        assert alert_dict["alert_id"] == "alert-002"
        assert alert_dict["worker_id"] == "worker2"
        assert alert_dict["alert_type"] == "deadline_warning"
        assert alert_dict["severity"] == "info"
        assert alert_dict["detected_at"] == timestamp.isoformat()
        assert alert_dict["resolved"] is True


class TestStatusMonitor:
    """StatusMonitor クラステスト"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.test_dir = Path(tempfile.mkdtemp())

        # Monitor directory setup
        self.monitor_dir = self.test_dir / ".hive" / "monitor"
        self.monitor_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_status_monitor_initialization(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """ステータスモニター初期化テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor("test_queen")

            assert monitor.queen_worker_id == "test_queen"
            assert monitor.monitoring_enabled is True
            assert len(monitor.worker_states) == 0
            assert len(monitor.bottleneck_alerts) == 0

            mock_comb_api.assert_called_once_with("test_queen")
            mock_task_distributor.assert_called_once_with("test_queen")

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_stop_monitoring(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """監視停止テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()
            monitor.monitoring_enabled = True

            monitor.stop_monitoring()

            assert monitor.monitoring_enabled is False

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_calculate_workload(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """ワークロード計算テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # テスト用Nectar作成
            nectars = [
                Nectar(
                    nectar_id="nectar1",
                    title="Task 1",
                    description="Task 1",
                    assigned_to="worker1",
                    created_by="test_creator",
                    priority=Priority.MEDIUM,
                    status=TaskStatus.ACTIVE,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=2,
                    created_at=datetime.now(),
                    deadline=datetime.now() + timedelta(days=1),
                ),
                Nectar(
                    nectar_id="nectar2",
                    title="Task 2",
                    description="Task 2",
                    assigned_to="worker1",
                    created_by="test_creator",
                    priority=Priority.HIGH,
                    status=TaskStatus.ACTIVE,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=4,
                    created_at=datetime.now(),
                    deadline=datetime.now() + timedelta(days=1),
                ),
            ]

            monitor.task_distributor.get_active_nectars = MagicMock(  # type: ignore
                return_value=nectars
            )

            workload = monitor._calculate_workload("worker1")

            # (2.0 + 4.0) / 8.0 = 0.75
            assert workload == 0.75

            # タスクなしの場合
            monitor.task_distributor.get_active_nectars = MagicMock(return_value=[])  # type: ignore
            workload = monitor._calculate_workload("worker1")
            assert workload == 0.0

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_determine_worker_state(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """Worker状態判定テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # IDLE状態
            state = monitor._determine_worker_state("worker1", 0.0)
            assert state == WorkerState.IDLE

            # WORKING状態
            state = monitor._determine_worker_state("worker1", 0.5)
            assert state == WorkerState.WORKING

            # OVERLOADED状態
            state = monitor._determine_worker_state("worker1", 0.9)
            assert state == WorkerState.OVERLOADED

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_is_nectar_stuck(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """Nectar停滞判定テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # 停滞していないNectar（推定時間内）
            nectar_normal = Nectar(
                nectar_id="normal",
                title="Normal Task",
                description="Normal task",
                assigned_to="worker1",
                created_by="test_creator",
                priority=Priority.MEDIUM,
                status=TaskStatus.ACTIVE,
                dependencies=[],
                expected_honey=[],
                estimated_time=2,
                created_at=datetime.now() - timedelta(hours=1),  # 1時間前に作成
                deadline=datetime.now() + timedelta(days=1),
            )

            assert not monitor._is_nectar_stuck(nectar_normal)

            # 停滞しているNectar（推定時間の2倍以上経過）
            nectar_stuck = Nectar(
                nectar_id="stuck",
                title="Stuck Task",
                description="Stuck task",
                assigned_to="worker1",
                created_by="test_creator",
                priority=Priority.MEDIUM,
                status=TaskStatus.ACTIVE,
                dependencies=[],
                expected_honey=[],
                estimated_time=2,
                created_at=datetime.now() - timedelta(hours=5),  # 5時間前に作成
                deadline=datetime.now() + timedelta(days=1),
            )

            assert monitor._is_nectar_stuck(nectar_stuck)

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_create_bottleneck_alert(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """ボトルネック警告作成テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            monitor._create_bottleneck_alert(
                "worker1",
                "nectar1",
                "overload",
                "warning",
                "Worker is overloaded",
            )

            assert len(monitor.bottleneck_alerts) == 1
            alert = monitor.bottleneck_alerts[0]

            assert alert.worker_id == "worker1"
            assert alert.nectar_id == "nectar1"
            assert alert.alert_type == "overload"
            assert alert.severity == "warning"
            assert alert.message == "Worker is overloaded"
            assert not alert.resolved

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_resolve_alert(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """警告解決テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # 警告作成
            monitor._create_bottleneck_alert(
                "worker1", "nectar1", "overload", "warning", "Test alert"
            )
            alert_id = monitor.bottleneck_alerts[0].alert_id

            # 警告解決
            result = monitor.resolve_alert(alert_id)
            assert result is True
            assert monitor.bottleneck_alerts[0].resolved is True

            # 存在しない警告ID
            result = monitor.resolve_alert("nonexistent")
            assert result is False

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_handle_worker_timeout(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """Workerタイムアウト処理テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # Worker状態を事前に設定
            monitor.worker_states["worker1"] = WorkerStatus(
                worker_id="worker1",
                state=WorkerState.WORKING,
                current_tasks=["task1"],
                last_seen=datetime.now(),
                total_tasks_completed=5,
                average_completion_time=2.0,
                current_workload=0.5,
                error_count=0,
            )

            monitor._handle_worker_timeout("worker1")

            # 状態がUNAVAILABLEに変更されていることを確認
            assert monitor.worker_states["worker1"].state == WorkerState.UNAVAILABLE

            # タイムアウト警告が作成されていることを確認
            timeout_alerts = [
                a for a in monitor.bottleneck_alerts if a.alert_type == "worker_timeout"
            ]
            assert len(timeout_alerts) == 1
            assert timeout_alerts[0].worker_id == "worker1"
            assert timeout_alerts[0].severity == "critical"

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_handle_worker_error(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """Workerエラー処理テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # Worker状態を事前に設定
            monitor.worker_states["worker1"] = WorkerStatus(
                worker_id="worker1",
                state=WorkerState.WORKING,
                current_tasks=["task1"],
                last_seen=datetime.now(),
                total_tasks_completed=5,
                average_completion_time=2.0,
                current_workload=0.5,
                error_count=0,
            )

            error_message = "Connection failed"
            monitor._handle_worker_error("worker1", error_message)

            # 状態がERRORに変更されていることを確認
            worker_status = monitor.worker_states["worker1"]
            assert worker_status.state == WorkerState.ERROR
            assert worker_status.error_count == 1
            assert worker_status.last_error == error_message

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_get_completed_task_count(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """完了タスク数取得テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # 完了タスクを設定
            completed_nectars = [
                Nectar(
                    nectar_id=f"completed{i}",
                    title=f"Completed Task {i}",
                    description=f"Completed task {i}",
                    assigned_to="worker1",
                    created_by="test_creator",
                    priority=Priority.MEDIUM,
                    status=TaskStatus.COMPLETED,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=1,
                    created_at=datetime.now(),
                    deadline=datetime.now(),
                )
                for i in range(3)
            ]

            monitor.task_distributor.get_completed_nectars = MagicMock(  # type: ignore
                return_value=completed_nectars
            )

            count = monitor._get_completed_task_count("worker1")
            assert count == 3

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_calculate_average_completion_time(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """平均完了時間計算テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # 完了タスクを設定
            completed_nectars = [
                Nectar(
                    nectar_id="completed1",
                    title="Task 1",
                    description="Task 1",
                    assigned_to="worker1",
                    created_by="test_creator",
                    priority=Priority.MEDIUM,
                    status=TaskStatus.COMPLETED,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=2,
                    created_at=datetime.now(),
                    deadline=datetime.now(),
                ),
                Nectar(
                    nectar_id="completed2",
                    title="Task 2",
                    description="Task 2",
                    assigned_to="worker1",
                    created_by="test_creator",
                    priority=Priority.MEDIUM,
                    status=TaskStatus.COMPLETED,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=4,
                    created_at=datetime.now(),
                    deadline=datetime.now(),
                ),
            ]

            monitor.task_distributor.get_completed_nectars = MagicMock(  # type: ignore
                return_value=completed_nectars
            )

            avg_time = monitor._calculate_average_completion_time("worker1")
            assert avg_time == 3.0  # (2.0 + 4.0) / 2

            # 完了タスクなしの場合
            monitor.task_distributor.get_completed_nectars = MagicMock(return_value=[])  # type: ignore
            avg_time = monitor._calculate_average_completion_time("worker1")
            assert avg_time == 0.0

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_get_error_count(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """エラー数取得テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # エラー警告作成
            monitor._create_bottleneck_alert(
                "worker1", "", "worker_error", "critical", "Error 1"
            )
            monitor._create_bottleneck_alert(
                "worker1", "", "frequent_errors", "warning", "Error 2"
            )
            monitor._create_bottleneck_alert(
                "worker1", "", "overload", "warning", "Not error"
            )  # これはエラーではない

            error_count = monitor._get_error_count("worker1")
            assert error_count == 2

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_get_nectar_priority_breakdown(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """優先度別Nectar内訳テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # テスト用Nectar作成
            nectars = [
                Nectar(
                    nectar_id="high1",
                    title="High Priority Task 1",
                    description="High priority task 1",
                    assigned_to="worker1",
                    created_by="test_creator",
                    priority=Priority.HIGH,
                    status=TaskStatus.ACTIVE,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=2,
                    created_at=datetime.now(),
                    deadline=datetime.now() + timedelta(days=1),
                ),
                Nectar(
                    nectar_id="high2",
                    title="High Priority Task 2",
                    description="High priority task 2",
                    assigned_to="worker2",
                    created_by="test_creator",
                    priority=Priority.HIGH,
                    status=TaskStatus.ACTIVE,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=3,
                    created_at=datetime.now(),
                    deadline=datetime.now() + timedelta(days=1),
                ),
                Nectar(
                    nectar_id="medium1",
                    title="Medium Priority Task",
                    description="Medium priority task",
                    assigned_to="worker1",
                    created_by="test_creator",
                    priority=Priority.MEDIUM,
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=1,
                    created_at=datetime.now(),
                    deadline=datetime.now() + timedelta(days=1),
                ),
            ]

            monitor.task_distributor.get_active_nectars = MagicMock(  # type: ignore
                return_value=nectars[:2]
            )
            monitor.task_distributor.get_pending_nectars = MagicMock(  # type: ignore
                return_value=[nectars[2]]
            )

            breakdown = monitor._get_nectar_priority_breakdown()

            assert breakdown["high"] == 2
            assert breakdown["medium"] == 1
            assert breakdown.get("low", 0) == 0

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_get_completion_statistics(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """完了統計情報テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # 完了タスクを設定
            completed_nectars = [
                Nectar(
                    nectar_id="completed1",
                    title="Task 1",
                    description="Task 1",
                    assigned_to="worker1",
                    created_by="test_creator",
                    priority=Priority.MEDIUM,
                    status=TaskStatus.COMPLETED,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=2,
                    created_at=datetime.now(),
                    deadline=datetime.now(),
                ),
                Nectar(
                    nectar_id="completed2",
                    title="Task 2",
                    description="Task 2",
                    assigned_to="worker2",
                    created_by="test_creator",
                    priority=Priority.HIGH,
                    status=TaskStatus.COMPLETED,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=4,
                    created_at=datetime.now(),
                    deadline=datetime.now(),
                ),
            ]

            monitor.task_distributor.get_completed_nectars = MagicMock(  # type: ignore
                return_value=completed_nectars
            )

            with patch.object(
                monitor, "_calculate_today_completion_rate", return_value=0.8
            ):
                with patch.object(
                    monitor, "_find_most_productive_worker", return_value="worker1"
                ):
                    stats = monitor._get_completion_statistics()

                    assert stats["total_completed"] == 2
                    assert stats["average_completion_time"] == 3.0  # (2.0 + 4.0) / 2
                    assert stats["completion_rate_today"] == 0.8
                    assert stats["most_productive_worker"] == "worker1"

            # 完了タスクなしの場合
            monitor.task_distributor.get_completed_nectars = MagicMock(return_value=[])  # type: ignore
            stats = monitor._get_completion_statistics()
            assert stats["total_completed"] == 0

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_find_most_productive_worker(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """最も生産性の高いWorker取得テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # Worker状態設定
            monitor.worker_states = {
                "worker1": MagicMock(),
                "worker2": MagicMock(),
                "worker3": MagicMock(),
            }

            # 各Workerの完了タスク数を設定
            def mock_get_completed_nectars(worker_id: str) -> list[Any]:
                task_counts = {"worker1": 5, "worker2": 8, "worker3": 3}
                return [MagicMock() for _ in range(task_counts.get(worker_id, 0))]

            monitor.task_distributor.get_completed_nectars = MagicMock(  # type: ignore
                side_effect=mock_get_completed_nectars
            )

            most_productive = monitor._find_most_productive_worker()
            assert most_productive == "worker2"  # 8個で最多

            # Workerが存在しない場合
            monitor.worker_states = {}
            most_productive = monitor._find_most_productive_worker()
            assert most_productive == ""

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_get_monitoring_dashboard(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """監視ダッシュボード情報取得テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # テストデータ設定
            monitor.task_distributor.get_active_nectars = MagicMock(  # type: ignore
                return_value=[
                    MagicMock(),
                    MagicMock(),
                ]
            )
            monitor.task_distributor.get_pending_nectars = MagicMock(  # type: ignore
                return_value=[MagicMock()]
            )
            monitor.task_distributor.get_completed_nectars = MagicMock(  # type: ignore
                return_value=[MagicMock() for _ in range(5)]
            )

            # Worker状態設定
            monitor.worker_states = {
                "worker1": WorkerStatus(
                    worker_id="worker1",
                    state=WorkerState.WORKING,
                    current_tasks=["task1"],
                    last_seen=datetime.now(),
                    total_tasks_completed=3,
                    average_completion_time=2.0,
                    current_workload=0.5,
                    error_count=0,
                ),
                "worker2": WorkerStatus(
                    worker_id="worker2",
                    state=WorkerState.IDLE,
                    current_tasks=[],
                    last_seen=datetime.now(),
                    total_tasks_completed=2,
                    average_completion_time=1.5,
                    current_workload=0.0,
                    error_count=0,
                ),
            }

            # 警告設定
            monitor.bottleneck_alerts = [
                BottleneckAlert(
                    alert_id="alert1",
                    worker_id="worker1",
                    nectar_id="nectar1",
                    alert_type="overload",
                    severity="warning",
                    message="Test alert",
                    detected_at=datetime.now(),
                    resolved=False,
                )
            ]

            with patch.object(
                monitor,
                "_get_nectar_priority_breakdown",
                return_value={"high": 1, "medium": 2},
            ):
                with patch.object(
                    monitor,
                    "_get_completion_statistics",
                    return_value={"total_completed": 5},
                ):
                    dashboard = monitor.get_monitoring_dashboard()

                    # Overview確認
                    overview = dashboard["overview"]
                    assert overview["active_nectars"] == 2
                    assert overview["pending_nectars"] == 1
                    assert overview["completed_nectars"] == 5
                    assert overview["active_workers"] == 1  # WorkingはWorker1のみ
                    assert overview["total_alerts"] == 1
                    assert overview["unresolved_alerts"] == 1

                    # Worker状態確認
                    assert "worker1" in dashboard["worker_states"]
                    assert "worker2" in dashboard["worker_states"]

                    # 他のフィールド確認
                    assert "recent_alerts" in dashboard
                    assert "nectar_by_priority" in dashboard
                    assert "completion_statistics" in dashboard

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_get_worker_performance_report(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """Worker性能レポート取得テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()

            # Worker状態設定
            worker_status = WorkerStatus(
                worker_id="worker1",
                state=WorkerState.WORKING,
                current_tasks=["task1", "task2"],
                last_seen=datetime.now(),
                total_tasks_completed=10,
                average_completion_time=2.5,
                current_workload=0.7,
                error_count=1,
            )
            monitor.worker_states["worker1"] = worker_status

            # 完了タスク設定
            completed_nectars = [
                Nectar(
                    nectar_id=f"completed{i}",
                    title=f"Task {i}",
                    description=f"Task {i}",
                    assigned_to="worker1",
                    created_by="test_creator",
                    priority=Priority.MEDIUM,
                    status=TaskStatus.COMPLETED,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=2,
                    created_at=datetime.now(),
                    deadline=datetime.now(),
                )
                for i in range(3)
            ]

            monitor.task_distributor.get_completed_nectars = MagicMock(  # type: ignore
                return_value=completed_nectars
            )

            # 警告設定
            monitor.bottleneck_alerts = [
                BottleneckAlert(
                    alert_id="alert1",
                    worker_id="worker1",
                    nectar_id="nectar1",
                    alert_type="overload",
                    severity="warning",
                    message="Worker overloaded",
                    detected_at=datetime.now(),
                    resolved=False,
                )
            ]

            with patch.object(monitor, "_calculate_success_rate", return_value=0.9):
                with patch.object(
                    monitor,
                    "_get_workload_history",
                    return_value=[
                        {"timestamp": "2023-01-01T12:00:00", "workload": 0.7}
                    ],
                ):
                    report = monitor.get_worker_performance_report("worker1")

                    assert report["worker_id"] == "worker1"
                    assert "current_status" in report
                    assert report["performance_metrics"]["total_completed"] == 3
                    assert (
                        report["performance_metrics"]["average_completion_time"] == 2.5
                    )
                    assert report["performance_metrics"]["success_rate"] == 0.9
                    assert len(report["recent_tasks"]) == 3
                    assert len(report["alerts"]) == 1

        # 存在しないWorkerの場合
        report = monitor.get_worker_performance_report("nonexistent")
        assert "error" in report

    @patch("queen.status_monitor.CombAPI")
    @patch("queen.status_monitor.TaskDistributor")
    def test_save_monitoring_data(
        self, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """監視データ保存テスト"""
        with patch("queen.status_monitor.Path") as mock_path:
            mock_path.return_value = self.monitor_dir

            monitor = StatusMonitor()
            monitor.monitor_dir = self.monitor_dir

            # テストデータ設定
            monitor.worker_states["worker1"] = WorkerStatus(
                worker_id="worker1",
                state=WorkerState.WORKING,
                current_tasks=["task1"],
                last_seen=datetime.now(),
                total_tasks_completed=5,
                average_completion_time=2.0,
                current_workload=0.5,
                error_count=0,
            )

            monitor.bottleneck_alerts = [
                BottleneckAlert(
                    alert_id="alert1",
                    worker_id="worker1",
                    nectar_id="nectar1",
                    alert_type="overload",
                    severity="warning",
                    message="Test alert",
                    detected_at=datetime.now(),
                    resolved=False,
                )
            ]

            monitor._save_monitoring_data()

            # ファイルが作成されていることを確認
            today = datetime.now().strftime("%Y%m%d")
            data_file = self.monitor_dir / f"monitoring-{today}.json"
            assert data_file.exists()

            # ファイル内容の確認
            with open(data_file, encoding="utf-8") as f:
                saved_data = json.load(f)

            assert "timestamp" in saved_data
            assert "worker_states" in saved_data
            assert "alerts" in saved_data
            assert "worker1" in saved_data["worker_states"]
            assert len(saved_data["alerts"]) == 1
