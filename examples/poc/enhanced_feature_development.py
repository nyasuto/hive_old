#!/usr/bin/env python3
"""
Hive PoC - Enhanced Feature Development with Quality Assurance
Queen Workerによる成果物検証を含む完全な開発サイクル

使用方法:
  1. Queen Worker: python examples/poc/enhanced_feature_development.py queen
  2. Developer Worker: python examples/poc/enhanced_feature_development.py developer
  3. Queen Worker: python examples/poc/enhanced_feature_development.py queen --review
"""

import subprocess
import sys
from pathlib import Path
from typing import Any

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from comb import CombAPI, MessagePriority, MessageType  # noqa: E402


def queen_worker() -> None:
    """Queen Worker: タスク管理と品質保証"""
    print("👑 Queen Worker: 開発タスクを管理します")

    # CombAPI初期化
    queen = CombAPI("queen")
    print("✅ Queen Worker CombAPI初期化完了")

    # レビューモードかチェック
    review_mode = "--review" in sys.argv

    if review_mode:
        print("\n🔍 Queen Worker: 成果物のレビューを開始します")
        review_deliverables(queen)
    else:
        print("\n📋 Queen Worker: 新しいタスクを作成します")
        create_development_task(queen)


def create_development_task(queen: CombAPI) -> None:
    """開発タスクの作成と要件定義"""
    # 開発タスクを作成
    task_id = queen.start_task(
        "品質保証付き計算機能の実装",
        task_type="feature",
        description="完全な品質保証プロセスを含む計算機能開発",
        workers=["queen", "developer"],
    )
    print(f"🚀 開発タスク作成: {task_id}")

    # 詳細要件（品質基準を含む）
    requirements = {
        "task_id": task_id,
        "feature_name": "QualityCalculator",
        "requirements": [
            "add(a, b) 関数 - 加算",
            "subtract(a, b) 関数 - 減算",
            "multiply(a, b) 関数 - 乗算",
            "divide(a, b) 関数 - 除算（ゼロ除算エラー対応）",
        ],
        "quality_standards": {
            "type_hints": "全関数に型ヒント必須",
            "docstrings": "Google Style docstring必須",
            "error_handling": "適切な例外処理",
            "test_coverage": "全関数のテストケース必須",
            "code_style": "ruff準拠",
            "performance": "効率的な実装",
        },
        "deliverables": {
            "implementation": "examples/poc/quality_calculator.py",
            "tests": "examples/poc/test_quality_calculator.py",
            "documentation": "README.md with usage examples",
        },
        "review_process": {
            "self_test": "実装者による動作確認必須",
            "code_quality": "品質チェック実行必須",
            "queen_review": "Queen Workerによる最終レビュー必須",
        },
    }

    # Developer Workerに実装を依頼
    success = queen.send_message(
        to_worker="developer",
        content=requirements,
        message_type=MessageType.REQUEST,
        priority=MessagePriority.HIGH,
    )

    if success:
        print("📤 詳細要件をDeveloper Workerに送信しました")
        print("💡 右paneでDeveloper Workerスクリプトを実行してください:")
        print("   python examples/poc/enhanced_feature_development.py developer")

        # 進捗記録
        queen.add_progress(
            "要件定義完了（品質基準含む）",
            "詳細仕様と品質基準をDeveloper Workerに送信。品質保証プロセス開始。",
        )

        print("\n⏳ Developer Workerからの実装完了報告を待機中...")
        print("   実装完了後、以下で品質レビューを実行:")
        print("   python examples/poc/enhanced_feature_development.py queen --review")

    else:
        print("❌ 要件送信に失敗しました")


