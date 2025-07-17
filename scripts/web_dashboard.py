#!/usr/bin/env python3
"""
Hive Web Dashboard Launcher
Issue #132 - Phase 3A: Browser-based Real-time Dashboard

Webダッシュボードサーバーの起動・管理スクリプト
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_dependencies() -> bool:
    """必要な依存関係を確認"""
    print("🔍 Checking dependencies...")

    required_packages = ["fastapi", "uvicorn", "websockets", "pydantic"]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")

    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Install with: pip install fastapi uvicorn websockets pydantic")
        return False

    print("✅ All dependencies satisfied")
    return True


def check_hive_system() -> bool:
    """Hiveシステムの状態を確認"""
    print("🐝 Checking Hive system status...")

    # tmuxセッション確認
    try:
        result = subprocess.run(
            ["tmux", "has-session", "-t", "cozy-hive"], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("  ✅ Hive tmux session active")
            return True
        else:
            print("  ⚠️  Hive tmux session not found")
            print("  💡 Start with: ./scripts/start-cozy-hive.sh")
            return False

    except subprocess.SubprocessError:
        print("  ❌ tmux not available")
        return False


def start_dashboard_server(
    host: str = "0.0.0.0", port: int = 8000, reload: bool = True
) -> None:
    """ダッシュボードサーバーを起動"""
    dashboard_api_path = PROJECT_ROOT / "web" / "dashboard" / "api" / "dashboard_api.py"

    if not dashboard_api_path.exists():
        print(f"❌ Dashboard API not found: {dashboard_api_path}")
        return

    print("🚀 Starting Hive Dashboard Server...")
    print(
        f"📊 Dashboard URL: http://{host if host != '0.0.0.0' else 'localhost'}:{port}"
    )
    print(
        f"🔌 WebSocket URL: ws://{host if host != '0.0.0.0' else 'localhost'}:{port}/ws"
    )
    print(
        f"📡 API Documentation: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs"
    )
    print()

    # 環境変数設定
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    # uvicornでサーバー起動
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "dashboard_api:app",
        "--host",
        host,
        "--port",
        str(port),
        "--log-level",
        "info",
    ]

    if reload:
        cmd.append("--reload")

    try:
        # ディレクトリを変更してサーバー起動
        os.chdir(dashboard_api_path.parent)
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\n👋 Dashboard server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")


def check_port_availability(port: int) -> bool:
    """ポートの利用可能性を確認"""
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("localhost", port))
            return True
    except OSError:
        return False


def open_browser(url: str) -> None:
    """ブラウザでダッシュボードを開く"""
    import webbrowser

    try:
        print(f"🌐 Opening browser: {url}")
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️  Could not open browser: {e}")
        print(f"💡 Manually open: {url}")


def main() -> None:
    """メイン実行関数"""
    parser = argparse.ArgumentParser(
        description="🐝 Hive Web Dashboard Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Start dashboard with default settings
  %(prog)s --port 9000              # Start on custom port
  %(prog)s --host localhost         # Bind to localhost only
  %(prog)s --no-reload              # Disable auto-reload
  %(prog)s --no-browser             # Don't auto-open browser
  %(prog)s --check-only             # Only check dependencies and system
        """,
    )

    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument(
        "--no-browser", action="store_true", help="Don't auto-open browser"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Only check dependencies and system"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force start even if Hive system is not active",
    )

    args = parser.parse_args()

    print("🐝 Hive Web Dashboard Launcher")
    print("=" * 50)

    # 依存関係チェック
    if not check_dependencies():
        sys.exit(1)

    # Hiveシステムチェック
    hive_active = check_hive_system()

    if args.check_only:
        print("\n✅ All checks completed")
        sys.exit(0 if hive_active else 1)

    if not hive_active and not args.force:
        print("\n⚠️  Hive system is not active")
        print("💡 Start Hive system first: ./scripts/start-cozy-hive.sh")
        print("🔧 Or use --force to start dashboard anyway")
        sys.exit(1)

    # ポート利用可能性チェック
    if not check_port_availability(args.port):
        print(f"❌ Port {args.port} is already in use")
        print("💡 Try a different port with --port option")
        sys.exit(1)

    # ブラウザを開く（サーバー起動前に少し待機）
    if not args.no_browser:
        dashboard_url = (
            f"http://{'localhost' if args.host == '0.0.0.0' else args.host}:{args.port}"
        )

        # 非同期でブラウザを開く
        def delayed_browser_open() -> None:
            time.sleep(3)  # サーバー起動待機
            open_browser(dashboard_url)

        import threading

        browser_thread = threading.Thread(target=delayed_browser_open)
        browser_thread.daemon = True
        browser_thread.start()

    # ダッシュボードサーバー起動
    try:
        start_dashboard_server(
            host=args.host, port=args.port, reload=not args.no_reload
        )
    except KeyboardInterrupt:
        print("\n👋 Dashboard launcher terminated")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
