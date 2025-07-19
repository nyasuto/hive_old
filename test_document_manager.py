#!/usr/bin/env python3
"""
Document Manager Test Script

.hive/docs への出力機能のテスト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from hive.hive_directory.manager import HiveDirectoryManager
from hive.hive_directory.document_manager import DocumentManager


def test_document_manager():
    """Document Manager の基本機能をテスト"""
    print("🧪 Document Manager テスト開始")
    
    # テスト用の.hiveディレクトリ
    test_dir = Path("/tmp/hive_test")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # HiveDirectoryManagerを初期化
        hive_manager = HiveDirectoryManager(test_dir)
        hive_manager.initialize(force=True)
        
        print(f"✅ .hiveディレクトリ初期化: {hive_manager.hive_dir}")
        
        # DocumentManagerを取得
        doc_manager = hive_manager.document_manager
        
        # テストレポートを作成
        report_content = """# テストレポート

## 概要
これはDocument Managerのテストレポートです。

## 実行内容
- .hive/docs ディレクトリの作成確認
- レポートファイルの生成確認
- メタデータの付加確認

## 結果
✅ 全ての機能が正常に動作しています。
"""
        
        report_path = doc_manager.create_report(
            "Document Manager Test", 
            report_content, 
            "test",
            "test_session_001"
        )
        
        print(f"✅ テストレポート作成: {report_path}")
        
        # 分析ドキュメントを作成
        analysis_content = """# 分析結果

## Beeの作業レポート出力先分析

### 現状
- 従来はdocs/ディレクトリに出力していた可能性がある
- 実際のコードベースでは直接的なdocs出力は見つからなかった

### 新しい仕組み
- .hive/docs/reports/ にレポートを出力
- .hive/docs/analysis/ に分析結果を出力
- .hive/docs/design/ に設計文書を出力
- .hive/docs/meetings/ に会議録を出力

### メリット
- プロジェクトのドキュメントとHive生成ドキュメントを分離
- バージョン管理から除外可能
- 自動クリーンアップ対応
"""
        
        analysis_path = doc_manager.create_analysis_document(
            "Bee Report Output Analysis",
            analysis_content,
            "test_session_001"
        )
        
        print(f"✅ 分析ドキュメント作成: {analysis_path}")
        
        # ドキュメント一覧を取得
        documents = doc_manager.list_documents()
        print(f"✅ 作成されたドキュメント数: {len(documents)}")
        
        for doc in documents:
            print(f"   📄 {doc['type']}: {doc['name']}")
        
        # ドキュメント概要を取得
        summary = doc_manager.get_docs_summary()
        print(f"✅ ドキュメント概要: {summary}")
        
        # ステータス確認
        status = hive_manager.status()
        print(f"✅ Hiveシステムステータス: {status['documents']}")
        
        print("\n🎉 Document Manager テスト完了!")
        print(f"📁 テストファイルは {test_dir} に保存されました")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_migration_scenario():
    """既存のdocs出力からの移行シナリオをテスト"""
    print("\n🔄 移行シナリオテスト開始")
    
    test_dir = Path("/tmp/hive_migration_test")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # 従来のdocsディレクトリをシミュレート
        old_docs_dir = test_dir / "docs"
        old_docs_dir.mkdir(exist_ok=True)
        
        # 既存のドキュメントファイルを作成
        old_report = old_docs_dir / "old_report.md"
        old_report.write_text("# 古いレポート\n\nこれは従来のdocs/に出力されていたファイルです。")
        
        print(f"✅ 従来のドキュメント作成: {old_report}")
        
        # Hiveシステムを初期化
        hive_manager = HiveDirectoryManager(test_dir)
        hive_manager.initialize(force=True)
        
        # 新しい場所にドキュメントを作成
        doc_manager = hive_manager.document_manager
        
        migration_report = doc_manager.create_report(
            "Migration Test Report",
            """# 移行テストレポート

## 移行内容
- 従来: docs/old_report.md
- 新規: .hive/docs/reports/

## 利点
1. プロジェクトドキュメントとの分離
2. 自動管理対象
3. .gitignoreで除外可能
""",
            "migration"
        )
        
        print(f"✅ 移行後ドキュメント作成: {migration_report}")
        
        # 両方のディレクトリ構造を確認
        print("\n📁 ディレクトリ構造:")
        print(f"   従来: {old_docs_dir} (手動管理)")
        print(f"   新規: {hive_manager.hive_dir}/docs (自動管理)")
        
        print("\n🎉 移行シナリオテスト完了!")
        
        return True
        
    except Exception as e:
        print(f"❌ 移行テスト失敗: {e}")
        return False


if __name__ == "__main__":
    print("🐝 Hive Document Manager テスト")
    print("=" * 50)
    
    # 基本機能テスト
    basic_test = test_document_manager()
    
    # 移行シナリオテスト
    migration_test = test_migration_scenario()
    
    print("\n" + "=" * 50)
    print("📊 テスト結果:")
    print(f"   基本機能テスト: {'✅ 成功' if basic_test else '❌ 失敗'}")
    print(f"   移行シナリオテスト: {'✅ 成功' if migration_test else '❌ 失敗'}")
    
    if basic_test and migration_test:
        print("\n🎉 全テスト成功! Document Managerは正常に動作しています。")
        sys.exit(0)
    else:
        print("\n❌ テストに失敗しました。")
        sys.exit(1)