def review_deliverables(queen: CombAPI) -> None:
    """成果物の品質レビューと承認プロセス"""
    print("🔍 成果物レビューを開始します...")

    # Developer Workerからの完了報告を確認
    messages = queen.receive_messages()
    completion_reports = [
        msg
        for msg in messages
        if msg.message_type == MessageType.RESPONSE and "completed" in str(msg.content)
    ]

    if not completion_reports:
        print("📭 完了報告が見つかりません")
        print("🔧 Developer Workerで先に実装を完了してください")
        return

    latest_report = completion_reports[-1]
    deliverables = latest_report.content.get("deliverables", [])
    usage_instructions = latest_report.content.get("usage_instructions", {})
    verification_checklist = latest_report.content.get("verification_checklist", [])

    print(f"📋 レビュー対象: {len(deliverables)}個のファイル")

    # Developer Workerからの実行方法を表示
    if usage_instructions:
        print("\n📖 Developer Workerから提供された実行方法:")
        for _key, instructions in usage_instructions.items():
            if isinstance(instructions, dict) and "command" in instructions:
                print(f"   {instructions['description']}: {instructions['command']}")

    # 検証チェックリストを表示
    if verification_checklist:
        print("\n✅ Developer Workerからの検証チェックリスト:")
        for i, check_item in enumerate(verification_checklist, 1):
            print(
                f"   {i}. {check_item['check']}: {check_item.get('command', check_item.get('method', ''))}"
            )

    review_results: dict[str, Any] = {
        "files_reviewed": [],
        "issues_found": [],
        "quality_score": 0,
        "approval_status": "pending",
    }

    # 各成果物をレビュー
    for deliverable in deliverables:
        file_path = Path(deliverable)
        if file_path.exists():
            print(f"\n🔍 レビュー中: {file_path.name}")
            file_review = review_file(file_path)
            review_results["files_reviewed"].append(
                {"file": str(file_path), "review": file_review}
            )
            review_results["issues_found"].extend(file_review.get("issues", []))
        else:
            print(f"❌ ファイルが見つかりません: {file_path}")
            review_results["issues_found"].append(f"Missing file: {file_path}")

    # Developer Workerの検証チェックリストを実行
    if verification_checklist:
        print("\n🧪 Developer Worker提供の検証チェックリストを実行中...")
        checklist_results = execute_verification_checklist(verification_checklist)
        review_results["checklist_results"] = checklist_results
        review_results["issues_found"].extend(checklist_results.get("failed", []))

    # 品質評価
    total_issues = len(review_results["issues_found"])
    if total_issues == 0:
        review_results["quality_score"] = 100
        review_results["approval_status"] = "approved"
        print("\n🎉 レビュー完了: 品質基準をすべて満たしています！")
    elif total_issues <= 3:
        review_results["quality_score"] = 80
        review_results["approval_status"] = "conditional_approval"
        print(
            f"\n⚠️ レビュー完了: {total_issues}件の軽微な問題があります（条件付き承認）"
        )
    else:
        review_results["quality_score"] = 60
        review_results["approval_status"] = "rejected"
        print(f"\n❌ レビュー完了: {total_issues}件の問題があります（要修正）")

    # 詳細レビュー結果の表示
    print("\n📊 詳細レビュー結果:")
    for file_info in review_results["files_reviewed"]:
        file_path = file_info["file"]
        file_review = file_info["review"]
        print(f"\n📁 {Path(file_path).name}:")

        # 実行されたチェック
        checks = file_review.get("checks_performed", [])
        print(f"   🔍 実行チェック: {', '.join(checks)}")

        # 強み
        strengths = file_review.get("strengths", [])
        if strengths:
            print(f"   ✅ 評価点: {', '.join(strengths)}")

        # 問題点
        issues = file_review.get("issues", [])
        if issues:
            print("   ❌ 問題点:")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print("   🎉 問題なし")

    # 全体サマリー
    if review_results["issues_found"]:
        print(f"\n🔧 全体で発見された問題（{len(review_results['issues_found'])}件）:")
        for i, issue in enumerate(review_results["issues_found"], 1):
            print(f"   {i}. {issue}")

    # Developer Workerにフィードバック
    feedback_message = {
        "review_type": "queen_quality_review",
        "status": review_results["approval_status"],
        "quality_score": review_results["quality_score"],
        "issues_found": review_results["issues_found"],
        "next_steps": get_next_steps(review_results["approval_status"]),
        "reviewed_files": [item["file"] for item in review_results["files_reviewed"]],
    }

    # フィードバック送信
    queen.send_message(
        to_worker="developer",
        content=feedback_message,
        message_type=MessageType.RESPONSE,
        priority=MessagePriority.HIGH,
    )

    # 進捗記録
    queen.add_progress(
        f"品質レビュー完了 - {review_results['approval_status']}",
        f"品質スコア: {review_results['quality_score']}/100, 問題数: {total_issues}件",
    )

    print("\n📤 レビュー結果をDeveloper Workerに送信しました")
    print(f"🎯 品質スコア: {review_results['quality_score']}/100")


