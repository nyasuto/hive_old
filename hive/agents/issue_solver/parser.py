"""
User Prompt Parser

ユーザーの自然言語プロンプトを解析して構造化データに変換します。
"""

import re
from typing import Any

from ..mixins import LoggingMixin, ValidationMixin


class UserPromptParser(LoggingMixin, ValidationMixin):
    """ユーザープロンプト解析器"""

    def __init__(self):
        self.setup_logger("user_prompt_parser")

        # 意図キーワード
        self.intent_keywords = {
            "solve": ["解決", "修正", "直す", "fix", "solve", "repair"],
            "investigate": ["調査", "確認", "見て", "check", "investigate", "analyze"],
            "explain": ["説明", "教えて", "について", "explain", "describe", "tell"],
            "implement": ["実装", "作る", "追加", "implement", "create", "add"],
        }

        # 優先度キーワード
        self.priority_keywords = {
            "high": ["緊急", "重要", "クリティカル", "urgent", "critical", "important"],
            "low": ["後で", "時間があるとき", "later", "when possible", "low priority"],
        }

    def parse_user_prompt(self, prompt: str) -> dict[str, Any]:
        """
        ユーザープロンプトを解析してアクションを特定

        Args:
            prompt: ユーザーの自然言語プロンプト

        Returns:
            解析結果の辞書
        """
        self.log_info(f"Parsing prompt: {prompt}")

        # 入力検証
        if not prompt or not prompt.strip():
            return self._create_error_result("Empty prompt provided")

        prompt_lower = prompt.lower()

        # Issue番号抽出
        issue_number = self._extract_issue_number(prompt)
        if not issue_number:
            return self._create_error_result("No issue number found in prompt")

        # 意図分析
        intent = self._analyze_intent(prompt_lower)

        # 優先度推定
        priority = self._estimate_priority(prompt_lower)

        # 追加情報抽出
        additional_info = self._extract_additional_info(prompt)

        result = {
            "success": True,
            "original_prompt": prompt,
            "issue_number": issue_number,
            "intent": intent,
            "priority": priority,
            "action_required": True,
            "additional_info": additional_info,
        }

        self.log_info(
            f"Parsed result: intent={intent}, priority={priority}, issue={issue_number}"
        )
        return result

    def _extract_issue_number(self, prompt: str) -> int | None:
        """Issue番号抽出"""
        # GitHub URL パターン
        github_pattern = r"github\.com/[^/]+/[^/]+/issues/(\d+)"
        github_match = re.search(github_pattern, prompt)
        if github_match:
            return int(github_match.group(1))

        # Issue番号パターン
        issue_patterns = [
            r"issue\s*#?(\d+)",
            r"#(\d+)",
            r"(\d+)番",
            r"issue\s+(\d+)",
        ]

        for pattern in issue_patterns:
            match = re.search(pattern, prompt.lower())
            if match:
                return int(match.group(1))

        return None

    def _analyze_intent(self, prompt_lower: str) -> str:
        """意図分析"""
        intent_scores = dict.fromkeys(self.intent_keywords.keys(), 0)

        # キーワードマッチング
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    intent_scores[intent] += 1

        # 最高スコアの意図を選択
        max_score = max(intent_scores.values())
        if max_score > 0:
            for intent, score in intent_scores.items():
                if score == max_score:
                    return intent

        # デフォルト意図
        return "solve"

    def _estimate_priority(self, prompt_lower: str) -> str:
        """優先度推定"""
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    return priority

        return "medium"  # デフォルト優先度

    def _extract_additional_info(self, prompt: str) -> dict[str, Any]:
        """追加情報抽出"""
        additional_info = {
            "has_url": "github.com" in prompt.lower(),
            "has_urgency_keywords": any(
                keyword in prompt.lower() for keyword in self.priority_keywords["high"]
            ),
            "prompt_length": len(prompt),
            "language": "japanese"
            if any(
                char >= "\u3040"
                and char <= "\u309f"  # ひらがな
                or char >= "\u30a0"
                and char <= "\u30ff"  # カタカナ
                or char >= "\u4e00"
                and char <= "\u9faf"  # 漢字
                for char in prompt
            )
            else "english",
        }

        return additional_info

    def _create_error_result(self, error_message: str) -> dict[str, Any]:
        """エラー結果作成"""
        self.log_error(f"Parser error: {error_message}")
        return {
            "success": False,
            "error": error_message,
            "original_prompt": "",
            "issue_number": None,
            "intent": "unknown",
            "priority": "medium",
            "action_required": False,
            "additional_info": {},
        }

    def validate_parse_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """解析結果検証"""
        return self.validate_output(result, dict)
