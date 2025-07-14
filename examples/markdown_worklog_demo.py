#!/usr/bin/env python3
"""
Hive Markdown通信ログ & 作業ログ デモンストレーション

Issue #25で実装されたMarkdown通信ログと作業ログ機能のデモ
"""

from datetime import datetime

from comb import create_worker_api


def markdown_worklog_demo() -> None:
    """Markdown通信ログと作業ログ機能のデモンストレーション"""
    print("🐝 Hive Markdown通信ログ & 作業ログ デモンストレーション")
    print("=" * 60)

    # Worker API作成
    queen_api = create_worker_api("queen")

    print("\n📝 1. 作業ログ機能のデモンストレーション")
    print("-" * 40)

    # タスク開始
    task_id = queen_api.start_task(
        task_title="Issue #25 - Markdown通信ログ & 作業ログ機能",
        task_type="feature",
        description="Worker間通信のMarkdown化と作業ログ機能を実装",
        issue_number=25,
        workers=["queen", "developer_worker"]
    )
    print(f"✅ タスク開始 (ID: {task_id})")

    # 進捗追加
    queen_api.add_progress(
        "Phase 1: Markdown通信ログ機能実装",
        "MarkdownLoggerクラスを実装し、通信ログを人間が読みやすい形式に変換"
    )
    print("📋 進捗追加: Phase 1完了")

    # 技術的決定記録
    queen_api.add_technical_decision(
        "循環インポート問題をTYPE_CHECKINGで解決",
        "message_routerとmarkdown_logger間の循環インポートを回避",
        ["forward references", "別モジュール分離"]
    )
    print("🔧 技術的決定記録: 循環インポート解決策")

    # 課題記録
    queen_api.add_challenge(
        "テストでの期待値の不一致",
        "実際の動作を確認してテストケースを修正"
    )
    print("🚧 課題記録: テスト修正")

    print("\n📡 2. Markdown通信ログのデモンストレーション")
    print("-" * 40)

    # 各種メッセージタイプの送信
    print("💬 各種メッセージタイプの送信...")

    # Ping/Pong
    queen_api.ping("developer_worker")
    print("  🏓 Ping送信 (queen → developer_worker)")

    # 通知
    queen_api.send_notification(
        "developer_worker",
        {"message": "Task progress update", "completion": "50%"},
        priority="high"
    )
    print("  📢 通知送信 (HIGH priority)")

    # エラー通知
    queen_api.send_error(
        "developer_worker",
        "Test error message",
        {"error_code": "TEST_001", "context": "demo"}
    )
    print("  ❌ エラー通知送信")

    # メトリクス追加
    queen_api.add_metrics({
        "lines_of_code": 1200,
        "test_coverage": "100%",
        "files_created": 3,
        "tests_passed": 28
    })
    print("📊 メトリクス追加: 実装統計")

    print("\n📄 3. ログファイル生成状況")
    print("-" * 40)

    # 現在のタスク情報表示
    current_task = queen_api.get_current_task()
    if current_task:
        print(f"🎯 現在のタスク: {current_task['title']}")
        print(f"   状態: {current_task['status']}")
        print(f"   進捗: {len(current_task['progress'])} items")
        print(f"   技術的決定: {len(current_task['technical_decisions'])} items")
        print(f"   課題: {len(current_task['challenges'])} items")

    # ステータス情報表示
    status = queen_api.get_status()
    print("\n📈 システム状況:")
    print(f"   通信ログファイル: {status['work_logs']['daily_logs']}")
    print(f"   プロジェクトログ: {status['work_logs']['project_logs']}")
    print(f"   ログサイズ: {status['work_logs']['total_size_kb']:.1f}KB")

    print("\n🗂️ 4. 日次サマリー生成")
    print("-" * 40)

    # 日次サマリー生成
    summary_success = queen_api.generate_daily_summary()
    if summary_success:
        print("✅ 日次サマリー生成完了")

        # 生成されたファイルの場所を表示
        today = datetime.now().strftime("%Y-%m-%d")
        print("\n📁 生成されたファイル (.hive/以下):")
        print(f"   📄 通信ログ: comb/communication_logs/{today}/queen_developer_worker.md")
        print(f"   📊 日次サマリー: comb/communication_logs/{today}/summary_{today}.md")
        print(f"   📝 作業ログ: work_logs/daily/{today}.md")
        print(f"   🎯 プロジェクトログ: work_logs/projects/issue-25-{task_id}.md")

    # タスク完了
    queen_api.complete_task("completed")
    print(f"\n🎉 タスク完了: {task_id}")

    print("\n✨ 5. 実際のログファイル例")
    print("-" * 40)

    # 実際のログファイル内容を少し表示
    try:
        from pathlib import Path

        # 通信ログの例
        comm_log_path = Path(".hive/comb/communication_logs") / today / "queen_developer_worker.md"
        if comm_log_path.exists():
            print("📡 通信ログ例 (最初の10行):")
            content = comm_log_path.read_text(encoding="utf-8")
            lines = content.split('\n')[:10]
            for line in lines:
                print(f"   {line}")
            print("   ...")

        # 作業ログの例
        work_log_path = Path(".hive/work_logs/projects") / f"issue-25-{task_id}.md"
        if work_log_path.exists():
            print("\n📝 作業ログ例 (ヘッダー部分):")
            content = work_log_path.read_text(encoding="utf-8")
            lines = content.split('\n')[:15]
            for line in lines:
                print(f"   {line}")
            print("   ...")

    except Exception as e:
        print(f"⚠️ ログファイル表示中にエラー: {e}")

    print("\n🎊 デモンストレーション完了！")
    print("=" * 60)
    print("🔍 生成されたファイルを確認してください:")
    print("   - .hive/comb/communication_logs/ (通信ログ)")
    print("   - .hive/work_logs/ (作業ログ)")
    print("📚 これらのファイルは人間とAIの両方が読みやすい形式です")


