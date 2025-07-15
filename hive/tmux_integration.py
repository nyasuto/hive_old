"""
Hive Tmux Integration Module
tmux session管理とWorker-paneマッピング機能
"""

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import libtmux
except ImportError:
    libtmux = None  # type: ignore


@dataclass
class PaneInfo:
    """tmux pane情報"""

    pane_id: str
    pane_index: int
    pane_title: str
    is_active: bool
    current_command: str


@dataclass
class WorkerPaneMapping:
    """Worker-pane マッピング情報"""

    worker_name: str
    pane_index: int
    pane_id: str | None = None
    title: str | None = None
    description: str | None = None
    is_active: bool = False


class HiveTmuxIntegration:
    """Hive tmux統合クラス"""

    def __init__(self, project_root: Path):
        """初期化"""
        self.project_root = project_root
        self.session_name = "hive"
        self.tmux_session: Any | None = None
        self.worker_mappings: dict[str, WorkerPaneMapping] = {}
        self._load_worker_mappings()

    def _load_worker_mappings(self) -> None:
        """Worker-paneマッピング設定を読み込み"""
        # プロジェクト固有の設定を優先
        project_config = self.project_root / ".hive" / "tmux" / "workers.json"
        template_config = self.project_root / "templates" / "tmux" / "workers.json"

        config_path = project_config if project_config.exists() else template_config

        if not config_path.exists():
            # デフォルト設定を作成
            self._create_default_mapping()
            return

        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)

            self.session_name = config.get("session", "hive")
            workers_config = config.get("workers", {})

            for worker_name, worker_config in workers_config.items():
                self.worker_mappings[worker_name] = WorkerPaneMapping(
                    worker_name=worker_name,
                    pane_index=worker_config["pane"],
                    title=worker_config.get("title"),
                    description=worker_config.get("description"),
                )
        except Exception as e:
            print(f"⚠️ Worker mapping設定の読み込みエラー: {e}")
            self._create_default_mapping()

    def _create_default_mapping(self) -> None:
        """デフォルトのWorker-paneマッピングを作成"""
        default_workers = [
            ("queen", 0, "Queen Worker"),
            ("architect", 1, "Architect Worker"),
            ("frontend", 2, "Frontend Worker"),
            ("backend", 3, "Backend Worker"),
            ("devops", 4, "DevOps Worker"),
            ("tester", 5, "Tester Worker"),
        ]

        for worker_name, pane_index, title in default_workers:
            self.worker_mappings[worker_name] = WorkerPaneMapping(
                worker_name=worker_name, pane_index=pane_index, title=title
            )

    def is_in_tmux(self) -> bool:
        """tmux環境内かどうか判定"""
        return "TMUX" in os.environ

    def get_hive_session(self) -> Any | None:
        """hive tmuxセッションを取得"""
        if not libtmux or not self.is_in_tmux():
            return None

        try:
            server = libtmux.Server()
            for session in server.sessions:
                if session.name == self.session_name:
                    self.tmux_session = session
                    return session
        except Exception:
            pass

        return None

    def get_all_panes(self) -> list[PaneInfo]:
        """全てのpane情報を取得"""
        panes: list[PaneInfo] = []

        session = self.get_hive_session()
        if not session:
            return panes

        try:
            for window in session.windows:
                for pane in window.panes:
                    pane_info = self._get_pane_info(pane)
                    if pane_info:
                        panes.append(pane_info)
        except Exception:
            pass

        return panes

    def _get_pane_info(self, pane: Any) -> PaneInfo | None:
        """paneの詳細情報を取得"""
        try:
            # tmux display-messageを使用してpane情報を取得
            result = subprocess.run(
                [
                    "tmux",
                    "display-message",
                    "-t",
                    pane.id,
                    "-p",
                    "#{pane_id}:#{pane_index}:#{pane_title}:#{pane_current_command}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                parts = result.stdout.strip().split(":")
                if len(parts) >= 4:
                    return PaneInfo(
                        pane_id=parts[0],
                        pane_index=int(parts[1]),
                        pane_title=parts[2],
                        is_active=pane.is_active(),
                        current_command=parts[3],
                    )
        except Exception:
            pass

        return None

    def update_worker_mappings(self) -> None:
        """Worker-paneマッピングを更新"""
        panes = self.get_all_panes()

        # 既存のマッピングをリセット
        for mapping in self.worker_mappings.values():
            mapping.pane_id = None
            mapping.is_active = False

        # pane情報を基にマッピングを更新
        for pane in panes:
            # pane indexでマッピング
            for _worker_name, mapping in self.worker_mappings.items():
                if mapping.pane_index == pane.pane_index:
                    mapping.pane_id = pane.pane_id
                    mapping.is_active = pane.is_active
                    break

            # pane titleでマッピング（フォールバック）
            if not any(
                m.pane_id == pane.pane_id for m in self.worker_mappings.values()
            ):
                for _worker_name, mapping in self.worker_mappings.items():
                    if (
                        mapping.title
                        and mapping.title.lower() in pane.pane_title.lower()
                    ):
                        mapping.pane_id = pane.pane_id
                        mapping.is_active = pane.is_active
                        break

    def get_worker_pane_id(self, worker_name: str) -> str | None:
        """指定されたworkerのpane IDを取得"""
        self.update_worker_mappings()

        mapping = self.worker_mappings.get(worker_name)
        if mapping:
            return mapping.pane_id

        return None

    def send_message_to_pane(
        self, recipient: str, message: str, priority: str = "normal"
    ) -> bool:
        """指定されたworkerのpaneにメッセージを送信"""
        if not self.is_in_tmux():
            return False

        pane_id = self.get_worker_pane_id(recipient)
        if not pane_id:
            return False

        try:
            # priorityに応じたプレフィックス
            prefix = "🚨 [緊急] " if priority == "urgent" else "📬 "

            # メッセージを構築
            cmd = f'echo "{prefix}→ {recipient}: {message}"'

            # tmux send-keysを使用してメッセージを送信
            result = subprocess.run(
                ["tmux", "send-keys", "-t", pane_id, cmd, "Enter"], check=False
            )

            return result.returncode == 0
        except Exception:
            return False

    def get_current_worker(self) -> str | None:
        """現在のpaneから対応するworkerを推定"""
        if not self.is_in_tmux():
            return None

        try:
            # 現在のpane情報を取得
            result = subprocess.run(
                ["tmux", "display-message", "-p", "#{pane_id}:#{pane_index}"],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                parts = result.stdout.strip().split(":")
                if len(parts) >= 2:
                    current_pane_id = parts[0]
                    current_pane_index = int(parts[1])

                    # マッピングを更新
                    self.update_worker_mappings()

                    # pane IDまたはindexで一致するworkerを探す
                    for worker_name, mapping in self.worker_mappings.items():
                        if (
                            mapping.pane_id == current_pane_id
                            or mapping.pane_index == current_pane_index
                        ):
                            return worker_name
        except Exception:
            pass

        return None

    def get_session_status(self) -> dict[str, Any]:
        """セッションの状態を取得"""
        status: dict[str, Any] = {
            "session_exists": False,
            "session_name": self.session_name,
            "in_tmux": self.is_in_tmux(),
            "workers": {},
            "unmapped_panes": [],
        }

        session = self.get_hive_session()
        if session:
            status["session_exists"] = True

            # Worker マッピング状態
            self.update_worker_mappings()
            for worker_name, mapping in self.worker_mappings.items():
                status["workers"][worker_name] = {
                    "pane_index": mapping.pane_index,
                    "pane_id": mapping.pane_id,
                    "is_active": mapping.is_active,
                    "title": mapping.title,
                    "mapped": mapping.pane_id is not None,
                }

            # マッピングされていないpane
            all_panes = self.get_all_panes()
            mapped_pane_ids = {
                m.pane_id for m in self.worker_mappings.values() if m.pane_id
            }

            for pane in all_panes:
                if pane.pane_id not in mapped_pane_ids:
                    status["unmapped_panes"].append(
                        {
                            "pane_id": pane.pane_id,
                            "pane_index": pane.pane_index,
                            "pane_title": pane.pane_title,
                            "current_command": pane.current_command,
                        }
                    )

        return status

    def save_current_mapping(self) -> None:
        """現在のマッピング状態を保存"""
        self.update_worker_mappings()

        # .hive/tmux ディレクトリを作成
        tmux_dir = self.project_root / ".hive" / "tmux"
        tmux_dir.mkdir(parents=True, exist_ok=True)

        # 現在のマッピング状態を保存
        config: dict[str, Any] = {
            "session": self.session_name,
            "description": "Auto-detected Hive Worker-Pane Mapping",
            "workers": {},
        }

        for worker_name, mapping in self.worker_mappings.items():
            config["workers"][worker_name] = {
                "pane": mapping.pane_index,
                "title": mapping.title or f"{worker_name.title()} Worker",
                "description": mapping.description or f"{worker_name} worker pane",
            }

        config_path = tmux_dir / "workers.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
