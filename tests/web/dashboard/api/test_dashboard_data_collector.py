"""
HiveDashboardCollector Tests

Hiveシステムからのデータ収集テストスイート
Web Dashboard API - DashboardDataCollector単体テスト
"""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from web.dashboard.api.dashboard_api import (
    DashboardData,
    HiveDashboardCollector,
)


class TestHiveDashboardCollector:
    """HiveDashboardCollectorのテスト"""

    @pytest.mark.asyncio
    async def test_collect_dashboard_data_structure(self):
        """ダッシュボードデータ収集の構造テスト"""
        with patch(
            "web.dashboard.api.dashboard_api.WorkerCommunicator"
        ) as mock_comm_class:
            with patch("web.dashboard.api.dashboard_api.HiveWatch") as mock_watch_class:
                mock_communicator = Mock()
                mock_hive_watch = Mock()
                mock_comm_class.return_value = mock_communicator
                mock_watch_class.return_value = mock_hive_watch

                collector = HiveDashboardCollector()

                # モックデータ設定
                mock_communicator.monitor_worker_status.return_value = {
                    "session_active": True,
                    "workers": {
                        "queen": {"pane_active": True},
                        "developer": {"pane_active": False},
                    },
                }

                # ファイル操作のモック
                with patch.object(Path, "exists", return_value=False):
                    result = await collector.collect_dashboard_data()

                # 結果の構造確認
                assert isinstance(result, DashboardData)
                assert isinstance(result.timestamp, str)
                assert isinstance(result.workers, list)
                assert isinstance(result.recent_messages, list)
                assert isinstance(result.performance_metrics, dict)

    @pytest.mark.asyncio
    async def test_collect_worker_status_active_session(self):
        """アクティブセッションでのWorker状態収集テスト"""
        with patch(
            "web.dashboard.api.dashboard_api.WorkerCommunicator"
        ) as mock_comm_class:
            with patch("web.dashboard.api.dashboard_api.HiveWatch") as mock_watch_class:
                mock_communicator = Mock()
                mock_hive_watch = Mock()
                mock_comm_class.return_value = mock_communicator
                mock_watch_class.return_value = mock_hive_watch

                collector = HiveDashboardCollector()

                # モックデータ設定
                mock_communicator.monitor_worker_status.return_value = {
                    "session_active": True,
                    "workers": {
                        "queen": {"pane_active": True},
                        "developer": {"pane_active": False},
                        "tester": {"pane_active": True},
                    },
                }

                workers = await collector._collect_worker_status()

                # 結果確認
                assert len(workers) == 3

                # queenの状態確認
                queen_worker = next(w for w in workers if w.name == "queen")
                assert queen_worker.status == "active"
                assert queen_worker.emoji == "👑"
                assert queen_worker.last_activity is not None

                # developerの状態確認
                developer_worker = next(w for w in workers if w.name == "developer")
                assert developer_worker.status == "idle"
                assert developer_worker.emoji == "👨‍💻"
                assert developer_worker.last_activity is None

                # testerの状態確認
                tester_worker = next(w for w in workers if w.name == "tester")
                assert tester_worker.status == "active"
                assert tester_worker.emoji == "🧪"
                assert tester_worker.last_activity is not None

    @pytest.mark.asyncio
    async def test_collect_worker_status_inactive_session(self):
        """非アクティブセッションでのWorker状態収集テスト"""
        with patch(
            "web.dashboard.api.dashboard_api.WorkerCommunicator"
        ) as mock_comm_class:
            with patch("web.dashboard.api.dashboard_api.HiveWatch") as mock_watch_class:
                mock_communicator = Mock()
                mock_hive_watch = Mock()
                mock_comm_class.return_value = mock_communicator
                mock_watch_class.return_value = mock_hive_watch

                collector = HiveDashboardCollector()

                # モックデータ設定
                mock_communicator.monitor_worker_status.return_value = {
                    "session_active": False,
                    "workers": {},
                }

                workers = await collector._collect_worker_status()

                # 結果確認
                assert len(workers) == 7  # デフォルトWorkerの数

                # 全てのWorkerが非アクティブ
                for worker in workers:
                    assert worker.status == "inactive"
                    assert worker.emoji in ["👑", "👨‍💻", "🧪", "🔍", "📝", "👀", "📋"]

    def test_collect_recent_messages_no_file(self):
        """ログファイルが存在しない場合のメッセージ収集テスト"""
        with patch(
            "web.dashboard.api.dashboard_api.WorkerCommunicator"
        ) as mock_comm_class:
            with patch("web.dashboard.api.dashboard_api.HiveWatch") as mock_watch_class:
                mock_communicator = Mock()
                mock_hive_watch = Mock()
                mock_comm_class.return_value = mock_communicator
                mock_watch_class.return_value = mock_hive_watch

                collector = HiveDashboardCollector()

                with patch.object(Path, "exists", return_value=False):
                    messages = collector._collect_recent_messages()

                assert messages == []

    def test_collect_recent_messages_valid_file(self):
        """有効なログファイルからのメッセージ収集テスト"""
        with patch(
            "web.dashboard.api.dashboard_api.WorkerCommunicator"
        ) as mock_comm_class:
            with patch("web.dashboard.api.dashboard_api.HiveWatch") as mock_watch_class:
                mock_communicator = Mock()
                mock_hive_watch = Mock()
                mock_comm_class.return_value = mock_communicator
                mock_watch_class.return_value = mock_hive_watch

                collector = HiveDashboardCollector()

                # テスト用ログデータ
                test_log_content = (
                    '''{"timestamp": "2024-01-01T12:00:00", "source": "queen", "target": "developer", "message": "Test message 1", "session_id": "session_123"}
{"timestamp": "2024-01-01T12:01:00", "source": "developer", "target": "tester", "message": "Test message 2", "session_id": "session_123"}
{"timestamp": "2024-01-01T12:02:00", "source": "tester", "target": "queen", "message": "'''
                    + "A" * 150
                    + """", "session_id": "session_123"}
"""
                )

                with patch.object(Path, "exists", return_value=True):
                    with patch("builtins.open", mock_open(read_data=test_log_content)):
                        messages = collector._collect_recent_messages(limit=5)

                # 結果確認
                assert len(messages) == 3

                # 最初のメッセージ確認
                assert messages[0].source == "queen"
                assert messages[0].target == "developer"
                assert messages[0].message == "Test message 1"

                # 長いメッセージの切り詰め確認
                assert len(messages[2].message) == 103  # 100 + "..."
                assert messages[2].message.endswith("...")

    def test_collect_recent_messages_invalid_json(self):
        """無効なJSONを含むログファイルのメッセージ収集テスト"""
        with patch(
            "web.dashboard.api.dashboard_api.WorkerCommunicator"
        ) as mock_comm_class:
            with patch("web.dashboard.api.dashboard_api.HiveWatch") as mock_watch_class:
                mock_communicator = Mock()
                mock_hive_watch = Mock()
                mock_comm_class.return_value = mock_communicator
                mock_watch_class.return_value = mock_hive_watch

                collector = HiveDashboardCollector()

                # テスト用ログデータ（無効なJSONを含む）
                test_log_content = """{"timestamp": "2024-01-01T12:00:00", "source": "queen", "target": "developer", "message": "Valid message 1"}
invalid json line
{"timestamp": "2024-01-01T12:01:00", "source": "developer", "target": "tester", "message": "Valid message 2"}
"""

                with patch.object(Path, "exists", return_value=True):
                    with patch("builtins.open", mock_open(read_data=test_log_content)):
                        messages = collector._collect_recent_messages()

                # 有効なJSONのみが処理される
                assert len(messages) == 2
                assert messages[0].message == "Valid message 1"
                assert messages[1].message == "Valid message 2"

    def test_get_current_session_info_inactive(self):
        """非アクティブセッションの情報取得テスト"""
        with patch(
            "web.dashboard.api.dashboard_api.WorkerCommunicator"
        ) as mock_comm_class:
            with patch("web.dashboard.api.dashboard_api.HiveWatch") as mock_watch_class:
                mock_communicator = Mock()
                mock_hive_watch = Mock()
                mock_comm_class.return_value = mock_communicator
                mock_watch_class.return_value = mock_hive_watch

                collector = HiveDashboardCollector()

                mock_communicator.monitor_worker_status.return_value = {
                    "session_active": False
                }

                session_info = collector._get_current_session_info()

                assert session_info is None

    def test_get_current_session_info_active(self):
        """アクティブセッションの情報取得テスト"""
        with patch(
            "web.dashboard.api.dashboard_api.WorkerCommunicator"
        ) as mock_comm_class:
            with patch("web.dashboard.api.dashboard_api.HiveWatch") as mock_watch_class:
                mock_communicator = Mock()
                mock_hive_watch = Mock()
                mock_comm_class.return_value = mock_communicator
                mock_watch_class.return_value = mock_hive_watch

                collector = HiveDashboardCollector()

                mock_communicator.monitor_worker_status.return_value = {
                    "session_active": True,
                    "workers": {
                        "queen": {"pane_active": True},
                        "developer": {"pane_active": False},
                        "tester": {"pane_active": True},
                    },
                }

                # メッセージ収集のモック
                with patch.object(
                    collector, "_collect_recent_messages", return_value=["msg1", "msg2"]
                ):
                    session_info = collector._get_current_session_info()

                assert session_info is not None
                assert session_info.session_id.startswith("session_")
                assert session_info.start_time is not None
                assert len(session_info.active_workers) == 2  # queen, tester
                assert "queen" in session_info.active_workers
                assert "tester" in session_info.active_workers
                assert "developer" not in session_info.active_workers
                assert session_info.message_count == 2
                assert session_info.status == "active"

    def test_calculate_performance_metrics_no_messages(self):
        """メッセージなしでのパフォーマンス指標計算テスト"""
        with patch(
            "web.dashboard.api.dashboard_api.WorkerCommunicator"
        ) as mock_comm_class:
            with patch("web.dashboard.api.dashboard_api.HiveWatch") as mock_watch_class:
                mock_communicator = Mock()
                mock_hive_watch = Mock()
                mock_comm_class.return_value = mock_communicator
                mock_watch_class.return_value = mock_hive_watch

                collector = HiveDashboardCollector()

                with patch.object(
                    collector, "_collect_recent_messages", return_value=[]
                ):
                    metrics = collector._calculate_performance_metrics()

                assert metrics["efficiency"] == 0
                assert metrics["active_workers"] == 0
                assert metrics["avg_response_time"] == 0
                assert metrics["message_rate"] == 0

    def test_calculate_performance_metrics_with_messages(self):
        """メッセージありでのパフォーマンス指標計算テスト"""
        with patch(
            "web.dashboard.api.dashboard_api.WorkerCommunicator"
        ) as mock_comm_class:
            with patch("web.dashboard.api.dashboard_api.HiveWatch") as mock_watch_class:
                mock_communicator = Mock()
                mock_hive_watch = Mock()
                mock_comm_class.return_value = mock_communicator
                mock_watch_class.return_value = mock_hive_watch

                collector = HiveDashboardCollector()

                # テスト用メッセージ（現在時刻から5分以内）
                from datetime import datetime, timedelta

                now = datetime.now()
                recent_time = now - timedelta(minutes=2)

                test_messages = [
                    Mock(
                        source="queen",
                        target="developer",
                        timestamp=recent_time.isoformat(),
                    ),
                    Mock(
                        source="developer",
                        target="tester",
                        timestamp=recent_time.isoformat(),
                    ),
                    Mock(
                        source="tester",
                        target="queen",
                        timestamp=recent_time.isoformat(),
                    ),
                    Mock(
                        source="queen",
                        target="analyzer",
                        timestamp=recent_time.isoformat(),
                    ),
                ]

                with patch.object(
                    collector, "_collect_recent_messages", return_value=test_messages
                ):
                    metrics = collector._calculate_performance_metrics()

                assert metrics["efficiency"] > 0
                assert (
                    metrics["active_workers"] == 3
                )  # queen, developer, tester (unique sources)
                assert metrics["avg_response_time"] > 0
                assert metrics["message_rate"] >= 0

    def test_worker_emojis_mapping(self):
        """Worker絵文字マッピングテスト"""
        with patch(
            "web.dashboard.api.dashboard_api.WorkerCommunicator"
        ) as mock_comm_class:
            with patch("web.dashboard.api.dashboard_api.HiveWatch") as mock_watch_class:
                mock_communicator = Mock()
                mock_hive_watch = Mock()
                mock_comm_class.return_value = mock_communicator
                mock_watch_class.return_value = mock_hive_watch

                collector = HiveDashboardCollector()

                expected_emojis = {
                    "queen": "👑",
                    "developer": "👨‍💻",
                    "tester": "🧪",
                    "analyzer": "🔍",
                    "documenter": "📝",
                    "reviewer": "👀",
                    "beekeeper": "📋",
                }

                assert collector.worker_emojis == expected_emojis

    @pytest.mark.asyncio
    async def test_collect_dashboard_data_integration(self):
        """ダッシュボードデータ収集の統合テスト"""
        with patch(
            "web.dashboard.api.dashboard_api.WorkerCommunicator"
        ) as mock_comm_class:
            with patch("web.dashboard.api.dashboard_api.HiveWatch") as mock_watch_class:
                mock_communicator = Mock()
                mock_hive_watch = Mock()
                mock_comm_class.return_value = mock_communicator
                mock_watch_class.return_value = mock_hive_watch

                collector = HiveDashboardCollector()

                # モックデータ設定
                mock_communicator.monitor_worker_status.return_value = {
                    "session_active": True,
                    "workers": {
                        "queen": {"pane_active": True},
                        "developer": {"pane_active": True},
                    },
                }

                # ファイル操作のモック
                with patch.object(Path, "exists", return_value=False):
                    result = await collector.collect_dashboard_data()

                # 結果の詳細確認
                assert isinstance(result, DashboardData)
                assert len(result.workers) == 2
                assert all(w.status == "active" for w in result.workers)
                assert result.current_session is not None
                assert result.current_session.status == "active"
                assert result.performance_metrics["efficiency"] == 0  # ファイルなし


if __name__ == "__main__":
    pytest.main([__file__])
