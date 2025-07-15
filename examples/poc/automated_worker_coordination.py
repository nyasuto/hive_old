#!/usr/bin/env python3
"""
Hive PoC - Automated Worker Coordination System
Queen Worker と Developer Worker 間の完全自動化された協調システム

Issue #50 実装: Queen-Developer自動協調システム

使用方法:
  1. 自動協調実行: python examples/poc/automated_worker_coordination.py auto
  2. 協調状況監視: python examples/poc/automated_worker_coordination.py monitor
  3. テストシナリオ: python examples/poc/automated_worker_coordination.py test
"""

import asyncio
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from comb import CombAPI, MessagePriority, MessageType  # noqa: E402

# Enhanced PoCから既存クラスをインポート
sys.path.insert(0, str(Path(__file__).parent))
if True:  # pragma: no cover
    from enhanced_feature_development import (  # noqa: E402  # type: ignore[import]
        AIQualityChecker,
        FixSuggestionEngine,
        QualityAssessment,
        QualityIssue,
    )


@dataclass
class IterationResult:
    """単一反復の実行結果"""

    iteration: int
    quality_score: int
    issues_found: list[QualityIssue]
    fix_suggestions: list[Any]
    execution_time: float
    status: str  # success, needs_improvement, failed


@dataclass
class CoordinationResult:
    """協調プロセス全体の結果"""

    success: bool
    iterations: int
    final_quality_score: int
    coordination_log: list[str]
    total_execution_time: float
    reason: str | None = None


