"""
Hive Comb Module - ファイルベース通信システム

このモジュールはWorker間の通信機能を提供します：
- api.py - Worker向け通信API
- file_handler.py - ファイル操作
- message_router.py - メッセージルーティング
- sync_manager.py - 同期管理
- markdown_logger.py - Markdown形式通信ログ
- work_log_manager.py - 作業ログ管理
"""

__version__ = "0.1.0"

# Public API exports
from .api import CombAPI, create_worker_api
from .file_handler import HiveFileHandler
from .markdown_logger import MarkdownLogger
from .message_router import Message, MessagePriority, MessageRouter, MessageType
from .sync_manager import SyncManager
from .work_log_manager import WorkLogManager

__all__ = [
    "CombAPI",
    "create_worker_api",
    "HiveFileHandler",
    "MessageRouter",
    "Message",
    "MessageType",
    "MessagePriority",
    "SyncManager",
    "MarkdownLogger",
    "WorkLogManager",
]
