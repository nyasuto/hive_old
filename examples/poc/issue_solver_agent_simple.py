#!/usr/bin/env python3
"""
新アーキテクチャ Issue解決エージェント（簡易版）

新プロトコルシステムを使用したIssue解決エージェントのシンプル実装
"""

import argparse
import asyncio
import re
from datetime import datetime
from typing import Any

from protocols import MessageProtocol, ProtocolValidator
from protocols.message_protocol import MessagePriority, MessageType


class SimpleUserPromptParser:
    """シンプルなユーザープロンプト解析器"""

    def parse_user_prompt(self, prompt: str) -> dict[str, Any]:
        """ユーザープロンプトを解析"""
        prompt_lower = prompt.lower()

        # Issue番号抽出
        issue_match = re.search(r"issue\s*[#]?(\d+)", prompt_lower)
        issue_number = issue_match.group(1) if issue_match else None

        # 意図認識
        intent = self._detect_intent(prompt_lower)

        # 優先度推定
        priority = self._estimate_priority(prompt_lower)

        return {
            "original_prompt": prompt,
            "issue_number": issue_number,
            "intent": intent,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
        }

    def _detect_intent(self, prompt_lower: str) -> str:
        """意図認識"""
        if any(word in prompt_lower for word in ["解決", "修正", "fix", "solve"]):
            return "solve"
        elif any(word in prompt_lower for word in ["調査", "確認", "investigate"]):
            return "investigate"
        elif any(word in prompt_lower for word in ["説明", "理解", "explain"]):
            return "explain"
        else:
            return "solve"  # デフォルト

    def _estimate_priority(self, prompt_lower: str) -> str:
        """優先度推定"""
        if any(word in prompt_lower for word in ["緊急", "急いで", "urgent"]):
            return "high"
        elif any(word in prompt_lower for word in ["後で", "later", "余裕"]):
            return "low"
        else:
            return "medium"