class AutomatedWorkerCoordination:
    """Worker間の自動協調制御システム"""

    def __init__(
        self,
        max_iterations: int = 3,
        quality_threshold: int = 90,
        timeout_seconds: int = 300,
    ):
        """
        自動協調システムの初期化

        Args:
            max_iterations: 最大反復回数
            quality_threshold: 品質基準スコア
            timeout_seconds: 各操作のタイムアウト
        """
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.timeout_seconds = timeout_seconds

        # Worker APIの初期化
        self.queen_proxy = EnhancedQueenProxy()
        self.developer_proxy = EnhancedDeveloperProxy()

        # AI機能の初期化
        self.ai_checker = AIQualityChecker()
        self.fix_engine = FixSuggestionEngine()

        # 協調ログ
        self.coordination_log: list[str] = []

    async def execute_automated_development_cycle(
        self, task_spec: dict
    ) -> CoordinationResult:
        """
        完全自動化された開発サイクルの実行

        Args:
            task_spec: 開発タスクの仕様

        Returns:
            CoordinationResult: 協調プロセスの結果
        """
        start_time = time.time()
        print("🤖 自動協調開発サイクル開始...")
        print(f"🎯 目標品質スコア: {self.quality_threshold}/100")
        print(f"🔄 最大反復回数: {self.max_iterations}")
        print("=" * 50)

        self.coordination_log = []
        current_task_spec = task_spec.copy()

        for iteration in range(self.max_iterations):
            print(f"\n📍 反復 {iteration + 1}/{self.max_iterations} 開始...")
            iteration_start = time.time()

            try:
                iteration_result = await self._execute_single_iteration(
                    current_task_spec, iteration
                )

                iteration_time = time.time() - iteration_start
                iteration_result.execution_time = iteration_time

                print(
                    f"⏱️ 反復{iteration + 1}完了 ({iteration_time:.1f}秒) - "
                    f"品質スコア: {iteration_result.quality_score}/100"
                )

                # 品質基準達成チェック
                if iteration_result.quality_score >= self.quality_threshold:
                    total_time = time.time() - start_time
                    self.coordination_log.append(
                        f"SUCCESS: 反復{iteration + 1}で品質基準達成 (スコア: {iteration_result.quality_score})"
                    )

                    print(
                        f"\n🎉 成功! 品質基準達成 (スコア: {iteration_result.quality_score}/100)"
                    )
                    print(f"⏱️ 総実行時間: {total_time:.1f}秒")

                    return CoordinationResult(
                        success=True,
                        iterations=iteration + 1,
                        final_quality_score=iteration_result.quality_score,
                        coordination_log=self.coordination_log,
                        total_execution_time=total_time,
                    )

                # 改善が必要な場合は次の反復のためにタスク仕様を強化
                if iteration < self.max_iterations - 1:
                    current_task_spec = self._enhance_task_spec(
                        current_task_spec, iteration_result
                    )
                    print("🔄 タスク仕様を改善して次の反復へ...")

            except Exception as e:
                error_msg = f"反復{iteration + 1}でエラー発生: {str(e)}"
                self.coordination_log.append(f"ERROR: {error_msg}")
                print(f"❌ {error_msg}")

                # クリティカルエラーの場合は即座に終了
                if "timeout" in str(e).lower() or "connection" in str(e).lower():
                    break

        # 最大反復に達した場合
        total_time = time.time() - start_time
        self.coordination_log.append(
            f"FAILURE: 最大反復数{self.max_iterations}に達しました"
        )

        print("\n❌ 失敗: 最大反復数に達しました")
        print(f"⏱️ 総実行時間: {total_time:.1f}秒")

        return CoordinationResult(
            success=False,
            reason="max_iterations_exceeded",
            iterations=self.max_iterations,
            coordination_log=self.coordination_log,
            total_execution_time=total_time,
            final_quality_score=0,
        )

    async def _execute_single_iteration(
        self, task_spec: dict, iteration: int
    ) -> IterationResult:
        """
        単一反復の実行

        Args:
            task_spec: タスク仕様
            iteration: 反復番号

        Returns:
            IterationResult: 反復実行結果
        """
        start_time = time.time()

        # Phase 1: Queen → Developer (タスク指示)
        print("   📤 Phase 1: Queen がタスクを送信中...")
        queen_success = await self.queen_proxy.send_enhanced_task_with_history(
            task_spec, self.coordination_log
        )

        if not queen_success:
            raise Exception("Queen からのタスク送信に失敗")

        self.coordination_log.append(f"反復{iteration + 1}: Queen タスク送信完了")

        # Phase 2: Developer実行 (実装・テスト)
        print("   ⚙️ Phase 2: Developer がタスクを実行中...")
        await asyncio.sleep(1)  # 実際の処理時間をシミュレート

        dev_result = await self.developer_proxy.execute_task_with_improvement_context(
            task_spec
        )
        self.coordination_log.append(f"反復{iteration + 1}: Developer 実装完了")

        # Phase 3: Queen Review (AI品質チェック)
        print("   🔍 Phase 3: Queen がAI品質レビュー実行中...")
        review_result = await self.queen_proxy.conduct_ai_powered_review(dev_result)
        self.coordination_log.append(
            f"反復{iteration + 1}: Queen AI品質レビュー完了 (スコア: {review_result.overall_score})"
        )

        # Phase 4: フィードバック送信
        print("   💬 Phase 4: フィードバック送信中...")
        if review_result.overall_score >= self.quality_threshold:
            # 成功 - 承認メッセージ送信
            await self.queen_proxy.send_approval(review_result)
            self.coordination_log.append(f"反復{iteration + 1}: Queen 承認送信")
            status = "success"
            fix_suggestions = []
        else:
            # 改善必要 - 修正提案送信
            fix_suggestions = self.fix_engine.generate_suggestions(review_result.issues)
            await self.queen_proxy.send_improvement_suggestions(fix_suggestions)
            self.coordination_log.append(
                f"反復{iteration + 1}: Queen 改善提案送信 ({len(fix_suggestions)}件)"
            )
            status = "needs_improvement"

        execution_time = time.time() - start_time

        return IterationResult(
            iteration=iteration,
            quality_score=review_result.overall_score,
            issues_found=review_result.issues,
            fix_suggestions=fix_suggestions,
            execution_time=execution_time,
            status=status,
        )

    def _enhance_task_spec(
        self, base_task: dict, iteration_result: IterationResult
    ) -> dict:
        """
        反復結果に基づいてタスク仕様を改善

        Args:
            base_task: 基本タスク仕様
            iteration_result: 前回の反復結果

        Returns:
            改善されたタスク仕様
        """
        enhanced_task = base_task.copy()

        # 反復コンテキストを追加
        enhanced_task["iteration_context"] = {
            "current_iteration": iteration_result.iteration + 2,  # 次の反復番号
            "previous_score": iteration_result.quality_score,
            "previous_issues": [
                {
                    "type": issue.issue_type,
                    "severity": issue.severity,
                    "description": issue.description,
                }
                for issue in iteration_result.issues_found
            ],
            "improvement_focus": self._determine_improvement_focus(iteration_result),
            "fix_suggestions": [
                {
                    "description": suggestion.description,
                    "fix_type": suggestion.fix_type,
                    "priority": suggestion.priority,
                }
                for suggestion in iteration_result.fix_suggestions
            ],
        }

        # 品質基準を強化
        if "quality_standards" in enhanced_task:
            enhanced_task["quality_standards"]["focus_areas"] = (
                self._determine_improvement_focus(iteration_result)
            )

        return enhanced_task

    def _determine_improvement_focus(
        self, iteration_result: IterationResult
    ) -> list[str]:
        """
        反復結果から改善フォーカスエリアを決定

        Args:
            iteration_result: 反復結果

        Returns:
            改善フォーカスエリアのリスト
        """
        focus_areas = []

        # 問題の種類に基づいてフォーカスを決定
        issue_types = [issue.issue_type for issue in iteration_result.issues_found]

        if "type_error" in issue_types:
            focus_areas.append("型安全性の向上")
        if "missing_type_hints" in issue_types:
            focus_areas.append("型アノテーションの完全性")
        if "missing_docstrings" in issue_types:
            focus_areas.append("ドキュメント品質")
        if "missing_error_handling" in issue_types:
            focus_areas.append("エラーハンドリングの強化")
        if "test_assertion" in issue_types:
            focus_areas.append("テストの正確性")

        # デフォルトフォーカス
        if not focus_areas:
            focus_areas = ["コード品質全般の向上"]

        return focus_areas


