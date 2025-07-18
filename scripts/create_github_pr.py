#!/usr/bin/env python3
"""
Hive GitHub Pull Request自動作成スクリプト

Hive実装結果をGitHub Pull Requestとして自動作成し、関連Issueと連携する機能を提供します。
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


class HiveGitHubPRCreator:
    """Hive実装結果のGitHub Pull Request作成クラス"""

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

        # Git状態確認
        self._check_git_status()

    def _load_config(self) -> dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config if config is not None else {}
        except FileNotFoundError:
            # デフォルト設定を使用
            return {
                "github": {
                    "repository": {"auto_detect": True},
                    "pr": {
                        "auto_push": True,
                        "draft": False,
                        "labels": {"default": ["hive-generated"]},
                        "reviewers": {"auto_assign": False},
                        "template": {"file": ".hive/templates/github/pr_template.md"},
                    },
                },
                "execution": {
                    "logging": {"level": "INFO", "file": "logs/github_pr_creation.log"},
                    "confirmation": {"confirm_create": True},
                },
            }
        except yaml.YAMLError as e:
            self.logger.error(f"設定ファイルの読み込みエラー: {e}")
            sys.exit(1)

    def _setup_logging(self) -> None:
        """ログ設定"""
        log_config = self.config.get("execution", {}).get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))

        # ログディレクトリ作成
        log_file = self.project_root / log_config.get(
            "file", "logs/github_pr_creation.log"
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

    def _check_gh_cli(self) -> None:
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

    def _check_git_status(self) -> None:
        """Git状態確認"""
        try:
            # 現在のブランチを取得
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.current_branch = result.stdout.strip()

            # mainブランチでないことを確認
            if self.current_branch == "main":
                self.logger.warning("mainブランチでPRを作成しようとしています")

            # 未コミットの変更があるかチェック
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                self.logger.info("未コミットの変更があります")
                self.has_uncommitted_changes = True
            else:
                self.has_uncommitted_changes = False

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git状態確認エラー: {e}")
            sys.exit(1)

    def _load_template(self) -> str:
        """テンプレートファイル読み込み"""
        template_config = (
            self.config.get("github", {}).get("pr", {}).get("template", {})
        )
        template_path = self.project_root / template_config.get(
            "file", ".hive/templates/github/pr_template.md"
        )

        try:
            with open(template_path, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            self.logger.error(f"テンプレートファイルが見つかりません: {template_path}")
            sys.exit(1)

    def _get_git_diff_summary(self) -> tuple[str, list[str]]:
        """Git差分サマリー取得"""
        try:
            # ファイル変更サマリー取得
            result = subprocess.run(
                ["git", "diff", "--name-status", "main...HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )

            changed_files = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        status = parts[0]
                        filename = parts[1]
                        changed_files.append(f"- {status}: {filename}")

            # 変更内容取得
            result = subprocess.run(
                ["git", "diff", "main...HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )

            diff_content = result.stdout

            return diff_content, changed_files

        except subprocess.CalledProcessError:
            self.logger.warning("Git差分を取得できませんでした")
            return "", []

    def _extract_changes_summary(self, diff_content: str) -> str:
        """差分から変更サマリーを抽出"""
        if not diff_content:
            return "変更内容を取得できませんでした"

        # 簡易的な変更サマリー生成
        lines = diff_content.split("\n")
        added_lines = len([line for line in lines if line.startswith("+")])
        removed_lines = len([line for line in lines if line.startswith("-")])

        summary = f"- **追加行数:** {added_lines}\n"
        summary += f"- **削除行数:** {removed_lines}\n"
        summary += f"- **変更ファイル数:** {len([line for line in lines if line.startswith('diff --git')])}"

        return summary

    def _format_template(self, template: str, pr_data: dict[str, Any]) -> str:
        """テンプレートの変数置換"""
        # 基本情報
        session_id = pr_data.get("session_id", "unknown")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Git差分情報取得
        diff_content, changed_files = self._get_git_diff_summary()
        changes_summary = self._extract_changes_summary(diff_content)

        # 変数置換
        variables = {
            "session_id": session_id,
            "timestamp": timestamp,
            "title": pr_data.get("title", "Hive実装結果"),
            "summary": pr_data.get("summary", ""),
            "related_issues": pr_data.get("related_issues", ""),
            "changes": changes_summary,
            "test_info": pr_data.get("test_info", ""),
            "worker_info": pr_data.get("worker_info", ""),
            "technical_changes": pr_data.get("technical_changes", ""),
            "changed_files": "\n".join(changed_files)
            if changed_files
            else "変更ファイルなし",
            "quality_checks": pr_data.get("quality_checks", ""),
            "completion_criteria": pr_data.get("completion_criteria", ""),
            "review_points": pr_data.get("review_points", ""),
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # テンプレート置換
        formatted = template
        for key, value in variables.items():
            formatted = formatted.replace("{{" + key + "}}", str(value))

        return formatted

    def _get_labels(self, pr_data: dict[str, Any]) -> list[str]:
        """ラベル取得"""
        labels_config = self.config.get("github", {}).get("pr", {}).get("labels", {})

        labels = list(labels_config.get("default", ["hive-generated"]))

        # 実装タイプに応じたラベル追加
        implementation_type = pr_data.get("implementation_type", "")
        type_labels = labels_config.get("type", {})

        if implementation_type and implementation_type in type_labels:
            labels.append(type_labels[implementation_type])

        return labels

    def _create_pr_title(self, pr_data: dict[str, Any]) -> str:
        """PR タイトル生成"""
        title_prefix = pr_data.get("title_prefix", "")
        title = pr_data.get("title", "Hive実装結果")

        if title_prefix:
            return f"{title_prefix}: {title}"
        else:
            return title if isinstance(title, str) else str(title)

    def _get_related_issues_links(self, issue_numbers: list[int]) -> str:
        """関連Issue番号からリンク文字列生成"""
        if not issue_numbers:
            return ""

        links = []
        for issue_num in issue_numbers:
            links.append(f"Closes #{issue_num}")

        return "\n".join(links)

    def _push_branch(self) -> bool:
        """ブランチをリモートにプッシュ"""
        try:
            self.logger.info(f"ブランチ {self.current_branch} をプッシュしています...")

            # リモートブランチの存在確認
            result = subprocess.run(
                ["git", "ls-remote", "--heads", "origin", self.current_branch],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                # 既存のリモートブランチがある場合は通常のプッシュ
                subprocess.run(
                    ["git", "push", "origin", self.current_branch],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            else:
                # 新規ブランチの場合は -u オプションでプッシュ
                subprocess.run(
                    ["git", "push", "-u", "origin", self.current_branch],
                    capture_output=True,
                    text=True,
                    check=True,
                )

            self.logger.info("ブランチプッシュ完了")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"ブランチプッシュエラー: {e}")
            return False

    def create_pr(self, pr_data: dict[str, Any], preview: bool = False) -> str | None:
        """
        GitHub Pull Request作成

        Args:
            pr_data: PR作成データ
            preview: プレビューモード（実際には作成しない）

        Returns:
            作成されたPR URL（previewの場合はNone）
        """
        self.logger.info("GitHub Pull Request作成開始")

        # 未コミットの変更があるかチェック
        if self.has_uncommitted_changes:
            self.logger.warning(
                "未コミットの変更があります。コミットしてからPRを作成してください。"
            )
            return None

        # テンプレート読み込み
        template = self._load_template()

        # PR内容生成
        pr_body = self._format_template(template, pr_data)
        pr_title = self._create_pr_title(pr_data)

        # ラベル取得
        labels = self._get_labels(pr_data)

        # プレビュー表示
        if preview:
            print("=" * 60)
            print("GitHub Pull Request プレビュー")
            print("=" * 60)
            print(f"タイトル: {pr_title}")
            print(f"ラベル: {', '.join(labels)}")
            print(f"ブランチ: {self.current_branch} -> main")
            print("-" * 60)
            print(pr_body)
            print("=" * 60)
            return None

        # 確認設定
        execution_config = self.config.get("execution", {})
        if execution_config.get("confirmation", {}).get("confirm_create", True):
            confirm = input("GitHub Pull Requestを作成しますか？ (y/N): ")
            if confirm.lower() != "y":
                self.logger.info("PR作成をキャンセルしました")
                return None

        # ブランチプッシュ
        pr_config = self.config.get("github", {}).get("pr", {})
        if pr_config.get("auto_push", True):
            if not self._push_branch():
                self.logger.error("ブランチプッシュに失敗しました")
                return None

        # GitHub CLI でPR作成
        try:
            cmd = ["gh", "pr", "create", "--title", pr_title, "--body", pr_body]

            # Draft PR設定
            if pr_config.get("draft", False):
                cmd.append("--draft")

            # ラベル追加
            if labels:
                cmd.extend(["--label", ",".join(labels)])

            # レビューアー設定
            reviewer_config = pr_config.get("reviewers", {})
            if reviewer_config.get("auto_assign", False):
                reviewers = reviewer_config.get("default_reviewers", [])
                if reviewers:
                    cmd.extend(["--reviewer", ",".join(reviewers)])

            self.logger.info(f"GitHub CLI コマンド実行: {' '.join(cmd[:4])}...")

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            pr_url = result.stdout.strip()
            self.logger.info(f"GitHub Pull Request作成完了: {pr_url}")

            return pr_url

        except subprocess.CalledProcessError as e:
            self.logger.error(f"GitHub Pull Request作成エラー: {e}")
            self.logger.error(f"stderr: {e.stderr}")
            return None


def main() -> None:
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Hive実装結果のGitHub Pull Request自動作成"
    )
    parser.add_argument("--config", "-c", help="設定ファイルパス")
    parser.add_argument("--data", "-d", help="PR作成データファイル（JSON）")
    parser.add_argument("--preview", "-p", action="store_true", help="プレビューモード")
    parser.add_argument("--title", "-t", help="PR タイトル")
    parser.add_argument("--summary", "-s", help="概要")
    parser.add_argument("--issues", "-i", help="関連Issue番号（カンマ区切り）")
    parser.add_argument("--session-id", help="セッションID")
    parser.add_argument("--worker-info", help="実装ワーカー情報")
    parser.add_argument("--test-info", help="テスト情報")

    args = parser.parse_args()

    # GitHub PR作成器初期化
    creator = HiveGitHubPRCreator(args.config)

    # PR作成データ準備
    if args.data:
        # JSONファイルから読み込み
        with open(args.data, encoding="utf-8") as f:
            pr_data = json.load(f)
    else:
        # コマンドライン引数から構築
        pr_data = {
            "title": args.title or "Hive実装結果",
            "summary": args.summary or "",
            "session_id": args.session_id
            or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "worker_info": args.worker_info or "",
            "test_info": args.test_info or "",
            "related_issues": creator._get_related_issues_links(
                [int(x.strip()) for x in args.issues.split(",") if x.strip().isdigit()]
            )
            if args.issues
            else "",
        }

    # PR作成
    pr_url = creator.create_pr(pr_data, preview=args.preview)

    if pr_url:
        print(f"GitHub Pull Request作成完了: {pr_url}")
        sys.exit(0)
    elif not args.preview:
        print("GitHub Pull Request作成に失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
