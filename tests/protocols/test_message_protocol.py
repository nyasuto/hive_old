"""
Message Protocol Tests

Issue #101: プロトコル定義システム実装
MessageProtocol及び関連クラスのテストスイート
"""

import time
import unittest
from unittest.mock import patch

from protocols.message_protocol import (
    MessageHeader,
    MessagePayload,
    MessagePriority,
    MessageProtocol,
    MessageStatus,
    MessageType,
    ProtocolMessage,
    ProtocolVersion,
    default_protocol,
)


class TestMessageHeader(unittest.TestCase):
    """MessageHeaderのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.header = MessageHeader(
            message_id="550e8400-e29b-41d4-a716-446655440000",
            protocol_version="1.1",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            timestamp=time.time(),
            sender_id="test-sender",
            receiver_id="test-receiver",
        )

    def test_to_dict(self):
        """辞書変換テスト"""
        header_dict = self.header.to_dict()

        self.assertEqual(
            header_dict["message_id"], "550e8400-e29b-41d4-a716-446655440000"
        )
        self.assertEqual(header_dict["protocol_version"], "1.1")
        self.assertEqual(header_dict["message_type"], "request")
        self.assertEqual(header_dict["priority"], 2)
        self.assertEqual(header_dict["sender_id"], "test-sender")
        self.assertEqual(header_dict["receiver_id"], "test-receiver")

    def test_from_dict(self):
        """辞書復元テスト"""
        header_dict = self.header.to_dict()
        restored_header = MessageHeader.from_dict(header_dict)

        self.assertEqual(restored_header.message_id, self.header.message_id)
        self.assertEqual(restored_header.protocol_version, self.header.protocol_version)
        self.assertEqual(restored_header.message_type, self.header.message_type)
        self.assertEqual(restored_header.priority, self.header.priority)
        self.assertEqual(restored_header.sender_id, self.header.sender_id)
        self.assertEqual(restored_header.receiver_id, self.header.receiver_id)

    def test_optional_fields(self):
        """オプションフィールドテスト"""
        header = MessageHeader(
            message_id="550e8400-e29b-41d4-a716-446655440000",
            protocol_version="1.1",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.HIGH,
            timestamp=time.time(),
            sender_id="sender",
            receiver_id="receiver",
            correlation_id="550e8400-e29b-41d4-a716-446655440001",
            reply_to="reply-to",
            expires_at=time.time() + 3600,
            max_retries=5,
        )

        header_dict = header.to_dict()
        restored_header = MessageHeader.from_dict(header_dict)

        self.assertEqual(restored_header.correlation_id, header.correlation_id)
        self.assertEqual(restored_header.reply_to, header.reply_to)
        self.assertEqual(restored_header.expires_at, header.expires_at)
        self.assertEqual(restored_header.max_retries, header.max_retries)


class TestMessagePayload(unittest.TestCase):
    """MessagePayloadのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.payload = MessagePayload(
            content={"key": "value", "number": 42},
            content_type="application/json",
            encoding="utf-8",
        )

    def test_to_dict(self):
        """辞書変換テスト"""
        payload_dict = self.payload.to_dict()

        self.assertEqual(payload_dict["content"], {"key": "value", "number": 42})
        self.assertEqual(payload_dict["content_type"], "application/json")
        self.assertEqual(payload_dict["encoding"], "utf-8")
        self.assertIsNone(payload_dict["checksum"])

    def test_from_dict(self):
        """辞書復元テスト"""
        payload_dict = self.payload.to_dict()
        restored_payload = MessagePayload.from_dict(payload_dict)

        self.assertEqual(restored_payload.content, self.payload.content)
        self.assertEqual(restored_payload.content_type, self.payload.content_type)
        self.assertEqual(restored_payload.encoding, self.payload.encoding)
        self.assertEqual(restored_payload.checksum, self.payload.checksum)

    def test_default_values(self):
        """デフォルト値テスト"""
        payload = MessagePayload(content={"test": "data"})

        self.assertEqual(payload.content_type, "application/json")
        self.assertEqual(payload.encoding, "utf-8")
        self.assertIsNone(payload.checksum)