class EnhancedQueenProxy:
    """Queen Worker の拡張機能プロキシ"""

    def __init__(self) -> None:
        self.queen_api = CombAPI("queen")

    async def send_enhanced_task_with_history(
        self, base_task: dict, iteration_history: list[str]
    ) -> bool:
        """
        反復履歴を考慮した改善されたタスク指示

        Args:
            base_task: 基本タスク
            iteration_history: 反復履歴

        Returns:
            送信成功の可否
        """
        enhanced_task = {
            **base_task,
            "coordination_metadata": {
                "coordination_type": "automated_cycle",
                "iteration_history": iteration_history[-5:],  # 最新5件のみ
                "timestamp": time.time(),
            },
        }

        try:
            success = self.queen_api.send_message(
                to_worker="developer",
                content=enhanced_task,
                message_type=MessageType.REQUEST,
                priority=MessagePriority.HIGH,
            )
            return success
        except Exception as e:
            print(f"Queen メッセージ送信エラー: {e}")
            return False

    async def conduct_ai_powered_review(self, deliverables: dict) -> QualityAssessment:
        """
        AI機能を活用した高度なレビュー

        Args:
            deliverables: 成果物

        Returns:
            QualityAssessment: 品質評価結果
        """
        # 実際のファイルが存在する場合はAI品質チェック実行
        implementation_file = Path("examples/poc/quality_calculator.py")
        if implementation_file.exists():
            ai_checker = AIQualityChecker()
            return ai_checker.assess_code_quality(implementation_file)

        # ファイルが存在しない場合はモック評価（反復ごとに改善）
        from enhanced_feature_development import QualityAssessment

        # 反復に応じて品質スコアを改善
        simulated_score = deliverables.get("simulated_quality_score", 75)
        improvements_applied = deliverables.get("improvements_applied", 0)

        # 問題を反復ごとに減らす
        issues = []
        if simulated_score < 85:
            issues.append(
                QualityIssue(
                    issue_type="missing_type_hints",
                    severity="medium",
                    description="型ヒントが不足しています",
                )
            )
        if simulated_score < 90:
            issues.append(
                QualityIssue(
                    issue_type="missing_docstrings",
                    severity="low",
                    description="docstringが不足しています",
                )
            )

        return QualityAssessment(
            overall_score=simulated_score,
            issues=issues,
            fix_suggestions=[],
            detailed_analysis={
                "ai_powered": True,
                "automated_coordination": True,
                "simulated": True,
                "improvements_applied": improvements_applied,
                "timestamp": time.time(),
            },
        )

    async def send_approval(self, review_result: QualityAssessment) -> bool:
        """
        承認メッセージの送信

        Args:
            review_result: レビュー結果

        Returns:
            送信成功の可否
        """
        approval_content = {
            "review_type": "automated_coordination_approval",
            "status": "approved",
            "quality_score": review_result.overall_score,
            "message": f"🎉 品質基準達成! スコア: {review_result.overall_score}/100",
            "next_steps": ["承認完了", "プロダクション準備", "ドキュメント最終化"],
        }

        try:
            return self.queen_api.send_message(
                to_worker="developer",
                content=approval_content,
                message_type=MessageType.RESPONSE,
                priority=MessagePriority.HIGH,
            )
        except Exception as e:
            print(f"Queen 承認メッセージ送信エラー: {e}")
            return False

    async def send_improvement_suggestions(self, fix_suggestions: list[Any]) -> bool:
        """
        改善提案の送信

        Args:
            fix_suggestions: 修正提案リスト

        Returns:
            送信成功の可否
        """
        improvement_content = {
            "review_type": "automated_coordination_improvement",
            "status": "needs_improvement",
            "suggestions_count": len(fix_suggestions),
            "suggestions": [
                {
                    "description": suggestion.description,
                    "fix_type": suggestion.fix_type,
                    "priority": suggestion.priority,
                    "estimated_effort": suggestion.estimated_effort,
                }
                for suggestion in fix_suggestions
            ],
            "message": f"🔧 改善が必要です。{len(fix_suggestions)}件の提案があります。",
        }

        try:
            return self.queen_api.send_message(
                to_worker="developer",
                content=improvement_content,
                message_type=MessageType.RESPONSE,
                priority=MessagePriority.HIGH,
            )
        except Exception as e:
            print(f"Queen 改善提案送信エラー: {e}")
            return False


