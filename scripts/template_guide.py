#!/usr/bin/env python3
"""
Template Guide - 対話式テンプレート作成ガイド
CODE_IMPROVEMENT:reviewer 対応

ユーザーが適切なテンプレートを簡単に作成できるよう、
対話式のガイド機能を提供
"""

import sys
from enum import Enum


class GuideMode(Enum):
    """ガイドモード"""

    QUICK_ASSIST = "quick"
    DETAILED_GUIDE = "detailed"
    INTERACTIVE_BUILDER = "builder"


class TemplateGuide:
    """対話式テンプレート作成ガイド"""

    def __init__(self) -> None:
        self.templates_info = {
            "TASK": {
                "pattern": "TASK:[タスクID]:[指示内容]",
                "description": "QueenからWorkerへのタスク指示",
                "use_case": "新しいタスクを依頼する時",
                "example": "TASK:BUG_FIX_001:ログイン機能のバグを修正してください",
                "questions": [
                    ("task_id", "タスクID（例: BUG_FIX_001, FEATURE_002）:"),
                    ("instruction", "具体的な指示内容:"),
                ],
            },
            "WORKER_RESULT": {
                "pattern": "WORKER_RESULT:[Worker名]:[タスクID]:[結果]",
                "description": "WorkerからQueenへの作業結果報告",
                "use_case": "作業完了時の報告",
                "example": "WORKER_RESULT:developer:BUG_FIX_001:バグ修正完了、テスト済み",
                "questions": [
                    ("worker", "Worker名（developer/tester/analyzer/etc）:"),
                    ("task_id", "対応したタスクID:"),
                    ("result", "作業結果の詳細:"),
                ],
            },
            "QUEEN_FINAL_REPORT": {
                "pattern": "QUEEN_FINAL_REPORT:[セッションID]:[報告内容]",
                "description": "QueenからBeekeeperへの最終報告",
                "use_case": "プロジェクト完了時の総括報告",
                "example": "QUEEN_FINAL_REPORT:session_001:全タスク完了、品質確認済み",
                "questions": [
                    ("session_id", "セッションID（例: session_001, project_alpha）:"),
                    ("report", "最終報告内容:"),
                ],
            },
        }

    def start_interactive_guide(self) -> None:
        """対話式ガイドを開始"""
        print("🐝 Hive Template Creation Guide")
        print("=" * 50)
        print("適切なテンプレートの作成をお手伝いします！\n")

        # モード選択
        mode = self._select_mode()

        if mode == GuideMode.QUICK_ASSIST:
            self._quick_assist_mode()
        elif mode == GuideMode.DETAILED_GUIDE:
            self._detailed_guide_mode()
        elif mode == GuideMode.INTERACTIVE_BUILDER:
            self._interactive_builder_mode()

    def _select_mode(self) -> GuideMode:
        """ガイドモードを選択"""
        print("📋 どのようなサポートが必要ですか？")
        print("1. 🚀 クイックアシスト - 目的に応じたテンプレートを素早く提案")
        print("2. 📚 詳細ガイド - テンプレートの詳しい説明と使い方")
        print("3. 🛠️  対話式ビルダー - ステップバイステップでテンプレート作成")

        while True:
            choice = input("\n選択してください (1-3): ").strip()

            if choice == "1":
                return GuideMode.QUICK_ASSIST
            elif choice == "2":
                return GuideMode.DETAILED_GUIDE
            elif choice == "3":
                return GuideMode.INTERACTIVE_BUILDER
            else:
                print("❌ 1、2、3のいずれかを入力してください")

    def _quick_assist_mode(self) -> None:
        """クイックアシストモード"""
        print("\n🚀 クイックアシストモード")
        print("-" * 30)

        purpose = self._ask_purpose()
        template_type = self._suggest_template_type(purpose)

        if template_type:
            template_info = self.templates_info[template_type]
            print(f"\n💡 推奨テンプレート: {template_type}")
            print(f"📝 形式: {template_info['pattern']}")
            print(f"📖 説明: {template_info['description']}")
            print(f"💼 使用例: {template_info['example']}")

            if self._ask_yes_no(
                "\nこのテンプレートを使用してメッセージを作成しますか？"
            ):
                message = self._build_template_interactive(template_type)
                print("\n✅ 完成したメッセージ:")
                print(f"📄 {message}")
                self._show_usage_instructions(message)
        else:
            print("\n❓ 適切なテンプレートが見つかりませんでした")
            print("💡 詳細ガイドモードをお試しください")

    def _detailed_guide_mode(self) -> None:
        """詳細ガイドモード"""
        print("\n📚 詳細ガイドモード")
        print("-" * 30)

        print("利用可能なテンプレート:")
        for i, (template_type, info) in enumerate(self.templates_info.items(), 1):
            print(f"{i}. {template_type}")
            print(f"   📝 {info['description']}")
            print(f"   🎯 {info['use_case']}")
            print(f"   💼 例: {info['example']}")
            print()

        # テンプレート選択
        while True:
            choice = input(
                "詳細を見たいテンプレート番号 (1-3) または 'q' で終了: "
            ).strip()

            if choice.lower() == "q":
                break

            try:
                index = int(choice) - 1
                template_types = list(self.templates_info.keys())
                if 0 <= index < len(template_types):
                    template_type = template_types[index]
                    self._show_template_details(template_type)

                    if self._ask_yes_no("このテンプレートでメッセージを作成しますか？"):
                        message = self._build_template_interactive(template_type)
                        print("\n✅ 完成したメッセージ:")
                        print(f"📄 {message}")
                        self._show_usage_instructions(message)
                        break
                else:
                    print("❌ 無効な番号です")
            except ValueError:
                print("❌ 数字を入力してください")

    def _interactive_builder_mode(self) -> None:
        """対話式ビルダーモード"""
        print("\n🛠️  対話式ビルダーモード")
        print("-" * 30)
        print("質問に答えて、最適なテンプレートを作成します\n")

        # 目的を詳しく聞く
        purpose = self._ask_detailed_purpose()

        # 推奨テンプレートを提案
        template_type = self._suggest_template_type(purpose)

        if template_type:
            print(f"\n🎯 推奨テンプレート: {template_type}")
            template_info = self.templates_info[template_type]
            print(f"📖 {template_info['description']}")

            if self._ask_yes_no("この推奨テンプレートを使用しますか？"):
                message = self._build_template_interactive(template_type)
            else:
                # 別のテンプレートを選択
                template_type = self._select_template_manual()
                message = self._build_template_interactive(template_type)
        else:
            # 手動選択
            template_type = self._select_template_manual()
            message = self._build_template_interactive(template_type)

        print("\n✅ 完成したメッセージ:")
        print(f"📄 {message}")

        # バリデーション
        if self._validate_template_message(message):
            print("✅ テンプレート形式が正しいです")
        else:
            print("⚠️  テンプレート形式を確認してください")

        self._show_usage_instructions(message)

    def _ask_purpose(self) -> str:
        """目的を質問"""
        print("何をしたいですか？")
        print("1. 新しいタスクを依頼したい")
        print("2. 作業結果を報告したい")
        print("3. プロジェクトの最終報告をしたい")
        print("4. その他")

        choice = input("選択してください (1-4): ").strip()

        purposes = {
            "1": "task_assignment",
            "2": "result_report",
            "3": "final_report",
            "4": "other",
        }

        return purposes.get(choice, "other")

    def _ask_detailed_purpose(self) -> str:
        """詳細な目的を質問"""
        questions = [
            "どのような作業を行いたいですか？（自由記述）",
            "誰に向けたメッセージですか？（Queen/Worker/Beekeeper）",
            "緊急度はどの程度ですか？（高/中/低）",
        ]

        answers = []
        for question in questions:
            answer = input(f"📝 {question}: ").strip()
            answers.append(answer)

        # 回答を分析して目的を判定
        content = " ".join(answers).lower()

        if any(
            word in content
            for word in ["task", "依頼", "やって", "実装", "修正", "作成"]
        ):
            return "task_assignment"
        elif any(
            word in content for word in ["result", "報告", "完了", "終了", "結果"]
        ):
            return "result_report"
        elif any(word in content for word in ["final", "最終", "総括", "まとめ"]):
            return "final_report"
        else:
            return "other"

    def _suggest_template_type(self, purpose: str) -> str | None:
        """目的に基づいてテンプレートタイプを提案"""
        suggestions = {
            "task_assignment": "TASK",
            "result_report": "WORKER_RESULT",
            "final_report": "QUEEN_FINAL_REPORT",
        }

        return suggestions.get(purpose)

    def _select_template_manual(self) -> str:
        """手動でテンプレートを選択"""
        print("\n利用可能なテンプレート:")
        template_types = list(self.templates_info.keys())

        for i, template_type in enumerate(template_types, 1):
            info = self.templates_info[template_type]
            print(f"{i}. {template_type} - {info['description']}")

        while True:
            choice = input("テンプレート番号を選択してください: ").strip()
            try:
                index = int(choice) - 1
                if 0 <= index < len(template_types):
                    return template_types[index]
                else:
                    print("❌ 無効な番号です")
            except ValueError:
                print("❌ 数字を入力してください")

    def _build_template_interactive(self, template_type: str) -> str:
        """対話式でテンプレートを構築"""
        template_info = self.templates_info[template_type]

        print(f"\n🔧 {template_type} テンプレートを作成します")
        print(f"形式: {template_info['pattern']}")
        print(f"例: {template_info['example']}\n")

        answers = {}

        for field, question in template_info["questions"]:
            while True:
                answer = input(f"📝 {question} ").strip()
                if answer:
                    answers[field] = answer
                    break
                else:
                    print("❌ 空欄にはできません。何かしら入力してください")

        # テンプレートを構築
        if template_type == "TASK":
            return f"TASK:{answers['task_id']}:{answers['instruction']}"
        elif template_type == "WORKER_RESULT":
            return f"WORKER_RESULT:{answers['worker']}:{answers['task_id']}:{answers['result']}"
        elif template_type == "QUEEN_FINAL_REPORT":
            return f"QUEEN_FINAL_REPORT:{answers['session_id']}:{answers['report']}"

        return ""

    def _show_template_details(self, template_type: str) -> None:
        """テンプレートの詳細情報を表示"""
        info = self.templates_info[template_type]

        print(f"\n📖 {template_type} テンプレート詳細")
        print("=" * 40)
        print(f"📝 形式: {info['pattern']}")
        print(f"📖 説明: {info['description']}")
        print(f"🎯 使用場面: {info['use_case']}")
        print(f"💼 使用例: {info['example']}")

        # 各フィールドの説明
        print("\n📋 入力フィールド:")
        for field, _question in info["questions"]:
            field_description = self._get_field_description(field)
            print(f"  • {field}: {field_description}")
        print()

    def _get_field_description(self, field: str) -> str:
        """フィールドの説明を取得"""
        descriptions = {
            "task_id": "一意のタスク識別子（例: BUG_FIX_001, FEATURE_002）",
            "instruction": "具体的で明確な指示内容",
            "worker": "作業を行うWorker名（developer, tester, analyzer等）",
            "result": "作業結果の詳細な説明",
            "session_id": "プロジェクトやセッションの識別子",
            "report": "最終的な成果や総括内容",
        }

        return descriptions.get(field, "詳細情報")

    def _validate_template_message(self, message: str) -> bool:
        """テンプレートメッセージの基本バリデーション"""
        # 基本的なパターンチェック
        patterns = [
            r"^TASK:[A-Z0-9_]+:.+",
            r"^WORKER_RESULT:\w+:[A-Z0-9_]+:.+",
            r"^QUEEN_FINAL_REPORT:[a-zA-Z0-9_]+:.+",
        ]

        import re

        return any(re.match(pattern, message) for pattern in patterns)

    def _show_usage_instructions(self, message: str) -> None:
        """使用方法の説明を表示"""
        print("\n📚 使用方法:")
        print("以下のコマンドでメッセージを送信できます:")
        print("```bash")
        print(f'python3 scripts/hive_cli.py send queen "{message}"')
        print("```")

        print("\nまたは、テンプレート機能を使用:")
        print("```bash")
        print(f'python3 scripts/hive_cli.py template send queen "{message}" --ui')
        print("```")

        print("\n💡 テンプレート検知のテスト:")
        print("```bash")
        print(f'python3 scripts/hive_cli.py template detect "{message}"')
        print("```")

    def _ask_yes_no(self, question: str) -> bool:
        """Yes/No質問"""
        while True:
            answer = input(f"{question} (y/n): ").strip().lower()
            if answer in ["y", "yes", "はい"]:
                return True
            elif answer in ["n", "no", "いいえ"]:
                return False
            else:
                print("❌ 'y' または 'n' で回答してください")


