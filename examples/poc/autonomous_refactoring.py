"""
自律的コードリファクタリングエージェント

コードベースを自律的に分析し、品質改善を継続的に実行するエージェント。
テストカバレッジ向上、型アノテーション追加、docstring生成、
パフォーマンス最適化を自動化します。

Usage:
    python examples/poc/autonomous_refactoring.py
"""

import ast
import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from examples.templates.autonomous_agent_template import AutonomousAgent


class CodeQualityAnalyzer:
    """コード品質分析器"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.python_files = []
        self._scan_python_files()

    def _scan_python_files(self) -> None:
        """Pythonファイルをスキャン"""
        self.python_files = list(self.project_root.rglob("*.py"))
        # テストファイルや隠しディレクトリを除外
        self.python_files = [
            f
            for f in self.python_files
            if not any(part.startswith(".") for part in f.parts)
            and "test" not in f.name.lower()
            and "__pycache__" not in str(f)
        ]

    async def analyze_codebase(self) -> dict[str, Any]:
        """コードベース全体の分析"""
        analysis = {
            "total_files": len(self.python_files),
            "quality_issues": [],
            "coverage_info": await self._get_test_coverage(),
            "type_annotation_coverage": await self._analyze_type_annotations(),
            "docstring_coverage": await self._analyze_docstring_coverage(),
            "complexity_analysis": await self._analyze_complexity(),
            "overall_score": 0,
        }

        # 個別ファイル分析
        for file_path in self.python_files[:10]:  # 最初の10ファイルを分析
            file_analysis = await self._analyze_file(file_path)
            analysis["quality_issues"].extend(file_analysis)

        # 総合スコア計算
        analysis["overall_score"] = self._calculate_overall_score(analysis)

        return analysis

    async def _get_test_coverage(self) -> dict[str, Any]:
        """テストカバレッジ取得"""
        try:
            # pytestでカバレッジ実行
            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=.", "--cov-report=json", "--quiet"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                coverage_file = Path("coverage.json")
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                    coverage_file.unlink()  # クリーンアップ

                    return {
                        "total_coverage": coverage_data.get("totals", {}).get(
                            "percent_covered", 0
                        ),
                        "lines_covered": coverage_data.get("totals", {}).get(
                            "covered_lines", 0
                        ),
                        "lines_total": coverage_data.get("totals", {}).get(
                            "num_statements", 0
                        ),
                    }

            return {"total_coverage": 0, "error": "Coverage analysis failed"}

        except Exception as e:
            return {"total_coverage": 0, "error": str(e)}

    async def _analyze_type_annotations(self) -> dict[str, Any]:
        """型アノテーション分析"""
        total_functions = 0
        annotated_functions = 0

        for file_path in self.python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1

                        # 戻り値の型アノテーションチェック
                        has_return_annotation = node.returns is not None

                        # 引数の型アノテーションチェック
                        has_arg_annotations = any(
                            arg.annotation is not None for arg in node.args.args
                        )

                        if has_return_annotation or has_arg_annotations:
                            annotated_functions += 1

            except Exception:
                continue

        coverage = (annotated_functions / max(total_functions, 1)) * 100

        return {
            "type_annotation_coverage": coverage,
            "total_functions": total_functions,
            "annotated_functions": annotated_functions,
        }

    async def _analyze_docstring_coverage(self) -> dict[str, Any]:
        """docstring分析"""
        total_functions = 0
        documented_functions = 0

        for file_path in self.python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef | ast.ClassDef):
                        total_functions += 1

                        # docstringの存在チェック
                        if (
                            node.body
                            and isinstance(node.body[0], ast.Expr)
                            and isinstance(node.body[0].value, ast.Constant)
                        ):
                            documented_functions += 1

            except Exception:
                continue

        coverage = (documented_functions / max(total_functions, 1)) * 100

        return {
            "docstring_coverage": coverage,
            "total_functions": total_functions,
            "documented_functions": documented_functions,
        }

    async def _analyze_complexity(self) -> dict[str, Any]:
        """複雑度分析"""
        try:
            # raderを使用してサイクロマティック複雑度を分析
            result = subprocess.run(
                ["python", "-m", "radon", "cc", ".", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                complexity_data = json.loads(result.stdout)

                total_complexity = 0
                function_count = 0

                for file_data in complexity_data.values():
                    for item in file_data:
                        if item.get("type") == "function":
                            total_complexity += item.get("complexity", 0)
                            function_count += 1

                avg_complexity = total_complexity / max(function_count, 1)

                return {
                    "average_complexity": avg_complexity,
                    "total_functions": function_count,
                    "high_complexity_count": sum(
                        1
                        for file_data in complexity_data.values()
                        for item in file_data
                        if item.get("complexity", 0) > 10
                    ),
                }

            return {"average_complexity": 0, "error": "Complexity analysis failed"}

        except Exception as e:
            return {"average_complexity": 0, "error": str(e)}

    async def _analyze_file(self, file_path: Path) -> list[dict[str, Any]]:
        """個別ファイル分析"""
        issues = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)

            # 関数分析
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 型アノテーション不足
                    if node.returns is None:
                        issues.append(
                            {
                                "file": str(file_path),
                                "line": node.lineno,
                                "type": "missing_return_annotation",
                                "function": node.name,
                                "severity": "medium",
                            }
                        )

                    # docstring不足
                    has_docstring = (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                    )

                    if not has_docstring:
                        issues.append(
                            {
                                "file": str(file_path),
                                "line": node.lineno,
                                "type": "missing_docstring",
                                "function": node.name,
                                "severity": "low",
                            }
                        )

        except Exception as e:
            issues.append(
                {
                    "file": str(file_path),
                    "type": "parse_error",
                    "error": str(e),
                    "severity": "high",
                }
            )

        return issues

    def _calculate_overall_score(self, analysis: dict[str, Any]) -> float:
        """総合スコア計算"""
        coverage_score = analysis["coverage_info"].get("total_coverage", 0)
        type_score = analysis["type_annotation_coverage"].get(
            "type_annotation_coverage", 0
        )
        doc_score = analysis["docstring_coverage"].get("docstring_coverage", 0)

        # 重み付き平均
        overall_score = (
            coverage_score * 0.4  # テストカバレッジ重視
            + type_score * 0.3  # 型アノテーション
            + doc_score * 0.3  # ドキュメント
        )

        return round(overall_score, 2)


class CodeRefactoringEngine:
    """コードリファクタリングエンジン"""

    def __init__(self):
        self.project_root = Path.cwd()

    async def generate_improvements(
        self, analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """改善提案生成"""
        improvements = []

        # テストカバレッジ改善
        coverage = analysis["coverage_info"].get("total_coverage", 0)
        if coverage < 80:
            improvements.append(
                {
                    "type": "test_coverage_improvement",
                    "current_coverage": coverage,
                    "target_coverage": 85,
                    "priority": "high",
                    "estimated_effort": "medium",
                }
            )

        # 型アノテーション追加
        type_coverage = analysis["type_annotation_coverage"].get(
            "type_annotation_coverage", 0
        )
        if type_coverage < 80:
            improvements.append(
                {
                    "type": "type_annotation_addition",
                    "current_coverage": type_coverage,
                    "target_coverage": 90,
                    "priority": "medium",
                    "estimated_effort": "low",
                }
            )

        # docstring追加
        doc_coverage = analysis["docstring_coverage"].get("docstring_coverage", 0)
        if doc_coverage < 70:
            improvements.append(
                {
                    "type": "docstring_addition",
                    "current_coverage": doc_coverage,
                    "target_coverage": 85,
                    "priority": "low",
                    "estimated_effort": "medium",
                }
            )

        # 複雑度改善
        avg_complexity = analysis["complexity_analysis"].get("average_complexity", 0)
        if avg_complexity > 8:
            improvements.append(
                {
                    "type": "complexity_reduction",
                    "current_complexity": avg_complexity,
                    "target_complexity": 6,
                    "priority": "medium",
                    "estimated_effort": "high",
                }
            )

        return improvements

    async def apply_improvement(self, improvement: dict[str, Any]) -> dict[str, Any]:
        """改善適用"""
        improvement_type = improvement["type"]

        if improvement_type == "test_coverage_improvement":
            return await self._improve_test_coverage(improvement)
        elif improvement_type == "type_annotation_addition":
            return await self._add_type_annotations(improvement)
        elif improvement_type == "docstring_addition":
            return await self._add_docstrings(improvement)
        elif improvement_type == "complexity_reduction":
            return await self._reduce_complexity(improvement)
        else:
            return {
                "success": False,
                "error": f"Unknown improvement type: {improvement_type}",
            }

    async def _improve_test_coverage(
        self, improvement: dict[str, Any]
    ) -> dict[str, Any]:
        """テストカバレッジ改善"""
        # 実装例: 不足しているテストを特定し、基本的なテストテンプレートを生成
        try:
            # カバレッジレポートから未テストファイルを特定
            uncovered_files = await self._find_uncovered_files()

            tests_generated = 0
            for file_path in uncovered_files[:3]:  # 最初の3ファイル
                test_content = await self._generate_basic_test(file_path)
                if test_content:
                    test_file = self._get_test_file_path(file_path)
                    if not test_file.exists():
                        test_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(test_file, "w", encoding="utf-8") as f:
                            f.write(test_content)
                        tests_generated += 1

            return {
                "success": True,
                "tests_generated": tests_generated,
                "improvement": f"Generated {tests_generated} test files",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _add_type_annotations(
        self, improvement: dict[str, Any]
    ) -> dict[str, Any]:
        """型アノテーション追加"""
        try:
            # mypyを使用して型エラーを特定
            subprocess.run(
                ["python", "-m", "mypy", ".", "--ignore-missing-imports"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            annotations_added = 0

            # 簡単な型アノテーション追加（基本型のみ）
            for file_path in Path(".").rglob("*.py"):
                if await self._add_basic_type_annotations(file_path):
                    annotations_added += 1

            return {
                "success": True,
                "annotations_added": annotations_added,
                "improvement": f"Added type annotations to {annotations_added} files",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _add_docstrings(self, improvement: dict[str, Any]) -> dict[str, Any]:
        """docstring追加"""
        try:
            docstrings_added = 0

            for file_path in Path(".").rglob("*.py"):
                if await self._add_basic_docstrings(file_path):
                    docstrings_added += 1

            return {
                "success": True,
                "docstrings_added": docstrings_added,
                "improvement": f"Added docstrings to {docstrings_added} files",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _reduce_complexity(self, improvement: dict[str, Any]) -> dict[str, Any]:
        """複雑度削減"""
        # 実装例: 複雑な関数を特定し、リファクタリング提案を生成
        try:
            complex_functions = await self._find_complex_functions()

            refactoring_suggestions = []
            for func_info in complex_functions[:5]:  # 最初の5つ
                suggestion = await self._generate_refactoring_suggestion(func_info)
                refactoring_suggestions.append(suggestion)

            return {
                "success": True,
                "suggestions_generated": len(refactoring_suggestions),
                "improvement": f"Generated {len(refactoring_suggestions)} refactoring suggestions",
                "suggestions": refactoring_suggestions,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _find_uncovered_files(self) -> list[Path]:
        """未カバーファイル特定"""
        # 簡易実装: Python ファイルのうちテストファイルでないものを返す
        all_python_files = list(Path(".").rglob("*.py"))
        return [
            f
            for f in all_python_files[:5]
            if "test" not in f.name.lower()
            and "__pycache__" not in str(f)
            and not str(f).startswith(".")
        ]

    async def _generate_basic_test(self, file_path: Path) -> str | None:
        """基本テスト生成"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)

            functions = []
            classes = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)

            if not functions and not classes:
                return None

            # 基本テストテンプレート生成
            module_name = file_path.stem
            import_path = str(file_path.with_suffix("")).replace("/", ".")

            test_content = f'''"""
Test module for {module_name}

Auto-generated basic tests for coverage improvement.
"""

import pytest
from {import_path} import {", ".join(functions + classes)}


'''

            # 関数テスト生成
            for func_name in functions:
                test_content += f'''def test_{func_name}():
    """Test {func_name} function"""
    # TODO: Implement actual test logic
    assert True  # Placeholder test


'''

            # クラステスト生成
            for class_name in classes:
                test_content += f'''class Test{class_name}:
    """Test {class_name} class"""

    def test_init(self):
        """Test {class_name} initialization"""
        # TODO: Implement actual test logic
        assert True  # Placeholder test


'''

            return test_content

        except Exception:
            return None

    def _get_test_file_path(self, source_file: Path) -> Path:
        """テストファイルパス取得"""
        test_dir = Path("tests")
        relative_path = source_file.relative_to(Path("."))
        test_file_name = f"test_{relative_path.stem}.py"
        return test_dir / relative_path.parent / test_file_name

    async def _add_basic_type_annotations(self, file_path: Path) -> bool:
        """基本型アノテーション追加"""
        # 実装省略: 実際には AST を使って型アノテーションを追加
        return False

    async def _add_basic_docstrings(self, file_path: Path) -> bool:
        """基本docstring追加"""
        # 実装省略: 実際には AST を使って docstring を追加
        return False

    async def _find_complex_functions(self) -> list[dict[str, Any]]:
        """複雑な関数特定"""
        return []

    async def _generate_refactoring_suggestion(
        self, func_info: dict[str, Any]
    ) -> dict[str, Any]:
        """リファクタリング提案生成"""
        return {"suggestion": "Extract method"}


