"""
Claude Code永続デーモン統合システム

各tmux paneでClaude Code --dangerously-skip-permissionsを実行し、
コマンド送信・レスポンス受信を管理する
"""

import asyncio
import logging
import time


class ClaudeDaemon:
    """Claude Codeデーモン管理クラス"""

    def __init__(self, tmux_manager, config: dict | None = None):
        self.tmux_manager = tmux_manager
        self.logger = logging.getLogger("claude_daemon")
        self.config = config or self._default_config()
        self.daemon_status: dict[str, dict] = {}
        self.command_queue: dict[str, list] = {}
        self.response_handlers: dict[str, asyncio.Queue] = {}

    def _default_config(self) -> dict:
        """デフォルト設定"""
        return {
            "command": "claude --dangerously-skip-permissions",
            "startup_timeout": 15,
            "response_timeout": 30,
            "max_retries": 3,
            "heartbeat_interval": 60,
            "log_level": "INFO",
        }

    async def start_daemon(self, pane_id: str) -> bool:
        """指定されたpaneでClaude Codeデーモンを起動"""
        try:
            self.logger.info(f"Starting Claude daemon in pane: {pane_id}")

            # paneの存在確認
            if not self.tmux_manager.session_exists:
                self.logger.error("Tmux session not exists")
                return False

            if pane_id not in self.tmux_manager.panes:
                self.logger.error(f"Pane {pane_id} not found")
                return False

            # 既存のデーモンをチェック
            if self._is_daemon_running(pane_id):
                self.logger.info(f"Daemon already running in pane: {pane_id}")
                return True

            # Claude Codeデーモンを起動
            command = self.config["command"]
            success = self.tmux_manager.send_to_pane(pane_id, command)

            if not success:
                self.logger.error(f"Failed to send daemon command to pane: {pane_id}")
                return False

            # 起動待機
            await self._wait_for_daemon_startup(pane_id)

            # デーモン状態を記録
            self.daemon_status[pane_id] = {
                "status": "running",
                "started_at": time.time(),
                "last_heartbeat": time.time(),
                "command_count": 0,
                "error_count": 0,
            }

            # コマンドキューを初期化
            self.command_queue[pane_id] = []
            self.response_handlers[pane_id] = asyncio.Queue()

            self.logger.info(f"Claude daemon started successfully in pane: {pane_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error starting daemon in pane {pane_id}: {e}")
            return False

    async def _wait_for_daemon_startup(self, pane_id: str) -> None:
        """デーモンの起動完了を待機"""
        startup_timeout = self.config["startup_timeout"]
        start_time = time.time()

        while time.time() - start_time < startup_timeout:
            # Claude Codeの起動プロンプトを確認
            content = self.tmux_manager.get_pane_content(pane_id, 5)
            if content and ("claude" in content.lower() or ">" in content):
                self.logger.debug(f"Daemon startup detected in pane: {pane_id}")
                await asyncio.sleep(2)  # 完全な起動を待つ
                return

            await asyncio.sleep(1)

        self.logger.warning(f"Daemon startup timeout in pane: {pane_id}")

    def _is_daemon_running(self, pane_id: str) -> bool:
        """デーモンが実行中かチェック"""
        if pane_id not in self.daemon_status:
            return False

        status = self.daemon_status[pane_id]
        return status.get("status") == "running"

    async def send_command(
        self, pane_id: str, command: str, timeout: int | None = None
    ) -> dict:
        """指定されたpaneにコマンドを送信し、レスポンスを受信"""
        if not self._is_daemon_running(pane_id):
            return {"success": False, "error": f"Daemon not running in pane: {pane_id}"}

        try:
            timeout = timeout or self.config["response_timeout"]
            command_id = f"cmd_{int(time.time() * 1000)}"

            self.logger.debug(f"Sending command to {pane_id}: {command[:100]}...")

            # コマンドを送信
            success = self.tmux_manager.send_to_pane(pane_id, command)
            if not success:
                return {
                    "success": False,
                    "error": f"Failed to send command to pane: {pane_id}",
                }

            # レスポンスを待機
            response = await self._wait_for_response(pane_id, timeout)

            # 統計更新
            self.daemon_status[pane_id]["command_count"] += 1
            self.daemon_status[pane_id]["last_heartbeat"] = time.time()

            return {
                "success": True,
                "command_id": command_id,
                "response": response,
                "timestamp": time.time(),
            }

        except Exception as e:
            self.logger.error(f"Error sending command to {pane_id}: {e}")
            self.daemon_status[pane_id]["error_count"] += 1
            return {"success": False, "error": str(e)}

    async def _wait_for_response(self, pane_id: str, timeout: int) -> str:
        """レスポンスを待機"""
        start_time = time.time()
        last_content = ""

        while time.time() - start_time < timeout:
            current_content = self.tmux_manager.get_pane_content(pane_id, 20)

            if current_content and current_content != last_content:
                # 新しいコンテンツが出力された
                last_content = current_content

                # Claude Codeの応答完了を検出
                if self._is_response_complete(current_content):
                    return self._extract_response(current_content)

            await asyncio.sleep(0.5)

        return f"Response timeout after {timeout} seconds"

    def _is_response_complete(self, content: str) -> bool:
        """レスポンスが完了したかチェック"""
        # Claude Codeの応答完了を示すパターン
        completion_patterns = [
            "Human:",  # 次のプロンプト待ち
            "Assistant:",  # 応答完了
            "$ ",  # コマンドプロンプト
            "> ",  # 待機プロンプト
        ]

        for pattern in completion_patterns:
            if pattern in content:
                return True

        return False

    def _extract_response(self, content: str) -> str:
        """paneコンテンツからレスポンスを抽出"""
        lines = content.strip().split("\n")

        # 最後の数行を取得（Claude Codeの応答部分）
        relevant_lines = []
        for line in reversed(lines):
            if line.strip():
                relevant_lines.append(line)
                if len(relevant_lines) >= 10:  # 最大10行
                    break

        return "\n".join(reversed(relevant_lines))

    async def send_claude_prompt(
        self, pane_id: str, prompt: str, timeout: int | None = None
    ) -> dict:
        """Claude Codeにプロンプトを送信"""
        return await self.send_command(pane_id, prompt, timeout)

    async def send_claude_file_command(
        self,
        pane_id: str,
        file_path: str,
        action: str = "read",
        timeout: int | None = None,
    ) -> dict:
        """Claude Codeにファイル操作コマンドを送信"""
        command = f"Please {action} the file: {file_path}"
        return await self.send_command(pane_id, command, timeout)

    async def stop_daemon(self, pane_id: str) -> bool:
        """指定されたpaneのデーモンを停止"""
        try:
            if not self._is_daemon_running(pane_id):
                self.logger.info(f"Daemon not running in pane: {pane_id}")
                return True

            # 終了コマンドを送信
            self.tmux_manager.send_to_pane(pane_id, "exit")
            await asyncio.sleep(2)

            # Ctrl+Cで強制終了
            self.tmux_manager.send_command_to_pane(pane_id, "C-c")
            await asyncio.sleep(1)

            # 状態を更新
            if pane_id in self.daemon_status:
                self.daemon_status[pane_id]["status"] = "stopped"
                self.daemon_status[pane_id]["stopped_at"] = time.time()

            self.logger.info(f"Daemon stopped in pane: {pane_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping daemon in pane {pane_id}: {e}")
            return False

    async def restart_daemon(self, pane_id: str) -> bool:
        """デーモンを再起動"""
        self.logger.info(f"Restarting daemon in pane: {pane_id}")

        # 停止
        await self.stop_daemon(pane_id)
        await asyncio.sleep(2)

        # 再起動
        return await self.start_daemon(pane_id)

    def get_daemon_status(self, pane_id: str) -> dict | None:
        """デーモンの状態を取得"""
        return self.daemon_status.get(pane_id)

    def get_all_daemon_status(self) -> dict:
        """全デーモンの状態を取得"""
        return {
            "daemons": self.daemon_status,
            "total_daemons": len(self.daemon_status),
            "running_daemons": len(
                [d for d in self.daemon_status.values() if d.get("status") == "running"]
            ),
            "total_commands": sum(
                d.get("command_count", 0) for d in self.daemon_status.values()
            ),
            "total_errors": sum(
                d.get("error_count", 0) for d in self.daemon_status.values()
            ),
        }

    async def health_check(self, pane_id: str) -> dict:
        """デーモンの健康状態をチェック"""
        if not self._is_daemon_running(pane_id):
            return {"healthy": False, "reason": "Daemon not running"}

        try:
            # 簡単なpingコマンドを送信
            result = await self.send_command(pane_id, "echo 'ping'", timeout=5)

            if result["success"]:
                return {
                    "healthy": True,
                    "response_time": time.time() - result["timestamp"],
                    "last_command_count": self.daemon_status[pane_id]["command_count"],
                }
            else:
                return {
                    "healthy": False,
                    "reason": result.get("error", "Unknown error"),
                }

        except Exception as e:
            return {"healthy": False, "reason": str(e)}

    async def start_all_daemons(self, pane_ids: list[str]) -> dict[str, bool]:
        """複数のpaneでデーモンを一括起動"""
        results = {}

        for pane_id in pane_ids:
            self.logger.info(f"Starting daemon in pane: {pane_id}")
            results[pane_id] = await self.start_daemon(pane_id)

            # 次のデーモン起動前に少し待機
            await asyncio.sleep(3)

        return results

    async def stop_all_daemons(self) -> dict[str, bool]:
        """全デーモンを停止"""
        results = {}

        for pane_id in list(self.daemon_status.keys()):
            results[pane_id] = await self.stop_daemon(pane_id)

        return results

    async def periodic_health_check(self) -> None:
        """定期的な健康状態チェック"""
        while True:
            try:
                for pane_id in list(self.daemon_status.keys()):
                    if self._is_daemon_running(pane_id):
                        health = await self.health_check(pane_id)
                        if not health["healthy"]:
                            self.logger.warning(
                                f"Daemon unhealthy in pane {pane_id}: {health['reason']}"
                            )
                            # 必要に応じて再起動
                            await self.restart_daemon(pane_id)

                await asyncio.sleep(self.config["heartbeat_interval"])

            except Exception as e:
                self.logger.error(f"Error in periodic health check: {e}")
                await asyncio.sleep(30)


class ClaudeCommandBuilder:
    """Claude Codeコマンド構築ヘルパー"""

    @staticmethod
    def create_file_read_command(file_path: str) -> str:
        """ファイル読み込みコマンド"""
        return f"Please read the file: {file_path}"

    @staticmethod
    def create_file_write_command(file_path: str, content: str) -> str:
        """ファイル書き込みコマンド"""
        return f"Please write to file {file_path}:\n\n{content}"

    @staticmethod
    def create_code_analysis_command(code_path: str) -> str:
        """コード分析コマンド"""
        return f"Please analyze the code in: {code_path}"

    @staticmethod
    def create_test_execution_command(test_path: str) -> str:
        """テスト実行コマンド"""
        return f"Please run tests in: {test_path}"

    @staticmethod
    def create_refactoring_command(target_path: str, instructions: str) -> str:
        """リファクタリングコマンド"""
        return f"Please refactor the code in {target_path} with the following instructions:\n\n{instructions}"
