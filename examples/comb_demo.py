#!/usr/bin/env python3
"""
Hive Comb通信システム デモンストレーション

Queen ↔ Developer Worker の基本的な通信パターンを実演
"""

import time
from datetime import datetime
from typing import Any

from comb import MessagePriority, MessageType, create_worker_api


def queen_worker_demo() -> None:
    """Queen ↔ Developer Worker の通信デモ"""
    print("🐝 Hive Comb通信システム デモンストレーション")
    print("=" * 50)

    # Worker API作成
    queen = create_worker_api("queen")
    developer = create_worker_api("developer_worker")

    print(f"✅ Queen API作成: {queen.worker_id}")
    print(f"✅ Developer Worker API作成: {developer.worker_id}")
    print()

    # 1. Ping/Pong通信テスト
    print("📍 1. Ping/Pong通信テスト")
    print("-" * 30)

    # Ping送信
    print("Queen → Developer: Ping送信")
    ping_result = queen.ping("developer_worker")
    print(f"   送信結果: {'成功' if ping_result else '失敗'}")

    # Ping受信
    messages = developer.receive_messages()
    if messages:
        ping_msg = messages[0]
        print(f"Developer ← Queen: Ping受信 (ID: {ping_msg.id})")
        print(f"   内容: {ping_msg.content}")

        # Pong送信
        print("Developer → Queen: Pong送信")
        pong_result = developer.pong(ping_msg)
        print(f"   送信結果: {'成功' if pong_result else '失敗'}")

    # Pong受信
    responses = queen.receive_messages()
    if responses:
        pong_msg = responses[0]
        print(f"Queen ← Developer: Pong受信 (ID: {pong_msg.id})")
        print(f"   内容: {pong_msg.content}")

    print()

    # 2. タスク割り当て（Nectar）デモ
    print("📍 2. タスク割り当て（Nectar）デモ")
    print("-" * 35)

    # タスク送信
    print("Queen: タスク作成・送信")
    nectar_result = queen.send_nectar(
        nectar_type="feature_implementation",
        content={
            "title": "ユーザーログイン機能実装",
            "description": "認証システムとバリデーション機能を実装",
            "priority": "high",
            "estimated_hours": 8,
            "requirements": [
                "パスワードハッシュ化",
                "セッション管理",
                "入力バリデーション",
            ],
        },
        priority="high",
    )
    print(f"   送信結果: {'成功' if nectar_result else '失敗'}")

    # タスク受信
    print("Developer: タスク受信・開始")
    nectar = developer.receive_nectar()
    if nectar:
        print(f"   タスクID: {nectar['id']}")
        print(f"   タイプ: {nectar['type']}")
        print(f"   タイトル: {nectar['content']['title']}")
        print(f"   ステータス: {nectar['status']}")

        # 作業シミュレーション
        print("Developer: 作業中... (2秒待機)")
        time.sleep(2)

        # タスク完了
        print("Developer: タスク完了・結果送信")
        completion_result = developer.complete_nectar(
            nectar["id"],
            result={
                "status": "completed",
                "files_created": [
                    "auth/login.py",
                    "auth/session.py",
                    "validators/user_input.py",
                ],
                "tests_written": True,
                "test_coverage": "95%",
                "notes": "全要件を満たして実装完了。パフォーマンステストも実施済み。",
            },
        )
        print(f"   完了処理結果: {'成功' if completion_result else '失敗'}")

    print()

    # 3. リソース同期（ロック）デモ
    print("📍 3. リソース同期（ロック）デモ")
    print("-" * 32)

    resource_name = "shared_config_file"

    # Queenがリソースロック取得
    print(f"Queen: リソース '{resource_name}' のロック取得試行")
    queen_lock = queen.acquire_lock(resource_name, timeout=2.0)
    print(f"   結果: {'成功' if queen_lock else '失敗'}")

    # Developerがロック取得試行（失敗するはず）
    print("Developer: 同じリソースのロック取得試行")
    developer_lock = developer.acquire_lock(resource_name, timeout=1.0)
    print(f"   結果: {'失敗（期待通り）' if not developer_lock else '予期しない成功'}")

    # Queenがロック解放
    print("Queen: リソースロック解放")
    queen_release = queen.release_lock(resource_name)
    print(f"   結果: {'成功' if queen_release else '失敗'}")

    # Developerがロック取得（成功するはず）
    print("Developer: リソースロック取得再試行")
    developer_lock_retry = developer.acquire_lock(resource_name, timeout=1.0)
    print(f"   結果: {'成功' if developer_lock_retry else '失敗'}")

    if developer_lock_retry:
        print("Developer: リソースロック解放")
        developer_release = developer.release_lock(resource_name)
        print(f"   結果: {'成功' if developer_release else '失敗'}")

    print()

    # 4. 通信統計表示
    print("📍 4. 通信統計")
    print("-" * 15)

    queen_status = queen.get_status()
    developer_status = developer.get_status()

    print("Queen統計:")
    print(f"   メッセージ送信済み: {queen_status['messages'].get('sent', 0)}")
    print(f"   アクティブロック: {queen_status['locks']['active_locks']}")

    print("Developer統計:")
    print(f"   メッセージ送信済み: {developer_status['messages'].get('sent', 0)}")
    print(f"   アクティブロック: {developer_status['locks']['active_locks']}")

    print()
    print("🎉 デモンストレーション完了！")
    print("✨ Hive Combシステムが正常に動作しています")