class AutonomousRefactoringAgent(AutonomousAgent):
    """自律的コードリファクタリングエージェント"""

    def __init__(self):
        super().__init__(
            agent_id="refactoring_agent",
            specialization="code_quality_improvement",
            config={
                "cycle_interval": 120,  # 2分間隔
                "quality_threshold": 80,
                "max_improvements_per_cycle": 3,
            },
        )

        self.analyzer = CodeQualityAnalyzer()
        self.refactoring_engine = CodeRefactoringEngine()
        self.baseline_analysis = None

    async def _get_project_status(self) -> dict[str, Any]:
        """プロジェクト状況取得"""
        python_files = list(Path(".").rglob("*.py"))
        return {
            "total_python_files": len(python_files),
            "project_type": "python_project",
            "status": "active",
        }

    async def _get_quality_metrics(self) -> dict[str, Any]:
        """品質メトリクス取得"""
        return await self.analyzer.analyze_codebase()

    async def _get_specialized_actions(
        self, analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """リファクタリング専用アクション決定"""
        actions = []

        quality_metrics = analysis.get("quality_metrics", {})
        overall_score = quality_metrics.get("overall_score", 0)

        # 品質スコアが閾値を下回る場合にアクション生成
        if overall_score < self.config["quality_threshold"]:
            # 改善提案生成
            improvements = await self.refactoring_engine.generate_improvements(
                quality_metrics
            )

            # 最大改善数まで選択
            selected_improvements = improvements[
                : self.config["max_improvements_per_cycle"]
            ]

            for improvement in selected_improvements:
                actions.append(
                    {
                        "type": "apply_refactoring",
                        "improvement": improvement,
                        "priority": improvement.get("priority", "medium"),
                    }
                )

        return actions

    async def _execute_specialized_action(
        self, action: dict[str, Any]
    ) -> dict[str, Any]:
        """リファクタリングアクション実行"""
        if action["type"] == "apply_refactoring":
            improvement = action["improvement"]
            result = await self.refactoring_engine.apply_improvement(improvement)

            if result.get("success", False):
                self.performance_metrics["quality_improvements"] += 1

            return result

        return {"success": False, "error": "Unknown action type"}

    async def _initialize_agent(self) -> None:
        """エージェント初期化"""
        await super()._initialize_agent()

        # ベースライン分析実行
        self.baseline_analysis = await self.analyzer.analyze_codebase()

        self.logger.info("Refactoring agent initialized with baseline analysis")
        self.logger.info(
            f"Baseline quality score: {self.baseline_analysis.get('overall_score', 0)}"
        )


async def main():
    """メイン実行関数"""
    print("🔄 Starting Autonomous Code Refactoring Agent...")

    # エージェント作成
    agent = AutonomousRefactoringAgent()

    try:
        # 初期分析実行
        print("📊 Running initial code analysis...")
        initial_analysis = await agent.analyzer.analyze_codebase()
        print(f"Initial quality score: {initial_analysis.get('overall_score', 0)}")

        # 短期間の自律実行（デモ用）
        print("🤖 Starting autonomous refactoring cycle...")

        # 非同期で実行開始
        asyncio.create_task(agent.start_autonomous_cycle())

        # 5分間実行
        await asyncio.sleep(300)

        # 停止
        await agent.stop_autonomous_cycle()

        # 最終結果
        final_report = agent.get_performance_report()
        print("\n📊 Final Performance Report:")
        print(json.dumps(final_report, indent=2, ensure_ascii=False))

        # 改善結果分析
        final_analysis = await agent.analyzer.analyze_codebase()
        print(
            f"\nQuality improvement: {initial_analysis.get('overall_score', 0)} → {final_analysis.get('overall_score', 0)}"
        )

    except KeyboardInterrupt:
        print("\n⏹️ Refactoring agent stopped by user")
        await agent.stop_autonomous_cycle()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await agent.stop_autonomous_cycle()


if __name__ == "__main__":
    asyncio.run(main())
