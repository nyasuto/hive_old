#!/usr/bin/env python3
"""
Issue #165型チェック体系的改善 - 回帰テストスイート
型チェック修正後の動作確認とテストシナリオ実行

🧪 Tester Worker - TYPECHECK_TEST_PREP_001
"""

import subprocess
from datetime import datetime
from pathlib import Path


class TypeCheckRegressionTest:
    """型チェック修正後の回帰テストクラス"""

    def __init__(self) -> None:
        self.project_root = Path(__file__).parent.parent
        self.test_results: dict[str, bool] = {}
        self.errors: list[str] = []

    def run_mypy_check(self) -> tuple[bool, str]:
        """mypyによる型チェック実行"""
        try:
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    "-m",
                    "mypy",
                    "--config-file=pyproject.toml",
                    "scripts/",
                    "workers/",
                    "tools/",
                    "web/",
                    "hive/",
                    "--show-error-codes",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "mypy timeout"
        except Exception as e:
            return False, f"mypy error: {e}"

    def test_scripts_functionality(self) -> dict[str, bool]:
        """scripts/系統ファイルの機能動作テスト"""
        scripts_tests = {}

        # 重要スクリプトの基本動作確認
        test_scripts = [
            "hive_cli.py",
            "create_github_issue.py",
            "github_issue_helper.py",
            "hive_directory.py",
            "init_hive_directory.py",
        ]

        for script in test_scripts:
            try:
                # --help オプションでの動作確認
                result = subprocess.run(
                    ["python3", f"scripts/{script}", "--help"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                scripts_tests[script] = result.returncode == 0
                if result.returncode != 0:
                    self.errors.append(f"{script} --help failed: {result.stderr}")
            except Exception as e:
                scripts_tests[script] = False
                self.errors.append(f"{script} test error: {e}")

        return scripts_tests

    def test_import_integrity(self) -> dict[str, bool]:
        """インポート関係の整合性テスト"""
        import_tests = {}

        # 主要モジュールのインポートテスト
        test_modules = [
            "scripts.hive_cli",
            "scripts.create_github_issue",
            "scripts.github_issue_helper",
            "scripts.hive_directory",
            "hive.hive_directory.cli",
            "hive.hive_directory.manager",
        ]

        for module in test_modules:
            try:
                result = subprocess.run(
                    ["python3", "-c", f"import {module}"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                import_tests[module] = result.returncode == 0
                if result.returncode != 0:
                    self.errors.append(f"Import {module} failed: {result.stderr}")
            except Exception as e:
                import_tests[module] = False
                self.errors.append(f"Import {module} error: {e}")

        return import_tests

    def test_quality_commands(self) -> dict[str, bool]:
        """品質チェックコマンドのテスト"""
        quality_tests = {}

        commands = [
            ("make quality-light", 30),
            ("make test", 60),
        ]

        for cmd, timeout in commands:
            try:
                result = subprocess.run(
                    cmd.split(),
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                quality_tests[cmd] = result.returncode == 0
                if result.returncode != 0:
                    self.errors.append(f"{cmd} failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                quality_tests[cmd] = False
                self.errors.append(f"{cmd} timeout")
            except Exception as e:
                quality_tests[cmd] = False
                self.errors.append(f"{cmd} error: {e}")

        return quality_tests

    def generate_test_report(self) -> str:
        """テスト結果レポート生成"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 型チェック実行
        mypy_success, mypy_output = self.run_mypy_check()

        # 各種テスト実行
        scripts_results = self.test_scripts_functionality()
        import_results = self.test_import_integrity()
        quality_results = self.test_quality_commands()

        # 総合結果計算
        all_results = {
            "mypy_check": mypy_success,
            **scripts_results,
            **import_results,
            **quality_results,
        }

        total_tests = len(all_results)
        passed_tests = sum(all_results.values())
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        # レポート生成
        report = f"""
🧪 TYPECHECK_TEST_PREP_001 - Issue #165型チェック回帰テスト結果
================================================================

⏰ 実行時刻: {timestamp}
📊 総合結果: {passed_tests}/{total_tests} ({success_rate:.1f}%)

🔍 型チェック結果:
{"✅" if mypy_success else "❌"} mypy check: {"PASS" if mypy_success else "FAIL"}

📝 Scripts機能テスト:
"""

        for script, result in scripts_results.items():
            report += (
                f"{'✅' if result else '❌'} {script}: {'PASS' if result else 'FAIL'}\n"
            )

        report += "\n🔗 インポート整合性テスト:\n"
        for module, result in import_results.items():
            report += (
                f"{'✅' if result else '❌'} {module}: {'PASS' if result else 'FAIL'}\n"
            )

        report += "\n⚙️ 品質コマンドテスト:\n"
        for cmd, result in quality_results.items():
            report += (
                f"{'✅' if result else '❌'} {cmd}: {'PASS' if result else 'FAIL'}\n"
            )

        if self.errors:
            report += "\n❌ 検出されたエラー:\n"
            for error in self.errors:
                report += f"   - {error}\n"

        if not mypy_success:
            report += f"\n🔍 Mypy詳細出力:\n{mypy_output}\n"

        report += "\n📋 テストサマリー:\n"
        if success_rate >= 95:
            report += "🎉 優秀: ほぼ全てのテストが成功\n"
        elif success_rate >= 80:
            report += "✅ 良好: 大部分のテストが成功\n"
        elif success_rate >= 60:
            report += "⚠️  注意: いくつかの問題があります\n"
        else:
            report += "❌ 要修正: 重要な問題が検出されました\n"

        return report

    def run_full_test(self) -> None:
        """フルテストスイート実行"""
        print("🧪 Issue #165型チェック回帰テスト開始...")

        report = self.generate_test_report()

        # レポート出力
        print(report)

        # ファイル保存
        report_file = (
            self.project_root
            / "test_scripts"
            / f"typecheck_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        report_file.parent.mkdir(exist_ok=True)
        report_file.write_text(report)

        print(f"\n📄 詳細レポート保存: {report_file}")


if __name__ == "__main__":
    test_runner = TypeCheckRegressionTest()
    test_runner.run_full_test()
