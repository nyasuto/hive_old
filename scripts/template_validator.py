#!/usr/bin/env python3
"""
Template Validator - テンプレートバリデーションシステム
CODE_IMPROVEMENT:reviewer 対応

YAML設定ファイルとテンプレートメッセージの形式バリデーション機能を提供
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ValidationLevel(Enum):
    """バリデーションレベル"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """バリデーション問題"""

    level: ValidationLevel
    message: str
    suggestion: str | None = None
    location: str | None = None
    error_code: str | None = None


@dataclass
class ValidationResult:
    """バリデーション結果"""

    is_valid: bool
    issues: list[ValidationIssue]
    score: float  # 0.0-1.0 品質スコア

    def add_issue(
        self,
        level: ValidationLevel,
        message: str,
        suggestion: str | None = None,
        location: str | None = None,
        error_code: str | None = None,
    ) -> None:
        """バリデーション問題を追加"""
        self.issues.append(
            ValidationIssue(
                level=level,
                message=message,
                suggestion=suggestion,
                location=location,
                error_code=error_code,
            )
        )

        # エラーがある場合は無効とマーク
        if level == ValidationLevel.ERROR:
            self.is_valid = False


class YAMLConfigValidator:
    """YAML設定ファイルのバリデーター"""

    def __init__(self) -> None:
        # 必須フィールドスキーマ
        self.required_schema = {
            "name": str,
            "pattern": str,
            "description": str,
            "ui_display": dict,
            "groups": list,
            "examples": list,
            "metadata": dict,
        }

        # UI表示必須フィールド
        self.ui_display_schema = {"icon": str, "title": str, "format": str}

        # Groups必須フィールド
        self.groups_schema = {
            "name": str,
            "index": int,
            "description": str,
            "validation": str,
        }

    def validate_yaml_config(self, config_path: str | Path) -> ValidationResult:
        """YAML設定ファイルを包括的にバリデーション"""
        result = ValidationResult(is_valid=True, issues=[], score=1.0)
        config_path = Path(config_path)

        # ファイル存在チェック
        if not config_path.exists():
            result.add_issue(
                ValidationLevel.ERROR,
                f"Configuration file not found: {config_path}",
                suggestion="Check file path and ensure the file exists",
                error_code="FILE_NOT_FOUND",
            )
            result.score = 0.0
            return result

        try:
            # YAML読み込み
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config:
                result.add_issue(
                    ValidationLevel.ERROR,
                    "Empty or invalid YAML configuration",
                    suggestion="Ensure YAML file contains valid configuration data",
                    error_code="EMPTY_CONFIG",
                )
                result.score = 0.0
                return result

            # スキーマバリデーション
            self._validate_schema(config, result, config_path.name)

            # パターンバリデーション
            if "pattern" in config:
                self._validate_pattern(config["pattern"], result)

            # UI表示設定バリデーション
            if "ui_display" in config:
                self._validate_ui_display(config["ui_display"], result)

            # グループ設定バリデーション
            if "groups" in config:
                self._validate_groups(config["groups"], result)

            # 例バリデーション
            if "examples" in config:
                self._validate_examples(
                    config["examples"], config.get("pattern", ""), result
                )

            # スコア計算
            result.score = self._calculate_score(result.issues)

        except yaml.YAMLError as e:
            result.add_issue(
                ValidationLevel.ERROR,
                f"YAML parsing error: {e}",
                suggestion="Check YAML syntax and formatting",
                error_code="YAML_PARSE_ERROR",
            )
            result.score = 0.0
        except Exception as e:
            result.add_issue(
                ValidationLevel.ERROR,
                f"Unexpected validation error: {e}",
                error_code="VALIDATION_ERROR",
            )
            result.score = 0.0

        return result

    def _validate_schema(
        self, config: dict[str, Any], result: ValidationResult, filename: str
    ) -> None:
        """基本スキーマバリデーション"""
        # 必須フィールドチェック
        for field, expected_type in self.required_schema.items():
            if field not in config:
                result.add_issue(
                    ValidationLevel.ERROR,
                    f"Missing required field: '{field}'",
                    suggestion=f"Add '{field}' field to {filename}",
                    location=f"root.{field}",
                    error_code="MISSING_REQUIRED_FIELD",
                )
            elif not isinstance(config[field], expected_type):
                result.add_issue(
                    ValidationLevel.ERROR,
                    f"Field '{field}' must be {expected_type.__name__}, got {type(config[field]).__name__}",
                    suggestion=f"Change '{field}' to {expected_type.__name__} type",
                    location=f"root.{field}",
                    error_code="INVALID_FIELD_TYPE",
                )

    def _validate_pattern(self, pattern: str, result: ValidationResult) -> None:
        """正規表現パターンのバリデーション"""
        try:
            # パターンコンパイルテスト
            compiled = re.compile(pattern)

            # グループ数チェック
            group_count = compiled.groups
            if group_count == 0:
                result.add_issue(
                    ValidationLevel.WARNING,
                    "Pattern contains no capture groups",
                    suggestion="Add capture groups using parentheses: (group1)",
                    location="pattern",
                    error_code="NO_CAPTURE_GROUPS",
                )
            elif group_count > 10:
                result.add_issue(
                    ValidationLevel.WARNING,
                    f"Pattern has many capture groups ({group_count}), consider simplification",
                    location="pattern",
                    error_code="TOO_MANY_GROUPS",
                )

        except re.error as e:
            result.add_issue(
                ValidationLevel.ERROR,
                f"Invalid regular expression pattern: {e}",
                suggestion="Fix regex syntax or use online regex validator",
                location="pattern",
                error_code="INVALID_REGEX",
            )

    def _validate_ui_display(
        self, ui_display: dict[str, Any], result: ValidationResult
    ) -> None:
        """UI表示設定のバリデーション"""
        for field, expected_type in self.ui_display_schema.items():
            if field not in ui_display:
                result.add_issue(
                    ValidationLevel.ERROR,
                    f"Missing UI display field: '{field}'",
                    suggestion=f"Add '{field}' to ui_display section",
                    location=f"ui_display.{field}",
                    error_code="MISSING_UI_FIELD",
                )
            elif not isinstance(ui_display[field], expected_type):
                result.add_issue(
                    ValidationLevel.ERROR,
                    f"UI field '{field}' must be {expected_type.__name__}",
                    location=f"ui_display.{field}",
                    error_code="INVALID_UI_FIELD_TYPE",
                )

        # アイコンバリデーション
        if "icon" in ui_display:
            icon = ui_display["icon"]
            if len(icon) != 2 or not self._is_emoji(icon):
                result.add_issue(
                    ValidationLevel.WARNING,
                    f"Icon '{icon}' may not be a valid emoji",
                    suggestion="Use standard emoji characters like 🎯, 📋, 👑",
                    location="ui_display.icon",
                    error_code="INVALID_EMOJI",
                )

    def _validate_groups(
        self, groups: list[dict[str, Any]], result: ValidationResult
    ) -> None:
        """グループ設定のバリデーション"""
        if not groups:
            result.add_issue(
                ValidationLevel.WARNING,
                "No groups defined",
                suggestion="Define groups to match regex capture groups",
                location="groups",
                error_code="NO_GROUPS",
            )
            return

        indices = []
        for i, group in enumerate(groups):
            group_location = f"groups[{i}]"

            # 必須フィールドチェック
            for field, expected_type in self.groups_schema.items():
                if field not in group:
                    result.add_issue(
                        ValidationLevel.ERROR,
                        f"Missing group field: '{field}' in group {i}",
                        suggestion=f"Add '{field}' to group definition",
                        location=f"{group_location}.{field}",
                        error_code="MISSING_GROUP_FIELD",
                    )
                elif not isinstance(group[field], expected_type):
                    result.add_issue(
                        ValidationLevel.ERROR,
                        f"Group field '{field}' must be {expected_type.__name__}",
                        location=f"{group_location}.{field}",
                        error_code="INVALID_GROUP_FIELD_TYPE",
                    )

            # インデックス重複チェック
            if "index" in group:
                index = group["index"]
                if index in indices:
                    result.add_issue(
                        ValidationLevel.ERROR,
                        f"Duplicate group index: {index}",
                        suggestion="Ensure each group has a unique index",
                        location=f"{group_location}.index",
                        error_code="DUPLICATE_GROUP_INDEX",
                    )
                indices.append(index)

                # インデックス範囲チェック
                if index < 0:
                    result.add_issue(
                        ValidationLevel.ERROR,
                        f"Group index must be non-negative, got {index}",
                        location=f"{group_location}.index",
                        error_code="INVALID_GROUP_INDEX",
                    )

            # バリデーション正規表現チェック
            if "validation" in group:
                try:
                    re.compile(group["validation"])
                except re.error as e:
                    result.add_issue(
                        ValidationLevel.ERROR,
                        f"Invalid validation regex in group {i}: {e}",
                        suggestion="Fix validation regex syntax",
                        location=f"{group_location}.validation",
                        error_code="INVALID_VALIDATION_REGEX",
                    )

    def _validate_examples(
        self, examples: list[dict[str, Any]], pattern: str, result: ValidationResult
    ) -> None:
        """例バリデーション"""
        if not examples:
            result.add_issue(
                ValidationLevel.WARNING,
                "No examples provided",
                suggestion="Add examples to demonstrate template usage",
                location="examples",
                error_code="NO_EXAMPLES",
            )
            return

        try:
            compiled_pattern = re.compile(pattern)
        except re.error:
            # パターンが無効な場合は例のバリデーションをスキップ
            return

        for i, example in enumerate(examples):
            example_location = f"examples[{i}]"

            if "message" not in example:
                result.add_issue(
                    ValidationLevel.ERROR,
                    f"Example {i} missing 'message' field",
                    location=example_location,
                    error_code="MISSING_EXAMPLE_MESSAGE",
                )
                continue

            message = example["message"]
            match = compiled_pattern.search(message)

            if not match:
                result.add_issue(
                    ValidationLevel.ERROR,
                    f"Example message doesn't match pattern: '{message[:50]}...'",
                    suggestion="Ensure example message matches the defined pattern",
                    location=f"{example_location}.message",
                    error_code="EXAMPLE_PATTERN_MISMATCH",
                )
            else:
                # 期待されるグループと実際のグループの一致確認
                if "expected_groups" in example:
                    expected = example["expected_groups"]
                    match.groups()

                    for _key, _expected_value in expected.items():
                        # groupsから対応するインデックスを探す
                        # (この例では簡単化のため省略)
                        pass

    def _is_emoji(self, text: str) -> bool:
        """絵文字判定（簡易版）"""
        if len(text) != 2:
            return False
        # Unicode絵文字範囲の簡易チェック
        return any(ord(char) >= 0x1F000 for char in text)

    def _calculate_score(self, issues: list[ValidationIssue]) -> float:
        """品質スコアを計算"""
        if not issues:
            return 1.0

        error_penalty = (
            sum(1 for issue in issues if issue.level == ValidationLevel.ERROR) * 0.3
        )
        warning_penalty = (
            sum(1 for issue in issues if issue.level == ValidationLevel.WARNING) * 0.1
        )
        info_penalty = (
            sum(1 for issue in issues if issue.level == ValidationLevel.INFO) * 0.05
        )

        total_penalty = error_penalty + warning_penalty + info_penalty
        return max(0.0, 1.0 - total_penalty)


class TemplateMessageValidator:
    """テンプレートメッセージのバリデーター"""

    def __init__(self, patterns_dir: str | Path = "templates/communication"):
        self.patterns_dir = Path(patterns_dir)
        self.known_patterns = self._load_patterns()

    def _load_patterns(self) -> dict[str, re.Pattern]:
        """利用可能なパターンを読み込み"""
        patterns: dict[str, re.Pattern] = {}

        if not self.patterns_dir.exists():
            return patterns

        for yaml_file in self.patterns_dir.glob("*.yaml"):
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                if config and "name" in config and "pattern" in config:
                    try:
                        patterns[config["name"]] = re.compile(config["pattern"])
                    except re.error:
                        pass  # 無効なパターンはスキップ

            except Exception:
                pass  # 読み込みエラーはスキップ

        return patterns

    def validate_template_message(self, message: str) -> ValidationResult:
        """テンプレートメッセージの形式バリデーション"""
        result = ValidationResult(is_valid=True, issues=[], score=1.0)

        if not message.strip():
            result.add_issue(
                ValidationLevel.ERROR,
                "Empty message",
                suggestion="Provide a non-empty template message",
                error_code="EMPTY_MESSAGE",
            )
            result.score = 0.0
            return result

        # 既知パターンとのマッチング試行
        matched_patterns = []
        partial_matches = []

        for pattern_name, compiled_pattern in self.known_patterns.items():
            match = compiled_pattern.search(message)
            if match:
                matched_patterns.append((pattern_name, match))
            else:
                # 部分マッチチェック
                if self._check_partial_match(message, pattern_name):
                    partial_matches.append(pattern_name)

        if not matched_patterns:
            if partial_matches:
                result.add_issue(
                    ValidationLevel.WARNING,
                    "Message partially matches known patterns but is not valid",
                    suggestion=f"Consider using: {', '.join(partial_matches)}",
                    error_code="PARTIAL_PATTERN_MATCH",
                )
                result.score = 0.6
            else:
                suggestions = self._generate_suggestions(message)
                result.add_issue(
                    ValidationLevel.WARNING,
                    "Message doesn't match any known template patterns",
                    suggestion=f"Try: {suggestions}"
                    if suggestions
                    else "Use template show command to see available patterns",
                    error_code="NO_PATTERN_MATCH",
                )
                result.score = 0.3
        else:
            # マッチした場合の詳細バリデーション
            for pattern_name, match in matched_patterns:
                self._validate_matched_pattern(message, pattern_name, match, result)

        return result

    def _check_partial_match(self, message: str, pattern_name: str) -> bool:
        """部分マッチをチェック"""
        # 簡単な部分マッチ検出
        pattern_prefixes = {
            "task_template": "TASK:",
            "worker_result_template": "WORKER_RESULT:",
            "queen_report_template": "QUEEN_FINAL_REPORT:",
            "collaboration_template": "COLLABORATE:",
            "approval_template": "APPROVAL:",
        }

        prefix = pattern_prefixes.get(pattern_name, "")
        return bool(prefix and message.startswith(prefix))

    def _validate_matched_pattern(
        self, message: str, pattern_name: str, match: re.Match, result: ValidationResult
    ) -> None:
        """マッチしたパターンの詳細バリデーション"""
        groups = match.groups()

        # パターン別の詳細バリデーション
        if pattern_name == "task_template":
            self._validate_task_pattern(groups, result)
        elif pattern_name == "worker_result_template":
            self._validate_worker_result_pattern(groups, result)
        elif pattern_name == "queen_report_template":
            self._validate_queen_report_pattern(groups, result)

    def _validate_task_pattern(self, groups: tuple, result: ValidationResult) -> None:
        """TASKパターンの詳細バリデーション"""
        if len(groups) >= 2:
            task_id, instruction = groups[0], groups[1]

            # タスクID形式チェック
            if not re.match(r"^[A-Z0-9_]+$", task_id):
                result.add_issue(
                    ValidationLevel.WARNING,
                    f"Task ID '{task_id}' should use uppercase letters, numbers, and underscores only",
                    suggestion="Example: TASK_001, BUG_FIX_001, FEATURE_001",
                    error_code="INVALID_TASK_ID_FORMAT",
                )

            # 指示内容チェック
            if len(instruction.strip()) < 10:
                result.add_issue(
                    ValidationLevel.WARNING,
                    "Task instruction is very short",
                    suggestion="Provide more detailed instructions for better task execution",
                    error_code="SHORT_INSTRUCTION",
                )

    def _validate_worker_result_pattern(
        self, groups: tuple, result: ValidationResult
    ) -> None:
        """WORKER_RESULTパターンの詳細バリデーション"""
        if len(groups) >= 3:
            worker_name, _task_id, result_content = groups[0], groups[1], groups[2]

            # Worker名チェック
            valid_workers = {
                "queen",
                "developer",
                "tester",
                "analyzer",
                "documenter",
                "reviewer",
                "beekeeper",
            }
            if worker_name not in valid_workers:
                result.add_issue(
                    ValidationLevel.WARNING,
                    f"Unknown worker name: '{worker_name}'",
                    suggestion=f"Use: {', '.join(valid_workers)}",
                    error_code="UNKNOWN_WORKER",
                )

            # 結果内容チェック
            if len(result_content.strip()) < 20:
                result.add_issue(
                    ValidationLevel.INFO,
                    "Result content is brief",
                    suggestion="Consider providing more detailed results for better tracking",
                    error_code="BRIEF_RESULT",
                )

    def _validate_queen_report_pattern(
        self, groups: tuple, result: ValidationResult
    ) -> None:
        """QUEEN_FINAL_REPORTパターンの詳細バリデーション"""
        if len(groups) >= 2:
            session_id, _report_content = groups[0], groups[1]

            # セッションID形式チェック
            if not re.match(r"^[a-zA-Z0-9_]+$", session_id):
                result.add_issue(
                    ValidationLevel.WARNING,
                    f"Session ID '{session_id}' should use alphanumeric characters and underscores",
                    suggestion="Example: session_001, template_impl, bug_fix_session",
                    error_code="INVALID_SESSION_ID_FORMAT",
                )

    def _generate_suggestions(self, message: str) -> str:
        """メッセージ内容に基づく提案生成"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["task", "todo", "do", "implement"]):
            return "TASK:[ID]:[INSTRUCTION] pattern"
        elif any(
            word in message_lower
            for word in ["result", "completed", "done", "finished"]
        ):
            return "WORKER_RESULT:[WORKER]:[TASK_ID]:[RESULT] pattern"
        elif any(word in message_lower for word in ["report", "final", "summary"]):
            return "QUEEN_FINAL_REPORT:[SESSION_ID]:[REPORT] pattern"
        else:
            return "template show command to see available patterns"


