"""
Message Router Integration Tests

Issue #101: プロトコル定義システム実装
MessageRouterIntegrationクラスのテストスイート
"""

import unittest
from unittest.mock import Mock

from comb.message_router import Message as LegacyMessage
from comb.message_router import MessagePriority as LegacyPriority
from comb.message_router import MessageRouter as LegacyRouter
from comb.message_router import MessageType as LegacyType
from protocols.message_protocol import MessagePriority, MessageProtocol, MessageType
from protocols.message_router_integration import MessageRouterIntegration
from protocols.protocol_validator import ProtocolValidator


class TestMessageRouterIntegration(unittest.TestCase):
    """MessageRouterIntegrationのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.mock_legacy_router = Mock(spec=LegacyRouter)
        self.protocol = MessageProtocol()
        self.validator = ProtocolValidator()
        self.integration = MessageRouterIntegration(
            protocol=self.protocol,
            validator=self.validator,
            legacy_router=self.mock_legacy_router,
        )

    def test_send_protocol_message_success(self):
        """プロトコルメッセージ送信成功テスト"""
        # 有効なプロトコルメッセージを作成
        message = self.protocol.create_message(
            message_type=MessageType.REQUEST,
            sender_id="test-sender",
            receiver_id="test-receiver",
            content={"action": "test"},
        )

        # 既存ルーターの送信成功をモック
        self.mock_legacy_router.send_message.return_value = True

        result = self.integration.send_protocol_message(message)

        self.assertTrue(result)
        self.mock_legacy_router.send_message.assert_called_once()

        # 送信されたメッセージを確認
        sent_message = self.mock_legacy_router.send_message.call_args[0][0]
        self.assertEqual(sent_message.from_worker, "test-sender")
        self.assertEqual(sent_message.to_worker, "test-receiver")
        self.assertEqual(sent_message.content, {"action": "test"})

    def test_send_protocol_message_validation_failure(self):
        """プロトコルメッセージ送信検証失敗テスト"""
        # 無効なプロトコルメッセージを作成
        message = self.protocol.create_message(
            message_type=MessageType.REQUEST,
            sender_id="test-sender",
            receiver_id="test-receiver",
            content={"action": "test"},
        )

        # メッセージIDを無効にする
        message.header.message_id = "invalid-id"

        result = self.integration.send_protocol_message(message)

        self.assertFalse(result)
        self.mock_legacy_router.send_message.assert_not_called()

    def test_receive_protocol_messages_success(self):
        """プロトコルメッセージ受信成功テスト"""
        # 既存メッセージを作成
        legacy_message = LegacyMessage.create(
            from_worker="sender",
            to_worker="receiver",
            message_type=LegacyType.REQUEST,
            content={"action": "test"},
            priority=LegacyPriority.MEDIUM,
        )

        # 既存ルーターの受信をモック
        self.mock_legacy_router.receive_messages.return_value = [legacy_message]

        messages = self.integration.receive_protocol_messages("test-worker")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].header.sender_id, "sender")
        self.assertEqual(messages[0].header.receiver_id, "receiver")
        self.assertEqual(messages[0].header.message_type, MessageType.REQUEST)
        self.assertEqual(messages[0].payload.content, {"action": "test"})

    def test_receive_protocol_messages_empty(self):
        """プロトコルメッセージ受信空テスト"""
        # 既存ルーターの受信をモック（空）
        self.mock_legacy_router.receive_messages.return_value = []

        messages = self.integration.receive_protocol_messages("test-worker")

        self.assertEqual(len(messages), 0)

    def test_send_task_assignment(self):
        """タスク割り当て送信テスト"""
        self.mock_legacy_router.send_message.return_value = True

        result = self.integration.send_task_assignment(
            sender_id="queen",
            receiver_id="worker",
            task_id="task-123",
            task_type="analysis",
            task_data={"file": "data.csv"},
            priority=MessagePriority.HIGH,
        )

        self.assertTrue(result)
        self.mock_legacy_router.send_message.assert_called_once()

        # 送信されたメッセージを確認
        sent_message = self.mock_legacy_router.send_message.call_args[0][0]
        self.assertEqual(sent_message.from_worker, "queen")
        self.assertEqual(sent_message.to_worker, "worker")
        self.assertEqual(sent_message.priority, LegacyPriority.HIGH)

        # コンテンツを確認
        content = sent_message.content
        self.assertEqual(content["task_id"], "task-123")
        self.assertEqual(content["task_type"], "analysis")
        self.assertEqual(content["task_data"], {"file": "data.csv"})

    def test_send_task_completion(self):
        """タスク完了送信テスト"""
        self.mock_legacy_router.send_message.return_value = True

        result = self.integration.send_task_completion(
            sender_id="worker",
            receiver_id="queen",
            task_id="task-123",
            result={"output": "processed"},
            success=True,
        )

        self.assertTrue(result)
        self.mock_legacy_router.send_message.assert_called_once()

        # 送信されたメッセージを確認
        sent_message = self.mock_legacy_router.send_message.call_args[0][0]
        self.assertEqual(sent_message.from_worker, "worker")
        self.assertEqual(sent_message.to_worker, "queen")
        self.assertEqual(sent_message.priority, LegacyPriority.HIGH)

        # コンテンツを確認
        content = sent_message.content
        self.assertEqual(content["task_id"], "task-123")
        self.assertEqual(content["result"], {"output": "processed"})
        self.assertTrue(content["success"])
        self.assertIsNone(content["error_message"])

    def test_send_task_completion_with_error(self):
        """エラー付きタスク完了送信テスト"""
        self.mock_legacy_router.send_message.return_value = True

        result = self.integration.send_task_completion(
            sender_id="worker",
            receiver_id="queen",
            task_id="task-123",
            result={},
            success=False,
            error_message="Processing failed",
        )

        self.assertTrue(result)

        # 送信されたメッセージを確認
        sent_message = self.mock_legacy_router.send_message.call_args[0][0]
        content = sent_message.content
        self.assertFalse(content["success"])
        self.assertEqual(content["error_message"], "Processing failed")

    def test_send_heartbeat(self):
        """ハートビート送信テスト"""
        self.mock_legacy_router.send_message.return_value = True

        result = self.integration.send_heartbeat(
            agent_id="worker-1",
            status={"cpu": 50, "memory": 60},
            broadcast=True,
        )

        self.assertTrue(result)
        self.mock_legacy_router.send_message.assert_called_once()

        # 送信されたメッセージを確認
        sent_message = self.mock_legacy_router.send_message.call_args[0][0]
        self.assertEqual(sent_message.from_worker, "worker-1")
        self.assertEqual(sent_message.to_worker, "*")
        self.assertEqual(sent_message.priority, LegacyPriority.LOW)

        # コンテンツを確認
        content = sent_message.content
        self.assertEqual(content["agent_id"], "worker-1")
        self.assertEqual(content["status"], {"cpu": 50, "memory": 60})
        self.assertTrue(content["broadcast"])

    def test_send_system_alert(self):
        """システムアラート送信テスト"""
        self.mock_legacy_router.send_message.return_value = True

        result = self.integration.send_system_alert(
            sender_id="system",
            alert_type="resource_warning",
            alert_message="High CPU usage",
            alert_data={"cpu": 90},
            severity="warning",
        )

        self.assertTrue(result)
        self.mock_legacy_router.send_message.assert_called_once()

        # 送信されたメッセージを確認
        sent_message = self.mock_legacy_router.send_message.call_args[0][0]
        self.assertEqual(sent_message.from_worker, "system")
        self.assertEqual(sent_message.to_worker, "*")
        self.assertEqual(sent_message.priority, LegacyPriority.HIGH)

        # コンテンツを確認
        content = sent_message.content
        self.assertEqual(content["alert_type"], "resource_warning")
        self.assertEqual(content["alert_message"], "High CPU usage")
        self.assertEqual(content["alert_data"], {"cpu": 90})
        self.assertEqual(content["severity"], "warning")

    def test_send_system_alert_critical(self):
        """クリティカルシステムアラート送信テスト"""
        self.mock_legacy_router.send_message.return_value = True

        result = self.integration.send_system_alert(
            sender_id="system",
            alert_type="system_failure",
            alert_message="Critical failure",
            alert_data={"error": "Database down"},
            severity="critical",
        )

        self.assertTrue(result)

        # 送信されたメッセージを確認
        sent_message = self.mock_legacy_router.send_message.call_args[0][0]
        self.assertEqual(
            sent_message.priority, LegacyPriority.URGENT
        )  # CRITICALはURGENTにマップ

    def test_type_mapping(self):
        """タイプマッピングテスト"""
        # プロトコル → 既存
        self.assertEqual(
            self.integration.protocol_to_legacy_type[MessageType.REQUEST],
            LegacyType.REQUEST,
        )
        self.assertEqual(
            self.integration.protocol_to_legacy_type[MessageType.RESPONSE],
            LegacyType.RESPONSE,
        )

        # 既存 → プロトコル
        self.assertEqual(
            self.integration.legacy_to_protocol_type[LegacyType.REQUEST],
            MessageType.REQUEST,
        )
        self.assertEqual(
            self.integration.legacy_to_protocol_type[LegacyType.RESPONSE],
            MessageType.RESPONSE,
        )

    def test_priority_mapping(self):
        """優先度マッピングテスト"""
        # プロトコル → 既存
        self.assertEqual(
            self.integration.protocol_to_legacy_priority[MessagePriority.LOW],
            LegacyPriority.LOW,
        )
        self.assertEqual(
            self.integration.protocol_to_legacy_priority[MessagePriority.HIGH],
            LegacyPriority.HIGH,
        )
        self.assertEqual(
            self.integration.protocol_to_legacy_priority[MessagePriority.CRITICAL],
            LegacyPriority.URGENT,
        )

        # 既存 → プロトコル
        self.assertEqual(
            self.integration.legacy_to_protocol_priority[LegacyPriority.LOW],
            MessagePriority.LOW,
        )
        self.assertEqual(
            self.integration.legacy_to_protocol_priority[LegacyPriority.URGENT],
            MessagePriority.URGENT,
        )

    def test_convert_protocol_to_legacy(self):
        """プロトコル → 既存変換テスト"""
        protocol_message = self.protocol.create_message(
            message_type=MessageType.REQUEST,
            sender_id="sender",
            receiver_id="receiver",
            content={"test": "data"},
            priority=MessagePriority.HIGH,
        )

        legacy_message = self.integration._convert_protocol_to_legacy(protocol_message)

        self.assertEqual(legacy_message.id, protocol_message.header.message_id)
        self.assertEqual(legacy_message.from_worker, "sender")
        self.assertEqual(legacy_message.to_worker, "receiver")
        self.assertEqual(legacy_message.message_type, LegacyType.REQUEST)
        self.assertEqual(legacy_message.priority, LegacyPriority.HIGH)
        self.assertEqual(legacy_message.content, {"test": "data"})

    def test_convert_legacy_to_protocol(self):
        """既存 → プロトコル変換テスト"""
        legacy_message = LegacyMessage.create(
            from_worker="sender",
            to_worker="receiver",
            message_type=LegacyType.REQUEST,
            content={"test": "data"},
            priority=LegacyPriority.HIGH,
        )

        protocol_message = self.integration._convert_legacy_to_protocol(legacy_message)

        self.assertEqual(protocol_message.header.message_id, legacy_message.id)
        self.assertEqual(protocol_message.header.sender_id, "sender")
        self.assertEqual(protocol_message.header.receiver_id, "receiver")
        self.assertEqual(protocol_message.header.message_type, MessageType.REQUEST)
        self.assertEqual(protocol_message.header.priority, MessagePriority.HIGH)
        self.assertEqual(protocol_message.payload.content, {"test": "data"})

    def test_timestamp_conversion(self):
        """タイムスタンプ変換テスト"""
        # タイムスタンプ → ISO
        timestamp = 1634567890.123
        iso_string = self.integration._timestamp_to_iso(timestamp)
        self.assertIsInstance(iso_string, str)
        self.assertIn("2021-10-18", iso_string)

        # None処理
        self.assertIsNone(self.integration._timestamp_to_iso(None))

        # ISO → タイムスタンプ
        converted_back = self.integration._iso_to_timestamp(iso_string)
        self.assertAlmostEqual(converted_back, timestamp, places=0)

    def test_get_integration_stats(self):
        """統合統計情報取得テスト"""
        # 既存ルーターの統計をモック
        self.mock_legacy_router.get_message_stats.return_value = {
            "inbox": 5,
            "outbox": 3,
            "sent": 10,
        }

        stats = self.integration.get_integration_stats()

        self.assertIn("legacy_router_stats", stats)
        self.assertIn("protocol_info", stats)
        self.assertIn("validator_stats", stats)
        self.assertIn("type_mappings", stats)
        self.assertIn("priority_mappings", stats)

        # 統計内容を確認
        self.assertEqual(stats["legacy_router_stats"]["inbox"], 5)
        self.assertEqual(stats["legacy_router_stats"]["outbox"], 3)
        self.assertEqual(stats["legacy_router_stats"]["sent"], 10)

    def test_validate_integration_success(self):
        """統合検証成功テスト"""
        result = self.integration.validate_integration()

        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)

    def test_validate_integration_no_legacy_router(self):
        """統合検証失敗テスト（既存ルーターなし）"""
        # legacy_routerをNoneに設定してテスト
        integration = MessageRouterIntegration(
            protocol=self.protocol,
            validator=self.validator,
            legacy_router=None,
        )

        # 実際にはデフォルトルーターが作成されるため、手動でNoneにする
        integration.legacy_router = None

        result = integration.validate_integration()

        self.assertFalse(result.valid)
        self.assertTrue(any("NOT_INITIALIZED" in error.code for error in result.errors))


class TestDefaultIntegration(unittest.TestCase):
    """デフォルト統合のテスト"""

    def test_default_integration_import(self):
        """デフォルト統合のインポートテスト"""
        from protocols.message_router_integration import default_integration

        self.assertIsInstance(default_integration, MessageRouterIntegration)
        self.assertIsNotNone(default_integration.protocol)
        self.assertIsNotNone(default_integration.validator)
        self.assertIsNotNone(default_integration.legacy_router)

    def test_default_integration_functionality(self):
        """デフォルト統合の機能テスト"""
        from protocols.message_router_integration import default_integration

        # 基本的な機能が動作することを確認
        stats = default_integration.get_integration_stats()
        self.assertIn("legacy_router_stats", stats)
        self.assertIn("protocol_info", stats)

        # 統合検証
        result = default_integration.validate_integration()
        self.assertTrue(result.valid)


if __name__ == "__main__":
    unittest.main()
