#!/usr/bin/env python3
"""
GitHub Issue自動作成機能のテストスクリプト

実際のGitHub APIを使用せず、機能の動作確認を行います。
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

# テスト用のプロジェクトルートを設定
sys.path.insert(0, str(Path(__file__).parent))

from github_issue_helper import HiveGitHubHelper


def test_basic_functionality() -> None:
    """基本機能のテスト"""
    print("=== 基本機能テスト ===")

    helper = HiveGitHubHelper()

    # プレビューテスト
    print("\n1. プレビュー機能テスト")
    helper.preview_issue(
        session_id="test_session_001",
        title="基本機能テスト",
        summary="これは基本機能のテスト用概要です。新しいAPI機能の検討を行いました。",
        details="詳細な分析結果:\n- パフォーマンス改善の必要性\n- セキュリティ要件の確認\n- 実装方針の決定",
        actions="推奨アクション:\n- [ ] API仕様書の更新\n- [ ] プロトタイプの作成\n- [ ] レビュー実施",
        workers=["Queen", "Developer", "Analyst"],
    )

    print("\n✅ プレビュー機能テスト完了")


def test_worker_results_formatting() -> None:
    """ワーカー別結果フォーマットのテスト"""
    print("\n=== ワーカー別結果フォーマットテスト ===")

    helper = HiveGitHubHelper()

    # プレビュー表示
    helper.preview_issue(
        session_id="test_session_002",
        title="ワーカー別結果フォーマットテスト",
        summary="複数ワーカーによる協調作業の結果",
        details="各専門分野のワーカーが協力して検討を実施",
        actions="統合された推奨アクション",
        workers=["Queen", "Developer", "Analyst"],
    )

    print("\n✅ ワーカー別結果フォーマットテスト完了")


def test_log_file_processing() -> None:
    """ログファイル処理のテスト"""
    print("\n=== ログファイル処理テスト ===")

    helper = HiveGitHubHelper()

    # テスト用ログファイル作成
    test_log_content = """
2024-01-15 10:00:00 - INFO - セッション開始: test_session_003
2024-01-15 10:01:00 - INFO - Queen Worker: プロジェクト管理開始
2024-01-15 10:02:00 - INFO - Developer Worker: 技術検討開始
2024-01-15 10:30:00 - INFO - Summary: 新機能の実装方針を決定
2024-01-15 10:31:00 - INFO - 詳細: TypeScript移行とAPI設計の検討
2024-01-15 10:32:00 - INFO - アクション: プロトタイプ作成とテスト実施
2024-01-15 10:35:00 - INFO - Task: コードレビュー実施
2024-01-15 10:36:00 - INFO - セッション終了: test_session_003
"""

    # 一時ファイル作成
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False, encoding="utf-8"
    ) as f:
        f.write(test_log_content)
        temp_log_path = f.name

    try:
        # ログファイル処理のテスト（実際のIssue作成は行わない）
        print(f"テスト用ログファイル: {temp_log_path}")

        # 抽出機能のテスト
        with open(temp_log_path, encoding="utf-8") as f:
            log_content = f.read()

        summary = helper._extract_summary_from_log(log_content)
        details = helper._extract_details_from_log(log_content)
        actions = helper._extract_actions_from_log(log_content)
        workers = helper._extract_workers_from_log(log_content)

        print(f"抽出された概要: {summary}")
        print(f"抽出された詳細: {details}")
        print(f"抽出されたアクション: {actions}")
        print(f"抽出されたワーカー: {workers}")

    finally:
        # 一時ファイル削除
        Path(temp_log_path).unlink()

    print("\n✅ ログファイル処理テスト完了")


def test_batch_processing() -> None:
    """バッチ処理のテスト"""
    print("\n=== バッチ処理テスト ===")

    # 複数の結果データ作成
    results_data = [
        {
            "session_id": "batch_session_001",
            "title": "バッチ処理テスト1",
            "summary": "バッチ処理の第1回テスト",
            "details": "複数Issue作成のテスト",
            "actions": "テスト結果の確認",
            "workers": ["Queen", "Developer"],
            "timestamp": datetime.now().isoformat(),
        },
        {
            "session_id": "batch_session_002",
            "title": "バッチ処理テスト2",
            "summary": "バッチ処理の第2回テスト",
            "details": "並列処理能力の確認",
            "actions": "パフォーマンス測定",
            "workers": ["Queen", "Analyst"],
            "timestamp": datetime.now().isoformat(),
        },
    ]

    print(f"バッチ処理テスト: {len(results_data)}個のIssue")
    print("※実際のIssue作成は行いません（テストモード）")

    # バッチ処理のプレビュー
    for i, result_data in enumerate(results_data):
        print(f"\n--- Issue {i + 1} ---")
        print(f"タイトル: {result_data['title']}")
        print(f"概要: {result_data['summary']}")
        print(f"ワーカー: {', '.join(result_data['workers'])}")

    print("\n✅ バッチ処理テスト完了")


def test_configuration_loading() -> None:
    """設定ファイル読み込みのテスト"""
    print("\n=== 設定ファイル読み込みテスト ===")

    try:
        helper = HiveGitHubHelper()
        config = helper.creator.config

        print("設定ファイル読み込み成功")
        print(
            f"GitHub設定: {config.get('github', {}).get('issue', {}).get('title_prefix', 'N/A')}"
        )
        print(f"テンプレート: {config.get('template', {}).get('file', 'N/A')}")
        print(f"実行モード: {config.get('execution', {}).get('mode', 'N/A')}")

        # ラベル設定確認
        labels = config.get("github", {}).get("issue", {}).get("labels", {})
        print(f"デフォルトラベル: {labels.get('default', [])}")

    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return False

    print("\n✅ 設定ファイル読み込みテスト完了")
    return True


def main() -> None:
    """メイン関数"""
    print("🐝 Hive GitHub Issue作成機能テストスイート")
    print("=" * 60)

    test_results = []

    # テスト実行
    try:
        test_results.append(test_configuration_loading())
        test_basic_functionality()
        test_worker_results_formatting()
        test_log_file_processing()
        test_batch_processing()

        print("\n" + "=" * 60)
        print("🎉 全テスト完了")
        print("=" * 60)

        print("\n📋 実行可能なコマンド例:")
        print("1. プレビュー:")
        print(
            "   python scripts/create_github_issue.py --preview --title 'テスト' --summary '概要' --workers 'Queen,Developer'"
        )

        print("\n2. Issue作成:")
        print(
            "   python scripts/create_github_issue.py --title 'テスト' --summary '概要' --actions 'アクション' --workers 'Queen,Developer'"
        )

        print("\n3. ヘルパー関数使用:")
        print(
            "   from scripts.github_issue_helper import create_issue_from_queen_worker"
        )
        print("   create_issue_from_queen_worker('session_001', 'タイトル', '概要')")

    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
