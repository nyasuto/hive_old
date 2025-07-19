#!/usr/bin/env python3
"""
Template UI - テンプレート表示システム
TASK:TEMPLATE_004 UI表示機能実装

テンプレート検知結果を視覚的に表示するUI機能を提供
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from template_detector import TemplateMatch, TemplateType
else:
    try:
        from template_detector import TemplateMatch, TemplateType
    except ImportError:
        # If template_detector module is not found during type checking
        TemplateMatch = Any
        TemplateType = Any


@dataclass
class UIDisplayConfig:
    """UI表示設定"""

    icon: str
    title: str
    format_template: str


class TemplateUIFormatter:
    """テンプレートUI表示フォーマッター"""

    def __init__(self, templates_dir: str = "templates/communication"):
        self.templates_dir = Path(templates_dir)
        self.display_configs: dict[TemplateType, UIDisplayConfig] = {}
        self._load_display_configs()

    def _load_display_configs(self) -> None:
        """テンプレート設定ファイルからUI表示設定を読み込み"""
        template_files = self.templates_dir.glob("*.yaml")

        for template_file in template_files:
            try:
                with open(template_file, encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                template_name = config.get("name")
                ui_display = config.get("ui_display", {})

                # TemplateTypeにマッピング
                template_type = self._name_to_template_type(template_name)
                if template_type:
                    self.display_configs[template_type] = UIDisplayConfig(
                        icon=ui_display.get("icon", "📄"),
                        title=ui_display.get("title", "TEMPLATE DETECTED"),
                        format_template=ui_display.get("format", "{message}"),
                    )

            except Exception as e:
                print(f"Warning: Failed to load template config {template_file}: {e}")

    def _name_to_template_type(self, name: str) -> TemplateType | None:
        """テンプレート名からTemplateTypeに変換"""
        mapping = {
            "task_template": TemplateType.TASK,
            "worker_result_template": TemplateType.WORKER_RESULT,
            "collaboration_template": TemplateType.COLLABORATION,
            "queen_report_template": TemplateType.QUEEN_REPORT,
            "approval_template": TemplateType.APPROVAL,
        }
        return mapping.get(name)

    def format_template_display(self, match: TemplateMatch) -> str:
        """テンプレートマッチ結果を視覚的にフォーマット"""
        config = self.display_configs.get(match.template_type)
        if not config:
            return self._format_default_display(match)

        # テンプレートタイプ別の詳細フォーマット
        if match.template_type == TemplateType.TASK:
            return self._format_task_template(match, config)
        elif match.template_type == TemplateType.WORKER_RESULT:
            return self._format_worker_result_template(match, config)
        elif match.template_type == TemplateType.QUEEN_REPORT:
            return self._format_queen_report_template(match, config)
        else:
            return self._format_generic_template(match, config)

    def _format_task_template(
        self, match: TemplateMatch, config: UIDisplayConfig
    ) -> str:
        """TASKテンプレートのフォーマット"""
        if len(match.groups) >= 2:
            task_id = match.groups[0]
            instruction = match.groups[1]

            # 長い指示文は切り詰める
            if len(instruction) > 100:
                instruction = instruction[:97] + "..."

            return f"""
{config.icon} {config.title}
┌─ Task ID: {task_id}
├─ Instruction: {instruction}
├─ Confidence: {match.confidence:.2f}
└─ Pattern: TASK:[ID]:[INSTRUCTION]
"""
        return self._format_default_display(match)

    def _format_worker_result_template(
        self, match: TemplateMatch, config: UIDisplayConfig
    ) -> str:
        """WORKER_RESULTテンプレートのフォーマット"""
        if len(match.groups) >= 3:
            worker_name = match.groups[0]
            task_id = match.groups[1]
            result_content = match.groups[2]

            # 長い結果は切り詰める
            if len(result_content) > 100:
                result_content = result_content[:97] + "..."

            return f"""
{config.icon} {config.title}
┌─ Worker: {worker_name}
├─ Task ID: {task_id}
├─ Result: {result_content}
├─ Confidence: {match.confidence:.2f}
└─ Pattern: WORKER_RESULT:[WORKER]:[TASK_ID]:[RESULT]
"""
        return self._format_default_display(match)

    def _format_queen_report_template(
        self, match: TemplateMatch, config: UIDisplayConfig
    ) -> str:
        """QUEEN_FINAL_REPORTテンプレートのフォーマット"""
        if len(match.groups) >= 2:
            session_id = match.groups[0]
            report_content = match.groups[1]

            # 長いレポートは切り詰める
            if len(report_content) > 100:
                report_content = report_content[:97] + "..."

            return f"""
{config.icon} {config.title}
┌─ Session ID: {session_id}
├─ Report: {report_content}
├─ Confidence: {match.confidence:.2f}
└─ Pattern: QUEEN_FINAL_REPORT:[SESSION_ID]:[REPORT]
"""
        return self._format_default_display(match)

    def _format_generic_template(
        self, match: TemplateMatch, config: UIDisplayConfig
    ) -> str:
        """汎用テンプレートフォーマット"""
        groups_str = ", ".join(match.groups) if match.groups else "None"

        return f"""
{config.icon} {config.title}
┌─ Type: {match.template_type.value}
├─ Groups: {groups_str}
├─ Confidence: {match.confidence:.2f}
└─ Full Match: {match.full_match}
"""

    def _format_default_display(self, match: TemplateMatch) -> str:
        """デフォルト表示フォーマット"""
        return f"""
