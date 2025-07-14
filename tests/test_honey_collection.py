"""
Test cases for Honey collection and quality management functionality
"""

import json
import tempfile
from pathlib import Path

from queen.honey_collector import HoneyArtifact, HoneyCollector, HoneyType, QualityLevel
from queen.task_distributor import TaskDistributor, TaskStatus


class TestHoneyCollector:
    """Honey収集機能のテストクラス"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())

        # テスト用のファイル構造を作成
        self.test_files_dir = self.temp_dir / "test_files"
        self.test_files_dir.mkdir()

        # サンプルファイルを作成
        self._create_test_files()

        # HiveCollectorを初期化（一時ディレクトリを使用）
        import os

        os.chdir(self.temp_dir)
        self.honey_collector = HoneyCollector()

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def _create_test_files(self) -> None:
        """テスト用ファイルを作成"""
        # Pythonコードファイル
        python_file = self.test_files_dir / "example.py"
        python_file.write_text("""
def hello_world():
    '''Simple hello world function'''
    print("Hello, World!")
    return "Hello, World!"

if __name__ == "__main__":
    hello_world()
""")

        # Markdownドキュメント
        md_file = self.test_files_dir / "README.md"
        md_file.write_text("""
# Test Project

This is a test project for the Hive system.

## Features

- Feature 1: Basic functionality
- Feature 2: Advanced features

## Code Example

