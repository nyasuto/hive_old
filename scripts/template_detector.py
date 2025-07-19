#!/usr/bin/env python3
"""
Template Detector - テンプレート検知システム
TASK:TEMPLATE_002 プロトタイプ実装

Hive CLIシステムのメッセージからテンプレートパターンを検知し、
構造化された情報として抽出する機能を提供
"""

import difflib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class TemplateType(Enum):
    """検知可能なテンプレートタイプ"""

    TASK = "task_template"
    WORKER_RESULT = "worker_result_template"
    COLLABORATION = "collaboration_template"
    QUEEN_REPORT = "queen_report_template"
    APPROVAL = "approval_template"
    UNKNOWN = "unknown_template"


@dataclass
class TemplateMatch:
    """テンプレートマッチ結果"""

    template_type: TemplateType
    pattern: str
    groups: tuple[str, ...]
    full_match: str
    raw_message: str
    confidence: float = 1.0


@dataclass
class TemplateDetectionError:
    """テンプレート検知エラー詳細情報"""

    message: str
    error_type: str
    suggestions: list[str]
    closest_patterns: list[tuple[str, float]]  # (pattern_name, similarity_score)
    partial_matches: list[str]
    fix_examples: list[str]


class TemplatePatternRegistry:
    """テンプレートパターンの登録・管理"""

    def __init__(self) -> None:
        self.patterns: dict[TemplateType, str] = {
            TemplateType.TASK: r"TASK:([A-Z0-9_]+):(.+)",
            TemplateType.WORKER_RESULT: r"WORKER_RESULT:(\w+):([A-Z0-9_]+):(.+)",
            TemplateType.COLLABORATION: r"COLLABORATE:([A-Z0-9_]+):(.+)",
            TemplateType.QUEEN_REPORT: r"QUEEN_FINAL_REPORT:([A-Z0-9_]+):(.+)",
            TemplateType.APPROVAL: r"APPROVAL:(\w+):([A-Z0-9_]+):(.+)",
        }

        # パターンを事前コンパイル（パフォーマンス向上）
        self.compiled_patterns: dict[TemplateType, re.Pattern] = {
            template_type: re.compile(pattern, re.MULTILINE | re.DOTALL)
            for template_type, pattern in self.patterns.items()
        }

    def add_pattern(self, template_type: TemplateType, pattern: str) -> None:
        """新しいパターンを追加"""
        self.patterns[template_type] = pattern
        self.compiled_patterns[template_type] = re.compile(
            pattern, re.MULTILINE | re.DOTALL
        )

    def get_pattern(self, template_type: TemplateType) -> str | None:
        """パターンを取得"""
        return self.patterns.get(template_type)


