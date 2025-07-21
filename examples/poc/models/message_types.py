"""
Message type definitions for Issue Solver Agent system.

Extracted from issue_solver_agent.py for better modularity.
"""

from enum import Enum


class MessageType(Enum):
    """メッセージタイプ"""

    REQUEST = "request"
    RESPONSE = "response"
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETION = "task_completion"
    SYSTEM_ALERT = "system_alert"


class MessagePriority(Enum):
    """メッセージ優先度"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5
