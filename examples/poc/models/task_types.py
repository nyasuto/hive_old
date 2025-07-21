"""
Task type definitions for Issue Solver Agent system.

Extracted from issue_solver_agent.py for better modularity.
"""

from enum import Enum


class TaskStatus(Enum):
    """タスクステータス"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskComplexity(Enum):
    """タスク複雑度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
