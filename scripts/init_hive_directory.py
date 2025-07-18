#!/usr/bin/env python3
"""
Hive Directory Initialization Script

.hive/ディレクトリの初期化を行うスクリプト
"""

import argparse
import logging
import sys
from pathlib import Path

# プロジェクトのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from hive.hive_directory import HiveDirectoryManager


def setup_logging(verbose: bool = False):
    """
    ログ設定を初期化

    Args:
        verbose: 詳細ログを出力するかどうか
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main():
    """
    メイン関数
    """
    parser = argparse.ArgumentParser(description="Initialize Hive directory structure")
    parser.add_argument(
        "--project-root",
        "-p",
        type=str,
        default=None,
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force initialization (remove existing directory)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--status",
        "-s",
        action="store_true",
        help="Show current status instead of initializing",
    )

    args = parser.parse_args()

    # ログ設定
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # プロジェクトルートを決定
        project_root = Path(args.project_root) if args.project_root else Path.cwd()
        logger.info(f"Project root: {project_root}")

        # HiveDirectoryManagerを初期化
        hive_manager = HiveDirectoryManager(project_root)

        if args.status:
            # ステータス表示
            print("\\n=== Hive Directory Status ===")
            status = hive_manager.status()

            if status.get("initialized"):
                print(f"✓ Initialized: {status['path']}")
                print(f"  Size: {status['size']} bytes")
                print(f"  Sessions: {len(status['sessions'])}")
                print(
                    f"  Cache files: {len(status['cache_files']['shared'])} shared, {len(status['cache_files']['worker'])} worker directories"
                )

                # セッション一覧
                if status["sessions"]:
                    print("\\n  Active Sessions:")
                    for session in status["sessions"][:5]:  # 最新5個まで表示
                        print(f"    - {session['session_id']} ({session['status']})")
                    if len(status["sessions"]) > 5:
                        print(f"    ... and {len(status['sessions']) - 5} more")

                # 設定概要
                config_summary = status.get("config", {})
                print("\\n  Configuration:")
                print(
                    f"    - Main config: {'✓' if config_summary.get('main_config', {}).get('exists') else '✗'}"
                )
                print(
                    f"    - Worker config: {'✓' if config_summary.get('worker_config', {}).get('exists') else '✗'}"
                )
                print(
                    f"    - Session config: {'✓' if config_summary.get('session_config', {}).get('exists') else '✗'}"
                )

            else:
                print("✗ Not initialized")
                if "error" in status:
                    print(f"  Error: {status['error']}")
        else:
            # 初期化実行
            print("\\n=== Initializing Hive Directory ===")

            if args.force:
                print("Force mode: Removing existing directory if present")

            success = hive_manager.initialize(force=args.force)

            if success:
                print("✓ Hive directory initialized successfully")
                print(f"  Location: {hive_manager.hive_dir}")

                # 作成されたディレクトリ構造を表示
                print("\\n  Created structure:")
                _print_directory_tree(hive_manager.hive_dir, "  ")

            else:
                print("✗ Failed to initialize Hive directory")
                if hive_manager.hive_dir.exists():
                    print("  Directory already exists. Use --force to overwrite.")
                sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


def _print_directory_tree(
    path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0
):
    """
    ディレクトリ構造を表示

    Args:
        path: 表示するパス
        prefix: 表示プレフィックス
        max_depth: 最大表示深度
        current_depth: 現在の深度
    """
    if current_depth >= max_depth:
        return

    try:
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))

        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item.name}")

            if item.is_dir() and not item.name.startswith("."):
                extension = "    " if is_last else "│   "
                _print_directory_tree(
                    item, prefix + extension, max_depth, current_depth + 1
                )

    except PermissionError:
        print(f"{prefix}└── [Permission Denied]")


if __name__ == "__main__":
    main()
