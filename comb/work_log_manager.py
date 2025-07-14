"""
Hive Comb Work Log Manager - 作業ログ管理システム

プロジェクトの作業履歴、進捗、技術的決定を記録・管理
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .file_handler import HiveFileHandler


class WorkLogManager:
    """作業ログ管理システム"""

    def __init__(self, file_handler: Optional[HiveFileHandler] = None) -> None:
        """
        初期化

        Args:
            file_handler: ファイルハンドラー
        """
        self.file_handler = file_handler or HiveFileHandler()
        self.file_handler.ensure_hive_structure()

        # 作業ログディレクトリ
        self.work_logs_dir = self.file_handler.get_path("work_logs")
        self.work_logs_dir.mkdir(exist_ok=True)

        # サブディレクトリ
        self.daily_dir = self.work_logs_dir / "daily"
        self.projects_dir = self.work_logs_dir / "projects"
        self.daily_dir.mkdir(exist_ok=True)
        self.projects_dir.mkdir(exist_ok=True)

        # 現在のタスク追跡
        self.current_task: Optional[dict[str, Any]] = None

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
            task_type: タスクタイプ（feature, bug, enhancement, etc.）
            description: タスク説明
            issue_number: GitHub Issue番号
            workers: 関与するWorkerリスト

        Returns:
            タスクID
        """
        task_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()

        self.current_task = {
            "id": task_id,
            "title": task_title,
            "type": task_type,
            "description": description,
            "issue_number": issue_number,
            "workers": workers or ["unknown"],
            "start_time": start_time.isoformat(),
            "end_time": None,
            "duration": None,
            "status": "in_progress",
            "progress": [],
            "technical_decisions": [],
            "challenges": [],
            "metrics": {},
            "files_modified": [],
        }

        # 日次ログに記録
        self._log_to_daily(f"🚀 **Task Started:** {task_title}")

        # プロジェクトログファイル作成
        if issue_number:
            project_file = self.projects_dir / f"issue-{issue_number}-{task_id}.md"
        else:
            project_file = self.projects_dir / f"task-{task_id}.md"

        self._create_project_log(project_file)

        return task_id

    def add_progress(self, description: str, details: Optional[str] = None) -> bool:
        """
        進捗を追加

        Args:
            description: 進捗説明
            details: 詳細情報

        Returns:
            追加成功時True
        """
        if not self.current_task:
            return False

        progress_entry = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "details": details,
        }

        self.current_task["progress"].append(progress_entry)

        # 日次ログに記録
        self._log_to_daily(f"📋 **Progress:** {description}")

        # プロジェクトログを更新
        self._update_project_log()

        return True

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
        if not self.current_task:
            return False

        decision_entry = {
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "reasoning": reasoning,
            "alternatives": alternatives or [],
        }

        self.current_task["technical_decisions"].append(decision_entry)

        # 日次ログに記録
        self._log_to_daily(f"🔧 **Technical Decision:** {decision}")

        # プロジェクトログを更新
        self._update_project_log()

        return True

    def add_challenge(self, challenge: str, solution: Optional[str] = None) -> bool:
        """
        課題と解決策を記録

        Args:
            challenge: 課題内容
            solution: 解決策

        Returns:
            記録成功時True
        """
        if not self.current_task:
            return False

        challenge_entry = {
            "timestamp": datetime.now().isoformat(),
            "challenge": challenge,
            "solution": solution,
        }

        self.current_task["challenges"].append(challenge_entry)

        # 日次ログに記録
        status = "🚧 **Challenge:**" if not solution else "✅ **Challenge Resolved:**"
        self._log_to_daily(f"{status} {challenge}")

        # プロジェクトログを更新
        self._update_project_log()

        return True

    def add_metrics(self, metrics: dict[str, Any]) -> bool:
        """
        メトリクスを追加

        Args:
            metrics: メトリクスデータ

        Returns:
            追加成功時True
        """
        if not self.current_task:
            return False

        self.current_task["metrics"].update(metrics)

        # 日次ログに記録
        metrics_str = ", ".join([f"{k}: {v}" for k, v in metrics.items()])
        self._log_to_daily(f"📊 **Metrics:** {metrics_str}")

        # プロジェクトログを更新
        self._update_project_log()

        return True

    def complete_task(self, result: str = "completed") -> bool:
        """
        タスクを完了

        Args:
            result: 完了結果

        Returns:
            完了処理成功時True
        """
        if not self.current_task:
            return False

        end_time = datetime.now()
        start_time = datetime.fromisoformat(self.current_task["start_time"])
        duration = end_time - start_time

        self.current_task["end_time"] = end_time.isoformat()
        self.current_task["duration"] = str(duration)
        self.current_task["status"] = result

        # 日次ログに記録
        self._log_to_daily(
            f"🎉 **Task Completed:** {self.current_task['title']} ({duration})"
        )

        # プロジェクトログを更新
        self._update_project_log()

        # タスクをクリア
        self.current_task = None

        return True

    def _log_to_daily(self, message: str) -> bool:
        """
        日次ログに記録

        Args:
            message: 記録するメッセージ

        Returns:
            記録成功時True
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            daily_file = self.daily_dir / f"{today}.md"

            # ファイルが存在しない場合はヘッダーを作成
            if not daily_file.exists():
                header = f"""# 🐝 Hive Work Log - {today}

Daily activity log

## 📅 Timeline

