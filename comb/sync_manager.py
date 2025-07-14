"""
Hive Comb Sync Manager - 同期管理システム

Worker間の同期、ロック管理、デッドロック防止機能を提供
"""

import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

from .file_handler import HiveFileHandler


@dataclass
class LockInfo:
    """ロック情報"""

    resource_name: str
    holder: str
    acquired_at: str
    expires_at: str
    lock_type: str = "exclusive"

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LockInfo":
        """辞書から復元"""
        return cls(**data)

    def is_expired(self) -> bool:
        """ロックが期限切れかチェック"""
        return datetime.now() > datetime.fromisoformat(self.expires_at)


class SyncManager:
    """Worker間同期管理"""

    def __init__(
        self,
        file_handler: HiveFileHandler | None = None,
        default_timeout: float = 30.0,
    ) -> None:
        """
        初期化

        Args:
            file_handler: ファイルハンドラー
            default_timeout: デフォルトタイムアウト（秒）
        """
        self.file_handler = file_handler or HiveFileHandler()
        self.default_timeout = default_timeout

        # 同期ディレクトリ
        self.sync_dir = self.file_handler.get_path("comb", "shared")
        self.locks_dir = self.sync_dir / "locks"
        self.barriers_dir = self.sync_dir / "barriers"
        self.semaphores_dir = self.sync_dir / "semaphores"

        # ディレクトリ作成
        for directory in [self.locks_dir, self.barriers_dir, self.semaphores_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # ローカルロック（デッドロック防止用）
        self._local_locks: set[str] = set()
        self._local_lock = threading.Lock()

    def acquire_lock(
        self, resource_name: str, worker_id: str, timeout: float | None = None
    ) -> bool:
        """
        排他ロック取得

        Args:
            resource_name: リソース名
            worker_id: Worker ID
            timeout: タイムアウト（秒）

        Returns:
            ロック取得成功時True
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()
        lock_file = self.locks_dir / f"{resource_name}.lock"

        # デッドロック防止：既に保持しているリソースはスキップ
        with self._local_lock:
            if resource_name in self._local_locks:
                return True

        while time.time() - start_time < timeout:
            try:
                # 既存ロック確認
                existing_lock = self.file_handler.read_json(lock_file)

                if existing_lock:
                    lock_info = LockInfo.from_dict(existing_lock)

                    # 期限切れチェック
                    if lock_info.is_expired():
                        self.file_handler.delete_file(lock_file)
                    elif lock_info.holder == worker_id:
                        # 既に自分が保持している
                        with self._local_lock:
                            self._local_locks.add(resource_name)
                        return True
                    else:
                        # 他のWorkerが保持中
                        time.sleep(0.1)
                        continue

                # ロック取得試行
                now = datetime.now()
                expires_at = now + timedelta(seconds=timeout)

                lock_info = LockInfo(
                    resource_name=resource_name,
                    holder=worker_id,
                    acquired_at=now.isoformat(),
                    expires_at=expires_at.isoformat(),
                )

                # アトミックに書き込み試行
                if self.file_handler.write_json(lock_file, lock_info.to_dict()):
                    # 書き込み成功後、再度確認（競合状態チェック）
                    time.sleep(0.01)  # 短い待機

                    current_lock = self.file_handler.read_json(lock_file)
                    if (
                        current_lock
                        and LockInfo.from_dict(current_lock).holder == worker_id
                    ):
                        with self._local_lock:
                            self._local_locks.add(resource_name)
                        return True

                time.sleep(0.1)

            except Exception as e:
                print(f"Error acquiring lock {resource_name}: {e}")
                time.sleep(0.1)

        return False

    def release_lock(self, resource_name: str, worker_id: str) -> bool:
        """
        ロック解放

        Args:
            resource_name: リソース名
            worker_id: Worker ID

        Returns:
            解放成功時True
        """
        lock_file = self.locks_dir / f"{resource_name}.lock"

        try:
            existing_lock = self.file_handler.read_json(lock_file)

            if existing_lock:
                lock_info = LockInfo.from_dict(existing_lock)

                # 保持者確認
                if lock_info.holder == worker_id:
                    self.file_handler.delete_file(lock_file)

                    with self._local_lock:
                        self._local_locks.discard(resource_name)

                    return True
                else:
                    print(f"Lock {resource_name} not held by {worker_id}")
                    return False

            return True  # ロックが存在しない場合も成功とする

        except Exception as e:
            print(f"Error releasing lock {resource_name}: {e}")
            return False

    def is_locked(self, resource_name: str) -> bool:
        """
        リソースがロックされているかチェック

        Args:
            resource_name: リソース名

        Returns:
            ロックされている場合True
        """
        lock_file = self.locks_dir / f"{resource_name}.lock"

        try:
            existing_lock = self.file_handler.read_json(lock_file)

            if existing_lock:
                lock_info = LockInfo.from_dict(existing_lock)

                if lock_info.is_expired():
                    self.file_handler.delete_file(lock_file)
                    return False

                return True

            return False

        except Exception:
            return False

    def get_lock_holder(self, resource_name: str) -> str | None:
        """
        リソースのロック保持者を取得

        Args:
            resource_name: リソース名

        Returns:
            保持者のWorker ID、ロックされていない場合はNone
        """
        lock_file = self.locks_dir / f"{resource_name}.lock"

        try:
            existing_lock = self.file_handler.read_json(lock_file)

            if existing_lock:
                lock_info = LockInfo.from_dict(existing_lock)

                if lock_info.is_expired():
                    self.file_handler.delete_file(lock_file)
                    return None

                return lock_info.holder

            return None

        except Exception:
            return None

    def cleanup_expired_locks(self) -> int:
        """
        期限切れロックをクリーンアップ

        Returns:
            クリーンアップしたロック数
        """
        cleanup_count = 0

        try:
            lock_files = self.file_handler.list_files(self.locks_dir, "*.lock")

            for lock_file in lock_files:
                try:
                    lock_data = self.file_handler.read_json(lock_file)

                    if lock_data:
                        lock_info = LockInfo.from_dict(lock_data)

                        if lock_info.is_expired():
                            self.file_handler.delete_file(lock_file)
                            cleanup_count += 1

                            # ローカルロックからも削除
                            with self._local_lock:
                                self._local_locks.discard(lock_info.resource_name)
                    else:
                        # 空ファイルも削除
                        self.file_handler.delete_file(lock_file)
                        cleanup_count += 1

                except Exception as e:
                    print(f"Error cleaning lock file {lock_file}: {e}")

        except Exception as e:
            print(f"Error during lock cleanup: {e}")

        return cleanup_count

    def force_release_locks(self, worker_id: str) -> int:
        """
        指定Workerの全ロックを強制解放

        Args:
            worker_id: Worker ID

        Returns:
            解放したロック数
        """
        released_count = 0

        try:
            lock_files = self.file_handler.list_files(self.locks_dir, "*.lock")

            for lock_file in lock_files:
                try:
                    lock_data = self.file_handler.read_json(lock_file)

                    if lock_data:
                        lock_info = LockInfo.from_dict(lock_data)

                        if lock_info.holder == worker_id:
                            self.file_handler.delete_file(lock_file)
                            released_count += 1

                            # ローカルロックからも削除
                            with self._local_lock:
                                self._local_locks.discard(lock_info.resource_name)

                except Exception as e:
                    print(f"Error force releasing lock {lock_file}: {e}")

        except Exception as e:
            print(f"Error during force release: {e}")

        return released_count

    def create_barrier(self, barrier_name: str, expected_workers: int) -> bool:
        """
        バリア作成

        Args:
            barrier_name: バリア名
            expected_workers: 期待するWorker数

        Returns:
            作成成功時True
        """
        barrier_file = self.barriers_dir / f"{barrier_name}.barrier"

        barrier_data = {
            "name": barrier_name,
            "expected_workers": expected_workers,
            "arrived_workers": [],
            "created_at": datetime.now().isoformat(),
        }

        return self.file_handler.write_json(barrier_file, barrier_data)

    def wait_at_barrier(
        self, barrier_name: str, worker_id: str, timeout: float = 30.0
    ) -> bool:
        """
        バリアで待機

        Args:
            barrier_name: バリア名
            worker_id: Worker ID
            timeout: タイムアウト（秒）

        Returns:
            全Worker到着時True、タイムアウト時False
        """
        barrier_file = self.barriers_dir / f"{barrier_name}.barrier"
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                barrier_data = self.file_handler.read_json(barrier_file)

                if not barrier_data:
                    return False

                # 自分を到着リストに追加
                if worker_id not in barrier_data["arrived_workers"]:
                    barrier_data["arrived_workers"].append(worker_id)
                    self.file_handler.write_json(barrier_file, barrier_data)

                # 全Worker到着チェック
                if (
                    len(barrier_data["arrived_workers"])
                    >= barrier_data["expected_workers"]
                ):
                    return True

                time.sleep(0.1)

            except Exception as e:
                print(f"Error waiting at barrier {barrier_name}: {e}")
                time.sleep(0.1)

        return False

    def remove_barrier(self, barrier_name: str) -> bool:
        """
        バリア削除

        Args:
            barrier_name: バリア名

        Returns:
            削除成功時True
        """
        barrier_file = self.barriers_dir / f"{barrier_name}.barrier"
        return self.file_handler.delete_file(barrier_file)

    def get_lock_stats(self) -> dict[str, Any]:
        """
        ロック統計取得

        Returns:
            ロック統計情報
        """
        try:
            lock_files = self.file_handler.list_files(self.locks_dir, "*.lock")
            active_locks = []
            expired_locks = 0

            for lock_file in lock_files:
                try:
                    lock_data = self.file_handler.read_json(lock_file)
                    if lock_data:
                        lock_info = LockInfo.from_dict(lock_data)

                        if lock_info.is_expired():
                            expired_locks += 1
                        else:
                            active_locks.append(
                                {
                                    "resource": lock_info.resource_name,
                                    "holder": lock_info.holder,
                                    "acquired_at": lock_info.acquired_at,
                                }
                            )
                except Exception:
                    continue

            return {
                "active_locks": len(active_locks),
                "expired_locks": expired_locks,
                "locks": active_locks,
                "local_locks": len(self._local_locks),
            }

        except Exception as e:
            print(f"Error getting lock stats: {e}")
            return {
                "active_locks": 0,
                "expired_locks": 0,
                "locks": [],
                "local_locks": 0,
            }


# モジュールレベルのデフォルトインスタンス
default_sync_manager = SyncManager()
