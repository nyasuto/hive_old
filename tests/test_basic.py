"""
Basic tests for Hive system modules.

現在のアーキテクチャ用の基本的なテストスイート。
ツールとワーカーモジュールの基本的なインポートと初期化をテストします。
"""


class TestBasicImports:
    """Test basic module imports."""

    def test_current_modules_import(self) -> None:
        """Test that current architecture modules can be imported."""
        # Test current modules only
        # Test that script files exist (without importing due to mypy issues)
        import os

        import tools  # noqa: F401
        import workers  # noqa: F401

        project_root = os.path.dirname(os.path.dirname(__file__))
        scripts_dir = os.path.join(project_root, "scripts")

        assert os.path.exists(os.path.join(scripts_dir, "hive_cli.py"))
        assert os.path.exists(os.path.join(scripts_dir, "hive_watch.py"))
        assert os.path.exists(os.path.join(scripts_dir, "worker_communication.py"))

    def test_module_versions(self) -> None:
        """Test that current modules have version information."""
        import tools
        import workers

        # Current modules should have version
        assert hasattr(workers, "__version__")
        assert hasattr(tools, "__version__")

        # Version should be valid
        assert workers.__version__ == "0.1.0"
        assert tools.__version__ == "0.1.0"


class TestProjectStructure:
    """Test project directory structure."""

    def test_module_structure(self) -> None:
        """Test that current module structure is correct."""
        import tools
        import workers

        # Current modules should be properly initialized
        assert workers.__doc__ is not None
        assert tools.__doc__ is not None


# 現在のアーキテクチャテスト
def test_basic_functionality() -> None:
    """Test basic functionality of current architecture."""
    # 現在のスクリプトベースアーキテクチャの基本動作確認
    import os

    # 重要なスクリプトファイルが存在することを確認
    project_root = os.path.dirname(os.path.dirname(__file__))
    scripts_dir = os.path.join(project_root, "scripts")

    assert os.path.exists(os.path.join(scripts_dir, "hive_cli.py"))
    assert os.path.exists(os.path.join(scripts_dir, "worker_communication.py"))
    assert os.path.exists(os.path.join(scripts_dir, "hive_watch.py"))
    assert os.path.exists(os.path.join(scripts_dir, "start-cozy-hive.sh"))
    assert os.path.exists(os.path.join(scripts_dir, "stop-cozy-hive.sh"))


def test_project_metadata() -> None:
    """Test project metadata is available."""
    # プロジェクト構造が正しく設定されていることを確認
    import os
    import sys

    # プロジェクトルートが Python path にあることを確認
    project_root = os.path.dirname(os.path.dirname(__file__))
    assert project_root in sys.path or any(project_root in path for path in sys.path)
