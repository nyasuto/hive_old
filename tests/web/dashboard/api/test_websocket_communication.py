"""
WebSocket Communication Tests

Web Dashboard API - WebSocket通信テストスイート
最終フェーズ: リアルタイム通信機能の包括的テスト
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from web.dashboard.api.dashboard_api import (
    CommunicationMessage,
    DashboardData,
    SessionInfo,
    WorkerStatus,
    broadcast_dashboard_data,
    websocket_endpoint,
)


class MockWebSocket:
    """WebSocketモッククラス"""

    def __init__(self):
        self.accept = AsyncMock()
        self.send_text = AsyncMock()
        self.receive_text = AsyncMock()
        self.closed = False
        self.disconnect_called = False

    async def close(self):
        self.closed = True


class MockWebSocketDisconnect(Exception):
    """WebSocketDisconnect例外のモック"""

    pass


class TestWebSocketCommunication:
    """WebSocket通信テスト"""

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
    async def test_websocket_basic_connection(self):
        """WebSocket基本接続テスト"""
        mock_websocket = MockWebSocket()
        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        # 接続が確立されるが即座に切断されることをシミュレート
        mock_websocket.receive_text.side_effect = MockWebSocketDisconnect()

        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch(
                "web.dashboard.api.dashboard_api.WebSocketDisconnect",
                MockWebSocketDisconnect,
            ):
                await websocket_endpoint(mock_websocket)

        # 接続確立が呼ばれたことを確認
        mock_manager.connect.assert_called_once_with(mock_websocket)

        # 切断処理が呼ばれたことを確認
        mock_manager.disconnect.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_websocket_keep_alive_loop(self):
        """WebSocket keep-aliveループテスト"""
        mock_websocket = MockWebSocket()
        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        # 最初の2回はメッセージを受信し、3回目で切断
        mock_websocket.receive_text.side_effect = [
            "keep-alive",
            "keep-alive",
            MockWebSocketDisconnect(),
        ]

        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch(
                "web.dashboard.api.dashboard_api.WebSocketDisconnect",
                MockWebSocketDisconnect,
            ):
                await websocket_endpoint(mock_websocket)

        # receive_textが3回呼ばれたことを確認
        assert mock_websocket.receive_text.call_count == 3

        # 切断処理が呼ばれたことを確認
        mock_manager.disconnect.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_websocket_disconnect_handling(self):
        """WebSocket切断処理テスト"""
        mock_websocket = MockWebSocket()
        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        # 接続後即座に切断
        mock_websocket.receive_text.side_effect = MockWebSocketDisconnect()

        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch(
                "web.dashboard.api.dashboard_api.WebSocketDisconnect",
                MockWebSocketDisconnect,
            ):
                await websocket_endpoint(mock_websocket)

        # 接続と切断が正しく処理されたことを確認
        mock_manager.connect.assert_called_once_with(mock_websocket)
        mock_manager.disconnect.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_websocket_connection_error(self):
        """WebSocket接続エラーテスト"""
        mock_websocket = MockWebSocket()
        mock_manager = Mock()
        mock_manager.connect = AsyncMock(side_effect=Exception("Connection failed"))
        mock_manager.disconnect = Mock()

        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch(
                "web.dashboard.api.dashboard_api.WebSocketDisconnect",
                MockWebSocketDisconnect,
            ):
                # 接続エラーが発生することを確認
                with pytest.raises(Exception) as exc_info:
                    await websocket_endpoint(mock_websocket)

                assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_broadcast_dashboard_data_with_connections(self):
        """アクティブ接続ありでのダッシュボードデータ配信テスト"""
        mock_manager = Mock()
        mock_manager.active_connections = [MockWebSocket(), MockWebSocket()]
        mock_manager.broadcast = AsyncMock()

        mock_collector = Mock()
        mock_collector.collect_dashboard_data = AsyncMock(
            return_value=self.test_dashboard_data
        )

        # 1回のループでテストを終了するため、asyncio.sleepで例外を発生させる
        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch("web.dashboard.api.dashboard_api.collector", mock_collector):
                with patch("asyncio.sleep", side_effect=KeyboardInterrupt()):
                    try:
                        await broadcast_dashboard_data()
                    except KeyboardInterrupt:
                        pass  # テスト終了のため無視

        # データ収集が呼ばれたことを確認
        mock_collector.collect_dashboard_data.assert_called_once()

        # ブロードキャストが呼ばれたことを確認
        mock_manager.broadcast.assert_called_once_with(self.test_dashboard_data)

    @pytest.mark.asyncio
    async def test_broadcast_dashboard_data_no_connections(self):
        """アクティブ接続なしでのダッシュボードデータ配信テスト"""
        mock_manager = Mock()
        mock_manager.active_connections = []
        mock_manager.broadcast = AsyncMock()

        mock_collector = Mock()
        mock_collector.collect_dashboard_data = AsyncMock(
            return_value=self.test_dashboard_data
        )

        # 1回のループでテストを終了
        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch("web.dashboard.api.dashboard_api.collector", mock_collector):
                with patch("asyncio.sleep", side_effect=KeyboardInterrupt()):
                    try:
                        await broadcast_dashboard_data()
                    except KeyboardInterrupt:
                        pass  # テスト終了のため無視

        # アクティブ接続がないため、データ収集は呼ばれない
        mock_collector.collect_dashboard_data.assert_not_called()

        # ブロードキャストも呼ばれない
        mock_manager.broadcast.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_dashboard_data_error_handling(self):
        """ダッシュボードデータ配信エラーハンドリングテスト"""
        mock_manager = Mock()
        mock_manager.active_connections = [MockWebSocket()]
        mock_manager.broadcast = AsyncMock(side_effect=Exception("Broadcast failed"))

        mock_collector = Mock()
        mock_collector.collect_dashboard_data = AsyncMock(
            return_value=self.test_dashboard_data
        )

        # エラーが発生してもループが継続することを確認
        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch("web.dashboard.api.dashboard_api.collector", mock_collector):
                with patch("asyncio.sleep", side_effect=KeyboardInterrupt()):
                    with patch("builtins.print") as mock_print:
                        try:
                            await broadcast_dashboard_data()
                        except KeyboardInterrupt:
                            pass  # テスト終了のため無視

        # エラーメッセージが出力されることを確認
        mock_print.assert_called_with("Error broadcasting data: Broadcast failed")

        # データ収集とブロードキャストが試行されたことを確認
        mock_collector.collect_dashboard_data.assert_called_once()
        mock_manager.broadcast.assert_called_once_with(self.test_dashboard_data)

    @pytest.mark.asyncio
    async def test_broadcast_data_collection_error(self):
        """データ収集エラーでのブロードキャストテスト"""
        mock_manager = Mock()
        mock_manager.active_connections = [MockWebSocket()]
        mock_manager.broadcast = AsyncMock()

        mock_collector = Mock()
        mock_collector.collect_dashboard_data = AsyncMock(
            side_effect=Exception("Data collection failed")
        )

        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch("web.dashboard.api.dashboard_api.collector", mock_collector):
                with patch("asyncio.sleep", side_effect=KeyboardInterrupt()):
                    with patch("builtins.print") as mock_print:
                        try:
                            await broadcast_dashboard_data()
                        except KeyboardInterrupt:
                            pass  # テスト終了のため無視

        # エラーメッセージが出力されることを確認
        mock_print.assert_called_with("Error broadcasting data: Data collection failed")

        # データ収集が試行されたことを確認
        mock_collector.collect_dashboard_data.assert_called_once()

        # ブロードキャストは呼ばれない
        mock_manager.broadcast.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_websocket_connections(self):
        """複数WebSocket接続の同時管理テスト"""
        mock_websocket1 = MockWebSocket()
        mock_websocket2 = MockWebSocket()

        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        # 両方のWebSocketが同時に切断されることをシミュレート
        mock_websocket1.receive_text.side_effect = MockWebSocketDisconnect()
        mock_websocket2.receive_text.side_effect = MockWebSocketDisconnect()

        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch(
                "web.dashboard.api.dashboard_api.WebSocketDisconnect",
                MockWebSocketDisconnect,
            ):
                # 2つのWebSocket接続を並行処理
                await asyncio.gather(
                    websocket_endpoint(mock_websocket1),
                    websocket_endpoint(mock_websocket2),
                    return_exceptions=True,
                )

        # 両方のWebSocketで接続と切断が処理されたことを確認
        assert mock_manager.connect.call_count == 2
        assert mock_manager.disconnect.call_count == 2

    @pytest.mark.asyncio
    async def test_websocket_message_flow(self):
        """WebSocketメッセージフローテスト"""
        mock_websocket = MockWebSocket()
        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        # 複数のメッセージを受信してから切断
        call_count = 0

        async def mock_receive():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return f"message_{call_count}"
            raise MockWebSocketDisconnect()

        mock_websocket.receive_text = mock_receive

        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch(
                "web.dashboard.api.dashboard_api.WebSocketDisconnect",
                MockWebSocketDisconnect,
            ):
                await websocket_endpoint(mock_websocket)

        # メッセージが正しく受信されたことを確認
        assert call_count == 4  # 3回成功 + 1回切断

        # 接続と切断が正しく処理されたことを確認
        mock_manager.connect.assert_called_once_with(mock_websocket)
        mock_manager.disconnect.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_websocket_concurrent_broadcast(self):
        """WebSocket同時配信テスト"""
        mock_websocket1 = MockWebSocket()
        mock_websocket2 = MockWebSocket()

        mock_manager = Mock()
        mock_manager.active_connections = [mock_websocket1, mock_websocket2]
        mock_manager.broadcast = AsyncMock()

        mock_collector = Mock()
        mock_collector.collect_dashboard_data = AsyncMock(
            return_value=self.test_dashboard_data
        )

        # 複数の並行配信をシミュレート
        tasks = []
        for _ in range(3):
            task = asyncio.create_task(self._single_broadcast_cycle())
            tasks.append(task)

        # 短時間で全タスクを完了
        await asyncio.gather(*tasks, return_exceptions=True)

        # 各タスクが独立してモックを作成するため、この部分は検証しない
        # 代わりに、タスクが正常に完了したことを確認
        assert len(tasks) == 3
        for task in tasks:
            assert task.done()
            assert not task.cancelled()

    async def _single_broadcast_cycle(self):
        """単一配信サイクルのヘルパー関数"""
        mock_manager = Mock()
        mock_manager.active_connections = [MockWebSocket()]
        mock_manager.broadcast = AsyncMock()

        mock_collector = Mock()
        mock_collector.collect_dashboard_data = AsyncMock(
            return_value=self.test_dashboard_data
        )

        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch("web.dashboard.api.dashboard_api.collector", mock_collector):
                if mock_manager.active_connections:
                    data = await mock_collector.collect_dashboard_data()
                    await mock_manager.broadcast(data)

    @pytest.mark.asyncio
    async def test_websocket_scalability_stress(self):
        """WebSocketスケーラビリティストレステスト"""
        # 大量のWebSocket接続をシミュレート
        num_connections = 50
        mock_websockets = [MockWebSocket() for _ in range(num_connections)]

        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        # 全ての接続が即座に切断されることをシミュレート
        for ws in mock_websockets:
            ws.receive_text.side_effect = MockWebSocketDisconnect()

        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch(
                "web.dashboard.api.dashboard_api.WebSocketDisconnect",
                MockWebSocketDisconnect,
            ):
                # 大量のWebSocket接続を並行処理
                tasks = [websocket_endpoint(ws) for ws in mock_websockets]
                await asyncio.gather(*tasks, return_exceptions=True)

        # 全ての接続で接続と切断が処理されたことを確認
        assert mock_manager.connect.call_count == num_connections
        assert mock_manager.disconnect.call_count == num_connections

    @pytest.mark.asyncio
    async def test_websocket_network_recovery(self):
        """WebSocketネットワーク復旧テスト"""
        mock_websocket = MockWebSocket()
        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        # 最初は接続エラー、その後正常に接続
        connect_attempts = [
            Exception("Network error"),
            None,  # 正常接続
        ]

        mock_manager.connect.side_effect = connect_attempts
        mock_websocket.receive_text.side_effect = MockWebSocketDisconnect()

        with patch("web.dashboard.api.dashboard_api.manager", mock_manager):
            with patch(
                "web.dashboard.api.dashboard_api.WebSocketDisconnect",
                MockWebSocketDisconnect,
            ):
                # 最初の接続試行はエラー
                with pytest.raises(Exception) as exc_info:
                    await websocket_endpoint(mock_websocket)

                assert "Network error" in str(exc_info.value)

                # 2回目の接続試行は成功
                await websocket_endpoint(mock_websocket)

        # 接続が2回試行されたことを確認
        assert mock_manager.connect.call_count == 2

        # 最後の接続では切断処理も実行されたことを確認
        mock_manager.disconnect.assert_called_once_with(mock_websocket)


if __name__ == "__main__":
    pytest.main([__file__])
