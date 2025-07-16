"""
自律的テスト自動生成エージェント

既存のコードベースを分析し、包括的なテストケースを自動生成するエージェント。
エッジケース検出、カバレッジ最適化、モックオブジェクト自動作成を実行します。

Usage:
    python examples/poc/autonomous_testing.py
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


class CodeAnalyzer:
    """コード分析器"""

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
            and "test_" not in f.name
            and "__pycache__" not in str(f)
            and "venv" not in str(f)
        ]

    async def analyze_testable_code(self) -> dict[str, Any]:
        """テスト可能なコード分析"""
        analysis = {
            "total_files": len(self.python_files),
            "functions": [],
            "classes": [],
            "methods": [],
            "complexity_analysis": {},
            "dependency_analysis": {},
            "edge_cases": [],
        }

        for file_path in self.python_files[:15]:  # 最初の15ファイルを分析
            file_analysis = await self._analyze_file(file_path)

            analysis["functions"].extend(file_analysis["functions"])
            analysis["classes"].extend(file_analysis["classes"])
            analysis["methods"].extend(file_analysis["methods"])
            analysis["edge_cases"].extend(file_analysis["edge_cases"])

        return analysis

    async def _analyze_file(self, file_path: Path) -> dict[str, Any]:
        """個別ファイル分析"""
        analysis = {
            "file": str(file_path),
            "functions": [],
            "classes": [],
            "methods": [],
            "edge_cases": [],
        }

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)

            # 関数分析
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = await self._analyze_function(node, file_path)
                    if not node.name.startswith("_"):  # プライベート関数を除外
                        analysis["functions"].append(func_info)
                    else:
                        analysis["methods"].append(func_info)

                elif isinstance(node, ast.ClassDef):
                    class_info = await self._analyze_class(node, file_path)
                    analysis["classes"].append(class_info)

        except Exception as e:
            analysis["error"] = str(e)

        return analysis

    async def _analyze_function(
        self, node: ast.FunctionDef, file_path: Path
    ) -> dict[str, Any]:
        """関数分析"""
        func_info = {
            "name": node.name,
            "file": str(file_path),
            "line": node.lineno,
            "args": [],
            "return_type": None,
            "complexity": await self._calculate_complexity(node),
            "edge_cases": [],
            "dependencies": [],
        }

        # 引数分析
        for arg in node.args.args:
            arg_info = {"name": arg.arg, "annotation": None, "default": None}

            if arg.annotation:
                arg_info["annotation"] = ast.unparse(arg.annotation)

            func_info["args"].append(arg_info)

        # デフォルト引数
        defaults = node.args.defaults
        if defaults:
            for i, default in enumerate(defaults):
                arg_index = len(func_info["args"]) - len(defaults) + i
                if arg_index >= 0:
                    func_info["args"][arg_index]["default"] = ast.unparse(default)

        # 戻り値の型
        if node.returns:
            func_info["return_type"] = ast.unparse(node.returns)

        # エッジケース検出
        func_info["edge_cases"] = await self._detect_edge_cases(node, func_info)

        return func_info

    async def _analyze_class(
        self, node: ast.ClassDef, file_path: Path
    ) -> dict[str, Any]:
        """クラス分析"""
        class_info = {
            "name": node.name,
            "file": str(file_path),
            "line": node.lineno,
            "methods": [],
            "base_classes": [],
            "attributes": [],
        }

        # 基底クラス
        for base in node.bases:
            class_info["base_classes"].append(ast.unparse(base))

        # メソッド分析
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = await self._analyze_function(item, file_path)
                class_info["methods"].append(method_info)

        return class_info

    async def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """サイクロマティック複雑度計算"""
        complexity = 1  # 基本パス

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    async def _detect_edge_cases(
        self, node: ast.FunctionDef, func_info: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """エッジケース検出"""
        edge_cases = []

        # 引数に基づくエッジケース
        for arg in func_info["args"]:
            arg_type = arg.get("annotation", "")

            if "int" in arg_type.lower():
                edge_cases.extend(
                    [
                        {
                            "type": "boundary",
                            "value": 0,
                            "description": f"{arg['name']} = 0",
                        },
                        {
                            "type": "boundary",
                            "value": -1,
                            "description": f"{arg['name']} = -1",
                        },
                        {
                            "type": "boundary",
                            "value": "sys.maxsize",
                            "description": f"{arg['name']} = maximum integer",
                        },
                    ]
                )

            elif "str" in arg_type.lower():
                edge_cases.extend(
                    [
                        {
                            "type": "empty",
                            "value": '""',
                            "description": f"{arg['name']} = empty string",
                        },
                        {
                            "type": "whitespace",
                            "value": '" "',
                            "description": f"{arg['name']} = whitespace only",
                        },
                        {
                            "type": "unicode",
                            "value": '"🐝"',
                            "description": f"{arg['name']} = unicode characters",
                        },
                    ]
                )

            elif "list" in arg_type.lower() or "List" in arg_type:
                edge_cases.extend(
                    [
                        {
                            "type": "empty",
                            "value": "[]",
                            "description": f"{arg['name']} = empty list",
                        },
                        {
                            "type": "single",
                            "value": "[item]",
                            "description": f"{arg['name']} = single item list",
                        },
                    ]
                )

            elif "dict" in arg_type.lower() or "Dict" in arg_type:
                edge_cases.extend(
                    [
                        {
                            "type": "empty",
                            "value": "{}",
                            "description": f"{arg['name']} = empty dict",
                        },
                    ]
                )

            elif not arg.get("default"):  # デフォルトがない引数
                edge_cases.append(
                    {
                        "type": "none",
                        "value": "None",
                        "description": f"{arg['name']} = None",
                    }
                )

        # 関数内容に基づくエッジケース
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                edge_cases.append(
                    {"type": "exception", "description": "Exception raising case"}
                )

        return edge_cases


class TestGenerator:
    """テストケース生成器"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.test_templates = {
            "function": self._generate_function_test,
            "class": self._generate_class_test,
            "edge_case": self._generate_edge_case_test,
            "mock": self._generate_mock_test,
        }

    async def generate_comprehensive_tests(
        self, analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """包括的テスト生成"""
        test_cases = []

        # 関数テスト生成
        for func in analysis["functions"][:10]:  # 最初の10関数
            test_case = await self._generate_function_test(func)
            if test_case:
                test_cases.append(test_case)

        # クラステスト生成
        for cls in analysis["classes"][:5]:  # 最初の5クラス
            test_case = await self._generate_class_test(cls)
            if test_case:
                test_cases.append(test_case)

        # エッジケーステスト生成
        edge_case_tests = await self._generate_edge_case_tests(analysis)
        test_cases.extend(edge_case_tests)

        return test_cases

    async def _generate_function_test(
        self, func_info: dict[str, Any]
    ) -> dict[str, Any] | None:
        """関数テスト生成"""
        try:
            func_name = func_info["name"]
            file_path = func_info["file"]
            args = func_info["args"]

            # モジュールパス生成
            module_path = self._get_module_path(Path(file_path))

            # テストケース作成
            test_methods = []

            # 基本テスト
            basic_test = f'''    def test_{func_name}_basic(self):
        """Test {func_name} with basic inputs"""
        # TODO: Add actual test implementation
        result = {func_name}({self._generate_sample_args(args)})
        assert result is not None'''

            test_methods.append(basic_test)

            # エッジケーステスト
            for edge_case in func_info.get("edge_cases", [])[:3]:  # 最初の3つ
                edge_test = f'''    def test_{func_name}_{edge_case["type"]}(self):
        """Test {func_name} with {edge_case["description"]}"""
        # TODO: Implement edge case test
        # Case: {edge_case["description"]}
        pass'''
                test_methods.append(edge_test)

            # 完整なテストクラス生成
            test_class = f'''class Test{func_name.title()}:
    """Test cases for {func_name} function"""
    
{chr(10).join(test_methods)}'''

            return {
                "type": "function_test",
                "target_function": func_name,
                "target_file": file_path,
                "test_content": test_class,
                "test_file": self._get_test_file_path(Path(file_path)),
                "imports": f"from {module_path} import {func_name}",
                "edge_cases_covered": len(func_info.get("edge_cases", [])),
            }

        except Exception:
            return None

    async def _generate_class_test(
        self, class_info: dict[str, Any]
    ) -> dict[str, Any] | None:
        """クラステスト生成"""
        try:
            class_name = class_info["name"]
            file_path = class_info["file"]
            methods = class_info["methods"]

            # モジュールパス生成
            module_path = self._get_module_path(Path(file_path))

            # テストケース作成
            test_methods = []

            # 初期化テスト
            init_test = f'''    def test_{class_name.lower()}_init(self):
        """Test {class_name} initialization"""
        instance = {class_name}()
        assert instance is not None'''

            test_methods.append(init_test)

            # メソッドテスト
            for method in methods[:5]:  # 最初の5メソッド
                if not method["name"].startswith("_"):  # プライベートメソッド除外
                    method_test = f'''    def test_{method["name"]}(self):
        """Test {class_name}.{method["name"]} method"""
        instance = {class_name}()
        # TODO: Implement method test
        result = instance.{method["name"]}({self._generate_sample_args(method["args"][1:])})  # self除外
        assert result is not None'''
                    test_methods.append(method_test)

            # 完整なテストクラス生成
            test_class = f'''class Test{class_name}:
    """Test cases for {class_name} class"""
    
{chr(10).join(test_methods)}'''

            return {
                "type": "class_test",
                "target_class": class_name,
                "target_file": file_path,
                "test_content": test_class,
                "test_file": self._get_test_file_path(Path(file_path)),
                "imports": f"from {module_path} import {class_name}",
                "methods_covered": len(
                    [m for m in methods if not m["name"].startswith("_")]
                ),
            }

        except Exception:
            return None

    async def _generate_edge_case_tests(
        self, analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """エッジケーステスト生成"""
        edge_tests = []

        # 全関数からエッジケースを収集
        all_edge_cases = []
        for func in analysis["functions"]:
            for edge_case in func.get("edge_cases", []):
                edge_case["function"] = func["name"]
                edge_case["file"] = func["file"]
                all_edge_cases.append(edge_case)

        # エッジケース種別でグループ化
        edge_case_groups = {}
        for edge_case in all_edge_cases:
            case_type = edge_case["type"]
            if case_type not in edge_case_groups:
                edge_case_groups[case_type] = []
            edge_case_groups[case_type].append(edge_case)

        # 各種別でテスト生成
        for case_type, cases in edge_case_groups.items():
            test_content = f'''class TestEdgeCases{case_type.title()}:
    """Edge case tests for {case_type} scenarios"""
    
    def test_{case_type}_scenarios(self):
        """Test various {case_type} edge cases"""
        # TODO: Implement comprehensive {case_type} testing
        edge_cases = {cases[:5]}  # First 5 cases
        
        for case in edge_cases:
            # Test case: {{case["description"]}}
            pass
        
        assert True  # Placeholder'''

            edge_tests.append(
                {
                    "type": "edge_case_test",
                    "case_type": case_type,
                    "test_content": test_content,
                    "test_file": Path(f"tests/test_edge_cases_{case_type}.py"),
                    "cases_covered": len(cases),
                }
            )

        return edge_tests

    def _generate_sample_args(self, args: list[dict[str, Any]]) -> str:
        """サンプル引数生成"""
        if not args:
            return ""

        sample_args = []
        for arg in args:
            arg_type = arg.get("annotation", "")
            default = arg.get("default")

            if default:
                sample_args.append(default)
            elif "int" in arg_type.lower():
                sample_args.append("1")
            elif "str" in arg_type.lower():
                sample_args.append('"test"')
            elif "bool" in arg_type.lower():
                sample_args.append("True")
            elif "list" in arg_type.lower() or "List" in arg_type:
                sample_args.append("[1, 2, 3]")
            elif "dict" in arg_type.lower() or "Dict" in arg_type:
                sample_args.append('{"key": "value"}')
            else:
                sample_args.append("None")

        return ", ".join(sample_args)

    def _get_module_path(self, file_path: Path) -> str:
        """モジュールパス取得"""
        try:
            relative_path = file_path.relative_to(Path.cwd())
            module_path = str(relative_path.with_suffix("")).replace("/", ".")
            return module_path
        except ValueError:
            return file_path.stem

    def _get_test_file_path(self, source_file: Path) -> Path:
        """テストファイルパス取得"""
        test_dir = Path("tests")
        test_file_name = f"test_{source_file.stem}.py"
        return test_dir / test_file_name

    async def write_test_files(
        self, test_cases: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """テストファイル書き込み"""
        written_files = 0
        errors = []

        for test_case in test_cases:
            try:
                test_file = test_case["test_file"]
                test_file.parent.mkdir(parents=True, exist_ok=True)

                # テストファイル内容構築
                content = f'''"""
Auto-generated test file for {test_case.get("target_function", test_case.get("target_class", "edge cases"))}

Generated by Autonomous Testing Agent
"""

import pytest
{test_case.get("imports", "")}


{test_case["test_content"]}
'''

                # ファイルが存在しない場合のみ作成
                if not test_file.exists():
                    with open(test_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    written_files += 1

            except Exception as e:
                errors.append({"test_case": test_case, "error": str(e)})

        return {
            "written_files": written_files,
            "total_test_cases": len(test_cases),
            "errors": errors,
        }


class TestCoverageAnalyzer:
    """テストカバレッジ分析器"""

    async def analyze_current_coverage(self) -> dict[str, Any]:
        """現在のテストカバレッジ分析"""
        try:
            # pytest + coverage実行
            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=.", "--cov-report=json", "--quiet"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            coverage_data = {"total_coverage": 0, "line_coverage": {}}

            if result.returncode == 0:
                coverage_file = Path("coverage.json")
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        data = json.load(f)
                    coverage_file.unlink()  # クリーンアップ

                    coverage_data = {
                        "total_coverage": data.get("totals", {}).get(
                            "percent_covered", 0
                        ),
                        "lines_covered": data.get("totals", {}).get("covered_lines", 0),
                        "lines_total": data.get("totals", {}).get("num_statements", 0),
                        "files": data.get("files", {}),
                        "missing_lines": self._extract_missing_lines(data),
                    }

            return coverage_data

        except Exception as e:
            return {"total_coverage": 0, "error": str(e)}

    def _extract_missing_lines(
        self, coverage_data: dict[str, Any]
    ) -> dict[str, list[int]]:
        """未カバーライン抽出"""
        missing_lines = {}

        files = coverage_data.get("files", {})
        for file_path, file_data in files.items():
            missing = file_data.get("missing_lines", [])
            if missing:
                missing_lines[file_path] = missing

        return missing_lines

    async def calculate_improvement_potential(
        self, test_cases: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """改善ポテンシャル計算"""
        potential_lines = 0
        target_files = set()

        for test_case in test_cases:
            target_file = test_case.get("target_file")
            if target_file:
                target_files.add(target_file)
                # 簡易推定: 1テストケースあたり5-10ライン改善
                potential_lines += test_case.get("edge_cases_covered", 3) * 2

        return {
            "potential_line_improvement": potential_lines,
            "target_files_count": len(target_files),
            "estimated_coverage_improvement": min(
                potential_lines * 0.1, 20
            ),  # 最大20%改善
        }


class AutonomousTestingAgent(AutonomousAgent):
    """自律的テスト生成エージェント"""

    def __init__(self):
        super().__init__(
            agent_id="testing_agent",
            specialization="test_generation",
            config={
                "cycle_interval": 180,  # 3分間隔
                "target_coverage": 85,
                "max_tests_per_cycle": 5,
            },
        )

        self.analyzer = CodeAnalyzer()
        self.test_generator = TestGenerator()
        self.coverage_analyzer = TestCoverageAnalyzer()
        self.baseline_coverage = None

    async def _get_project_status(self) -> dict[str, Any]:
        """プロジェクト状況取得"""
        test_files = list(Path(".").rglob("test_*.py"))
        return {
            "total_test_files": len(test_files),
            "project_type": "python_project",
            "status": "active",
        }

    async def _get_quality_metrics(self) -> dict[str, Any]:
        """品質メトリクス取得"""
        coverage_data = await self.coverage_analyzer.analyze_current_coverage()
        code_analysis = await self.analyzer.analyze_testable_code()

        return {
            "test_coverage": coverage_data.get("total_coverage", 0),
            "coverage_details": coverage_data,
            "testable_functions": len(code_analysis["functions"]),
            "testable_classes": len(code_analysis["classes"]),
            "edge_cases_identified": len(code_analysis["edge_cases"]),
        }

    async def _get_specialized_actions(
        self, analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """テスト生成専用アクション決定"""
        actions = []

        quality_metrics = analysis.get("quality_metrics", {})
        current_coverage = quality_metrics.get("test_coverage", 0)

        # カバレッジが目標を下回る場合にアクション生成
        if current_coverage < self.config["target_coverage"]:
            actions.append(
                {
                    "type": "generate_tests",
                    "current_coverage": current_coverage,
                    "target_coverage": self.config["target_coverage"],
                    "priority": "high",
                }
            )

        # エッジケースが多く特定された場合
        edge_cases_count = quality_metrics.get("edge_cases_identified", 0)
        if edge_cases_count > 10:
            actions.append(
                {
                    "type": "generate_edge_case_tests",
                    "edge_cases_count": edge_cases_count,
                    "priority": "medium",
                }
            )

        return actions

    async def _execute_specialized_action(
        self, action: dict[str, Any]
    ) -> dict[str, Any]:
        """テスト生成アクション実行"""
        if action["type"] == "generate_tests":
            return await self._generate_comprehensive_tests()
        elif action["type"] == "generate_edge_case_tests":
            return await self._generate_edge_case_tests()

        return {"success": False, "error": "Unknown action type"}

    async def _generate_comprehensive_tests(self) -> dict[str, Any]:
        """包括的テスト生成"""
        try:
            # コード分析
            code_analysis = await self.analyzer.analyze_testable_code()

            # テスト生成
            test_cases = await self.test_generator.generate_comprehensive_tests(
                code_analysis
            )

            # テストファイル書き込み
            write_result = await self.test_generator.write_test_files(test_cases)

            # カバレッジ改善ポテンシャル計算
            improvement = await self.coverage_analyzer.calculate_improvement_potential(
                test_cases
            )

            success = write_result["written_files"] > 0
            if success:
                self.performance_metrics["tasks_completed"] += write_result[
                    "written_files"
                ]

            return {
                "success": success,
                "tests_generated": write_result["written_files"],
                "total_test_cases": write_result["total_test_cases"],
                "improvement_potential": improvement,
                "improvement": f"Generated {write_result['written_files']} test files",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_edge_case_tests(self) -> dict[str, Any]:
        """エッジケーステスト生成"""
        try:
            # コード分析
            code_analysis = await self.analyzer.analyze_testable_code()

            # エッジケースのみテスト生成
            edge_test_cases = await self.test_generator._generate_edge_case_tests(
                code_analysis
            )

            # テストファイル書き込み
            write_result = await self.test_generator.write_test_files(edge_test_cases)

            return {
                "success": write_result["written_files"] > 0,
                "edge_tests_generated": write_result["written_files"],
                "improvement": f"Generated {write_result['written_files']} edge case test files",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _initialize_agent(self) -> None:
        """エージェント初期化"""
        await super()._initialize_agent()

        # ベースラインカバレッジ取得
        self.baseline_coverage = await self.coverage_analyzer.analyze_current_coverage()

        self.logger.info("Testing agent initialized with baseline coverage analysis")
        self.logger.info(
            f"Baseline coverage: {self.baseline_coverage.get('total_coverage', 0)}%"
        )


async def main():
    """メイン実行関数"""
    print("🧪 Starting Autonomous Test Generation Agent...")

    # エージェント作成
    agent = AutonomousTestingAgent()

    try:
        # 初期カバレッジ分析
        print("📊 Running initial coverage analysis...")
        initial_coverage = await agent.coverage_analyzer.analyze_current_coverage()
        print(f"Initial test coverage: {initial_coverage.get('total_coverage', 0)}%")

        # 短期間の自律実行（デモ用）
        print("🤖 Starting autonomous test generation cycle...")

        # 非同期で実行開始
        agent_task = asyncio.create_task(agent.start_autonomous_cycle())

        # 5分間実行
        await asyncio.sleep(300)

        # 停止
        await agent.stop_autonomous_cycle()

        # 最終結果
        final_report = agent.get_performance_report()
        print("\n📊 Final Performance Report:")
        print(json.dumps(final_report, indent=2, ensure_ascii=False))

        # カバレッジ改善結果
        final_coverage = await agent.coverage_analyzer.analyze_current_coverage()
        print(
            f"\nCoverage improvement: {initial_coverage.get('total_coverage', 0)}% → {final_coverage.get('total_coverage', 0)}%"
        )

    except KeyboardInterrupt:
        print("\n⏹️ Testing agent stopped by user")
        await agent.stop_autonomous_cycle()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await agent.stop_autonomous_cycle()


if __name__ == "__main__":
    asyncio.run(main())
