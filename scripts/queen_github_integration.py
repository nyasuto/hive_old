#!/usr/bin/env python3
"""
Queen Worker用 GitHub統合ヘルパー

Queen WorkerからGitHub Issue-PR統合機能を簡単に使用するためのラッパー関数群
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from github_issue_pr_integration import HiveGitHubIntegration


class QueenGitHubIntegration:
    """Queen Worker専用 GitHub統合ヘルパー"""

    def __init__(self):
        """初期化"""
        self.integration = HiveGitHubIntegration()
        self.logger = logging.getLogger(__name__)

    def process_hive_analysis_to_github(
        self,
        session_id: str,
        analysis_result: dict[str, Any],
        auto_create_pr: bool = True,
    ) -> dict[str, Any]:
        """
        Hive分析結果をGitHub Issue-PRワークフローで処理

        Args:
            session_id: セッションID
            analysis_result: Hive分析結果
            auto_create_pr: PR自動作成フラグ

        Returns:
            処理結果辞書
        """
        self.logger.info(f"Queen Worker: GitHub統合処理開始 - {session_id}")

        try:
            if auto_create_pr:
                # 統合ワークフロー実行
                issue_url, pr_url = (
                    self.integration.create_issue_implementation_workflow(
                        session_id, analysis_result
                    )
                )

                result = {
                    "success": True,
                    "session_id": session_id,
                    "issue_url": issue_url,
                    "pr_url": pr_url,
                    "workflow_type": "full_integration",
                    "created_at": datetime.now().isoformat(),
                    "message": "Issue-PR統合ワークフロー完了",
                }
            else:
                # Issue作成のみ
                issue_url = self.integration._create_issue_from_analysis(
                    session_id, analysis_result
                )

                result = {
                    "success": True,
                    "session_id": session_id,
                    "issue_url": issue_url,
                    "pr_url": None,
                    "workflow_type": "issue_only",
                    "created_at": datetime.now().isoformat(),
                    "message": "Issue作成完了",
                }

            self.logger.info(f"Queen Worker: GitHub統合処理完了 - {session_id}")
            return result

        except Exception as e:
            self.logger.error(f"Queen Worker: GitHub統合処理エラー - {e}")
            return {
                "success": False,
                "session_id": session_id,
                "error": str(e),
                "workflow_type": "error",
                "created_at": datetime.now().isoformat(),
                "message": "GitHub統合処理エラー",
            }

    def create_implementation_pr(
        self,
        session_id: str,
        implementation_summary: str,
        technical_details: str = "",
        test_results: str = "",
        worker_notes: str = "",
    ) -> dict[str, Any]:
        """
        実装完了後のPR作成

        Args:
            session_id: セッションID
            implementation_summary: 実装サマリー
            technical_details: 技術的詳細
            test_results: テスト結果
            worker_notes: Worker備考

        Returns:
            PR作成結果辞書
        """
        self.logger.info(f"Queen Worker: 実装PR作成開始 - {session_id}")

        try:
            # セッションデータを取得
            session_data = self.integration.load_session_data(session_id)
            if not session_data:
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": "セッションデータが見つかりません",
                    "message": "セッションデータ読み込みエラー",
                }

            # 実装データを準備
            implementation_data = {
                "session_id": session_id,
                "title": implementation_summary,
                "summary": implementation_summary,
                "technical_changes": technical_details,
                "test_info": test_results,
                "worker_info": worker_notes,
                "related_issues": f"Closes #{session_data.get('issue_number', '')}"
                if session_data.get("issue_number")
                else "",
            }

            # PR作成
            pr_url = self.integration.pr_creator.create_pr(implementation_data)

            if pr_url:
                # セッションデータを更新
                session_data["pr_url"] = pr_url
                session_data["implementation_completed_at"] = datetime.now().isoformat()
                self.integration._save_session_data(session_id, session_data)

                result = {
                    "success": True,
                    "session_id": session_id,
                    "pr_url": pr_url,
                    "issue_url": session_data.get("issue_url"),
                    "created_at": datetime.now().isoformat(),
                    "message": "実装PR作成完了",
                }
            else:
                result = {
                    "success": False,
                    "session_id": session_id,
                    "error": "PR作成に失敗しました",
                    "message": "PR作成エラー",
                }

            self.logger.info(f"Queen Worker: 実装PR作成完了 - {session_id}")
            return result

        except Exception as e:
            self.logger.error(f"Queen Worker: 実装PR作成エラー - {e}")
            return {
                "success": False,
                "session_id": session_id,
                "error": str(e),
                "message": "実装PR作成エラー",
            }

    def get_session_status(self, session_id: str) -> dict[str, Any]:
        """
        セッションステータス取得

        Args:
            session_id: セッションID

        Returns:
            セッションステータス辞書
        """
        try:
            session_data = self.integration.load_session_data(session_id)
            if not session_data:
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": "セッションが見つかりません",
                    "status": "not_found",
                }

            # ステータス判定
            if session_data.get("pr_url"):
                status = "pr_created"
            elif session_data.get("issue_url"):
                status = "issue_created"
            else:
                status = "initialized"

            return {
                "success": True,
                "session_id": session_id,
                "status": status,
                "issue_url": session_data.get("issue_url"),
                "issue_number": session_data.get("issue_number"),
                "pr_url": session_data.get("pr_url"),
                "created_at": session_data.get("created_at"),
                "title": session_data.get("analysis_result", {}).get("title", ""),
                "participants": session_data.get("analysis_result", {}).get(
                    "participants", []
                ),
            }

        except Exception as e:
            self.logger.error(f"Queen Worker: セッションステータス取得エラー - {e}")
            return {
                "success": False,
                "session_id": session_id,
                "error": str(e),
                "status": "error",
            }

    def list_active_sessions(self) -> list[dict[str, Any]]:
        """
        アクティブセッション一覧取得

        Returns:
            アクティブセッション一覧
        """
        try:
            sessions_dir = Path(__file__).parent.parent / ".hive" / "sessions"
            if not sessions_dir.exists():
                return []

            sessions = []
            for session_file in sessions_dir.glob("*.json"):
                session_id = session_file.stem
                status = self.get_session_status(session_id)
                if status["success"]:
                    sessions.append(status)

            return sorted(sessions, key=lambda x: x.get("created_at", ""), reverse=True)

        except Exception as e:
            self.logger.error(f"Queen Worker: アクティブセッション一覧取得エラー - {e}")
            return []

    def create_follow_up_issue(
        self,
        original_session_id: str,
        follow_up_title: str,
        follow_up_summary: str,
        follow_up_details: str = "",
    ) -> dict[str, Any]:
        """
        フォローアップIssue作成

        Args:
            original_session_id: 元のセッションID
            follow_up_title: フォローアップタイトル
            follow_up_summary: フォローアップサマリー
            follow_up_details: フォローアップ詳細

        Returns:
            フォローアップIssue作成結果
        """
        try:
            # 元のセッションデータを取得
            original_data = self.integration.load_session_data(original_session_id)
            if not original_data:
                return {
                    "success": False,
                    "error": "元のセッションデータが見つかりません",
                    "message": "セッションデータ読み込みエラー",
                }

            # フォローアップセッションID生成
            follow_up_session_id = f"{original_session_id}_followup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # フォローアップ分析結果を構築
            follow_up_analysis = {
                "title": follow_up_title,
                "summary": follow_up_summary,
                "details": follow_up_details,
                "recommended_actions": "フォローアップ実装",
                "participants": original_data.get("analysis_result", {}).get(
                    "participants", []
                ),
                "original_session_id": original_session_id,
                "original_issue_number": original_data.get("issue_number"),
                "follow_up_type": "enhancement",
            }

            # フォローアップIssue作成
            issue_url = self.integration._create_issue_from_analysis(
                follow_up_session_id, follow_up_analysis
            )

            if issue_url:
                result = {
                    "success": True,
                    "session_id": follow_up_session_id,
                    "original_session_id": original_session_id,
                    "issue_url": issue_url,
                    "created_at": datetime.now().isoformat(),
                    "message": "フォローアップIssue作成完了",
                }
            else:
                result = {
                    "success": False,
                    "error": "フォローアップIssue作成に失敗しました",
                    "message": "Issue作成エラー",
                }

            return result

        except Exception as e:
            self.logger.error(f"Queen Worker: フォローアップIssue作成エラー - {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "フォローアップIssue作成エラー",
            }

    def format_session_report(self, session_id: str) -> str:
        """
        セッションレポート生成

        Args:
            session_id: セッションID

        Returns:
            Markdown形式のセッションレポート
        """
        try:
            session_data = self.integration.load_session_data(session_id)
            if not session_data:
                return f"# セッションレポート\n\n**エラー:** セッションデータが見つかりません (ID: {session_id})"

            analysis_result = session_data.get("analysis_result", {})

            report = f"""# セッションレポート: {session_id}