# チュートリアル機能
class TemplateTutorial:
    """テンプレートチュートリアル"""

    def run_tutorial(self) -> None:
        """チュートリアルを実行"""
        print("🎓 Hive Template Tutorial")
        print("=" * 50)
        print("Hiveテンプレートシステムの基本的な使い方を学びましょう！\n")

        # レッスン1: 基本概念
        self._lesson_1_basics()

        if self._ask_continue():
            # レッスン2: 実践例
            self._lesson_2_practice()

        if self._ask_continue():
            # レッスン3: 応用
            self._lesson_3_advanced()

        print("\n🎉 チュートリアル完了！")
        print("💡 実際にテンプレートを使ってみましょう:")
        print("   python3 scripts/hive_cli.py template guide")

    def _lesson_1_basics(self) -> None:
        """レッスン1: 基本概念"""
        print("📚 レッスン1: テンプレートの基本概念")
        print("-" * 40)
        print("Hiveでは、Worker間の通信に定型的なテンプレートを使用します。")
        print("これにより、一貫性のある効率的なコミュニケーションが可能になります。\n")

        print("🎯 主なテンプレート:")
        print("1. TASK: QueenからWorkerへのタスク指示")
        print("2. WORKER_RESULT: WorkerからQueenへの結果報告")
        print("3. QUEEN_FINAL_REPORT: QueenからBeekeeperへの最終報告\n")

        input("📝 Enter キーを押して次に進む...")

    def _lesson_2_practice(self) -> None:
        """レッスン2: 実践例"""
        print("\n📚 レッスン2: 実践例")
        print("-" * 40)
        print("実際のテンプレート例を見てみましょう:\n")

        examples = [
            ("タスク指示", "TASK:BUG_FIX_001:ログイン機能のバグを修正してください"),
            (
                "結果報告",
                "WORKER_RESULT:developer:BUG_FIX_001:バグ修正完了、テスト済み",
            ),
            ("最終報告", "QUEEN_FINAL_REPORT:session_001:全タスク完了、品質確認済み"),
        ]

        for title, example in examples:
            print(f"💼 {title}:")
            print(f"   {example}\n")

        input("📝 Enter キーを押して次に進む...")

    def _lesson_3_advanced(self) -> None:
        """レッスン3: 応用"""
        print("\n📚 レッスン3: 応用機能")
        print("-" * 40)
        print("Hive CLIの便利な機能:\n")

        features = [
            (
                "テンプレート検知",
                "template detect",
                "メッセージがテンプレート形式かチェック",
            ),
            ("テンプレート表示", "template show", "利用可能なテンプレートを表示"),
            ("UI付き送信", "template send --ui", "視覚的なフィードバック付きで送信"),
            ("対話式ガイド", "template guide", "テンプレート作成をサポート"),
        ]

        for feature, command, description in features:
            print(f"🔧 {feature}:")
            print(f"   コマンド: python3 scripts/hive_cli.py {command}")
            print(f"   説明: {description}\n")

    def _ask_continue(self) -> bool:
        """続行確認"""
        while True:
            answer = input("次のレッスンに進みますか？ (y/n): ").strip().lower()
            if answer in ["y", "yes", "はい"]:
                return True
            elif answer in ["n", "no", "いいえ"]:
                return False
            else:
                print("❌ 'y' または 'n' で回答してください")


# CLI統合
def main() -> None:
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("Usage: python3 template_guide.py [guide|tutorial]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "guide":
        guide = TemplateGuide()
        guide.start_interactive_guide()
    elif command == "tutorial":
        tutorial = TemplateTutorial()
        tutorial.run_tutorial()
    else:
        print("❌ Unknown command. Use 'guide' or 'tutorial'")
        sys.exit(1)


if __name__ == "__main__":
    main()
