"""
Protocol Definition System Package

Issue #101: プロトコル定義システム実装
分散エージェント通信プロトコルの統一定義とバリデーション
"""

from .message_protocol import (
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
from .message_router_integration import (
    MessageRouterIntegration,
    default_integration,
)
from .protocol_validator import (
    ProtocolValidator,
    ValidationError,
    ValidationResult,
    default_validator,
    strict_validator,
)

__all__ = [
    # Message Protocol
    "MessageHeader",
    "MessagePayload",
    "MessagePriority",
    "MessageStatus",
    "MessageType",
    "ProtocolMessage",
    "ProtocolVersion",
    "MessageProtocol",
    "default_protocol",
    # Protocol Validator
    "ProtocolValidator",
    "ValidationError",
    "ValidationResult",
    "default_validator",
    "strict_validator",
    # Integration
    "MessageRouterIntegration",
    "default_integration",
]

__version__ = "1.0.0"
