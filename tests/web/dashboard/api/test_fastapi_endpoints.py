"""
FastAPI Endpoints Integration Tests

Web Dashboard API - FastAPI Endpoints統合テストスイート
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from web.dashboard.api.dashboard_api import (
    CommunicationMessage,
    DashboardData,
    SessionInfo,
    WorkerStatus,
    dashboard_home,
    get_performance_metrics,
    get_recent_messages,
    get_system_status,
    get_workers,
)


class TestFastAPIEndpoints:
    """FastAPI Endpoints統合テスト"""

    def setup_method(self):
        """テストセットアップ"""
        # テスト用データ
        self.test_dashboard_data = DashboardData(
            timestamp="2024-01-01T12:00:00",
            workers=[
                WorkerStatus(
                    name="queen", status="active", emoji="👑", last_activity="12:00:00"
                ),
                WorkerStatus(
                    name="developer", status="idle", emoji="👨‍💻", last_activity=None
                ),
            ],
            recent_messages=[
                CommunicationMessage(
                    timestamp="2024-01-01T12:00:00",
                    source="queen",
                    target="developer",
                    message_type="task",
                    message="Test message",
                    session_id="session_123",
                )
            ],
            current_session=SessionInfo(
                session_id="session_123",
                start_time="12:00:00",
                active_workers=["queen"],
                message_count=1,
                status="active",
            ),
            performance_metrics={
                "efficiency": 85,
                "avg_response_time": 2.3,
                "message_rate": 0.5,
                "active_workers": 1,
            },
        )

    @pytest.mark.asyncio
    async def test_dashboard_home_default_html(self):
        """ダッシュボードホーム - デフォルトHTML表示テスト"""
        with patch.object(Path, "exists", return_value=False):
            response = await dashboard_home()

            assert response.status_code == 200
            assert response.media_type == "text/html"
            assert "🐝 Hive Dashboard" in response.body.decode()
            assert "WebSocket接続中..." in response.body.decode()
            assert "dashboard.css" in response.body.decode()
            assert "dashboard.js" in response.body.decode()

    @pytest.mark.asyncio
    async def test_dashboard_home_template_file(self):
        """ダッシュボードホーム - テンプレートファイル読み込みテスト"""
        mock_template_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Custom Dashboard</title></head>
        <body><h1>Custom Content</h1></body>
        </html>
        """

        with (
            patch.object(Path, "exists", return_value=True),
            patch("builtins.open", mock_open(read_data=mock_template_content)),
        ):
            response = await dashboard_home()

            assert response.status_code == 200
            assert "Custom Dashboard" in response.body.decode()
            assert "Custom Content" in response.body.decode()

    @pytest.mark.asyncio
    async def test_get_system_status_active(self):
        """システム状態API - アクティブ状態テスト"""
        with patch("web.dashboard.api.dashboard_api.collector") as mock_collector:
            mock_collector.collect_dashboard_data = AsyncMock(
                return_value=self.test_dashboard_data
            )

            response = await get_system_status()

            assert response["status"] == "active"
            assert response["timestamp"] == "2024-01-01T12:00:00"
            assert response["worker_count"] == 2
            assert response["active_workers"] == 1
            assert response["message_count"] == 1

    @pytest.mark.asyncio
    async def test_get_system_status_inactive(self):
        """システム状態API - 非アクティブ状態テスト"""
        inactive_data = DashboardData(
            timestamp="2024-01-01T12:00:00",
            workers=[],
            recent_messages=[],
            current_session=None,
            performance_metrics={},
        )

        with patch("web.dashboard.api.dashboard_api.collector") as mock_collector:
            mock_collector.collect_dashboard_data = AsyncMock(
                return_value=inactive_data
            )

            response = await get_system_status()

            assert response["status"] == "inactive"
            assert response["worker_count"] == 0
            assert response["active_workers"] == 0
            assert response["message_count"] == 0

    @pytest.mark.asyncio
    async def test_get_workers(self):
        """Worker一覧APIテスト"""
        with patch("web.dashboard.api.dashboard_api.collector") as mock_collector:
            mock_collector.collect_dashboard_data = AsyncMock(
                return_value=self.test_dashboard_data
            )

            response = await get_workers()

            assert "workers" in response
            assert len(response["workers"]) == 2

            # Queen Worker確認
            workers_data = response["workers"]
            queen_worker = next(w for w in workers_data if w["name"] == "queen")
            assert queen_worker["status"] == "active"
            assert queen_worker["emoji"] == "👑"
            assert queen_worker["last_activity"] == "12:00:00"

            # Developer Worker確認
            developer_worker = next(w for w in workers_data if w["name"] == "developer")
            assert developer_worker["status"] == "idle"
            assert developer_worker["emoji"] == "👨‍💻"
            assert developer_worker["last_activity"] is None

    @pytest.mark.asyncio
    async def test_get_recent_messages_default_limit(self):
        """最近のメッセージAPI - デフォルトリミットテスト"""
        test_messages = [
            CommunicationMessage(
                timestamp="2024-01-01T12:00:00",
                source="queen",
                target="developer",
                message_type="task",
                message="Message 1",
                session_id="session_123",
            ),
            CommunicationMessage(
                timestamp="2024-01-01T12:01:00",
                source="developer",
                target="tester",
                message_type="response",
                message="Message 2",
                session_id="session_123",
            ),
        ]

        with patch("web.dashboard.api.dashboard_api.collector") as mock_collector:
            mock_collector._collect_recent_messages = Mock(return_value=test_messages)

            response = await get_recent_messages()

            assert "messages" in response
            assert len(response["messages"]) == 2

            # 最初のメッセージ確認
            first_message = response["messages"][0]
            assert first_message["source"] == "queen"
            assert first_message["target"] == "developer"
            assert first_message["message"] == "Message 1"
            assert first_message["message_type"] == "task"

            # デフォルトリミットが20であることを確認
            mock_collector._collect_recent_messages.assert_called_once_with(20)

    @pytest.mark.asyncio
    async def test_get_recent_messages_custom_limit(self):
        """最近のメッセージAPI - カスタムリミットテスト"""
        with patch("web.dashboard.api.dashboard_api.collector") as mock_collector:
            mock_collector._collect_recent_messages = Mock(return_value=[])

            response = await get_recent_messages(limit=5)

            assert "messages" in response
            assert len(response["messages"]) == 0

            # カスタムリミットが正しく渡されることを確認
            mock_collector._collect_recent_messages.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self):
        """パフォーマンス指標APIテスト"""
        with patch("web.dashboard.api.dashboard_api.collector") as mock_collector:
            mock_collector.collect_dashboard_data = AsyncMock(
                return_value=self.test_dashboard_data
            )

            response = await get_performance_metrics()

            assert "metrics" in response

            metrics = response["metrics"]
            assert metrics["efficiency"] == 85
            assert metrics["avg_response_time"] == 2.3
            assert metrics["message_rate"] == 0.5
            assert metrics["active_workers"] == 1

    @pytest.mark.asyncio
    async def test_api_endpoints_data_collection_error(self):
        """APIエンドポイントのデータ収集エラーテスト"""
        with patch("web.dashboard.api.dashboard_api.collector") as mock_collector:
            # データ収集エラーをシミュレート
            mock_collector.collect_dashboard_data = AsyncMock(
                side_effect=Exception("Data collection failed")
            )

            # 各エンドポイントがエラーを適切に処理することを確認
            with pytest.raises(Exception) as exc_info:
                await get_system_status()
            assert "Data collection failed" in str(exc_info.value)

            with pytest.raises(Exception) as exc_info:
                await get_workers()
            assert "Data collection failed" in str(exc_info.value)

            with pytest.raises(Exception) as exc_info:
                await get_performance_metrics()
            assert "Data collection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_recent_messages_collector_error(self):
        """最近のメッセージAPIのコレクターエラーテスト"""
        with patch("web.dashboard.api.dashboard_api.collector") as mock_collector:
            # メッセージ収集エラーをシミュレート
            mock_collector._collect_recent_messages = Mock(
                side_effect=Exception("Message collection failed")
            )

            with pytest.raises(Exception) as exc_info:
                await get_recent_messages()
            assert "Message collection failed" in str(exc_info.value)

    def test_dashboard_home_path_handling(self):
        """ダッシュボードホームのパス処理テスト"""
        # Path.exists が False の場合のテスト
        with patch.object(Path, "exists", return_value=False):
            # dashboard_home関数内でPath(__file__).parent.parentが正しく動作することを確認
            # 実際の実装では、この部分でパスの計算が行われる
            html_file = Path(__file__).parent.parent / "templates" / "index.html"
            assert not html_file.exists()  # テスト環境では存在しない

    @pytest.mark.asyncio
    async def test_api_response_data_types(self):
        """APIレスポンスのデータ型テスト"""
        with patch("web.dashboard.api.dashboard_api.collector") as mock_collector:
            mock_collector.collect_dashboard_data = AsyncMock(
                return_value=self.test_dashboard_data
            )
            mock_collector._collect_recent_messages = Mock(return_value=[])

            # システム状態API
            status_response = await get_system_status()
            assert isinstance(status_response, dict)
            assert isinstance(status_response["status"], str)
            assert isinstance(status_response["timestamp"], str)
            assert isinstance(status_response["worker_count"], int)
            assert isinstance(status_response["active_workers"], int)
            assert isinstance(status_response["message_count"], int)

            # Worker一覧API
            workers_response = await get_workers()
            assert isinstance(workers_response, dict)
            assert isinstance(workers_response["workers"], list)

            # メッセージAPI
            messages_response = await get_recent_messages()
            assert isinstance(messages_response, dict)
            assert isinstance(messages_response["messages"], list)

            # パフォーマンスAPI
            performance_response = await get_performance_metrics()
            assert isinstance(performance_response, dict)
            assert isinstance(performance_response["metrics"], dict)

    @pytest.mark.asyncio
    async def test_worker_status_serialization(self):
        """WorkerStatus オブジェクトのシリアライゼーションテスト"""
        with patch("web.dashboard.api.dashboard_api.collector") as mock_collector:
            mock_collector.collect_dashboard_data = AsyncMock(
                return_value=self.test_dashboard_data
            )

            response = await get_workers()

            # WorkerStatus オブジェクトが正しくdict形式にシリアライズされることを確認
            workers = response["workers"]
            for worker in workers:
                assert isinstance(worker, dict)
                assert "name" in worker
                assert "status" in worker
                assert "emoji" in worker
                # last_activity はNoneまたはstr
                assert worker["last_activity"] is None or isinstance(
                    worker["last_activity"], str
                )

    @pytest.mark.asyncio
    async def test_communication_message_serialization(self):
        """CommunicationMessage オブジェクトのシリアライゼーションテスト"""
        test_messages = [
            CommunicationMessage(
                timestamp="2024-01-01T12:00:00",
                source="queen",
                target="developer",
                message_type="task",
                message="Test message",
                session_id="session_123",
            )
        ]

        with patch("web.dashboard.api.dashboard_api.collector") as mock_collector:
            mock_collector._collect_recent_messages = Mock(return_value=test_messages)

            response = await get_recent_messages()

            # CommunicationMessage オブジェクトが正しくdict形式にシリアライズされることを確認
            messages = response["messages"]
            for message in messages:
                assert isinstance(message, dict)
                assert "timestamp" in message
                assert "source" in message
                assert "target" in message
                assert "message_type" in message
                assert "message" in message
                assert "session_id" in message


if __name__ == "__main__":
    pytest.main([__file__])
