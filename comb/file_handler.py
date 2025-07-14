"""
Hive Comb File Handler - ファイル操作とディレクトリ管理

.hive/ディレクトリ構造の作成と管理、JSON読み書き、ファイルロック機能を提供
"""

import errno
import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional


class HiveFileHandler:
    """ファイル操作とディレクトリ管理を担当"""

    HIVE_DIR = ".hive"

    # ディレクトリ構造定義
    DIRECTORIES = {
        "nectar": ["pending", "active", "completed"],
        "comb": ["messages", "shared", "cells"],
        "honey": [],
        "logs": [],
    }

    def __init__(self, root_path: Optional[Path] = None) -> None:
        """
        初期化

        Args:
            root_path: Hiveプロジェクトのルートパス（デフォルト: 現在のディレクトリ）
        """
        self.root_path = Path(root_path) if root_path else Path.cwd()
        self.hive_path = self.root_path / self.HIVE_DIR

    def ensure_hive_structure(self) -> None:
        """
        .hive/ディレクトリ構造を作成（存在しない場合）

        Creates:
            .hive/
            ├── nectar/
            │   ├── pending/
            │   ├── active/
            │   └── completed/
            ├── comb/
            │   ├── messages/
            │   ├── shared/
            │   └── cells/
            ├── honey/
            └── logs/
        """
        # メインディレクトリ作成
        self.hive_path.mkdir(exist_ok=True)

        # サブディレクトリ作成
        for main_dir, sub_dirs in self.DIRECTORIES.items():
            main_path = self.hive_path / main_dir
            main_path.mkdir(exist_ok=True)

            for sub_dir in sub_dirs:
                sub_path = main_path / sub_dir
                sub_path.mkdir(exist_ok=True)

    def get_path(self, *path_parts: str) -> Path:
        """
        .hive/配下のパスを取得

        Args:
            *path_parts: パス要素（例: "nectar", "pending"）

        Returns:
            完全なファイルパス
        """
        return self.hive_path.joinpath(*path_parts)

    @contextmanager
    def file_lock(self, file_path: Path) -> Any:
        """
        ファイルロックのコンテキストマネージャー

        Args:
            file_path: ロックするファイルのパス

        Yields:
            ロックされたファイルハンドル
        """
        # ファイルが存在しない場合は作成
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "a+") as f:
            retry_count = 0
            max_retries = 10

            while retry_count < max_retries:
                try:
                    # 排他ロック取得を試行
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    yield f
                    break
                except OSError as e:
                    if e.errno == errno.EAGAIN or e.errno == errno.EACCES:
                        # ロック失敗、少し待ってリトライ
                        retry_count += 1
                        time.sleep(0.1 * retry_count)  # 指数バックオフ
                    else:
                        raise
            else:
                raise TimeoutError(f"Could not acquire lock for {file_path}")

    def write_json(self, file_path: Path, data: dict[str, Any]) -> bool:
        """
        JSONファイルの安全な書き込み

        Args:
            file_path: 書き込むファイルパス
            data: 書き込むデータ

        Returns:
            成功時True、失敗時False
        """
        try:
            with self.file_lock(file_path) as f:
                # ファイルの先頭に戻って内容をクリア
                f.seek(0)
                f.truncate()

                # JSONとして書き込み
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # 確実にディスクに書き込み

            return True
        except Exception as e:
            print(f"Error writing JSON to {file_path}: {e}")
            return False

    def read_json(self, file_path: Path) -> Optional[dict[str, Any]]:
        """
        JSONファイルの安全な読み込み

        Args:
            file_path: 読み込むファイルパス

        Returns:
            読み込んだデータ、失敗時はNone
        """
        if not file_path.exists():
            return None

        try:
            with self.file_lock(file_path) as f:
                f.seek(0)
                content = f.read()

                if not content.strip():
                    return None

                return json.loads(content)  # type: ignore[no-any-return]
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error reading JSON from {file_path}: {e}")
            return None

    def list_files(self, directory_path: Path, pattern: str = "*") -> list[Path]:
        """
        ディレクトリ内のファイル一覧取得

        Args:
            directory_path: 検索するディレクトリ
            pattern: ファイルパターン（デフォルト: "*"）

        Returns:
            ファイルパスのリスト
        """
        if not directory_path.exists():
            return []

        return list(directory_path.glob(pattern))

    def move_file(self, src: Path, dst: Path) -> bool:
        """
        ファイルの安全な移動

        Args:
            src: 移動元ファイルパス
            dst: 移動先ファイルパス

        Returns:
            成功時True、失敗時False
        """
        try:
            # 移動先ディレクトリを作成
            dst.parent.mkdir(parents=True, exist_ok=True)

            # ファイル移動
            src.rename(dst)
            return True
        except Exception as e:
            print(f"Error moving file from {src} to {dst}: {e}")
            return False

    def delete_file(self, file_path: Path) -> bool:
        """
        ファイルの安全な削除

        Args:
            file_path: 削除するファイルパス

        Returns:
            成功時True、失敗時False
        """
        try:
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False


# モジュールレベルのデフォルトインスタンス
default_handler = HiveFileHandler()
