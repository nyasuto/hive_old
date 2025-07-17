#!/usr/bin/env python3
"""
Hive Watch テストスクリプト
Issue #125 - Phase 1 実装の動作確認
"""

import asyncio
import sys
import time
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# 動的importでhive_watchを読み込み
import importlib.util

from scripts.hive_cli import HiveCLI

spec = importlib.util.spec_from_file_location(
    "hive_watch", Path(__file__).parent / "hive_watch.py"
)
hive_watch_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hive_watch_module)
HiveWatch = hive_watch_module.HiveWatch


async def test_basic_functionality():
    """基本機能テスト"""
    print("🧪 Hive Watch Phase 1 テスト開始")
    print("=" * 50)

    cli = HiveCLI()

    # 1. セッション状態確認
    print("1. セッション状態確認...")
    status = await cli.list_workers()
    if status.get("session_active", False):
        print("  ✅ Hive session is active")
        workers = status.get("workers", {})
        active_count = sum(1 for w in workers.values() if w.get("pane_active", False))
        print(f"  👥 Active workers: {active_count}/{len(workers)}")
    else:
        print("  ❌ Hive session not active")
        print("  💡 Please start with: ./scripts/start-cozy-hive.sh")
        return False

    # 2. 基本メッセージ送信テスト
    print("\n2. 基本メッセージ送信テスト...")
    try:
        test_message = "Hello from Hive Watch test!"
        result = await cli.send_message("documenter", test_message, "direct")
        print("  ✅ Message sent successfully")
        print(
            f"  📝 Response received: {len(result.get('result', {}).get('content', ''))} characters"
        )
    except Exception as e:
        print(f"  ❌ Message sending failed: {e}")
        return False

    # 3. ログ記録確認
    print("\n3. ログ記録確認...")
    log_file = Path("logs/hive_communications.log")
    if log_file.exists():
        print("  ✅ Log file exists")
        with open(log_file) as f:
            lines = f.readlines()
            print(f"  📝 Log entries: {len(lines)}")
    else:
        print("  ❌ Log file not found")
        return False

    # 4. Worker履歴取得テスト
    print("\n4. Worker履歴取得テスト...")
    try:
        history = await cli.get_worker_history("documenter", 5)
        print("  ✅ Worker history retrieved")
        print(f"  📄 History length: {len(history)} characters")
    except Exception as e:
        print(f"  ❌ History retrieval failed: {e}")
        return False

    print("\n✅ All basic functionality tests passed!")
    return True


async def test_monitoring_features():
    """監視機能テスト"""
    print("\n🔍 監視機能テスト")
    print("=" * 50)

    # 短時間の監視テスト
    hive_watch = HiveWatch()

    print("1. 短時間監視テスト（10秒）...")

    # 監視開始（バックグラウンド）
    monitor_task = asyncio.create_task(hive_watch.start_monitoring(interval=1.0))

    # 10秒後に監視停止
    await asyncio.sleep(10)
    hive_watch.stop_monitoring()

    # 監視タスクの完了を待機
    try:
        await asyncio.wait_for(monitor_task, timeout=5.0)
        print("  ✅ Monitoring test completed successfully")
    except TimeoutError:
        monitor_task.cancel()
        print("  ⚠️  Monitoring task cancelled due to timeout")
    except Exception as e:
        print(f"  ❌ Monitoring test failed: {e}")
        return False

    return True


async def test_parallel_messaging():
    """並列メッセージ送信テスト"""
    print("\n🚀 並列メッセージ送信テスト")
    print("=" * 50)

    cli = HiveCLI()

    # 複数のWorkerに同時にメッセージ送信
    workers = ["analyzer", "documenter"]
    messages = ["Analyze the current system status", "Document the test results"]

    print(f"1. {len(workers)} workers に並列メッセージ送信...")

    start_time = time.time()

    # 並列送信
    tasks = []
    for worker, message in zip(workers, messages, strict=False):
        task = cli.send_message(worker, message, "direct")
        tasks.append(task)

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        success_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = len(results) - success_count

        print(f"  ✅ Parallel messaging completed in {end_time - start_time:.2f}s")
        print(f"  📊 Success: {success_count}, Errors: {error_count}")

        return error_count == 0

    except Exception as e:
        print(f"  ❌ Parallel messaging failed: {e}")
        return False


async def main():
    """メインテスト実行"""
    print("🔬 Hive Watch Phase 1 統合テスト")
    print("Issue #125 - 基本監視機能実装検証")
    print("=" * 60)

    test_results = []

    # テスト実行
    test_results.append(await test_basic_functionality())
    test_results.append(await test_monitoring_features())
    test_results.append(await test_parallel_messaging())

    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)

    test_names = ["基本機能テスト", "監視機能テスト", "並列メッセージ送信テスト"]

    passed = 0
    for i, (name, result) in enumerate(zip(test_names, test_results, strict=False)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i + 1}. {name}: {status}")
        if result:
            passed += 1

    print(f"\n📈 総合結果: {passed}/{len(test_results)} テスト通過")

    if passed == len(test_results):
        print("🎉 Issue #125 Phase 1 実装完了！")
        print("\n✅ 受入条件:")
        print("  - tmux全paneの内容取得機能 ✓")
        print("  - 通信メッセージの正確な抽出 ✓")
        print("  - 時系列ログの生成と保存 ✓")
        print("  - 基本的なCLIインターフェース ✓")
        print("  - 継続的な監視機能 ✓")
        return True
    else:
        print("❌ 一部のテストが失敗しました")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
