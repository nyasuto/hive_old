"""
Hive Tmux Integration テスト
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from hive.tmux_integration import HiveTmuxIntegration, PaneInfo, WorkerPaneMapping


class TestHiveTmuxIntegration:
    """HiveTmuxIntegration のテストクラス"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.integration = HiveTmuxIntegration(self.test_dir)

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_with_default_mapping(self) -> None:
        """デフォルトマッピングでの初期化テスト"""
        assert len(self.integration.worker_mappings) == 6
        assert "queen" in self.integration.worker_mappings
        assert "architect" in self.integration.worker_mappings
        assert "frontend" in self.integration.worker_mappings
        assert "backend" in self.integration.worker_mappings
        assert "devops" in self.integration.worker_mappings
        assert "tester" in self.integration.worker_mappings

        # Queen workerのマッピング確認
        queen_mapping = self.integration.worker_mappings["queen"]
        assert queen_mapping.worker_name == "queen"
        assert queen_mapping.pane_index == 0
        assert queen_mapping.title == "Queen Worker"

    def test_init_with_custom_mapping(self) -> None:
        """カスタムマッピングでの初期化テスト"""
        # カスタム設定ファイルを作成
        tmux_dir = self.test_dir / "templates" / "tmux"
        tmux_dir.mkdir(parents=True)

        custom_config = {
            "session": "custom-hive",
            "workers": {
                "queen": {"pane": 1, "title": "Custom Queen"},
                "architect": {"pane": 2, "title": "Custom Architect"},
            },
        }

        with open(tmux_dir / "workers.json", "w", encoding="utf-8") as f:
            json.dump(custom_config, f)

        # 新しいインスタンスを作成
        integration = HiveTmuxIntegration(self.test_dir)

        assert integration.session_name == "custom-hive"
        assert len(integration.worker_mappings) == 2
        assert integration.worker_mappings["queen"].pane_index == 1
        assert integration.worker_mappings["queen"].title == "Custom Queen"

    def test_is_in_tmux_true(self) -> None:
        """tmux環境内の判定テスト（True）"""
        with patch.dict("os.environ", {"TMUX": "/tmp/tmux-1000/default,12345,0"}):
            assert self.integration.is_in_tmux() is True

    def test_is_in_tmux_false(self) -> None:
        """tmux環境外の判定テスト（False）"""
        with patch.dict("os.environ", {}, clear=True):
            assert self.integration.is_in_tmux() is False

    @patch("hive.tmux_integration.libtmux")
    def test_get_hive_session_found(self, mock_libtmux: Mock) -> None:
        """hiveセッション取得テスト（見つかった場合）"""
        with patch.dict("os.environ", {"TMUX": "/tmp/tmux-1000/default,12345,0"}):
            # モックセッションを設定
            mock_session = Mock()
            mock_session.name = "hive"
            mock_server = Mock()
            mock_server.sessions = [mock_session]
            mock_libtmux.Server.return_value = mock_server

            result = self.integration.get_hive_session()

            assert result == mock_session
            assert self.integration.tmux_session == mock_session

    @patch("hive.tmux_integration.libtmux")
    def test_get_hive_session_not_found(self, mock_libtmux: Mock) -> None:
        """hiveセッション取得テスト（見つからない場合）"""
        with patch.dict("os.environ", {"TMUX": "/tmp/tmux-1000/default,12345,0"}):
            # モックセッションを設定（hiveセッションなし）
            mock_session = Mock()
            mock_session.name = "other-session"
            mock_server = Mock()
            mock_server.sessions = [mock_session]
            mock_libtmux.Server.return_value = mock_server

            result = self.integration.get_hive_session()

            assert result is None

    def test_get_hive_session_not_in_tmux(self) -> None:
        """tmux環境外でのセッション取得テスト"""
        with patch.dict("os.environ", {}, clear=True):
            result = self.integration.get_hive_session()
            assert result is None

    def test_get_worker_pane_id_found(self) -> None:
        """Worker pane ID取得テスト（見つかった場合）"""
        # マッピングを手動で設定
        self.integration.worker_mappings["queen"].pane_id = "%1"

        with patch.object(self.integration, "update_worker_mappings"):
            result = self.integration.get_worker_pane_id("queen")
            assert result == "%1"

    def test_get_worker_pane_id_not_found(self) -> None:
        """Worker pane ID取得テスト（見つからない場合）"""
        with patch.object(self.integration, "update_worker_mappings"):
            result = self.integration.get_worker_pane_id("nonexistent")
            assert result is None

    @patch("subprocess.run")
    def test_send_message_to_pane_success(self, mock_run: Mock) -> None:
        """paneへのメッセージ送信テスト（成功）"""
        mock_run.return_value.returncode = 0

        with patch.dict("os.environ", {"TMUX": "/tmp/tmux-1000/default,12345,0"}):
            with patch.object(
                self.integration, "get_worker_pane_id", return_value="%1"
            ):
                result = self.integration.send_message_to_pane("queen", "test message")

                assert result is True
                mock_run.assert_called_once()

                # 呼び出された引数を確認
                call_args = mock_run.call_args[0][0]
                assert call_args[0] == "tmux"
                assert call_args[1] == "send-keys"
                assert call_args[2] == "-t"
                assert call_args[3] == "%1"

    @patch("subprocess.run")
    def test_send_message_to_pane_failure(self, mock_run: Mock) -> None:
        """paneへのメッセージ送信テスト（失敗）"""
        mock_run.return_value.returncode = 1

        with patch.dict("os.environ", {"TMUX": "/tmp/tmux-1000/default,12345,0"}):
            with patch.object(
                self.integration, "get_worker_pane_id", return_value="%1"
            ):
                result = self.integration.send_message_to_pane("queen", "test message")

                assert result is False

    def test_send_message_to_pane_not_in_tmux(self) -> None:
        """tmux環境外でのメッセージ送信テスト"""
        with patch.dict("os.environ", {}, clear=True):
            result = self.integration.send_message_to_pane("queen", "test message")
            assert result is False

    def test_send_message_to_pane_no_pane_id(self) -> None:
        """pane ID未設定での送信テスト"""
        with patch.dict("os.environ", {"TMUX": "/tmp/tmux-1000/default,12345,0"}):
            with patch.object(
                self.integration, "get_worker_pane_id", return_value=None
            ):
                result = self.integration.send_message_to_pane("queen", "test message")
                assert result is False

    @patch("subprocess.run")
    def test_get_current_worker_success(self, mock_run: Mock) -> None:
        """現在のworker取得テスト（成功）"""
        mock_run.return_value.stdout = "%1:0"
        mock_run.return_value.returncode = 0

        with patch.dict("os.environ", {"TMUX": "/tmp/tmux-1000/default,12345,0"}):
            with patch.object(self.integration, "update_worker_mappings"):
                # queen workerがpane 0にマッピングされている設定
                self.integration.worker_mappings["queen"].pane_index = 0
                self.integration.worker_mappings["queen"].pane_id = "%1"

                result = self.integration.get_current_worker()

                assert result == "queen"

    @patch("subprocess.run")
    def test_get_current_worker_not_in_tmux(self, mock_run: Mock) -> None:
        """tmux環境外での現在worker取得テスト"""
        with patch.dict("os.environ", {}, clear=True):
            result = self.integration.get_current_worker()
            assert result is None

    def test_get_session_status_no_session(self) -> None:
        """セッション状態取得テスト（セッションなし）"""
        with patch.object(self.integration, "get_hive_session", return_value=None):
            status = self.integration.get_session_status()

            assert status["session_exists"] is False
            assert status["session_name"] == "hive"
            assert status["workers"] == {}
            assert status["unmapped_panes"] == []

    def test_get_session_status_with_session(self) -> None:
        """セッション状態取得テスト（セッションあり）"""
        mock_session = Mock()

        with patch.object(
            self.integration, "get_hive_session", return_value=mock_session
        ):
            with patch.object(self.integration, "update_worker_mappings"):
                with patch.object(self.integration, "get_all_panes", return_value=[]):
                    # テスト用マッピングを設定
                    self.integration.worker_mappings["queen"].pane_id = "%1"
                    self.integration.worker_mappings["queen"].is_active = True

                    status = self.integration.get_session_status()

                    assert status["session_exists"] is True
                    assert "queen" in status["workers"]
                    assert status["workers"]["queen"]["mapped"] is True
                    assert status["workers"]["queen"]["is_active"] is True

    def test_save_current_mapping(self) -> None:
        """現在のマッピング保存テスト"""
        with patch.object(self.integration, "update_worker_mappings"):
            self.integration.save_current_mapping()

            # 保存されたファイルを確認
            config_file = self.test_dir / ".hive" / "tmux" / "workers.json"
            assert config_file.exists()

            with open(config_file, encoding="utf-8") as f:
                config = json.load(f)

            assert config["session"] == "hive"
            assert "workers" in config
            assert "queen" in config["workers"]
            assert config["workers"]["queen"]["pane"] == 0


