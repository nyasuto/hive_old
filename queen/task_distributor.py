"""
Nectar Task Distribution System

Issue #4の実装: Nectarタスク管理システムの配布機能
Queen WorkerがDeveloper Workerにタスクを効率的に配布するシステム
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from comb.api import CombAPI
from comb.message_router import MessagePriority, MessageType


class Priority(Enum):
    """タスクの優先度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(Enum):
    """タスクの状態"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Nectar:
    """
    Nectarタスクの構造体

    Issue #4の要件に基づいたNectarフォーマット
    """
    nectar_id: str
    title: str
    description: str
    assigned_to: str
    created_by: str
    priority: Priority
    status: TaskStatus
    dependencies: list[str]
    expected_honey: list[str]
    estimated_time: int  # 時間単位
    created_at: datetime
    deadline: datetime
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        # Enumを文字列に変換
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        # datetimeを文字列に変換
        data['created_at'] = self.created_at.isoformat()
        data['deadline'] = self.deadline.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Nectar':
        """辞書から作成"""
        # Enumに変換
        data['priority'] = Priority(data['priority'])
        data['status'] = TaskStatus(data['status'])
        # datetimeに変換
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['deadline'] = datetime.fromisoformat(data['deadline'])
        return cls(**data)


class TaskDistributor:
    """
    Nectar配布システム

    Queen WorkerがDeveloper Workerにタスクを配布する機能を提供
    """

    def __init__(self, queen_worker_id: str = "queen"):
        self.queen_worker_id = queen_worker_id
        self.comb_api = CombAPI(queen_worker_id)
        self.logger = logging.getLogger(__name__)

        # Nectar保存ディレクトリ
        self.nectar_dir = Path(".hive/nectar")
        self.nectar_dir.mkdir(parents=True, exist_ok=True)

        # サブディレクトリ
        self.pending_dir = self.nectar_dir / "pending"
        self.active_dir = self.nectar_dir / "active"
        self.completed_dir = self.nectar_dir / "completed"
        self.failed_dir = self.nectar_dir / "failed"

        for dir_path in [self.pending_dir, self.active_dir, self.completed_dir, self.failed_dir]:
            dir_path.mkdir(exist_ok=True)

    def create_nectar(
        self,
        title: str,
        description: str,
        assigned_to: str,
        priority: Priority = Priority.MEDIUM,
        estimated_time: int = 4,
        deadline_hours: int = 24,
        dependencies: list[str] | None = None,
        expected_honey: list[str] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> Nectar:
        """
        新しいNectarタスクを作成

        Args:
            title: タスクのタイトル
            description: 詳細な作業内容
            assigned_to: 担当Workerの ID
            priority: タスクの優先度
            estimated_time: 推定作業時間（時間）
            deadline_hours: 期限（時間後）
            dependencies: 依存するNectar ID一覧
            expected_honey: 期待される成果物一覧
            tags: タグ一覧
            metadata: 追加のメタデータ

        Returns:
            作成されたNectarオブジェクト
        """
        # ユニークなNectar ID生成
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        nectar_id = f"nectar-{timestamp}-{unique_id}"

        # デフォルト値の設定
        if dependencies is None:
            dependencies = []
        if expected_honey is None:
            expected_honey = [f"{title}の実装完了"]
        if tags is None:
            tags = []
        if metadata is None:
            metadata = {}

        # Nectar作成
        nectar = Nectar(
            nectar_id=nectar_id,
            title=title,
            description=description,
            assigned_to=assigned_to,
            created_by=self.queen_worker_id,
            priority=priority,
            status=TaskStatus.PENDING,
            dependencies=dependencies,
            expected_honey=expected_honey,
            estimated_time=estimated_time,
            created_at=datetime.now(),
            deadline=datetime.now() + timedelta(hours=deadline_hours),
            tags=tags,
            metadata=metadata
        )

        # ファイルシステムに保存
        self._save_nectar(nectar)

        self.logger.info(f"Created nectar: {nectar_id} for {assigned_to}")
        return nectar

    def distribute_nectar(self, nectar: Nectar) -> bool:
        """
        Nectarを担当Workerに配布

        Args:
            nectar: 配布するNectar

        Returns:
            配布成功フラグ
        """
        try:
            # 依存関係チェック
            if not self._check_dependencies(nectar):
                self.logger.warning(f"Dependencies not satisfied for {nectar.nectar_id}")
                return False

            # 担当Workerに配布メッセージ送信
            message_content = {
                "nectar_id": nectar.nectar_id,
                "title": nectar.title,
                "description": nectar.description,
                "priority": nectar.priority.value,
                "estimated_time": nectar.estimated_time,
                "deadline": nectar.deadline.isoformat(),
                "expected_honey": nectar.expected_honey,
                "dependencies": nectar.dependencies,
                "tags": nectar.tags,
                "metadata": nectar.metadata
            }

            # Comb通信でNectar配布
            self.comb_api.send_message(
                to_worker=nectar.assigned_to,
                content=message_content,
                message_type=MessageType.NECTAR_DISTRIBUTION,
                priority=self._convert_priority(nectar.priority)
            )

            # ステータスをACTIVEに変更
            nectar.status = TaskStatus.ACTIVE
            self._move_nectar(nectar, self.pending_dir, self.active_dir)

            self.logger.info(f"Distributed nectar {nectar.nectar_id} to {nectar.assigned_to}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to distribute nectar {nectar.nectar_id}: {e}")
            return False

    def batch_distribute(self, worker_id: str, max_tasks: int = 3) -> list[str]:
        """
        Worker向けのバッチ配布

        Args:
            worker_id: 配布先Worker ID
            max_tasks: 最大配布数

        Returns:
            配布されたNectar ID一覧
        """
        distributed_nectars = []

        # 利用可能なNectar取得（優先度順）
        available_nectars = self.get_pending_nectars(worker_id)
        available_nectars.sort(key=lambda n: (n.priority.value, n.deadline))

        # 現在のアクティブタスク数チェック
        active_count = len(self.get_active_nectars(worker_id))

        for nectar in available_nectars[:max_tasks - active_count]:
            if self.distribute_nectar(nectar):
                distributed_nectars.append(nectar.nectar_id)

        self.logger.info(f"Batch distributed {len(distributed_nectars)} nectars to {worker_id}")
        return distributed_nectars

    def get_pending_nectars(self, worker_id: str | None = None) -> list[Nectar]:
        """保留中のNectar一覧取得"""
        return self._load_nectars_from_dir(self.pending_dir, worker_id)

    def get_active_nectars(self, worker_id: str | None = None) -> list[Nectar]:
        """アクティブなNectar一覧取得"""
        return self._load_nectars_from_dir(self.active_dir, worker_id)

    def get_completed_nectars(self, worker_id: str | None = None) -> list[Nectar]:
        """完了したNectar一覧取得"""
        return self._load_nectars_from_dir(self.completed_dir, worker_id)

    def get_nectar_by_id(self, nectar_id: str) -> Nectar | None:
        """Nectar ID指定でNectar取得"""
        for directory in [self.pending_dir, self.active_dir, self.completed_dir, self.failed_dir]:
            nectar_file = directory / f"{nectar_id}.json"
            if nectar_file.exists():
                return self._load_nectar(nectar_file)
        return None

    def update_nectar_status(self, nectar_id: str, status: TaskStatus) -> bool:
        """Nectarステータス更新"""
        nectar = self.get_nectar_by_id(nectar_id)
        if not nectar:
            return False

        old_status = nectar.status
        nectar.status = status

        # ディレクトリ間の移動
        source_dir = self._get_status_dir(old_status)
        target_dir = self._get_status_dir(status)

        if source_dir != target_dir:
            self._move_nectar(nectar, source_dir, target_dir)
        else:
            self._save_nectar(nectar)

        self.logger.info(f"Updated nectar {nectar_id} status: {old_status.value} → {status.value}")
        return True

    def get_worker_workload(self, worker_id: str) -> dict[str, Any]:
        """Worker別ワークロード取得"""
        active_nectars = self.get_active_nectars(worker_id)
        pending_nectars = self.get_pending_nectars(worker_id)

        total_estimated_time = sum(n.estimated_time for n in active_nectars + pending_nectars)

        return {
            "worker_id": worker_id,
            "active_tasks": len(active_nectars),
            "pending_tasks": len(pending_nectars),
            "total_estimated_time": total_estimated_time,
            "tasks_by_priority": self._get_priority_breakdown(active_nectars + pending_nectars),
            "average_deadline": self._calculate_average_deadline(active_nectars + pending_nectars)
        }

    def redistribute_failed_nectar(self, nectar_id: str, new_worker_id: str) -> bool:
        """失敗したNectarの再配布"""
        nectar = self.get_nectar_by_id(nectar_id)
        if not nectar or nectar.status != TaskStatus.FAILED:
            return False

        # 新しいWorkerに再配布
        nectar.assigned_to = new_worker_id
        nectar.status = TaskStatus.PENDING

        # ファイルシステムで移動
        self._move_nectar(nectar, self.failed_dir, self.pending_dir)

        self.logger.info(f"Redistributed failed nectar {nectar_id} to {new_worker_id}")
        return True

    def _save_nectar(self, nectar: Nectar) -> None:
        """Nectarをファイルシステムに保存"""
        status_dir = self._get_status_dir(nectar.status)
        nectar_file = status_dir / f"{nectar.nectar_id}.json"

        with open(nectar_file, 'w', encoding='utf-8') as f:
            json.dump(nectar.to_dict(), f, ensure_ascii=False, indent=2)

    def _load_nectar(self, nectar_file: Path) -> Nectar:
        """ファイルからNectarロード"""
        with open(nectar_file, encoding='utf-8') as f:
            data = json.load(f)
        return Nectar.from_dict(data)

    def _load_nectars_from_dir(self, directory: Path, worker_id: str | None = None) -> list[Nectar]:
        """ディレクトリからNectar一覧ロード"""
        nectars = []
        for nectar_file in directory.glob("*.json"):
            nectar = self._load_nectar(nectar_file)
            if worker_id is None or nectar.assigned_to == worker_id:
                nectars.append(nectar)
        return nectars

    def _move_nectar(self, nectar: Nectar, source_dir: Path, target_dir: Path) -> None:
        """NectarをディレクトリAからディレクトリBに移動"""
        source_file = source_dir / f"{nectar.nectar_id}.json"
        target_file = target_dir / f"{nectar.nectar_id}.json"

        # 新しい場所に保存
        self._save_nectar(nectar)

        # 古いファイルを削除
        if source_file.exists() and source_file != target_file:
            source_file.unlink()

    def _get_status_dir(self, status: TaskStatus) -> Path:
        """ステータスに対応するディレクトリ取得"""
        if status == TaskStatus.PENDING:
            return self.pending_dir
        elif status == TaskStatus.ACTIVE:
            return self.active_dir
        elif status == TaskStatus.COMPLETED:
            return self.completed_dir
        elif status == TaskStatus.FAILED:
            return self.failed_dir
        else:
            return self.pending_dir

    def _check_dependencies(self, nectar: Nectar) -> bool:
        """依存関係チェック"""
        for dep_id in nectar.dependencies:
            dep_nectar = self.get_nectar_by_id(dep_id)
            if not dep_nectar or dep_nectar.status != TaskStatus.COMPLETED:
                return False
        return True

    def _convert_priority(self, priority: Priority) -> MessagePriority:
        """Priority → MessagePriorityの変換"""
        mapping = {
            Priority.LOW: MessagePriority.LOW,
            Priority.MEDIUM: MessagePriority.MEDIUM,
            Priority.HIGH: MessagePriority.HIGH,
            Priority.CRITICAL: MessagePriority.HIGH
        }
        return mapping.get(priority, MessagePriority.MEDIUM)

    def _get_priority_breakdown(self, nectars: list[Nectar]) -> dict[str, int]:
        """優先度別の内訳取得"""
        breakdown = {p.value: 0 for p in Priority}
        for nectar in nectars:
            breakdown[nectar.priority.value] += 1
        return breakdown

    def _calculate_average_deadline(self, nectars: list[Nectar]) -> str | None:
        """平均期限の計算"""
        if not nectars:
            return None

        total_seconds = sum((n.deadline - datetime.now()).total_seconds() for n in nectars)
        average_seconds = total_seconds / len(nectars)
        average_deadline = datetime.now() + timedelta(seconds=average_seconds)

        return average_deadline.isoformat()