def message_handler_demo() -> None:
    """自動メッセージハンドラーのデモ"""
    print("🤖 自動メッセージハンドラー デモ")
    print("=" * 35)

    # Worker作成
    worker = create_worker_api("auto_worker")
    client = create_worker_api("client")

    # メッセージカウンター
    processed_count = 0

    def handle_request(message: Any) -> None:
        """リクエストハンドラー"""
        nonlocal processed_count
        processed_count += 1

        print(f"📨 リクエスト受信 #{processed_count}")
        print(f"   送信者: {message.from_worker}")
        print(f"   内容: {message.content}")

        # 自動応答
        if message.content.get("action") == "ping":
            worker.pong(message)
            print("   → Pong応答送信")
        else:
            worker.send_response(
                message,
                {"status": "processed", "timestamp": datetime.now().isoformat()},
            )
            print("   → 処理完了応答送信")

    # ハンドラー登録
    worker.register_handler(MessageType.REQUEST, handle_request)

    # 自動ポーリング開始
    print("🔄 自動メッセージポーリング開始...")
    worker.start_polling(0.5)

    # テストメッセージ送信
    print("\n📤 テストメッセージ送信:")

    # Ping送信
    client.ping("auto_worker")
    print("1. Ping送信")

    time.sleep(1)

    # 通常メッセージ送信
    client.send_message(
        "auto_worker",
        {"action": "process_data", "data": [1, 2, 3, 4, 5]},
        MessageType.REQUEST,
    )
    print("2. データ処理リクエスト送信")

    time.sleep(1)

    # 緊急メッセージ送信
    client.send_message(
        "auto_worker",
        {"action": "urgent_task", "priority": "critical"},
        MessageType.REQUEST,
        priority=MessagePriority.URGENT,
    )
    print("3. 緊急タスク送信")

    # 応答待機
    print("\n⏱️  応答待機中...")
    time.sleep(2)

    # 応答確認
    responses = client.receive_messages()
    print(f"\n📬 受信応答数: {len(responses)}")

    for i, response in enumerate(responses, 1):
        print(f"応答 {i}:")
        if response.message_type == MessageType.RESPONSE:
            content = response.content.get("response", response.content)
            print("   タイプ: レスポンス")
            print(f"   内容: {content}")

    # ポーリング停止
    worker.stop_polling()
    print("\n✅ 自動メッセージハンドラー デモ完了")


if __name__ == "__main__":
    print("🐝 Welcome to Hive Comb Communication System Demo!")
    print()

    # 基本通信デモ
    queen_worker_demo()

    print("\n" + "=" * 60 + "\n")

    # 自動ハンドラーデモ
    message_handler_demo()

    print(f"\n⏰ デモ実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🙏 Hive Combシステムをご利用いただき、ありがとうございました！")