class TestProtocolMessage(unittest.TestCase):
    """ProtocolMessageのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.header = MessageHeader(
            message_id="550e8400-e29b-41d4-a716-446655440000",
            protocol_version="1.1",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            timestamp=time.time(),
            sender_id="test-sender",
            receiver_id="test-receiver",
        )

        self.payload = MessagePayload(
            content={"action": "test", "data": {"value": 123}},
        )

        self.message = ProtocolMessage(
            header=self.header,
            payload=self.payload,
        )

    def test_to_dict(self):
        """辞書変換テスト"""
        message_dict = self.message.to_dict()

        self.assertIn("header", message_dict)
        self.assertIn("payload", message_dict)
        self.assertEqual(message_dict["status"], "pending")

        # ヘッダー部分のテスト
        header_dict = message_dict["header"]
        self.assertEqual(
            header_dict["message_id"], "550e8400-e29b-41d4-a716-446655440000"
        )
        self.assertEqual(header_dict["message_type"], "request")

        # ペイロード部分のテスト
        payload_dict = message_dict["payload"]
        self.assertEqual(
            payload_dict["content"], {"action": "test", "data": {"value": 123}}
        )

    def test_from_dict(self):
        """辞書復元テスト"""
        message_dict = self.message.to_dict()
        restored_message = ProtocolMessage.from_dict(message_dict)

        # ヘッダー検証
        self.assertEqual(
            restored_message.header.message_id, self.message.header.message_id
        )
        self.assertEqual(
            restored_message.header.message_type, self.message.header.message_type
        )

        # ペイロード検証
        self.assertEqual(restored_message.payload.content, self.message.payload.content)

        # ステータス検証
        self.assertEqual(restored_message.status, self.message.status)

    def test_is_expired(self):
        """期限切れチェックテスト"""
        # 期限なしメッセージ
        self.assertFalse(self.message.is_expired())

        # 未来の期限
        self.message.header.expires_at = time.time() + 3600
        self.assertFalse(self.message.is_expired())

        # 過去の期限
        self.message.header.expires_at = time.time() - 3600
        self.assertTrue(self.message.is_expired())

    def test_can_retry(self):
        """リトライ可能チェックテスト"""
        # 基本的なリトライ可能状態
        self.message.status = MessageStatus.FAILED
        self.assertTrue(self.message.can_retry())

        # 最大リトライ回数に達している場合
        self.message.header.retry_count = 3
        self.message.header.max_retries = 3
        self.assertFalse(self.message.can_retry())

        # 期限切れの場合
        self.message.header.retry_count = 0
        self.message.header.expires_at = time.time() - 3600
        self.assertFalse(self.message.can_retry())

        # 完了済みの場合
        self.message.header.expires_at = time.time() + 3600
        self.message.status = MessageStatus.COMPLETED
        self.assertFalse(self.message.can_retry())

    def test_increment_retry(self):
        """リトライ増加テスト"""
        original_count = self.message.header.retry_count
        self.message.status = MessageStatus.FAILED

        self.message.increment_retry()

        self.assertEqual(self.message.header.retry_count, original_count + 1)
        self.assertEqual(self.message.status, MessageStatus.PENDING)

    def test_status_transitions(self):
        """ステータス遷移テスト"""
        # 初期状態
        self.assertEqual(self.message.status, MessageStatus.PENDING)

        # 処理中へ
        self.message.mark_processing()
        self.assertEqual(self.message.status, MessageStatus.PROCESSING)

        # 完了へ
        self.message.mark_completed()
        self.assertEqual(self.message.status, MessageStatus.COMPLETED)

        # 失敗へ
        self.message.mark_failed()
        self.assertEqual(self.message.status, MessageStatus.FAILED)

        # キャンセルへ
        self.message.mark_cancelled()
        self.assertEqual(self.message.status, MessageStatus.CANCELLED)


class TestMessageProtocol(unittest.TestCase):
    """MessageProtocolのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.protocol = MessageProtocol(ProtocolVersion.V1_1)

    def test_create_message(self):
        """メッセージ作成テスト"""
        message = self.protocol.create_message(
            message_type=MessageType.REQUEST,
            sender_id="sender",
            receiver_id="receiver",
            content={"action": "test"},
            priority=MessagePriority.HIGH,
        )

        self.assertEqual(message.header.message_type, MessageType.REQUEST)
        self.assertEqual(message.header.sender_id, "sender")
        self.assertEqual(message.header.receiver_id, "receiver")
        self.assertEqual(message.header.priority, MessagePriority.HIGH)
        self.assertEqual(message.payload.content, {"action": "test"})
        self.assertEqual(message.status, MessageStatus.PENDING)

    def test_create_message_with_ttl(self):
        """TTL付きメッセージ作成テスト"""
        with patch("time.time", return_value=1000.0):
            message = self.protocol.create_message(
                message_type=MessageType.REQUEST,
                sender_id="sender",
                receiver_id="receiver",
                content={"action": "test"},
                ttl_seconds=3600,
            )

        self.assertEqual(message.header.expires_at, 1000.0 + 3600)

    def test_create_response(self):
        """レスポンスメッセージ作成テスト"""
        original_message = self.protocol.create_message(
            message_type=MessageType.REQUEST,
            sender_id="sender",
            receiver_id="receiver",
            content={"action": "test"},
        )

        response = self.protocol.create_response(
            original_message=original_message,
            response_content={"result": "success"},
        )

        self.assertEqual(response.header.message_type, MessageType.RESPONSE)
        self.assertEqual(response.header.sender_id, "receiver")
        self.assertEqual(response.header.receiver_id, "sender")
        self.assertEqual(
            response.header.correlation_id, original_message.header.correlation_id
        )

        # レスポンス内容の検証
        response_content = response.payload.content
        self.assertEqual(
            response_content["original_message_id"], original_message.header.message_id
        )
        self.assertEqual(response_content["response"], {"result": "success"})

    def test_create_task_assignment(self):
        """タスク割り当てメッセージ作成テスト"""
        message = self.protocol.create_task_assignment(
            sender_id="queen",
            receiver_id="worker",
            task_id="task-123",
            task_type="analysis",
            task_data={"file": "data.csv"},
            priority=MessagePriority.HIGH,
        )

        self.assertEqual(message.header.message_type, MessageType.TASK_ASSIGNMENT)
        self.assertEqual(message.header.priority, MessagePriority.HIGH)
        self.assertEqual(message.header.correlation_id, "task-123")

        content = message.payload.content
        self.assertEqual(content["task_id"], "task-123")
        self.assertEqual(content["task_type"], "analysis")
        self.assertEqual(content["task_data"], {"file": "data.csv"})

    def test_create_task_completion(self):
        """タスク完了メッセージ作成テスト"""
        message = self.protocol.create_task_completion(
            sender_id="worker",
            receiver_id="queen",
            task_id="task-123",
            result={"output": "processed"},
            success=True,
        )

        self.assertEqual(message.header.message_type, MessageType.TASK_COMPLETION)
        self.assertEqual(message.header.priority, MessagePriority.HIGH)
        self.assertEqual(message.header.correlation_id, "task-123")

        content = message.payload.content
        self.assertEqual(content["task_id"], "task-123")
        self.assertEqual(content["result"], {"output": "processed"})
        self.assertTrue(content["success"])
        self.assertIsNone(content["error_message"])

    def test_create_task_completion_with_error(self):
        """エラー付きタスク完了メッセージ作成テスト"""
        message = self.protocol.create_task_completion(
            sender_id="worker",
            receiver_id="queen",
            task_id="task-123",
            result={},
            success=False,
            error_message="Processing failed",
        )

        content = message.payload.content
        self.assertFalse(content["success"])
        self.assertEqual(content["error_message"], "Processing failed")

    def test_create_heartbeat(self):
        """ハートビートメッセージ作成テスト"""
        message = self.protocol.create_heartbeat(
            agent_id="worker-1",
            status={"cpu": 50, "memory": 60},
        )

        self.assertEqual(message.header.message_type, MessageType.AGENT_HEARTBEAT)
        self.assertEqual(message.header.priority, MessagePriority.LOW)
        self.assertEqual(message.header.receiver_id, "*")

        content = message.payload.content
        self.assertEqual(content["agent_id"], "worker-1")
        self.assertEqual(content["status"], {"cpu": 50, "memory": 60})
        self.assertFalse(content["broadcast"])

    def test_create_heartbeat_broadcast(self):
        """ブロードキャストハートビートメッセージ作成テスト"""
        message = self.protocol.create_heartbeat(
            agent_id="worker-1",
            status={"cpu": 50, "memory": 60},
            broadcast=True,
        )

        content = message.payload.content
        self.assertTrue(content["broadcast"])

    def test_create_system_alert(self):
        """システムアラートメッセージ作成テスト"""
        message = self.protocol.create_system_alert(
            sender_id="system",
            alert_type="resource_warning",
            alert_message="High CPU usage detected",
            alert_data={"cpu_usage": 90},
            severity="warning",
        )

        self.assertEqual(message.header.message_type, MessageType.SYSTEM_ALERT)
        self.assertEqual(message.header.priority, MessagePriority.HIGH)
        self.assertEqual(message.header.receiver_id, "*")

        content = message.payload.content
        self.assertEqual(content["alert_type"], "resource_warning")
        self.assertEqual(content["alert_message"], "High CPU usage detected")
        self.assertEqual(content["alert_data"], {"cpu_usage": 90})
        self.assertEqual(content["severity"], "warning")
        self.assertTrue(content["broadcast"])

    def test_create_system_alert_critical(self):
        """クリティカルシステムアラートメッセージ作成テスト"""
        message = self.protocol.create_system_alert(
            sender_id="system",
            alert_type="system_failure",
            alert_message="System failure detected",
            alert_data={"error": "Database connection lost"},
            severity="critical",
        )

        self.assertEqual(message.header.priority, MessagePriority.CRITICAL)

    def test_is_version_supported(self):
        """バージョンサポートチェックテスト"""
        self.assertTrue(self.protocol.is_version_supported("1.0"))
        self.assertTrue(self.protocol.is_version_supported("1.1"))
        self.assertTrue(self.protocol.is_version_supported("2.0"))
        self.assertFalse(self.protocol.is_version_supported("3.0"))
        self.assertFalse(self.protocol.is_version_supported("invalid"))

    def test_get_protocol_info(self):
        """プロトコル情報取得テスト"""
        info = self.protocol.get_protocol_info()

        self.assertEqual(info["current_version"], "1.1")
        self.assertIn("1.0", info["supported_versions"])
        self.assertIn("1.1", info["supported_versions"])
        self.assertIn("2.0", info["supported_versions"])

        self.assertIn("request", info["supported_message_types"])
        self.assertIn("response", info["supported_message_types"])
        self.assertIn("task_assignment", info["supported_message_types"])

        self.assertIn(1, info["supported_priorities"])
        self.assertIn(2, info["supported_priorities"])
        self.assertIn(3, info["supported_priorities"])

        self.assertIn("pending", info["supported_statuses"])
        self.assertIn("processing", info["supported_statuses"])
        self.assertIn("completed", info["supported_statuses"])


class TestDefaultProtocol(unittest.TestCase):
    """デフォルトプロトコルのテスト"""

    def test_default_protocol_exists(self):
        """デフォルトプロトコルの存在確認"""
        self.assertIsInstance(default_protocol, MessageProtocol)
        self.assertEqual(default_protocol.protocol_version, ProtocolVersion.CURRENT)

    def test_default_protocol_functionality(self):
        """デフォルトプロトコルの機能テスト"""
        message = default_protocol.create_message(
            message_type=MessageType.REQUEST,
            sender_id="test-sender",
            receiver_id="test-receiver",
            content={"test": "data"},
        )

        self.assertEqual(message.header.protocol_version, ProtocolVersion.CURRENT.value)
        self.assertEqual(message.header.message_type, MessageType.REQUEST)
        self.assertEqual(message.payload.content, {"test": "data"})


if __name__ == "__main__":
    unittest.main()