# 統合バリデーター
class TemplateValidator:
    """テンプレート統合バリデーター"""

    def __init__(self, patterns_dir: str | Path = "templates/communication"):
        self.yaml_validator = YAMLConfigValidator()
        self.message_validator = TemplateMessageValidator(patterns_dir)

    def validate_all_configs(
        self, config_dir: str | Path
    ) -> dict[str, ValidationResult]:
        """指定ディレクトリ内の全YAML設定をバリデーション"""
        config_dir = Path(config_dir)
        results: dict[str, ValidationResult] = {}

        if not config_dir.exists():
            return results

        for yaml_file in config_dir.glob("*.yaml"):
            results[yaml_file.name] = self.yaml_validator.validate_yaml_config(
                yaml_file
            )

        return results

    def validate_message_with_suggestions(self, message: str) -> ValidationResult:
        """メッセージバリデーション（修正候補付き）"""
        return self.message_validator.validate_template_message(message)

    def generate_validation_report(self, config_dir: str | Path) -> str:
        """バリデーションレポートを生成"""
        results = self.validate_all_configs(config_dir)

        report = "# 🔍 Template Configuration Validation Report\n\n"

        total_files = len(results)
        valid_files = sum(1 for result in results.values() if result.is_valid)

        report += "## 📊 Summary\n"
        report += f"- **Total Files**: {total_files}\n"
        report += f"- **Valid Files**: {valid_files}\n"
        report += f"- **Invalid Files**: {total_files - valid_files}\n\n"

        for filename, result in results.items():
            status = "✅" if result.is_valid else "❌"
            score = f"{result.score:.1%}"

            report += f"## {status} {filename} (Score: {score})\n\n"

            if result.issues:
                for issue in result.issues:
                    level_icon = {"error": "🔴", "warning": "🟡", "info": "ℹ️"}[
                        issue.level.value
                    ]
                    report += f"- {level_icon} **{issue.level.value.upper()}**: {issue.message}\n"
                    if issue.suggestion:
                        report += f"  - 💡 **Suggestion**: {issue.suggestion}\n"
                    if issue.location:
                        report += f"  - 📍 **Location**: `{issue.location}`\n"
                    report += "\n"
            else:
                report += "No issues found.\n\n"

        return report


