"""
Hive CLI テスト
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from hive.cli_core import HiveCLI, MessageInfo, WorkerInfo


class TestHiveCLI:
    """Hive CLI のテストクラス"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.cli = HiveCLI()

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init(self) -> None:
        """CLI初期化テスト"""
        assert self.cli.project_root is not None
        assert (
            self.cli.current_worker in self.cli.VALID_WORKERS
            or self.cli.current_worker == "unknown"
        )
        assert self.cli.VALID_WORKERS == [
            "queen",
            "architect",
            "frontend",
            "backend",
            "devops",
            "tester",
        ]

    def test_detect_current_worker_default(self) -> None:
        """デフォルトworker検出テスト"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("hive.cli_core.libtmux", None):
                cli = HiveCLI()
                assert cli.current_worker == "unknown"

    def test_detect_current_worker_from_env(self) -> None:
        """環境変数からworker検出テスト"""
        with patch.dict(os.environ, {"HIVE_WORKER_NAME": "backend"}):
            cli = HiveCLI()
            assert cli.current_worker == "backend"

    def test_is_in_tmux_false(self) -> None:
        """tmux環境外の判定テスト"""
        with patch.dict(os.environ, {}, clear=True):
            cli = HiveCLI()
            assert not cli._is_in_tmux()

    def test_is_in_tmux_true(self) -> None:
        """tmux環境内の判定テスト"""
        with patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,12345,0"}):
            cli = HiveCLI()
            assert cli._is_in_tmux()

    def test_send_message_valid_recipient(self) -> None:
        """有効なrecipientへのメッセージ送信テスト"""
        with patch.object(self.cli, "_save_message_to_file") as mock_save:
            with patch.object(self.cli, "_send_to_tmux_pane") as mock_tmux:
                self.cli.send_message("backend", "テストメッセージ")
                mock_save.assert_called_once_with(
                    "backend", "テストメッセージ", "normal"
                )
                mock_tmux.assert_called_once_with(
                    "backend", "テストメッセージ", "normal"
                )

    def test_send_message_invalid_recipient(self) -> None:
        """無効なrecipientへのメッセージ送信テスト"""
        with pytest.raises(ValueError) as exc_info:
            self.cli.send_message("invalid", "テストメッセージ")
        assert "無効なWorker名" in str(exc_info.value)

    def test_urgent_message(self) -> None:
        """緊急メッセージ送信テスト"""
        with patch.object(self.cli, "send_message") as mock_send:
            self.cli.urgent_message("queen", "緊急メッセージ")
            mock_send.assert_called_once_with(
                "queen", "緊急メッセージ", priority="urgent"
            )

    def test_broadcast_message(self) -> None:
        """ブロードキャストメッセージテスト"""
        with patch.object(self.cli, "_save_message_to_file") as mock_save:
            with patch.object(self.cli, "_send_to_tmux_pane") as mock_tmux:
                self.cli.current_worker = "queen"
                self.cli.broadcast_message("全体メッセージ")

                # queen以外の全workerに送信されることを確認
                expected_calls = len(self.cli.VALID_WORKERS) - 1  # queen自身を除く
                assert mock_save.call_count == expected_calls
                assert mock_tmux.call_count == expected_calls

    def test_save_message_to_file(self) -> None:
        """メッセージファイル保存テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            self.cli._save_message_to_file("backend", "テストメッセージ", "normal")

            # メッセージファイルが作成されていることを確認
            messages_dir = self.test_dir / ".hive" / "messages"
            assert messages_dir.exists()

            message_files = list(messages_dir.glob("*.json"))
            assert len(message_files) == 1

            # メッセージ内容を確認
            with open(message_files[0], encoding="utf-8") as f:
                data = json.load(f)
                assert data["to_worker"] == "backend"
                assert data["message"] == "テストメッセージ"
                assert data["priority"] == "normal"

    def test_get_all_workers_without_tmux(self) -> None:
        """tmux環境なしでのworker取得テスト"""
        with patch.object(self.cli, "tmux_session", None):
            workers = self.cli._get_all_workers()
            assert len(workers) == len(self.cli.VALID_WORKERS)
            assert all(w.pane_id == "virtual" for w in workers)

    def test_who_am_i_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """who-am-i出力テスト"""
        with patch.object(self.cli, "current_worker", "backend"):
            with patch.object(self.cli, "_is_in_tmux", return_value=False):
                self.cli.who_am_i()
                captured = capsys.readouterr()
                assert "現在のWorker: backend" in captured.out

    def test_status_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """status出力テスト"""
        with patch.object(self.cli, "current_worker", "frontend"):
            with patch.object(self.cli, "_is_in_tmux", return_value=False):
                with patch.object(self.cli, "_get_all_workers", return_value=[]):
                    with patch.object(self.cli, "_show_message_statistics"):
                        self.cli.status()
                        captured = capsys.readouterr()
                        assert "Hive Status" in captured.out
                        assert "現在のWorker: frontend" in captured.out

    def test_show_message_statistics_no_messages(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """メッセージ統計表示テスト（メッセージなし）"""
        with patch.object(self.cli, "project_root", self.test_dir):
            self.cli._show_message_statistics()
            captured = capsys.readouterr()
            assert "メッセージなし" in captured.out

    def test_show_message_statistics_with_messages(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """メッセージ統計表示テスト（メッセージあり）"""
        with patch.object(self.cli, "project_root", self.test_dir):
            # テスト用メッセージファイルを作成
            messages_dir = self.test_dir / ".hive" / "messages"
            messages_dir.mkdir(parents=True, exist_ok=True)

            message_data = {
                "from_worker": "queen",
                "to_worker": "backend",
                "message": "テストメッセージ",
                "timestamp": "2025-01-01T12:00:00",
                "priority": "normal",
            }

            with open(messages_dir / "test_message.json", "w", encoding="utf-8") as f:
                json.dump(message_data, f, ensure_ascii=False, indent=2)

            self.cli._show_message_statistics()
            captured = capsys.readouterr()
            assert "メッセージ統計: 1 件" in captured.out
            assert "queen → backend" in captured.out


class TestWorkerInfo:
    """WorkerInfo データクラステスト"""

    def test_worker_info_creation(self) -> None:
        """WorkerInfo作成テスト"""
        worker = WorkerInfo(name="backend", pane_id="1", active=True)
        assert worker.name == "backend"
        assert worker.pane_id == "1"
        assert worker.active is True
        assert worker.last_activity is None


class TestMessageInfo:
    """MessageInfo データクラステスト"""

    def test_message_info_creation(self) -> None:
        """MessageInfo作成テスト"""
        from datetime import datetime

        timestamp = datetime.now()
        message = MessageInfo(
            from_worker="queen",
            to_worker="backend",
            message="テストメッセージ",
            timestamp=timestamp,
            priority="urgent",
            message_type="command",
        )

        assert message.from_worker == "queen"
        assert message.to_worker == "backend"
        assert message.message == "テストメッセージ"
        assert message.timestamp == timestamp
        assert message.priority == "urgent"
        assert message.message_type == "command"

    def test_message_info_defaults(self) -> None:
        """MessageInfo デフォルト値テスト"""
        from datetime import datetime

        timestamp = datetime.now()
        message = MessageInfo(
            from_worker="queen",
            to_worker="backend",
            message="テストメッセージ",
            timestamp=timestamp,
        )

        assert message.priority == "normal"
        assert message.message_type == "command"