```python
def example():
    return "Hello"
```
""")

        # 設定ファイル
        config_file = self.test_files_dir / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "name": "test_project",
                    "version": "1.0.0",
                    "settings": {"debug": True, "timeout": 30},
                },
                indent=2,
            )
        )

        # 小さいファイル（品質が低い）
        tiny_file = self.test_files_dir / "tiny.txt"
        tiny_file.write_text("x")

        # データファイル
        data_file = self.test_files_dir / "data.csv"
        data_file.write_text("id,name,value\n1,test,100\n2,demo,200\n")

    def test_file_type_classification(self) -> None:
        """ファイルタイプ分類テスト"""
        test_cases = [
            ("test.py", HoneyType.CODE),
            ("test.js", HoneyType.CODE),
            ("README.md", HoneyType.DOCS),
            ("config.json", HoneyType.CONFIG),
            ("data.csv", HoneyType.DATA),
            ("report.log", HoneyType.REPORTS),
            ("unknown.xyz", HoneyType.UNKNOWN),
        ]

        for filename, expected_type in test_cases:
            file_path = Path(filename)
            actual_type = self.honey_collector._classify_file_type(file_path)
            assert actual_type == expected_type, (
                f"Expected {expected_type} for {filename}, got {actual_type}"
            )

    def test_manual_artifact_collection(self) -> None:
        """手動成果物収集テスト"""
        # テストファイルパス
        test_file = self.test_files_dir / "example.py"

        # 手動収集実行
        artifacts = self.honey_collector.collect_manual_artifacts(
            [str(test_file)], "test-nectar"
        )

        assert len(artifacts) == 1
        artifact = artifacts[0]

        assert artifact.nectar_id == "test-nectar"
        assert artifact.honey_type == HoneyType.CODE
        assert artifact.file_size > 0
        assert artifact.quality_score > 0
        assert artifact.worker_id == "manual"
        assert Path(artifact.collected_path).exists()

    def test_quality_score_calculation(self) -> None:
        """品質スコア計算テスト"""
        # 高品質ファイル（Python）
        python_file = self.test_files_dir / "example.py"
        python_score = self.honey_collector._calculate_quality_score(
            python_file, HoneyType.CODE
        )
        assert python_score > 50, (
            f"Python file should have good quality score, got {python_score}"
        )

        # 高品質ドキュメント（Markdown）
        md_file = self.test_files_dir / "README.md"
        md_score = self.honey_collector._calculate_quality_score(
            md_file, HoneyType.DOCS
        )
        assert md_score > 50, (
            f"Markdown file should have good quality score, got {md_score}"
        )

        # 低品質ファイル（小さすぎる）
        tiny_file = self.test_files_dir / "tiny.txt"
        tiny_score = self.honey_collector._calculate_quality_score(
            tiny_file, HoneyType.DOCS
        )
        assert tiny_score < 50, (
            f"Tiny file should have low quality score, got {tiny_score}"
        )

    def test_quality_level_determination(self) -> None:
        """品質レベル決定テスト"""
        test_cases = [
            (95, QualityLevel.EXCELLENT),
            (80, QualityLevel.GOOD),
            (60, QualityLevel.ACCEPTABLE),
            (30, QualityLevel.POOR),
        ]

        for score, expected_level in test_cases:
            actual_level = self.honey_collector._determine_quality_level(score)
            assert actual_level == expected_level, (
                f"Score {score} should be {expected_level}, got {actual_level}"
            )

    def test_duplicate_detection(self) -> None:
        """重複検出テスト"""
        test_file = self.test_files_dir / "example.py"

        # 最初の収集
        artifacts1 = self.honey_collector.collect_manual_artifacts(
            [str(test_file)], "test-nectar-1"
        )
        assert len(artifacts1) == 1

        # 同じファイルの再収集（重複として検出される）
        artifacts2 = self.honey_collector.collect_manual_artifacts(
            [str(test_file)], "test-nectar-2"
        )
        assert len(artifacts2) == 0, "Duplicate file should not be collected again"

    def test_honey_directory_structure(self) -> None:
        """Honeyディレクトリ構造テスト"""
        expected_dirs = [
            self.honey_collector.honey_dir / "code",
            self.honey_collector.honey_dir / "docs",
            self.honey_collector.honey_dir / "reports",
            self.honey_collector.honey_dir / "config",
            self.honey_collector.honey_dir / "data",
            self.honey_collector.honey_dir / "history",
        ]

        for dir_path in expected_dirs:
            assert dir_path.exists(), f"Directory should exist: {dir_path}"
            assert dir_path.is_dir(), f"Should be a directory: {dir_path}"

    def test_get_honey_by_type(self) -> None:
        """タイプ別Honey取得テスト"""
        # 複数のファイルを収集
        python_file = self.test_files_dir / "example.py"
        md_file = self.test_files_dir / "README.md"
        config_file = self.test_files_dir / "config.json"

        self.honey_collector.collect_manual_artifacts(
            [str(python_file), str(md_file), str(config_file)], "test-nectar"
        )

        # タイプ別取得テスト
        code_artifacts = self.honey_collector.get_honey_by_type(HoneyType.CODE)
        docs_artifacts = self.honey_collector.get_honey_by_type(HoneyType.DOCS)
        config_artifacts = self.honey_collector.get_honey_by_type(HoneyType.CONFIG)

        assert len(code_artifacts) == 1
        assert len(docs_artifacts) == 1
        assert len(config_artifacts) == 1

        assert code_artifacts[0].honey_type == HoneyType.CODE
        assert docs_artifacts[0].honey_type == HoneyType.DOCS
        assert config_artifacts[0].honey_type == HoneyType.CONFIG

    def test_quality_report_generation(self) -> None:
        """品質レポート生成テスト"""
        # 複数のファイルを収集
        all_files = [
            str(self.test_files_dir / "example.py"),
            str(self.test_files_dir / "README.md"),
            str(self.test_files_dir / "config.json"),
            str(self.test_files_dir / "tiny.txt"),
            str(self.test_files_dir / "data.csv"),
        ]

        self.honey_collector.collect_manual_artifacts(all_files, "test-nectar")

        # 品質レポート生成
        report = self.honey_collector.generate_quality_report()

        assert report.total_artifacts == 5
        assert report.average_quality >= 0
        assert report.average_quality <= 100
        assert len(report.type_distribution) > 0
        assert len(report.quality_distribution) > 0
        assert isinstance(report.recommendations, list)
        assert isinstance(report.issues, list)

    def test_collection_stats(self) -> None:
        """収集統計テスト"""
        # ファイルを収集
        test_file = self.test_files_dir / "example.py"
        self.honey_collector.collect_manual_artifacts([str(test_file)], "test-nectar")

        # 統計取得
        stats = self.honey_collector.get_collection_stats()

        assert "total_artifacts" in stats
        assert "type_distribution" in stats
        assert "quality_distribution" in stats
        assert "average_quality" in stats
        assert "total_size_mb" in stats
        assert "unique_nectars" in stats

        assert stats["total_artifacts"] >= 1
        assert stats["average_quality"] >= 0

    def test_hash_registry_persistence(self) -> None:
        """ハッシュレジストリ永続化テスト"""
        test_file = self.test_files_dir / "example.py"

        # ファイル収集
        self.honey_collector.collect_manual_artifacts([str(test_file)], "test-nectar")

        # ハッシュレジストリファイルの存在確認
        assert self.honey_collector.hash_registry_file.exists()

        # レジストリ内容確認
        assert len(self.honey_collector.hash_registry) > 0

        # 新しいコレクターインスタンスでレジストリがロードされることを確認
        new_collector = HoneyCollector()
        assert len(new_collector.hash_registry) > 0

    def test_collection_history_saving(self) -> None:
        """収集履歴保存テスト"""
        test_file = self.test_files_dir / "example.py"

        # ファイル収集
        self.honey_collector.collect_manual_artifacts([str(test_file)], "test-nectar")

        # 履歴ディレクトリとファイルの存在確認
        history_files = list(
            self.honey_collector.collection_history_dir.glob("collection-*.json")
        )
        assert len(history_files) > 0

        # 履歴ファイル内容確認
        with open(history_files[0], encoding="utf-8") as f:
            history_data = json.load(f)

        assert "collected_at" in history_data
        assert "artifact_count" in history_data
        assert "artifacts" in history_data
        assert history_data["artifact_count"] == 1

    def test_cleanup_old_honey(self) -> None:
        """古いHoney清理テスト"""
        # ファイル収集
        test_file = self.test_files_dir / "example.py"
        artifacts = self.honey_collector.collect_manual_artifacts(
            [str(test_file)], "test-nectar"
        )

        # 収集ファイルの存在確認
        assert len(artifacts) == 1
        collected_path = Path(artifacts[0].collected_path)
        assert collected_path.exists()

        # 0日で清理（すべて削除）
        deleted_count = self.honey_collector.cleanup_old_honey(0)
        assert deleted_count == 1

        # ファイルが削除されたことを確認
        assert not collected_path.exists()

    def test_artifact_metadata_serialization(self) -> None:
        """成果物メタデータシリアライゼーションテスト"""
        test_file = self.test_files_dir / "example.py"
        artifacts = self.honey_collector.collect_manual_artifacts(
            [str(test_file)], "test-nectar"
        )

        artifact = artifacts[0]

        # 辞書変換テスト
        artifact_dict = artifact.to_dict()
        assert isinstance(artifact_dict, dict)
        assert artifact_dict["honey_id"] == artifact.honey_id
        assert artifact_dict["honey_type"] == artifact.honey_type.value
        assert artifact_dict["quality_level"] == artifact.quality_level.value

        # 辞書から復元テスト
        restored_artifact = HoneyArtifact.from_dict(artifact_dict)
        assert restored_artifact.honey_id == artifact.honey_id
        assert restored_artifact.honey_type == artifact.honey_type
        assert restored_artifact.quality_level == artifact.quality_level
        assert restored_artifact.collected_at == artifact.collected_at


class TestHoneyIntegration:
    """Honey機能統合テストクラス"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        import os

        os.chdir(self.temp_dir)

        self.task_distributor = TaskDistributor()
        self.honey_collector = HoneyCollector()

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_nectar_to_honey_workflow(self) -> None:
        """Nectar→Honey ワークフローテスト"""
        # テストファイル作成
        test_file = self.temp_dir / "output.py"
        test_file.write_text("print('Hello from nectar!')")

        # Nectar作成
        nectar = self.task_distributor.create_nectar(
            title="Test Task",
            description="Create a simple Python script",
            assigned_to="developer",
            expected_honey=["output.py"],
        )

        # Nectarを完了状態に変更
        self.task_distributor.update_nectar_status(
            nectar.nectar_id, TaskStatus.COMPLETED
        )

        # 手動でファイルを収集（自動収集のシミュレーション）
        artifacts = self.honey_collector.collect_manual_artifacts(
            [str(test_file)], nectar.nectar_id
        )

        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert artifact.nectar_id == nectar.nectar_id
        assert artifact.honey_type == HoneyType.CODE

    def test_quality_workflow_end_to_end(self) -> None:
        """エンドツーエンド品質ワークフローテスト"""
        # 複数のファイルタイプを作成
        files = {
            "main.py": "def main():\n    print('Hello World')\n\nif __name__ == '__main__':\n    main()",
            "README.md": "# Project\n\nThis is a test project.\n\n## Usage\n\nRun `python main.py`",
            "config.json": '{"debug": true, "version": "1.0.0"}',
            "data.csv": "id,name\n1,test\n2,demo",
        }

        file_paths = []
        for filename, content in files.items():
            file_path = self.temp_dir / filename
            file_path.write_text(content)
            file_paths.append(str(file_path))

        # 手動収集
        artifacts = self.honey_collector.collect_manual_artifacts(
            file_paths, "integration-test"
        )
        assert len(artifacts) == 4

        # 品質レポート生成
        report = self.honey_collector.generate_quality_report()
        assert report.total_artifacts == 4
        assert len(report.type_distribution) >= 3  # code, docs, config最低3タイプ

        # タイプ別取得
        code_artifacts = self.honey_collector.get_honey_by_type(HoneyType.CODE)
        docs_artifacts = self.honey_collector.get_honey_by_type(HoneyType.DOCS)
        config_artifacts = self.honey_collector.get_honey_by_type(HoneyType.CONFIG)

        assert len(code_artifacts) == 1  # main.py
        assert len(docs_artifacts) == 1  # README.md
        assert len(config_artifacts) == 1  # config.json

        # 統計確認
        stats = self.honey_collector.get_collection_stats()
        assert stats["total_artifacts"] == 4
        assert stats["unique_nectars"] == 1  # integration-test nectar
