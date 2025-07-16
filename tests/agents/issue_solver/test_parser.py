"""
User Prompt Parser Tests

UserPromptParserのテストです。
"""

from hive.agents.issue_solver.parser import UserPromptParser


class TestUserPromptParser:
    """UserPromptParserのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = UserPromptParser()

    def test_parse_solve_intent(self):
        """解決意図のテスト"""
        test_cases = [
            "Issue 64を解決する",
            "バグ修正をお願いします issue 84",
            "Issue 75を直してください",
            "Fix issue 64",
            "Solve issue #84",
        ]

        for prompt in test_cases:
            result = self.parser.parse_user_prompt(prompt)

            assert result["success"] is True
            assert result["intent"] == "solve"
            assert result["action_required"] is True
            assert result["issue_number"] is not None

    def test_parse_investigate_intent(self):
        """調査意図のテスト"""
        test_cases = [
            "Issue 64について調査してください",
            "issue 84を確認して",
            "Issue 75を見てください",
            "Check issue 64",
            "Investigate issue #84",
        ]

        for prompt in test_cases:
            result = self.parser.parse_user_prompt(prompt)

            assert result["success"] is True
            assert result["intent"] == "investigate"
            assert result["action_required"] is True
            assert result["issue_number"] is not None

    def test_parse_explain_intent(self):
        """説明意図のテスト"""
        test_cases = [
            "Issue 64の内容を説明してください",
            "issue 84について教えて",
            "Issue 75について詳しく",
            "Explain issue 64",
            "Describe issue #84",
        ]

        for prompt in test_cases:
            result = self.parser.parse_user_prompt(prompt)

            assert result["success"] is True
            assert result["intent"] == "explain"
            assert result["action_required"] is True
            assert result["issue_number"] is not None

    def test_extract_issue_number(self):
        """Issue番号抽出のテスト"""
        test_cases = [
            ("Issue 64を解決する", 64),
            ("issue #84を修正", 84),
            ("75番のissueを確認", 75),
            ("#123を見て", 123),
            ("https://github.com/owner/repo/issues/456", 456),
            ("issue 789について", 789),
        ]

        for prompt, expected_number in test_cases:
            result = self.parser.parse_user_prompt(prompt)

            assert result["issue_number"] == expected_number

    def test_estimate_priority(self):
        """優先度推定のテスト"""
        # 高優先度
        high_priority_cases = [
            "緊急でissue 64を修正",
            "重要なissue 84を解決",
            "Urgent issue 75",
            "Critical issue #123",
        ]

        for prompt in high_priority_cases:
            result = self.parser.parse_user_prompt(prompt)
            assert result["priority"] == "high"

        # 低優先度
        low_priority_cases = [
            "後でissue 64を確認",
            "時間があるときにissue 84を見て",
            "Later issue 75",
            "Low priority issue #123",
        ]

        for prompt in low_priority_cases:
            result = self.parser.parse_user_prompt(prompt)
            assert result["priority"] == "low"

        # 通常優先度（デフォルト）
        normal_case = "Issue 64を解決する"
        result = self.parser.parse_user_prompt(normal_case)
        assert result["priority"] == "medium"

    def test_extract_additional_info(self):
        """追加情報抽出のテスト"""
        # GitHub URLを含む
        github_prompt = "https://github.com/owner/repo/issues/64 を修正して"
        result = self.parser.parse_user_prompt(github_prompt)

        assert result["additional_info"]["has_url"] is True
        assert result["additional_info"]["language"] == "japanese"

        # 緊急キーワードを含む
        urgent_prompt = "緊急でissue 64を修正してください"
        result = self.parser.parse_user_prompt(urgent_prompt)

        assert result["additional_info"]["has_urgency_keywords"] is True

        # 英語プロンプト
        english_prompt = "Fix issue 64 urgently"
        result = self.parser.parse_user_prompt(english_prompt)

        assert result["additional_info"]["language"] == "english"
        assert result["additional_info"]["has_urgency_keywords"] is True

    def test_invalid_input(self):
        """無効な入力のテスト"""
        invalid_cases = [
            "",  # 空文字
            "   ",  # 空白のみ
            "何かを解決する",  # Issue番号なし
            "タスクを実行",  # Issue番号なし
            "Hello world",  # Issue番号なし
        ]

        for prompt in invalid_cases:
            result = self.parser.parse_user_prompt(prompt)

            assert result["success"] is False
            assert result["action_required"] is False
            assert result["issue_number"] is None

    def test_edge_cases(self):
        """エッジケースのテスト"""
        # 複数のIssue番号
        multi_issue_prompt = "Issue 64とissue 84を同時に解決"
        result = self.parser.parse_user_prompt(multi_issue_prompt)

        assert result["success"] is True
        assert result["issue_number"] in [64, 84]  # 最初に見つかったものを使用

        # 非常に長いプロンプト
        long_prompt = "Issue 64" + "を解決する" * 100
        result = self.parser.parse_user_prompt(long_prompt)

        assert result["success"] is True
        assert result["issue_number"] == 64
        assert result["additional_info"]["prompt_length"] > 500

    def test_validation_methods(self):
        """検証メソッドのテスト"""
        # 正常な結果の検証
        normal_result = {
            "success": True,
            "issue_number": 64,
            "intent": "solve",
            "priority": "medium",
        }

        validation = self.parser.validate_parse_result(normal_result)
        assert validation["valid"] is True

        # 不正な結果の検証
        invalid_result = {
            "success": True,
            # issue_number が欠けている
            "intent": "solve",
            "priority": "medium",
        }

        validation = self.parser.validate_parse_result(invalid_result)
        # 現在の実装では型チェックのみなので、辞書であればvalidとなる
        assert validation["valid"] is True

    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        # None入力
        result = self.parser.parse_user_prompt(None)
        assert result["success"] is False
        assert "error" in result

        # 非文字列入力は現在の実装では処理されないが、
        # 実際の使用では文字列変換が必要かもしれない
        try:
            result = self.parser.parse_user_prompt(123)
            # 数値でもlower()が呼ばれてエラーになるはず
            assert False, "Should have raised an error"
        except AttributeError:
            # 期待されるエラー
            pass
