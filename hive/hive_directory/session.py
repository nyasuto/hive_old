"""
Session Manager

セッション管理機能を提供するモジュール
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SessionManager:
    """
    セッション管理を行うクラス
    """

    def __init__(self, hive_dir: Path):
        """
        Initialize SessionManager

        Args:
            hive_dir: .hive/ディレクトリのパス
        """
        self.hive_dir = hive_dir
        self.sessions_dir = hive_dir / "sessions"

    def create_session(self, session_name: str | None = None) -> str:
        """
        新しいセッションを作成

        Args:
            session_name: セッション名（指定しない場合は自動生成）

        Returns:
            str: 作成されたセッションID
        """
        try:
            # セッションIDを生成
            if session_name:
                session_id = (
                    f"{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            else:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # セッションディレクトリを作成
            session_dir = self.sessions_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            # セッション情報ファイルを作成
            session_info = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "workers": [],
                "files": {
                    "analysis": "analysis.md",
                    "design": "design.md",
                    "communication": "communication.log",
                },
            }

            session_info_path = session_dir / "session_info.json"
            session_info_path.write_text(
                json.dumps(session_info, indent=2), encoding="utf-8"
            )

            # 基本ファイルを作成
            self._create_session_files(session_dir)

            logger.info(f"Created new session: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise

    def _create_session_files(self, session_dir: Path) -> None:
        """
        セッションの基本ファイルを作成

        Args:
            session_dir: セッションディレクトリのパス
        """
        # analysis.md
        analysis_content = """# Analysis

## Problem Analysis

### Current Situation
-

### Key Issues
-

### Requirements
-

## Technical Analysis

### Architecture
-

### Dependencies
-

### Constraints
-

## Next Steps
-
"""

        analysis_path = session_dir / "analysis.md"
        analysis_path.write_text(analysis_content, encoding="utf-8")

        # design.md
        design_content = """# Design

## Solution Design

### Overview
-

### Architecture
-

### Components
-

## Implementation Plan

### Phase 1
-

### Phase 2
-

### Phase 3
-

## Testing Strategy
-

## Deployment Plan
-
"""

        design_path = session_dir / "design.md"
        design_path.write_text(design_content, encoding="utf-8")

        # communication.log
        communication_content = f"""# Communication Log

Session started at: {datetime.now().isoformat()}

## Worker Communications

