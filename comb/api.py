"""
Hive Comb API - Worker向け通信API

Worker間通信の統一インターフェースを提供
"""

import threading
import time
from datetime import datetime
from typing import Any, Callable, Optional, Union

from .file_handler import HiveFileHandler
from .message_router import Message, MessagePriority, MessageRouter, MessageType
from .sync_manager import SyncManager
from .work_log_manager import WorkLogManager


class CombAPI:
    """Worker向け通信APIの統一インターフェース"""

    def __init__(
        self,
        worker_id: str,
        file_handler: Optional[HiveFileHandler] = None,
        message_router: Optional[MessageRouter] = None,
        sync_manager: Optional[SyncManager] = None,
        work_log_manager: Optional[WorkLogManager] = None,
        enable_markdown_logging: bool = True,
    ) -> None:
        """
        API初期化

        Args:
            worker_id: Worker識別子
            file_handler: ファイルハンドラー
            message_router: メッセージルーター
            sync_manager: 同期マネージャー
            work_log_manager: 作業ログマネージャー
            enable_markdown_logging: Markdownログ機能を有効化
        """
        self.worker_id = worker_id
        self.file_handler = file_handler or HiveFileHandler()
        self.message_router = message_router or MessageRouter(
            self.file_handler, enable_markdown_logging
        )
        self.sync_manager = sync_manager or SyncManager(self.file_handler)
        self.work_log_manager = work_log_manager or WorkLogManager(self.file_handler)

        # 初期化
        self.file_handler.ensure_hive_structure()

        # メッセージ処理ハンドラー
        self.message_handlers: dict[MessageType, Callable] = {}

        # ポーリング制御
        self._polling = False
        self._polling_thread: Optional[threading.Thread] = None
        self._polling_interval = 1.0  # seconds

    def send_message(
        self,
        to_worker: str,
        content: dict[str, Any],
        message_type: MessageType = MessageType.REQUEST,
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl_minutes: int = 60,
    ) -> bool:
        """
        メッセージ送信

        Args:
            to_worker: 送信先Worker ID
            content: メッセージ内容
            message_type: メッセージタイプ
            priority: 優先度
            ttl_minutes: TTL（分）

        Returns:
            送信成功時True
        """
        message = Message.create(
            from_worker=self.worker_id,
            to_worker=to_worker,
            message_type=message_type,
            content=content,
            priority=priority,
            ttl_minutes=ttl_minutes,
        )

        return self.message_router.send_message(message)

    def receive_messages(self) -> list[Message]:
        """
        メッセージ受信

        Returns:
            受信したメッセージのリスト
        """
        return self.message_router.receive_messages(self.worker_id)

    def send_response(
        self,
        original_message: Message,
        response_content: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> bool:
        """
        レスポンス送信

        Args:
            original_message: 元のメッセージ
            response_content: レスポンス内容
            priority: 優先度

        Returns:
            送信成功時True
        """
        return self.message_router.send_response(
            original_message, response_content, priority
        )

    def send_notification(
        self,
        to_worker: str,
        content: dict[str, Any],
        priority: Union[MessagePriority, str] = MessagePriority.NORMAL,
    ) -> bool:
        """
        通知送信

        Args:
            to_worker: 送信先Worker ID
            content: 通知内容
            priority: 優先度

        Returns:
            送信成功時True
        """
        # 文字列の場合は MessagePriority に変換
        if isinstance(priority, str):
            priority_map = {
                "low": MessagePriority.LOW,
                "normal": MessagePriority.NORMAL,
                "high": MessagePriority.HIGH,
                "urgent": MessagePriority.URGENT,
            }
            priority = priority_map.get(priority.lower(), MessagePriority.NORMAL)

        return self.message_router.send_notification(
            self.worker_id, to_worker, content, priority
        )

    def send_error(
        self,
        to_worker: str,
        error_message: str,
        error_details: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        エラー通知送信

        Args:
            to_worker: 送信先Worker ID
            error_message: エラーメッセージ
            error_details: エラー詳細

        Returns:
            送信成功時True
        """
        return self.message_router.send_error(
            self.worker_id, to_worker, error_message, error_details
        )

    def ping(self, to_worker: str) -> bool:
        """
        Pingメッセージ送信

        Args:
            to_worker: 送信先Worker ID

        Returns:
            送信成功時True
        """
        return self.send_message(
            to_worker=to_worker,
            content={"action": "ping", "timestamp": datetime.now().isoformat()},
            message_type=MessageType.REQUEST,
            priority=MessagePriority.LOW,
        )

    def pong(self, original_message: Message) -> bool:
        """
        Pongレスポンス送信

        Args:
            original_message: 元のPingメッセージ

        Returns:
            送信成功時True
        """
        return self.send_response(
            original_message=original_message,
            response_content={
                "action": "pong",
                "timestamp": datetime.now().isoformat(),
            },
            priority=MessagePriority.LOW,
        )

    # Nectar操作（タスク管理）
    def send_nectar(
        self, nectar_type: str, content: dict[str, Any], priority: str = "normal"
    ) -> bool:
        """
        Nectar（タスク）送信

        Args:
            nectar_type: Nectarタイプ
            content: タスク内容
            priority: 優先度

        Returns:
            送信成功時True
        """
        nectar_data = {
            "id": f"nectar_{int(time.time() * 1000)}",
            "type": nectar_type,
            "content": content,
            "priority": priority,
            "created_by": self.worker_id,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }

        nectar_file = self.file_handler.get_path(
            "nectar", "pending", f"{nectar_data['id']}.json"
        )

        return self.file_handler.write_json(nectar_file, nectar_data)

    def receive_nectar(self) -> Optional[dict[str, Any]]:
        """
        Nectar（タスク）受信

        Returns:
            受信したNectar、なければNone
        """
        pending_dir = self.file_handler.get_path("nectar", "pending")
        nectar_files = self.file_handler.list_files(pending_dir, "*.json")

        if not nectar_files:
            return None

        # 最初のNectarを取得
        nectar_file = nectar_files[0]
        nectar_data = self.file_handler.read_json(nectar_file)

        if nectar_data:
            # pendingからactiveに移動
            active_file = self.file_handler.get_path(
                "nectar", "active", nectar_file.name
            )

            nectar_data["status"] = "active"
            nectar_data["assigned_to"] = self.worker_id
            nectar_data["started_at"] = datetime.now().isoformat()

            if self.file_handler.write_json(active_file, nectar_data):
                self.file_handler.delete_file(nectar_file)
                return nectar_data

        return None

    def complete_nectar(self, nectar_id: str, result: dict[str, Any]) -> bool:
        """
        Nectar完了

        Args:
            nectar_id: Nectar ID
            result: 完了結果

        Returns:
            完了処理成功時True
        """
        active_file = self.file_handler.get_path(
            "nectar", "active", f"{nectar_id}.json"
        )

        nectar_data = self.file_handler.read_json(active_file)
        if not nectar_data:
            return False

        # 完了データ更新
        nectar_data["status"] = "completed"
        nectar_data["completed_by"] = self.worker_id
        nectar_data["completed_at"] = datetime.now().isoformat()
        nectar_data["result"] = result

        # activeからcompletedに移動
        completed_file = self.file_handler.get_path(
            "nectar", "completed", f"{nectar_id}.json"
        )

        if self.file_handler.write_json(completed_file, nectar_data):
            self.file_handler.delete_file(active_file)

            # Honeyとして結果を保存
            honey_file = self.file_handler.get_path("honey", f"{nectar_id}_result.json")
            self.file_handler.write_json(
                honey_file,
                {
                    "nectar_id": nectar_id,
                    "worker_id": self.worker_id,
                    "result": result,
                    "completed_at": nectar_data["completed_at"],
                },
            )

            return True

        return False

    # 同期操作
    def acquire_lock(self, resource_name: str, timeout: float = 10.0) -> bool:
        """
        リソースロック取得

        Args:
            resource_name: リソース名
            timeout: タイムアウト（秒）

        Returns:
            ロック取得成功時True
        """
        return self.sync_manager.acquire_lock(resource_name, self.worker_id, timeout)

    def release_lock(self, resource_name: str) -> bool:
        """
        リソースロック解放

        Args:
            resource_name: リソース名

        Returns:
            ロック解放成功時True
        """
        return self.sync_manager.release_lock(resource_name, self.worker_id)

    # メッセージハンドラー登録
    def register_handler(
        self, message_type: MessageType, handler: Callable[[Message], None]
    ) -> None:
        """
        メッセージハンドラー登録

        Args:
            message_type: 処理するメッセージタイプ
            handler: ハンドラー関数
        """
        self.message_handlers[message_type] = handler

    def start_polling(self, interval: float = 1.0) -> None:
        """
        メッセージポーリング開始

        Args:
            interval: ポーリング間隔（秒）
        """
        if self._polling:
            return

        self._polling = True
        self._polling_interval = interval
        self._polling_thread = threading.Thread(target=self._poll_messages)
        self._polling_thread.daemon = True
        self._polling_thread.start()

    def stop_polling(self) -> None:
        """メッセージポーリング停止"""
        self._polling = False
        if self._polling_thread:
            self._polling_thread.join()

    def _poll_messages(self) -> None:
        """メッセージポーリング処理"""
        while self._polling:
            try:
                messages = self.receive_messages()
                for message in messages:
                    handler = self.message_handlers.get(message.message_type)
                    if handler:
                        try:
                            handler(message)
                        except Exception as e:
                            print(f"Error in message handler: {e}")
                            # エラーレスポンス送信
                            self.send_error(
                                message.from_worker, f"Handler error: {str(e)}"
                            )

                time.sleep(self._polling_interval)

            except Exception as e:
                print(f"Error in polling: {e}")
                time.sleep(self._polling_interval)

    def get_status(self) -> dict[str, Any]:
        """
        Worker通信状況取得

        Returns:
            状況情報
        """
        message_stats = self.message_router.get_message_stats()
        lock_stats = self.sync_manager.get_lock_stats()

        work_log_stats = self.work_log_manager.get_work_log_stats()

        return {
            "worker_id": self.worker_id,
            "polling": self._polling,
            "messages": message_stats,
            "locks": lock_stats,
            "work_logs": work_log_stats,
            "timestamp": datetime.now().isoformat(),
        }

    # 作業ログ機能

    def start_task(
        self,
        task_title: str,
        task_type: str = "feature",
        description: str = "",
        issue_number: Optional[int] = None,
        workers: Optional[list[str]] = None,
    ) -> str:
        """
        タスクを開始

        Args:
            task_title: タスクタイトル
            task_type: タスクタイプ
            description: タスク説明
            issue_number: GitHub Issue番号
            workers: 関与するWorkerリスト

        Returns:
            タスクID
        """
        if workers is None:
            workers = [self.worker_id]

        return self.work_log_manager.start_task(
            task_title, task_type, description, issue_number, workers
        )

    def add_progress(self, description: str, details: Optional[str] = None) -> bool:
        """
        進捗を追加

        Args:
            description: 進捗説明
            details: 詳細情報

        Returns:
            追加成功時True
        """
        return self.work_log_manager.add_progress(description, details)

    def add_technical_decision(
        self, decision: str, reasoning: str, alternatives: Optional[list[str]] = None
    ) -> bool:
        """
        技術的決定を記録

        Args:
            decision: 決定内容
            reasoning: 決定理由
            alternatives: 検討した代替案

        Returns:
            記録成功時True
        """
        return self.work_log_manager.add_technical_decision(
            decision, reasoning, alternatives
        )

    def add_challenge(self, challenge: str, solution: Optional[str] = None) -> bool:
        """
        課題と解決策を記録

        Args:
            challenge: 課題内容
            solution: 解決策

        Returns:
            記録成功時True
        """
        return self.work_log_manager.add_challenge(challenge, solution)

    def add_metrics(self, metrics: dict[str, Any]) -> bool:
        """
        メトリクスを追加

        Args:
            metrics: メトリクスデータ

        Returns:
            追加成功時True
        """
        return self.work_log_manager.add_metrics(metrics)

    def complete_task(self, result: str = "completed") -> bool:
        """
        タスクを完了

        Args:
            result: 完了結果

        Returns:
            完了処理成功時True
        """
        return self.work_log_manager.complete_task(result)

    def get_current_task(self) -> Optional[dict[str, Any]]:
        """
        現在のタスク情報を取得

        Returns:
            現在のタスク情報
        """
        return self.work_log_manager.get_current_task()

    def generate_daily_summary(self) -> bool:
        """
        日次サマリーを生成

        Returns:
            生成成功時True
        """
        # 通信ログとワークログの両方でサマリー生成
        comm_success = True
        if self.message_router.markdown_logger:
            comm_success = self.message_router.markdown_logger.generate_daily_summary()

        return comm_success


def create_worker_api(worker_id: str) -> CombAPI:
    """
    Worker API作成のヘルパー関数

    Args:
        worker_id: Worker ID

    Returns:
        設定済みのCombAPI
    """
    return CombAPI(worker_id)
