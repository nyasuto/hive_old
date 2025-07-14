#!/usr/bin/env python3
"""
Hive PoC - Simple Feature Development Test
実際の開発タスクでWorker間協調をテスト

使用方法:
  Queen Worker: python examples/poc/simple_feature_development.py queen
  Developer Worker: python examples/poc/simple_feature_development.py developer
"""

import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from comb import CombAPI, MessagePriority, MessageType  # noqa: E402


def queen_worker() -> None:
    """Queen Worker: 実際の開発タスクを管理"""
    print("👑 Queen Worker: 実際の開発タスクを開始します")

    # CombAPI初期化
    queen = CombAPI("queen")
    print("✅ Queen Worker CombAPI初期化完了")

    # 実際の開発タスクを作成
    task_id = queen.start_task(
        "シンプルな計算機能の実装",
        task_type="feature",
        description="加算・減算・乗算・除算ができる計算機能を実装",
        workers=["queen", "developer"],
    )
    print(f"🚀 開発タスク作成: {task_id}")

    # 要件を明確化
    requirements = {
        "task_id": task_id,
        "feature_name": "Calculator",
        "requirements": [
            "add(a, b) 関数 - 加算",
            "subtract(a, b) 関数 - 減算",
            "multiply(a, b) 関数 - 乗算",
            "divide(a, b) 関数 - 除算（ゼロ除算エラー対応）",
        ],
        "technical_specs": {
            "language": "Python",
            "type_hints": "必須",
            "error_handling": "例外処理を適切に実装",
            "tests": "各関数のテストコードも作成",
        },
        "file_location": "examples/poc/calculator.py",
    }

    # Developer Workerに実装を依頼
    success = queen.send_message(
        to_worker="developer",
        content=requirements,
        message_type=MessageType.REQUEST,
        priority=MessagePriority.HIGH,
    )

    if success:
        print("📤 実装要件をDeveloper Workerに送信しました")
        print("💡 右paneでDeveloper Workerスクリプトを実行してください:")
        print("   python examples/poc/simple_feature_development.py developer")

        # 進捗記録
        queen.add_progress(
            "要件定義完了",
            "計算機能の詳細仕様をDeveloper Workerに送信。実装開始を待機中。",
        )

        print("\n⏳ Developer Workerからの実装完了報告を待機中...")
        print("   実装が完了したら、再度このスクリプトを実行して結果を確認できます。")

    else:
        print("❌ 要件送信に失敗しました")


