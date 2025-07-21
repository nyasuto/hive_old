"""
User prompt parsing functionality.

Extracted from issue_solver_agent.py for better modularity.
"""

import re
from datetime import datetime
from typing import Any

from ..models import MessagePriority


class UserPromptParser:
    """ユーザープロンプト解析器"""

    def parse_user_prompt(self, prompt: str) -> dict[str, Any]:
        """ユーザープロンプトを解析"""
        prompt_lower = prompt.lower()

        # Issue番号抽出
        issue_number = self._extract_issue_number(prompt)

        # 意図認識
        intent = self._detect_intent(prompt_lower)

        # 優先度推定
        priority = self._estimate_priority(prompt_lower)

        # 複雑度推定
        complexity = self._estimate_complexity(prompt_lower)

        return {
            "original_prompt": prompt,
            "issue_number": issue_number,
            "intent": intent,
            "priority": priority,
            "complexity": complexity,
            "timestamp": datetime.now().isoformat(),
            "requires_investigation": "調査" in prompt or "investigate" in prompt_lower,
            "mentions_urgency": any(
                word in prompt_lower for word in ["緊急", "急いで", "urgent"]
            ),
            "mentions_files": bool(re.search(r"[a-zA-Z0-9_/.-]+\.[a-zA-Z]+", prompt)),
            "mentions_code": "コード" in prompt or "code" in prompt_lower,
            "mentions_test": "テスト" in prompt or "test" in prompt_lower,
        }

    def _extract_issue_number(self, prompt: str) -> str | None:
        """Issue番号抽出"""
        # GitHub URL形式
        url_match = re.search(r"/issues/(\d+)", prompt)
        if url_match:
            return url_match.group(1)

        # Issue #64 形式
        issue_match = re.search(r"issue\s*[#]?(\d+)", prompt.lower())
        if issue_match:
            return issue_match.group(1)

        return None

    def _detect_intent(self, prompt_lower: str) -> str:
        """意図検出"""
        if any(word in prompt_lower for word in ["修正", "fix", "bug", "エラー"]):
            return "fix_bug"
        elif any(word in prompt_lower for word in ["追加", "実装", "add", "implement"]):
            return "add_feature"
        elif any(word in prompt_lower for word in ["テスト", "test"]):
            return "add_test"
        elif any(word in prompt_lower for word in ["ドキュメント", "document", "docs"]):
            return "update_docs"
        elif any(word in prompt_lower for word in ["調査", "investigate", "analyze"]):
            return "investigate"
        else:
            return "general"

    def _estimate_priority(self, prompt_lower: str) -> MessagePriority:
        """優先度推定"""
        if any(word in prompt_lower for word in ["緊急", "urgent", "critical"]):
            return MessagePriority.CRITICAL
        elif any(word in prompt_lower for word in ["重要", "important", "高", "high"]):
            return MessagePriority.HIGH
        elif any(word in prompt_lower for word in ["普通", "medium", "中"]):
            return MessagePriority.MEDIUM
        else:
            return MessagePriority.LOW

    def _estimate_complexity(self, prompt_lower: str) -> str:
        """複雑度推定"""
        complexity_indicators = {
            "high": [
                "複雑",
                "difficult",
                "多数",
                "multiple",
                "システム",
                "アーキテクチャ",
            ],
            "medium": ["機能", "feature", "変更", "change", "更新", "update"],
            "low": ["簡単", "simple", "小さな", "minor", "typo", "誤字"],
        }

        for complexity, indicators in complexity_indicators.items():
            if any(word in prompt_lower for word in indicators):
                return complexity

        return "medium"  # デフォルト
