"""
Test cases for Markdown communication logging and work log functionality
"""

import tempfile
import time
from datetime import datetime
from pathlib import Path

from comb import (
    CombAPI,
    MarkdownLogger,
    Message,
    MessagePriority,
    MessageType,
    WorkLogManager,
)
from comb.file_handler import HiveFileHandler


class TestMarkdownLogger:
    """Markdownログ機能のテストクラス"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.file_handler = HiveFileHandler(self.temp_dir)
        self.markdown_logger = MarkdownLogger(self.file_handler)

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_log_message_basic(self) -> None:
        """基本的なメッセージログテスト"""
        message = Message.create(
            from_worker="queen",
            to_worker="developer",
            message_type=MessageType.REQUEST,
            content={"action": "ping"},
            priority=MessagePriority.LOW
        )

        # ログ記録
        success = self.markdown_logger.log_message(message)
        assert success

        # ログファイルの存在確認
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.temp_dir / ".hive" / "comb" / "communication_logs" / today / "queen_developer.md"
        assert log_file.exists()

        # ログ内容確認
        content = log_file.read_text(encoding="utf-8")
        assert "# 🐝 Hive Communication Log" in content
        assert "## ❓ Request" in content
        assert "### queen → developer" in content
        assert "🏓 **Ping** - Health check request" in content

    def test_log_message_different_types(self) -> None:
        """異なるメッセージタイプのログテスト"""
        message_types = [
            (MessageType.REQUEST, "❓"),
            (MessageType.RESPONSE, "✅"),
            (MessageType.NOTIFICATION, "📢"),
            (MessageType.ERROR, "❌")
        ]

        for msg_type, emoji in message_types:
            message = Message.create(
                from_worker="queen",
                to_worker="developer",
                message_type=msg_type,
                content={"test": "data"},
                priority=MessagePriority.NORMAL
            )

            success = self.markdown_logger.log_message(message)
            assert success

            # ログファイル内容確認
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.temp_dir / ".hive" / "comb" / "communication_logs" / today / "queen_developer.md"
            content = log_file.read_text(encoding="utf-8")
            assert f"## {emoji} {msg_type.value.title()}" in content

    def test_log_message_priorities(self) -> None:
        """優先度別ログテスト"""
        priorities = [
            (MessagePriority.LOW, "🟢"),
            (MessagePriority.NORMAL, "🔵"),
            (MessagePriority.HIGH, "🟠"),
            (MessagePriority.URGENT, "🔴")
        ]

        for priority, emoji in priorities:
            message = Message.create(
                from_worker="queen",
                to_worker="developer",
                message_type=MessageType.REQUEST,
                content={"test": "data"},
                priority=priority
            )

            success = self.markdown_logger.log_message(message)
            assert success

            # ログファイル内容確認
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.temp_dir / ".hive" / "comb" / "communication_logs" / today / "queen_developer.md"
            content = log_file.read_text(encoding="utf-8")
            assert f"**Priority:** {emoji} {priority.name}" in content

    def test_generate_daily_summary(self) -> None:
        """日次サマリー生成テスト"""
        # 複数のメッセージをログ記録
        messages = [
            Message.create("queen", "developer", MessageType.REQUEST, {"action": "ping"}),
            Message.create("developer", "queen", MessageType.RESPONSE, {"action": "pong"}),
            Message.create("queen", "worker", MessageType.NOTIFICATION, {"status": "active"})
        ]

        for message in messages:
            self.markdown_logger.log_message(message)

        # サマリー生成
        success = self.markdown_logger.generate_daily_summary()
        assert success

        # サマリーファイル確認
        today = datetime.now().strftime("%Y-%m-%d")
        summary_file = self.temp_dir / ".hive" / "comb" / "communication_logs" / today / f"summary_{today}.md"
        assert summary_file.exists()

        content = summary_file.read_text(encoding="utf-8")
        assert "# 📊 Daily Communication Summary" in content
        assert "**Total Communication Files:** 3" in content
        assert "queen ↔ developer" in content
        assert "queen ↔ worker" in content

    def test_communication_stats(self) -> None:
        """通信統計取得テスト"""
        # メッセージをログ記録
        message = Message.create(
            "queen", "developer", MessageType.REQUEST, {"action": "ping"}
        )
        self.markdown_logger.log_message(message)

        # 統計取得
        stats = self.markdown_logger.get_communication_stats()

        assert stats["total_log_files"] == 1
        assert stats["total_size_kb"] > 0
        assert "queen_developer" in stats["worker_pairs"]
        assert stats["daily_directories"] == 1


class TestWorkLogManager:
    """作業ログ管理機能のテストクラス"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.file_handler = HiveFileHandler(self.temp_dir)
        self.work_log_manager = WorkLogManager(self.file_handler)

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_start_task(self) -> None:
        """タスク開始テスト"""
        task_id = self.work_log_manager.start_task(
            task_title="Test Task",
            task_type="feature",
            description="Test description",
            issue_number=25,
            workers=["queen", "developer"]
        )

        assert task_id is not None
        assert len(task_id) == 8  # UUID shortened to 8 chars

        # 現在のタスク確認
        current_task = self.work_log_manager.get_current_task()
        assert current_task is not None
        assert current_task["title"] == "Test Task"
        assert current_task["type"] == "feature"
        assert current_task["issue_number"] == 25
        assert current_task["status"] == "in_progress"

        # プロジェクトログファイル確認
        project_file = self.temp_dir / ".hive" / "work_logs" / "projects" / f"issue-25-{task_id}.md"
        assert project_file.exists()

        content = project_file.read_text(encoding="utf-8")
        assert "# 🎯 Test Task" in content
        assert "**Type:** feature" in content
        assert "**Issue:** #25" in content

    def test_add_progress(self) -> None:
        """進捗追加テスト"""
        # タスク開始
        self.work_log_manager.start_task("Test Task", "feature")

        # 進捗追加
        success = self.work_log_manager.add_progress(
            "Implementation started",
            "Created basic structure"
        )
        assert success

        # 現在のタスク確認
        current_task = self.work_log_manager.get_current_task()
        assert current_task is not None
        assert len(current_task["progress"]) == 1
        assert current_task["progress"][0]["description"] == "Implementation started"
        assert current_task["progress"][0]["details"] == "Created basic structure"

        # 日次ログファイル確認
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = self.temp_dir / ".hive" / "work_logs" / "daily" / f"{today}.md"
        assert daily_file.exists()

        content = daily_file.read_text(encoding="utf-8")
        assert "📋 **Progress:** Implementation started" in content

    def test_add_technical_decision(self) -> None:
        """技術的決定記録テスト"""
        # タスク開始
        self.work_log_manager.start_task("Test Task", "feature")

        # 技術的決定追加
        success = self.work_log_manager.add_technical_decision(
            "Use file-based communication",
            "Better reliability and debugging",
            ["HTTP API", "WebSocket"]
        )
        assert success

        # 現在のタスク確認
        current_task = self.work_log_manager.get_current_task()
        assert current_task is not None
        assert len(current_task["technical_decisions"]) == 1
        decision = current_task["technical_decisions"][0]
        assert decision["decision"] == "Use file-based communication"
        assert decision["reasoning"] == "Better reliability and debugging"
        assert "HTTP API" in decision["alternatives"]

    def test_add_challenge(self) -> None:
        """課題記録テスト"""
        # タスク開始
        self.work_log_manager.start_task("Test Task", "feature")

        # 課題追加
        success = self.work_log_manager.add_challenge(
            "File locking issues",
            "Implemented fcntl-based locking"
        )
        assert success

        # 現在のタスク確認
        current_task = self.work_log_manager.get_current_task()
        assert current_task is not None
        assert len(current_task["challenges"]) == 1
        challenge = current_task["challenges"][0]
        assert challenge["challenge"] == "File locking issues"
        assert challenge["solution"] == "Implemented fcntl-based locking"

    def test_complete_task(self) -> None:
        """タスク完了テスト"""
        # タスク開始
        task_id = self.work_log_manager.start_task("Test Task", "feature")

        # 少し待機（duration計算のため）
        time.sleep(0.1)

        # タスク完了
        success = self.work_log_manager.complete_task("completed")
        assert success

        # 現在のタスクがクリアされることを確認
        current_task = self.work_log_manager.get_current_task()
        assert current_task is None

        # プロジェクトログファイル確認
        project_file = self.temp_dir / ".hive" / "work_logs" / "projects" / f"task-{task_id}.md"
        content = project_file.read_text(encoding="utf-8")
        assert "**Status:** completed" in content
        assert "**Completed:**" in content
        assert "**Duration:**" in content

    def test_work_log_stats(self) -> None:
        """作業ログ統計テスト"""
        # タスク開始
        self.work_log_manager.start_task("Test Task", "feature")

        # 統計取得
        stats = self.work_log_manager.get_work_log_stats()

        assert stats["daily_logs"] == 1
        assert stats["project_logs"] == 1
        assert stats["total_size_kb"] > 0
        assert stats["current_task"]["title"] == "Test Task"


