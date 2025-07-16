"""
Message Protocol Definition System

Issue #101: プロトコル定義システム実装
分散エージェント通信用の統一プロトコル定義
"""

import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ProtocolVersion(Enum):
    """プロトコルバージョン"""

    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"
    CURRENT = "1.1"  # 現在のバージョン


class MessageType(Enum):
    """統一メッセージタイプ"""

    # 基本メッセージ
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

    # タスク管理
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETION = "task_completion"
    TASK_STATUS = "task_status"
    TASK_CANCEL = "task_cancel"

    # 分散エージェント通信
    AGENT_HEARTBEAT = "agent_heartbeat"
    AGENT_REGISTRATION = "agent_registration"
    AGENT_DISCOVERY = "agent_discovery"
    AGENT_SHUTDOWN = "agent_shutdown"

    # システム管理
    SYSTEM_STATUS = "system_status"
    SYSTEM_COMMAND = "system_command"
    SYSTEM_ALERT = "system_alert"

    # 特殊メッセージ
    NECTAR_DISTRIBUTION = "nectar_distribution"
    URGENT_NOTIFICATION = "urgent_notification"


class MessagePriority(Enum):
    """メッセージ優先度"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class MessageStatus(Enum):
    """メッセージステータス"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class MessageHeader:
    """メッセージヘッダー"""

    message_id: str
    protocol_version: str
    message_type: MessageType
    priority: MessagePriority
    timestamp: float
    sender_id: str
    receiver_id: str
    correlation_id: str | None = None
    reply_to: str | None = None
    expires_at: float | None = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "message_id": self.message_id,
            "protocol_version": self.protocol_version,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "expires_at": self.expires_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessageHeader":
        """辞書から復元"""
        return cls(
            message_id=data["message_id"],
            protocol_version=data["protocol_version"],
            message_type=MessageType(data["message_type"]),
            priority=MessagePriority(data["priority"]),
            timestamp=data["timestamp"],
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            expires_at=data.get("expires_at"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )


@dataclass
class MessagePayload:
    """メッセージペイロード"""

    content: dict[str, Any]
    content_type: str = "application/json"
    encoding: str = "utf-8"
    checksum: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "content": self.content,
            "content_type": self.content_type,
            "encoding": self.encoding,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessagePayload":
        """辞書から復元"""
        return cls(
            content=data["content"],
            content_type=data.get("content_type", "application/json"),
            encoding=data.get("encoding", "utf-8"),
            checksum=data.get("checksum"),
        )


@dataclass
class ProtocolMessage:
    """統一プロトコルメッセージ"""

    header: MessageHeader
    payload: MessagePayload
    status: MessageStatus = MessageStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "header": self.header.to_dict(),
            "payload": self.payload.to_dict(),
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProtocolMessage":
        """辞書から復元"""
        return cls(
            header=MessageHeader.from_dict(data["header"]),
            payload=MessagePayload.from_dict(data["payload"]),
            status=MessageStatus(data.get("status", MessageStatus.PENDING.value)),
        )

    def is_expired(self) -> bool:
        """メッセージが期限切れかチェック"""
        if not self.header.expires_at:
            return False
        return time.time() > self.header.expires_at

    def can_retry(self) -> bool:
        """リトライ可能かチェック"""
        return (
            self.header.retry_count < self.header.max_retries
            and not self.is_expired()
            and self.status in [MessageStatus.PENDING, MessageStatus.FAILED]
        )

    def increment_retry(self) -> None:
        """リトライ回数を増加"""
        self.header.retry_count += 1
        self.status = MessageStatus.PENDING

    def mark_processing(self) -> None:
        """処理中にマーク"""
        self.status = MessageStatus.PROCESSING

    def mark_completed(self) -> None:
        """完了にマーク"""
        self.status = MessageStatus.COMPLETED

    def mark_failed(self) -> None:
        """失敗にマーク"""
        self.status = MessageStatus.FAILED

    def mark_cancelled(self) -> None:
        """キャンセルにマーク"""
        self.status = MessageStatus.CANCELLED


class MessageProtocol:
    """メッセージプロトコル管理クラス"""

    def __init__(self, protocol_version: ProtocolVersion = ProtocolVersion.CURRENT):
        self.protocol_version = protocol_version
        self.supported_versions = [v.value for v in ProtocolVersion]

    def create_message(
        self,
        message_type: MessageType,
        sender_id: str,
        receiver_id: str,
        content: dict[str, Any],
        priority: MessagePriority = MessagePriority.MEDIUM,
        correlation_id: str | None = None,
        reply_to: str | None = None,
        ttl_seconds: int | None = None,
        max_retries: int = 3,
    ) -> ProtocolMessage:
        """
        プロトコルメッセージを作成

        Args:
            message_type: メッセージタイプ
            sender_id: 送信者ID
            receiver_id: 受信者ID
            content: メッセージ内容
            priority: 優先度
            correlation_id: 相関ID
            reply_to: 返信先
            ttl_seconds: TTL（秒）
            max_retries: 最大リトライ回数

        Returns:
            作成されたプロトコルメッセージ
        """
        now = time.time()
        expires_at = now + ttl_seconds if ttl_seconds else None

        header = MessageHeader(
            message_id=str(uuid.uuid4()),
            protocol_version=self.protocol_version.value,
            message_type=message_type,
            priority=priority,
            timestamp=now,
            sender_id=sender_id,
            receiver_id=receiver_id,
            correlation_id=correlation_id,
            reply_to=reply_to,
            expires_at=expires_at,
            max_retries=max_retries,
        )

        payload = MessagePayload(content=content)

        return ProtocolMessage(header=header, payload=payload)

    def create_response(
        self,
        original_message: ProtocolMessage,
        response_content: dict[str, Any],
        priority: MessagePriority = MessagePriority.MEDIUM,
    ) -> ProtocolMessage:
        """
        レスポンスメッセージを作成

        Args:
            original_message: 元のメッセージ
            response_content: レスポンス内容
            priority: 優先度

        Returns:
            作成されたレスポンスメッセージ
        """
        return self.create_message(
            message_type=MessageType.RESPONSE,
            sender_id=original_message.header.receiver_id,
            receiver_id=original_message.header.sender_id,
            content={
                "original_message_id": original_message.header.message_id,
                "response": response_content,
            },
            priority=priority,
            correlation_id=original_message.header.correlation_id,
        )

    def create_task_assignment(
        self,
        sender_id: str,
        receiver_id: str,
        task_id: str,
        task_type: str,
        task_data: dict[str, Any],
        priority: MessagePriority = MessagePriority.MEDIUM,
        deadline: float | None = None,
    ) -> ProtocolMessage:
        """
        タスク割り当てメッセージを作成

        Args:
            sender_id: 送信者ID
            receiver_id: 受信者ID
            task_id: タスクID
            task_type: タスクタイプ
            task_data: タスクデータ
            priority: 優先度
            deadline: 期限

        Returns:
            作成されたタスク割り当てメッセージ
        """
        return self.create_message(
            message_type=MessageType.TASK_ASSIGNMENT,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content={
                "task_id": task_id,
                "task_type": task_type,
                "task_data": task_data,
                "deadline": deadline,
            },
            priority=priority,
            correlation_id=task_id,
        )

    def create_task_completion(
        self,
        sender_id: str,
        receiver_id: str,
        task_id: str,
        result: dict[str, Any],
        success: bool = True,
        error_message: str | None = None,
    ) -> ProtocolMessage:
        """
        タスク完了メッセージを作成

        Args:
            sender_id: 送信者ID
            receiver_id: 受信者ID
            task_id: タスクID
            result: 結果
            success: 成功フラグ
            error_message: エラーメッセージ

        Returns:
            作成されたタスク完了メッセージ
        """
        return self.create_message(
            message_type=MessageType.TASK_COMPLETION,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content={
                "task_id": task_id,
                "result": result,
                "success": success,
                "error_message": error_message,
            },
            priority=MessagePriority.HIGH,
            correlation_id=task_id,
        )

    def create_heartbeat(
        self,
        agent_id: str,
        status: dict[str, Any],
        broadcast: bool = False,
        receiver_id: str = "*",
    ) -> ProtocolMessage:
        """
        ハートビートメッセージを作成

        Args:
            agent_id: エージェントID
            status: ステータス情報
            broadcast: ブロードキャストフラグ
            receiver_id: 受信者ID（ブロードキャスト時は"*"）

        Returns:
            作成されたハートビートメッセージ
        """
        return self.create_message(
            message_type=MessageType.AGENT_HEARTBEAT,
            sender_id=agent_id,
            receiver_id=receiver_id,
            content={
                "agent_id": agent_id,
                "status": status,
                "broadcast": broadcast,
            },
            priority=MessagePriority.LOW,
            ttl_seconds=60,  # ハートビートは1分で期限切れ
        )

    def create_system_alert(
        self,
        sender_id: str,
        alert_type: str,
        alert_message: str,
        alert_data: dict[str, Any],
        severity: str = "warning",
        broadcast: bool = True,
    ) -> ProtocolMessage:
        """
        システムアラートメッセージを作成

        Args:
            sender_id: 送信者ID
            alert_type: アラートタイプ
            alert_message: アラートメッセージ
            alert_data: アラートデータ
            severity: 重要度
            broadcast: ブロードキャストフラグ

        Returns:
            作成されたシステムアラートメッセージ
        """
        priority = (
            MessagePriority.CRITICAL if severity == "critical" else MessagePriority.HIGH
        )

        return self.create_message(
            message_type=MessageType.SYSTEM_ALERT,
            sender_id=sender_id,
            receiver_id="*" if broadcast else sender_id,
            content={
                "alert_type": alert_type,
                "alert_message": alert_message,
                "alert_data": alert_data,
                "severity": severity,
                "broadcast": broadcast,
            },
            priority=priority,
        )

    def is_version_supported(self, version: str) -> bool:
        """
        プロトコルバージョンがサポートされているかチェック

        Args:
            version: バージョン文字列

        Returns:
            サポートされている場合True
        """
        return version in self.supported_versions

    def get_protocol_info(self) -> dict[str, Any]:
        """
        プロトコル情報を取得

        Returns:
            プロトコル情報
        """
        return {
            "current_version": self.protocol_version.value,
            "supported_versions": self.supported_versions,
            "supported_message_types": [t.value for t in MessageType],
            "supported_priorities": [p.value for p in MessagePriority],
            "supported_statuses": [s.value for s in MessageStatus],
        }


# デフォルトプロトコルインスタンス
default_protocol = MessageProtocol()
