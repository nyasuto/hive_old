#!/usr/bin/env python3
"""
New Protocol System Test

新プロトコルシステムの動作確認用テストスクリプト
分散環境起動後の動作確認に使用
"""

import asyncio
import sys
import traceback

from protocols import MessageProtocol, ProtocolValidator, default_integration
from protocols.message_protocol import MessageType


async def test_new_protocol() -> bool:
    """新プロトコルシステムの基本動作テスト"""
    print("🚀 新プロトコルシステムテスト開始")

    try:
        # 1. プロトコル初期化
        print("\n1. プロトコル初期化...")
        protocol = MessageProtocol()
        validator = ProtocolValidator()
        print("✅ プロトコル初期化完了")

        # 2. 基本メッセージ作成テスト
        print("\n2. 基本メッセージ作成...")
        basic_msg = protocol.create_message(
            message_type=MessageType.REQUEST,
            sender_id="test-sender",
            receiver_id="test-receiver",
            content={"action": "test", "data": "basic_message"},
        )
        print(f"✅ 基本メッセージ作成完了: {basic_msg.header.message_id}")

        # 3. バリデーション
        print("\n3. メッセージバリデーション...")
        result = validator.validate_message(basic_msg)
        print(f"✅ バリデーション結果: {result.valid}")
        if not result.valid:
            for error in result.errors:
                print(f"❌ エラー: {error}")

        # 4. タスク割り当てメッセージ作成
        print("\n4. タスク割り当てメッセージ作成...")
        task_msg = protocol.create_task_assignment(
            sender_id="queen-coordinator",
            receiver_id="worker-test",
            task_id="protocol-test-001",
            task_type="validation_test",
            task_data={"test": "new_protocol", "priority": "high"},
        )
        print(f"✅ タスクメッセージ作成完了: {task_msg.header.message_id}")

        # 5. タスクメッセージバリデーション
        print("\n5. タスクメッセージバリデーション...")
        task_result = validator.validate_message(task_msg)
        print(f"✅ タスクバリデーション結果: {task_result.valid}")
        if not task_result.valid:
            for error in task_result.errors:
                print(f"❌ エラー: {error}")

        # 6. 統合レイヤーテスト
        print("\n6. 統合レイヤーテスト...")
        integration_success = default_integration.send_protocol_message(task_msg)
        print(f"✅ 統合レイヤー送信結果: {integration_success}")

        # 7. プロトコル情報表示
        print("\n7. プロトコル情報...")
        protocol_info = protocol.get_protocol_info()
        print(f"✅ プロトコルバージョン: {protocol_info['current_version']}")
        print(f"✅ サポートバージョン: {protocol_info['supported_versions']}")
        print(
            f"✅ サポートメッセージタイプ: {protocol_info['supported_message_types']}"
        )

        # 8. 統合統計情報
        print("\n8. 統合統計情報...")
        stats = default_integration.get_integration_stats()
        print(f"✅ 統合統計: {stats}")

        # 9. システムアラートメッセージテスト
        print("\n9. システムアラートメッセージテスト...")
        alert_msg = protocol.create_system_alert(
            sender_id="system",
            alert_type="test_alert",
            alert_message="プロトコルテスト実行中",
            alert_data={"test": True, "timestamp": "2024-01-01T00:00:00Z"},
        )
        alert_result = validator.validate_message(alert_msg)
        print(f"✅ アラートメッセージバリデーション: {alert_result.valid}")

        # 10. ハートビートメッセージテスト
        print("\n10. ハートビートメッセージテスト...")
        heartbeat_msg = protocol.create_heartbeat(
            agent_id="test-agent", status={"cpu": 50, "memory": 60, "status": "healthy"}
        )
        heartbeat_result = validator.validate_message(heartbeat_msg)
        print(f"✅ ハートビートメッセージバリデーション: {heartbeat_result.valid}")

        # 最終結果
        overall_success = (
            result.valid
            and task_result.valid
            and integration_success
            and alert_result.valid
            and heartbeat_result.valid
        )

        print(f"\n🎉 全体テスト結果: {'✅ 成功' if overall_success else '❌ 失敗'}")
        return overall_success

    except Exception as e:
        print(f"❌ テスト中にエラーが発生: {e}")
        traceback.print_exc()
        return False


