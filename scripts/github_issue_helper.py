#!/usr/bin/env python3
"""
Hive GitHub Issue作成ヘルパー

Queen WorkerからGitHub Issue作成機能を簡単に使用するためのヘルパー関数群
"""

import logging
from datetime import datetime
from typing import Any

from create_github_issue import HiveGitHubIssueCreator


class HiveGitHubHelper:
    """Queen Worker向けGitHub Issue作成ヘルパー"""

    def __init__(self) -> None:
        """初期化"""
        self.creator = HiveGitHubIssueCreator()
        self.logger = logging.getLogger(__name__)

    def create_issue_from_hive_session(
        self,
        session_id: str,
        title: str,
        summary: str,
        details: str = "",
        actions: str = "",
        workers: list[str] | None = None,
        additional_data: dict[str, Any] | None = None,
    ) -> str | None:
        """
        Hiveセッションから直接GitHub Issue作成

        Args:
            session_id: セッションID
            title: Issueタイトル
            summary: 概要
            details: 詳細
            actions: 推奨アクション
            workers: 参加ワーカーリスト
            additional_data: 追加データ

        Returns:
            作成されたIssue URL（失敗時はNone）
        """
        # 検討結果データ構築
        result_data = {
            "session_id": session_id,
            "title": title,
            "summary": summary,
            "details": details,
            "actions": actions,
            "workers": workers or [],
            "timestamp": datetime.now().isoformat(),
            "duration": additional_data.get("duration", "") if additional_data else "",
            "worker_count": len(workers) if workers else 0,
            "proposal_count": additional_data.get("proposal_count", 0)
            if additional_data
            else 0,
            "item_count": additional_data.get("item_count", 0)
            if additional_data
            else 0,
            "related_resources": additional_data.get("related_resources", "")
            if additional_data
            else "",
            "completion_criteria": additional_data.get("completion_criteria", "")
            if additional_data
            else "",
            "additional_notes": additional_data.get("additional_notes", "")
            if additional_data
            else "",
            "impact": additional_data.get("impact", "") if additional_data else "",
        }

        # ワーカー別結果構築
        if additional_data and "worker_results" in additional_data:
            worker_results = self._format_worker_results(
                additional_data["worker_results"]
            )
            result_data["worker_results"] = worker_results

        return self.creator.create_issue(result_data)

    def _format_worker_results(self, worker_results: dict[str, Any]) -> str:
        """ワーカー別結果をMarkdown形式でフォーマット"""
        if not worker_results:
            return ""

        formatted_results = []

        for worker_name, result in worker_results.items():
            formatted_results.append(f"### {worker_name}")

            if isinstance(result, dict):
                if "summary" in result:
                    formatted_results.append(f"**概要:** {result['summary']}")
                if "details" in result:
                    formatted_results.append(f"**詳細:** {result['details']}")
                if "recommendations" in result:
                    formatted_results.append(
                        f"**推奨事項:** {result['recommendations']}"
                    )
                if "tasks" in result:
                    formatted_results.append("**タスク:**")
                    for task in result["tasks"]:
                        formatted_results.append(f"- {task}")
            else:
                formatted_results.append(str(result))

            formatted_results.append("")  # 空行

        return "\n".join(formatted_results)

    def create_issue_from_log_file(
        self, log_file_path: str, session_id: str
    ) -> str | None:
        """
        ログファイルからGitHub Issue作成

        Args:
            log_file_path: ログファイルパス
            session_id: セッションID

        Returns:
            作成されたIssue URL（失敗時はNone）
        """
        try:
            # ログファイル読み込み
            with open(log_file_path, encoding="utf-8") as f:
                log_content = f.read()

            # ログから情報抽出（簡易版）
            title = f"セッション {session_id} の検討結果"
            summary = self._extract_summary_from_log(log_content)
            details = self._extract_details_from_log(log_content)
            actions = self._extract_actions_from_log(log_content)
            workers = self._extract_workers_from_log(log_content)

            return self.create_issue_from_hive_session(
                session_id=session_id,
                title=title,
                summary=summary,
                details=details,
                actions=actions,
                workers=workers,
            )

        except Exception as e:
            self.logger.error(f"ログファイルからのIssue作成エラー: {e}")
            return None

    def _extract_summary_from_log(self, log_content: str) -> str:
        """ログから概要抽出"""
        # 簡易的な抽出ロジック
        lines = log_content.split("\n")
        summary_lines = []

        for line in lines:
            if any(
                keyword in line.lower() for keyword in ["summary", "概要", "まとめ"]
            ):
                summary_lines.append(line.strip())

        return "\n".join(summary_lines) if summary_lines else "ログから概要を抽出"

    def _extract_details_from_log(self, log_content: str) -> str:
        """ログから詳細抽出"""
        # 簡易的な抽出ロジック
        lines = log_content.split("\n")
        detail_lines = []

        for line in lines:
            if any(
                keyword in line.lower()
                for keyword in ["detail", "詳細", "analysis", "分析"]
            ):
                detail_lines.append(line.strip())

        return "\n".join(detail_lines) if detail_lines else "ログから詳細を抽出"

    def _extract_actions_from_log(self, log_content: str) -> str:
        """ログから推奨アクション抽出"""
        # 簡易的な抽出ロジック
        lines = log_content.split("\n")
        action_lines = []

        for line in lines:
            if any(
                keyword in line.lower()
                for keyword in ["action", "アクション", "todo", "task", "タスク"]
            ):
                action_lines.append(line.strip())

        return (
            "\n".join(action_lines) if action_lines else "ログから推奨アクションを抽出"
        )

    def _extract_workers_from_log(self, log_content: str) -> list[str]:
        """ログから参加ワーカー抽出"""
        # 簡易的な抽出ロジック
        workers = []
        lines = log_content.split("\n")

        for line in lines:
            if any(keyword in line.lower() for keyword in ["worker", "ワーカー"]):
                # より詳細な抽出ロジックを実装可能
                if "queen" in line.lower():
                    workers.append("Queen")
                if "developer" in line.lower():
                    workers.append("Developer")
                if "analyst" in line.lower():
                    workers.append("Analyst")

        return list(set(workers)) if workers else ["Unknown"]

    def preview_issue(
        self,
        session_id: str,
        title: str,
        summary: str,
        details: str = "",
        actions: str = "",
        workers: list[str] | None = None,
    ) -> None:
        """
        Issue作成のプレビュー表示

        Args:
            session_id: セッションID
            title: Issueタイトル
            summary: 概要
            details: 詳細
            actions: 推奨アクション
            workers: 参加ワーカーリスト
        """
        result_data = {
            "session_id": session_id,
            "title": title,
            "summary": summary,
            "details": details,
            "actions": actions,
            "workers": workers or [],
            "timestamp": datetime.now().isoformat(),
        }

        self.creator.create_issue(result_data, preview=True)

    def batch_create_issues(
        self, results_data: list[dict[str, Any]]
    ) -> list[str | None]:
        """
        複数のIssueを一括作成

        Args:
            results_data: 結果データのリスト

        Returns:
            作成されたIssue URLのリスト
        """
        issue_urls = []

        for i, result_data in enumerate(results_data):
            self.logger.info(f"Issue作成中 ({i + 1}/{len(results_data)})")

            issue_url = self.creator.create_issue(result_data)
            issue_urls.append(issue_url)

            if issue_url:
                self.logger.info(f"Issue作成完了: {issue_url}")
            else:
                self.logger.warning(
                    f"Issue作成失敗: {result_data.get('title', 'Unknown')}"
                )

        return issue_urls


def create_issue_from_queen_worker(
    session_id: str,
    title: str,
    summary: str,
    details: str = "",
    actions: str = "",
    workers: list[str] | None = None,
) -> str | None:
    """
    Queen WorkerからGitHub Issue作成（簡易関数）

    Args:
        session_id: セッションID
        title: Issueタイトル
        summary: 概要
        details: 詳細
        actions: 推奨アクション
        workers: 参加ワーカーリスト

    Returns:
        作成されたIssue URL（失敗時はNone）
    """
    helper = HiveGitHubHelper()
    return helper.create_issue_from_hive_session(
        session_id=session_id,
        title=title,
        summary=summary,
        details=details,
        actions=actions,
        workers=workers,
    )


def main() -> None:
    """テスト用メイン関数"""
    helper = HiveGitHubHelper()

    # テスト用のプレビュー
    helper.preview_issue(
        session_id="test_session_001",
        title="テスト検討結果",
        summary="これはテスト用の概要です",
        details="これはテスト用の詳細です",
        actions="これはテスト用のアクションです",
        workers=["Queen", "Developer"],
    )


if __name__ == "__main__":
    main()