## 基本情報

- **セッションID:** {session_id}
- **タイトル:** {analysis_result.get("title", "N/A")}
- **作成日時:** {session_data.get("created_at", "N/A")}
- **参加者:** {", ".join(analysis_result.get("participants", []))}

## GitHub連携状況

- **Issue:** {session_data.get("issue_url", "N/A")}
- **Issue番号:** #{session_data.get("issue_number", "N/A")}
- **Pull Request:** {session_data.get("pr_url", "N/A")}

## 分析結果

### 概要
{analysis_result.get("summary", "N/A")}

### 詳細
{analysis_result.get("details", "N/A")}

### 推奨アクション
{analysis_result.get("recommended_actions", "N/A")}

### 完了条件
{analysis_result.get("completion_criteria", "N/A")}

## 実装状況

- **Issue作成:** {"✅" if session_data.get("issue_url") else "❌"}
- **PR作成:** {"✅" if session_data.get("pr_url") else "❌"}
- **実装完了:** {"✅" if session_data.get("implementation_completed_at") else "❌"}

---

*🤖 このレポートはHive Multi-Agent Systemにより自動生成されました*
"""

            return report

        except Exception as e:
            self.logger.error(f"Queen Worker: セッションレポート生成エラー - {e}")
            return f"# セッションレポート\n\n**エラー:** レポート生成に失敗しました - {str(e)}"


# Queen Worker向け簡易関数群
def queen_create_issue_pr_workflow(
    session_id: str, analysis_result: dict[str, Any]
) -> dict[str, Any]:
    """Queen Worker用 Issue-PR統合ワークフロー実行"""
    integration = QueenGitHubIntegration()
    return integration.process_hive_analysis_to_github(session_id, analysis_result)


def queen_create_implementation_pr(
    session_id: str,
    implementation_summary: str,
    technical_details: str = "",
    test_results: str = "",
) -> dict[str, Any]:
    """Queen Worker用 実装PR作成"""
    integration = QueenGitHubIntegration()
    return integration.create_implementation_pr(
        session_id, implementation_summary, technical_details, test_results
    )


def queen_get_session_status(session_id: str) -> dict[str, Any]:
    """Queen Worker用 セッションステータス取得"""
    integration = QueenGitHubIntegration()
    return integration.get_session_status(session_id)


def queen_list_active_sessions() -> list[dict[str, Any]]:
    """Queen Worker用 アクティブセッション一覧取得"""
    integration = QueenGitHubIntegration()
    return integration.list_active_sessions()


def main() -> None:
    """テスト用メイン関数"""
    integration = QueenGitHubIntegration()

    print("=== Queen Worker GitHub統合テスト ===")

    # アクティブセッション一覧のテスト
    sessions = integration.list_active_sessions()
    print(f"アクティブセッション数: {len(sessions)}")

    # テスト用分析結果
    test_analysis = {
        "title": "Queen Worker統合テスト",
        "summary": "GitHub統合機能のテスト",
        "details": "Issue-PR統合機能のテスト実装",
        "recommended_actions": "テストの実行と結果確認",
        "participants": ["Queen", "Test"],
        "completion_criteria": "- テスト実行完了\n- 結果確認完了",
    }

    print("\nテスト用分析結果:")
    print(json.dumps(test_analysis, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
