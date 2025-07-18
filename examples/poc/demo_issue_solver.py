"""
Issue Solver Agent デモスクリプト

様々な自然言語プロンプトでIssue解決エージェントの動作を確認する。

Usage:
    python examples/poc/demo_issue_solver.py
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from examples.poc.issue_solver_agent import DistributedBeeKeeperAgent


async def run_demo_scenarios():
    """デモシナリオ実行"""

    # デモプロンプト集
    demo_prompts = [
        "Issue 64を解決する",
        "バグ修正をお願いします issue 84",
        "Issue 75について調査してください",
        "https://github.com/nyasuto/hive/issues/84 を修正して",
        "緊急でissue 64を直してほしい",
        "Issue 84の内容を説明してください",
        "テストに関する問題 issue 84を見てください",
        "Issue 64のドキュメントを更新してください",
        "後で時間があるときに issue 75を確認して",
        "Issue 84について詳しく教えて",
    ]

    beekeeper = DistributedBeeKeeperAgent()

    print("🎯 Issue Solver Agent デモ開始")
    print("=" * 60)

    for i, prompt in enumerate(demo_prompts, 1):
        print(f'\n🔍 デモ {i}/{len(demo_prompts)}: "{prompt}"')
        print("-" * 40)

        try:
            # プロンプト解析のみ実行（実際の解決は時間がかかるため）
            parsed = beekeeper.parser.parse_user_prompt(prompt)

            print("📋 解析結果:")
            print(f"   Intent: {parsed['intent']}")
            print(f"   Priority: {parsed['priority']}")
            print(f"   Issue Number: {parsed['issue_number']}")
            print(f"   Complexity: {parsed['complexity']}")

            # 短い実行サンプル（調査モードのみ）
            if parsed["intent"] == "investigate" and parsed["issue_number"]:
                print("🔍 調査モード実行中...")
                result = await beekeeper.process_user_request(prompt)
                if result["status"] == "success":
                    print("✅ 調査完了")
                else:
                    print(f"❌ 調査失敗: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ エラー: {e}")

        print()

    print("🎉 デモ完了")


async def interactive_demo():
    """インタラクティブデモ"""
    beekeeper = DistributedBeeKeeperAgent()

    print("🐝 Issue Solver Agent インタラクティブデモ")
    print("終了するには 'quit' または 'exit' を入力してください")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n🐝 BeeKeeper: どのようなご依頼でしょうか？ > ")

            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 デモを終了します")
                break

            if not user_input.strip():
                continue

            # プロンプト解析表示
            parsed = beekeeper.parser.parse_user_prompt(user_input)
            print(
                f"🔍 解析結果: intent={parsed['intent']}, priority={parsed['priority']}, issue={parsed['issue_number']}"
            )

            # 軽量実行
            if parsed["issue_number"]:
                if parsed["intent"] == "explain":
                    result = await beekeeper.process_user_request(user_input)
                elif parsed["intent"] == "investigate":
                    result = await beekeeper.process_user_request(user_input)
                else:
                    print("🔧 実際の解決はデモでは省略されます（時間がかかるため）")
                    print("   実際の解決には issue_solver_agent.py を使用してください")
                    continue

                if result["status"] == "success":
                    print("✅ 処理完了")
                else:
                    print(f"❌ 処理失敗: {result.get('error', 'Unknown error')}")
            else:
                print("❌ Issue番号が特定できませんでした")
                print("💡 「Issue 64を解決する」のような形式でお試しください")

        except KeyboardInterrupt:
            print("\n👋 デモを終了します")
            break
        except Exception as e:
            print(f"❌ エラー: {e}")


async def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Issue Solver Agent Demo")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run interactive demo"
    )

    args = parser.parse_args()

    if args.interactive:
        await interactive_demo()
    else:
        await run_demo_scenarios()


if __name__ == "__main__":
    asyncio.run(main())