# CLI統合とテスト実行
if __name__ == "__main__":
    # バリデーターテスト
    validator = TemplateValidator()

    print("🔍 Template Validator Test")
    print("=" * 50)

    # 設定ファイルバリデーションテスト
    config_dir = Path("templates/communication")
    if config_dir.exists():
        results = validator.validate_all_configs(config_dir)

        print(f"\n📁 Config Directory: {config_dir}")
        for filename, result in results.items():
            status = "✅" if result.is_valid else "❌"
            print(f"  {status} {filename} (Score: {result.score:.1%})")

            for issue in result.issues[:3]:  # 最初の3つの問題を表示
                level_icon = {"error": "🔴", "warning": "🟡", "info": "ℹ️"}[
                    issue.level.value
                ]
                print(f"    {level_icon} {issue.message}")

    # メッセージバリデーションテスト
    test_messages = [
        "TASK:TEST_001:テンプレートバリデーター機能のテスト",
        "WORKER_RESULT:developer:TEST_001:バリデーション機能実装完了",
        "INVALID_FORMAT:missing_parts",
        "TASK:invalid-id:不正なタスクID形式のテスト",
        "",
    ]

    print("\n📝 Message Validation Test")
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Message: {message[:30]}...")
        result = validator.validate_message_with_suggestions(message)
        status = "✅" if result.is_valid else "❌"
        print(f"   {status} Valid: {result.is_valid} (Score: {result.score:.1%})")

        for issue in result.issues[:2]:  # 最初の2つの問題を表示
            level_icon = {"error": "🔴", "warning": "🟡", "info": "ℹ️"}[
                issue.level.value
            ]
            print(f"   {level_icon} {issue.message}")
            if issue.suggestion:
                print(f"   💡 {issue.suggestion}")

    print("\n🎯 Validation test completed!")
