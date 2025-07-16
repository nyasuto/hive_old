"""
Claude Daemon Tests

ClaudeDaemonとClaudeCommandBuilderのテストスイート
Issue #97: Claude Code永続デーモン統合
"""

import unittest
from unittest.mock import Mock, patch

from hive.agents_distributed.distributed.claude_daemon import (
    ClaudeCommandBuilder,
    ClaudeDaemon,
)


class TestClaudeDaemon(unittest.TestCase):
    """ClaudeDaemonのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.mock_tmux_manager = Mock()
        self.mock_tmux_manager.session_exists = True
        self.mock_tmux_manager.panes = {
            "queen": "hive:queen",
            "developer1": "hive:developer1",
        }

        self.daemon = ClaudeDaemon(self.mock_tmux_manager)

    def test_init(self):
        """初期化テスト"""
        assert self.daemon.tmux_manager == self.mock_tmux_manager
        assert self.daemon.daemon_status == {}
        assert self.daemon.command_queue == {}
        assert self.daemon.response_handlers == {}

    def test_default_config(self):
        """デフォルト設定テスト"""
        config = self.daemon._default_config()

        assert config["command"] == "claude --dangerously-skip-permissions"
        assert config["startup_timeout"] == 15
        assert config["response_timeout"] == 30
        assert config["max_retries"] == 3
        assert config["heartbeat_interval"] == 60

    @patch("asyncio.sleep")
    async def test_start_daemon_success(self, mock_sleep):
        """デーモン起動成功テスト"""
        # tmux_managerのモック設定
        self.mock_tmux_manager.send_to_pane.return_value = True
        self.mock_tmux_manager.get_pane_content.return_value = "claude> "

        # 非同期スリープのモック
        mock_sleep.return_value = None

        result = await self.daemon.start_daemon("queen")

        assert result is True
        assert "queen" in self.daemon.daemon_status
        assert self.daemon.daemon_status["queen"]["status"] == "running"
        assert "queen" in self.daemon.command_queue
        assert "queen" in self.daemon.response_handlers

    async def test_start_daemon_session_not_exists(self):
        """セッション未存在でのデーモン起動テスト"""
        self.mock_tmux_manager.session_exists = False

        result = await self.daemon.start_daemon("queen")

        assert result is False

    async def test_start_daemon_pane_not_found(self):
        """pane未発見でのデーモン起動テスト"""
        result = await self.daemon.start_daemon("unknown_pane")

        assert result is False

    async def test_start_daemon_already_running(self):
        """既に実行中のデーモン起動テスト"""
        # デーモンが実行中の状態を設定
        self.daemon.daemon_status["queen"] = {"status": "running"}

        result = await self.daemon.start_daemon("queen")

        assert result is True

    async def test_start_daemon_send_command_failed(self):
        """コマンド送信失敗でのデーモン起動テスト"""
        self.mock_tmux_manager.send_to_pane.return_value = False

        result = await self.daemon.start_daemon("queen")

        assert result is False

    def test_is_daemon_running(self):
        """デーモン実行状態チェックテスト"""
        # 実行中でない状態
        assert self.daemon._is_daemon_running("queen") is False

        # 実行中の状態
        self.daemon.daemon_status["queen"] = {"status": "running"}
        assert self.daemon._is_daemon_running("queen") is True

        # 停止状態
        self.daemon.daemon_status["queen"] = {"status": "stopped"}
        assert self.daemon._is_daemon_running("queen") is False

    @patch("time.time")
    @patch("asyncio.sleep")
    async def test_send_command_success(self, mock_sleep, mock_time):
        """コマンド送信成功テスト"""
        # 時間のモック
        mock_time.return_value = 1000.0
        mock_sleep.return_value = None

        # デーモンを実行中に設定
        self.daemon.daemon_status["queen"] = {
            "status": "running",
            "command_count": 0,
            "error_count": 0,
        }

        # tmux_managerのモック
        self.mock_tmux_manager.send_to_pane.return_value = True
        self.mock_tmux_manager.get_pane_content.return_value = (
            "Response content\nHuman: "
        )

        result = await self.daemon.send_command("queen", "test command")

        assert result["success"] is True
        assert "command_id" in result
        assert "response" in result
        assert "timestamp" in result

    async def test_send_command_daemon_not_running(self):
        """デーモン未実行でのコマンド送信テスト"""
        result = await self.daemon.send_command("queen", "test command")

        assert result["success"] is False
        assert "Daemon not running" in result["error"]

    async def test_send_command_send_failed(self):
        """コマンド送信失敗テスト"""
        self.daemon.daemon_status["queen"] = {
            "status": "running",
            "command_count": 0,
            "error_count": 0,
        }
        self.mock_tmux_manager.send_to_pane.return_value = False

        result = await self.daemon.send_command("queen", "test command")

        assert result["success"] is False
        assert "Failed to send command" in result["error"]

    def test_is_response_complete(self):
        """レスポンス完了検出テスト"""
        # 完了パターン
        assert self.daemon._is_response_complete("Some response\nHuman: ") is True
        assert self.daemon._is_response_complete("Response\nAssistant: ") is True
        assert self.daemon._is_response_complete("Output\n$ ") is True
        assert self.daemon._is_response_complete("Content\n> ") is True

        # 未完了パターン
        assert self.daemon._is_response_complete("Still processing...") is False
        assert self.daemon._is_response_complete("Loading data") is False

    def test_extract_response(self):
        """レスポンス抽出テスト"""
        content = "Line 1\nLine 2\nLine 3\nHuman: "

        response = self.daemon._extract_response(content)

        assert "Line 1" in response
        assert "Line 2" in response
        assert "Line 3" in response

    async def test_send_claude_prompt(self):
        """Claude プロンプト送信テスト"""
        self.daemon.daemon_status["queen"] = {
            "status": "running",
            "command_count": 0,
            "error_count": 0,
        }
        self.mock_tmux_manager.send_to_pane.return_value = True
        self.mock_tmux_manager.get_pane_content.return_value = "Response\nHuman: "

        with patch("time.time", return_value=1000.0):
            with patch("asyncio.sleep"):
                result = await self.daemon.send_claude_prompt("queen", "Hello Claude")

        assert result["success"] is True

    async def test_send_claude_file_command(self):
        """Claude ファイルコマンド送信テスト"""
        self.daemon.daemon_status["queen"] = {
            "status": "running",
            "command_count": 0,
            "error_count": 0,
        }
        self.mock_tmux_manager.send_to_pane.return_value = True
        self.mock_tmux_manager.get_pane_content.return_value = "File content\nHuman: "

        with patch("time.time", return_value=1000.0):
            with patch("asyncio.sleep"):
                result = await self.daemon.send_claude_file_command(
                    "queen", "/path/to/file.py"
                )

        assert result["success"] is True

    @patch("asyncio.sleep")
    async def test_stop_daemon(self, mock_sleep):
        """デーモン停止テスト"""
        # デーモンを実行中に設定
        self.daemon.daemon_status["queen"] = {"status": "running"}

        # tmux_managerのモック
        self.mock_tmux_manager.send_to_pane.return_value = True
        self.mock_tmux_manager.send_command_to_pane.return_value = True

        mock_sleep.return_value = None

        result = await self.daemon.stop_daemon("queen")

        assert result is True
        assert self.daemon.daemon_status["queen"]["status"] == "stopped"

    async def test_stop_daemon_not_running(self):
        """実行中でないデーモンの停止テスト"""
        result = await self.daemon.stop_daemon("queen")

        assert result is True

    @patch("asyncio.sleep")
    async def test_restart_daemon(self, mock_sleep):
        """デーモン再起動テスト"""
        # デーモンを実行中に設定
        self.daemon.daemon_status["queen"] = {"status": "running"}

        # tmux_managerのモック
        self.mock_tmux_manager.send_to_pane.return_value = True
        self.mock_tmux_manager.send_command_to_pane.return_value = True
        self.mock_tmux_manager.get_pane_content.return_value = "claude> "

        mock_sleep.return_value = None

        result = await self.daemon.restart_daemon("queen")

        assert result is True

    def test_get_daemon_status(self):
        """デーモン状態取得テスト"""
        # 存在しないデーモン
        assert self.daemon.get_daemon_status("queen") is None

        # 存在するデーモン
        status = {"status": "running", "command_count": 5}
        self.daemon.daemon_status["queen"] = status

        assert self.daemon.get_daemon_status("queen") == status

    def test_get_all_daemon_status(self):
        """全デーモン状態取得テスト"""
        # デーモン状態を設定
        self.daemon.daemon_status["queen"] = {
            "status": "running",
            "command_count": 5,
            "error_count": 1,
        }
        self.daemon.daemon_status["developer1"] = {
            "status": "stopped",
            "command_count": 3,
            "error_count": 0,
        }

        status = self.daemon.get_all_daemon_status()

        assert status["total_daemons"] == 2
        assert status["running_daemons"] == 1
        assert status["total_commands"] == 8
        assert status["total_errors"] == 1

    @patch("time.time")
    async def test_health_check_healthy(self, mock_time):
        """健康なデーモンのヘルスチェックテスト"""
        mock_time.return_value = 1000.0

        # デーモンを実行中に設定
        self.daemon.daemon_status["queen"] = {
            "status": "running",
            "command_count": 0,
            "error_count": 0,
        }

        # tmux_managerのモック
        self.mock_tmux_manager.send_to_pane.return_value = True
        self.mock_tmux_manager.get_pane_content.return_value = "ping\nHuman: "

        with patch("asyncio.sleep"):
            result = await self.daemon.health_check("queen")

        assert result["healthy"] is True
        assert "response_time" in result

    async def test_health_check_not_running(self):
        """実行中でないデーモンのヘルスチェックテスト"""
        result = await self.daemon.health_check("queen")

        assert result["healthy"] is False
        assert result["reason"] == "Daemon not running"

    @patch("asyncio.sleep")
    async def test_start_all_daemons(self, mock_sleep):
        """全デーモン起動テスト"""
        # tmux_managerのモック
        self.mock_tmux_manager.send_to_pane.return_value = True
        self.mock_tmux_manager.get_pane_content.return_value = "claude> "

        mock_sleep.return_value = None

        pane_ids = ["queen", "developer1"]
        results = await self.daemon.start_all_daemons(pane_ids)

        assert results["queen"] is True
        assert results["developer1"] is True

    @patch("asyncio.sleep")
    async def test_stop_all_daemons(self, mock_sleep):
        """全デーモン停止テスト"""
        # デーモンを実行中に設定
        self.daemon.daemon_status["queen"] = {"status": "running"}
        self.daemon.daemon_status["developer1"] = {"status": "running"}

        # tmux_managerのモック
        self.mock_tmux_manager.send_to_pane.return_value = True
        self.mock_tmux_manager.send_command_to_pane.return_value = True

        mock_sleep.return_value = None

        results = await self.daemon.stop_all_daemons()

        assert results["queen"] is True
        assert results["developer1"] is True


class TestClaudeCommandBuilder(unittest.TestCase):
    """ClaudeCommandBuilderのテスト"""

    def test_create_file_read_command(self):
        """ファイル読み込みコマンド生成テスト"""
        command = ClaudeCommandBuilder.create_file_read_command("/path/to/file.py")

        assert "Please read the file: /path/to/file.py" == command

    def test_create_file_write_command(self):
        """ファイル書き込みコマンド生成テスト"""
        command = ClaudeCommandBuilder.create_file_write_command(
            "/path/to/file.py", "print('hello')"
        )

        assert "Please write to file /path/to/file.py:" in command
        assert "print('hello')" in command

    def test_create_code_analysis_command(self):
        """コード分析コマンド生成テスト"""
        command = ClaudeCommandBuilder.create_code_analysis_command("/path/to/code.py")

        assert "Please analyze the code in: /path/to/code.py" == command

    def test_create_test_execution_command(self):
        """テスト実行コマンド生成テスト"""
        command = ClaudeCommandBuilder.create_test_execution_command("/path/to/tests/")

        assert "Please run tests in: /path/to/tests/" == command

    def test_create_refactoring_command(self):
        """リファクタリングコマンド生成テスト"""
        command = ClaudeCommandBuilder.create_refactoring_command(
            "/path/to/code.py", "Add type hints"
        )

        assert "Please refactor the code in /path/to/code.py" in command
        assert "Add type hints" in command


if __name__ == "__main__":
    unittest.main()
