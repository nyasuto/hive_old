"""
Protocol Validator Tests

Issue #101: プロトコル定義システム実装
ProtocolValidator及び関連クラスのテストスイート
"""

import time
import unittest

from protocols.message_protocol import (
    MessageHeader,
    MessagePayload,
    MessagePriority,
    MessageProtocol,
    MessageStatus,
    MessageType,
)
from protocols.protocol_validator import (
    ProtocolValidator,
    ValidationError,
    ValidationResult,
    default_validator,
    strict_validator,
)


class TestValidationError(unittest.TestCase):
    """ValidationErrorのテスト"""

    def test_basic_error(self):
        """基本エラーテスト"""
        error = ValidationError("Test error message")

        self.assertEqual(str(error), "Test error message")
        self.assertIsNone(error.field)
        self.assertIsNone(error.code)

    def test_error_with_field_and_code(self):
        """フィールドとコード付きエラーテスト"""
        error = ValidationError(
            "Invalid format", field="message_id", code="INVALID_FORMAT"
        )

        self.assertEqual(str(error), "Invalid format")
        self.assertEqual(error.field, "message_id")
        self.assertEqual(error.code, "INVALID_FORMAT")


class TestValidationResult(unittest.TestCase):
    """ValidationResultのテスト"""

    def test_valid_result(self):
        """有効な結果テスト"""
        result = ValidationResult()

        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)

    def test_invalid_result(self):
        """無効な結果テスト"""
        result = ValidationResult(valid=False)

        self.assertFalse(result.valid)
        self.assertEqual(len(result.errors), 0)

    def test_add_error(self):
        """エラー追加テスト"""
        result = ValidationResult()
        error = ValidationError("Test error", field="test_field", code="TEST_ERROR")

        result.add_error(error)

        self.assertFalse(result.valid)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0], error)

    def test_to_dict(self):
        """辞書変換テスト"""
        result = ValidationResult()
        error = ValidationError("Test error", field="test_field", code="TEST_ERROR")
        result.add_error(error)

        result_dict = result.to_dict()

        self.assertFalse(result_dict["valid"])
        self.assertEqual(len(result_dict["errors"]), 1)

        error_dict = result_dict["errors"][0]
        self.assertEqual(error_dict["message"], "Test error")
        self.assertEqual(error_dict["field"], "test_field")
        self.assertEqual(error_dict["code"], "TEST_ERROR")


