"""
ConnectionManager Tests

WebSocket接続管理のテストスイート
Web Dashboard API - ConnectionManager単体テスト
"""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import WebSocket

from web.dashboard.api.dashboard_api import ConnectionManager, DashboardData


class TestConnectionManager:
    """ConnectionManagerのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.connection_manager = ConnectionManager()
        self.mock_websocket = Mock(spec=WebSocket)
        self.mock_websocket.accept = AsyncMock()
        self.mock_websocket.send_text = AsyncMock()

    def test_init(self):
        """初期化テスト"""
        assert isinstance(self.connection_manager.active_connections, set)
        assert len(self.connection_manager.active_connections) == 0
        assert self.connection_manager.last_data is None

    @pytest.mark.asyncio
    async def test_connect_without_last_data(self):
        """初期データなしでの接続テスト"""
        # last_dataがない状態で接続
        assert self.connection_manager.last_data is None

        await self.connection_manager.connect(self.mock_websocket)

        # WebSocketの接続確認
        self.mock_websocket.accept.assert_called_once()
        assert self.mock_websocket in self.connection_manager.active_connections

        # 初期データ送信は実行されない
        self.mock_websocket.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_connect_with_last_data(self):
        """初期データありでの接続テスト"""
        # テスト用のlast_dataを設定
        test_data = DashboardData(
            timestamp="2024-01-01T00:00:00",
            workers=[],
            recent_messages=[],
            current_session=None,
            performance_metrics={},
        )
        self.connection_manager.last_data = test_data

        await self.connection_manager.connect(self.mock_websocket)

        # WebSocketの接続確認
        self.mock_websocket.accept.assert_called_once()
        assert self.mock_websocket in self.connection_manager.active_connections

        # 初期データが送信される
        self.mock_websocket.send_text.assert_called_once_with(
            test_data.model_dump_json()
        )

    def test_disconnect(self):
        """切断テスト"""
        # 接続を追加
        self.connection_manager.active_connections.add(self.mock_websocket)
        assert self.mock_websocket in self.connection_manager.active_connections

        # 切断
        self.connection_manager.disconnect(self.mock_websocket)

        # 接続が削除される
        assert self.mock_websocket not in self.connection_manager.active_connections

    def test_disconnect_nonexistent_connection(self):
        """存在しない接続の切断テスト"""
        # 存在しない接続を切断（エラーが発生しないことを確認）
        self.connection_manager.disconnect(self.mock_websocket)
        assert len(self.connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_single_connection(self):
        """単一接続へのブロードキャストテスト"""
        # 接続を追加
        self.connection_manager.active_connections.add(self.mock_websocket)

        # テストデータ
        test_data = DashboardData(
            timestamp="2024-01-01T00:00:00",
            workers=[],
            recent_messages=[],
            current_session=None,
            performance_metrics={},
        )

        await self.connection_manager.broadcast(test_data)

        # last_dataが更新される
        assert self.connection_manager.last_data == test_data

        # メッセージが送信される
        self.mock_websocket.send_text.assert_called_once_with(
            test_data.model_dump_json()
        )

    @pytest.mark.asyncio
    async def test_broadcast_multiple_connections(self):
        """複数接続へのブロードキャストテスト"""
        # 複数の接続を追加
        mock_websocket2 = Mock(spec=WebSocket)
        mock_websocket2.send_text = AsyncMock()

        self.connection_manager.active_connections.add(self.mock_websocket)
        self.connection_manager.active_connections.add(mock_websocket2)

        # テストデータ
        test_data = DashboardData(
            timestamp="2024-01-01T00:00:00",
            workers=[],
            recent_messages=[],
            current_session=None,
            performance_metrics={},
        )

        await self.connection_manager.broadcast(test_data)

        # 両方の接続にメッセージが送信される
        expected_message = test_data.model_dump_json()
        self.mock_websocket.send_text.assert_called_once_with(expected_message)
        mock_websocket2.send_text.assert_called_once_with(expected_message)

    @pytest.mark.asyncio
    async def test_broadcast_with_failed_connection(self):
        """失敗した接続を含むブロードキャストテスト"""
        # 正常な接続と失敗する接続を追加
        mock_websocket_failed = Mock(spec=WebSocket)
        mock_websocket_failed.send_text = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        self.connection_manager.active_connections.add(self.mock_websocket)
        self.connection_manager.active_connections.add(mock_websocket_failed)

        # テストデータ
        test_data = DashboardData(
            timestamp="2024-01-01T00:00:00",
            workers=[],
            recent_messages=[],
            current_session=None,
            performance_metrics={},
        )

        await self.connection_manager.broadcast(test_data)

        # 正常な接続にはメッセージが送信される
        self.mock_websocket.send_text.assert_called_once_with(
            test_data.model_dump_json()
        )

        # 失敗した接続は削除される
        assert mock_websocket_failed not in self.connection_manager.active_connections
        assert self.mock_websocket in self.connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_no_connections(self):
        """接続なしでのブロードキャストテスト"""
        # 接続がない状態でブロードキャスト
        test_data = DashboardData(
            timestamp="2024-01-01T00:00:00",
            workers=[],
            recent_messages=[],
            current_session=None,
            performance_metrics={},
        )

        await self.connection_manager.broadcast(test_data)

        # last_dataは更新される
        assert self.connection_manager.last_data == test_data

        # エラーは発生しない
        assert len(self.connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_updates_last_data(self):
        """ブロードキャストでlast_dataが更新されるテスト"""
        # 初期データ
        initial_data = DashboardData(
            timestamp="2024-01-01T00:00:00",
            workers=[],
            recent_messages=[],
            current_session=None,
            performance_metrics={},
        )
        self.connection_manager.last_data = initial_data

        # 新しいデータ
        new_data = DashboardData(
            timestamp="2024-01-01T01:00:00",
            workers=[],
            recent_messages=[],
            current_session=None,
            performance_metrics={"test": "value"},
        )

        await self.connection_manager.broadcast(new_data)

        # last_dataが新しいデータに更新される
        assert self.connection_manager.last_data == new_data
        assert self.connection_manager.last_data != initial_data


if __name__ == "__main__":
    pytest.main([__file__])
