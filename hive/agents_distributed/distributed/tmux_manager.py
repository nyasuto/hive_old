"""
Tmux統合基盤システム

分散エージェントアーキテクチャのためのtmux管理システム
BeeKeeper、Queen、Developer間の通信基盤を提供
"""

import json
import logging
import subprocess
import time


class TmuxManager:
    """tmuxセッション管理とpane間通信を担当するクラス"""

    def __init__(self, session_name: str = "hive"):
        self.session_name = session_name
        self.logger = logging.getLogger("tmux_manager")
        self.panes: dict[str, str] = {}  # pane_id -> window_name mapping
        self.session_exists = False

    def create_hive_session(self) -> bool:
        """Hive分散システム用のtmuxセッションを作成"""
        try:
            # 既存セッションをチェック
            if self._session_exists():
                self.logger.info(f"Session '{self.session_name}' already exists")
                self.session_exists = True
                return True

            # 新しいセッションを作成
            self.logger.info(f"Creating new tmux session: {self.session_name}")

            # BeeKeeperウィンドウでセッション作成
            result = subprocess.run(
                [
                    "tmux",
                    "new-session",
                    "-d",
                    "-s",
                    self.session_name,
                    "-n",
                    "beekeeper",
                    "-c",
                    "/Users/yast/git/hive",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.logger.error(f"Failed to create session: {result.stderr}")
                return False

            # Queenウィンドウを作成
            result = subprocess.run(
                [
                    "tmux",
                    "new-window",
                    "-t",
                    f"{self.session_name}:1",
                    "-n",
                    "queen",
                    "-c",
                    "/Users/yast/git/hive",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.logger.error(f"Failed to create queen window: {result.stderr}")
                return False

            # Developer1ウィンドウを作成
            result = subprocess.run(
                [
                    "tmux",
                    "new-window",
                    "-t",
                    f"{self.session_name}:2",
                    "-n",
                    "developer1",
                    "-c",
                    "/Users/yast/git/hive",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.logger.error(
                    f"Failed to create developer1 window: {result.stderr}"
                )
                return False

            # paneマッピングを設定
            self.panes = {
                "beekeeper": f"{self.session_name}:beekeeper",
                "queen": f"{self.session_name}:queen",
                "developer1": f"{self.session_name}:developer1",
            }

            self.session_exists = True
            self.logger.info("Hive distributed session created successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error creating tmux session: {e}")
            return False

    def send_to_pane(self, pane_id: str, message: str) -> bool:
        """指定されたpaneにメッセージを送信"""
        if not self.session_exists:
            self.logger.error("Session not initialized")
            return False

        if pane_id not in self.panes:
            self.logger.error(f"Unknown pane: {pane_id}")
            return False

        try:
            # メッセージをpaneに送信
            target_pane = self.panes[pane_id]
            self.logger.debug(f"Sending to {target_pane}: {message[:100]}...")

            # tmux send-keysを使用してメッセージを送信
            result = subprocess.run(
                ["tmux", "send-keys", "-t", target_pane, message, "C-m"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.logger.error(
                    f"Failed to send message to {pane_id}: {result.stderr}"
                )
                return False

            self.logger.debug(f"Message sent successfully to {pane_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error sending message to {pane_id}: {e}")
            return False

    def send_command_to_pane(self, pane_id: str, command: str) -> bool:
        """指定されたpaneにコマンドを送信（改行なし）"""
        if not self.session_exists:
            self.logger.error("Session not initialized")
            return False

        if pane_id not in self.panes:
            self.logger.error(f"Unknown pane: {pane_id}")
            return False

        try:
            target_pane = self.panes[pane_id]
            self.logger.debug(f"Sending command to {target_pane}: {command}")

            # コマンドを送信（改行なし）
            result = subprocess.run(
                ["tmux", "send-keys", "-t", target_pane, command],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.logger.error(
                    f"Failed to send command to {pane_id}: {result.stderr}"
                )
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error sending command to {pane_id}: {e}")
            return False

    def get_pane_content(self, pane_id: str, lines: int = 10) -> str | None:
        """指定されたpaneの内容を取得"""
        if not self.session_exists:
            self.logger.error("Session not initialized")
            return None

        if pane_id not in self.panes:
            self.logger.error(f"Unknown pane: {pane_id}")
            return None

        try:
            target_pane = self.panes[pane_id]

            # paneの内容を取得
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", target_pane, "-p", "-S", f"-{lines}"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.logger.error(
                    f"Failed to get pane content from {pane_id}: {result.stderr}"
                )
                return None

            return result.stdout

        except Exception as e:
            self.logger.error(f"Error getting pane content from {pane_id}: {e}")
            return None

    def create_message_file(self, pane_id: str, message: dict) -> bool:
        """一時ファイルを使用してメッセージを送信"""
        import os
        import tempfile

        try:
            # 一時ファイルを作成
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".json"
            ) as f:
                json.dump(message, f, indent=2, ensure_ascii=False)
                temp_file = f.name

            # ファイルパスをpaneに送信
            success = self.send_to_pane(pane_id, f"echo 'Message file: {temp_file}'")

            # 一時ファイルを削除
            os.unlink(temp_file)

            return success

        except Exception as e:
            self.logger.error(f"Error creating message file: {e}")
            return False

    def list_panes(self) -> list[str]:
        """利用可能なpaneのリストを返す"""
        return list(self.panes.keys())

    def get_pane_status(self, pane_id: str) -> dict | None:
        """指定されたpaneの状態を取得"""
        if not self.session_exists:
            return None

        if pane_id not in self.panes:
            return None

        try:
            target_pane = self.panes[pane_id]

            # paneの状態を取得
            result = subprocess.run(
                ["tmux", "display-message", "-t", target_pane, "-p", "#{pane_active}"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return None

            return {
                "pane_id": pane_id,
                "target": target_pane,
                "active": result.stdout.strip() == "1",
                "exists": True,
            }

        except Exception as e:
            self.logger.error(f"Error getting pane status: {e}")
            return None

    def destroy_session(self) -> bool:
        """tmuxセッションを終了"""
        if not self.session_exists:
            return True

        try:
            result = subprocess.run(
                ["tmux", "kill-session", "-t", self.session_name],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.logger.error(f"Failed to destroy session: {result.stderr}")
                return False

            self.session_exists = False
            self.panes.clear()
            self.logger.info(f"Session '{self.session_name}' destroyed")
            return True

        except Exception as e:
            self.logger.error(f"Error destroying session: {e}")
            return False

    def _session_exists(self) -> bool:
        """セッションが存在するかチェック"""
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", self.session_name],
                capture_output=True,
                text=True,
            )

            return result.returncode == 0

        except Exception:
            return False

    def get_session_status(self) -> dict:
        """セッション全体の状態を取得"""
        panes_status = {}
        for pane_id in self.panes:
            pane_status = self.get_pane_status(pane_id)
            panes_status[pane_id] = pane_status

        status = {
            "session_name": self.session_name,
            "exists": self.session_exists,
            "panes": panes_status,
        }

        return status


class PaneMessenger:
    """pane間通信を管理するクラス"""

    def __init__(self, tmux_manager: TmuxManager):
        self.tmux_manager = tmux_manager
        self.logger = logging.getLogger("pane_messenger")

    def send_structured_message(
        self, from_pane: str, to_pane: str, message_type: str, content: dict
    ) -> bool:
        """構造化されたメッセージを送信"""
        try:
            structured_msg = {
                "from": from_pane,
                "to": to_pane,
                "type": message_type,
                "timestamp": time.time(),
                "content": content,
            }

            # メッセージをJSON形式で送信
            json_msg = json.dumps(structured_msg, ensure_ascii=False)

            # メッセージヘッダーを追加
            formatted_msg = f"HIVE_MESSAGE:{json_msg}"

            return self.tmux_manager.send_to_pane(to_pane, formatted_msg)

        except Exception as e:
            self.logger.error(f"Error sending structured message: {e}")
            return False

    def send_task_message(
        self, from_pane: str, to_pane: str, task_id: str, task_data: dict
    ) -> bool:
        """タスクメッセージを送信"""
        return self.send_structured_message(
            from_pane,
            to_pane,
            "task_assignment",
            {"task_id": task_id, "task_data": task_data},
        )

    def send_response_message(
        self, from_pane: str, to_pane: str, task_id: str, response_data: dict
    ) -> bool:
        """応答メッセージを送信"""
        return self.send_structured_message(
            from_pane,
            to_pane,
            "task_response",
            {"task_id": task_id, "response_data": response_data},
        )

    def send_heartbeat(self, from_pane: str, to_pane: str) -> bool:
        """ハートビートメッセージを送信"""
        return self.send_structured_message(
            from_pane, to_pane, "heartbeat", {"status": "alive"}
        )
