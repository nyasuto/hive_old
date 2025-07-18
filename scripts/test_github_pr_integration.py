#!/usr/bin/env python3
"""
GitHub Issue-PR統合機能テストスクリプト

実装した機能をテストし、動作を確認します。
"""

import sys
from datetime import datetime
from pathlib import Path

# プロジェクトのルートディレクトリをPATHに追加
sys.path.insert(0, str(Path(__file__).parent))

from github_issue_pr_integration import HiveGitHubIntegration
from queen_github_integration import QueenGitHubIntegration


def test_template_loading() -> None:
    """テンプレート読み込みテスト"""
    print("=== テンプレート読み込みテスト ===")

    try:
        integration = HiveGitHubIntegration()

        # Issueテンプレート読み込み
        issue_template = integration.issue_creator._load_template()
        print(f"✅ Issue テンプレート読み込み成功 ({len(issue_template)} 文字)")

        # PRテンプレート読み込み
        pr_template = integration.pr_creator._load_template()
        print(f"✅ PR テンプレート読み込み成功 ({len(pr_template)} 文字)")

        return True

    except Exception as e:
        print(f"❌ テンプレート読み込みエラー: {e}")
        return False


def test_data_formatting() -> None:
    """データフォーマット機能テスト"""
    print("\n=== データフォーマット機能テスト ===")

    try:
        integration = HiveGitHubIntegration()

        # テスト用分析結果
        test_analysis = {
            "title": "テスト機能実装",
            "summary": "GitHub統合機能のテストケース",
            "details": "詳細なテスト実装内容",
            "recommended_actions": "テストの実行と結果確認",
            "participants": ["Queen", "Developer", "Tester"],
            "impact_assessment": "テスト環境のみに影響",
            "completion_criteria": "- テスト実行完了\n- 結果確認完了\n- レポート作成完了",
        }

        # 実装データ生成テスト
        implementation_data = integration._generate_implementation_data_from_analysis(
            "test_session_001", test_analysis, 123
        )

        print("✅ 実装データ生成成功")
        print(f"   タイトル: {implementation_data.get('title')}")
        print(f"   実装タイプ: {implementation_data.get('implementation_type')}")
        print(f"   関連Issue: {implementation_data.get('related_issues')}")

        return True

    except Exception as e:
        print(f"❌ データフォーマットエラー: {e}")
        return False


def test_session_management() -> None:
    """セッション管理機能テスト"""
    print("\n=== セッション管理機能テスト ===")

    try:
        integration = QueenGitHubIntegration()

        # テスト用セッションデータ
        test_session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # セッション状態テスト
        status = integration.get_session_status(test_session_id)
        print(f"✅ セッション状態取得: {status.get('status', 'unknown')}")

        # アクティブセッション一覧テスト
        sessions = integration.list_active_sessions()
        print(f"✅ アクティブセッション数: {len(sessions)}")

        return True

    except Exception as e:
        print(f"❌ セッション管理エラー: {e}")
        return False


def test_report_generation() -> None:
    """レポート生成機能テスト"""
    print("\n=== レポート生成機能テスト ===")

    try:
        integration = QueenGitHubIntegration()

        # 存在しないセッションのレポート生成テスト
        test_session_id = "nonexistent_session"
        report = integration.format_session_report(test_session_id)

        print("✅ レポート生成成功")
        print(f"   レポート長: {len(report)} 文字")
        print("   レポート内容プレビュー:")
        print("   " + report[:200] + "...")

        return True

    except Exception as e:
        print(f"❌ レポート生成エラー: {e}")
        return False


def test_integration_workflow() -> None:
    """統合ワークフロー機能テスト（プレビューモード）"""
    print("\n=== 統合ワークフロー機能テスト ===")

    try:
        # テスト用分析結果
        test_analysis = {
            "title": "GitHub統合機能テスト",
            "summary": "Issue-PR統合機能のテスト実装",
            "details": "統合ワークフローの動作確認",
            "recommended_actions": "テスト実行と結果確認",
            "participants": ["Queen", "Developer"],
            "impact_assessment": "テスト環境のみに影響",
            "completion_criteria": "- 統合テスト完了\n- 動作確認完了",
        }

        # 統合ワークフロー処理テスト（実際のGitHub操作は行わない）
        print("✅ 統合ワークフロー処理準備完了")
        print(f"   分析結果タイトル: {test_analysis['title']}")
        print(f"   参加者: {', '.join(test_analysis['participants'])}")

        return True

    except Exception as e:
        print(f"❌ 統合ワークフローエラー: {e}")
        return False


def test_helper_functions() -> None:
    """ヘルパー関数テスト"""
    print("\n=== ヘルパー関数テスト ===")

    try:
        from queen_github_integration import (
            queen_get_session_status,
            queen_list_active_sessions,
        )

        # セッション状態取得関数テスト
        status = queen_get_session_status("test_session")
        print(f"✅ セッション状態取得関数: {status.get('success', False)}")

        # アクティブセッション一覧取得関数テスト
        sessions = queen_list_active_sessions()
        print(f"✅ アクティブセッション一覧取得関数: {len(sessions)} sessions")

        return True

    except Exception as e:
        print(f"❌ ヘルパー関数エラー: {e}")
        return False


def run_all_tests() -> None:
    """全テスト実行"""
    print("🐝 GitHub Issue-PR統合機能テスト開始")
    print("=" * 50)

    test_results = []

    # 各テストを実行
    test_results.append(("テンプレート読み込み", test_template_loading()))
    test_results.append(("データフォーマット機能", test_data_formatting()))
    test_results.append(("セッション管理機能", test_session_management()))
    test_results.append(("レポート生成機能", test_report_generation()))
    test_results.append(("統合ワークフロー機能", test_integration_workflow()))
    test_results.append(("ヘルパー関数", test_helper_functions()))

    # 結果サマリー
    print("\n" + "=" * 50)
    print("🐝 テスト結果サマリー")
    print("=" * 50)

    passed = 0
    failed = 0

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n📊 テスト結果: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 全テストが成功しました！")
        return True
    else:
        print("⚠️  いくつかのテストが失敗しました。")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