class TemplateDetector:
    """メインのテンプレート検知クラス"""

    def __init__(self, registry: TemplatePatternRegistry | None = None):
        self.registry = registry or TemplatePatternRegistry()
        self.detection_stats: dict[str, int] = {
            "total_messages": 0,
            "template_matches": 0,
        }
        self.by_type_stats: dict[TemplateType, int] = dict.fromkeys(TemplateType, 0)

    def detect(self, message: str) -> TemplateMatch | None:
        """
        メッセージからテンプレートを検知

        Args:
            message: 検知対象のメッセージ

        Returns:
            TemplateMatch: マッチした場合のテンプレート情報、マッチしない場合はNone
        """
        self.detection_stats["total_messages"] += 1

        for template_type, compiled_pattern in self.registry.compiled_patterns.items():
            match = compiled_pattern.search(message)
            if match:
                self.detection_stats["template_matches"] += 1
                self.by_type_stats[template_type] += 1

                return TemplateMatch(
                    template_type=template_type,
                    pattern=self.registry.patterns[template_type],
                    groups=match.groups(),
                    full_match=match.group(0),
                    raw_message=message,
                    confidence=self._calculate_confidence(
                        template_type, match, message
                    ),
                )

        return None

    def detect_with_error_analysis(
        self, message: str
    ) -> tuple[TemplateMatch | None, TemplateDetectionError | None]:
        """
        エラー分析付きテンプレート検知

        Args:
            message: 検知対象のメッセージ

        Returns:
            Tuple[TemplateMatch, TemplateDetectionError]: マッチ結果とエラー情報
        """
        match = self.detect(message)

        if match:
            return match, None

        # マッチしなかった場合のエラー分析
        error = self._analyze_detection_failure(message)
        return None, error

    def _analyze_detection_failure(self, message: str) -> TemplateDetectionError:
        """検知失敗の詳細分析"""
        # 部分マッチの検出
        partial_matches = self._find_partial_matches(message)

        # 類似パターンの検出
        closest_patterns = self._find_closest_patterns(message)

        # 修正候補の生成
        suggestions = self._generate_suggestions(
            message, partial_matches, closest_patterns
        )

        # 修正例の生成
        fix_examples = self._generate_fix_examples(message, partial_matches)

        # エラータイプの判定
        error_type = self._classify_error_type(message, partial_matches)

        return TemplateDetectionError(
            message=message,
            error_type=error_type,
            suggestions=suggestions,
            closest_patterns=closest_patterns,
            partial_matches=partial_matches,
            fix_examples=fix_examples,
        )

    def _find_partial_matches(self, message: str) -> list[str]:
        """部分マッチを検出"""
        partial_matches = []

        # 一般的なプレフィックスパターン
        prefixes = {
            "TASK:": TemplateType.TASK,
            "WORKER_RESULT:": TemplateType.WORKER_RESULT,
            "QUEEN_FINAL_REPORT:": TemplateType.QUEEN_REPORT,
            "COLLABORATE:": TemplateType.COLLABORATION,
            "APPROVAL:": TemplateType.APPROVAL,
        }

        for prefix, template_type in prefixes.items():
            if message.startswith(prefix):
                partial_matches.append(template_type.value)

        # キーワードベースの部分マッチ
        keywords = {
            "task": [TemplateType.TASK],
            "result": [TemplateType.WORKER_RESULT],
            "report": [TemplateType.QUEEN_REPORT],
            "collaborate": [TemplateType.COLLABORATION],
            "approval": [TemplateType.APPROVAL],
        }

        message_lower = message.lower()
        for keyword, template_types in keywords.items():
            if keyword in message_lower:
                for template_type in template_types:
                    if template_type.value not in partial_matches:
                        partial_matches.append(template_type.value)

        return partial_matches

    def _find_closest_patterns(self, message: str) -> list[tuple[str, float]]:
        """最も類似したパターンを検出"""
        similarities = []

        for template_type, pattern in self.registry.patterns.items():
            # パターンから例を生成
            example = self._pattern_to_example(pattern, template_type)

            # 類似度計算
            similarity = difflib.SequenceMatcher(None, message, example).ratio()
            similarities.append((template_type.value, similarity))

        # 類似度順にソート
        similarities.sort(key=lambda x: x[1], reverse=True)

        # 上位3つを返す
        return similarities[:3]

    def _pattern_to_example(self, pattern: str, template_type: TemplateType) -> str:
        """パターンから使用例を生成"""
        examples = {
            TemplateType.TASK: "TASK:EXAMPLE_001:サンプルタスクの実行",
            TemplateType.WORKER_RESULT: "WORKER_RESULT:developer:EXAMPLE_001:作業完了報告",
            TemplateType.QUEEN_REPORT: "QUEEN_FINAL_REPORT:session_001:最終報告",
            TemplateType.COLLABORATION: "COLLABORATE:PROJECT_001:Worker間の協力",
            TemplateType.APPROVAL: "APPROVAL:reviewer:TASK_001:承認完了",
        }

        return examples.get(template_type, "TEMPLATE:EXAMPLE")

    def _generate_suggestions(
        self,
        message: str,
        partial_matches: list[str],
        closest_patterns: list[tuple[str, float]],
    ) -> list[str]:
        """修正候補を生成"""
        suggestions = []

        # 部分マッチに基づく提案
        if partial_matches:
            for partial_match in partial_matches[:2]:  # 上位2つ
                template_type = TemplateType(partial_match)
                if template_type == TemplateType.TASK:
                    suggestions.append("正しい形式: TASK:[タスクID]:[指示内容]")
                elif template_type == TemplateType.WORKER_RESULT:
                    suggestions.append(
                        "正しい形式: WORKER_RESULT:[Worker名]:[タスクID]:[結果]"
                    )
                elif template_type == TemplateType.QUEEN_REPORT:
                    suggestions.append(
                        "正しい形式: QUEEN_FINAL_REPORT:[セッションID]:[報告内容]"
                    )

        # 最も類似したパターンに基づく提案
        if closest_patterns and closest_patterns[0][1] > 0.3:
            best_match = closest_patterns[0][0]
            example = self._pattern_to_example("", TemplateType(best_match))
            suggestions.append(f"類似パターン: {example}")

        # 一般的な修正提案
        if not suggestions:
            suggestions.extend(
                [
                    "テンプレート形式を確認してください",
                    "利用可能なテンプレート: python3 scripts/hive_cli.py template show",
                    "例: TASK:001:タスクの説明",
                ]
            )

        return suggestions

    def _generate_fix_examples(
        self, message: str, partial_matches: list[str]
    ) -> list[str]:
        """修正例を生成"""
        fix_examples = []

        if partial_matches:
            for partial_match in partial_matches[:1]:  # 最初の1つ
                template_type = TemplateType(partial_match)

                if template_type == TemplateType.TASK:
                    # メッセージから推測してタスク例を生成
                    clean_message = message.replace("TASK:", "").strip()
                    if clean_message:
                        fix_examples.append(f"TASK:AUTO_001:{clean_message}")
                    else:
                        fix_examples.append("TASK:EXAMPLE_001:具体的なタスク内容を記述")

                elif template_type == TemplateType.WORKER_RESULT:
                    clean_message = message.replace("WORKER_RESULT:", "").strip()
                    if clean_message:
                        fix_examples.append(
                            f"WORKER_RESULT:developer:AUTO_001:{clean_message}"
                        )
                    else:
                        fix_examples.append(
                            "WORKER_RESULT:worker_name:TASK_001:作業結果の詳細"
                        )

        return fix_examples

    def _classify_error_type(self, message: str, partial_matches: list[str]) -> str:
        """エラータイプを分類"""
        if not message.strip():
            return "empty_message"
        elif partial_matches:
            return "incomplete_pattern"
        elif ":" in message:
            return "invalid_format"
        else:
            return "no_pattern_detected"

    def detect_all(self, message: str) -> list[TemplateMatch]:
        """
        メッセージから全ての可能なテンプレートを検知

        Args:
            message: 検知対象のメッセージ

        Returns:
            List[TemplateMatch]: マッチした全てのテンプレート情報
        """
        matches = []

        for template_type, compiled_pattern in self.registry.compiled_patterns.items():
            for match in compiled_pattern.finditer(message):
                matches.append(
                    TemplateMatch(
                        template_type=template_type,
                        pattern=self.registry.patterns[template_type],
                        groups=match.groups(),
                        full_match=match.group(0),
                        raw_message=message,
                        confidence=self._calculate_confidence(
                            template_type, match, message
                        ),
                    )
                )

        # 信頼度順にソート
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches

    def _calculate_confidence(
        self, template_type: TemplateType, match: re.Match, message: str
    ) -> float:
        """
        マッチの信頼度を計算

        Args:
            template_type: テンプレートタイプ
            match: 正規表現マッチオブジェクト
            message: 元メッセージ

        Returns:
            float: 信頼度（0.0-1.0）
        """
        base_confidence = 0.8

        # マッチ部分がメッセージの先頭にある場合は信頼度を上げる
        if match.start() == 0:
            base_confidence += 0.1

        # マッチ部分がメッセージ全体の大部分を占める場合は信頼度を上げる
        match_ratio = len(match.group(0)) / len(message)
        if match_ratio > 0.5:
            base_confidence += 0.1

        return min(1.0, base_confidence)

    def get_statistics(self) -> dict[str, Any]:
        """検知統計情報を取得"""
        total = self.detection_stats["total_messages"]
        matches = self.detection_stats["template_matches"]

        return {
            "total_messages_processed": total,
            "total_template_matches": matches,
            "match_rate": matches / total if total > 0 else 0.0,
            "matches_by_type": {
                template_type.value: count
                for template_type, count in self.by_type_stats.items()
            },
        }


