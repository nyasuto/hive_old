"""
Cache Manager

ワーカー間共有キャッシュ管理機能を提供するモジュール
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CacheManager:
    """
    キャッシュ管理を行うクラス
    """

    def __init__(self, hive_dir: Path):
        """
        Initialize CacheManager

        Args:
            hive_dir: .hive/ディレクトリのパス
        """
        self.hive_dir = hive_dir
        self.cache_dir = hive_dir / "cache"
        self.shared_cache_dir = self.cache_dir / "shared"
        self.worker_cache_dir = self.cache_dir / "worker"

        # キャッシュディレクトリを作成
        self.shared_cache_dir.mkdir(parents=True, exist_ok=True)
        self.worker_cache_dir.mkdir(parents=True, exist_ok=True)

    def set_shared_cache(
        self, key: str, value: Any, expire_minutes: int | None = None
    ) -> bool:
        """
        共有キャッシュに値を設定

        Args:
            key: キャッシュキー
            value: 保存する値
            expire_minutes: 有効期限（分）

        Returns:
            bool: 設定成功の可否
        """
        try:
            cache_data = {
                "key": key,
                "value": value,
                "created_at": datetime.now().isoformat(),
                "expire_minutes": expire_minutes,
            }

            # 有効期限を設定
            if expire_minutes:
                expire_at = datetime.now().timestamp() + (expire_minutes * 60)
                cache_data["expire_at"] = expire_at

            # ファイルに保存
            cache_file = self.shared_cache_dir / f"{key}.json"
            cache_file.write_text(
                json.dumps(cache_data, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            logger.debug(f"Set shared cache: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to set shared cache {key}: {e}")
            return False

    def get_shared_cache(self, key: str) -> Any | None:
        """
        共有キャッシュから値を取得

        Args:
            key: キャッシュキー

        Returns:
            Optional[Any]: 取得した値
        """
        try:
            cache_file = self.shared_cache_dir / f"{key}.json"
            if not cache_file.exists():
                return None

            cache_data = json.loads(cache_file.read_text(encoding="utf-8"))

            # 有効期限をチェック
            if "expire_at" in cache_data:
                if datetime.now().timestamp() > cache_data["expire_at"]:
                    # 期限切れの場合は削除
                    cache_file.unlink()
                    logger.debug(f"Expired shared cache removed: {key}")
                    return None

            return cache_data.get("value")

        except Exception as e:
            logger.error(f"Failed to get shared cache {key}: {e}")
            return None

    def delete_shared_cache(self, key: str) -> bool:
        """
        共有キャッシュを削除

        Args:
            key: キャッシュキー

        Returns:
            bool: 削除成功の可否
        """
        try:
            cache_file = self.shared_cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Deleted shared cache: {key}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete shared cache {key}: {e}")
            return False

    def set_worker_cache(
        self, worker_id: str, key: str, value: Any, expire_minutes: int | None = None
    ) -> bool:
        """
        ワーカー専用キャッシュに値を設定

        Args:
            worker_id: ワーカーID
            key: キャッシュキー
            value: 保存する値
            expire_minutes: 有効期限（分）

        Returns:
            bool: 設定成功の可否
        """
        try:
            # ワーカー専用ディレクトリを作成
            worker_dir = self.worker_cache_dir / worker_id
            worker_dir.mkdir(parents=True, exist_ok=True)

            cache_data = {
                "key": key,
                "value": value,
                "worker_id": worker_id,
                "created_at": datetime.now().isoformat(),
                "expire_minutes": expire_minutes,
            }

            # 有効期限を設定
            if expire_minutes:
                expire_at = datetime.now().timestamp() + (expire_minutes * 60)
                cache_data["expire_at"] = expire_at

            # ファイルに保存
            cache_file = worker_dir / f"{key}.json"
            cache_file.write_text(
                json.dumps(cache_data, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            logger.debug(f"Set worker cache: {worker_id}/{key}")
            return True

        except Exception as e:
            logger.error(f"Failed to set worker cache {worker_id}/{key}: {e}")
            return False

    def get_worker_cache(self, worker_id: str, key: str) -> Any | None:
        """
        ワーカー専用キャッシュから値を取得

        Args:
            worker_id: ワーカーID
            key: キャッシュキー

        Returns:
            Optional[Any]: 取得した値
        """
        try:
            cache_file = self.worker_cache_dir / worker_id / f"{key}.json"
            if not cache_file.exists():
                return None

            cache_data = json.loads(cache_file.read_text(encoding="utf-8"))

            # 有効期限をチェック
            if "expire_at" in cache_data:
                if datetime.now().timestamp() > cache_data["expire_at"]:
                    # 期限切れの場合は削除
                    cache_file.unlink()
                    logger.debug(f"Expired worker cache removed: {worker_id}/{key}")
                    return None

            return cache_data.get("value")

        except Exception as e:
            logger.error(f"Failed to get worker cache {worker_id}/{key}: {e}")
            return None

    def delete_worker_cache(self, worker_id: str, key: str) -> bool:
        """
        ワーカー専用キャッシュを削除

        Args:
            worker_id: ワーカーID
            key: キャッシュキー

        Returns:
            bool: 削除成功の可否
        """
        try:
            cache_file = self.worker_cache_dir / worker_id / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Deleted worker cache: {worker_id}/{key}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete worker cache {worker_id}/{key}: {e}")
            return False

    def set_binary_cache(self, key: str, data: bytes, is_shared: bool = True) -> bool:
        """
        バイナリデータをキャッシュに保存

        Args:
            key: キャッシュキー
            data: バイナリデータ
            is_shared: 共有キャッシュかどうか

        Returns:
            bool: 保存成功の可否
        """
        try:
            cache_dir = self.shared_cache_dir if is_shared else self.worker_cache_dir
            cache_file = cache_dir / f"{key}.bin"

            # メタデータを作成
            metadata = {
                "key": key,
                "created_at": datetime.now().isoformat(),
                "size": len(data),
                "type": "binary",
            }

            # バイナリデータを保存
            cache_file.write_bytes(data)

            # メタデータを保存
            metadata_file = cache_dir / f"{key}.meta"
            metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

            logger.debug(f"Set binary cache: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to set binary cache {key}: {e}")
            return False

    def get_binary_cache(self, key: str, is_shared: bool = True) -> bytes | None:
        """
        バイナリデータをキャッシュから取得

        Args:
            key: キャッシュキー
            is_shared: 共有キャッシュかどうか

        Returns:
            Optional[bytes]: バイナリデータ
        """
        try:
            cache_dir = self.shared_cache_dir if is_shared else self.worker_cache_dir
            cache_file = cache_dir / f"{key}.bin"

            if not cache_file.exists():
                return None

            return cache_file.read_bytes()

        except Exception as e:
            logger.error(f"Failed to get binary cache {key}: {e}")
            return None

    def list_cache_files(self) -> dict[str, list[str]]:
        """
        キャッシュファイル一覧を取得

        Returns:
            Dict[str, List[str]]: キャッシュファイル一覧
        """
        cache_files = {"shared": [], "worker": {}}

        try:
            # 共有キャッシュファイル
            if self.shared_cache_dir.exists():
                for file_path in self.shared_cache_dir.glob("*.json"):
                    cache_files["shared"].append(file_path.stem)

            # ワーカー専用キャッシュファイル
            if self.worker_cache_dir.exists():
                for worker_dir in self.worker_cache_dir.iterdir():
                    if worker_dir.is_dir():
                        worker_files = []
                        for file_path in worker_dir.glob("*.json"):
                            worker_files.append(file_path.stem)
                        cache_files["worker"][worker_dir.name] = worker_files

        except Exception as e:
            logger.error(f"Failed to list cache files: {e}")

        return cache_files

    def cleanup_expired_cache(self) -> None:
        """
        期限切れのキャッシュファイルを削除
        """
        try:
            current_time = datetime.now().timestamp()

            # 共有キャッシュをチェック
            if self.shared_cache_dir.exists():
                for cache_file in self.shared_cache_dir.glob("*.json"):
                    try:
                        cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
                        if (
                            "expire_at" in cache_data
                            and current_time > cache_data["expire_at"]
                        ):
                            cache_file.unlink()
                            logger.debug(
                                f"Deleted expired shared cache: {cache_file.stem}"
                            )
                    except Exception:
                        pass

            # ワーカー専用キャッシュをチェック
            if self.worker_cache_dir.exists():
                for worker_dir in self.worker_cache_dir.iterdir():
                    if worker_dir.is_dir():
                        for cache_file in worker_dir.glob("*.json"):
                            try:
                                cache_data = json.loads(
                                    cache_file.read_text(encoding="utf-8")
                                )
                                if (
                                    "expire_at" in cache_data
                                    and current_time > cache_data["expire_at"]
                                ):
                                    cache_file.unlink()
                                    logger.debug(
                                        f"Deleted expired worker cache: {worker_dir.name}/{cache_file.stem}"
                                    )
                            except Exception:
                                pass

        except Exception as e:
            logger.error(f"Failed to cleanup expired cache: {e}")

    def cleanup_old_cache(self, older_than_days: int) -> None:
        """
        古いキャッシュファイルを削除

        Args:
            older_than_days: 削除対象とする日数
        """
        try:
            import time

            cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)

            # 共有キャッシュをチェック
            if self.shared_cache_dir.exists():
                for cache_file in self.shared_cache_dir.glob("*"):
                    try:
                        if cache_file.stat().st_mtime < cutoff_time:
                            cache_file.unlink()
                            logger.debug(f"Deleted old shared cache: {cache_file.name}")
                    except Exception:
                        pass

            # ワーカー専用キャッシュをチェック
            if self.worker_cache_dir.exists():
                for worker_dir in self.worker_cache_dir.iterdir():
                    if worker_dir.is_dir():
                        for cache_file in worker_dir.glob("*"):
                            try:
                                if cache_file.stat().st_mtime < cutoff_time:
                                    cache_file.unlink()
                                    logger.debug(
                                        f"Deleted old worker cache: {worker_dir.name}/{cache_file.name}"
                                    )
                            except Exception:
                                pass

                        # 空のワーカーディレクトリを削除
                        try:
                            if not any(worker_dir.iterdir()):
                                worker_dir.rmdir()
                                logger.debug(
                                    f"Deleted empty worker cache directory: {worker_dir.name}"
                                )
                        except Exception:
                            pass

        except Exception as e:
            logger.error(f"Failed to cleanup old cache: {e}")

    def clear_all_cache(self) -> bool:
        """
        すべてのキャッシュファイルを削除

        Returns:
            bool: 削除成功の可否
        """
        try:
            import shutil

            # 共有キャッシュを削除
            if self.shared_cache_dir.exists():
                shutil.rmtree(self.shared_cache_dir)
                self.shared_cache_dir.mkdir(parents=True, exist_ok=True)

            # ワーカー専用キャッシュを削除
            if self.worker_cache_dir.exists():
                shutil.rmtree(self.worker_cache_dir)
                self.worker_cache_dir.mkdir(parents=True, exist_ok=True)

            logger.info("Cleared all cache files")
            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
