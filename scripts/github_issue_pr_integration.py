#!/usr/bin/env python3
"""
Hive GitHub Issue-PR統合ヘルパー

GitHub IssueとPull Requestの連携機能を提供します。
Issue作成 → 実装 → PR作成 → レビュー の一連のワークフローを統合します。
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .create_github_issue import HiveGitHubIssueCreator
from .create_github_pr import HiveGitHubPRCreator
from .github_issue_helper import HiveGitHubHelper


class HiveGitHubIntegration:
    """GitHub Issue-PR統合管理クラス"""

    def __init__(self, config_path: str | None = None):
        """
        初期化

        Args:
            config_path: 設定ファイルパス
        """
        self.project_root = Path(__file__).parent.parent
        self.config_path = config_path

        # 各種作成器の初期化
        self.issue_creator = HiveGitHubIssueCreator(config_path)
        self.pr_creator = HiveGitHubPRCreator(config_path)
        self.github_helper = HiveGitHubHelper()

        # ログ設定
        self.logger = logging.getLogger(__name__)

        # セッション管理
        self.session_data: dict[str, Any] = {}

    def create_issue_implementation_workflow(
        self,
        session_id: str,
        analysis_result: dict[str, Any],
        implementation_data: dict[str, Any] | None = None,
    ) -> tuple[str | None, str | None]:
        """
        Issue作成 → 実装 → PR作成の統合ワークフロー

        Args:
            session_id: セッションID
            analysis_result: 分析結果データ
            implementation_data: 実装データ（省略時は分析結果から生成）

        Returns:
            (issue_url, pr_url) のタプル
        """
        self.logger.info(f"統合ワークフロー開始: {session_id}")

        # 1. Issue作成
        issue_url = self._create_issue_from_analysis(session_id, analysis_result)
        if not issue_url:
            self.logger.error("Issue作成に失敗しました")
            return None, None

        # Issue番号を抽出
        issue_number = self._extract_issue_number(issue_url)

        # 2. 実装データ準備
        if implementation_data is None:
            implementation_data = self._generate_implementation_data_from_analysis(
                session_id, analysis_result, issue_number
            )

        # 3. PR作成
        pr_url = self._create_pr_from_implementation(
            session_id, implementation_data, issue_number
        )

        # 4. セッションデータ保存
        self._save_session_data(
            session_id,
            {
                "issue_url": issue_url,
                "issue_number": issue_number,
                "pr_url": pr_url,
                "analysis_result": analysis_result,
                "implementation_data": implementation_data,
                "created_at": datetime.now().isoformat(),
            },
        )

        self.logger.info(f"統合ワークフロー完了: Issue={issue_url}, PR={pr_url}")
        return issue_url, pr_url

    def _create_issue_from_analysis(
        self, session_id: str, analysis_result: dict[str, Any]
    ) -> str | None:
        """分析結果からIssue作成"""
        try:
            # 分析結果をIssue作成用データに変換
            issue_data = {
                "session_id": session_id,
                "title": analysis_result.get("title", "分析結果"),
                "summary": analysis_result.get("summary", ""),
                "details": analysis_result.get("details", ""),
                "actions": analysis_result.get("recommended_actions", ""),
                "workers": analysis_result.get("participants", []),
                "worker_results": analysis_result.get("worker_results", {}),
                "impact": analysis_result.get("impact_assessment", ""),
                "duration": analysis_result.get("duration", ""),
                "proposal_count": analysis_result.get("proposal_count", 0),
                "completion_criteria": analysis_result.get("completion_criteria", ""),
                "related_resources": analysis_result.get("related_resources", ""),
                "additional_notes": analysis_result.get("notes", ""),
            }

            return self.issue_creator.create_issue(issue_data)

        except Exception as e:
            self.logger.error(f"Issue作成エラー: {e}")
            return None

    def _extract_issue_number(self, issue_url: str) -> int | None:
        """Issue URLからIssue番号を抽出"""
        try:
            # GitHub Issue URLから番号を抽出
            # 例: https://github.com/owner/repo/issues/123
            if "/issues/" in issue_url:
                return int(issue_url.split("/issues/")[-1])
            return None
        except (ValueError, IndexError):
            return None

    def _generate_implementation_data_from_analysis(
        self, session_id: str, analysis_result: dict[str, Any], issue_number: int | None
    ) -> dict[str, Any]:
        """分析結果から実装データを生成"""
        # 実装タイプを推定
        implementation_type = self._estimate_implementation_type(analysis_result)

        # Worker情報を構築
        worker_info = self._format_worker_info(analysis_result.get("participants", []))

        # テクニカル変更点を生成
        technical_changes = self._generate_technical_changes(analysis_result)

        # 品質チェック情報を生成
        quality_checks = self._generate_quality_checks(implementation_type)

        # レビュー観点を生成
        review_points = self._generate_review_points(analysis_result)

        return {
            "session_id": session_id,
            "title": analysis_result.get("title", "実装結果"),
            "title_prefix": implementation_type,
            "summary": analysis_result.get("summary", ""),
            "related_issues": f"Closes #{issue_number}" if issue_number else "",
            "worker_info": worker_info,
            "technical_changes": technical_changes,
            "quality_checks": quality_checks,
            "review_points": review_points,
            "test_info": self._generate_test_info(analysis_result),
            "completion_criteria": analysis_result.get("completion_criteria", ""),
            "implementation_type": implementation_type,
        }

    def _estimate_implementation_type(self, analysis_result: dict[str, Any]) -> str:
        """分析結果から実装タイプを推定"""
        content = str(analysis_result.get("summary", "")) + str(
            analysis_result.get("details", "")
        )
        content_lower = content.lower()

        if any(word in content_lower for word in ["新機能", "feature", "機能追加"]):
            return "feat"
        elif any(
            word in content_lower for word in ["バグ", "bug", "エラー", "error", "修正"]
        ):
            return "fix"
        elif any(word in content_lower for word in ["改善", "enhancement", "向上"]):
            return "enhancement"
        elif any(word in content_lower for word in ["リファクタリング", "refactor"]):
            return "refactor"
        elif any(word in content_lower for word in ["テスト", "test"]):
            return "test"
        elif any(word in content_lower for word in ["ドキュメント", "docs", "文書"]):
            return "docs"
        else:
            return "feat"

    def _format_worker_info(self, participants: list[str]) -> str:
        """参加者情報をフォーマット"""
        if not participants:
            return "参加Workerなし"

        info = "### 参加Worker\n\n"
        for participant in participants:
            info += f"- **{participant}**\n"

        return info

    def _generate_technical_changes(self, analysis_result: dict[str, Any]) -> str:
        """技術的変更点を生成"""
        changes = []

        # 分析結果から技術的な要素を抽出
        details = analysis_result.get("details", "")
        if details:
            changes.append(f"実装詳細: {details}")

        recommendations = analysis_result.get("recommended_actions", "")
        if recommendations:
            changes.append(f"推奨実装: {recommendations}")

        if not changes:
            changes.append("実装の詳細は差分をご確認ください")

        return "\n".join(changes)

    def _generate_quality_checks(self, implementation_type: str) -> str:
        """品質チェック情報を生成"""
        checks = [
            "- [ ] `make quality` での品質チェック通過",
            "- [ ] テストカバレッジ維持",
            "- [ ] コードレビュー完了",
        ]

        if implementation_type == "feat":
            checks.append("- [ ] 新機能の動作確認")
        elif implementation_type == "fix":
            checks.append("- [ ] バグ修正の動作確認")
        elif implementation_type == "test":
            checks.append("- [ ] テストの実行確認")

        return "\n".join(checks)

    def _generate_review_points(self, analysis_result: dict[str, Any]) -> str:
        """レビュー観点を生成"""
        points = [
            "### コードレビュー観点",
            "",
            "- コードの可読性と保守性",
            "- 実装の妥当性",
            "- テストの適切性",
            "- パフォーマンスへの影響",
        ]

        # 分析結果から特別な観点を追加
        if analysis_result.get("impact_assessment"):
            points.append(f"- 影響範囲: {analysis_result['impact_assessment']}")

        return "\n".join(points)

    def _generate_test_info(self, analysis_result: dict[str, Any]) -> str:
        """テスト情報を生成"""
        test_info = [
            "### テスト実行結果",
            "",
            "```bash",
            "make test",
            "```",
            "",
            "### テストカバレッジ",
            "",
            "実装後のテストカバレッジレポートを確認してください。",
        ]

        return "\n".join(test_info)

    def _create_pr_from_implementation(
        self,
        session_id: str,
        implementation_data: dict[str, Any],
        issue_number: int | None,
    ) -> str | None:
        """実装データからPR作成"""
        try:
            return self.pr_creator.create_pr(implementation_data)
        except Exception as e:
            self.logger.error(f"PR作成エラー: {e}")
            return None

    def _save_session_data(self, session_id: str, data: dict[str, Any]) -> None:
        """セッションデータを保存"""
        try:
            session_dir = self.project_root / ".hive" / "sessions"
            session_dir.mkdir(parents=True, exist_ok=True)

            session_file = session_dir / f"{session_id}.json"

            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"セッションデータ保存: {session_file}")

        except Exception as e:
            self.logger.error(f"セッションデータ保存エラー: {e}")

    def load_session_data(self, session_id: str) -> dict[str, Any] | None:
        """セッションデータを読み込み"""
        try:
            session_file = (
                self.project_root / ".hive" / "sessions" / f"{session_id}.json"
            )

            if not session_file.exists():
                return None

            with open(session_file, encoding="utf-8") as f:
                data = json.load(f)
                return dict(data) if isinstance(data, dict) else None

        except Exception as e:
            self.logger.error(f"セッションデータ読み込みエラー: {e}")
            return None

    def create_follow_up_pr(
        self, session_id: str, follow_up_data: dict[str, Any]
    ) -> str | None:
        """フォローアップPRを作成"""
        session_data = self.load_session_data(session_id)
        if not session_data:
            self.logger.error(f"セッションデータが見つかりません: {session_id}")
            return None

        # 元のIssue番号を取得
        original_issue_number = session_data.get("issue_number")

        # フォローアップPRデータを準備
        pr_data = {
            "session_id": session_id,
            "title": follow_up_data.get("title", "フォローアップ実装"),
            "title_prefix": "feat",
            "summary": follow_up_data.get("summary", ""),
            "related_issues": f"Relates to #{original_issue_number}"
            if original_issue_number
            else "",
            "worker_info": follow_up_data.get("worker_info", ""),
            "technical_changes": follow_up_data.get("technical_changes", ""),
            "quality_checks": self._generate_quality_checks("feat"),
            "review_points": follow_up_data.get("review_points", ""),
            "test_info": follow_up_data.get("test_info", ""),
            "completion_criteria": follow_up_data.get("completion_criteria", ""),
            "implementation_type": "feat",
        }

        return self.pr_creator.create_pr(pr_data)

    def get_session_summary(self, session_id: str) -> dict[str, Any] | None:
        """セッションサマリーを取得"""
        session_data = self.load_session_data(session_id)
        if not session_data:
            return None

        return {
            "session_id": session_id,
            "issue_url": session_data.get("issue_url"),
            "issue_number": session_data.get("issue_number"),
            "pr_url": session_data.get("pr_url"),
            "created_at": session_data.get("created_at"),
            "title": session_data.get("analysis_result", {}).get("title", ""),
            "status": "completed" if session_data.get("pr_url") else "in_progress",
        }


def main() -> None:
    """テスト用メイン関数"""
    integration = HiveGitHubIntegration()

    # テスト用のプレビュー表示
    print("🐝 Hive GitHub統合機能テスト")
    print("実際のGitHub操作は行いません")
    print(f"設定読み込み: {integration.issue_creator.config is not None}")
    print("Issue作成機能: 利用可能")
    print("PR統合機能: 利用可能")

    # テスト用の分析結果データ
    test_analysis = {
        "title": "テスト機能の実装",
        "summary": "テスト機能の実装と検証",
        "details": "詳細な実装内容...",
        "recommended_actions": "実装とテストの実行",
        "participants": ["Queen", "Developer"],
        "impact_assessment": "システム全体への影響は軽微",
        "completion_criteria": "- 実装完了\n- テスト通過\n- コードレビュー完了",
    }

    # 統合ワークフローのテスト（プレビューモード）
    print("=== GitHub Issue-PR統合ワークフロー テスト ===")
    print("テスト用の分析結果:")
    print(json.dumps(test_analysis, ensure_ascii=False, indent=2))

    # セッションサマリーの表示例
    print("\n=== セッションサマリー例 ===")
    example_summary = {
        "session_id": "test_session_001",
        "issue_url": "https://github.com/example/repo/issues/123",
        "issue_number": 123,
        "pr_url": "https://github.com/example/repo/pull/456",
        "created_at": "2024-01-01T12:00:00",
        "title": "テスト機能の実装",
        "status": "completed",
    }
    print(json.dumps(example_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
