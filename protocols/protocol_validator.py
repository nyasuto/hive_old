"""
Protocol Validator System

Issue #101: プロトコル定義システム実装
メッセージプロトコルの検証とバージョン管理
"""

import re
import time
from typing import Any

from .message_protocol import (
    MessageHeader,
    MessagePayload,
    MessagePriority,
    MessageStatus,
    MessageType,
    ProtocolMessage,
    ProtocolVersion,
)


class ValidationError(Exception):
    """プロトコル検証エラー"""

    def __init__(self, message: str, field: str | None = None, code: str | None = None):
        super().__init__(message)
        self.field = field
        self.code = code


class ValidationResult:
    """検証結果"""

    def __init__(self, valid: bool = True, errors: list[ValidationError] | None = None):
        self.valid = valid
        self.errors = errors or []

    def add_error(self, error: ValidationError) -> None:
        """エラーを追加"""
        self.errors.append(error)
        self.valid = False

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "valid": self.valid,
            "errors": [
                {
                    "message": str(error),
                    "field": error.field,
                    "code": error.code,
                }
                for error in self.errors
            ],
        }


class ProtocolValidator:
    """プロトコル検証システム"""

    def __init__(self, strict_mode: bool = False):
        """
        初期化

        Args:
            strict_mode: 厳密モード（デフォルト: False）
        """
        self.strict_mode = strict_mode
        self.supported_versions = [v.value for v in ProtocolVersion]
        self.supported_message_types = [t.value for t in MessageType]
        self.supported_priorities = [p.value for p in MessagePriority]
        self.supported_statuses = [s.value for s in MessageStatus]

        # ID形式のパターン
        self.uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        self.agent_id_pattern = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

        # 必須フィールド定義
        self.required_header_fields = {
            "message_id",
            "protocol_version",
            "message_type",
            "priority",
            "timestamp",
            "sender_id",
            "receiver_id",
        }

        self.required_payload_fields = {
            "content",
        }

    def validate_message(self, message: ProtocolMessage) -> ValidationResult:
        """
        プロトコルメッセージを検証

        Args:
            message: 検証対象のメッセージ

        Returns:
            検証結果
        """
        result = ValidationResult()

        # ヘッダー検証
        header_result = self.validate_header(message.header)
        if not header_result.valid:
            result.errors.extend(header_result.errors)
            result.valid = False

        # ペイロード検証
        payload_result = self.validate_payload(message.payload)
        if not payload_result.valid:
            result.errors.extend(payload_result.errors)
            result.valid = False

        # ステータス検証
        status_result = self.validate_status(message.status)
        if not status_result.valid:
            result.errors.extend(status_result.errors)
            result.valid = False

        # メッセージタイプ固有の検証
        type_result = self.validate_message_type_specific(message)
        if not type_result.valid:
            result.errors.extend(type_result.errors)
            result.valid = False

        # 期限切れチェック
        if message.is_expired():
            result.add_error(
                ValidationError(
                    "Message has expired", field="expires_at", code="EXPIRED"
                )
            )

        return result

    def validate_header(self, header: MessageHeader) -> ValidationResult:
        """
        メッセージヘッダーを検証

        Args:
            header: 検証対象のヘッダー

        Returns:
            検証結果
        """
        result = ValidationResult()

        # 必須フィールドチェック
        header_dict = header.to_dict()
        for field in self.required_header_fields:
            if field not in header_dict or header_dict[field] is None:
                result.add_error(
                    ValidationError(
                        f"Required field '{field}' is missing or null",
                        field=field,
                        code="REQUIRED_FIELD_MISSING",
                    )
                )

        # message_id検証
        if not self.uuid_pattern.match(header.message_id):
            result.add_error(
                ValidationError(
                    "Invalid message_id format (must be UUID)",
                    field="message_id",
                    code="INVALID_FORMAT",
                )
            )

        # プロトコルバージョン検証
        if header.protocol_version not in self.supported_versions:
            result.add_error(
                ValidationError(
                    f"Unsupported protocol version: {header.protocol_version}",
                    field="protocol_version",
                    code="UNSUPPORTED_VERSION",
                )
            )

        # メッセージタイプ検証
        if header.message_type.value not in self.supported_message_types:
            result.add_error(
                ValidationError(
                    f"Unsupported message type: {header.message_type.value}",
                    field="message_type",
                    code="UNSUPPORTED_TYPE",
                )
            )

        # 優先度検証
        if header.priority.value not in self.supported_priorities:
            result.add_error(
                ValidationError(
                    f"Unsupported priority: {header.priority.value}",
                    field="priority",
                    code="UNSUPPORTED_PRIORITY",
                )
            )

        # タイムスタンプ検証
        if header.timestamp <= 0:
            result.add_error(
                ValidationError(
                    "Invalid timestamp (must be positive)",
                    field="timestamp",
                    code="INVALID_TIMESTAMP",
                )
            )

        # 未来のタイムスタンプチェック
        if header.timestamp > time.time() + 300:  # 5分の誤差を許容
            result.add_error(
                ValidationError(
                    "Timestamp is too far in the future",
                    field="timestamp",
                    code="FUTURE_TIMESTAMP",
                )
            )

        # エージェントID検証
        if not self.agent_id_pattern.match(header.sender_id):
            result.add_error(
                ValidationError(
                    "Invalid sender_id format",
                    field="sender_id",
                    code="INVALID_AGENT_ID",
                )
            )

        if (
            not self.agent_id_pattern.match(header.receiver_id)
            and header.receiver_id != "*"
        ):
            result.add_error(
                ValidationError(
                    "Invalid receiver_id format",
                    field="receiver_id",
                    code="INVALID_AGENT_ID",
                )
            )

        # 相関ID検証（存在する場合）
        # 相関IDはUUID形式またはタスクID形式を許可
        if header.correlation_id and not (
            self.uuid_pattern.match(header.correlation_id)
            or self.agent_id_pattern.match(header.correlation_id)
        ):
            result.add_error(
                ValidationError(
                    "Invalid correlation_id format (must be UUID or task ID)",
                    field="correlation_id",
                    code="INVALID_FORMAT",
                )
            )

        # リトライ検証
        if header.retry_count < 0:
            result.add_error(
                ValidationError(
                    "Invalid retry_count (must be non-negative)",
                    field="retry_count",
                    code="INVALID_RETRY_COUNT",
                )
            )

        if header.max_retries < 0:
            result.add_error(
                ValidationError(
                    "Invalid max_retries (must be non-negative)",
                    field="max_retries",
                    code="INVALID_MAX_RETRIES",
                )
            )

        if header.retry_count > header.max_retries:
            result.add_error(
                ValidationError(
                    "retry_count exceeds max_retries",
                    field="retry_count",
                    code="RETRY_EXCEEDED",
                )
            )

        # 期限検証
        if header.expires_at and header.expires_at <= header.timestamp:
            result.add_error(
                ValidationError(
                    "expires_at must be after timestamp",
                    field="expires_at",
                    code="INVALID_EXPIRY",
                )
            )

        return result

    def validate_payload(self, payload: MessagePayload) -> ValidationResult:
        """
        メッセージペイロードを検証

        Args:
            payload: 検証対象のペイロード

        Returns:
            検証結果
        """
        result = ValidationResult()

        # 必須フィールドチェック
        payload_dict = payload.to_dict()
        for field in self.required_payload_fields:
            if field not in payload_dict or payload_dict[field] is None:
                result.add_error(
                    ValidationError(
                        f"Required field '{field}' is missing or null",
                        field=field,
                        code="REQUIRED_FIELD_MISSING",
                    )
                )

        # コンテンツタイプ検証
        valid_content_types = [
            "application/json",
            "text/plain",
            "application/xml",
            "application/yaml",
        ]

        if payload.content_type not in valid_content_types:
            result.add_error(
                ValidationError(
                    f"Unsupported content type: {payload.content_type}",
                    field="content_type",
                    code="UNSUPPORTED_CONTENT_TYPE",
                )
            )

        # エンコーディング検証
        valid_encodings = ["utf-8", "utf-16", "ascii"]
        if payload.encoding not in valid_encodings:
            result.add_error(
                ValidationError(
                    f"Unsupported encoding: {payload.encoding}",
                    field="encoding",
                    code="UNSUPPORTED_ENCODING",
                )
            )

        # コンテンツ検証
        # Runtime validation for content type safety despite type annotations
        if not isinstance(payload.content, dict):
            result.add_error(  # type: ignore[unreachable]
                ValidationError(
                    "Content must be a dictionary",
                    field="content",
                    code="INVALID_CONTENT_TYPE",
                )
            )

        # 厳密モードでのコンテンツサイズ制限
        if self.strict_mode:
            content_str = str(payload.content)
            if len(content_str) > 1024 * 1024:  # 1MB制限
                result.add_error(
                    ValidationError(
                        "Content size exceeds 1MB limit",
                        field="content",
                        code="CONTENT_TOO_LARGE",
                    )
                )

        return result

    def validate_status(self, status: MessageStatus) -> ValidationResult:
        """
        メッセージステータスを検証

        Args:
            status: 検証対象のステータス

        Returns:
            検証結果
        """
        result = ValidationResult()

        if status.value not in self.supported_statuses:
            result.add_error(
                ValidationError(
                    f"Unsupported status: {status.value}",
                    field="status",
                    code="UNSUPPORTED_STATUS",
                )
            )

        return result

    def validate_message_type_specific(
        self, message: ProtocolMessage
    ) -> ValidationResult:
        """
        メッセージタイプ固有の検証

        Args:
            message: 検証対象のメッセージ

        Returns:
            検証結果
        """
        result = ValidationResult()

        message_type = message.header.message_type
        content = message.payload.content

        # タスク関連メッセージの検証
        if message_type == MessageType.TASK_ASSIGNMENT:
            required_fields = ["task_id", "task_type", "task_data"]
            for field in required_fields:
                if field not in content:
                    result.add_error(
                        ValidationError(
                            f"Task assignment missing required field: {field}",
                            field=field,
                            code="TASK_FIELD_MISSING",
                        )
                    )

        elif message_type == MessageType.TASK_COMPLETION:
            required_fields = ["task_id", "result", "success"]
            for field in required_fields:
                if field not in content:
                    result.add_error(
                        ValidationError(
                            f"Task completion missing required field: {field}",
                            field=field,
                            code="TASK_FIELD_MISSING",
                        )
                    )

            if "success" in content and not isinstance(content["success"], bool):
                result.add_error(
                    ValidationError(
                        "Task completion 'success' field must be boolean",
                        field="success",
                        code="INVALID_FIELD_TYPE",
                    )
                )

        # レスポンスメッセージの検証
        elif message_type == MessageType.RESPONSE:
            if "original_message_id" not in content:
                result.add_error(
                    ValidationError(
                        "Response message missing original_message_id",
                        field="original_message_id",
                        code="RESPONSE_FIELD_MISSING",
                    )
                )
            elif not self.uuid_pattern.match(content["original_message_id"]):
                result.add_error(
                    ValidationError(
                        "Response message has invalid original_message_id format",
                        field="original_message_id",
                        code="INVALID_FORMAT",
                    )
                )

        # ハートビートメッセージの検証
        elif message_type == MessageType.AGENT_HEARTBEAT:
            required_fields = ["agent_id", "status"]
            for field in required_fields:
                if field not in content:
                    result.add_error(
                        ValidationError(
                            f"Heartbeat message missing required field: {field}",
                            field=field,
                            code="HEARTBEAT_FIELD_MISSING",
                        )
                    )

        # システムアラートメッセージの検証
        elif message_type == MessageType.SYSTEM_ALERT:
            required_fields = ["alert_type", "alert_message", "severity"]
            for field in required_fields:
                if field not in content:
                    result.add_error(
                        ValidationError(
                            f"System alert missing required field: {field}",
                            field=field,
                            code="ALERT_FIELD_MISSING",
                        )
                    )

            if "severity" in content:
                valid_severities = ["info", "warning", "error", "critical"]
                if content["severity"] not in valid_severities:
                    result.add_error(
                        ValidationError(
                            f"Invalid alert severity: {content['severity']}",
                            field="severity",
                            code="INVALID_SEVERITY",
                        )
                    )

        return result

    def validate_batch(
        self, messages: list[ProtocolMessage]
    ) -> dict[str, ValidationResult]:
        """
        メッセージバッチを検証

        Args:
            messages: 検証対象のメッセージリスト

        Returns:
            メッセージIDをキーとした検証結果辞書
        """
        results = {}

        for message in messages:
            results[message.header.message_id] = self.validate_message(message)

        return results

    def validate_version_compatibility(
        self,
        sender_version: str,
        receiver_version: str,
    ) -> ValidationResult:
        """
        プロトコルバージョン互換性を検証

        Args:
            sender_version: 送信者のプロトコルバージョン
            receiver_version: 受信者のプロトコルバージョン

        Returns:
            検証結果
        """
        result = ValidationResult()

        # 両方のバージョンがサポートされているかチェック
        if sender_version not in self.supported_versions:
            result.add_error(
                ValidationError(
                    f"Unsupported sender version: {sender_version}",
                    field="sender_version",
                    code="UNSUPPORTED_VERSION",
                )
            )

        if receiver_version not in self.supported_versions:
            result.add_error(
                ValidationError(
                    f"Unsupported receiver version: {receiver_version}",
                    field="receiver_version",
                    code="UNSUPPORTED_VERSION",
                )
            )

        # 互換性チェック
        if not self._is_version_compatible(sender_version, receiver_version):
            result.add_error(
                ValidationError(
                    f"Version incompatibility: {sender_version} -> {receiver_version}",
                    field="version_compatibility",
                    code="VERSION_INCOMPATIBLE",
                )
            )

        return result

    def _is_version_compatible(
        self, sender_version: str, receiver_version: str
    ) -> bool:
        """
        バージョン互換性をチェック

        Args:
            sender_version: 送信者バージョン
            receiver_version: 受信者バージョン

        Returns:
            互換性がある場合True
        """
        # 同じバージョンは常に互換性がある
        if sender_version == receiver_version:
            return True

        # バージョン固有の互換性ルール
        compatibility_matrix = {
            ("1.0", "1.1"): True,
            ("1.1", "1.0"): True,
            ("1.0", "2.0"): False,
            ("2.0", "1.0"): False,
            ("1.1", "2.0"): False,
            ("2.0", "1.1"): False,
        }

        return compatibility_matrix.get((sender_version, receiver_version), False)

    def get_validation_stats(self) -> dict[str, Any]:
        """
        検証統計情報を取得

        Returns:
            検証統計情報
        """
        return {
            "supported_versions": self.supported_versions,
            "supported_message_types": self.supported_message_types,
            "supported_priorities": self.supported_priorities,
            "supported_statuses": self.supported_statuses,
            "strict_mode": self.strict_mode,
            "validation_rules": {
                "required_header_fields": list(self.required_header_fields),
                "required_payload_fields": list(self.required_payload_fields),
                "uuid_pattern": self.uuid_pattern.pattern,
                "agent_id_pattern": self.agent_id_pattern.pattern,
            },
        }


# デフォルトバリデーターインスタンス
default_validator = ProtocolValidator()
strict_validator = ProtocolValidator(strict_mode=True)
