"""
Tmux Manager Tests

TmuxManagerとPaneMessengerのテストスイート
Issue #96: tmux統合基盤システム
"""

import json
import unittest
from unittest.mock import Mock, patch

from hive.agents_distributed.distributed.tmux_manager import PaneMessenger, TmuxManager


class TestTmuxManager(unittest.TestCase):
    """TmuxManagerのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.tmux_manager = TmuxManager("test_session")

    def test_init(self):
        """初期化テスト"""
        assert self.tmux_manager.session_name == "test_session"
        assert self.tmux_manager.panes == {}
        assert self.tmux_manager.session_exists is False

    @patch("subprocess.run")
    def test_create_hive_session_success(self, mock_run):
        """セッション作成成功テスト"""
        # すべてのsubprocess.runが成功を返すように設定
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""

        # セッション存在チェックは最初はFalse
        with patch.object(self.tmux_manager, "_session_exists", return_value=False):
            result = self.tmux_manager.create_hive_session()

        assert result is True
        assert self.tmux_manager.session_exists is True
        assert "beekeeper" in self.tmux_manager.panes
        assert "queen" in self.tmux_manager.panes
        assert "developer1" in self.tmux_manager.panes

    @patch("subprocess.run")
    def test_create_hive_session_already_exists(self, mock_run):
        """既存セッションテスト"""
        with patch.object(self.tmux_manager, "_session_exists", return_value=True):
            result = self.tmux_manager.create_hive_session()

        assert result is True
        assert self.tmux_manager.session_exists is True

    @patch("subprocess.run")
    def test_create_hive_session_failure(self, mock_run):
        """セッション作成失敗テスト"""
        # subprocess.runが失敗を返すように設定
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Error creating session"

        with patch.object(self.tmux_manager, "_session_exists", return_value=False):
            result = self.tmux_manager.create_hive_session()

        assert result is False
        assert self.tmux_manager.session_exists is False

    @patch("subprocess.run")
    def test_send_to_pane_success(self, mock_run):
        """メッセージ送信成功テスト"""
        # セッション初期化
        self.tmux_manager.session_exists = True
        self.tmux_manager.panes = {"beekeeper": "test_session:beekeeper"}

        # subprocess.runが成功を返すように設定
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""

        result = self.tmux_manager.send_to_pane("beekeeper", "test message")

        assert result is True
        mock_run.assert_called_once()

    def test_send_to_pane_session_not_exists(self):
        """セッション未初期化テスト"""
        result = self.tmux_manager.send_to_pane("beekeeper", "test message")

        assert result is False

    def test_send_to_pane_unknown_pane(self):
        """未知のpaneテスト"""
        self.tmux_manager.session_exists = True
        self.tmux_manager.panes = {"beekeeper": "test_session:beekeeper"}

        result = self.tmux_manager.send_to_pane("unknown", "test message")

        assert result is False

    @patch("subprocess.run")
    def test_send_to_pane_failure(self, mock_run):
        """メッセージ送信失敗テスト"""
        # セッション初期化
        self.tmux_manager.session_exists = True
        self.tmux_manager.panes = {"beekeeper": "test_session:beekeeper"}

        # subprocess.runが失敗を返すように設定
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Send failed"

        result = self.tmux_manager.send_to_pane("beekeeper", "test message")

        assert result is False

    @patch("subprocess.run")
    def test_get_pane_content_success(self, mock_run):
        """pane内容取得成功テスト"""
        # セッション初期化
        self.tmux_manager.session_exists = True
        self.tmux_manager.panes = {"beekeeper": "test_session:beekeeper"}

        # subprocess.runが成功を返すように設定
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "test content\\nline 2"

        result = self.tmux_manager.get_pane_content("beekeeper")

        assert result == "test content\\nline 2"

    def test_get_pane_content_session_not_exists(self):
        """セッション未初期化での内容取得テスト"""
        result = self.tmux_manager.get_pane_content("beekeeper")

        assert result is None

    def test_list_panes(self):
        """paneリスト取得テスト"""
        self.tmux_manager.panes = {"beekeeper": "test:beekeeper", "queen": "test:queen"}

        result = self.tmux_manager.list_panes()

        assert result == ["beekeeper", "queen"]

    @patch("subprocess.run")
    def test_get_pane_status_success(self, mock_run):
        """pane状態取得成功テスト"""
        # セッション初期化
        self.tmux_manager.session_exists = True
        self.tmux_manager.panes = {"beekeeper": "test_session:beekeeper"}

        # subprocess.runが成功を返すように設定
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "1"

        result = self.tmux_manager.get_pane_status("beekeeper")

        assert result is not None
        assert result["pane_id"] == "beekeeper"
        assert result["active"] is True
        assert result["exists"] is True

    @patch("subprocess.run")
    def test_destroy_session_success(self, mock_run):
        """セッション破棄成功テスト"""
        # セッション初期化
        self.tmux_manager.session_exists = True
        self.tmux_manager.panes = {"beekeeper": "test_session:beekeeper"}

        # subprocess.runが成功を返すように設定
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""

        result = self.tmux_manager.destroy_session()

        assert result is True
        assert self.tmux_manager.session_exists is False
        assert self.tmux_manager.panes == {}

    def test_destroy_session_not_exists(self):
        """セッション未初期化での破棄テスト"""
        result = self.tmux_manager.destroy_session()

        assert result is True

    def test_get_session_status(self):
        """セッション状態取得テスト"""
        self.tmux_manager.session_exists = True
        self.tmux_manager.panes = {"beekeeper": "test_session:beekeeper"}

        with patch.object(
            self.tmux_manager, "get_pane_status", return_value={"test": "data"}
        ):
            result = self.tmux_manager.get_session_status()

        assert result["session_name"] == "test_session"
        assert result["exists"] is True
        assert "panes" in result
        assert result["panes"]["beekeeper"] == {"test": "data"}


class TestPaneMessenger(unittest.TestCase):
    """PaneMessengerのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.mock_tmux_manager = Mock()
        self.messenger = PaneMessenger(self.mock_tmux_manager)

    def test_init(self):
        """初期化テスト"""
        assert self.messenger.tmux_manager == self.mock_tmux_manager

    def test_send_structured_message_success(self):
        """構造化メッセージ送信成功テスト"""
        # tmux_manager.send_to_paneが成功を返すように設定
        self.mock_tmux_manager.send_to_pane.return_value = True

        result = self.messenger.send_structured_message(
            "beekeeper", "queen", "test_message", {"test": "data"}
        )

        assert result is True

        # send_to_paneが正しい引数で呼ばれたかチェック
        self.mock_tmux_manager.send_to_pane.assert_called_once()
        call_args = self.mock_tmux_manager.send_to_pane.call_args

        assert call_args[0][0] == "queen"  # to_pane
        assert call_args[0][1].startswith("HIVE_MESSAGE:")  # formatted message

        # JSONメッセージの構造をチェック
        json_part = call_args[0][1][13:]  # "HIVE_MESSAGE:" を除去
        message_data = json.loads(json_part)

        assert message_data["from"] == "beekeeper"
        assert message_data["to"] == "queen"
        assert message_data["type"] == "test_message"
        assert message_data["content"] == {"test": "data"}
        assert "timestamp" in message_data

    def test_send_structured_message_failure(self):
        """構造化メッセージ送信失敗テスト"""
        # tmux_manager.send_to_paneが失敗を返すように設定
        self.mock_tmux_manager.send_to_pane.return_value = False

        result = self.messenger.send_structured_message(
            "beekeeper", "queen", "test_message", {"test": "data"}
        )

        assert result is False

    def test_send_task_message(self):
        """タスクメッセージ送信テスト"""
        self.mock_tmux_manager.send_to_pane.return_value = True

        result = self.messenger.send_task_message(
            "beekeeper", "queen", "task_123", {"action": "solve_issue"}
        )

        assert result is True

        # send_to_paneが呼ばれたかチェック
        self.mock_tmux_manager.send_to_pane.assert_called_once()

    def test_send_response_message(self):
        """応答メッセージ送信テスト"""
        self.mock_tmux_manager.send_to_pane.return_value = True

        result = self.messenger.send_response_message(
            "queen", "beekeeper", "task_123", {"status": "completed"}
        )

        assert result is True

        # send_to_paneが呼ばれたかチェック
        self.mock_tmux_manager.send_to_pane.assert_called_once()

    def test_send_heartbeat(self):
        """ハートビート送信テスト"""
        self.mock_tmux_manager.send_to_pane.return_value = True

        result = self.messenger.send_heartbeat("beekeeper", "queen")

        assert result is True

        # send_to_paneが呼ばれたかチェック
        self.mock_tmux_manager.send_to_pane.assert_called_once()

    def test_send_structured_message_exception(self):
        """構造化メッセージ送信例外テスト"""
        # tmux_manager.send_to_paneが例外を投げるように設定
        self.mock_tmux_manager.send_to_pane.side_effect = Exception("Test error")

        result = self.messenger.send_structured_message(
            "beekeeper", "queen", "test_message", {"test": "data"}
        )

        assert result is False


if __name__ == "__main__":
    unittest.main()
