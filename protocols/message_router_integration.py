"""
Message Router Integration

Issue #101: プロトコル定義システム実装
既存のMessageRouterと新しいプロトコルシステムの統合レイヤー
"""

import logging
from typing import Any

from comb.message_router import Message as LegacyMessage
from comb.message_router import MessagePriority as LegacyPriority
from comb.message_router import MessageRouter as LegacyRouter
from comb.message_router import MessageType as LegacyType

from .message_protocol import (
    MessagePriority,
    MessageProtocol,
    MessageType,
    ProtocolMessage,
    default_protocol,
)
from .protocol_validator import ProtocolValidator, ValidationResult, default_validator


class MessageRouterIntegration:
    """メッセージルーター統合クラス"""

    def __init__(
        self,
        protocol: MessageProtocol = default_protocol,
        validator: ProtocolValidator = default_validator,
        legacy_router: LegacyRouter | None = None,
    ):
        """
        初期化

        Args:
            protocol: 使用するプロトコル
            validator: 使用するバリデーター
            legacy_router: 既存のメッセージルーター
        """
        self.protocol = protocol
        self.validator = validator
        self.legacy_router = legacy_router or LegacyRouter()
        self.logger = logging.getLogger("protocol_integration")

        # メッセージタイプマッピング
        self.legacy_to_protocol_type = {
            LegacyType.REQUEST: MessageType.REQUEST,
            LegacyType.RESPONSE: MessageType.RESPONSE,
            LegacyType.NOTIFICATION: MessageType.NOTIFICATION,
            LegacyType.ERROR: MessageType.ERROR,
            LegacyType.NECTAR_DISTRIBUTION: MessageType.NECTAR_DISTRIBUTION,
            LegacyType.STATUS_REQUEST: MessageType.SYSTEM_STATUS,
            LegacyType.ALERT: MessageType.SYSTEM_ALERT,
            LegacyType.URGENT_NOTIFICATION: MessageType.URGENT_NOTIFICATION,
        }

        self.protocol_to_legacy_type = {
            v: k for k, v in self.legacy_to_protocol_type.items()
        }

        # 優先度マッピング
        self.legacy_to_protocol_priority = {
            LegacyPriority.LOW: MessagePriority.LOW,
            LegacyPriority.MEDIUM: MessagePriority.MEDIUM,
            LegacyPriority.HIGH: MessagePriority.HIGH,
            LegacyPriority.URGENT: MessagePriority.URGENT,
        }

        self.protocol_to_legacy_priority = {
            MessagePriority.LOW: LegacyPriority.LOW,
            MessagePriority.MEDIUM: LegacyPriority.MEDIUM,
            MessagePriority.HIGH: LegacyPriority.HIGH,
            MessagePriority.URGENT: LegacyPriority.URGENT,
            MessagePriority.CRITICAL: LegacyPriority.URGENT,  # CRITICALはURGENTにマップ
        }

    def send_protocol_message(self, message: ProtocolMessage) -> bool:
        """
        プロトコルメッセージを送信

        Args:
            message: 送信するプロトコルメッセージ

        Returns:
            送信成功時True
        """
        try:
            # メッセージを検証
            validation_result = self.validator.validate_message(message)
            if not validation_result.valid:
                self.logger.error(
                    f"Message validation failed: {validation_result.errors}"
                )
                return False

            # プロトコルメッセージを既存形式に変換
            legacy_message = self._convert_protocol_to_legacy(message)

            # 既存ルーターで送信
            return self.legacy_router.send_message(legacy_message)

        except Exception as e:
            self.logger.error(f"Error sending protocol message: {e}")
            return False

    def receive_protocol_messages(self, worker_id: str) -> list[ProtocolMessage]:
        """
        プロトコルメッセージを受信

        Args:
            worker_id: Worker ID

        Returns:
            受信したプロトコルメッセージリスト
        """
        try:
            # 既存ルーターからメッセージを受信
            legacy_messages = self.legacy_router.receive_messages(worker_id)

            # プロトコルメッセージに変換
            protocol_messages = []
            for legacy_msg in legacy_messages:
                try:
                    protocol_msg = self._convert_legacy_to_protocol(legacy_msg)

                    # 変換されたメッセージを検証
                    validation_result = self.validator.validate_message(protocol_msg)
                    if validation_result.valid:
                        protocol_messages.append(protocol_msg)
                    else:
                        self.logger.warning(
                            f"Invalid converted message {legacy_msg.id}: {validation_result.errors}"
                        )

                except Exception as e:
                    self.logger.error(
                        f"Error converting legacy message {legacy_msg.id}: {e}"
                    )
                    continue

            return protocol_messages

        except Exception as e:
            self.logger.error(f"Error receiving protocol messages: {e}")
            return []

    def send_task_assignment(
        self,
        sender_id: str,
        receiver_id: str,
        task_id: str,
        task_type: str,
        task_data: dict[str, Any],
        priority: MessagePriority = MessagePriority.MEDIUM,
    ) -> bool:
        """
        タスク割り当てメッセージを送信

        Args:
            sender_id: 送信者ID
            receiver_id: 受信者ID
            task_id: タスクID
            task_type: タスクタイプ
            task_data: タスクデータ
            priority: 優先度

        Returns:
            送信成功時True
        """
        message = self.protocol.create_task_assignment(
            sender_id=sender_id,
            receiver_id=receiver_id,
            task_id=task_id,
            task_type=task_type,
            task_data=task_data,
            priority=priority,
        )

        return self.send_protocol_message(message)

    def send_task_completion(
        self,
        sender_id: str,
        receiver_id: str,
        task_id: str,
        result: dict[str, Any],
        success: bool = True,
        error_message: str | None = None,
    ) -> bool:
        """
        タスク完了メッセージを送信

        Args:
            sender_id: 送信者ID
            receiver_id: 受信者ID
            task_id: タスクID
            result: 結果
            success: 成功フラグ
            error_message: エラーメッセージ

        Returns:
            送信成功時True
        """
        message = self.protocol.create_task_completion(
            sender_id=sender_id,
            receiver_id=receiver_id,
            task_id=task_id,
            result=result,
            success=success,
            error_message=error_message,
        )

        return self.send_protocol_message(message)

    def send_heartbeat(
        self,
        agent_id: str,
        status: dict[str, Any],
        broadcast: bool = False,
    ) -> bool:
        """
        ハートビートメッセージを送信

        Args:
            agent_id: エージェントID
            status: ステータス情報
            broadcast: ブロードキャストフラグ

        Returns:
            送信成功時True
        """
        message = self.protocol.create_heartbeat(
            agent_id=agent_id,
            status=status,
            broadcast=broadcast,
        )

        return self.send_protocol_message(message)

    def send_system_alert(
        self,
        sender_id: str,
        alert_type: str,
        alert_message: str,
        alert_data: dict[str, Any],
        severity: str = "warning",
    ) -> bool:
        """
        システムアラートメッセージを送信

        Args:
            sender_id: 送信者ID
            alert_type: アラートタイプ
            alert_message: アラートメッセージ
            alert_data: アラートデータ
            severity: 重要度

        Returns:
            送信成功時True
        """
        message = self.protocol.create_system_alert(
            sender_id=sender_id,
            alert_type=alert_type,
            alert_message=alert_message,
            alert_data=alert_data,
            severity=severity,
        )

        return self.send_protocol_message(message)

    def _convert_protocol_to_legacy(
        self, protocol_msg: ProtocolMessage
    ) -> LegacyMessage:
        """
        プロトコルメッセージを既存形式に変換

        Args:
            protocol_msg: プロトコルメッセージ

        Returns:
            既存形式のメッセージ
        """
        header = protocol_msg.header
        payload = protocol_msg.payload

        # メッセージタイプを変換
        legacy_type = self.protocol_to_legacy_type.get(
            header.message_type, LegacyType.NOTIFICATION
        )

        # 優先度を変換
        legacy_priority = self.protocol_to_legacy_priority.get(
            header.priority, LegacyPriority.MEDIUM
        )

        # 既存メッセージを作成
        legacy_message = LegacyMessage(
            id=header.message_id,
            from_worker=header.sender_id,
            to_worker=header.receiver_id,
            message_type=legacy_type,
            priority=legacy_priority,
            content=payload.content,
            timestamp=self._timestamp_to_iso(header.timestamp) or "",
            expires_at=self._timestamp_to_iso(header.expires_at)
            if header.expires_at
            else None,
            retry_count=header.retry_count,
            max_retries=header.max_retries,
        )

        return legacy_message

    def _convert_legacy_to_protocol(self, legacy_msg: LegacyMessage) -> ProtocolMessage:
        """
        既存メッセージをプロトコル形式に変換

        Args:
            legacy_msg: 既存メッセージ

        Returns:
            プロトコルメッセージ
        """
        # メッセージタイプを変換
        protocol_type = self.legacy_to_protocol_type.get(
            legacy_msg.message_type, MessageType.NOTIFICATION
        )

        # 優先度を変換
        protocol_priority = self.legacy_to_protocol_priority.get(
            legacy_msg.priority, MessagePriority.MEDIUM
        )

        # TTLを計算
        ttl_seconds = None
        if legacy_msg.expires_at:
            expires_timestamp = self._iso_to_timestamp(legacy_msg.expires_at)
            current_timestamp = self._iso_to_timestamp(legacy_msg.timestamp)
            ttl_seconds = int(expires_timestamp - current_timestamp)

        # プロトコルメッセージを作成
        protocol_message = self.protocol.create_message(
            message_type=protocol_type,
            sender_id=legacy_msg.from_worker,
            receiver_id=legacy_msg.to_worker,
            content=legacy_msg.content,
            priority=protocol_priority,
            ttl_seconds=ttl_seconds,
            max_retries=legacy_msg.max_retries,
        )

        # 既存のタイムスタンプとリトライ情報を設定
        protocol_message.header.timestamp = self._iso_to_timestamp(legacy_msg.timestamp)
        protocol_message.header.retry_count = legacy_msg.retry_count
        protocol_message.header.message_id = legacy_msg.id

        return protocol_message

    def _timestamp_to_iso(self, timestamp: float | None) -> str | None:
        """
        タイムスタンプをISO形式に変換

        Args:
            timestamp: タイムスタンプ

        Returns:
            ISO形式の文字列
        """
        if timestamp is None:
            return None

        from datetime import datetime

        return datetime.fromtimestamp(timestamp).isoformat()

    def _iso_to_timestamp(self, iso_string: str) -> float:
        """
        ISO形式の文字列をタイムスタンプに変換

        Args:
            iso_string: ISO形式の文字列

        Returns:
            タイムスタンプ
        """
        from datetime import datetime

        return datetime.fromisoformat(iso_string).timestamp()

    def get_integration_stats(self) -> dict[str, Any]:
        """
        統合統計情報を取得

        Returns:
            統合統計情報
        """
        legacy_stats = self.legacy_router.get_message_stats()
        protocol_info = self.protocol.get_protocol_info()
        validator_stats = self.validator.get_validation_stats()

        return {
            "legacy_router_stats": legacy_stats,
            "protocol_info": protocol_info,
            "validator_stats": validator_stats,
            "type_mappings": {
                "legacy_to_protocol": {
                    k.value: v.value for k, v in self.legacy_to_protocol_type.items()
                },
                "protocol_to_legacy": {
                    k.value: v.value for k, v in self.protocol_to_legacy_type.items()
                },
            },
            "priority_mappings": {
                "legacy_to_protocol": {
                    k.value: v.value
                    for k, v in self.legacy_to_protocol_priority.items()
                },
                "protocol_to_legacy": {
                    k.value: v.value
                    for k, v in self.protocol_to_legacy_priority.items()
                },
            },
        }

    def validate_integration(self) -> ValidationResult:
        """
        統合システムの検証

        Returns:
            検証結果
        """
        from .protocol_validator import ValidationError, ValidationResult

        result = ValidationResult()

        try:
            # 既存ルーターの動作確認
            if not self.legacy_router:
                result.add_error(
                    ValidationError(
                        "Legacy router not initialized",
                        field="legacy_router",
                        code="NOT_INITIALIZED",
                    )
                )

            # プロトコルの動作確認
            test_message = self.protocol.create_message(
                message_type=MessageType.REQUEST,
                sender_id="test-sender",
                receiver_id="test-receiver",
                content={"test": "integration"},
            )

            validation_result = self.validator.validate_message(test_message)
            if not validation_result.valid:
                result.add_error(
                    ValidationError(
                        "Protocol validation failed",
                        field="protocol",
                        code="VALIDATION_FAILED",
                    )
                )

            # 変換機能の確認
            legacy_message = self._convert_protocol_to_legacy(test_message)
            converted_back = self._convert_legacy_to_protocol(legacy_message)

            if test_message.header.message_type != converted_back.header.message_type:
                result.add_error(
                    ValidationError(
                        "Message type conversion failed",
                        field="conversion",
                        code="TYPE_CONVERSION_FAILED",
                    )
                )

            if test_message.header.priority != converted_back.header.priority:
                result.add_error(
                    ValidationError(
                        "Priority conversion failed",
                        field="conversion",
                        code="PRIORITY_CONVERSION_FAILED",
                    )
                )

        except Exception as e:
            result.add_error(
                ValidationError(
                    f"Integration validation error: {str(e)}",
                    field="integration",
                    code="VALIDATION_ERROR",
                )
            )

        return result


# デフォルト統合インスタンス
default_integration = MessageRouterIntegration()