async def test_message_types() -> bool:
    """様々なメッセージタイプのテスト"""
    print("\n🔍 メッセージタイプテスト開始")

    try:
        protocol = MessageProtocol()
        validator = ProtocolValidator()

        # テストメッセージ一覧
        test_messages = []

        # 1. REQUEST
        request_msg = protocol.create_message(
            message_type=MessageType.REQUEST,
            sender_id="client",
            receiver_id="server",
            content={"action": "get_data", "params": {"id": 123}},
        )
        test_messages.append(("REQUEST", request_msg))

        # 2. RESPONSE
        response_msg = protocol.create_response(
            original_message=request_msg,
            response_content={"data": "response_data", "status": "ok"},
        )
        test_messages.append(("RESPONSE", response_msg))

        # 3. TASK_ASSIGNMENT
        task_msg = protocol.create_task_assignment(
            sender_id="queen",
            receiver_id="worker-1",
            task_id="task-abc-123",
            task_type="code_analysis",
            task_data={"file": "test.py", "analysis_type": "complexity"},
        )
        test_messages.append(("TASK_ASSIGNMENT", task_msg))

        # 4. TASK_COMPLETION
        completion_msg = protocol.create_task_completion(
            sender_id="worker-1",
            receiver_id="queen",
            task_id="task-abc-123",
            result={"complexity": 5, "lines": 100},
            success=True,
        )
        test_messages.append(("TASK_COMPLETION", completion_msg))

        # 5. AGENT_HEARTBEAT
        heartbeat_msg = protocol.create_heartbeat(
            agent_id="worker-1", status={"cpu": 75, "memory": 80, "tasks": 3}
        )
        test_messages.append(("AGENT_HEARTBEAT", heartbeat_msg))

        # 6. SYSTEM_ALERT
        alert_msg = protocol.create_system_alert(
            sender_id="monitor",
            alert_type="performance_warning",
            alert_message="CPU使用率が高くなっています",
            alert_data={"cpu": 95, "threshold": 90},
        )
        test_messages.append(("SYSTEM_ALERT", alert_msg))

        # 各メッセージタイプのテスト
        all_valid = True
        for msg_type, message in test_messages:
            result = validator.validate_message(message)
            status = "✅" if result.valid else "❌"
            print(f"{status} {msg_type}: {result.valid}")
            if not result.valid:
                for error in result.errors:
                    print(f"   - {error}")
                all_valid = False

        print(
            f"\n🎯 メッセージタイプテスト結果: {'✅ 全て成功' if all_valid else '❌ 一部失敗'}"
        )
        return all_valid

    except Exception as e:
        print(f"❌ メッセージタイプテスト中にエラー: {e}")
        traceback.print_exc()
        return False


async def test_protocol_integration() -> bool:
    """プロトコル統合機能のテスト"""
    print("\n🔧 プロトコル統合テスト開始")

    try:
        # 統合検証
        validation_result = default_integration.validate_integration()
        print(f"✅ 統合検証結果: {validation_result.valid}")

        if not validation_result.valid:
            for error in validation_result.errors:
                print(f"❌ 統合エラー: {error}")
            return False

        # 統合統計
        stats = default_integration.get_integration_stats()
        print("✅ 統合統計取得完了")

        # 統計情報表示
        if "protocol_info" in stats:
            protocol_info = stats["protocol_info"]
            print(
                f"   - プロトコルバージョン: {protocol_info.get('current_version', 'N/A')}"
            )

        if "validator_stats" in stats:
            validator_stats = stats["validator_stats"]
            print(f"   - バリデーター統計: {validator_stats}")

        return True

    except Exception as e:
        print(f"❌ 統合テスト中にエラー: {e}")
        traceback.print_exc()
        return False


async def main() -> bool:
    """メインテスト実行"""
    print("=" * 60)
    print("🐝 Hive Protocol System Test Suite")
    print("=" * 60)

    # テスト実行
    test_results = []

    # 1. 基本プロトコルテスト
    basic_result = await test_new_protocol()
    test_results.append(("基本プロトコル", basic_result))

    # 2. メッセージタイプテスト
    message_result = await test_message_types()
    test_results.append(("メッセージタイプ", message_result))

    # 3. 統合テスト
    integration_result = await test_protocol_integration()
    test_results.append(("統合機能", integration_result))

    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)

    all_passed = True
    for test_name, result in test_results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 全テスト成功！新プロトコルシステムは正常に動作しています。")
        print("\n次のステップ:")
        print("1. python examples/poc/demo_issue_solver.py")
        print("2. ./scripts/check-comb.sh")
        print("3. python examples/poc/claude_daemon_demo.py")
    else:
        print("❌ 一部のテストが失敗しました。詳細を確認してください。")

    print("=" * 60)
    return all_passed


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        traceback.print_exc()
        sys.exit(1)