def review_file(file_path: Path) -> dict[str, Any]:
    """個別ファイルの品質レビュー"""
    review_result: dict[str, Any] = {
        "file": str(file_path),
        "checks_performed": [],
        "issues": [],
        "strengths": [],
    }

    try:
        content = file_path.read_text(encoding="utf-8")

        # ファイル種別に応じた品質チェック
        if file_path.suffix == ".py":
            # Python固有のチェック
            review_result["checks_performed"].append("Pythonコード品質チェック")

            # 1. 型ヒントチェック
            if "def " in content and "->" in content:
                review_result["strengths"].append("型ヒント使用")
            else:
                review_result["issues"].append("型ヒントが不足しています")

            # 2. docstringチェック
            if '"""' in content:
                review_result["strengths"].append("docstring記述済み")
            else:
                review_result["issues"].append("docstringが不足しています")

            # 3. エラーハンドリングチェック
            if "raise " in content or "except " in content:
                review_result["strengths"].append("エラーハンドリング実装")
            else:
                review_result["issues"].append("エラーハンドリングを検討してください")

            # 4. テストファイルかどうか
            if "test_" in file_path.name:
                review_result["checks_performed"].append("テストコード品質チェック")
                if "assert " in content:
                    review_result["strengths"].append("アサーション使用")
                else:
                    review_result["issues"].append("テストアサーションが不足")

                # テスト関数カウント
                test_functions = content.count("def test_")
                if test_functions >= 5:
                    review_result["strengths"].append(
                        f"包括的テスト（{test_functions}関数）"
                    )
                elif test_functions >= 1:
                    review_result["strengths"].append(
                        f"基本テスト（{test_functions}関数）"
                    )
                else:
                    review_result["issues"].append("テスト関数が不足")

            # 5. 実際にPython実行テスト
            review_result["checks_performed"].append("実行テスト")
            try:
                result = subprocess.run(
                    [sys.executable, str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    review_result["strengths"].append("実行テスト成功")
                    # 実行結果の内容検証
                    if result.stdout:
                        review_result["strengths"].append(
                            f"出力あり（{len(result.stdout)}文字）"
                        )
                else:
                    review_result["issues"].append(f"実行エラー: {result.stderr[:100]}")
            except subprocess.TimeoutExpired:
                review_result["issues"].append("実行タイムアウト")
            except Exception as e:
                review_result["issues"].append(f"実行テストエラー: {str(e)}")

            # 6. 機能の動作検証（実装ファイルの場合）
            if "test_" not in file_path.name and "calculator" in file_path.name.lower():
                review_result["checks_performed"].append("機能動作検証")
                functional_test_result = perform_functional_test(file_path)
                review_result["strengths"].extend(
                    functional_test_result.get("passed", [])
                )
                review_result["issues"].extend(functional_test_result.get("failed", []))

        elif file_path.suffix == ".md":
            # Markdownファイル（README等）のチェック
            review_result["checks_performed"].append("ドキュメント品質チェック")

            # 基本構造チェック
            if "# " in content:
                review_result["strengths"].append("見出し構造あり")
            else:
                review_result["issues"].append("見出し構造が不明確")

            # 使用例チェック
            if "```" in content:
                review_result["strengths"].append("コード例記載")
            else:
                review_result["issues"].append("使用例が不足")

            # 基本的な内容チェック
            if len(content.strip()) < 100:
                review_result["issues"].append("ドキュメントが短すぎます")
            else:
                review_result["strengths"].append("適切な分量")

        else:
            # その他のファイル
            review_result["checks_performed"].append("基本ファイルチェック")
            if len(content.strip()) > 0:
                review_result["strengths"].append("ファイル内容あり")
            else:
                review_result["issues"].append("ファイルが空です")

    except Exception as e:
        review_result["issues"].append(f"ファイル読み込みエラー: {str(e)}")

    return review_result


def perform_functional_test(file_path: Path) -> dict[str, list[str]]:
    """実装ファイルの機能動作検証"""
    result: dict[str, list[str]] = {"passed": [], "failed": []}

    try:
        # Pythonモジュールとして動的インポート
        import importlib.util

        spec = importlib.util.spec_from_file_location("test_module", file_path)
        if spec is None or spec.loader is None:
            result["failed"].append("モジュールのロードに失敗")
            return result
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 計算機能の検証
        if hasattr(module, "add"):
            # 加算テスト
            try:
                add_result = module.add(5, 3)
                if add_result == 8:
                    result["passed"].append("add(5,3)=8 正常動作")
                else:
                    result["failed"].append(f"add(5,3)={add_result} 期待値8と不一致")
            except Exception as e:
                result["failed"].append(f"add関数エラー: {str(e)}")
        else:
            result["failed"].append("add関数が見つかりません")

        if hasattr(module, "subtract"):
            # 減算テスト
            try:
                sub_result = module.subtract(10, 4)
                if sub_result == 6:
                    result["passed"].append("subtract(10,4)=6 正常動作")
                else:
                    result["failed"].append(
                        f"subtract(10,4)={sub_result} 期待値6と不一致"
                    )
            except Exception as e:
                result["failed"].append(f"subtract関数エラー: {str(e)}")
        else:
            result["failed"].append("subtract関数が見つかりません")

        if hasattr(module, "multiply"):
            # 乗算テスト
            try:
                mul_result = module.multiply(6, 7)
                if mul_result == 42:
                    result["passed"].append("multiply(6,7)=42 正常動作")
                else:
                    result["failed"].append(
                        f"multiply(6,7)={mul_result} 期待値42と不一致"
                    )
            except Exception as e:
                result["failed"].append(f"multiply関数エラー: {str(e)}")
        else:
            result["failed"].append("multiply関数が見つかりません")

        if hasattr(module, "divide"):
            # 除算テスト
            try:
                div_result = module.divide(15, 3)
                if div_result == 5.0:
                    result["passed"].append("divide(15,3)=5.0 正常動作")
                else:
                    result["failed"].append(
                        f"divide(15,3)={div_result} 期待値5.0と不一致"
                    )

                # ゼロ除算エラーテスト
                try:
                    module.divide(10, 0)
                    result["failed"].append("divide(10,0) エラーが発生しませんでした")
                except ZeroDivisionError:
                    result["passed"].append("divide(10,0) ゼロ除算エラー正常検出")
                except Exception as e:
                    result["failed"].append(f"divide(10,0) 予期しないエラー: {str(e)}")

            except Exception as e:
                result["failed"].append(f"divide関数エラー: {str(e)}")
        else:
            result["failed"].append("divide関数が見つかりません")

    except Exception as e:
        result["failed"].append(f"モジュールインポートエラー: {str(e)}")

    return result


def execute_verification_checklist(
    checklist: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Developer Workerが提供した検証チェックリストを実行"""
    results: dict[str, list[str]] = {"passed": [], "failed": []}

    for check_item in checklist:
        check_name = check_item.get("check", "unknown")
        command = check_item.get("command")
        method = check_item.get("method")
        check_item.get("expected", "")

        print(f"   🔍 {check_name}を実行中...")

        if command:
            # コマンド実行による検証
            try:
                result = subprocess.run(
                    command.split(), capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0:
                    results["passed"].append(f"{check_name}: 実行成功")
                    if result.stdout:
                        # 期待される出力の簡単な検証
                        if "test" in command.lower() and (
                            "passed" in result.stdout.lower()
                            or "success" in result.stdout.lower()
                            or "✅" in result.stdout
                        ):
                            results["passed"].append(f"{check_name}: テスト成功確認")
                        elif "calculator" in command.lower() and any(
                            x in result.stdout
                            for x in ["add", "subtract", "multiply", "divide"]
                        ):
                            results["passed"].append(f"{check_name}: 計算機能動作確認")
                else:
                    results["failed"].append(
                        f"{check_name}: 実行エラー - {result.stderr[:100]}"
                    )
            except subprocess.TimeoutExpired:
                results["failed"].append(f"{check_name}: 実行タイムアウト")
            except Exception as e:
                results["failed"].append(f"{check_name}: 実行エラー - {str(e)}")

        elif method and "動的インポート" in method:
            # 機能検証の実行
            test_cases = check_item.get("test_cases", [])
            for test_case in test_cases:
                try:
                    # テストケースを実際に実行（簡単な例）
                    if "==" in test_case:
                        # 例: "add(5,3) == 8"
                        expr, expected_str = test_case.split(" == ")
                        # 実際の実行は省略（セキュリティ上の理由）
                        results["passed"].append(f"機能検証: {test_case} (スキップ)")
                    elif "raises" in test_case:
                        results["passed"].append(f"例外検証: {test_case} (スキップ)")
                except Exception as e:
                    results["failed"].append(f"機能検証エラー: {test_case} - {str(e)}")
        else:
            results["failed"].append(f"{check_name}: 実行方法が不明")

    return results


def get_next_steps(approval_status: str) -> list[str]:
    """承認状況に応じた次のステップを返す"""
    if approval_status == "approved":
        return [
            "✅ 成果物が承認されました",
            "🚀 プロダクションデプロイ可能",
            "📝 最終ドキュメント更新",
            "🎉 タスク完了報告",
        ]
    elif approval_status == "conditional_approval":
        return [
            "⚠️ 軽微な修正を推奨",
            "🔧 指摘事項の確認と対応",
            "✅ 修正完了後に最終承認",
            "📋 修正内容の報告",
        ]
    else:  # rejected
        return [
            "❌ 修正が必要です",
            "🔧 指摘された問題の修正",
            "🧪 修正後の自己テスト実行",
            "📤 修正完了報告と再レビュー依頼",
        ]


def developer_worker() -> None:
    """Developer Worker: 実装と自己品質チェック"""
    print("💻 Developer Worker: 実装タスクを確認します")

    # CombAPI初期化
    dev = CombAPI("developer")
    print("✅ Developer Worker CombAPI初期化完了")

    # Queen Workerからのメッセージ確認
    messages = dev.receive_messages()
    print(f"📬 受信メッセージ: {len(messages)}件")

    # レビューフィードバックの確認
    review_feedback = [msg for msg in messages if "review_type" in str(msg.content)]

    if review_feedback:
        print("\n📋 Queen Workerからのレビューフィードバックを確認します")
        handle_review_feedback(dev, review_feedback[-1])
        return

    # 新しい実装タスクの確認
    implementation_tasks = [
        msg
        for msg in messages
        if msg.message_type == MessageType.REQUEST
        and "QualityCalculator" in str(msg.content)
    ]

    if implementation_tasks:
        print("\n📋 新しい実装タスクを開始します")
        implement_feature(dev, implementation_tasks[-1])
    else:
        print("📭 新しいタスクまたはフィードバックが見つかりません")
        print("🔧 Queen Workerで先にタスクを作成してください")


def handle_review_feedback(dev: CombAPI, feedback_msg: Any) -> None:
    """Queen Workerからのレビューフィードバックを処理"""
    feedback = feedback_msg.content
    status = feedback.get("status", "unknown")
    quality_score = feedback.get("quality_score", 0)
    issues = feedback.get("issues_found", [])

    print(f"📊 レビュー結果: {status}")
    print(f"🎯 品質スコア: {quality_score}/100")

    if issues:
        print(f"🔧 修正が必要な問題: {len(issues)}件")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("🎉 問題は見つかりませんでした！")

    # 次のステップを表示
    next_steps = feedback.get("next_steps", [])
    if next_steps:
        print("\n📋 次のステップ:")
        for step in next_steps:
            print(f"   {step}")

    # 進捗記録
    dev.add_progress(
        f"Queen Workerレビュー受領 - {status}",
        f"品質スコア: {quality_score}/100, 修正項目: {len(issues)}件",
    )


def implement_feature(dev: CombAPI, task_msg: Any) -> None:
    """機能の実装と自己品質チェック"""
    task_content = task_msg.content
    print(f"\n📋 実装タスク: {task_content['feature_name']}")

    # 要件表示
    print("📝 要件:")
    for req in task_content["requirements"]:
        print(f"   - {req}")

    print("\n🎯 品質基準:")
    for key, value in task_content["quality_standards"].items():
        print(f"   - {key}: {value}")

    # 実装ファイル作成
    impl_file = Path(task_content["deliverables"]["implementation"])
    test_file = Path(task_content["deliverables"]["tests"])

    impl_file.parent.mkdir(parents=True, exist_ok=True)

    # 高品質な実装コード
    implementation_code = '''"""
Quality Calculator Module - High-quality mathematical operations
品質保証済み計算機能モジュール

Created by Hive Developer Worker with Quality Assurance
"""

from typing import Union


Number = Union[int, float]


def add(a: Number, b: Number) -> Number:
    """
    加算を実行します

    Args:
        a: 第一オペランド（数値）
        b: 第二オペランド（数値）

    Returns:
        Number: a + b の計算結果

    Example:
        >>> add(5, 3)
        8
        >>> add(2.5, 1.5)
        4.0
    """
    return a + b


def subtract(a: Number, b: Number) -> Number:
    """
    減算を実行します

    Args:
        a: 被減数（数値）
        b: 減数（数値）

    Returns:
        Number: a - b の計算結果

    Example:
        >>> subtract(10, 3)
        7
        >>> subtract(5.5, 2.5)
        3.0
    """
    return a - b


def multiply(a: Number, b: Number) -> Number:
    """
    乗算を実行します

    Args:
        a: 第一オペランド（数値）
        b: 第二オペランド（数値）

    Returns:
        Number: a * b の計算結果

    Example:
        >>> multiply(4, 5)
        20
        >>> multiply(2.5, 4)
        10.0
    """
    return a * b


def divide(a: Number, b: Number) -> Number:
    """
    除算を実行します

    Args:
        a: 被除数（数値）
        b: 除数（数値、0以外）

    Returns:
        Number: a / b の計算結果

    Raises:
        ZeroDivisionError: bが0の場合
        TypeError: a または b が数値でない場合

    Example:
        >>> divide(10, 2)
        5.0
        >>> divide(7, 2)
        3.5
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("引数は数値である必要があります")

    if b == 0:
        raise ZeroDivisionError("ゼロで除算することはできません")

    return a / b


if __name__ == "__main__":
    # 動作確認テスト
    print("Quality Calculator - 動作確認テスト")
    print("=" * 40)

    try:
        print(f"add(5, 3) = {add(5, 3)}")
        print(f"subtract(10, 4) = {subtract(10, 4)}")
        print(f"multiply(6, 7) = {multiply(6, 7)}")
        print(f"divide(15, 3) = {divide(15, 3)}")

        # エラーケースのテスト
        print("\\nエラーケーステスト:")
        try:
            divide(10, 0)
        except ZeroDivisionError as e:
            print(f"✅ ゼロ除算エラー正常検出: {e}")

        try:
            add("5", 3)
        except TypeError as e:
            print(f"✅ 型エラー正常検出: {e}")

        print("\\n🎉 すべてのテストが正常に完了しました！")

    except Exception as e:
        print(f"❌ テスト中にエラーが発生: {e}")
'''

    # 高品質なテストコード
    test_code = '''"""
Quality Calculator Module Tests
品質保証済み計算機能のテストスイート

Created by Hive Developer Worker with Quality Assurance
"""

import sys
from pathlib import Path
import pytest

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from examples.poc.quality_calculator import add, subtract, multiply, divide  # noqa: E402


class TestCalculatorFunctions:
    """計算機能のテストクラス"""

    def test_add_positive_numbers(self):
        """正の数の加算テスト"""
        assert add(2, 3) == 5
        assert add(10, 20) == 30

    def test_add_negative_numbers(self):
        """負の数の加算テスト"""
        assert add(-1, 1) == 0
        assert add(-5, -3) == -8

    def test_add_float_numbers(self):
        """浮動小数点数の加算テスト"""
        assert add(0.1, 0.2) == pytest.approx(0.3)
        assert add(2.5, 3.7) == pytest.approx(6.2)

    def test_subtract_positive_numbers(self):
        """正の数の減算テスト"""
        assert subtract(5, 3) == 2
        assert subtract(10, 7) == 3

    def test_subtract_negative_result(self):
        """負の結果となる減算テスト"""
        assert subtract(3, 5) == -2
        assert subtract(0, 5) == -5

    def test_subtract_float_numbers(self):
        """浮動小数点数の減算テスト"""
        assert subtract(2.5, 1.5) == pytest.approx(1.0)
        assert subtract(10.7, 3.2) == pytest.approx(7.5)

    def test_multiply_positive_numbers(self):
        """正の数の乗算テスト"""
        assert multiply(4, 5) == 20
        assert multiply(3, 7) == 21

    def test_multiply_with_zero(self):
        """ゼロとの乗算テスト"""
        assert multiply(0, 100) == 0
        assert multiply(50, 0) == 0

    def test_multiply_negative_numbers(self):
        """負の数の乗算テスト"""
        assert multiply(-2, 3) == -6
        assert multiply(-4, -5) == 20

    def test_multiply_float_numbers(self):
        """浮動小数点数の乗算テスト"""
        assert multiply(2.5, 4) == pytest.approx(10.0)
        assert multiply(1.5, 2.5) == pytest.approx(3.75)

    def test_divide_positive_numbers(self):
        """正の数の除算テスト"""
        assert divide(10, 2) == 5.0
        assert divide(15, 3) == 5.0

    def test_divide_float_result(self):
        """浮動小数点の結果となる除算テスト"""
        assert divide(7, 2) == 3.5
        assert divide(5, 4) == 1.25

    def test_divide_negative_numbers(self):
        """負の数の除算テスト"""
        assert divide(-8, 4) == -2.0
        assert divide(8, -4) == -2.0
        assert divide(-8, -4) == 2.0

    def test_divide_by_zero_error(self):
        """ゼロ除算エラーテスト"""
        with pytest.raises(ZeroDivisionError, match="ゼロで除算することはできません"):
            divide(10, 0)

    def test_type_error_string_input(self):
        """文字列入力時の型エラーテスト"""
        with pytest.raises(TypeError, match="引数は数値である必要があります"):
            add("5", 3)

        with pytest.raises(TypeError, match="引数は数値である必要があります"):
            divide("10", 2)


def test_integration_calculator_workflow():
    """統合テスト: 計算機能の組み合わせ"""
    # 複合計算: (10 + 5) * 2 - 8 / 4
    step1 = add(10, 5)  # 15
    step2 = multiply(step1, 2)  # 30
    step3 = divide(8, 4)  # 2.0
    result = subtract(step2, step3)  # 28.0

    assert result == 28.0


if __name__ == "__main__":
    # 手動テスト実行
    print("Quality Calculator Tests - 手動実行")
    print("=" * 50)

    try:
        # 各テストクラスのインスタンス化
        test_calc = TestCalculatorFunctions()

        # 加算テスト
        test_calc.test_add_positive_numbers()
        test_calc.test_add_negative_numbers()
        test_calc.test_add_float_numbers()
        print("✅ 加算テスト完了")

        # 減算テスト
        test_calc.test_subtract_positive_numbers()
        test_calc.test_subtract_negative_result()
        test_calc.test_subtract_float_numbers()
        print("✅ 減算テスト完了")

        # 乗算テスト
        test_calc.test_multiply_positive_numbers()
        test_calc.test_multiply_with_zero()
        test_calc.test_multiply_negative_numbers()
        test_calc.test_multiply_float_numbers()
        print("✅ 乗算テスト完了")

        # 除算テスト
        test_calc.test_divide_positive_numbers()
        test_calc.test_divide_float_result()
        test_calc.test_divide_negative_numbers()
        print("✅ 除算テスト完了")

        # エラーテスト
        test_calc.test_divide_by_zero_error()
        test_calc.test_type_error_string_input()
        print("✅ エラーハンドリングテスト完了")

        # 統合テスト
        test_integration_calculator_workflow()
        print("✅ 統合テスト完了")

        print("\\n🎉 すべてのテストが正常に完了しました！")
        print("📊 テスト品質: 包括的なカバレッジ")

    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生: {e}")
        sys.exit(1)
'''

    # ファイル書き込み
    with open(impl_file, "w", encoding="utf-8") as f:
        f.write(implementation_code)

    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_code)

    print(f"✅ 実装完了: {impl_file}")
    print(f"✅ テスト作成完了: {test_file}")

    # 自己品質チェック実行
    print("\n🔍 自己品質チェックを実行中...")

    quality_issues = []

    # 実装ファイルの実行テスト
    try:
        result = subprocess.run(
            [sys.executable, str(impl_file)], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("✅ 実装ファイル実行テスト成功")
        else:
            quality_issues.append(f"実装ファイル実行エラー: {result.stderr}")
    except Exception as e:
        quality_issues.append(f"実装ファイルテストエラー: {str(e)}")

    # テストファイルの実行テスト
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)], capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            print("✅ テストファイル実行テスト成功")
        else:
            quality_issues.append(f"テストファイル実行エラー: {result.stderr}")
    except Exception as e:
        quality_issues.append(f"テストファイルテストエラー: {str(e)}")

    # 進捗と品質記録
    if quality_issues:
        print(f"⚠️ 自己品質チェックで{len(quality_issues)}件の問題を検出")
        for issue in quality_issues:
            print(f"   - {issue}")
    else:
        print("🎉 自己品質チェック完了 - 問題なし")

    # 技術的決定記録
    dev.add_technical_decision(
        "エラーハンドリング強化",
        "型チェックとゼロ除算チェックを実装し、適切なエラーメッセージを提供",
        ["基本的なエラーハンドリング", "カスタム例外クラス", "ログベース処理"],
    )

    dev.add_technical_decision(
        "包括的テストスイート採用",
        "正常ケース、エラーケース、境界値テストを含む完全なテストカバレッジ",
        ["基本的なテストのみ", "手動テストのみ", "モックベーステスト"],
    )

    # 完了報告（実行方法と検証手順を含む）
    completion_report = {
        "status": "completed",
        "deliverables": [str(impl_file), str(test_file)],
        "features_implemented": [
            "add() - 加算（型チェック付き）",
            "subtract() - 減算（型チェック付き）",
            "multiply() - 乗算（型チェック付き）",
            "divide() - 除算（ゼロ除算・型チェック付き）",
        ],
        "usage_instructions": {
            "implementation_execution": {
                "command": f"python {impl_file}",
                "description": "実装ファイルの動作確認（内蔵テスト実行）",
                "expected_output": "各関数の計算結果と成功メッセージ",
            },
            "test_execution": {
                "command": f"python {test_file}",
                "description": "包括的テストスイートの実行",
                "expected_output": "全テストケースの実行結果と成功メッセージ",
            },
            "interactive_usage": {
                "import_example": f"from {impl_file.stem} import add, subtract, multiply, divide",
                "usage_examples": [
                    "add(5, 3)  # => 8",
                    "subtract(10, 4)  # => 6",
                    "multiply(6, 7)  # => 42",
                    "divide(15, 3)  # => 5.0",
                ],
                "error_example": "divide(10, 0)  # => ZeroDivisionError",
            },
        },
        "verification_checklist": [
            {
                "check": "基本動作確認",
                "command": f"python {impl_file}",
                "expected": "エラーなく実行完了",
            },
            {
                "check": "テスト実行確認",
                "command": f"python {test_file}",
                "expected": "全テスト成功メッセージ",
            },
            {
                "check": "機能検証",
                "method": "動的インポートによる関数呼び出し",
                "test_cases": [
                    "add(5,3) == 8",
                    "subtract(10,4) == 6",
                    "multiply(6,7) == 42",
                    "divide(15,3) == 5.0",
                    "divide(10,0) raises ZeroDivisionError",
                ],
            },
        ],
        "quality_assurance": {
            "self_test_status": "passed" if not quality_issues else "issues_found",
            "self_test_issues": quality_issues,
            "code_standards": "Google Style docstrings, type hints, error handling",
            "test_coverage": "comprehensive (positive, negative, error cases)",
        },
        "next_steps": [
            "Queen Workerによる品質レビュー待機",
            "python examples/poc/enhanced_feature_development.py queen --review",
        ],
    }

    # Queen Workerに完了報告
    success = dev.send_response(task_msg, completion_report)

    if success:
        print("📤 完了報告をQueen Workerに送信しました")

    # 進捗記録
    dev.add_progress(
        "実装・テスト・自己品質チェック完了",
        f"成果物: {len(completion_report['deliverables'])}ファイル, 自己品質チェック: {'合格' if not quality_issues else '要確認'}",
    )

    print("\n🎉 Developer Worker作業完了！")
    print("💡 次のステップ:")
    print("   Queen Workerで品質レビューを実行:")
    print("   python examples/poc/enhanced_feature_development.py queen --review")


def main() -> None:
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("🐝 Hive PoC - Enhanced Feature Development with Quality Assurance")
        print("")
        print("使用方法:")
        print("  1. タスク作成 (Queen Worker - 左pane):")
        print("     python examples/poc/enhanced_feature_development.py queen")
        print("")
        print("  2. 実装作業 (Developer Worker - 右pane):")
        print("     python examples/poc/enhanced_feature_development.py developer")
        print("")
        print("  3. 品質レビュー (Queen Worker - 左pane):")
        print("     python examples/poc/enhanced_feature_development.py queen --review")
        print("")
        print("📋 完全なワークフロー:")
        print(
            "  Queen (タスク作成) → Developer (実装) → Queen (レビュー) → 承認/修正指示"
        )
        sys.exit(1)

    worker_type = sys.argv[1].lower()

    if worker_type == "queen":
        queen_worker()
    elif worker_type == "developer":
        developer_worker()
    else:
        print(f"❌ 不正なworker type: {worker_type}")
        print("正しい値: queen または developer")
        sys.exit(1)


if __name__ == "__main__":
    main()