class EnhancedDeveloperProxy:
    """Developer Worker の拡張機能プロキシ"""

    def __init__(self) -> None:
        self.developer_api = CombAPI("developer")

    async def execute_task_with_improvement_context(self, task_message: dict) -> dict:
        """
        改善コンテキストを考慮したタスク実行（実際のファイル生成）

        Args:
            task_message: タスクメッセージ

        Returns:
            実行結果
        """
        iteration_context = task_message.get("iteration_context", {})
        previous_issues = iteration_context.get("previous_issues", [])

        # 前回の問題を考慮した実装
        if previous_issues:
            print(f"   📚 前回の問題を考慮: {len(previous_issues)}件の改善点")
            for issue in previous_issues:
                print(f"      - {issue['type']}: {issue['description']}")

        # 実際のファイル生成
        impl_file = Path("examples/poc/automated_quality_calculator.py")
        test_file = Path("examples/poc/test_automated_quality_calculator.py")

        # 反復番号に応じて品質を向上させる
        current_iteration = iteration_context.get("current_iteration", 1)

        # 実装ファイルの生成
        impl_content = self._generate_implementation_code(
            current_iteration, previous_issues
        )
        test_content = self._generate_test_code(current_iteration, previous_issues)

        # ファイル書き込み
        impl_file.parent.mkdir(parents=True, exist_ok=True)
        impl_file.write_text(impl_content, encoding="utf-8")
        test_file.write_text(test_content, encoding="utf-8")

        print(f"   ✅ 実装ファイル生成: {impl_file}")
        print(f"   ✅ テストファイル生成: {test_file}")

        # 実装時間をシミュレート
        await asyncio.sleep(0.5)

        # 品質スコア計算
        base_quality = min(70 + (current_iteration - 1) * 15, 95)

        result = {
            "implementation_status": "completed",
            "deliverables": [str(impl_file), str(test_file)],
            "simulated_quality_score": base_quality,
            "improvements_applied": len(previous_issues),
            "iteration_context": iteration_context,
            "files_created": {
                "implementation": str(impl_file),
                "tests": str(test_file),
                "timestamp": time.time(),
            },
        }

        # 完了報告を送信
        try:
            self.developer_api.send_message(
                to_worker="queen",
                content=result,
                message_type=MessageType.RESPONSE,
                priority=MessagePriority.MEDIUM,
            )
        except Exception as e:
            print(f"Developer 完了報告送信エラー: {e}")

        return result

    def _generate_implementation_code(
        self, iteration: int, previous_issues: list
    ) -> str:
        """反復に応じた実装コード生成"""
        # 基本的な実装
        base_code = '''"""
Automated Quality Calculator - 自動協調システムで生成
反復回数: {iteration}回目

自動協調システムにより生成された高品質な計算機能
"""

Number = int | float


def add(a: Number, b: Number) -> Number:{docstring_add}
    {type_check}return a + b


def subtract(a: Number, b: Number) -> Number:{docstring_subtract}
    {type_check}return a - b


def multiply(a: Number, b: Number) -> Number:{docstring_multiply}
    {type_check}return a * b


def divide(a: Number, b: Number) -> Number:{docstring_divide}
    {type_check}if b == 0:
        raise ZeroDivisionError("ゼロで除算することはできません")
    return a / b


if __name__ == "__main__":
    print("🤖 自動協調システム生成 - 品質計算機能テスト")
    print(f"反復: {iteration}回目")
    print("=" * 50)

    try:
        print(f"add(5, 3) = {{add(5, 3)}}")
        print(f"subtract(10, 4) = {{subtract(10, 4)}}")
        print(f"multiply(6, 7) = {{multiply(6, 7)}}")
        print(f"divide(15, 3) = {{divide(15, 3)}}")
        print("✅ 全ての基本計算が正常に動作しました")

        # エラーケーステスト
        try:
            divide(10, 0)
        except ZeroDivisionError as e:
            print(f"✅ ゼロ除算エラー正常検出: {{e}}")

    except Exception as e:
        print(f"❌ エラーが発生: {{e}}")
'''

        # 反復に応じて機能を追加
        additions = {
            "type_import": "",
            "docstring_add": "",
            "docstring_subtract": "",
            "docstring_multiply": "",
            "docstring_divide": "",
            "type_check": "",
        }

        # 反復1以降: 型チェック追加
        if iteration >= 1:
            issue_types = [issue.get("type", "") for issue in previous_issues]

            if "missing_type_hints" in issue_types or iteration >= 2:
                # docstring追加
                additions["docstring_add"] = '''
    """
    加算を実行します

    Args:
        a: 第一オペランド
        b: 第二オペランド

    Returns:
        Number: 計算結果
    """'''
                additions["docstring_subtract"] = '''
    """減算を実行します"""'''
                additions["docstring_multiply"] = '''
    """乗算を実行します"""'''
                additions["docstring_divide"] = '''
    """
    除算を実行します

    Raises:
        ZeroDivisionError: ゼロ除算の場合
    """'''

            if "type_error" in issue_types or iteration >= 3:
                # 型チェック追加
                additions[
                    "type_check"
                ] = """if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("引数は数値である必要があります")
    """

        return base_code.format(iteration=iteration, **additions)

    def _generate_test_code(self, iteration: int, previous_issues: list) -> str:
        """反復に応じたテストコード生成"""
        base_test = '''"""
Automated Quality Calculator Tests - 自動協調システムで生成
反復回数: {iteration}回目

自動協調システムにより生成された包括的テストスイート
"""

import sys
from pathlib import Path
import pytest

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from examples.poc.automated_quality_calculator import add, subtract, multiply, divide


class TestCalculatorFunctions:
    """計算機能の包括的テスト（反復{iteration}回目生成）"""

    def test_add_basic(self):
        """基本的な加算テスト"""
        assert add(2, 3) == 5
        assert add(0, 0) == 0
        assert add(-1, 1) == 0

    def test_subtract_basic(self):
        """基本的な減算テスト"""
        assert subtract(5, 3) == 2
        assert subtract(0, 0) == 0
        assert subtract(1, 1) == 0

    def test_multiply_basic(self):
        """基本的な乗算テスト"""
        assert multiply(4, 5) == 20
        assert multiply(0, 100) == 0
        assert multiply(-2, 3) == -6

    def test_divide_basic(self):
        """基本的な除算テスト"""
        assert divide(10, 2) == 5.0
        assert divide(7, 2) == 3.5

    def test_divide_zero_error(self):
        """ゼロ除算エラーテスト"""
        with pytest.raises(ZeroDivisionError):
            divide(10, 0)

{advanced_tests}

if __name__ == "__main__":
    print("🧪 自動協調システム生成テスト実行")
    print(f"反復: {iteration}回目")
    print("=" * 50)

    test_calc = TestCalculatorFunctions()

    try:
        test_calc.test_add_basic()
        test_calc.test_subtract_basic()
        test_calc.test_multiply_basic()
        test_calc.test_divide_basic()
        test_calc.test_divide_zero_error()
        print("✅ 全てのテストが正常に完了しました")

    except Exception as e:
        print(f"❌ テスト実行中にエラー: {{e}}")
'''

        # 反復に応じて高度なテストを追加
        advanced_tests = ""
        if iteration >= 2:
            advanced_tests += '''
    def test_add_floats(self):
        """浮動小数点数の加算テスト"""
        assert add(0.1, 0.2) == pytest.approx(0.3)
        assert add(2.5, 3.7) == pytest.approx(6.2)

    def test_negative_numbers(self):
        """負の数のテスト"""
        assert add(-5, -3) == -8
        assert subtract(-5, -3) == -2
        assert multiply(-4, -5) == 20'''

        if iteration >= 3:
            advanced_tests += '''

    def test_type_validation(self):
        """型チェックテスト"""
        with pytest.raises(TypeError):
            add("5", 3)
        with pytest.raises(TypeError):
            divide(10, "2")'''

        return base_test.format(iteration=iteration, advanced_tests=advanced_tests)