"""

        communication_path = session_dir / "communication.log"
        communication_path.write_text(communication_content, encoding="utf-8")

        logger.debug(f"Created session files in {session_dir}")

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """
        セッション情報を取得

        Args:
            session_id: セッションID

        Returns:
            Optional[Dict[str, Any]]: セッション情報
        """
        try:
            session_dir = self.sessions_dir / session_id
            if not session_dir.exists():
                return None

            session_info_path = session_dir / "session_info.json"
            if not session_info_path.exists():
                return None

            session_info = json.loads(session_info_path.read_text(encoding="utf-8"))
            session_info["path"] = str(session_dir)

            return session_info

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def list_sessions(self) -> list[dict[str, Any]]:
        """
        セッション一覧を取得

        Returns:
            List[Dict[str, Any]]: セッション一覧
        """
        sessions = []

        try:
            if not self.sessions_dir.exists():
                return sessions

            for session_path in self.sessions_dir.iterdir():
                if session_path.is_dir():
                    session_info = self.get_session(session_path.name)
                    if session_info:
                        sessions.append(session_info)

            # 作成日時でソート
            sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        セッションを削除

        Args:
            session_id: セッションID

        Returns:
            bool: 削除成功の可否
        """
        try:
            session_dir = self.sessions_dir / session_id
            if not session_dir.exists():
                logger.warning(f"Session {session_id} not found")
                return False

            shutil.rmtree(session_dir)
            logger.info(f"Deleted session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def update_session_status(self, session_id: str, status: str) -> bool:
        """
        セッションステータスを更新

        Args:
            session_id: セッションID
            status: 新しいステータス

        Returns:
            bool: 更新成功の可否
        """
        try:
            session_dir = self.sessions_dir / session_id
            session_info_path = session_dir / "session_info.json"

            if not session_info_path.exists():
                logger.warning(f"Session info not found for {session_id}")
                return False

            session_info = json.loads(session_info_path.read_text(encoding="utf-8"))
            session_info["status"] = status
            session_info["updated_at"] = datetime.now().isoformat()

            session_info_path.write_text(
                json.dumps(session_info, indent=2), encoding="utf-8"
            )

            logger.debug(f"Updated session {session_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update session {session_id} status: {e}")
            return False

    def add_worker_to_session(
        self, session_id: str, worker_info: dict[str, Any]
    ) -> bool:
        """
        セッションにワーカーを追加

        Args:
            session_id: セッションID
            worker_info: ワーカー情報

        Returns:
            bool: 追加成功の可否
        """
        try:
            session_dir = self.sessions_dir / session_id
            session_info_path = session_dir / "session_info.json"

            if not session_info_path.exists():
                logger.warning(f"Session info not found for {session_id}")
                return False

            session_info = json.loads(session_info_path.read_text(encoding="utf-8"))

            # ワーカーが既に存在するかチェック
            worker_id = worker_info.get("worker_id")
            if worker_id:
                existing_worker = next(
                    (
                        w
                        for w in session_info["workers"]
                        if w.get("worker_id") == worker_id
                    ),
                    None,
                )
                if existing_worker:
                    # 既存のワーカー情報を更新
                    existing_worker.update(worker_info)
                else:
                    # 新しいワーカーを追加
                    session_info["workers"].append(worker_info)
            else:
                session_info["workers"].append(worker_info)

            session_info["updated_at"] = datetime.now().isoformat()

            session_info_path.write_text(
                json.dumps(session_info, indent=2), encoding="utf-8"
            )

            logger.debug(f"Added worker to session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add worker to session {session_id}: {e}")
            return False

    def get_session_file(self, session_id: str, file_type: str) -> Path | None:
        """
        セッションファイルのパスを取得

        Args:
            session_id: セッションID
            file_type: ファイルタイプ（analysis, design, communication）

        Returns:
            Optional[Path]: ファイルパス
        """
        try:
            session_dir = self.sessions_dir / session_id
            if not session_dir.exists():
                return None

            file_mapping = {
                "analysis": "analysis.md",
                "design": "design.md",
                "communication": "communication.log",
            }

            filename = file_mapping.get(file_type)
            if not filename:
                return None

            file_path = session_dir / filename
            return file_path if file_path.exists() else None

        except Exception as e:
            logger.error(f"Failed to get session file {session_id}/{file_type}: {e}")
            return None

    def write_session_file(self, session_id: str, file_type: str, content: str) -> bool:
        """
        セッションファイルに書き込み

        Args:
            session_id: セッションID
            file_type: ファイルタイプ
            content: 書き込む内容

        Returns:
            bool: 書き込み成功の可否
        """
        try:
            file_path = self.get_session_file(session_id, file_type)
            if not file_path:
                return False

            file_path.write_text(content, encoding="utf-8")
            logger.debug(f"Wrote to session file {session_id}/{file_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to write session file {session_id}/{file_type}: {e}")
            return False

    def append_session_file(
        self, session_id: str, file_type: str, content: str
    ) -> bool:
        """
        セッションファイルに追記

        Args:
            session_id: セッションID
            file_type: ファイルタイプ
            content: 追記する内容

        Returns:
            bool: 追記成功の可否
        """
        try:
            file_path = self.get_session_file(session_id, file_type)
            if not file_path:
                return False

            # 既存の内容を読み込み
            existing_content = (
                file_path.read_text(encoding="utf-8") if file_path.exists() else ""
            )

            # 新しい内容を追加
            updated_content = existing_content + "\n" + content

            file_path.write_text(updated_content, encoding="utf-8")
            logger.debug(f"Appended to session file {session_id}/{file_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to append session file {session_id}/{file_type}: {e}")
            return False

    def cleanup_old_sessions(self, older_than_days: int) -> None:
        """
        古いセッションを削除

        Args:
            older_than_days: 削除対象とする日数
        """
        try:
            if not self.sessions_dir.exists():
                return

            import time

            cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)

            for session_path in self.sessions_dir.iterdir():
                if session_path.is_dir():
                    try:
                        # セッション情報を読み込み
                        session_info_path = session_path / "session_info.json"
                        if session_info_path.exists():
                            session_info = json.loads(
                                session_info_path.read_text(encoding="utf-8")
                            )
                            created_at = session_info.get("created_at")

                            if created_at:
                                created_time = datetime.fromisoformat(
                                    created_at
                                ).timestamp()
                                if created_time < cutoff_time:
                                    shutil.rmtree(session_path)
                                    logger.debug(
                                        f"Deleted old session: {session_path.name}"
                                    )
                    except Exception as e:
                        logger.warning(
                            f"Failed to check session {session_path.name}: {e}"
                        )

        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