class TemplateAnalyzer:
    """テンプレートマッチ結果の分析機能"""

    @staticmethod
    def extract_task_info(match: TemplateMatch) -> dict[str, str] | None:
        """TASKテンプレートから情報を抽出"""
        if match.template_type != TemplateType.TASK:
            return None

        if len(match.groups) >= 2:
            return {
                "task_id": match.groups[0],
                "instruction": match.groups[1],
                "template_type": "task",
            }
        return None

    @staticmethod
    def extract_worker_result_info(match: TemplateMatch) -> dict[str, str] | None:
        """WORKER_RESULTテンプレートから情報を抽出"""
        if match.template_type != TemplateType.WORKER_RESULT:
            return None

        if len(match.groups) >= 3:
            return {
                "worker_name": match.groups[0],
                "task_id": match.groups[1],
                "result_content": match.groups[2],
                "template_type": "worker_result",
            }
        return None

    @staticmethod
    def extract_queen_report_info(match: TemplateMatch) -> dict[str, str] | None:
        """QUEEN_FINAL_REPORTテンプレートから情報を抽出"""
        if match.template_type != TemplateType.QUEEN_REPORT:
            return None

        if len(match.groups) >= 2:
            return {
                "session_id": match.groups[0],
                "report_content": match.groups[1],
                "template_type": "queen_report",
            }
        return None


