"""
Hive Directory Manager

.hive/ディレクトリ全体の管理を行うメインクラス
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Any

from .cache import CacheManager
from .config import ConfigManager
from .document_manager import DocumentManager
from .session import SessionManager

logger = logging.getLogger(__name__)


class HiveDirectoryManager:
    """
    .hive/ディレクトリ全体の管理を行うメインクラス
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize HiveDirectoryManager

        Args:
            project_root: プロジェクトルートディレクトリ（指定しない場合は現在のディレクトリ）
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.hive_dir = self.project_root / ".hive"

        # 各種マネージャーを初期化
        self.session_manager = SessionManager(self.hive_dir)
        self.cache_manager = CacheManager(self.hive_dir)
        self.config_manager = ConfigManager(self.hive_dir)
        self.document_manager = DocumentManager(self.hive_dir)

    def initialize(self, force: bool = False) -> bool:
        """
        .hive/ディレクトリを初期化

        Args:
            force: 既存のディレクトリを削除して再作成するかどうか

        Returns:
            bool: 初期化成功の可否
        """
        try:
            # 既存のディレクトリが存在する場合の処理
            if self.hive_dir.exists():
                if not force:
                    logger.warning(f".hive directory already exists at {self.hive_dir}")
                    return False
                else:
                    logger.info(f"Removing existing .hive directory at {self.hive_dir}")
                    shutil.rmtree(self.hive_dir)

            # ディレクトリ構造を作成
            self._create_directory_structure()

            # 初期設定ファイルを作成
            self._create_initial_files()

            # DocumentManagerのサブディレクトリを作成
            self.document_manager._initialize_subdirectories()

            # .gitignoreを更新
            self._update_gitignore()

            logger.info(f"Successfully initialized .hive directory at {self.hive_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize .hive directory: {e}")
            return False

    def _create_directory_structure(self) -> None:
        """
        基本的なディレクトリ構造を作成
        """
        directories = [
            "sessions",
            "templates",
            "cache",
            "config",
            "logs",
            "docs",
            "templates/roles",
            "templates/analysis",
            "templates/design",
            "cache/shared",
            "cache/worker",
        ]

        for directory in directories:
            dir_path = self.hive_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")

    def _create_initial_files(self) -> None:
        """
        初期設定ファイルを作成
        """
        # README.md
        readme_content = """# .hive Directory

This directory contains Hive system's local data and configuration.

## Structure

- `sessions/` - Session records and working files
- `templates/` - Templates for analysis, design, and roles
- `cache/` - Shared cache between workers
- `config/` - Local configuration files
- `logs/` - Local log files
- `docs/` - Generated documentation and reports

## Note

This directory is automatically managed by Hive system.
Do not manually edit files unless you know what you're doing.
"""

        readme_path = self.hive_dir / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")

        # 初期設定ファイル
        self.config_manager.create_default_config()

        logger.debug("Created initial files")

    def _update_gitignore(self) -> None:
        """
        .gitignoreを更新して.hive/ディレクトリを適切に管理
        """
        gitignore_path = self.project_root / ".gitignore"

        # 追加すべきエントリ
        hive_entries = [
            "",
            "# Hive System",
            ".hive/sessions/",
            ".hive/cache/",
            ".hive/logs/",
            "!.hive/templates/",
            "!.hive/config/",
            "!.hive/README.md",
        ]

        try:
            # 既存の.gitignoreの内容を読み込み
            if gitignore_path.exists():
                content = gitignore_path.read_text(encoding="utf-8")
            else:
                content = ""

            # Hive関連のエントリがすでに存在するかチェック
            if "# Hive System" in content:
                logger.debug(".gitignore already contains Hive entries")
                return

            # 新しいエントリを追加
            updated_content = content + "\n".join(hive_entries) + "\n"
            gitignore_path.write_text(updated_content, encoding="utf-8")

            logger.debug("Updated .gitignore with Hive entries")

        except Exception as e:
            logger.warning(f"Failed to update .gitignore: {e}")

    def status(self) -> dict[str, Any]:
        """
        .hive/ディレクトリの状態を取得

        Returns:
            Dict[str, Any]: 状態情報
        """
        if not self.hive_dir.exists():
            return {"initialized": False, "error": "Directory not found"}

        try:
            # 基本情報
            status_info = {
                "initialized": True,
                "path": str(self.hive_dir),
                "size": self._get_directory_size(),
                "sessions": self.session_manager.list_sessions(),
                "cache_files": self.cache_manager.list_cache_files(),
                "config": self.config_manager.get_config_summary(),
                "documents": self.document_manager.get_docs_summary(),
            }

            return status_info

        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {"initialized": False, "error": str(e)}

    def _get_directory_size(self) -> int:
        """
        ディレクトリサイズを取得

        Returns:
            int: バイト数
        """
        total_size = 0
        for dirpath, _dirnames, filenames in os.walk(self.hive_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass
        return total_size

    def cleanup(self, older_than_days: int = 7) -> None:
        """
        古いファイルをクリーンアップ

        Args:
            older_than_days: 削除対象とする日数
        """
        try:
            # 古いセッションを削除
            self.session_manager.cleanup_old_sessions(older_than_days)

            # 古いキャッシュファイルを削除
            self.cache_manager.cleanup_old_cache(older_than_days)

            # 古いドキュメントを削除
            self.document_manager.cleanup_old_documents(older_than_days)

            # 古いログファイルを削除
            self._cleanup_old_logs(older_than_days)

            logger.info(f"Cleaned up files older than {older_than_days} days")

        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")

    def _cleanup_old_logs(self, older_than_days: int) -> None:
        """
        古いログファイルを削除

        Args:
            older_than_days: 削除対象とする日数
        """
        logs_dir = self.hive_dir / "logs"
        if not logs_dir.exists():
            return

        import time

        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)

        for log_file in logs_dir.glob("*.log"):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    logger.debug(f"Deleted old log file: {log_file}")
            except OSError:
                pass

    def reset(self) -> bool:
        """
        .hive/ディレクトリをリセット（削除して再初期化）

        Returns:
            bool: リセット成功の可否
        """
        return self.initialize(force=True)