async def run_automated_coordination_demo() -> CoordinationResult:
    """自動協調デモの実行"""
    print("🚀 自動協調システムデモ開始")
    print("=" * 50)

    # サンプルタスク仕様
    demo_task = {
        "task_id": "auto_coord_demo",
        "feature_name": "AutomatedCalculator",
        "requirements": [
            "add(a, b) 関数 - 加算",
            "subtract(a, b) 関数 - 減算",
            "型安全性とエラーハンドリング",
        ],
        "quality_standards": {
            "type_hints": "必須",
            "docstrings": "Google Style必須",
            "error_handling": "適切な例外処理",
            "target_score": 90,
        },
    }

    # 自動協調システムを初期化
    coordinator = AutomatedWorkerCoordination(
        max_iterations=3, quality_threshold=90, timeout_seconds=60
    )

    # 自動開発サイクルを実行
    result = await coordinator.execute_automated_development_cycle(demo_task)

    # 結果表示
    print("\n" + "=" * 50)
    print("📊 自動協調結果サマリー")
    print("=" * 50)
    print(f"成功: {'✅' if result.success else '❌'}")
    print(f"反復回数: {result.iterations}/{coordinator.max_iterations}")
    print(f"最終品質スコア: {result.final_quality_score}/100")
    print(f"総実行時間: {result.total_execution_time:.1f}秒")

    if result.reason:
        print(f"終了理由: {result.reason}")

    print(f"\n📝 協調ログ ({len(result.coordination_log)}件):")
    for i, log_entry in enumerate(result.coordination_log, 1):
        print(f"   {i}. {log_entry}")

    return result