class TestProtocolValidator(unittest.TestCase):
    """ProtocolValidatorのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.validator = ProtocolValidator()
        self.protocol = MessageProtocol()

        # 有効なメッセージを作成
        self.valid_message = self.protocol.create_message(
            message_type=MessageType.REQUEST,
            sender_id="test-sender",
            receiver_id="test-receiver",
            content={"action": "test"},
        )

    def test_validate_valid_message(self):
        """有効なメッセージの検証テスト"""
        result = self.validator.validate_message(self.valid_message)

        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)

    def test_validate_header_required_fields(self):
        """ヘッダー必須フィールド検証テスト"""
        # 無効なヘッダーを作成
        invalid_header = MessageHeader(
            message_id="",  # 空のメッセージID
            protocol_version="1.1",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            timestamp=time.time(),
            sender_id="sender",
            receiver_id="receiver",
        )

        result = self.validator.validate_header(invalid_header)

        self.assertFalse(result.valid)
        self.assertTrue(any("message_id" in str(error) for error in result.errors))

    def test_validate_header_invalid_uuid(self):
        """ヘッダー無効UUID検証テスト"""
        header = MessageHeader(
            message_id="invalid-uuid",
            protocol_version="1.1",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            timestamp=time.time(),
            sender_id="sender",
            receiver_id="receiver",
        )

        result = self.validator.validate_header(header)

        self.assertFalse(result.valid)
        self.assertTrue(any("INVALID_FORMAT" in error.code for error in result.errors))

    def test_validate_header_unsupported_version(self):
        """ヘッダー未サポートバージョン検証テスト"""
        header = MessageHeader(
            message_id="550e8400-e29b-41d4-a716-446655440000",
            protocol_version="999.0",  # 未サポートバージョン
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            timestamp=time.time(),
            sender_id="sender",
            receiver_id="receiver",
        )

        result = self.validator.validate_header(header)

        self.assertFalse(result.valid)
        self.assertTrue(
            any("UNSUPPORTED_VERSION" in error.code for error in result.errors)
        )

    def test_validate_header_invalid_timestamp(self):
        """ヘッダー無効タイムスタンプ検証テスト"""
        header = MessageHeader(
            message_id="550e8400-e29b-41d4-a716-446655440000",
            protocol_version="1.1",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            timestamp=-1,  # 無効なタイムスタンプ
            sender_id="sender",
            receiver_id="receiver",
        )

        result = self.validator.validate_header(header)

        self.assertFalse(result.valid)
        self.assertTrue(
            any("INVALID_TIMESTAMP" in error.code for error in result.errors)
        )

    def test_validate_header_future_timestamp(self):
        """ヘッダー未来タイムスタンプ検証テスト"""
        header = MessageHeader(
            message_id="550e8400-e29b-41d4-a716-446655440000",
            protocol_version="1.1",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            timestamp=time.time() + 3600,  # 1時間後
            sender_id="sender",
            receiver_id="receiver",
        )

        result = self.validator.validate_header(header)

        self.assertFalse(result.valid)
        self.assertTrue(
            any("FUTURE_TIMESTAMP" in error.code for error in result.errors)
        )

    def test_validate_header_invalid_agent_id(self):
        """ヘッダー無効エージェントID検証テスト"""
        header = MessageHeader(
            message_id="550e8400-e29b-41d4-a716-446655440000",
            protocol_version="1.1",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            timestamp=time.time(),
            sender_id="invalid@agent#id",  # 無効なエージェントID
            receiver_id="receiver",
        )

        result = self.validator.validate_header(header)

        self.assertFalse(result.valid)
        self.assertTrue(
            any("INVALID_AGENT_ID" in error.code for error in result.errors)
        )

    def test_validate_header_retry_validation(self):
        """ヘッダーリトライ検証テスト"""
        header = MessageHeader(
            message_id="550e8400-e29b-41d4-a716-446655440000",
            protocol_version="1.1",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            timestamp=time.time(),
            sender_id="sender",
            receiver_id="receiver",
            retry_count=5,
            max_retries=3,  # リトライ回数が最大値を超過
        )

        result = self.validator.validate_header(header)

        self.assertFalse(result.valid)
        self.assertTrue(any("RETRY_EXCEEDED" in error.code for error in result.errors))

    def test_validate_header_invalid_expiry(self):
        """ヘッダー無効期限検証テスト"""
        timestamp = time.time()
        header = MessageHeader(
            message_id="550e8400-e29b-41d4-a716-446655440000",
            protocol_version="1.1",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            timestamp=timestamp,
            sender_id="sender",
            receiver_id="receiver",
            expires_at=timestamp - 3600,  # 過去の期限
        )

        result = self.validator.validate_header(header)

        self.assertFalse(result.valid)
        self.assertTrue(any("INVALID_EXPIRY" in error.code for error in result.errors))

    def test_validate_payload_required_fields(self):
        """ペイロード必須フィールド検証テスト"""
        payload = MessagePayload(content=None)  # 必須フィールドがNone

        result = self.validator.validate_payload(payload)

        self.assertFalse(result.valid)
        self.assertTrue(
            any("REQUIRED_FIELD_MISSING" in error.code for error in result.errors)
        )

    def test_validate_payload_unsupported_content_type(self):
        """ペイロード未サポートコンテンツタイプ検証テスト"""
        payload = MessagePayload(
            content={"test": "data"},
            content_type="application/unknown",  # 未サポートタイプ
        )

        result = self.validator.validate_payload(payload)

        self.assertFalse(result.valid)
        self.assertTrue(
            any("UNSUPPORTED_CONTENT_TYPE" in error.code for error in result.errors)
        )

    def test_validate_payload_invalid_content_type(self):
        """ペイロード無効コンテンツタイプ検証テスト"""
        payload = MessagePayload(
            content="invalid content",  # 辞書ではない
        )

        result = self.validator.validate_payload(payload)

        self.assertFalse(result.valid)
        self.assertTrue(
            any("INVALID_CONTENT_TYPE" in error.code for error in result.errors)
        )

    def test_validate_status(self):
        """ステータス検証テスト"""
        # 有効なステータス
        result = self.validator.validate_status(MessageStatus.PENDING)
        self.assertTrue(result.valid)

        result = self.validator.validate_status(MessageStatus.PROCESSING)
        self.assertTrue(result.valid)

        result = self.validator.validate_status(MessageStatus.COMPLETED)
        self.assertTrue(result.valid)

    def test_validate_task_assignment_message(self):
        """タスク割り当てメッセージ検証テスト"""
        # 有効なタスク割り当てメッセージ
        message = self.protocol.create_task_assignment(
            sender_id="queen",
            receiver_id="worker",
            task_id="task-123",
            task_type="analysis",
            task_data={"file": "data.csv"},
        )

        result = self.validator.validate_message(message)
        self.assertTrue(result.valid)

        # 無効なタスク割り当てメッセージ（必須フィールド不足）
        invalid_message = self.protocol.create_message(
            message_type=MessageType.TASK_ASSIGNMENT,
            sender_id="queen",
            receiver_id="worker",
            content={"incomplete": "data"},  # 必須フィールド不足
        )

        result = self.validator.validate_message(invalid_message)
        self.assertFalse(result.valid)
        self.assertTrue(
            any("TASK_FIELD_MISSING" in error.code for error in result.errors)
        )

    def test_validate_task_completion_message(self):
        """タスク完了メッセージ検証テスト"""
        # 有効なタスク完了メッセージ
        message = self.protocol.create_task_completion(
            sender_id="worker",
            receiver_id="queen",
            task_id="task-123",
            result={"output": "processed"},
            success=True,
        )

        result = self.validator.validate_message(message)
        self.assertTrue(result.valid)

        # 無効なタスク完了メッセージ（successフィールドが非boolean）
        invalid_message = self.protocol.create_message(
            message_type=MessageType.TASK_COMPLETION,
            sender_id="worker",
            receiver_id="queen",
            content={
                "task_id": "task-123",
                "result": {"output": "processed"},
                "success": "true",  # 文字列（無効）
            },
        )

        result = self.validator.validate_message(invalid_message)
        self.assertFalse(result.valid)
        self.assertTrue(
            any("INVALID_FIELD_TYPE" in error.code for error in result.errors)
        )

    def test_validate_response_message(self):
        """レスポンスメッセージ検証テスト"""
        # 有効なレスポンスメッセージ
        response = self.protocol.create_response(
            original_message=self.valid_message,
            response_content={"result": "success"},
        )

        result = self.validator.validate_message(response)
        self.assertTrue(result.valid)

        # 無効なレスポンスメッセージ（original_message_id不足）
        invalid_response = self.protocol.create_message(
            message_type=MessageType.RESPONSE,
            sender_id="receiver",
            receiver_id="sender",
            content={"response": "data"},  # original_message_id不足
        )

        result = self.validator.validate_message(invalid_response)
        self.assertFalse(result.valid)
        self.assertTrue(
            any("RESPONSE_FIELD_MISSING" in error.code for error in result.errors)
        )

    def test_validate_heartbeat_message(self):
        """ハートビートメッセージ検証テスト"""
        # 有効なハートビートメッセージ
        message = self.protocol.create_heartbeat(
            agent_id="worker-1",
            status={"cpu": 50, "memory": 60},
        )

        result = self.validator.validate_message(message)
        self.assertTrue(result.valid)

        # 無効なハートビートメッセージ（agent_id不足）
        invalid_message = self.protocol.create_message(
            message_type=MessageType.AGENT_HEARTBEAT,
            sender_id="worker",
            receiver_id="*",
            content={"status": {"cpu": 50}},  # agent_id不足
        )

        result = self.validator.validate_message(invalid_message)
        self.assertFalse(result.valid)
        self.assertTrue(
            any("HEARTBEAT_FIELD_MISSING" in error.code for error in result.errors)
        )

    def test_validate_system_alert_message(self):
        """システムアラートメッセージ検証テスト"""
        # 有効なシステムアラートメッセージ
        message = self.protocol.create_system_alert(
            sender_id="system",
            alert_type="resource_warning",
            alert_message="High CPU usage",
            alert_data={"cpu": 90},
        )

        result = self.validator.validate_message(message)
        self.assertTrue(result.valid)

        # 無効なシステムアラートメッセージ（無効なseverity）
        invalid_message = self.protocol.create_message(
            message_type=MessageType.SYSTEM_ALERT,
            sender_id="system",
            receiver_id="*",
            content={
                "alert_type": "resource_warning",
                "alert_message": "High CPU usage",
                "severity": "invalid_severity",  # 無効
            },
        )

        result = self.validator.validate_message(invalid_message)
        self.assertFalse(result.valid)
        self.assertTrue(
            any("INVALID_SEVERITY" in error.code for error in result.errors)
        )

    def test_validate_expired_message(self):
        """期限切れメッセージ検証テスト"""
        # 期限切れメッセージを作成
        expired_message = self.protocol.create_message(
            message_type=MessageType.REQUEST,
            sender_id="sender",
            receiver_id="receiver",
            content={"test": "data"},
            ttl_seconds=1,
        )

        # 期限切れにするため少し待つ
        time.sleep(1.1)

        result = self.validator.validate_message(expired_message)

        self.assertFalse(result.valid)
        self.assertTrue(any("EXPIRED" in error.code for error in result.errors))

    def test_validate_batch(self):
        """バッチ検証テスト"""
        messages = [
            self.protocol.create_message(
                message_type=MessageType.REQUEST,
                sender_id="sender1",
                receiver_id="receiver1",
                content={"test": "data1"},
            ),
            self.protocol.create_message(
                message_type=MessageType.REQUEST,
                sender_id="sender2",
                receiver_id="receiver2",
                content={"test": "data2"},
            ),
        ]

        results = self.validator.validate_batch(messages)

        self.assertEqual(len(results), 2)
        for message in messages:
            self.assertIn(message.header.message_id, results)
            self.assertTrue(results[message.header.message_id].valid)

    def test_validate_version_compatibility(self):
        """バージョン互換性検証テスト"""
        # 互換性のあるバージョン
        result = self.validator.validate_version_compatibility("1.0", "1.1")
        self.assertTrue(result.valid)

        result = self.validator.validate_version_compatibility("1.1", "1.0")
        self.assertTrue(result.valid)

        # 互換性のないバージョン
        result = self.validator.validate_version_compatibility("1.0", "2.0")
        self.assertFalse(result.valid)
        self.assertTrue(
            any("VERSION_INCOMPATIBLE" in error.code for error in result.errors)
        )

        # 未サポートバージョン
        result = self.validator.validate_version_compatibility("999.0", "1.0")
        self.assertFalse(result.valid)
        self.assertTrue(
            any("UNSUPPORTED_VERSION" in error.code for error in result.errors)
        )

    def test_get_validation_stats(self):
        """検証統計情報取得テスト"""
        stats = self.validator.get_validation_stats()

        self.assertIn("supported_versions", stats)
        self.assertIn("supported_message_types", stats)
        self.assertIn("supported_priorities", stats)
        self.assertIn("supported_statuses", stats)
        self.assertIn("strict_mode", stats)
        self.assertIn("validation_rules", stats)

        # 検証ルールの詳細チェック
        rules = stats["validation_rules"]
        self.assertIn("required_header_fields", rules)
        self.assertIn("required_payload_fields", rules)
        self.assertIn("uuid_pattern", rules)
        self.assertIn("agent_id_pattern", rules)


class TestStrictValidator(unittest.TestCase):
    """厳密モードバリデーターのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.strict_validator = ProtocolValidator(strict_mode=True)
        self.protocol = MessageProtocol()

    def test_strict_mode_enabled(self):
        """厳密モード有効化テスト"""
        self.assertTrue(self.strict_validator.strict_mode)

    def test_strict_mode_content_size_limit(self):
        """厳密モードコンテンツサイズ制限テスト"""
        # 大きなコンテンツを作成
        large_content = {"data": "x" * (1024 * 1024 + 1)}  # 1MB+1バイト

        payload = MessagePayload(content=large_content)

        result = self.strict_validator.validate_payload(payload)

        self.assertFalse(result.valid)
        self.assertTrue(
            any("CONTENT_TOO_LARGE" in error.code for error in result.errors)
        )


class TestDefaultValidators(unittest.TestCase):
    """デフォルトバリデーターのテスト"""

    def test_default_validator_exists(self):
        """デフォルトバリデーターの存在確認"""
        self.assertIsInstance(default_validator, ProtocolValidator)
        self.assertFalse(default_validator.strict_mode)

    def test_strict_validator_exists(self):
        """厳密バリデーターの存在確認"""
        self.assertIsInstance(strict_validator, ProtocolValidator)
        self.assertTrue(strict_validator.strict_mode)

    def test_default_validator_functionality(self):
        """デフォルトバリデーターの機能テスト"""
        protocol = MessageProtocol()
        message = protocol.create_message(
            message_type=MessageType.REQUEST,
            sender_id="test-sender",
            receiver_id="test-receiver",
            content={"test": "data"},
        )

        result = default_validator.validate_message(message)

        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)


if __name__ == "__main__":
    unittest.main()
