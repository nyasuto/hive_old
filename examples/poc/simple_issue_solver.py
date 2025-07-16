#!/usr/bin/env python3
"""
Simple Issue Solver Agent

新しいフレームワークを使用したシンプルなIssue解決エージェントです。
従来の1000行超のコードが50行程度に簡素化されています。

Usage:
    python examples/poc/simple_issue_solver.py "Issue 84を解決する"
    python examples/poc/simple_issue_solver.py "Issue 64について調査してください"
    python examples/poc/simple_issue_solver.py "Issue 75の内容を説明してください"
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hive.agents.issue_solver import IssueSolverAgent


async def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="Simple Issue Solver Agent")
    parser.add_argument("prompt", nargs="?", help="User prompt for issue resolution")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive mode"
    )

    args = parser.parse_args()

    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # エージェント作成
    agent = IssueSolverAgent()

    if args.demo:
        await run_demo(agent)
    elif args.interactive:
        await run_interactive(agent)
    elif args.prompt:
        await process_single_request(agent, args.prompt)
    else:
        print("Usage: python simple_issue_solver.py <prompt>")
        print("       python simple_issue_solver.py --demo")
        print("       python simple_issue_solver.py --interactive")


async def process_single_request(agent: IssueSolverAgent, prompt: str):
    """単一リクエスト処理"""
    print(f"🐝 Processing: {prompt}")

    try:
        result = await agent.process(prompt)

        if result["success"]:
            print(f"✅ {result['message']}")
            if result["mode"] == "solve":
                print(
                    f"📝 Resolution completed in {result['resolution_result'].get('total_time', 0):.1f}s"
                )
            elif result["mode"] == "investigate":
                print(
                    f"🔍 Issue type: {result['investigation_result']['issue_summary']['type']}"
                )
                print(
                    f"⚡ Complexity: {result['investigation_result']['issue_summary']['complexity']}"
                )
            elif result["mode"] == "explain":
                print(f"💬 Explanation:\n{result['explanation']}")
        else:
            print(f"❌ {result['message']}: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def run_demo(agent: IssueSolverAgent):
    """デモモード実行"""
    demo_prompts = [
        "Issue 84を解決する",
        "Issue 64について調査してください",
        "Issue 75の内容を説明してください",
        "緊急でissue 84を直してほしい",
        "バグ修正をお願いします issue 64",
    ]

    print("🧪 Issue Solver Agent Demo")
    print("=" * 50)

    for i, prompt in enumerate(demo_prompts, 1):
        print(f"\n🎯 Demo {i}/{len(demo_prompts)}: {prompt}")
        print("-" * 30)

        await process_single_request(agent, prompt)

        if i < len(demo_prompts):
            print("\n⏳ Waiting 3 seconds...")
            await asyncio.sleep(3)

    print("\n🎉 Demo completed!")


async def run_interactive(agent: IssueSolverAgent):
    """インタラクティブモード"""
    print("🐝 Issue Solver Agent - Interactive Mode")
    print("Type 'quit' to exit")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n🐝 > ")

            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break

            if not user_input.strip():
                continue

            await process_single_request(agent, user_input)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