class TestCombAPIIntegration:
    """CombAPI統合テストクラス"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.file_handler = HiveFileHandler(self.temp_dir)
        self.queen_api = CombAPI("queen", self.file_handler)
        self.developer_api = CombAPI("developer", self.file_handler)

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_markdown_logging_integration(self) -> None:
        """Markdownログ統合テスト"""
        # メッセージ送信
        success = self.queen_api.ping("developer")
        assert success

        # Markdownログファイルの確認
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.temp_dir / ".hive" / "comb" / "communication_logs" / today / "queen_developer.md"
        assert log_file.exists()

        content = log_file.read_text(encoding="utf-8")
        assert "🏓 **Ping** - Health check request" in content

    def test_work_log_integration(self) -> None:
        """作業ログ統合テスト"""
        # タスク開始
        task_id = self.queen_api.start_task(
            "Integration Test Task",
            "test",
            "Testing work log integration",
            issue_number=25
        )
        assert task_id is not None

        # 進捗追加
        success = self.queen_api.add_progress("Started integration test")
        assert success

        # 技術的決定追加
        success = self.queen_api.add_technical_decision(
            "Use CombAPI integration",
            "Provides unified interface"
        )
        assert success

        # メトリクス追加
        success = self.queen_api.add_metrics({
            "lines_of_code": 500,
            "test_coverage": "95%"
        })
        assert success

        # 課題追加
        success = self.queen_api.add_challenge(
            "Integration complexity",
            "Simplified API design"
        )
        assert success

        # タスク完了
        success = self.queen_api.complete_task()
        assert success

        # プロジェクトログファイル確認
        project_file = self.temp_dir / ".hive" / "work_logs" / "projects" / f"issue-25-{task_id}.md"
        assert project_file.exists()

        content = project_file.read_text(encoding="utf-8")
        assert "# 🎯 Integration Test Task" in content
        assert "Started integration test" in content
        assert "Use CombAPI integration" in content
        assert "**lines_of_code:** 500" in content
        assert "Integration complexity" in content

    def test_status_with_logs(self) -> None:
        """ログ機能を含むステータス取得テスト"""
        # タスク開始
        self.queen_api.start_task("Status Test Task", "test")

        # メッセージ送信
        self.queen_api.ping("developer")

        # ステータス取得
        status = self.queen_api.get_status()

        assert "work_logs" in status
        assert status["work_logs"]["current_task"]["title"] == "Status Test Task"
        assert status["work_logs"]["daily_logs"] == 1
        assert status["work_logs"]["project_logs"] == 1

    def test_daily_summary_generation(self) -> None:
        """日次サマリー生成テスト"""
        # 通信とタスク活動
        self.queen_api.start_task("Summary Test Task", "test")
        self.queen_api.ping("developer")
        self.queen_api.add_progress("Test progress")

        # サマリー生成
        success = self.queen_api.generate_daily_summary()
        assert success

        # サマリーファイル確認
        today = datetime.now().strftime("%Y-%m-%d")
        summary_file = self.temp_dir / ".hive" / "comb" / "communication_logs" / today / f"summary_{today}.md"
        assert summary_file.exists()

        content = summary_file.read_text(encoding="utf-8")
        assert "# 📊 Daily Communication Summary" in content

