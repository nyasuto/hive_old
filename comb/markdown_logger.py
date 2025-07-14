"""
Hive Comb Markdown Logger - Markdown形式での通信ログ機能

Worker間の通信を人間とAIにとって読みやすいMarkdown形式で記録
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .file_handler import HiveFileHandler

if TYPE_CHECKING:
    from .message_router import Message


class MarkdownLogger:
    """Markdown形式での通信ログ管理"""

    def __init__(self, file_handler: HiveFileHandler | None = None) -> None:
        """
        初期化

        Args:
            file_handler: ファイルハンドラー
        """
        self.file_handler = file_handler or HiveFileHandler()
        self.file_handler.ensure_hive_structure()

        # 通信ログディレクトリ
        self.comm_logs_dir = self.file_handler.get_path("comb", "communication_logs")
        self.comm_logs_dir.mkdir(exist_ok=True)

        # 日次ディレクトリ
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_dir = self.comm_logs_dir / today
        self.daily_dir.mkdir(exist_ok=True)

    def log_message(self, message: "Message") -> bool:
        """
        メッセージをMarkdown形式でログ記録

        Args:
            message: 記録するメッセージ

        Returns:
            記録成功時True
        """
        try:
            # ログファイル名生成
            log_filename = f"{message.from_worker}_{message.to_worker}.md"
            log_file = self.daily_dir / log_filename

            # Markdownエントリ生成
            markdown_entry = self._generate_markdown_entry(message)

            # ファイルに追記
            return self._append_to_log_file(log_file, markdown_entry)

        except Exception as e:
            print(f"Error logging message to Markdown: {e}")
            return False

    def _generate_markdown_entry(self, message: "Message") -> str:
        """
        メッセージからMarkdownエントリを生成

        Args:
            message: 変換するメッセージ

        Returns:
            Markdownエントリ文字列
        """
        timestamp = datetime.fromisoformat(message.timestamp)
        formatted_time = timestamp.strftime("%H:%M:%S")

        # 優先度の絵文字マッピング
        priority_emoji = {"LOW": "🟢", "NORMAL": "🔵", "HIGH": "🟠", "URGENT": "🔴"}

        # メッセージタイプの絵文字マッピング
        type_emoji = {
            "request": "❓",
            "response": "✅",
            "notification": "📢",
            "error": "❌",
        }

        # コンテンツの整形
        content_md = self._format_content(message.content)

        markdown_entry = f"""
## {type_emoji.get(message.message_type.value, "📝")} {message.message_type.value.title()}

### {message.from_worker} → {message.to_worker}
**Time:** {formatted_time}
**Priority:** {priority_emoji.get(message.priority.name, "⚪")} {message.priority.name}
**Message ID:** `{message.id}`

{content_md}

---

"""
        return markdown_entry

    def _format_content(self, content: dict[str, Any]) -> str:
        """
        メッセージコンテンツをMarkdown形式に整形

        Args:
            content: メッセージコンテンツ

        Returns:
            整形されたMarkdown文字列
        """
        if not content:
            return "*(Empty message)*"

        # 特殊なコンテンツタイプの処理
        if "action" in content:
            action = content["action"]
            if action == "ping":
                return "🏓 **Ping** - Health check request"
            elif action == "pong":
                return "🏓 **Pong** - Health check response"

        # 通常のコンテンツ処理
        formatted_lines = []
        for key, value in content.items():
            if isinstance(value, dict):
                formatted_lines.append(f"**{key.title()}:**")
                for sub_key, sub_value in value.items():
                    formatted_lines.append(f"  - {sub_key}: `{sub_value}`")
            elif isinstance(value, list):
                formatted_lines.append(f"**{key.title()}:**")
                for item in value:
                    formatted_lines.append(f"  - {item}")
            else:
                formatted_lines.append(f"**{key.title()}:** {value}")

        return "\n".join(formatted_lines)

    def _append_to_log_file(self, log_file: Path, content: str) -> bool:
        """
        ログファイルにコンテンツを追記

        Args:
            log_file: ログファイルパス
            content: 追記するコンテンツ

        Returns:
            成功時True
        """
        try:
            # ファイルが存在しない場合はヘッダーを作成
            if not log_file.exists():
                today = datetime.now().strftime("%Y-%m-%d")
                header = f"""# 🐝 Hive Communication Log - {today}