def show_file_examples() -> None:
    """生成されたファイルの実例を表示"""
    from pathlib import Path

    print("\n📂 生成されたファイルの実例:")
    print("=" * 50)

    try:
        hive_dir = Path(".hive")
        if not hive_dir.exists():
            print("⚠️ .hiveディレクトリが存在しません。先にデモを実行してください。")
            return

        # 通信ログディレクトリ
        comm_logs_dir = hive_dir / "comb" / "communication_logs"
        if comm_logs_dir.exists():
            print("📡 通信ログファイル:")
            for date_dir in sorted(comm_logs_dir.iterdir()):
                if date_dir.is_dir():
                    print(f"   📅 {date_dir.name}/")
                    for log_file in sorted(date_dir.glob("*.md")):
                        size_kb = log_file.stat().st_size / 1024
                        print(f"      📄 {log_file.name} ({size_kb:.1f}KB)")

        # 作業ログディレクトリ
        work_logs_dir = hive_dir / "work_logs"
        if work_logs_dir.exists():
            print("\n📝 作業ログファイル:")

            # 日次ログ
            daily_dir = work_logs_dir / "daily"
            if daily_dir.exists():
                print("   📅 日次ログ:")
                for log_file in sorted(daily_dir.glob("*.md")):
                    size_kb = log_file.stat().st_size / 1024
                    print(f"      📄 {log_file.name} ({size_kb:.1f}KB)")

            # プロジェクトログ
            projects_dir = work_logs_dir / "projects"
            if projects_dir.exists():
                print("   🎯 プロジェクトログ:")
                for log_file in sorted(projects_dir.glob("*.md")):
                    size_kb = log_file.stat().st_size / 1024
                    print(f"      📄 {log_file.name} ({size_kb:.1f}KB)")

    except Exception as e:
        print(f"❌ ファイル一覧表示中にエラー: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--show-files":
        show_file_examples()
    else:
        markdown_worklog_demo()
        print("\n💡 ヒント: 生成されたファイルの一覧を見るには:")
        print("   python3 examples/markdown_worklog_demo.py --show-files")