📄 TEMPLATE DETECTED
┌─ Type: {match.template_type.value}
├─ Groups: {", ".join(match.groups) if match.groups else "None"}
├─ Confidence: {match.confidence:.2f}
└─ Pattern: {match.pattern}
"""

    def format_no_template_message(self, message: str) -> str:
        """テンプレートが検知されない場合のフォーマット"""
        # メッセージが長い場合は切り詰める
        display_message = message
        if len(message) > 150:
            display_message = message[:147] + "..."

        return f"""
💬 REGULAR MESSAGE
┌─ Content: {display_message}
└─ No template pattern detected
"""

    def format_multiple_templates(self, matches: list[TemplateMatch]) -> str:
        """複数テンプレートが検知された場合のフォーマット"""
        if not matches:
            return "No templates detected"

        result = f"🔍 MULTIPLE TEMPLATES DETECTED ({len(matches)} matches)\n"

        for i, match in enumerate(matches, 1):
            result += f"\n--- Match {i} (Confidence: {match.confidence:.2f}) ---\n"
            result += self.format_template_display(match)

        return result

    def format_template_summary(self, matches: list[TemplateMatch]) -> str:
        """テンプレート検知結果のサマリー表示"""
        if not matches:
            return "📊 No templates detected in message"

        # テンプレートタイプ別にカウント
        type_counts: dict[str, int] = {}
        for match in matches:
            type_name = match.template_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        result = "📊 TEMPLATE DETECTION SUMMARY\n"
        result += f"┌─ Total matches: {len(matches)}\n"

        for template_type, count in type_counts.items():
            result += f"├─ {template_type}: {count}\n"

        # 最も信頼度の高いマッチを表示
        best_match = max(matches, key=lambda x: x.confidence)
        result += f"└─ Best match: {best_match.template_type.value} (confidence: {best_match.confidence:.2f})\n"

        return result


class TemplateUIManager:
    """テンプレートUI管理クラス"""

    def __init__(self, templates_dir: str = "templates/communication"):
        self.formatter = TemplateUIFormatter(templates_dir)
        self.history: list[dict[str, Any]] = []

    def display_template_result(
        self, message: str, matches: list[TemplateMatch]
    ) -> str:
        """テンプレート検知結果を表示用にフォーマット"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if not matches:
            formatted = self.formatter.format_no_template_message(message)
        elif len(matches) == 1:
            formatted = self.formatter.format_template_display(matches[0])
        else:
            formatted = self.formatter.format_multiple_templates(matches)

        # 履歴に追加
        self.history.append(
            {
                "timestamp": timestamp,
                "message": message,
                "matches": len(matches),
                "template_types": [m.template_type.value for m in matches],
            }
        )

        return f"[{timestamp}] {formatted}"

    def get_history_summary(self, last_n: int = 10) -> str:
        """最近のテンプレート検知履歴を表示"""
        if not self.history:
            return "📜 No template detection history"

        recent_history = self.history[-last_n:]

        result = f"📜 TEMPLATE DETECTION HISTORY (last {len(recent_history)} items)\n"
        result += "=" * 50 + "\n"

        for entry in recent_history:
            timestamp = entry["timestamp"]
            matches = entry["matches"]
            types = (
                ", ".join(entry["template_types"])
                if entry["template_types"]
                else "None"
            )

            result += f"{timestamp} | Matches: {matches} | Types: {types}\n"

        return result


# 使用例とテスト
if __name__ == "__main__":
    from template_detector import TemplateDetector

    # UI管理クラスを初期化
    ui_manager = TemplateUIManager()
    detector = TemplateDetector()

    # テストメッセージ
    test_messages = [
        "TASK:TEMPLATE_004:調査結果を基にテンプレート機能の実装を開始してください。",
        "WORKER_RESULT:developer:TEMPLATE_004:テンプレート実装完了、Queenに報告します。",
        "QUEEN_FINAL_REPORT:template_impl:テンプレート機能実装完了、テスト済み",
        "通常のメッセージです。テンプレートパターンは含まれていません。",
    ]

    print("🎨 Template UI Display Test")
    print("=" * 60)

    for message in test_messages:
        print(f"\n📝 Input: {message[:50]}...")

        # テンプレート検知
        matches = detector.detect_all(message)

        # UI表示
        display_result = ui_manager.display_template_result(message, matches)
        print(display_result)

    print("\n" + ui_manager.get_history_summary())