"""
                with open(daily_file, "w", encoding="utf-8") as f:
                    f.write(header)

            # タイムスタンプ付きでメッセージを追記
            timestamp = datetime.now().strftime("%H:%M:%S")
            entry = f"**{timestamp}** {message}\n\n"

            with open(daily_file, "a", encoding="utf-8") as f:
                f.write(entry)

            return True

        except Exception as e:
            print(f"Error logging to daily log: {e}")
            return False

    def _create_project_log(self, project_file: Path) -> bool:
        """
        プロジェクトログファイルを作成

        Args:
            project_file: プロジェクトファイルパス

        Returns:
            作成成功時True
        """
        try:
            if not self.current_task:
                return False

            content = self._generate_project_log_content()

            with open(project_file, "w", encoding="utf-8") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Error creating project log: {e}")
            return False

    def _update_project_log(self) -> bool:
        """
        プロジェクトログを更新

        Returns:
            更新成功時True
        """
        try:
            if not self.current_task:
                return False

            # プロジェクトファイルを特定
            issue_number = self.current_task.get("issue_number")
            task_id = self.current_task["id"]

            if issue_number:
                project_file = self.projects_dir / f"issue-{issue_number}-{task_id}.md"
            else:
                project_file = self.projects_dir / f"task-{task_id}.md"

            # コンテンツを更新
            content = self._generate_project_log_content()

            with open(project_file, "w", encoding="utf-8") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Error updating project log: {e}")
            return False

    def _generate_project_log_content(self) -> str:
        """
        プロジェクトログコンテンツを生成

        Returns:
            プロジェクトログコンテンツ
        """
        if not self.current_task:
            return ""

        task = self.current_task
        start_time = datetime.fromisoformat(task["start_time"])

        # ヘッダー
        lines = [
            f"# 🎯 {task['title']}",
            "",
            f"**Type:** {task['type']}",
            f"**Status:** {task['status']}",
            f"**Started:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if task["end_time"]:
            end_time = datetime.fromisoformat(task["end_time"])
            lines.append(f"**Completed:** {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"**Duration:** {task['duration']}")

        if task["issue_number"]:
            lines.append(f"**Issue:** #{task['issue_number']}")

        lines.extend(
            [
                f"**Workers:** {', '.join(task['workers'])}",
                "",
                "## 📝 Description",
                "",
                task["description"]
                if task["description"]
                else "*No description provided*",
                "",
            ]
        )

        # 進捗セクション
        if task["progress"]:
            lines.extend(["## 📋 Progress", ""])
            for progress in task["progress"]:
                timestamp = datetime.fromisoformat(progress["timestamp"])
                time_str = timestamp.strftime("%H:%M:%S")
                lines.append(f"- **{time_str}** {progress['description']}")
                if progress["details"]:
                    lines.append(f"  - {progress['details']}")
            lines.append("")

        # 技術的決定セクション
        if task["technical_decisions"]:
            lines.extend(["## 🔧 Technical Decisions", ""])
            for decision in task["technical_decisions"]:
                timestamp = datetime.fromisoformat(decision["timestamp"])
                time_str = timestamp.strftime("%H:%M:%S")
                lines.append(f"### {time_str} - {decision['decision']}")
                lines.append(f"**Reasoning:** {decision['reasoning']}")
                if decision["alternatives"]:
                    lines.append("**Alternatives considered:**")
                    for alt in decision["alternatives"]:
                        lines.append(f"- {alt}")
                lines.append("")

        # 課題セクション
        if task["challenges"]:
            lines.extend(["## 🚧 Challenges Encountered", ""])
            for challenge in task["challenges"]:
                timestamp = datetime.fromisoformat(challenge["timestamp"])
                time_str = timestamp.strftime("%H:%M:%S")
                lines.append(f"### {time_str} - {challenge['challenge']}")
                if challenge["solution"]:
                    lines.append(f"**Solution:** {challenge['solution']}")
                else:
                    lines.append("**Status:** Pending resolution")
                lines.append("")

        # メトリクスセクション
        if task["metrics"]:
            lines.extend(["## 📊 Metrics", ""])
            for key, value in task["metrics"].items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")

        # フッター
        lines.extend(
            ["---", f"*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"]
        )

        return "\n".join(lines)

    def get_current_task(self) -> Optional[dict[str, Any]]:
        """
        現在のタスク情報を取得

        Returns:
            現在のタスク情報
        """
        return self.current_task.copy() if self.current_task else None

    def get_work_log_stats(self) -> dict[str, Any]:
        """
        作業ログ統計を取得

        Returns:
            作業ログ統計情報
        """
        try:
            stats: dict[str, Any] = {
                "daily_logs": 0,
                "project_logs": 0,
                "total_size_kb": 0.0,
                "current_task": None,
            }

            # 日次ログ数
            daily_files = list(self.daily_dir.glob("*.md"))
            stats["daily_logs"] = len(daily_files)

            # プロジェクトログ数
            project_files = list(self.projects_dir.glob("*.md"))
            stats["project_logs"] = len(project_files)

            # 総サイズ
            total_size = 0
            for file in daily_files + project_files:
                total_size += file.stat().st_size
            stats["total_size_kb"] = float(total_size) / 1024.0

            # 現在のタスク
            if self.current_task:
                stats["current_task"] = {
                    "id": self.current_task["id"],
                    "title": self.current_task["title"],
                    "status": self.current_task["status"],
                    "start_time": self.current_task["start_time"],
                }

            return stats

        except Exception as e:
            print(f"Error getting work log stats: {e}")
            return {}
