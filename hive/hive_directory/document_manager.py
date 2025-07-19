"""
Document Manager

Hiveシステムでのドキュメント生成・管理機能を提供するモジュール
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DocumentManager:
    """
    ドキュメント生成・管理を行うクラス

    従来のdocs/ディレクトリではなく、.hive/docs/に出力することで
    プロジェクトのドキュメントとHiveが生成するドキュメントを分離
    """

    def __init__(self, hive_dir: Path):
        """
        Initialize DocumentManager

        Args:
            hive_dir: .hive/ディレクトリのパス
        """
        self.hive_dir = hive_dir
        self.docs_dir = hive_dir / "docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)

        # ドキュメントタイプ別ディレクトリ
        self.report_dir = self.docs_dir / "reports"
        self.analysis_dir = self.docs_dir / "analysis"
        self.design_dir = self.docs_dir / "design"
        self.meeting_dir = self.docs_dir / "meetings"

        # 初期化時にサブディレクトリを作成
        self._initialize_subdirectories()

    def _initialize_subdirectories(self) -> None:
        """
        サブディレクトリを作成
        """
        # サブディレクトリを作成
        for subdir in [
            self.report_dir,
            self.analysis_dir,
            self.design_dir,
            self.meeting_dir,
        ]:
            subdir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created docs subdirectory: {subdir}")

    def create_report(
        self,
        report_name: str,
        content: str,
        report_type: str = "general",
        session_id: str | None = None,
    ) -> Path:
        """
        レポートファイルを作成

        Args:
            report_name: レポート名
            content: レポート内容
            report_type: レポートタイプ (general, worker, task, error)
            session_id: 関連するセッションID

        Returns:
            Path: 作成されたファイルのパス
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self._sanitize_filename(report_name)
            filename = f"{timestamp}_{report_type}_{safe_name}.md"

            file_path = self.report_dir / filename

            # メタデータを含むコンテンツを生成
            full_content = self._add_metadata(
                content, report_name, report_type, session_id
            )

            file_path.write_text(full_content, encoding="utf-8")

            logger.info(f"Created report: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to create report {report_name}: {e}")
            raise

    def create_analysis_document(
        self, analysis_name: str, content: str, session_id: str | None = None
    ) -> Path:
        """
        分析ドキュメントを作成

        Args:
            analysis_name: 分析名
            content: 分析内容
            session_id: 関連するセッションID

        Returns:
            Path: 作成されたファイルのパス
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self._sanitize_filename(analysis_name)
            filename = f"{timestamp}_analysis_{safe_name}.md"

            file_path = self.analysis_dir / filename

            # メタデータを含むコンテンツを生成
            full_content = self._add_metadata(
                content, analysis_name, "analysis", session_id
            )

            file_path.write_text(full_content, encoding="utf-8")

            logger.info(f"Created analysis document: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to create analysis document {analysis_name}: {e}")
            raise

    def create_design_document(
        self, design_name: str, content: str, session_id: str | None = None
    ) -> Path:
        """
        設計ドキュメントを作成

        Args:
            design_name: 設計名
            content: 設計内容
            session_id: 関連するセッションID

        Returns:
            Path: 作成されたファイルのパス
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self._sanitize_filename(design_name)
            filename = f"{timestamp}_design_{safe_name}.md"

            file_path = self.design_dir / filename

            # メタデータを含むコンテンツを生成
            full_content = self._add_metadata(
                content, design_name, "design", session_id
            )

            file_path.write_text(full_content, encoding="utf-8")

            logger.info(f"Created design document: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to create design document {design_name}: {e}")
            raise

    def create_meeting_notes(
        self, meeting_name: str, content: str, session_id: str | None = None
    ) -> Path:
        """
        会議録を作成

        Args:
            meeting_name: 会議名
            content: 会議内容
            session_id: 関連するセッションID

        Returns:
            Path: 作成されたファイルのパス
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self._sanitize_filename(meeting_name)
            filename = f"{timestamp}_meeting_{safe_name}.md"

            file_path = self.meeting_dir / filename

            # メタデータを含むコンテンツを生成
            full_content = self._add_metadata(
                content, meeting_name, "meeting", session_id
            )

            file_path.write_text(full_content, encoding="utf-8")

            logger.info(f"Created meeting notes: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to create meeting notes {meeting_name}: {e}")
            raise

    def _add_metadata(
        self, content: str, title: str, doc_type: str, session_id: str | None
    ) -> str:
        """
        コンテンツにメタデータを追加

        Args:
            content: 元のコンテンツ
            title: ドキュメントタイトル
            doc_type: ドキュメントタイプ
            session_id: セッションID

        Returns:
            str: メタデータ付きコンテンツ
        """
        metadata = {
            "title": title,
            "type": doc_type,
            "created_at": datetime.now().isoformat(),
            "session_id": session_id,
            "generated_by": "Hive Document Manager",
        }

        metadata_yaml = "---\n"
        for key, value in metadata.items():
            if value is not None:
                metadata_yaml += f"{key}: {value}\n"
        metadata_yaml += "---\n\n"

        return metadata_yaml + content

    def _sanitize_filename(self, filename: str) -> str:
        """
        ファイル名を安全な形式にサニタイズ

        Args:
            filename: 元のファイル名

        Returns:
            str: サニタイズされたファイル名
        """
        # 危険な文字を置換
        import re

        safe_filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        safe_filename = re.sub(r"\s+", "_", safe_filename)
        safe_filename = safe_filename.strip("._")

        # 長すぎる場合は切り詰め
        if len(safe_filename) > 50:
            safe_filename = safe_filename[:50]

        return safe_filename

    def list_documents(self, doc_type: str | None = None) -> list[dict[str, Any]]:
        """
        ドキュメント一覧を取得

        Args:
            doc_type: フィルタするドキュメントタイプ (report, analysis, design, meeting)

        Returns:
            List[Dict[str, Any]]: ドキュメント一覧
        """
        documents = []

        try:
            search_dirs = {}
            if doc_type is None:
                search_dirs = {
                    "report": self.report_dir,
                    "analysis": self.analysis_dir,
                    "design": self.design_dir,
                    "meeting": self.meeting_dir,
                }
            else:
                if doc_type == "report":
                    search_dirs = {"report": self.report_dir}
                elif doc_type == "analysis":
                    search_dirs = {"analysis": self.analysis_dir}
                elif doc_type == "design":
                    search_dirs = {"design": self.design_dir}
                elif doc_type == "meeting":
                    search_dirs = {"meeting": self.meeting_dir}

            for dtype, directory in search_dirs.items():
                if directory.exists():
                    for file_path in directory.glob("*.md"):
                        try:
                            stat = file_path.stat()
                            doc_info = {
                                "name": file_path.name,
                                "path": str(file_path),
                                "type": dtype,
                                "size": stat.st_size,
                                "created_at": datetime.fromtimestamp(
                                    stat.st_ctime
                                ).isoformat(),
                                "modified_at": datetime.fromtimestamp(
                                    stat.st_mtime
                                ).isoformat(),
                            }
                            documents.append(doc_info)
                        except Exception as e:
                            logger.warning(
                                f"Failed to read file info for {file_path}: {e}"
                            )

            # 作成日時でソート
            documents.sort(key=lambda x: x["created_at"], reverse=True)

        except Exception as e:
            logger.error(f"Failed to list documents: {e}")

        return documents

    def delete_document(self, file_path: str | Path) -> bool:
        """
        ドキュメントを削除

        Args:
            file_path: ファイルパス

        Returns:
            bool: 削除成功の可否
        """
        try:
            path = Path(file_path)

            # セキュリティチェック: .hive/docs/ 配下のファイルのみ削除可能
            if not str(path).startswith(str(self.docs_dir)):
                logger.error(f"Attempted to delete file outside docs directory: {path}")
                return False

            if path.exists():
                path.unlink()
                logger.info(f"Deleted document: {path}")
                return True
            else:
                logger.warning(f"Document not found: {path}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete document {file_path}: {e}")
            return False

    def get_docs_summary(self) -> dict[str, Any]:
        """
        ドキュメント管理の概要を取得

        Returns:
            Dict[str, Any]: 概要情報
        """
        try:
            summary = {
                "docs_directory": str(self.docs_dir),
                "total_documents": 0,
                "by_type": {},
            }

            for doc_type in ["report", "analysis", "design", "meeting"]:
                documents = self.list_documents(doc_type)
                summary["by_type"][doc_type] = len(documents)
                summary["total_documents"] += len(documents)

            return summary

        except Exception as e:
            logger.error(f"Failed to get docs summary: {e}")
            return {"error": str(e)}

    def cleanup_old_documents(self, older_than_days: int) -> None:
        """
        古いドキュメントを削除

        Args:
            older_than_days: 削除対象とする日数
        """
        try:
            import time

            cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
            deleted_count = 0

            for doc_dir in [
                self.report_dir,
                self.analysis_dir,
                self.design_dir,
                self.meeting_dir,
            ]:
                if doc_dir.exists():
                    for doc_file in doc_dir.glob("*.md"):
                        try:
                            if doc_file.stat().st_mtime < cutoff_time:
                                doc_file.unlink()
                                deleted_count += 1
                                logger.debug(f"Deleted old document: {doc_file}")
                        except OSError as e:
                            logger.warning(f"Failed to delete {doc_file}: {e}")

            logger.info(
                f"Cleaned up {deleted_count} old documents (older than {older_than_days} days)"
            )

        except Exception as e:
            logger.error(f"Failed to cleanup old documents: {e}")