async def run_test_scenarios() -> list[dict[str, Any]]:
    """複数のテストシナリオを実行"""
    print("🧪 自動協調テストシナリオ実行")
    print("=" * 50)

    scenarios = [
        {
            "name": "高品質タスク（1回で成功予定）",
            "quality_threshold": 70,
            "max_iterations": 2,
        },
        {
            "name": "標準品質タスク（反復改善予定）",
            "quality_threshold": 90,
            "max_iterations": 3,
        },
        {
            "name": "困難タスク（最大反復予定）",
            "quality_threshold": 95,
            "max_iterations": 2,
        },
    ]

    results = []

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🎯 シナリオ {i}: {scenario['name']}")
        print("-" * 30)

        demo_task = {
            "task_id": f"scenario_{i}",
            "feature_name": f"TestCalculator_{i}",
            "requirements": ["基本的な計算機能", "品質保証"],
            "quality_standards": {"target_score": scenario["quality_threshold"]},
        }

        max_iter = cast(int, scenario["max_iterations"])
        qual_thresh = cast(int, scenario["quality_threshold"])
        coordinator = AutomatedWorkerCoordination(
            max_iterations=max_iter,
            quality_threshold=qual_thresh,
            timeout_seconds=30,
        )

        result = await coordinator.execute_automated_development_cycle(demo_task)
        results.append({"scenario": scenario["name"], "result": result})

        status = "✅ 成功" if result.success else "❌ 失敗"
        print(
            f"結果: {status} ({result.iterations}反復, {result.total_execution_time:.1f}秒)"
        )

    # 全体サマリー
    print("\n" + "=" * 50)
    print("📈 テストシナリオ結果サマリー")
    print("=" * 50)

    success_results = [
        r for r in results if cast(CoordinationResult, r["result"]).success
    ]
    success_count = len(success_results)
    print(
        f"成功率: {success_count}/{len(results)} ({success_count / len(results) * 100:.1f}%)"
    )

    for i, result_data in enumerate(results, 1):
        coord_result = cast(CoordinationResult, result_data["result"])
        status = "✅" if coord_result.success else "❌"
        print(f"{i}. {status} {result_data['scenario']}")
        print(
            f"   反復: {coord_result.iterations}, スコア: {coord_result.final_quality_score}, 時間: {coord_result.total_execution_time:.1f}秒"
        )

    return results


