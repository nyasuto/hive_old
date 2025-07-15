"""
Hive CLI Core Implementation
CLIコマンドの実装とtmux統合
"""

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import libtmux
except ImportError:
    libtmux = None  # type: ignore


@dataclass
class WorkerInfo:
    """Worker情報"""

    name: str
    pane_id: str
    active: bool
    last_activity: datetime | None = None


@dataclass
class MessageInfo:
    """メッセージ情報"""

    from_worker: str
    to_worker: str
    message: str
    timestamp: datetime
    priority: str = "normal"  # normal, urgent
    message_type: str = "command"  # command, response, status


class HiveCLI:
    """Hive CLI コア機能"""

    VALID_WORKERS = ["queen", "architect", "frontend", "backend", "devops", "tester"]

    def __init__(self) -> None:
        """初期化"""
        self.project_root = Path(__file__).parent.parent
        self.current_worker = self._detect_current_worker()
        self.tmux_session = self._get_tmux_session()

    def _detect_current_worker(self) -> str:
        """現在のWorkerを検出"""
        # tmux pane名から判定
        if libtmux and self._is_in_tmux():
            try:
                current_pane = self._get_current_tmux_pane()
                if current_pane:
                    # pane名からworker名を抽出
                    pane_name = current_pane.get("pane_title", "")
                    for worker in self.VALID_WORKERS:
                        if worker in pane_name.lower():
                            return worker
            except Exception:
                pass

        # 環境変数から判定
        worker_from_env = os.environ.get("HIVE_WORKER_NAME")
        if worker_from_env in self.VALID_WORKERS:
            return worker_from_env

        # デフォルト
        return "unknown"

    def _is_in_tmux(self) -> bool:
        """tmux環境内かどうか判定"""
        return "TMUX" in os.environ

    def _get_tmux_session(self) -> Any | None:
        """tmuxセッションを取得"""
        if not libtmux or not self._is_in_tmux():
            return None

        try:
            server = libtmux.Server()
            # "hive"セッションを探す
            for session in server.sessions:
                if session.name == "hive":
                    return session
        except Exception:
            pass

        return None

    def _get_current_tmux_pane(self) -> dict[str, Any] | None:
        """現在のtmux paneを取得"""
        try:
            result = subprocess.run(
                [
                    "tmux",
                    "display-message",
                    "-p",
                    "-F",
                    "#{pane_id}:#{pane_title}:#{pane_current_command}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                parts = result.stdout.strip().split(":")
                if len(parts) >= 3:
                    return {
                        "pane_id": parts[0],
                        "pane_title": parts[1],
                        "current_command": parts[2],
                    }
        except Exception:
            pass

        return None

    def _get_all_workers(self) -> list[WorkerInfo]:
        """全Workerの情報を取得"""
        workers = []

        if not self.tmux_session:
            # tmuxなしの場合は仮想的なworker情報を返す
            for worker in self.VALID_WORKERS:
                workers.append(
                    WorkerInfo(
                        name=worker,
                        pane_id="virtual",
                        active=worker == self.current_worker,
                    )
                )
            return workers

        try:
            # tmuxセッション内のpaneを検索
            for window in self.tmux_session.windows:
                for pane in window.panes:
                    pane_info = pane.cmd(
                        "display-message",
                        "-p",
                        "-F",
                        "#{pane_title}:#{pane_current_command}",
                    )
                    if pane_info:
                        title_cmd = pane_info.split(":")
                        if len(title_cmd) >= 1:
                            title = title_cmd[0].lower()
                            for worker in self.VALID_WORKERS:
                                if worker in title:
                                    workers.append(
                                        WorkerInfo(
                                            name=worker,
                                            pane_id=pane.id,
                                            active=pane.is_active(),
                                        )
                                    )
                                    break
        except Exception:
            pass

        return workers

    def send_message(
        self, recipient: str, message: str, priority: str = "normal"
    ) -> None:
        """メッセージを送信"""
        if recipient not in self.VALID_WORKERS:
            raise ValueError(
                f"無効なWorker名: {recipient}. 有効な名前: {', '.join(self.VALID_WORKERS)}"
            )

        print(f"📤 {self.current_worker} → {recipient}: {message}")

        # メッセージをファイルに保存（旧Combシステムとの互換性）
        self._save_message_to_file(recipient, message, priority)

        # tmux paneにメッセージを送信
        self._send_to_tmux_pane(recipient, message, priority)

        print(f"✅ メッセージを {recipient} に送信しました")

    def who_am_i(self) -> None:
        """現在のWorkerを表示"""
        print(f"🐝 現在のWorker: {self.current_worker}")

        if self._is_in_tmux():
            pane_info = self._get_current_tmux_pane()
            if pane_info:
                print(
                    f"📍 tmux pane: {pane_info['pane_id']} ({pane_info['pane_title']})"
                )

        env_worker = os.environ.get("HIVE_WORKER_NAME")
        if env_worker:
            print(f"🌍 環境変数: HIVE_WORKER_NAME={env_worker}")

    def status(self) -> None:
        """Hiveの状態を表示"""
        print("🐝 Hive Status")
        print("=" * 50)

        # 基本情報
        print(f"📁 プロジェクトルート: {self.project_root}")
        print(f"🔄 現在のWorker: {self.current_worker}")
        print(f"🖥️  tmux環境: {'✅' if self._is_in_tmux() else '❌'}")

        # Workerの状態
        workers = self._get_all_workers()
        print(f"\n👥 Workers ({len(workers)}):")
        for worker in workers:
            status_icon = "🟢" if worker.active else "⚪"
            print(f"   {status_icon} {worker.name} (pane: {worker.pane_id})")

        # メッセージ統計
        self._show_message_statistics()

    def broadcast_message(self, message: str) -> None:
        """全Workerにメッセージを送信"""
        print(f"📢 {self.current_worker} が全Workerに送信: {message}")

        success_count = 0
        for worker in self.VALID_WORKERS:
            if worker != self.current_worker:  # 自分以外に送信
                try:
                    self._save_message_to_file(worker, message, "normal")
                    self._send_to_tmux_pane(worker, message, "normal")
                    success_count += 1
                except Exception as e:
                    print(f"⚠️ {worker} への送信に失敗: {e}")

        print(f"✅ {success_count} 人のWorkerに送信しました")

    def urgent_message(self, recipient: str, message: str) -> None:
        """緊急メッセージを送信"""
        print(f"🚨 緊急メッセージ: {self.current_worker} → {recipient}")
        self.send_message(recipient, message, priority="urgent")

    def _save_message_to_file(
        self, recipient: str, message: str, priority: str
    ) -> None:
        """メッセージをファイルに保存（旧Combシステムとの互換性）"""
        try:
            # メッセージディレクトリを作成
            messages_dir = self.project_root / ".hive" / "messages"
            messages_dir.mkdir(parents=True, exist_ok=True)

            # メッセージファイルを作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{self.current_worker}_to_{recipient}.json"
            filepath = messages_dir / filename

            message_data = {
                "from_worker": self.current_worker,
                "to_worker": recipient,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "priority": priority,
                "message_type": "command",
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(message_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠️ メッセージファイル保存エラー: {e}")

    def _send_to_tmux_pane(self, recipient: str, message: str, priority: str) -> None:
        """tmux paneにメッセージを送信"""
        if not self._is_in_tmux():
            return

        try:
            # priorityに応じたプレフィックス
            prefix = "🚨 [緊急] " if priority == "urgent" else "📬 "

            # tmux paneを探して送信
            workers = self._get_all_workers()
            for worker in workers:
                if worker.name == recipient and worker.pane_id != "virtual":
                    # コマンドを構築
                    cmd = (
                        f'echo "{prefix}{self.current_worker} → {recipient}: {message}"'
                    )

                    # tmux send-keys を使用
                    subprocess.run(
                        ["tmux", "send-keys", "-t", worker.pane_id, cmd, "Enter"],
                        check=False,
                    )
                    break

        except Exception as e:
            print(f"⚠️ tmux送信エラー: {e}")

    def _show_message_statistics(self) -> None:
        """メッセージ統計を表示"""
        try:
            messages_dir = self.project_root / ".hive" / "messages"
            if not messages_dir.exists():
                print("\n📊 メッセージ統計: メッセージなし")
                return

            message_files = list(messages_dir.glob("*.json"))
            if not message_files:
                print("\n📊 メッセージ統計: メッセージなし")
                return

            print(f"\n📊 メッセージ統計: {len(message_files)} 件")

            # 最新メッセージを表示
            latest_files = sorted(
                message_files, key=lambda f: f.stat().st_mtime, reverse=True
            )[:3]
            print("   最新メッセージ:")
            for file in latest_files:
                try:
                    with open(file, encoding="utf-8") as f:
                        data = json.load(f)
                        timestamp = datetime.fromisoformat(data["timestamp"]).strftime(
                            "%H:%M"
                        )
                        print(
                            f"   • {timestamp} {data['from_worker']} → {data['to_worker']}"
                        )
                except Exception:
                    pass

        except Exception as e:
            print(f"⚠️ 統計取得エラー: {e}")