Worker間通信の記録

"""
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write(header)

            # コンテンツを追記
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Error appending to log file {log_file}: {e}")
            return False

    def generate_daily_summary(self) -> bool:
        """
        日次サマリーを生成

        Returns:
            生成成功時True
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            summary_file = self.daily_dir / f"summary_{today}.md"

            # 当日のログファイル一覧取得
            log_files = list(self.daily_dir.glob("*.md"))
            log_files = [f for f in log_files if not f.name.startswith("summary_")]

            if not log_files:
                return True  # ログがない場合は正常終了

            # サマリー生成
            summary_content = self._generate_summary_content(log_files)

            # サマリーファイル作成
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(summary_content)

            return True

        except Exception as e:
            print(f"Error generating daily summary: {e}")
            return False

    def _generate_summary_content(self, log_files: list[Path]) -> str:
        """
        サマリーコンテンツを生成

        Args:
            log_files: ログファイルリスト

        Returns:
            サマリーコンテンツ
        """
        today = datetime.now().strftime("%Y-%m-%d")
        summary_lines = [
            f"# 📊 Daily Communication Summary - {today}",
            "",
            "## 📈 Overview",
            f"**Total Communication Files:** {len(log_files)}",
            "",
            "## 📁 Communication Files",
            "",
        ]

        for log_file in sorted(log_files):
            file_size = log_file.stat().st_size
            file_size_kb = file_size / 1024
            worker_pair = log_file.stem.replace("_", " ↔ ")
            summary_lines.append(f"- **{worker_pair}** (`{file_size_kb:.1f}KB`)")

        summary_lines.extend(["", "## 🔍 Quick Access", ""])

        for log_file in sorted(log_files):
            relative_path = log_file.name
            worker_pair = log_file.stem.replace("_", " ↔ ")
            summary_lines.append(f"- [{worker_pair}](./{relative_path})")

        summary_lines.extend(
            ["", f"*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"]
        )

        return "\n".join(summary_lines)

    def cleanup_old_logs(self, days_to_keep: int = 7) -> int:
        """
        古いログファイルをクリーンアップ

        Args:
            days_to_keep: 保持日数

        Returns:
            削除したファイル数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0

            for date_dir in self.comm_logs_dir.iterdir():
                if not date_dir.is_dir():
                    continue

                try:
                    dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                    if dir_date < cutoff_date:
                        # ディレクトリ内のファイルを削除
                        for file in date_dir.glob("*"):
                            file.unlink()
                            deleted_count += 1
                        # 空のディレクトリを削除
                        date_dir.rmdir()
                except ValueError:
                    # 日付形式でないディレクトリは無視
                    continue

            return deleted_count

        except Exception as e:
            print(f"Error cleaning up old logs: {e}")
            return 0

    def get_communication_stats(self) -> dict[str, Any]:
        """
        通信統計を取得

        Returns:
            通信統計情報
        """
        try:
            stats = {
                "total_log_files": 0,
                "total_size_kb": 0,
                "worker_pairs": [],
                "daily_directories": 0,
            }

            # 日次ディレクトリ数
            date_dirs = [d for d in self.comm_logs_dir.iterdir() if d.is_dir()]
            stats["daily_directories"] = len(date_dirs)

            # 当日のログファイル統計
            log_files = list(self.daily_dir.glob("*.md"))
            log_files = [f for f in log_files if not f.name.startswith("summary_")]

            stats["total_log_files"] = len(log_files)

            total_size = 0
            worker_pairs = set()

            for log_file in log_files:
                file_size = log_file.stat().st_size
                total_size += file_size
                worker_pairs.add(log_file.stem)

            stats["total_size_kb"] = total_size / 1024
            stats["worker_pairs"] = sorted(worker_pairs)

            return stats

        except Exception as e:
            print(f"Error getting communication stats: {e}")
            return {}
