"""
Queen Coordinator テスト

Queen Coordinatorクラスの包括的なテストカバレージ
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from queen.coordinator import (
    CoordinationMode,
    CoordinationReport,
    LoadBalancingStrategy,
    QueenCoordinator,
)
from queen.task_distributor import Nectar, Priority, TaskStatus


class TestCoordinationReport:
    """CoordinationReport データクラステスト"""

    def test_coordination_report_creation(self) -> None:
        """CoordinationReport作成テスト"""
        timestamp = datetime.now()
        report = CoordinationReport(
            timestamp=timestamp,
            mode=CoordinationMode.NORMAL,
            total_nectars=10,
            active_workers=3,
            completion_rate=0.75,
            bottlenecks=["overload_worker1"],
            recommendations=["Add more workers"],
            next_actions=["Execute load balancing"],
        )

        assert report.timestamp == timestamp
        assert report.mode == CoordinationMode.NORMAL
        assert report.total_nectars == 10
        assert report.active_workers == 3
        assert report.completion_rate == 0.75
        assert report.bottlenecks == ["overload_worker1"]
        assert report.recommendations == ["Add more workers"]
        assert report.next_actions == ["Execute load balancing"]

    def test_coordination_report_to_dict(self) -> None:
        """CoordinationReport辞書変換テスト"""
        timestamp = datetime.now()
        report = CoordinationReport(
            timestamp=timestamp,
            mode=CoordinationMode.EMERGENCY,
            total_nectars=5,
            active_workers=2,
            completion_rate=0.5,
            bottlenecks=[],
            recommendations=[],
            next_actions=[],
        )

        report_dict = report.to_dict()

        assert report_dict["timestamp"] == timestamp.isoformat()
        assert report_dict["mode"] == "emergency"
        assert report_dict["total_nectars"] == 5
        assert report_dict["active_workers"] == 2
        assert report_dict["completion_rate"] == 0.5


class TestQueenCoordinator:
    """QueenCoordinator クラステスト"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.test_dir = Path(tempfile.mkdtemp())

        # Coordination directory setup
        self.coordination_dir = self.test_dir / ".hive" / "coordination"
        self.coordination_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_coordinator_initialization(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """コーディネーター初期化テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator("test_queen")

            assert coordinator.queen_worker_id == "test_queen"
            assert coordinator.current_mode == CoordinationMode.NORMAL
            assert (
                coordinator.load_balancing_strategy
                == LoadBalancingStrategy.LEAST_LOADED
            )
            assert coordinator.coordination_active is False
            assert len(coordinator.known_workers) == 0

            mock_comb_api.assert_called_once_with("test_queen")
            mock_task_distributor.assert_called_once_with("test_queen")
            mock_status_monitor.assert_called_once_with("test_queen")

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_start_coordination(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """調整開始テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            with patch("asyncio.create_task") as mock_create_task:
                coordinator.start_coordination()

                assert coordinator.coordination_active is True
                mock_create_task.assert_called_once()

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_stop_coordination(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """調整停止テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()
            coordinator.coordination_active = True

            coordinator.stop_coordination()

            assert coordinator.coordination_active is False

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_determine_coordination_mode_normal(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """通常モード判定テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            situation = {
                "average_workload": 0.5,
                "bottlenecks": [],
                "completion_rate": 0.8,
            }

            mode = coordinator._determine_coordination_mode(situation)
            assert mode == CoordinationMode.NORMAL

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_determine_coordination_mode_emergency(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """緊急モード判定テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            # 緊急事態の条件設定
            situation = {
                "average_workload": 0.95,  # 緊急事態閾値超過
                "bottlenecks": [],
                "completion_rate": 0.8,
            }

            mode = coordinator._determine_coordination_mode(situation)
            assert mode == CoordinationMode.EMERGENCY

            # 複数ボトルネックでも緊急事態
            situation = {
                "average_workload": 0.5,
                "bottlenecks": ["b1", "b2", "b3", "b4"],  # 3個超過
                "completion_rate": 0.8,
            }

            mode = coordinator._determine_coordination_mode(situation)
            assert mode == CoordinationMode.EMERGENCY

            # 低い完了率でも緊急事態
            situation = {
                "average_workload": 0.5,
                "bottlenecks": [],
                "completion_rate": 0.4,  # 0.5未満
            }

            mode = coordinator._determine_coordination_mode(situation)
            assert mode == CoordinationMode.EMERGENCY

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_determine_coordination_mode_optimizing(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """最適化モード判定テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            # 負荷分散閾値超過で最適化モード
            situation = {
                "average_workload": 0.8,  # 負荷分散閾値(0.7)超過
                "bottlenecks": [],
                "completion_rate": 0.8,
            }

            mode = coordinator._determine_coordination_mode(situation)
            assert mode == CoordinationMode.OPTIMIZING

            # ボトルネック存在で最適化モード
            situation = {
                "average_workload": 0.5,
                "bottlenecks": ["bottleneck1"],
                "completion_rate": 0.8,
            }

            mode = coordinator._determine_coordination_mode(situation)
            assert mode == CoordinationMode.OPTIMIZING

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_select_least_loaded_worker(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """最小負荷Worker選択テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            worker_workloads = {
                "worker1": {"total_estimated_time": 8.0},
                "worker2": {"total_estimated_time": 4.0},  # 最小
                "worker3": {"total_estimated_time": 6.0},
            }

            selected = coordinator._select_least_loaded_worker(worker_workloads)
            assert selected == "worker2"

            # 空の場合
            selected = coordinator._select_least_loaded_worker({})
            assert selected is None

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_select_skill_based_worker(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """スキルベースWorker選択テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            # Workerスキル設定
            coordinator.worker_capabilities = {
                "worker1": ["python", "api"],
                "worker2": ["javascript", "frontend"],
                "worker3": ["python", "backend"],
            }

            worker_workloads = {
                "worker1": {"total_estimated_time": 6.0},
                "worker2": {"total_estimated_time": 4.0},
                "worker3": {"total_estimated_time": 5.0},  # pythonスキルで最小負荷
            }

            # pythonタグを持つNectar
            nectar = Nectar(
                nectar_id="test_nectar",
                title="Python Development Task",
                description="Python development task",
                assigned_to="",
                created_by="test_creator",
                priority=Priority.MEDIUM,
                status=TaskStatus.PENDING,
                dependencies=[],
                expected_honey=[],
                estimated_time=2,
                created_at=datetime.now(),
                deadline=datetime.now() + timedelta(days=1),
                tags=["python"],
            )

            selected = coordinator._select_skill_based_worker(nectar, worker_workloads)
            assert selected == "worker3"  # pythonスキルを持つ中で最小負荷

            # スキルマッチしない場合は最小負荷を選択
            nectar.tags = ["ruby"]
            selected = coordinator._select_skill_based_worker(nectar, worker_workloads)
            assert selected == "worker2"  # 全体で最小負荷

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_select_round_robin_worker(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """ラウンドロビンWorker選択テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            worker_workloads = {
                "worker1": {"total_estimated_time": 6.0},
                "worker2": {"total_estimated_time": 4.0},
                "worker3": {"total_estimated_time": 5.0},
            }

            selected = coordinator._select_round_robin_worker(worker_workloads)
            # 簡易実装では最初のWorkerを選択
            assert selected in worker_workloads.keys()

            # 空の場合
            selected = coordinator._select_round_robin_worker({})
            assert selected is None

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_calculate_completion_rate(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """完了率計算テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            # モックの設定
            coordinator.task_distributor.get_completed_nectars = MagicMock(  # type: ignore
                return_value=[
                    1,
                    2,
                    3,
                ]
            )  # 3個完了
            coordinator.task_distributor.get_active_nectars = MagicMock(  # type: ignore
                return_value=[
                    4,
                    5,
                ]
            )  # 2個アクティブ
            coordinator.task_distributor.get_pending_nectars = MagicMock(  # type: ignore
                return_value=[6]
            )  # 1個保留

            completion_rate = coordinator._calculate_completion_rate()
            assert completion_rate == 0.5  # 3 / (3 + 2 + 1) = 0.5

            # タスクが0個の場合
            coordinator.task_distributor.get_completed_nectars = MagicMock(  # type: ignore
                return_value=[]
            )
            coordinator.task_distributor.get_active_nectars = MagicMock(return_value=[])  # type: ignore
            coordinator.task_distributor.get_pending_nectars = MagicMock(  # type: ignore
                return_value=[]
            )

            completion_rate = coordinator._calculate_completion_rate()
            assert completion_rate == 0.0

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_calculate_average_workload(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """平均ワークロード計算テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            worker_workloads = {
                "worker1": {"total_estimated_time": 8.0},
                "worker2": {"total_estimated_time": 4.0},
                "worker3": {"total_estimated_time": 6.0},
            }

            avg_workload = coordinator._calculate_average_workload(worker_workloads)
            assert avg_workload == 6.0  # (8 + 4 + 6) / 3 = 6.0

            # 空の場合
            avg_workload = coordinator._calculate_average_workload({})
            assert avg_workload == 0.0

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_identify_bottlenecks(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """ボトルネック特定テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            dashboard = {
                "recent_alerts": [
                    {"alert_type": "overload_worker1", "resolved": False},
                    {"alert_type": "deadline_miss", "resolved": False},
                    {"alert_type": "old_alert", "resolved": True},  # 解決済み
                ]
            }

            bottlenecks = coordinator._identify_bottlenecks(dashboard)
            assert len(bottlenecks) == 2
            assert "overload_worker1" in bottlenecks
            assert "deadline_miss" in bottlenecks
            assert "old_alert" not in bottlenecks

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_identify_urgent_tasks(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """緊急タスク特定テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            now = datetime.now()
            nectars = [
                Nectar(
                    nectar_id="urgent1",
                    title="Urgent Task 1",
                    description="Urgent task 1",
                    assigned_to="worker1",
                    created_by="test_creator",
                    priority=Priority.HIGH,
                    status=TaskStatus.ACTIVE,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=1,
                    created_at=now - timedelta(hours=1),
                    deadline=now + timedelta(hours=1),  # 1時間後（緊急）
                ),
                Nectar(
                    nectar_id="normal1",
                    title="Normal Task",
                    description="Normal task",
                    assigned_to="worker2",
                    created_by="test_creator",
                    priority=Priority.MEDIUM,
                    status=TaskStatus.ACTIVE,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=2,
                    created_at=now - timedelta(hours=1),
                    deadline=now + timedelta(days=1),  # 1日後（通常）
                ),
                Nectar(
                    nectar_id="completed1",
                    title="Completed Urgent Task",
                    description="Completed urgent task",
                    assigned_to="worker3",
                    created_by="test_creator",
                    priority=Priority.HIGH,
                    status=TaskStatus.COMPLETED,
                    dependencies=[],
                    expected_honey=[],
                    estimated_time=1,
                    created_at=now - timedelta(hours=2),
                    deadline=now + timedelta(hours=1),  # 緊急だが完了済み
                ),
            ]

            urgent_tasks = coordinator._identify_urgent_tasks(nectars)
            assert len(urgent_tasks) == 1
            assert urgent_tasks[0].nectar_id == "urgent1"

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_update_known_workers(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """既知Worker更新テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            # テスト用Nectar作成
            nectar1 = Nectar(
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
            )

            nectar2 = Nectar(
                nectar_id="nectar2",
                title="Task 2",
                description="Task 2",
                assigned_to="worker2",
                created_by="test_creator",
                priority=Priority.HIGH,
                status=TaskStatus.PENDING,
                dependencies=[],
                expected_honey=[],
                estimated_time=3,
                created_at=datetime.now(),
                deadline=datetime.now() + timedelta(days=1),
            )

            # モック設定
            coordinator.task_distributor.get_active_nectars = MagicMock(  # type: ignore
                return_value=[nectar1]
            )
            coordinator.task_distributor.get_pending_nectars = MagicMock(  # type: ignore
                return_value=[nectar2]
            )
            coordinator.task_distributor.get_completed_nectars = MagicMock(  # type: ignore
                return_value=[]
            )

            coordinator._update_known_workers()

            assert "worker1" in coordinator.known_workers
            assert "worker2" in coordinator.known_workers
            assert len(coordinator.known_workers) == 2

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_generate_recommendations(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """推奨事項生成テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            # 高負荷・低完了率・多ボトルネックの状況
            situation = {
                "average_workload": 7.0,  # 6時間超過
                "completion_rate": 0.6,  # 0.7未満
                "bottlenecks": ["b1", "b2", "b3"],  # 2個超過
            }

            recommendations = coordinator._generate_recommendations(situation)

            assert len(recommendations) == 3
            assert any("adding more workers" in r.lower() for r in recommendations)
            assert any("review task complexity" in r.lower() for r in recommendations)
            assert any(
                "proactive bottleneck prevention" in r.lower() for r in recommendations
            )

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_generate_next_actions(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """次のアクション生成テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            situation = {
                "urgent_tasks": ["task1", "task2"],
                "average_workload": 0.8,  # 負荷分散閾値(0.7)超過
                "bottlenecks": ["bottleneck1"],
            }

            actions = coordinator._generate_next_actions(situation)

            assert len(actions) == 3
            assert any("urgent tasks" in action.lower() for action in actions)
            assert any("load balancing" in action.lower() for action in actions)
            assert any("bottlenecks" in action.lower() for action in actions)

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    @pytest.mark.asyncio  # type: ignore
    async def test_save_coordination_report(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """調整レポート保存テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()
            coordinator.coordination_dir = self.coordination_dir

            report = CoordinationReport(
                timestamp=datetime.now(),
                mode=CoordinationMode.NORMAL,
                total_nectars=5,
                active_workers=2,
                completion_rate=0.8,
                bottlenecks=[],
                recommendations=[],
                next_actions=[],
            )

            await coordinator._save_coordination_report(report)

            # ファイルが作成されていることを確認
            report_files = list(self.coordination_dir.glob("coordination-*.json"))
            assert len(report_files) == 1

            # ファイル内容の確認
            with open(report_files[0], encoding="utf-8") as f:
                saved_data = json.load(f)

            assert saved_data["mode"] == "normal"
            assert saved_data["total_nectars"] == 5
            assert saved_data["active_workers"] == 2
            assert saved_data["completion_rate"] == 0.8

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_get_coordination_summary(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """調整サマリー取得テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()
            coordinator.known_workers = {"worker1", "worker2"}
            coordinator.coordination_active = True

            summary = coordinator.get_coordination_summary()

            assert summary["current_mode"] == "normal"
            assert summary["coordination_active"] is True
            assert summary["load_balancing_strategy"] == "least_loaded"
            assert set(summary["known_workers"]) == {"worker1", "worker2"}
            assert "statistics" in summary
            assert "config" in summary

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_update_load_balancing_strategy(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """負荷分散戦略更新テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            coordinator.update_load_balancing_strategy(
                LoadBalancingStrategy.SKILL_BASED
            )
            assert (
                coordinator.load_balancing_strategy == LoadBalancingStrategy.SKILL_BASED
            )

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_update_worker_capabilities(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """Workerスキル更新テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            capabilities = ["python", "api", "database"]
            coordinator.update_worker_capabilities("worker1", capabilities)

            assert coordinator.worker_capabilities["worker1"] == capabilities

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_force_emergency_mode(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """緊急モード強制起動テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            coordinator.force_emergency_mode()
            assert coordinator.current_mode == CoordinationMode.EMERGENCY

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    def test_reset_to_normal_mode(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """通常モードリセットテスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()
            coordinator.current_mode = CoordinationMode.EMERGENCY

            coordinator.reset_to_normal_mode()
            assert coordinator.current_mode == CoordinationMode.NORMAL

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    @pytest.mark.asyncio  # type: ignore
    async def test_send_urgent_notification(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """緊急通知送信テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            nectar = Nectar(
                nectar_id="urgent_nectar",
                title="Urgent Task",
                description="Urgent task",
                assigned_to="worker1",
                created_by="test_creator",
                priority=Priority.CRITICAL,
                status=TaskStatus.ACTIVE,
                dependencies=[],
                expected_honey=[],
                estimated_time=2,
                created_at=datetime.now(),
                deadline=datetime.now() + timedelta(hours=1),
            )

            await coordinator._send_urgent_notification(nectar)

            # CombAPIのsend_messageが呼ばれていることを確認
            coordinator.comb_api.send_message.assert_called_once()  # type: ignore
            call_args = coordinator.comb_api.send_message.call_args  # type: ignore

            assert call_args[1]["to_worker"] == "worker1"
            assert call_args[1]["content"]["nectar_id"] == "urgent_nectar"
            assert call_args[1]["content"]["urgent"] is True

    @patch("queen.coordinator.CombAPI")
    @patch("queen.coordinator.TaskDistributor")
    @patch("queen.coordinator.StatusMonitor")
    @pytest.mark.asyncio  # type: ignore
    async def test_notify_emergency_status(
        self, mock_status_monitor: Any, mock_task_distributor: Any, mock_comb_api: Any
    ) -> None:
        """緊急状態通知テスト"""
        with patch("queen.coordinator.Path") as mock_path:
            mock_path.return_value = self.coordination_dir

            coordinator = QueenCoordinator()

            await coordinator._notify_emergency_status()

            # CombAPIのadd_progressが呼ばれていることを確認
            coordinator.comb_api.add_progress.assert_called_once()  # type: ignore
            call_args = coordinator.comb_api.add_progress.call_args  # type: ignore

            assert "Emergency Mode Activated" in call_args[0][0]