# 使用例とテスト
if __name__ == "__main__":
    # テンプレート検知器を初期化
    detector = TemplateDetector()
    analyzer = TemplateAnalyzer()

    # テストメッセージ
    test_messages = [
        "TASK:TEMPLATE_002:テンプレート機能のプロトタイプ実装を開始してください。",
        "WORKER_RESULT:developer:TEMPLATE_002:Hive CLIシステム調査完了。詳細分析を実施しました。",
        "QUEEN_FINAL_REPORT:session_84:Issue #84の分析・説明完了",
        "通常のメッセージ（テンプレートではない）",
        "APPROVAL:reviewer:TASK_002:コードレビュー完了、承認します",
    ]

    print("🔍 Template Detection Test Results")
    print("=" * 50)

    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Test Message {i}: {message[:50]}...")

        match = detector.detect(message)
        if match:
            print(f"✅ Template Detected: {match.template_type.value}")
            print(f"   Confidence: {match.confidence:.2f}")
            print(f"   Groups: {match.groups}")

            # 詳細分析
            if match.template_type == TemplateType.TASK:
                info = analyzer.extract_task_info(match)
                if info:
                    print(f"   📋 Task ID: {info['task_id']}")
                    print(f"   📝 Instruction: {info['instruction'][:50]}...")

            elif match.template_type == TemplateType.WORKER_RESULT:
                info = analyzer.extract_worker_result_info(match)
                if info:
                    print(f"   👨‍💻 Worker: {info['worker_name']}")
                    print(f"   📋 Task ID: {info['task_id']}")
                    print(f"   📄 Result: {info['result_content'][:50]}...")
        else:
            print("❌ No template detected")

    print("\n📊 Detection Statistics:")
    stats = detector.get_statistics()
    print(f"   Total Messages: {stats['total_messages_processed']}")
    print(f"   Template Matches: {stats['total_template_matches']}")
    print(f"   Match Rate: {stats['match_rate']:.2%}")