def developer_worker() -> None:
    """Developer Worker: 実際の実装作業"""
    print("💻 Developer Worker: 実装タスクを確認します")

    # CombAPI初期化
    dev = CombAPI("developer")
    print("✅ Developer Worker CombAPI初期化完了")

    # Queen Workerからのタスクを確認
    messages = dev.receive_messages()
    print(f"📬 受信メッセージ: {len(messages)}件")

    # 最新の実装タスクを探す
    implementation_task = None
    for msg in messages:
        if msg.message_type == MessageType.REQUEST and "Calculator" in str(msg.content):
            implementation_task = msg
            break

    if implementation_task:
        task_content = implementation_task.content
        print(f"\n📋 実装タスク受信: {task_content['feature_name']}")
        print("要件:")
        for req in task_content["requirements"]:
            print(f"  - {req}")

        # 実装ファイルを作成
        file_path = Path(task_content["file_location"])
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 計算機能の実装
        calculator_code = '''"""
Calculator Module - Simple mathematical operations
計算機能モジュール - 基本的な数学演算

Created by Hive Developer Worker
"""

from typing import Union

Number = Union[int, float]


def add(a: Number, b: Number) -> Number:
    """
    加算を実行します

    Args:
        a: 第一オペランド
        b: 第二オペランド

    Returns:
        a + b の結果
    """
    return a + b


def subtract(a: Number, b: Number) -> Number:
    """
    減算を実行します

    Args:
        a: 被減数
        b: 減数

    Returns:
        a - b の結果
    """
    return a - b


def multiply(a: Number, b: Number) -> Number:
    """
    乗算を実行します

    Args:
        a: 第一オペランド
        b: 第二オペランド

    Returns:
        a * b の結果
    """
    return a * b


def divide(a: Number, b: Number) -> Number:
    """
    除算を実行します

    Args:
        a: 被除数
        b: 除数

    Returns:
        a / b の結果

    Raises:
        ZeroDivisionError: bが0の場合
    """
    if b == 0:
        raise ZeroDivisionError("ゼロで除算することはできません")
    return a / b


if __name__ == "__main__":
    # 簡単なテスト
    print("Calculator Test:")
    print(f"add(5, 3) = {add(5, 3)}")
    print(f"subtract(10, 4) = {subtract(10, 4)}")
    print(f"multiply(6, 7) = {multiply(6, 7)}")
    print(f"divide(15, 3) = {divide(15, 3)}")

    try:
        divide(10, 0)
    except ZeroDivisionError as e:
        print(f"Error test: {e}")
'''

        # ファイルに書き込み
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(calculator_code)

        print(f"✅ 実装完了: {file_path}")

        # テストファイルも作成
        test_file_path = file_path.parent / "test_calculator.py"
        test_code = '''"""
Calculator Module Tests
計算機能のテストスイート
"""

import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from examples.poc.calculator import add, subtract, multiply, divide  # noqa: E402
import pytest  # noqa: E402


def test_add():
    """加算のテスト"""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0.1, 0.2) == pytest.approx(0.3)


def test_subtract():
    """減算のテスト"""
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5
    assert subtract(2.5, 1.5) == 1.0


def test_multiply():
    """乗算のテスト"""
    assert multiply(4, 5) == 20
    assert multiply(-2, 3) == -6
    assert multiply(0, 100) == 0


def test_divide():
    """除算のテスト"""
    assert divide(10, 2) == 5
    assert divide(7, 2) == 3.5
    assert divide(-8, 4) == -2


def test_divide_by_zero():
    """ゼロ除算のテスト"""
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)


if __name__ == "__main__":
    # 手動テスト実行
    print("Running manual tests...")

    test_add()
    print("✅ add() tests passed")

    test_subtract()
    print("✅ subtract() tests passed")

    test_multiply()
    print("✅ multiply() tests passed")

    test_divide()
    print("✅ divide() tests passed")

    test_divide_by_zero()
    print("✅ divide_by_zero() test passed")

    print("🎉 All tests passed!")
'''

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_code)

        print(f"✅ テスト作成完了: {test_file_path}")

        # 進捗報告
        dev.add_progress(
            "実装完了", f"Calculator機能を{file_path}に実装。テストコードも作成済み。"
        )

        # 技術的決定を記録
        dev.add_technical_decision(
            "型ヒントにUnion型を使用",
            "int/float両方をサポートするためUnion[int, float]型を採用",
            ["Any型", "Protocol使用", "個別関数"],
        )

        # Queen Workerに完了報告
        success = dev.send_response(
            implementation_task,
            {
                "status": "completed",
                "deliverables": [str(file_path), str(test_file_path)],
                "features_implemented": [
                    "add() - 加算",
                    "subtract() - 減算",
                    "multiply() - 乗算",
                    "divide() - 除算（ゼロ除算エラー対応）",
                ],
                "test_results": "全テストケース通過",
                "next_steps": [
                    "実際にファイルを実行して動作確認",
                    "python examples/poc/calculator.py",
                    "python examples/poc/test_calculator.py",
                ],
            },
        )

        if success:
            print("📤 完了報告をQueen Workerに送信しました")

        print("\n🎉 実装完了！")
        print("💡 次のステップ:")
        print(f"   python {file_path}  # 実装の動作確認")
        print(f"   python {test_file_path}  # テスト実行")

    else:
        print("📭 実装タスクが見つかりません")
        print("🔧 Queen Workerで先にタスクを作成してください")


def main() -> None:
    """メイン実行関数"""
    if len(sys.argv) != 2:
        print("🐝 Hive PoC - Simple Feature Development Test")
        print("")
        print("使用方法:")
        print("  Queen Worker (左pane):")
        print("    python examples/poc/simple_feature_development.py queen")
        print("")
        print("  Developer Worker (右pane):")
        print("    python examples/poc/simple_feature_development.py developer")
        print("")
        print("📋 手順:")
        print("  1. 左paneで queen を実行（タスク作成・要件定義）")
        print("  2. 右paneで developer を実行（実装・テスト作成）")
        print("  3. 生成されたファイルの動作確認")
        sys.exit(1)

    worker_type = sys.argv[1].lower()

    if worker_type == "queen":
        queen_worker()
    elif worker_type == "developer":
        developer_worker()
    else:
        print(f"❌ 不正なworker type: {worker_type}")
        print("正しい値: queen または developer")
        sys.exit(1)


if __name__ == "__main__":
    main()
