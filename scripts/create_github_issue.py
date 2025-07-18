#!/usr/bin/env python3
"""
Hive GitHub Issue自動作成スクリプト

Hive検討結果をGitHub Issueとして自動作成する機能を提供します。
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class HiveGitHubIssueCreator:
    """Hive検討結果のGitHub Issue作成クラス"""

    def __init__(self, config_path: str | None = None):
        """
        初期化

        Args:
            config_path: 設定ファイルパス（省略時は config/github_settings.yaml）
        """
        self.project_root = Path(__file__).parent.parent
        self.config_path = (
            config_path or self.project_root / "config" / "github_settings.yaml"
        )
        self.config = self._load_config()

        # ログ設定
        self._setup_logging()

        # GitHub CLI確認
        self._check_gh_cli()

        # リポジトリ情報取得
        self.repo_info = self._get_repository_info()

    def _load_config(self) -> dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.error(f"設定ファイルが見つかりません: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            self.logger.error(f"設定ファイルの読み込みエラー: {e}")
            sys.exit(1)

    def _setup_logging(self):
        """ログ設定"""
        log_config = self.config.get("execution", {}).get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))

        # ログディレクトリ作成
        log_file = self.project_root / log_config.get(
            "file", "logs/github_issue_creation.log"
        )
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # ログ設定
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )

        self.logger = logging.getLogger(__name__)

    def _check_gh_cli(self):
        """GitHub CLI存在確認"""
        try:
            result = subprocess.run(
                ["gh", "--version"], capture_output=True, text=True, check=True
            )
            self.logger.info(f"GitHub CLI確認: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.error("GitHub CLIがインストールされていません")
            sys.exit(1)

    def _get_repository_info(self) -> dict[str, str]:
        """リポジトリ情報取得"""
        github_config = self.config.get("github", {})
        repo_config = github_config.get("repository", {})

        if repo_config.get("auto_detect", True):
            try:
                # git remoteから自動検出
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                remote_url = result.stdout.strip()
                self.logger.info(f"リモートURL検出: {remote_url}")

                # GitHubリポジトリ情報を抽出
                if "github.com" in remote_url:
                    # https://github.com/owner/repo.git または git@github.com:owner/repo.git
                    if remote_url.startswith("https://"):
                        repo_part = remote_url.split("github.com/")[-1]
                    else:
                        repo_part = remote_url.split("github.com:")[-1]

                    repo_part = repo_part.replace(".git", "")
                    owner, name = repo_part.split("/")

                    return {"owner": owner, "name": name}
                else:
                    self.logger.warning("GitHub以外のリポジトリです")
                    return {"owner": "", "name": ""}

            except subprocess.CalledProcessError:
                self.logger.warning(
                    "git remoteからリポジトリ情報を取得できませんでした"
                )
                return {"owner": "", "name": ""}
        else:
            return {
                "owner": repo_config.get("owner", ""),
                "name": repo_config.get("name", ""),
            }

    def _load_template(self) -> str:
        """テンプレートファイル読み込み"""
        template_config = self.config.get("template", {})
        template_path = self.project_root / template_config.get(
            "file", "templates/github/issue_template.md"
        )

        try:
            with open(template_path, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            self.logger.error(f"テンプレートファイルが見つかりません: {template_path}")
            sys.exit(1)

    def _classify_result(self, result_data: dict[str, Any]) -> dict[str, str]:
        """検討結果の分類"""
        classification_config = (
            self.config.get("hive", {}).get("results", {}).get("classification", {})
        )

        if not classification_config.get("auto_priority", True):
            return {"priority": "medium", "type": "proposal"}

        content = str(result_data.get("summary", "")) + str(
            result_data.get("details", "")
        )
        content_lower = content.lower()

        # 優先度判定
        keywords = classification_config.get("keywords", {})
        priority = "low"

        for level, words in keywords.items():
            if any(word in content_lower for word in words):
                priority = level
                break

        # タイプ判定（デフォルト：proposal）
        result_type = "proposal"
        if any(word in content_lower for word in ["バグ", "bug", "エラー", "error"]):
            result_type = "bug"
        elif any(word in content_lower for word in ["機能", "feature", "新機能"]):
            result_type = "feature"
        elif any(word in content_lower for word in ["改善", "enhancement", "向上"]):
            result_type = "enhancement"
        elif any(word in content_lower for word in ["リファクタリング", "refactor"]):
            result_type = "refactor"
        elif any(word in content_lower for word in ["テスト", "test"]):
            result_type = "test"
        elif any(word in content_lower for word in ["ドキュメント", "docs", "文書"]):
            result_type = "docs"

        return {"priority": priority, "type": result_type}

    def _format_template(self, template: str, result_data: dict[str, Any]) -> str:
        """テンプレートの変数置換"""
        # 基本情報
        session_id = result_data.get("session_id", "unknown")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        workers = ", ".join(result_data.get("workers", []))

        # 分類情報
        classification = self._classify_result(result_data)

        # 変数置換
        variables = {
            "session_id": session_id,
            "timestamp": timestamp,
            "workers": workers,
            "title": result_data.get("title", "検討結果"),
            "summary": result_data.get("summary", ""),
            "details": result_data.get("details", ""),
            "actions": result_data.get("actions", ""),
            "worker_results": result_data.get("worker_results", ""),
            "priority": classification["priority"],
            "type": classification["type"],
            "impact": result_data.get("impact", ""),
            "duration": result_data.get("duration", ""),
            "worker_count": str(len(result_data.get("workers", []))),
            "proposal_count": str(result_data.get("proposal_count", 0)),
            "item_count": str(result_data.get("item_count", 0)),
            "related_resources": result_data.get("related_resources", ""),
            "completion_criteria": result_data.get("completion_criteria", ""),
            "additional_notes": result_data.get("additional_notes", ""),
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # テンプレート置換
        formatted = template
        for key, value in variables.items():
            formatted = formatted.replace("{{" + key + "}}", str(value))

        return formatted

    def _get_labels(self, classification: dict[str, str]) -> list[str]:
        """ラベル取得"""
        labels_config = self.config.get("github", {}).get("issue", {}).get("labels", {})

        labels = list(labels_config.get("default", []))

        # 優先度ラベル
        priority_labels = labels_config.get("priority", {})
        if classification["priority"] in priority_labels:
            labels.append(priority_labels[classification["priority"]])

        # タイプラベル
        type_labels = labels_config.get("type", {})
        if classification["type"] in type_labels:
            labels.append(type_labels[classification["type"]])

        return labels

    def _create_issue_title(self, result_data: dict[str, Any]) -> str:
        """Issue タイトル生成"""
        title_prefix = (
            self.config.get("github", {})
            .get("issue", {})
            .get("title_prefix", "[Hive検討結果]")
        )
        title = result_data.get("title", "検討結果")

        return f"{title_prefix} {title}"

    def create_issue(
        self, result_data: dict[str, Any], preview: bool = False
    ) -> str | None:
        """
        GitHub Issue作成

        Args:
            result_data: 検討結果データ
            preview: プレビューモード（実際には作成しない）

        Returns:
            作成されたIssue URL（previewの場合はNone）
        """
        self.logger.info("GitHub Issue作成開始")

        # テンプレート読み込み
        template = self._load_template()

        # Issue内容生成
        issue_body = self._format_template(template, result_data)
        issue_title = self._create_issue_title(result_data)

        # 分類情報取得
        classification = self._classify_result(result_data)
        labels = self._get_labels(classification)

        # プレビュー表示
        if preview:
            print("=" * 60)
            print("GitHub Issue プレビュー")
            print("=" * 60)
            print(f"タイトル: {issue_title}")
            print(f"ラベル: {', '.join(labels)}")
            print("-" * 60)
            print(issue_body)
            print("=" * 60)
            return None

        # 確認設定
        execution_config = self.config.get("execution", {})
        if execution_config.get("confirmation", {}).get("confirm_create", True):
            confirm = input("GitHub Issueを作成しますか？ (y/N): ")
            if confirm.lower() != "y":
                self.logger.info("Issue作成をキャンセルしました")
                return None

        # GitHub CLI でIssue作成
        try:
            cmd = [
                "gh",
                "issue",
                "create",
                "--title",
                issue_title,
                "--body",
                issue_body,
            ]

            # ラベル追加
            if labels:
                cmd.extend(["--label", ",".join(labels)])

            # アサイン設定
            assignee_config = (
                self.config.get("github", {}).get("issue", {}).get("assignees", {})
            )
            if assignee_config.get("auto_assign", False):
                default_assignee = assignee_config.get("default_assignee", "")
                if default_assignee:
                    cmd.extend(["--assignee", default_assignee])

            # マイルストーン設定
            milestone_config = (
                self.config.get("github", {}).get("issue", {}).get("milestone", {})
            )
            if milestone_config.get("auto_detect", False):
                default_milestone = milestone_config.get("default", "")
                if default_milestone:
                    cmd.extend(["--milestone", default_milestone])

            self.logger.info(f"GitHub CLI コマンド実行: {' '.join(cmd[:4])}...")

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            issue_url = result.stdout.strip()
            self.logger.info(f"GitHub Issue作成完了: {issue_url}")

            return issue_url

        except subprocess.CalledProcessError as e:
            self.logger.error(f"GitHub Issue作成エラー: {e}")
            self.logger.error(f"stderr: {e.stderr}")
            return None


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Hive検討結果のGitHub Issue自動作成")
    parser.add_argument("--config", "-c", help="設定ファイルパス")
    parser.add_argument("--data", "-d", help="検討結果データファイル（JSON）")
    parser.add_argument("--preview", "-p", action="store_true", help="プレビューモード")
    parser.add_argument("--title", "-t", help="Issue タイトル")
    parser.add_argument("--summary", "-s", help="概要")
    parser.add_argument("--details", help="詳細")
    parser.add_argument("--actions", "-a", help="推奨アクション")
    parser.add_argument("--workers", "-w", help="参加ワーカー（カンマ区切り）")
    parser.add_argument("--session-id", help="セッションID")

    args = parser.parse_args()

    # GitHub Issue作成器初期化
    creator = HiveGitHubIssueCreator(args.config)

    # 検討結果データ準備
    if args.data:
        # JSONファイルから読み込み
        with open(args.data, encoding="utf-8") as f:
            result_data = json.load(f)
    else:
        # コマンドライン引数から構築
        result_data = {
            "title": args.title or "検討結果",
            "summary": args.summary or "",
            "details": args.details or "",
            "actions": args.actions or "",
            "workers": args.workers.split(",") if args.workers else [],
            "session_id": args.session_id
            or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        }

    # Issue作成
    issue_url = creator.create_issue(result_data, preview=args.preview)

    if issue_url:
        print(f"GitHub Issue作成完了: {issue_url}")
        sys.exit(0)
    elif not args.preview:
        print("GitHub Issue作成に失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
