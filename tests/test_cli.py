"""
Hive CLI テスト
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from hive.cli_core import HiveCLI, MessageInfo, WorkerInfo
from hive.tmux_integration import HiveTmuxIntegration


class TestHiveCLI:
    """Hive CLI のテストクラス"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.cli = HiveCLI()

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init(self) -> None:
        """CLI初期化テスト"""
        assert self.cli.project_root is not None
        assert (
            self.cli.current_worker in self.cli.VALID_WORKERS
            or self.cli.current_worker == "unknown"
        )
        assert self.cli.VALID_WORKERS == [
            "queen",
            "architect",
            "frontend",
            "backend",
            "devops",
            "tester",
        ]

    def test_detect_current_worker_default(self) -> None:
        """デフォルトworker検出テスト"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("hive.cli_core.libtmux", None):
                cli = HiveCLI()
                assert cli.current_worker == "unknown"

    def test_detect_current_worker_from_env(self) -> None:
        """環境変数からworker検出テスト"""
        with patch.dict(os.environ, {"HIVE_WORKER_NAME": "backend"}):
            with patch.object(
                HiveTmuxIntegration, "get_current_worker", return_value=None
            ):
                cli = HiveCLI()
                assert cli.current_worker == "backend"

    def test_is_in_tmux_false(self) -> None:
        """tmux環境外の判定テスト"""
        with patch.dict(os.environ, {}, clear=True):
            cli = HiveCLI()
            assert not cli._is_in_tmux()

    def test_is_in_tmux_true(self) -> None:
        """tmux環境内の判定テスト"""
        with patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,12345,0"}):
            cli = HiveCLI()
            assert cli._is_in_tmux()

    def test_send_message_valid_recipient(self) -> None:
        """有効なrecipientへのメッセージ送信テスト"""
        with patch.object(self.cli, "_save_message_to_file") as mock_save:
            with patch.object(self.cli, "_send_to_tmux_pane") as mock_tmux:
                self.cli.send_message("backend", "テストメッセージ")
                mock_save.assert_called_once_with(
                    "backend", "テストメッセージ", "normal"
                )
                mock_tmux.assert_called_once_with(
                    "backend", "テストメッセージ", "normal"
                )

    def test_send_message_invalid_recipient(self) -> None:
        """無効なrecipientへのメッセージ送信テスト"""
        with pytest.raises(ValueError) as exc_info:
            self.cli.send_message("invalid", "テストメッセージ")
        assert "無効なWorker名" in str(exc_info.value)

    def test_urgent_message(self) -> None:
        """緊急メッセージ送信テスト"""
        with patch.object(self.cli, "send_message") as mock_send:
            self.cli.urgent_message("queen", "緊急メッセージ")
            mock_send.assert_called_once_with(
                "queen", "緊急メッセージ", priority="urgent"
            )

    def test_broadcast_message(self) -> None:
        """ブロードキャストメッセージテスト"""
        with patch.object(self.cli, "_save_message_to_file") as mock_save:
            with patch.object(self.cli, "_send_to_tmux_pane") as mock_tmux:
                self.cli.current_worker = "queen"
                self.cli.broadcast_message("全体メッセージ")

                # queen以外の全workerに送信されることを確認
                expected_calls = len(self.cli.VALID_WORKERS) - 1  # queen自身を除く
                assert mock_save.call_count == expected_calls
                assert mock_tmux.call_count == expected_calls

    def test_save_message_to_file(self) -> None:
        """メッセージファイル保存テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            self.cli._save_message_to_file("backend", "テストメッセージ", "normal")

            # メッセージファイルが作成されていることを確認
            messages_dir = self.test_dir / ".hive" / "messages"
            assert messages_dir.exists()

            message_files = list(messages_dir.glob("*.json"))
            assert len(message_files) == 1

            # メッセージ内容を確認
            with open(message_files[0], encoding="utf-8") as f:
                data = json.load(f)
                assert data["to_worker"] == "backend"
                assert data["message"] == "テストメッセージ"
                assert data["priority"] == "normal"

    def test_get_all_workers_without_tmux(self) -> None:
        """tmux環境なしでのworker取得テスト"""
        with patch.object(self.cli, "tmux_session", None):
            workers = self.cli._get_all_workers()
            assert len(workers) == len(self.cli.VALID_WORKERS)
            assert all(w.pane_id == "virtual" for w in workers)

    def test_who_am_i_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """who-am-i出力テスト"""
        with patch.object(self.cli, "current_worker", "backend"):
            with patch.object(self.cli, "_is_in_tmux", return_value=False):
                self.cli.who_am_i()
                captured = capsys.readouterr()
                assert "現在のWorker: backend" in captured.out

    def test_status_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """status出力テスト"""
        with patch.object(self.cli, "current_worker", "frontend"):
            with patch.object(self.cli, "_is_in_tmux", return_value=False):
                with patch.object(self.cli, "_get_all_workers", return_value=[]):
                    with patch.object(self.cli, "_show_message_statistics"):
                        self.cli.status()
                        captured = capsys.readouterr()
                        assert "Hive Status" in captured.out
                        assert "現在のWorker: frontend" in captured.out

    def test_show_message_statistics_no_messages(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """メッセージ統計表示テスト（メッセージなし）"""
        with patch.object(self.cli, "project_root", self.test_dir):
            self.cli._show_message_statistics()
            captured = capsys.readouterr()
            assert "メッセージなし" in captured.out

    def test_show_message_statistics_with_messages(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """メッセージ統計表示テスト（メッセージあり）"""
        with patch.object(self.cli, "project_root", self.test_dir):
            # テスト用メッセージファイルを作成
            messages_dir = self.test_dir / ".hive" / "messages"
            messages_dir.mkdir(parents=True, exist_ok=True)

            message_data = {
                "from_worker": "queen",
                "to_worker": "backend",
                "message": "テストメッセージ",
                "timestamp": "2025-01-01T12:00:00",
                "priority": "normal",
            }

            with open(messages_dir / "test_message.json", "w", encoding="utf-8") as f:
                json.dump(message_data, f, ensure_ascii=False, indent=2)

            self.cli._show_message_statistics()
            captured = capsys.readouterr()
            assert "メッセージ統計: 1 件" in captured.out
            assert "queen → backend" in captured.out


class TestWorkerInfo:
    """WorkerInfo データクラステスト"""

    def test_worker_info_creation(self) -> None:
        """WorkerInfo作成テスト"""
        worker = WorkerInfo(name="backend", pane_id="1", active=True)
        assert worker.name == "backend"
        assert worker.pane_id == "1"
        assert worker.active is True
        assert worker.last_activity is None


class TestMessageInfo:
    """MessageInfo データクラステスト"""

    def test_message_info_creation(self) -> None:
        """MessageInfo作成テスト"""
        from datetime import datetime

        timestamp = datetime.now()
        message = MessageInfo(
            from_worker="queen",
            to_worker="backend",
            message="テストメッセージ",
            timestamp=timestamp,
            priority="urgent",
            message_type="command",
        )

        assert message.from_worker == "queen"
        assert message.to_worker == "backend"
        assert message.message == "テストメッセージ"
        assert message.timestamp == timestamp
        assert message.priority == "urgent"
        assert message.message_type == "command"

    def test_message_info_defaults(self) -> None:
        """MessageInfo デフォルト値テスト"""
        from datetime import datetime

        timestamp = datetime.now()
        message = MessageInfo(
            from_worker="queen",
            to_worker="backend",
            message="テストメッセージ",
            timestamp=timestamp,
        )

        assert message.priority == "normal"
        assert message.message_type == "command"


class TestBootstrapFunctionality:
    """Bootstrap機能のテストクラス"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.cli = HiveCLI()

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_bootstrap_project_web_app(self) -> None:
        """web-appプロジェクトのブートストラップテスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            # テンプレートディレクトリの作成
            templates_dir = self.test_dir / "templates"
            templates_dir.mkdir()

            # プロジェクトテンプレートの作成
            projects_dir = templates_dir / "projects"
            projects_dir.mkdir()

            test_template = {
                "name": "web-app",
                "description": "Test web app",
                "variables": {
                    "PROJECT_TYPE": "テストアプリ",
                    "PROJECT_TECH_STACK": "React + Node.js",
                },
                "initial_tasks": {
                    "queen": ["要件確認", "スケジュール作成"],
                    "backend": ["環境構築", "API実装"],
                },
            }

            with open(projects_dir / "web-app.json", "w", encoding="utf-8") as f:
                json.dump(test_template, f, ensure_ascii=False, indent=2)

            # 役割テンプレートの作成
            roles_dir = templates_dir / "roles"
            roles_dir.mkdir()

            with open(roles_dir / "queen.md", "w", encoding="utf-8") as f:
                f.write("# Queen Worker\n\n{{PROJECT_NAME}} - {{PROJECT_TYPE}}")

            with open(roles_dir / "backend.md", "w", encoding="utf-8") as f:
                f.write("# Backend Worker\n\n{{PROJECT_TECH_STACK}}")

            # Bootstrap実行
            self.cli.bootstrap_project("web-app", "テストプロジェクト")

            # 生成されたファイルの確認
            hive_dir = self.test_dir / ".hive"
            assert hive_dir.exists()

            config_file = hive_dir / "config.json"
            assert config_file.exists()

            with open(config_file, encoding="utf-8") as f:
                config = json.load(f)
                assert config["project_name"] == "テストプロジェクト"
                assert config["project_type"] == "web-app"

            # Workerディレクトリの確認
            workers_dir = hive_dir / "workers"
            assert workers_dir.exists()

            queen_dir = workers_dir / "queen"
            assert queen_dir.exists()

            role_file = queen_dir / "ROLE.md"
            assert role_file.exists()

            with open(role_file, encoding="utf-8") as f:
                content = f.read()
                assert "テストプロジェクト" in content
                assert "テストアプリ" in content

            tasks_file = queen_dir / "tasks.md"
            assert tasks_file.exists()

            with open(tasks_file, encoding="utf-8") as f:
                content = f.read()
                assert "要件確認" in content
                assert "スケジュール作成" in content

    def test_bootstrap_project_invalid_type(self) -> None:
        """無効なプロジェクトタイプでのブートストラップテスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with pytest.raises(ValueError) as exc_info:
                self.cli.bootstrap_project("invalid-type", "テストプロジェクト")
            assert "プロジェクトテンプレート 'invalid-type' が見つかりません" in str(
                exc_info.value
            )

    def test_who_am_i_detailed_with_role_file(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """役割ファイルありでのwho-am-i詳細表示テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with patch.object(self.cli, "current_worker", "queen"):
                # .hive/workers/queen ディレクトリの作成
                queen_dir = self.test_dir / ".hive" / "workers" / "queen"
                queen_dir.mkdir(parents=True)

                # ROLE.mdファイルの作成
                role_content = """# Queen Worker
## 🎯 基本的な役割
あなたは **Queen Worker** です。
### 主な責務
- プロジェクト管理
- タスク配布
## 他のセクション
その他の情報
"""
                with open(queen_dir / "ROLE.md", "w", encoding="utf-8") as f:
                    f.write(role_content)

                self.cli.who_am_i_detailed()
                captured = capsys.readouterr()
                assert "現在のWorker: queen" in captured.out
                assert "あなたは **Queen Worker** です。" in captured.out

    def test_who_am_i_detailed_without_role_file(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """役割ファイルなしでのwho-am-i詳細表示テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with patch.object(self.cli, "current_worker", "queen"):
                self.cli.who_am_i_detailed()
                captured = capsys.readouterr()
                assert "現在のWorker: queen" in captured.out
                assert "役割定義ファイルが見つかりません" in captured.out

    def test_show_my_role(self, capsys: pytest.CaptureFixture[str]) -> None:
        """完全な役割定義表示テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with patch.object(self.cli, "current_worker", "backend"):
                # .hive/workers/backend ディレクトリの作成
                backend_dir = self.test_dir / ".hive" / "workers" / "backend"
                backend_dir.mkdir(parents=True)

                # ROLE.mdファイルの作成
                role_content = "# Backend Worker\n\n完全な役割定義\n詳細な説明文"
                with open(backend_dir / "ROLE.md", "w", encoding="utf-8") as f:
                    f.write(role_content)

                self.cli.show_my_role()
                captured = capsys.readouterr()
                assert "# Backend Worker" in captured.out
                assert "完全な役割定義" in captured.out

    def test_remind_me_with_files(self, capsys: pytest.CaptureFixture[str]) -> None:
        """ファイルありでのremind-me表示テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with patch.object(self.cli, "current_worker", "frontend"):
                # .hive/workers/frontend ディレクトリの作成
                frontend_dir = self.test_dir / ".hive" / "workers" / "frontend"
                frontend_dir.mkdir(parents=True)

                # ROLE.mdファイルの作成
                role_content = """# Frontend Worker
### 主な責務
- UI実装
- UX最適化
### その他
"""
                with open(frontend_dir / "ROLE.md", "w", encoding="utf-8") as f:
                    f.write(role_content)

                # tasks.mdファイルの作成
                tasks_content = (
                    "## 現在のタスク\n1. ログイン画面の実装\n2. レスポンシブ対応"
                )
                with open(frontend_dir / "tasks.md", "w", encoding="utf-8") as f:
                    f.write(tasks_content)

                self.cli.remind_me()
                captured = capsys.readouterr()
                assert "現在のWorker: frontend" in captured.out
                assert "- UI実装" in captured.out
                assert "- UX最適化" in captured.out
                assert "現在のタスク:" in captured.out
                assert "ログイン画面の実装" in captured.out

    def test_remind_me_without_tasks(self, capsys: pytest.CaptureFixture[str]) -> None:
        """タスクファイルなしでのremind-me表示テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with patch.object(self.cli, "current_worker", "devops"):
                # .hive/workers/devops ディレクトリの作成
                devops_dir = self.test_dir / ".hive" / "workers" / "devops"
                devops_dir.mkdir(parents=True)

                # ROLE.mdファイルの作成
                role_content = """# DevOps Worker
### 主な責務
- インフラ構築
- CI/CD設定
"""
                with open(devops_dir / "ROLE.md", "w", encoding="utf-8") as f:
                    f.write(role_content)

                self.cli.remind_me()
                captured = capsys.readouterr()
                assert "現在のWorker: devops" in captured.out
                assert "- インフラ構築" in captured.out
                assert "まだ設定されていません" in captured.out

    def test_generate_role_file(self) -> None:
        """役割ファイル生成テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            # テンプレートディレクトリの作成
            templates_dir = self.test_dir / "templates" / "roles"
            templates_dir.mkdir(parents=True)

            # テンプレートファイルの作成
            template_content = "# {{PROJECT_NAME}} - {{PROJECT_TYPE}}\n\n技術スタック: {{PROJECT_TECH_STACK}}"
            with open(templates_dir / "tester.md", "w", encoding="utf-8") as f:
                f.write(template_content)

            # Workerディレクトリの作成
            worker_dir = self.test_dir / ".hive" / "workers" / "tester"
            worker_dir.mkdir(parents=True)

            # 変数の設定
            variables = {
                "PROJECT_NAME": "テストプロジェクト",
                "PROJECT_TYPE": "テストアプリ",
                "PROJECT_TECH_STACK": "Python + Jest",
            }

            self.cli._generate_role_file("tester", variables)

            # 生成されたファイルの確認
            role_file = worker_dir / "ROLE.md"
            assert role_file.exists()

            with open(role_file, encoding="utf-8") as f:
                content = f.read()
                assert "テストプロジェクト" in content
                assert "テストアプリ" in content
                assert "Python + Jest" in content

    def test_generate_tasks_file(self) -> None:
        """タスクファイル生成テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            # Workerディレクトリの作成
            worker_dir = self.test_dir / ".hive" / "workers" / "architect"
            worker_dir.mkdir(parents=True)

            tasks = ["システム設計", "API仕様作成", "データベース設計"]

            self.cli._generate_tasks_file("architect", tasks)

            # 生成されたファイルの確認
            tasks_file = worker_dir / "tasks.md"
            assert tasks_file.exists()

            with open(tasks_file, encoding="utf-8") as f:
                content = f.read()
                assert "Architect Worker - 初期タスク" in content
                assert "1. システム設計" in content
                assert "2. API仕様作成" in content
                assert "3. データベース設計" in content
                assert "完了したタスク" in content

    def test_generate_project_config(self) -> None:
        """プロジェクト設定ファイル生成テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            # .hiveディレクトリの作成
            hive_dir = self.test_dir / ".hive"
            hive_dir.mkdir()

            template = {
                "name": "test-project",
                "description": "Test project description",
                "variables": {"TEST_VAR": "test_value"},
            }

            self.cli._generate_project_config(template, "テストプロジェクト")

            # 生成されたファイルの確認
            config_file = hive_dir / "config.json"
            assert config_file.exists()

            with open(config_file, encoding="utf-8") as f:
                config = json.load(f)
                assert config["project_name"] == "テストプロジェクト"
                assert config["project_type"] == "test-project"
                assert config["project_description"] == "Test project description"
                assert config["variables"]["TEST_VAR"] == "test_value"
                assert "created_at" in config
                assert config["workers"] == self.cli.VALID_WORKERS


class TestTmuxIntegration:
    """Tmux統合機能のテストクラス"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.cli = HiveCLI()

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_tmux_status_no_session(self, capsys: pytest.CaptureFixture[str]) -> None:
        """tmux状態表示テスト（セッションなし）"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with patch.object(
                self.cli.tmux_integration, "get_session_status"
            ) as mock_status:
                mock_status.return_value = {
                    "session_exists": False,
                    "session_name": "hive",
                    "in_tmux": False,
                    "workers": {},
                    "unmapped_panes": [],
                }

                self.cli.tmux_status()
                captured = capsys.readouterr()

                assert "Hive Tmux Status" in captured.out
                assert "Hiveセッションが見つかりません" in captured.out

    def test_tmux_status_with_session(self, capsys: pytest.CaptureFixture[str]) -> None:
        """tmux状態表示テスト（セッションあり）"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with patch.object(
                self.cli.tmux_integration, "get_session_status"
            ) as mock_status:
                mock_status.return_value = {
                    "session_exists": True,
                    "session_name": "hive",
                    "in_tmux": True,
                    "workers": {
                        "queen": {
                            "pane_index": 0,
                            "pane_id": "%1",
                            "is_active": True,
                            "mapped": True,
                        },
                        "architect": {
                            "pane_index": 1,
                            "pane_id": None,
                            "is_active": False,
                            "mapped": False,
                        },
                    },
                    "unmapped_panes": [
                        {
                            "pane_id": "%3",
                            "pane_index": 3,
                            "pane_title": "Unmapped Pane",
                        }
                    ],
                }

                self.cli.tmux_status()
                captured = capsys.readouterr()

                assert "Hive Tmux Status" in captured.out
                assert "Worker-Pane Mappings" in captured.out
                assert "queen" in captured.out
                assert "architect" in captured.out
                assert "マッピングされていないpane" in captured.out

    def test_save_tmux_mapping_success(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """tmuxマッピング保存テスト（成功）"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with patch.object(
                self.cli.tmux_integration, "save_current_mapping"
            ) as mock_save:
                self.cli.save_tmux_mapping()
                captured = capsys.readouterr()

                assert "tmuxマッピングを保存しました" in captured.out
                mock_save.assert_called_once()

    def test_save_tmux_mapping_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """tmuxマッピング保存テスト（エラー）"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with patch.object(
                self.cli.tmux_integration, "save_current_mapping"
            ) as mock_save:
                mock_save.side_effect = Exception("Test error")

                self.cli.save_tmux_mapping()
                captured = capsys.readouterr()

                assert "マッピング保存エラー" in captured.out

    def test_enhanced_message_sending(self) -> None:
        """拡張されたメッセージ送信テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with patch.object(
                self.cli.tmux_integration, "is_in_tmux", return_value=True
            ):
                with patch.object(
                    self.cli.tmux_integration, "send_message_to_pane"
                ) as mock_send:
                    with patch.object(self.cli, "_save_message_to_file") as mock_save:
                        mock_send.return_value = True

                        self.cli.send_message("backend", "テストメッセージ")

                        mock_send.assert_called_once()
                        mock_save.assert_called_once()

    def test_enhanced_worker_detection(self) -> None:
        """拡張されたworker検出テスト"""
        with patch("hive.cli_core.HiveTmuxIntegration") as mock_tmux_class:
            mock_tmux_instance = mock_tmux_class.return_value
            mock_tmux_instance.get_current_worker.return_value = "backend"

            # 新しいCLIインスタンスを作成してworker検出をテスト
            cli = HiveCLI()

            assert cli.current_worker == "backend"
            mock_tmux_instance.get_current_worker.assert_called()


class TestProjectInitialization:
    """プロジェクト初期化機能のテストクラス"""

    def setup_method(self) -> None:
        """テスト前のセットアップ"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.cli = HiveCLI()

    def teardown_method(self) -> None:
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_project_new(self) -> None:
        """新規プロジェクト初期化テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with patch("builtins.input", return_value="y"):
                # テンプレートディレクトリの作成
                templates_dir = self.test_dir / "templates"
                templates_dir.mkdir()
                projects_dir = templates_dir / "projects"
                projects_dir.mkdir()
                roles_dir = templates_dir / "roles"
                roles_dir.mkdir()

                # プロジェクトテンプレートの作成
                test_template = {
                    "name": "web-app",
                    "description": "Test web app",
                    "variables": {
                        "PROJECT_TYPE": "テストアプリ",
                        "PROJECT_TECH_STACK": "React + Node.js",
                    },
                    "initial_tasks": {
                        "queen": ["要件確認", "スケジュール作成"],
                        "backend": ["環境構築", "API実装"],
                    },
                }

                with open(projects_dir / "web-app.json", "w", encoding="utf-8") as f:
                    json.dump(test_template, f, ensure_ascii=False, indent=2)

                # 役割テンプレートの作成
                for worker in self.cli.VALID_WORKERS:
                    with open(roles_dir / f"{worker}.md", "w", encoding="utf-8") as f:
                        f.write(
                            f"# {worker.title()} Worker\n\n{{{{PROJECT_NAME}}}} - {{{{PROJECT_TYPE}}}}"
                        )

                self.cli.init_project("テストプロジェクト", "web-app")

                # 生成されたファイルの確認
                hive_dir = self.test_dir / ".hive"
                assert hive_dir.exists()

                # config.json確認
                config_file = hive_dir / "config.json"
                assert config_file.exists()
                with open(config_file, encoding="utf-8") as f:
                    config = json.load(f)
                    assert config["project_name"] == "テストプロジェクト"

                # workers.json確認
                workers_file = hive_dir / "workers.json"
                assert workers_file.exists()
                with open(workers_file, encoding="utf-8") as f:
                    workers_config = json.load(f)
                    assert "workers" in workers_config
                    assert "queen" in workers_config["workers"]

                # Workerディレクトリ確認
                workers_dir = hive_dir / "workers"
                assert workers_dir.exists()

                for worker in self.cli.VALID_WORKERS:
                    worker_dir = workers_dir / worker
                    assert worker_dir.exists()

                    # 各Workerの必須ファイル確認
                    role_file = worker_dir / "ROLE.md"
                    assert role_file.exists()

                    context_file = worker_dir / "context.md"
                    assert context_file.exists()

                    # context.mdの内容確認
                    with open(context_file, encoding="utf-8") as f:
                        context_content = f.read()
                        assert "テストプロジェクト" in context_content
                        assert "プロジェクトコンテキスト" in context_content

    def test_init_project_existing_directory(self) -> None:
        """既存ディレクトリでの初期化テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            # 既存の.hiveディレクトリを作成
            hive_dir = self.test_dir / ".hive"
            hive_dir.mkdir()

            with patch("builtins.input", return_value="n"):
                self.cli.init_project("テストプロジェクト", "web-app")
                # キャンセルされるため、追加のファイルは作成されない

    def test_verify_project_config_valid(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """有効なプロジェクト設定の検証テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            # 完全な.hive構造を作成
            hive_dir = self.test_dir / ".hive"
            hive_dir.mkdir()

            # config.json作成
            config = {"project_name": "test", "project_type": "web-app"}
            with open(hive_dir / "config.json", "w", encoding="utf-8") as f:
                json.dump(config, f)

            # workers.json作成
            workers_config = {"version": "1.0", "workers": {}}
            with open(hive_dir / "workers.json", "w", encoding="utf-8") as f:
                json.dump(workers_config, f)

            # workersディレクトリ作成
            workers_dir = hive_dir / "workers"
            workers_dir.mkdir()

            for worker in self.cli.VALID_WORKERS:
                worker_dir = workers_dir / worker
                worker_dir.mkdir()
                (worker_dir / "ROLE.md").write_text("# Role")
                (worker_dir / "tasks.md").write_text("# Tasks")
                (worker_dir / "context.md").write_text("# Context")

            self.cli.verify_project_config()
            captured = capsys.readouterr()
            assert "プロジェクト設定に問題はありません" in captured.out

    def test_verify_project_config_invalid(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """無効なプロジェクト設定の検証テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            with patch("builtins.input", return_value="n"):
                # 空のディレクトリで検証
                self.cli.verify_project_config()
                captured = capsys.readouterr()
                assert "問題が見つかりました" in captured.out
                assert ".hiveディレクトリが存在しません" in captured.out

    def test_generate_context_file(self) -> None:
        """context.mdファイル生成テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            # Workerディレクトリの作成
            worker_dir = self.test_dir / ".hive" / "workers" / "queen"
            worker_dir.mkdir(parents=True)

            variables = {
                "PROJECT_NAME": "テストプロジェクト",
                "PROJECT_TYPE": "ウェブアプリ",
                "PROJECT_TECH_STACK": "React + Node.js",
                "PROJECT_DESCRIPTION": "テスト用のプロジェクトです",
            }

            self.cli._generate_context_file("queen", variables)

            # 生成されたファイルの確認
            context_file = worker_dir / "context.md"
            assert context_file.exists()

            with open(context_file, encoding="utf-8") as f:
                content = f.read()
                assert "テストプロジェクト" in content
                assert "ウェブアプリ" in content
                assert "React + Node.js" in content
                assert "テスト用のプロジェクトです" in content
                assert "Queen Worker - プロジェクトコンテキスト" in content

    def test_generate_workers_json(self) -> None:
        """workers.json生成テスト"""
        with patch.object(self.cli, "project_root", self.test_dir):
            # .hiveディレクトリの作成
            hive_dir = self.test_dir / ".hive"
            hive_dir.mkdir()

            self.cli._generate_workers_json()

            # 生成されたファイルの確認
            workers_file = hive_dir / "workers.json"
            assert workers_file.exists()

            with open(workers_file, encoding="utf-8") as f:
                workers_config = json.load(f)
                assert workers_config["version"] == "1.0"
                assert "workers" in workers_config
                assert len(workers_config["workers"]) == len(self.cli.VALID_WORKERS)

                # 各Workerの設定確認
                for worker in self.cli.VALID_WORKERS:
                    assert worker in workers_config["workers"]
                    worker_config = workers_config["workers"][worker]
                    assert worker_config["name"] == worker
                    assert worker_config["active"] is True
                    assert "role_file" in worker_config
                    assert "tasks_file" in worker_config
                    assert "context_file" in worker_config