class TestPaneInfo:
    """PaneInfo データクラステスト"""

    def test_pane_info_creation(self) -> None:
        """PaneInfo作成テスト"""
        pane = PaneInfo(
            pane_id="%1",
            pane_index=0,
            pane_title="Queen Worker",
            is_active=True,
            current_command="zsh",
        )

        assert pane.pane_id == "%1"
        assert pane.pane_index == 0
        assert pane.pane_title == "Queen Worker"
        assert pane.is_active is True
        assert pane.current_command == "zsh"


class TestWorkerPaneMapping:
    """WorkerPaneMapping データクラステスト"""

    def test_worker_pane_mapping_creation(self) -> None:
        """WorkerPaneMapping作成テスト"""
        mapping = WorkerPaneMapping(
            worker_name="queen",
            pane_index=0,
            pane_id="%1",
            title="Queen Worker",
            description="Project management",
            is_active=True,
        )

        assert mapping.worker_name == "queen"
        assert mapping.pane_index == 0
        assert mapping.pane_id == "%1"
        assert mapping.title == "Queen Worker"
        assert mapping.description == "Project management"
        assert mapping.is_active is True

    def test_worker_pane_mapping_defaults(self) -> None:
        """WorkerPaneMapping デフォルト値テスト"""
        mapping = WorkerPaneMapping(worker_name="architect", pane_index=1)

        assert mapping.worker_name == "architect"
        assert mapping.pane_index == 1
        assert mapping.pane_id is None
        assert mapping.title is None
        assert mapping.description is None
        assert mapping.is_active is False
