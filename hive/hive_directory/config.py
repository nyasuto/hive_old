"""
Config Manager

設定ファイル管理機能を提供するモジュール
"""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    設定ファイル管理を行うクラス
    """

    def __init__(self, hive_dir: Path):
        """
        Initialize ConfigManager

        Args:
            hive_dir: .hive/ディレクトリのパス
        """
        self.hive_dir = hive_dir
        self.config_dir = hive_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 設定ファイルのパス
        self.main_config_path = self.config_dir / "hive_config.yaml"
        self.worker_config_path = self.config_dir / "worker_config.yaml"
        self.session_config_path = self.config_dir / "session_config.yaml"

    def create_default_config(self) -> None:
        """
        デフォルト設定ファイルを作成
        """
        # メイン設定
        default_main_config = {
            "hive": {
                "version": "1.0.0",
                "project_name": "hive_project",
                "max_workers": 8,
                "session_timeout_minutes": 120,
                "log_level": "INFO",
                "cache_cleanup_days": 7,
            },
            "tmux": {
                "session_prefix": "hive",
                "window_prefix": "worker",
                "base_port": 8000,
            },
            "logging": {
                "enable_file_logging": True,
                "max_log_size_mb": 10,
                "log_rotation_count": 5,
                "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        }

        # ワーカー設定
        default_worker_config = {
            "workers": {
                "queen": {
                    "role": "coordinator",
                    "max_concurrent_tasks": 5,
                    "timeout_seconds": 300,
                    "retry_count": 3,
                },
                "analyzer": {
                    "role": "analyzer",
                    "max_concurrent_tasks": 2,
                    "timeout_seconds": 180,
                    "retry_count": 2,
                },
                "developer": {
                    "role": "developer",
                    "max_concurrent_tasks": 3,
                    "timeout_seconds": 600,
                    "retry_count": 2,
                },
                "tester": {
                    "role": "tester",
                    "max_concurrent_tasks": 2,
                    "timeout_seconds": 300,
                    "retry_count": 2,
                },
                "reviewer": {
                    "role": "reviewer",
                    "max_concurrent_tasks": 2,
                    "timeout_seconds": 240,
                    "retry_count": 2,
                },
            },
            "communication": {
                "message_queue_size": 100,
                "heartbeat_interval_seconds": 30,
                "sync_interval_seconds": 10,
            },
        }

        # セッション設定
        default_session_config = {
            "session": {
                "auto_cleanup_enabled": True,
                "auto_cleanup_days": 30,
                "max_active_sessions": 10,
                "session_backup_enabled": True,
            },
            "files": {
                "auto_save_enabled": True,
                "auto_save_interval_seconds": 60,
                "backup_count": 3,
            },
            "templates": {
                "analysis_template": "analysis_template.md",
                "design_template": "design_template.md",
                "review_template": "review_template.md",
            },
        }

        # ファイルに保存
        try:
            self._save_config(self.main_config_path, default_main_config)
            self._save_config(self.worker_config_path, default_worker_config)
            self._save_config(self.session_config_path, default_session_config)

            logger.info("Created default configuration files")

        except Exception as e:
            logger.error(f"Failed to create default config files: {e}")

    def _save_config(self, file_path: Path, config: dict[str, Any]) -> None:
        """
        設定をファイルに保存

        Args:
            file_path: ファイルパス
            config: 設定データ
        """
        if file_path.suffix.lower() in [".yaml", ".yml"]:
            file_path.write_text(
                yaml.dump(config, default_flow_style=False, allow_unicode=True),
                encoding="utf-8",
            )
        else:
            file_path.write_text(
                json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
            )

    def _load_config(self, file_path: Path) -> dict[str, Any] | None:
        """
        設定ファイルを読み込み

        Args:
            file_path: ファイルパス

        Returns:
            Optional[Dict[str, Any]]: 設定データ
        """
        try:
            if not file_path.exists():
                return None

            content = file_path.read_text(encoding="utf-8")

            if file_path.suffix.lower() in [".yaml", ".yml"]:
                return yaml.safe_load(content)
            else:
                return json.loads(content)

        except Exception as e:
            logger.error(f"Failed to load config from {file_path}: {e}")
            return None

    def get_main_config(self) -> dict[str, Any]:
        """
        メイン設定を取得

        Returns:
            Dict[str, Any]: メイン設定
        """
        config = self._load_config(self.main_config_path)
        if config is None:
            logger.warning("Main config not found, creating default")
            self.create_default_config()
            config = self._load_config(self.main_config_path)
        return config or {}

    def get_worker_config(self) -> dict[str, Any]:
        """
        ワーカー設定を取得

        Returns:
            Dict[str, Any]: ワーカー設定
        """
        config = self._load_config(self.worker_config_path)
        if config is None:
            logger.warning("Worker config not found, creating default")
            self.create_default_config()
            config = self._load_config(self.worker_config_path)
        return config or {}

    def get_session_config(self) -> dict[str, Any]:
        """
        セッション設定を取得

        Returns:
            Dict[str, Any]: セッション設定
        """
        config = self._load_config(self.session_config_path)
        if config is None:
            logger.warning("Session config not found, creating default")
            self.create_default_config()
            config = self._load_config(self.session_config_path)
        return config or {}

    def update_main_config(self, updates: dict[str, Any]) -> bool:
        """
        メイン設定を更新

        Args:
            updates: 更新する設定

        Returns:
            bool: 更新成功の可否
        """
        try:
            config = self.get_main_config()
            self._deep_update(config, updates)
            self._save_config(self.main_config_path, config)
            logger.info("Updated main config")
            return True

        except Exception as e:
            logger.error(f"Failed to update main config: {e}")
            return False

    def update_worker_config(self, updates: dict[str, Any]) -> bool:
        """
        ワーカー設定を更新

        Args:
            updates: 更新する設定

        Returns:
            bool: 更新成功の可否
        """
        try:
            config = self.get_worker_config()
            self._deep_update(config, updates)
            self._save_config(self.worker_config_path, config)
            logger.info("Updated worker config")
            return True

        except Exception as e:
            logger.error(f"Failed to update worker config: {e}")
            return False

    def update_session_config(self, updates: dict[str, Any]) -> bool:
        """
        セッション設定を更新

        Args:
            updates: 更新する設定

        Returns:
            bool: 更新成功の可否
        """
        try:
            config = self.get_session_config()
            self._deep_update(config, updates)
            self._save_config(self.session_config_path, config)
            logger.info("Updated session config")
            return True

        except Exception as e:
            logger.error(f"Failed to update session config: {e}")
            return False

    def _deep_update(self, target: dict[str, Any], updates: dict[str, Any]) -> None:
        """
        辞書を深くマージ

        Args:
            target: 更新対象の辞書
            updates: 更新内容
        """
        for key, value in updates.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(target[key], value)
            else:
                target[key] = value

    def get_config_value(
        self, config_type: str, key_path: str, default: Any = None
    ) -> Any:
        """
        設定値を取得（ドット記法対応）

        Args:
            config_type: 設定タイプ（main, worker, session）
            key_path: キーパス（例: "hive.max_workers"）
            default: デフォルト値

        Returns:
            Any: 設定値
        """
        try:
            if config_type == "main":
                config = self.get_main_config()
            elif config_type == "worker":
                config = self.get_worker_config()
            elif config_type == "session":
                config = self.get_session_config()
            else:
                return default

            # ドット記法でキーを辿る
            keys = key_path.split(".")
            value = config

            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default

            return value

        except Exception as e:
            logger.error(f"Failed to get config value {config_type}.{key_path}: {e}")
            return default

    def set_config_value(self, config_type: str, key_path: str, value: Any) -> bool:
        """
        設定値を設定（ドット記法対応）

        Args:
            config_type: 設定タイプ（main, worker, session）
            key_path: キーパス（例: "hive.max_workers"）
            value: 設定値

        Returns:
            bool: 設定成功の可否
        """
        try:
            # キーパスを分解
            keys = key_path.split(".")
            updates = {}

            # ネストした辞書を作成
            current = updates
            for key in keys[:-1]:
                current[key] = {}
                current = current[key]
            current[keys[-1]] = value

            # 設定を更新
            if config_type == "main":
                return self.update_main_config(updates)
            elif config_type == "worker":
                return self.update_worker_config(updates)
            elif config_type == "session":
                return self.update_session_config(updates)
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to set config value {config_type}.{key_path}: {e}")
            return False

    def get_config_summary(self) -> dict[str, Any]:
        """
        設定の概要を取得

        Returns:
            Dict[str, Any]: 設定概要
        """
        try:
            summary = {
                "main_config": {
                    "exists": self.main_config_path.exists(),
                    "path": str(self.main_config_path),
                },
                "worker_config": {
                    "exists": self.worker_config_path.exists(),
                    "path": str(self.worker_config_path),
                },
                "session_config": {
                    "exists": self.session_config_path.exists(),
                    "path": str(self.session_config_path),
                },
            }

            # 主要な設定値を取得
            if summary["main_config"]["exists"]:
                main_config = self.get_main_config()
                summary["main_config"]["version"] = main_config.get("hive", {}).get(
                    "version"
                )
                summary["main_config"]["max_workers"] = main_config.get("hive", {}).get(
                    "max_workers"
                )

            if summary["worker_config"]["exists"]:
                worker_config = self.get_worker_config()
                summary["worker_config"]["worker_count"] = len(
                    worker_config.get("workers", {})
                )

            return summary

        except Exception as e:
            logger.error(f"Failed to get config summary: {e}")
            return {"error": str(e)}

    def validate_config(self) -> dict[str, list[str]]:
        """
        設定の妥当性を検証

        Returns:
            Dict[str, List[str]]: 検証結果（エラーリスト）
        """
        errors = {"main": [], "worker": [], "session": []}

        try:
            # メイン設定の検証
            main_config = self.get_main_config()
            if not main_config.get("hive", {}).get("version"):
                errors["main"].append("Version is required")

            max_workers = main_config.get("hive", {}).get("max_workers")
            if not isinstance(max_workers, int) or max_workers < 1:
                errors["main"].append("max_workers must be a positive integer")

            # ワーカー設定の検証
            worker_config = self.get_worker_config()
            workers = worker_config.get("workers", {})

            if not workers:
                errors["worker"].append("No workers configured")

            for worker_name, worker_info in workers.items():
                if not worker_info.get("role"):
                    errors["worker"].append(f"Worker {worker_name} has no role")

                max_tasks = worker_info.get("max_concurrent_tasks")
                if not isinstance(max_tasks, int) or max_tasks < 1:
                    errors["worker"].append(
                        f"Worker {worker_name} max_concurrent_tasks must be a positive integer"
                    )

            # セッション設定の検証
            session_config = self.get_session_config()
            auto_cleanup_days = session_config.get("session", {}).get(
                "auto_cleanup_days"
            )
            if not isinstance(auto_cleanup_days, int) or auto_cleanup_days < 1:
                errors["session"].append("auto_cleanup_days must be a positive integer")

        except Exception as e:
            errors["general"] = [f"Config validation failed: {e}"]

        return errors

    def backup_config(self) -> bool:
        """
        設定ファイルをバックアップ

        Returns:
            bool: バックアップ成功の可否
        """
        try:
            import shutil
            from datetime import datetime

            backup_dir = self.config_dir / "backup"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 各設定ファイルをバックアップ
            for config_file in [
                self.main_config_path,
                self.worker_config_path,
                self.session_config_path,
            ]:
                if config_file.exists():
                    backup_name = f"{config_file.stem}_{timestamp}{config_file.suffix}"
                    backup_path = backup_dir / backup_name
                    shutil.copy2(config_file, backup_path)
                    logger.debug(f"Backed up {config_file.name} to {backup_name}")

            logger.info(f"Configuration backed up to {backup_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to backup config: {e}")
            return False