def monitor_coordination_status() -> None:
    """協調システムの状況監視"""
    print("📊 協調システム状況監視")
    print("=" * 50)

    # Combメッセージの状況確認
    try:
        queen_api = CombAPI("queen")
        developer_api = CombAPI("developer")

        # メッセージ確認
        queen_messages = queen_api.receive_messages()
        dev_messages = developer_api.receive_messages()

        print(f"📬 Queen メッセージ: {len(queen_messages)}件")
        print(f"📬 Developer メッセージ: {len(dev_messages)}件")

        # 最新のメッセージ表示
        if queen_messages:
            latest = queen_messages[-1]
            print("\n最新Queen メッセージ:")
            print(f"   From: {latest.from_worker}")
            print(f"   Type: {latest.message_type}")
            print(f"   Time: {latest.timestamp}")

        if dev_messages:
            latest = dev_messages[-1]
            print("\n最新Developer メッセージ:")
            print(f"   From: {latest.from_worker}")
            print(f"   Type: {latest.message_type}")
            print(f"   Time: {latest.timestamp}")

    except Exception as e:
        print(f"⚠️ 監視エラー: {e}")

    # システム状況表示
    print("\n🔧 システム情報:")
    print(f"   プロジェクト: {project_root.name}")
    print(f"   PoC ディレクトリ: {Path(__file__).parent}")
    print("   Comb API: 利用可能")


def main() -> None:
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("🤖 Hive PoC - Automated Worker Coordination System")
        print("")
        print("使用方法:")
        print("  1. 自動協調デモ実行:")
        print("     python examples/poc/automated_worker_coordination.py auto")
        print("")
        print("  2. 協調状況監視:")
        print("     python examples/poc/automated_worker_coordination.py monitor")
        print("")
        print("  3. テストシナリオ実行:")
        print("     python examples/poc/automated_worker_coordination.py test")
        print("")
        print("💡 Issue #50: Queen-Developer自動協調システム")
        print("   完全自動化された品質改善サイクルを実行します")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "auto":
        print("🤖 自動協調デモを開始します...")
        asyncio.run(run_automated_coordination_demo())
    elif command == "monitor":
        monitor_coordination_status()
    elif command == "test":
        print("🧪 テストシナリオを開始します...")
        asyncio.run(run_test_scenarios())
    else:
        print(f"❌ 不正なコマンド: {command}")
        print("正しいコマンド: auto, monitor, test")
        sys.exit(1)


if __name__ == "__main__":
    main()
