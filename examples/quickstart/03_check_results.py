#!/usr/bin/env python3
"""
Hive Quickstart - Results Check
クイックスタートガイド Step 3: 成果物の確認

このスクリプトは新しいターミナルで実行してください
"""

import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from comb import CombAPI  # noqa: E402


def check_comb_system() -> bool:
    """Combシステムの状態確認"""
    print("🔍 Comb通信システムの状態確認中...")

    try:
        # テスト用APIで状態確認
        checker = CombAPI("quickstart-checker")
        status = checker.get_status()

        print("✅ Combシステム正常動作中")
        print(f"   Worker ID: {status['worker_id']}")
        print(f"   Timestamp: {status['timestamp']}")

        if "messages" in status:
            msg_stats = status["messages"]
            print(f"   送信済みメッセージ: {msg_stats.get('sent', 0)}件")

        return True
    except Exception as e:
        print(f"❌ Combシステム確認エラー: {e}")
        return False


def check_work_logs() -> bool:
    """作業ログの確認"""
    print("\n📋 作業ログの確認中...")

    work_logs_dir = Path(".hive/work_logs")

    if not work_logs_dir.exists():
        print("❌ 作業ログディレクトリが見つかりません")
        return False

    # 日次ログ確認
    daily_dir = work_logs_dir / "daily"
    daily_logs = list(daily_dir.glob("*.md")) if daily_dir.exists() else []
    print(f"📅 日次ログ: {len(daily_logs)}件")

    for log_file in daily_logs[:3]:  # 最新3件まで表示
        print(f"   - {log_file.name}")

    # プロジェクトログ確認
    projects_dir = work_logs_dir / "projects"
    project_logs = list(projects_dir.glob("*.md")) if projects_dir.exists() else []
    print(f"📊 プロジェクトログ: {len(project_logs)}件")

    for log_file in project_logs[:3]:  # 最新3件まで表示
        print(f"   - {log_file.name}")

    return len(daily_logs) > 0 or len(project_logs) > 0


def check_messages() -> bool:
    """メッセージファイルの確認"""
    print("\n📬 メッセージファイルの確認中...")

    messages_dir = Path(".hive/comb/messages")

    if not messages_dir.exists():
        print("❌ メッセージディレクトリが見つかりません")
        return False

    # 各種メッセージフォルダの確認
    folders = ["inbox", "outbox", "sent", "failed"]
    total_messages = 0

    for folder in folders:
        folder_path = messages_dir / folder
        if folder_path.exists():
            message_files = list(folder_path.glob("*.json"))
            count = len(message_files)
            total_messages += count
            print(f"   {folder}: {count}件")
        else:
            print(f"   {folder}: フォルダなし")

    print(f"📊 総メッセージ数: {total_messages}件")
    return total_messages > 0


def check_communication_logs() -> bool:
    """通信ログ（Markdown）の確認"""
    print("\n📝 通信ログ（Markdown）の確認中...")

    comm_logs_dir = Path(".hive/comb/communication_logs")

    if not comm_logs_dir.exists():
        print("❌ 通信ログディレクトリが見つかりません")
        return False

    # 今日の日付のフォルダを確認
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    today_dir = comm_logs_dir / today

    if today_dir.exists():
        log_files = list(today_dir.glob("*.md"))
        print(f"📅 本日の通信ログ: {len(log_files)}件")

        for log_file in log_files:
            print(f"   - {log_file.name}")

        return len(log_files) > 0
    else:
        print(f"📅 本日（{today}）の通信ログはまだありません")
        return False


def show_next_steps() -> None:
    """次のステップの案内"""
    print("\n🎯 次のステップ:")
    print("1. 📖 詳細なドキュメントを確認:")
    print("   - docs/comb-api.md - Comb API詳細仕様")
    print("   - docs/setup-guide.md - 詳細セットアップガイド")
    print("")
    print("2. 🚀 実際のプロジェクトを試す:")
    print("   - examples/web-app-hive/ - Webアプリ開発例")
    print("   - examples/api-development-hive/ - API開発例")
    print("")
    print("3. 🔧 Hive管理コマンド:")
    print("   - ./scripts/check-comb.sh --verbose - 詳細診断")
    print("   - ./scripts/collect-honey.sh - 成果物収集")
    print("   - ./scripts/shutdown-hive.sh - Hive終了")
    print("")
    print("🍯 Hiveでの開発を楽しんでください！")


def main() -> None:
    """メイン実行関数"""
    print("🐝 Hive Quickstart - Results Check")
    print("=" * 50)

    # 各種確認を実行
    checks = [
        ("Combシステム", check_comb_system),
        ("作業ログ", check_work_logs),
        ("メッセージファイル", check_messages),
        ("通信ログ", check_communication_logs),
    ]

    passed_checks = 0
    total_checks = len(checks)

    for _check_name, check_func in checks:
        if check_func():
            passed_checks += 1

    print("\n" + "=" * 50)
    print(f"📊 確認結果: {passed_checks}/{total_checks} 項目が正常")

    if passed_checks == total_checks:
        print("🎉 すべての確認が完了しました！")
        print("Hiveの基本機能が正常に動作しています。")
    elif passed_checks > 0:
        print("⚠️ 一部の機能で問題があります。")
        print("トラブルシューティング:")
        print("  - ./scripts/check-comb.sh --verbose で詳細確認")
        print("  - ./scripts/start-small-hive.sh --force で再起動")
    else:
        print("❌ 重要な問題があります。")
        print("Hiveが正常に起動していない可能性があります。")
        print("  - tmux list-sessions でセッション確認")
        print("  - ./scripts/start-small-hive.sh で起動")

    show_next_steps()


if __name__ == "__main__":
    main()
