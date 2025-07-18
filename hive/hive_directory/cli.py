"""
Hive Directory CLI

.hive/ディレクトリ操作のCLIインターフェース
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from .manager import HiveDirectoryManager

logger = logging.getLogger(__name__)


class HiveDirectoryCLI:
    """
    Hive Directory CLI クラス
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize CLI

        Args:
            project_root: プロジェクトルートディレクトリ
        """
        self.project_root = project_root or Path.cwd()
        self.hive_manager = HiveDirectoryManager(self.project_root)

    def run(self, args: list[str]) -> int:
        """
        CLI を実行

        Args:
            args: コマンドライン引数

        Returns:
            int: 終了コード
        """
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)

        # ログレベルを設定
        if parsed_args.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        try:
            # サブコマンドを実行
            return parsed_args.func(parsed_args)
        except Exception as e:
            logger.error(f"Error: {e}")
            return 1

    def _create_parser(self) -> argparse.ArgumentParser:
        """
        コマンドライン引数パーサーを作成

        Returns:
            argparse.ArgumentParser: パーサー
        """
        parser = argparse.ArgumentParser(
            description="Hive Directory Management CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose logging"
        )
        parser.add_argument(
            "--project-root", "-p", type=str, help="Project root directory"
        )

        # サブコマンドを作成
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # init コマンド
        init_parser = subparsers.add_parser("init", help="Initialize .hive directory")
        init_parser.add_argument(
            "--force",
            "-f",
            action="store_true",
            help="Force initialization (remove existing)",
        )
        init_parser.set_defaults(func=self._cmd_init)

        # status コマンド
        status_parser = subparsers.add_parser("status", help="Show directory status")
        status_parser.add_argument(
            "--json", action="store_true", help="Output in JSON format"
        )
        status_parser.set_defaults(func=self._cmd_status)

        # session コマンド
        session_parser = subparsers.add_parser("session", help="Session management")
        session_subparsers = session_parser.add_subparsers(dest="session_command")

        # session create
        session_create_parser = session_subparsers.add_parser(
            "create", help="Create new session"
        )
        session_create_parser.add_argument("name", nargs="?", help="Session name")
        session_create_parser.set_defaults(func=self._cmd_session_create)

        # session list
        session_list_parser = session_subparsers.add_parser(
            "list", help="List sessions"
        )
        session_list_parser.add_argument(
            "--json", action="store_true", help="Output in JSON format"
        )
        session_list_parser.set_defaults(func=self._cmd_session_list)

        # session delete
        session_delete_parser = session_subparsers.add_parser(
            "delete", help="Delete session"
        )
        session_delete_parser.add_argument("session_id", help="Session ID to delete")
        session_delete_parser.set_defaults(func=self._cmd_session_delete)

        # session show
        session_show_parser = session_subparsers.add_parser(
            "show", help="Show session details"
        )
        session_show_parser.add_argument("session_id", help="Session ID to show")
        session_show_parser.add_argument(
            "--json", action="store_true", help="Output in JSON format"
        )
        session_show_parser.set_defaults(func=self._cmd_session_show)

        # cache コマンド
        cache_parser = subparsers.add_parser("cache", help="Cache management")
        cache_subparsers = cache_parser.add_subparsers(dest="cache_command")

        # cache list
        cache_list_parser = cache_subparsers.add_parser("list", help="List cache files")
        cache_list_parser.add_argument(
            "--json", action="store_true", help="Output in JSON format"
        )
        cache_list_parser.set_defaults(func=self._cmd_cache_list)

        # cache clear
        cache_clear_parser = cache_subparsers.add_parser(
            "clear", help="Clear all cache"
        )
        cache_clear_parser.add_argument(
            "--confirm", action="store_true", help="Confirm cache clearing"
        )
        cache_clear_parser.set_defaults(func=self._cmd_cache_clear)

        # cache cleanup
        cache_cleanup_parser = cache_subparsers.add_parser(
            "cleanup", help="Cleanup old cache"
        )
        cache_cleanup_parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Delete cache older than days (default: 7)",
        )
        cache_cleanup_parser.set_defaults(func=self._cmd_cache_cleanup)

        # config コマンド
        config_parser = subparsers.add_parser("config", help="Configuration management")
        config_subparsers = config_parser.add_subparsers(dest="config_command")

        # config show
        config_show_parser = config_subparsers.add_parser(
            "show", help="Show configuration"
        )
        config_show_parser.add_argument(
            "config_type",
            choices=["main", "worker", "session"],
            help="Configuration type to show",
        )
        config_show_parser.add_argument(
            "--json", action="store_true", help="Output in JSON format"
        )
        config_show_parser.set_defaults(func=self._cmd_config_show)

        # config get
        config_get_parser = config_subparsers.add_parser(
            "get", help="Get configuration value"
        )
        config_get_parser.add_argument(
            "config_type",
            choices=["main", "worker", "session"],
            help="Configuration type",
        )
        config_get_parser.add_argument("key", help="Configuration key (dot notation)")
        config_get_parser.set_defaults(func=self._cmd_config_get)

        # config set
        config_set_parser = config_subparsers.add_parser(
            "set", help="Set configuration value"
        )
        config_set_parser.add_argument(
            "config_type",
            choices=["main", "worker", "session"],
            help="Configuration type",
        )
        config_set_parser.add_argument("key", help="Configuration key (dot notation)")
        config_set_parser.add_argument("value", help="Configuration value")
        config_set_parser.set_defaults(func=self._cmd_config_set)

        # cleanup コマンド
        cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup old files")
        cleanup_parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Delete files older than days (default: 7)",
        )
        cleanup_parser.add_argument(
            "--confirm", action="store_true", help="Confirm cleanup"
        )
        cleanup_parser.set_defaults(func=self._cmd_cleanup)

        # reset コマンド
        reset_parser = subparsers.add_parser("reset", help="Reset .hive directory")
        reset_parser.add_argument(
            "--confirm", action="store_true", help="Confirm reset"
        )
        reset_parser.set_defaults(func=self._cmd_reset)

        return parser

    def _cmd_init(self, args) -> int:
        """Initialize .hive directory"""
        try:
            success = self.hive_manager.initialize(force=args.force)
            if success:
                print("✓ Hive directory initialized successfully")
                print(f"  Location: {self.hive_manager.hive_dir}")
                return 0
            else:
                print("✗ Failed to initialize Hive directory")
                return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_status(self, args) -> int:
        """Show directory status"""
        try:
            status = self.hive_manager.status()

            if args.json:
                print(json.dumps(status, indent=2, ensure_ascii=False))
            else:
                self._print_status(status)

            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_session_create(self, args) -> int:
        """Create new session"""
        try:
            session_id = self.hive_manager.session_manager.create_session(args.name)
            print(f"✓ Created session: {session_id}")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_session_list(self, args) -> int:
        """List sessions"""
        try:
            sessions = self.hive_manager.session_manager.list_sessions()

            if args.json:
                print(json.dumps(sessions, indent=2, ensure_ascii=False))
            else:
                self._print_sessions(sessions)

            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_session_delete(self, args) -> int:
        """Delete session"""
        try:
            success = self.hive_manager.session_manager.delete_session(args.session_id)
            if success:
                print(f"✓ Deleted session: {args.session_id}")
                return 0
            else:
                print(f"✗ Failed to delete session: {args.session_id}")
                return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_session_show(self, args) -> int:
        """Show session details"""
        try:
            session = self.hive_manager.session_manager.get_session(args.session_id)

            if not session:
                print(f"✗ Session not found: {args.session_id}")
                return 1

            if args.json:
                print(json.dumps(session, indent=2, ensure_ascii=False))
            else:
                self._print_session_details(session)

            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_cache_list(self, args) -> int:
        """List cache files"""
        try:
            cache_files = self.hive_manager.cache_manager.list_cache_files()

            if args.json:
                print(json.dumps(cache_files, indent=2, ensure_ascii=False))
            else:
                self._print_cache_files(cache_files)

            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_cache_clear(self, args) -> int:
        """Clear all cache"""
        try:
            if not args.confirm:
                print("This will delete all cache files. Use --confirm to proceed.")
                return 1

            success = self.hive_manager.cache_manager.clear_all_cache()
            if success:
                print("✓ All cache files cleared")
                return 0
            else:
                print("✗ Failed to clear cache")
                return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_cache_cleanup(self, args) -> int:
        """Cleanup old cache"""
        try:
            self.hive_manager.cache_manager.cleanup_old_cache(args.days)
            print(f"✓ Cleaned up cache files older than {args.days} days")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_config_show(self, args) -> int:
        """Show configuration"""
        try:
            if args.config_type == "main":
                config = self.hive_manager.config_manager.get_main_config()
            elif args.config_type == "worker":
                config = self.hive_manager.config_manager.get_worker_config()
            elif args.config_type == "session":
                config = self.hive_manager.config_manager.get_session_config()
            else:
                print(f"Invalid config type: {args.config_type}")
                return 1

            if args.json:
                print(json.dumps(config, indent=2, ensure_ascii=False))
            else:
                self._print_config(config, args.config_type)

            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_config_get(self, args) -> int:
        """Get configuration value"""
        try:
            value = self.hive_manager.config_manager.get_config_value(
                args.config_type, args.key
            )

            if value is not None:
                print(json.dumps(value, ensure_ascii=False))
            else:
                print(f"Configuration key not found: {args.key}")
                return 1

            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_config_set(self, args) -> int:
        """Set configuration value"""
        try:
            # 値の型を推定
            value = self._parse_value(args.value)

            success = self.hive_manager.config_manager.set_config_value(
                args.config_type, args.key, value
            )

            if success:
                print(f"✓ Set {args.config_type}.{args.key} = {value}")
                return 0
            else:
                print("✗ Failed to set configuration")
                return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_cleanup(self, args) -> int:
        """Cleanup old files"""
        try:
            if not args.confirm:
                print(
                    f"This will delete files older than {args.days} days. Use --confirm to proceed."
                )
                return 1

            self.hive_manager.cleanup(args.days)
            print(f"✓ Cleaned up files older than {args.days} days")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_reset(self, args) -> int:
        """Reset .hive directory"""
        try:
            if not args.confirm:
                print(
                    "This will delete the entire .hive directory. Use --confirm to proceed."
                )
                return 1

            success = self.hive_manager.reset()
            if success:
                print("✓ Hive directory reset successfully")
                return 0
            else:
                print("✗ Failed to reset Hive directory")
                return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _print_status(self, status: dict[str, Any]) -> None:
        """Print status information"""
        print("=== Hive Directory Status ===")

        if status.get("initialized"):
            print(f"✓ Initialized: {status['path']}")
            print(f"  Size: {status['size']} bytes")
            print(f"  Sessions: {len(status['sessions'])}")
            print(
                f"  Cache files: {len(status['cache_files']['shared'])} shared, {len(status['cache_files']['worker'])} worker dirs"
            )
        else:
            print("✗ Not initialized")
            if "error" in status:
                print(f"  Error: {status['error']}")

    def _print_sessions(self, sessions: list[dict[str, Any]]) -> None:
        """Print sessions list"""
        print("=== Sessions ===")

        if not sessions:
            print("No sessions found")
            return

        for session in sessions:
            print(f"  {session['session_id']}")
            print(f"    Status: {session['status']}")
            print(f"    Created: {session['created_at']}")
            print(f"    Workers: {len(session['workers'])}")
            print()

    def _print_session_details(self, session: dict[str, Any]) -> None:
        """Print session details"""
        print(f"=== Session: {session['session_id']} ===")
        print(f"Status: {session['status']}")
        print(f"Created: {session['created_at']}")
        print(f"Path: {session['path']}")
        print(f"Workers: {len(session['workers'])}")

        if session["workers"]:
            print("\\nWorker Details:")
            for worker in session["workers"]:
                print(f"  - {worker.get('worker_id', 'Unknown')}")
                print(f"    Role: {worker.get('role', 'Unknown')}")
                print(f"    Status: {worker.get('status', 'Unknown')}")

    def _print_cache_files(self, cache_files: dict[str, Any]) -> None:
        """Print cache files"""
        print("=== Cache Files ===")

        print(f"Shared cache: {len(cache_files['shared'])} files")
        for file_name in cache_files["shared"]:
            print(f"  - {file_name}")

        print(f"\\nWorker cache: {len(cache_files['worker'])} workers")
        for worker_id, files in cache_files["worker"].items():
            print(f"  {worker_id}: {len(files)} files")
            for file_name in files:
                print(f"    - {file_name}")

    def _print_config(self, config: dict[str, Any], config_type: str) -> None:
        """Print configuration"""
        print(f"=== {config_type.title()} Configuration ===")
        self._print_dict(config, indent=0)

    def _print_dict(self, data: Any, indent: int = 0) -> None:
        """Print dictionary recursively"""
        if isinstance(data, dict):
            for key, value in data.items():
                print("  " * indent + f"{key}:")
                self._print_dict(value, indent + 1)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                print("  " * indent + f"[{i}]:")
                self._print_dict(item, indent + 1)
        else:
            print("  " * indent + str(data))

    def _parse_value(self, value_str: str) -> Any:
        """Parse value string to appropriate type"""
        # JSON として解析を試行
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            # 単純な文字列として返す
            return value_str


def main():
    """Main entry point"""
    cli = HiveDirectoryCLI()
    return cli.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
