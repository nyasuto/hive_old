"""
Hive Comb Message Router - メッセージルーティングシステム

Worker間のメッセージ配信、優先度管理、リトライ機能を提供
"""

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from .file_handler import HiveFileHandler


class MessageType(Enum):
    """メッセージタイプ"""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MessagePriority(Enum):
    """メッセージ優先度"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """メッセージデータ構造"""

    id: str
    from_worker: str
    to_worker: str
    message_type: MessageType
    priority: MessagePriority
    content: dict[str, Any]
    timestamp: str
    expires_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    @classmethod
    def create(
        cls,
        from_worker: str,
        to_worker: str,
        message_type: MessageType,
        content: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl_minutes: int = 60,
        max_retries: int = 3,
    ) -> "Message":
        """
        新しいメッセージを作成

        Args:
            from_worker: 送信元Worker ID
            to_worker: 送信先Worker ID
            message_type: メッセージタイプ
            content: メッセージ内容
            priority: 優先度
            ttl_minutes: TTL（分）
            max_retries: 最大リトライ回数

        Returns:
            作成されたメッセージ
        """
        now = datetime.now()
        expires_at = now + timedelta(minutes=ttl_minutes)

        return cls(
            id=str(uuid.uuid4()),
            from_worker=from_worker,
            to_worker=to_worker,
            message_type=message_type,
            priority=priority,
            content=content,
            timestamp=now.isoformat(),
            expires_at=expires_at.isoformat(),
            max_retries=max_retries,
        )

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        data["priority"] = self.priority.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """辞書から復元"""
        data["message_type"] = MessageType(data["message_type"])
        data["priority"] = MessagePriority(data["priority"])
        return cls(**data)

    def is_expired(self) -> bool:
        """メッセージが期限切れかチェック"""
        if not self.expires_at:
            return False
        return datetime.now() > datetime.fromisoformat(self.expires_at)

    def can_retry(self) -> bool:
        """リトライ可能かチェック"""
        return self.retry_count < self.max_retries and not self.is_expired()


class MessageRouter:
    """メッセージルーティング管理"""

    def __init__(
        self,
        file_handler: Optional[HiveFileHandler] = None,
        enable_markdown_logging: bool = True,
    ) -> None:
        """
        初期化

        Args:
            file_handler: ファイルハンドラー（デフォルト: default_handler）
            enable_markdown_logging: Markdownログ機能を有効化
        """
        self.file_handler = file_handler or HiveFileHandler()
        self.file_handler.ensure_hive_structure()

        # Markdownログ機能 (遅延インポート)
        self.markdown_logger = None
        if enable_markdown_logging:
            from .markdown_logger import MarkdownLogger

            self.markdown_logger = MarkdownLogger(self.file_handler)

        # メッセージディレクトリ
        self.messages_dir = self.file_handler.get_path("comb", "messages")
        self.inbox_dir = self.messages_dir / "inbox"
        self.outbox_dir = self.messages_dir / "outbox"
        self.pending_dir = self.messages_dir / "pending"
        self.sent_dir = self.messages_dir / "sent"
        self.failed_dir = self.messages_dir / "failed"

        # ディレクトリ作成
        for directory in [
            self.inbox_dir,
            self.outbox_dir,
            self.pending_dir,
            self.sent_dir,
            self.failed_dir,
        ]:
            directory.mkdir(exist_ok=True)

    def send_message(self, message: Message) -> bool:
        """
        メッセージを送信

        Args:
            message: 送信するメッセージ

        Returns:
            送信成功時True、失敗時False
        """
        try:
            # メッセージをoutboxに保存
            outbox_file = self.outbox_dir / f"{message.id}.json"
            success = self.file_handler.write_json(outbox_file, message.to_dict())

            if success:
                # 受信者のinboxにもコピー
                inbox_file = self.inbox_dir / f"{message.to_worker}_{message.id}.json"
                self.file_handler.write_json(inbox_file, message.to_dict())

                # outboxからsentに移動
                sent_file = self.sent_dir / f"{message.id}.json"
                self.file_handler.move_file(outbox_file, sent_file)

                # Markdownログに記録
                if self.markdown_logger:
                    self.markdown_logger.log_message(message)

                return True
            return False

        except Exception as e:
            print(f"Error sending message {message.id}: {e}")
            return False

    def receive_messages(self, worker_id: str) -> list[Message]:
        """
        指定されたWorkerのメッセージを受信

        Args:
            worker_id: Worker ID

        Returns:
            受信したメッセージのリスト（優先度順）
        """
        messages = []

        try:
            # inboxから該当Workerのメッセージを取得
            pattern = f"{worker_id}_*.json"
            message_files = self.file_handler.list_files(self.inbox_dir, pattern)

            for message_file in message_files:
                data = self.file_handler.read_json(message_file)
                if data:
                    try:
                        message = Message.from_dict(data)

                        # 期限切れチェック
                        if message.is_expired():
                            self.file_handler.delete_file(message_file)
                            continue

                        messages.append(message)

                        # 受信完了したファイルを削除
                        self.file_handler.delete_file(message_file)

                    except Exception as e:
                        print(f"Error parsing message {message_file}: {e}")
                        continue

            # 優先度順にソート（高優先度が先）
            messages.sort(key=lambda m: m.priority.value, reverse=True)

            return messages

        except Exception as e:
            print(f"Error receiving messages for {worker_id}: {e}")
            return []

    def send_response(
        self,
        original_message: Message,
        response_content: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> bool:
        """
        レスポンスメッセージを送信

        Args:
            original_message: 元のメッセージ
            response_content: レスポンス内容
            priority: 優先度

        Returns:
            送信成功時True、失敗時False
        """
        response = Message.create(
            from_worker=original_message.to_worker,
            to_worker=original_message.from_worker,
            message_type=MessageType.RESPONSE,
            content={
                "original_message_id": original_message.id,
                "response": response_content,
            },
            priority=priority,
        )

        return self.send_message(response)

    def send_notification(
        self,
        from_worker: str,
        to_worker: str,
        content: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> bool:
        """
        通知メッセージを送信

        Args:
            from_worker: 送信元Worker ID
            to_worker: 送信先Worker ID
            content: 通知内容
            priority: 優先度

        Returns:
            送信成功時True、失敗時False
        """
        notification = Message.create(
            from_worker=from_worker,
            to_worker=to_worker,
            message_type=MessageType.NOTIFICATION,
            content=content,
            priority=priority,
        )

        return self.send_message(notification)

    def send_error(
        self,
        from_worker: str,
        to_worker: str,
        error_message: str,
        error_details: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        エラーメッセージを送信

        Args:
            from_worker: 送信元Worker ID
            to_worker: 送信先Worker ID
            error_message: エラーメッセージ
            error_details: エラー詳細

        Returns:
            送信成功時True、失敗時False
        """
        error = Message.create(
            from_worker=from_worker,
            to_worker=to_worker,
            message_type=MessageType.ERROR,
            content={"error": error_message, "details": error_details or {}},
            priority=MessagePriority.HIGH,
        )

        return self.send_message(error)

    def retry_failed_messages(self) -> int:
        """
        失敗したメッセージのリトライを実行

        Returns:
            リトライしたメッセージ数
        """
        retry_count = 0

        try:
            failed_files = self.file_handler.list_files(self.failed_dir, "*.json")

            for failed_file in failed_files:
                data = self.file_handler.read_json(failed_file)
                if data:
                    try:
                        message = Message.from_dict(data)

                        if message.can_retry():
                            message.retry_count += 1

                            # リトライ実行
                            if self.send_message(message):
                                self.file_handler.delete_file(failed_file)
                                retry_count += 1
                            else:
                                # リトライも失敗
                                self.file_handler.write_json(
                                    failed_file, message.to_dict()
                                )
                        else:
                            # リトライ不可、削除
                            self.file_handler.delete_file(failed_file)

                    except Exception as e:
                        print(f"Error retrying message {failed_file}: {e}")
                        continue

        except Exception as e:
            print(f"Error during retry process: {e}")

        return retry_count

    def cleanup_expired_messages(self) -> int:
        """
        期限切れメッセージをクリーンアップ

        Returns:
            クリーンアップしたメッセージ数
        """
        cleanup_count = 0

        for directory in [self.inbox_dir, self.outbox_dir, self.pending_dir]:
            try:
                message_files = self.file_handler.list_files(directory, "*.json")

                for message_file in message_files:
                    data = self.file_handler.read_json(message_file)
                    if data:
                        try:
                            message = Message.from_dict(data)
                            if message.is_expired():
                                self.file_handler.delete_file(message_file)
                                cleanup_count += 1
                        except Exception:
                            # パース失敗したファイルも削除
                            self.file_handler.delete_file(message_file)
                            cleanup_count += 1

            except Exception as e:
                print(f"Error cleaning up {directory}: {e}")

        return cleanup_count

    def get_message_stats(self) -> dict[str, int]:
        """
        メッセージ統計を取得

        Returns:
            メッセージ統計情報
        """
        stats = {}

        for name, directory in [
            ("inbox", self.inbox_dir),
            ("outbox", self.outbox_dir),
            ("pending", self.pending_dir),
            ("sent", self.sent_dir),
            ("failed", self.failed_dir),
        ]:
            try:
                files = self.file_handler.list_files(directory, "*.json")
                stats[name] = len(files)
            except Exception:
                stats[name] = 0

        return stats


# モジュールレベルのデフォルトインスタンス
default_router = MessageRouter()
