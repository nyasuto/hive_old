"""
Comb通信システムのテスト

基本的なping/pong通信とCombシステム全体のテスト
"""

import shutil
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

from comb.api import CombAPI, create_worker_api
from comb.file_handler import HiveFileHandler
from comb.message_router import Message, MessagePriority, MessageType


class TestCombCommunication:
    """Comb通信システムのテストクラス"""

    def setup_method(self) -> None:
        """各テストメソッド前の初期化"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.file_handler = HiveFileHandler(self.temp_dir)
        self.file_handler.ensure_hive_structure()

        # Worker APIs作成
        self.queen_api = CombAPI("queen", self.file_handler)
        self.worker_api = CombAPI("developer_worker", self.file_handler)

    def teardown_method(self) -> None:
        """各テストメソッド後のクリーンアップ"""
        if hasattr(self, "queen_api"):
            self.queen_api.stop_polling()
        if hasattr(self, "worker_api"):
            self.worker_api.stop_polling()

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_hive_structure_creation(self) -> None:
        """Hiveディレクトリ構造の作成テスト"""
        hive_path = self.temp_dir / ".hive"

        # メインディレクトリ確認
        assert hive_path.exists()
        assert (hive_path / "nectar").exists()
        assert (hive_path / "comb").exists()
        assert (hive_path / "honey").exists()
        assert (hive_path / "logs").exists()

        # Nectarサブディレクトリ確認
        assert (hive_path / "nectar" / "pending").exists()
        assert (hive_path / "nectar" / "active").exists()
        assert (hive_path / "nectar" / "completed").exists()

        # Combサブディレクトリ確認
        assert (hive_path / "comb" / "messages").exists()
        assert (hive_path / "comb" / "shared").exists()
        assert (hive_path / "comb" / "cells").exists()

    def test_basic_message_sending(self) -> None:
        """基本的なメッセージ送信テスト"""
        # Queenからメッセージ送信
        success = self.queen_api.send_message(
            to_worker="developer_worker",
            content={"task": "implement_feature", "priority": "high"},
            message_type=MessageType.REQUEST,
        )

        assert success

        # Worker側でメッセージ受信
        messages = self.worker_api.receive_messages()

        assert len(messages) == 1
        message = messages[0]

        assert message.from_worker == "queen"
        assert message.to_worker == "developer_worker"
        assert message.message_type == MessageType.REQUEST
        assert message.content["task"] == "implement_feature"

    def test_ping_pong_communication(self) -> None:
        """Ping/Pong通信テスト"""
        # QueenからPing送信
        ping_success = self.queen_api.ping("developer_worker")
        assert ping_success

        # WorkerでPing受信
        messages = self.worker_api.receive_messages()
        assert len(messages) == 1

        ping_message = messages[0]
        assert ping_message.content["action"] == "ping"

        # WorkerからPong送信
        pong_success = self.worker_api.pong(ping_message)
        assert pong_success

        # QueenでPong受信
        responses = self.queen_api.receive_messages()
        assert len(responses) == 1

        pong_message = responses[0]
        assert pong_message.message_type == MessageType.RESPONSE
        assert pong_message.content["response"]["action"] == "pong"

    def test_message_priority_ordering(self) -> None:
        """メッセージ優先度順序テスト"""
        # 異なる優先度のメッセージを送信
        self.queen_api.send_message(
            "developer_worker", {"msg": "low"}, priority=MessagePriority.LOW
        )
        self.queen_api.send_message(
            "developer_worker", {"msg": "urgent"}, priority=MessagePriority.URGENT
        )
        self.queen_api.send_message(
            "developer_worker", {"msg": "normal"}, priority=MessagePriority.NORMAL
        )

        messages = self.worker_api.receive_messages()

        # 優先度順で並んでいることを確認
        assert len(messages) == 3
        assert messages[0].content["msg"] == "urgent"  # URGENT最初
        assert messages[1].content["msg"] == "normal"  # NORMAL次
        assert messages[2].content["msg"] == "low"  # LOW最後

    def test_nectar_workflow(self) -> None:
        """Nectar（タスク）ワークフローテスト"""
        # Queenからタスク送信
        nectar_success = self.queen_api.send_nectar(
            nectar_type="code_implementation",
            content={
                "description": "Implement login feature",
                "requirements": ["authentication", "validation"],
            },
            priority="high",
        )
        assert nectar_success

        # Workerでタスク受信
        nectar = self.worker_api.receive_nectar()
        assert nectar is not None
        assert nectar["type"] == "code_implementation"
        assert nectar["status"] == "active"
        assert nectar["assigned_to"] == "developer_worker"

        # タスク完了
        completion_success = self.worker_api.complete_nectar(
            nectar["id"],
            result={
                "status": "completed",
                "files": ["login.py", "auth.py"],
                "tests_passed": True,
            },
        )
        assert completion_success

        # Honeyファイル確認
        honey_file = self.file_handler.get_path("honey", f"{nectar['id']}_result.json")
        assert honey_file.exists()

        honey_data = self.file_handler.read_json(honey_file)
        assert honey_data is not None
        assert honey_data["nectar_id"] == nectar["id"]
        assert honey_data["result"]["status"] == "completed"

    def test_lock_synchronization(self) -> None:
        """ロック同期テスト"""
        resource_name = "shared_config"

        # Queenがロック取得
        queen_lock = self.queen_api.acquire_lock(resource_name, timeout=5.0)
        assert queen_lock

        # Workerがロック取得試行（失敗するはず）
        worker_lock = self.worker_api.acquire_lock(resource_name, timeout=1.0)
        assert not worker_lock

        # Queenがロック解放
        queen_release = self.queen_api.release_lock(resource_name)
        assert queen_release

        # Workerがロック取得（成功するはず）
        worker_lock_retry = self.worker_api.acquire_lock(resource_name, timeout=1.0)
        assert worker_lock_retry

        # Worker解放
        worker_release = self.worker_api.release_lock(resource_name)
        assert worker_release

    def test_concurrent_message_handling(self) -> None:
        """並行メッセージ処理テスト"""
        received_messages = []

        def message_handler(message: Message) -> None:
            received_messages.append(message)
            if message.content.get("action") == "ping":
                self.worker_api.pong(message)

        # メッセージハンドラー登録
        self.worker_api.register_handler(MessageType.REQUEST, message_handler)

        # ポーリング開始
        self.worker_api.start_polling(0.1)

        # 複数のPingを同時送信
        ping_threads = []
        for i in range(5):
            thread = threading.Thread(
                target=lambda i=i: self.queen_api.send_message(
                    "developer_worker", {"action": "ping", "id": i}, MessageType.REQUEST
                )
            )
            ping_threads.append(thread)
            thread.start()

        # 全スレッド完了待機
        for thread in ping_threads:
            thread.join()

        # 少し待ってハンドラー処理完了を待つ
        time.sleep(0.5)

        # 全メッセージが処理されたことを確認
        assert len(received_messages) == 5

        # Pongレスポンス確認
        responses = self.queen_api.receive_messages()
        assert len(responses) == 5

        for response in responses:
            assert response.message_type == MessageType.RESPONSE
            assert response.content["response"]["action"] == "pong"

    def test_error_handling(self) -> None:
        """エラーハンドリングテスト"""
        # エラーメッセージ送信
        error_success = self.queen_api.send_error(
            "developer_worker",
            "Invalid task format",
            {"code": "INVALID_FORMAT", "line": 42},
        )
        assert error_success

        # Worker側でエラー受信
        messages = self.worker_api.receive_messages()
        assert len(messages) == 1

        error_message = messages[0]
        assert error_message.message_type == MessageType.ERROR
        assert error_message.content["error"] == "Invalid task format"
        assert error_message.content["details"]["code"] == "INVALID_FORMAT"

    def test_message_expiration(self) -> None:
        """メッセージ期限切れテスト"""
        # 非常に短いTTLでメッセージ送信（テスト用）
        import datetime

        now = datetime.datetime.now()
        expires_at = now + datetime.timedelta(seconds=0.5)  # 0.5秒後に期限切れ

        message = Message(
            id="test_message",
            from_worker="queen",
            to_worker="developer_worker",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.NORMAL,
            content={"action": "test"},
            timestamp=now.isoformat(),
            expires_at=expires_at.isoformat(),
        )

        # メッセージをinboxに直接配置（期限切れテスト用）
        inbox_file = (
            self.queen_api.message_router.inbox_dir
            / "developer_worker_test_message.json"
        )
        self.queen_api.file_handler.write_json(inbox_file, message.to_dict())

        # 期限切れまで待機
        time.sleep(1)

        # 期限切れメッセージのクリーンアップ
        cleanup_count = self.queen_api.message_router.cleanup_expired_messages()
        assert cleanup_count > 0

        # メッセージが受信されないことを確認
        messages = self.worker_api.receive_messages()
        assert len(messages) == 0

    def test_api_status_reporting(self) -> None:
        """API状況レポートテスト"""
        # いくつかのメッセージを送信
        self.queen_api.ping("developer_worker")
        self.queen_api.send_nectar("test_task", {"data": "test"})

        # ロック取得
        self.queen_api.acquire_lock("test_resource")

        # 状況取得
        status = self.queen_api.get_status()

        assert status["worker_id"] == "queen"
        assert "messages" in status
        assert "locks" in status
        assert "timestamp" in status

        # メッセージ統計確認
        assert status["messages"]["sent"] >= 1

        # ロック統計確認
        assert status["locks"]["active_locks"] >= 1


class TestFileHandler:
    """ファイルハンドラーの個別テスト"""

    def setup_method(self) -> None:
        """テスト前初期化"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.handler = HiveFileHandler(self.temp_dir)

    def teardown_method(self) -> None:
        """テスト後クリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_json_read_write(self) -> None:
        """JSON読み書きテスト"""
        test_data = {
            "message": "Hello Hive",
            "timestamp": datetime.now().isoformat(),
            "numbers": [1, 2, 3, 4, 5],
        }

        test_file = self.temp_dir / "test.json"

        # 書き込み
        write_success = self.handler.write_json(test_file, test_data)
        assert write_success
        assert test_file.exists()

        # 読み込み
        read_data = self.handler.read_json(test_file)
        assert read_data == test_data

    def test_concurrent_file_access(self) -> None:
        """並行ファイルアクセステスト"""
        test_file = self.temp_dir / "concurrent.json"
        results = []

        def write_data(worker_id: int) -> None:
            data = {"worker": worker_id, "timestamp": time.time()}
            success = self.handler.write_json(test_file, data)
            results.append(success)

        # 複数スレッドで同時書き込み
        threads = []
        for i in range(5):
            thread = threading.Thread(target=write_data, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 全て成功したことを確認
        assert all(results)

        # ファイルが破損していないことを確認
        final_data = self.handler.read_json(test_file)
        assert final_data is not None
        assert "worker" in final_data


def test_create_worker_api() -> None:
    """Worker API作成ヘルパーテスト"""
    api = create_worker_api("test_worker")

    assert api.worker_id == "test_worker"
    assert api.file_handler is not None
    assert api.message_router is not None
    assert api.sync_manager is not None
