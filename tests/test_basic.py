"""
Basic tests for Hive system modules.

Phase 1 用の基本的なテストスイート。
各モジュールの基本的なインポートと初期化をテストします。
"""


class TestBasicImports:
    """Test basic module imports."""

    def test_hive_modules_import(self) -> None:
        """Test that all Hive modules can be imported."""
        # Test core modules
        import comb  # noqa: F401
        import queen  # noqa: F401
        import tools  # noqa: F401
        import workers  # noqa: F401

    def test_module_versions(self) -> None:
        """Test that modules have version information."""
        import comb
        import queen
        import tools
        import workers

        # All modules should have version
        assert hasattr(queen, "__version__")
        assert hasattr(workers, "__version__")
        assert hasattr(comb, "__version__")
        assert hasattr(tools, "__version__")

        # Version should be valid
        assert queen.__version__ == "0.1.0"
        assert workers.__version__ == "0.1.0"
        assert comb.__version__ == "0.1.0"
        assert tools.__version__ == "0.1.0"


class TestProjectStructure:
    """Test project directory structure."""

    def test_module_structure(self) -> None:
        """Test that module structure is correct."""
        import comb
        import queen
        import tools
        import workers

        # Modules should be properly initialized
        assert queen.__doc__ is not None
        assert workers.__doc__ is not None
        assert comb.__doc__ is not None
        assert tools.__doc__ is not None


# Phase 1 テストのためのダミーテスト
def test_basic_functionality() -> None:
    """Test basic functionality placeholder."""
    # Phase 1 では実装はまだないので、基本的な動作確認のみ
    assert True


def test_project_metadata() -> None:
    """Test project metadata is available."""
    # プロジェクト構造が正しく設定されていることを確認
    import os
    import sys

    # プロジェクトルートが Python path にあることを確認
    project_root = os.path.dirname(os.path.dirname(__file__))
    assert project_root in sys.path or any(project_root in path for path in sys.path)