class SimpleIssueSolverAgent:
    """シンプルなIssue解決エージェント"""

    def __init__(self):
        self.protocol = MessageProtocol()
        self.validator = ProtocolValidator()
        self.parser = SimpleUserPromptParser()

    async def process_user_request(self, user_prompt: str) -> dict[str, Any]:
        """ユーザー要求を処理"""
        print(f"🐝 BeeKeeper: {user_prompt}")

        # 1. プロンプト解析
        parsed = self.parser.parse_user_prompt(user_prompt)
        print(f"📋 解析結果: {parsed}")

        # 2. Queen協調メッセージ作成
        queen_message = self.protocol.create_message(
            message_type=MessageType.REQUEST,
            sender_id="beekeeper",
            receiver_id="queen",
            content={"user_request": parsed, "action": "coordinate_issue_resolution"},
            priority=MessagePriority.HIGH
            if parsed["priority"] == "high"
            else MessagePriority.MEDIUM,
        )

        # 3. メッセージ検証
        validation_result = self.validator.validate_message(queen_message)
        if not validation_result.valid:
            return {
                "status": "error",
                "error": "メッセージ検証失敗",
                "details": validation_result.errors,
            }

        # 4. Queen協調（模擬）
        queen_response = await self._simulate_queen_coordination(parsed)

        # 5. 結果返却
        return {
            "status": "success",
            "user_request": parsed,
            "queen_response": queen_response,
            "timestamp": datetime.now().isoformat(),
        }

    async def _simulate_queen_coordination(
        self, parsed_request: dict[str, Any]
    ) -> dict[str, Any]:
        """Queen協調の模擬"""
        print("👑 Queen: 承知しました。分析中...")

        await asyncio.sleep(1)  # 処理時間模擬

        # Issue分析（模擬）
        issue_analysis = {
            "issue_number": parsed_request["issue_number"],
            "intent": parsed_request["intent"],
            "priority": parsed_request["priority"],
            "complexity": "medium",
            "estimated_time": "30分",
        }

        print(
            f"👑 Queen: 分析完了 - 複雑度: {issue_analysis['complexity']}, 優先度: {issue_analysis['priority']}"
        )

        # Worker割り当て（模擬）
        if parsed_request["intent"] == "solve":
            workers = ["developer", "tester"]
            action = "問題解決を実行"
        elif parsed_request["intent"] == "investigate":
            workers = ["analyzer"]
            action = "詳細調査を実行"
        else:
            workers = ["documenter"]
            action = "説明資料を作成"

        print(f"👑 Queen: {len(workers)}つのWorkerで{action}します")

        # Worker実行（模擬）
        worker_results = await self._simulate_worker_execution(workers, issue_analysis)

        # 結果統合
        print("👑 Queen: 全Worker完了。結果を統合中...")
        await asyncio.sleep(1)

        final_result = {
            "action_taken": action,
            "workers_used": workers,
            "worker_results": worker_results,
            "status": "completed",
            "deliverables": self._generate_deliverables(parsed_request["intent"]),
        }

        print(f"👑 Queen: {action}完了！")
        return final_result

    async def _simulate_worker_execution(
        self, workers: list, issue_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Worker実行の模擬"""
        results = {}

        for worker in workers:
            print(f"🏗️ {worker.capitalize()} Worker: 作業開始")
            await asyncio.sleep(0.5)  # 作業時間模擬

            if worker == "developer":
                results[worker] = {
                    "task": "実装・修正",
                    "status": "完了",
                    "output": "コード修正完了、テスト追加",
                }
            elif worker == "tester":
                results[worker] = {
                    "task": "テスト・品質チェック",
                    "status": "完了",
                    "output": "テスト通過、品質基準クリア",
                }
            elif worker == "analyzer":
                results[worker] = {
                    "task": "分析・調査",
                    "status": "完了",
                    "output": "根本原因特定、改善提案作成",
                }
            else:
                results[worker] = {
                    "task": "ドキュメント作成",
                    "status": "完了",
                    "output": "説明資料・手順書作成",
                }

            print(f"✅ {worker.capitalize()} Worker: {results[worker]['output']}")

        return results

    def _generate_deliverables(self, intent: str) -> list:
        """成果物生成"""
        if intent == "solve":
            return [
                "修正されたコード",
                "テストケース",
                "品質チェック結果",
                "プルリクエスト（模擬）",
            ]
        elif intent == "investigate":
            return ["調査レポート", "根本原因分析", "改善提案", "次のステップ"]
        else:
            return ["説明資料", "理解しやすいドキュメント", "実装手順", "参考資料"]


async def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="新アーキテクチャ Issue解決エージェント"
    )
    parser.add_argument("prompt", nargs="?", help="自然言語による指示")
    parser.add_argument("--demo", action="store_true", help="デモモード")

    args = parser.parse_args()

    agent = SimpleIssueSolverAgent()

    if args.demo:
        # デモモード
        demo_prompts = [
            "Issue 64を解決する",
            "緊急でissue 75を直してほしい",
            "Issue 101について調査してください",
            "Issue 95の説明をお願いします",
        ]

        print("🎪 デモモード開始")
        for i, prompt in enumerate(demo_prompts, 1):
            print(f"\n--- デモ {i}/{len(demo_prompts)} ---")
            result = await agent.process_user_request(prompt)
            print(f"📊 結果: {result['status']}")
            if i < len(demo_prompts):
                print("⏳ 次のデモまで待機中...")
                await asyncio.sleep(2)

        print("\n🎉 デモ完了！")

    elif args.prompt:
        # 指定プロンプト実行
        result = await agent.process_user_request(args.prompt)
        print(f"\n📊 最終結果: {result}")

    else:
        # インタラクティブモード
        print("🐝 Hive Issue解決エージェント（新アーキテクチャ）")
        print("自然言語で指示してください（例: 'Issue 64を解決する'）")
        print("終了するには 'quit' を入力してください")

        while True:
            try:
                user_input = input("\n🐝 BeeKeeper> ").strip()
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("👋 さようなら！")
                    break

                if user_input:
                    result = await agent.process_user_request(user_input)
                    print(f"\n📊 結果: {result['status']}")

                    if result["status"] == "success":
                        deliverables = result["queen_response"]["deliverables"]
                        print(f"🎁 成果物: {', '.join(deliverables)}")

            except KeyboardInterrupt:
                print("\n👋 中断されました。さようなら！")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
