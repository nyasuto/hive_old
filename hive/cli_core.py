"""
Hive CLI Core Implementation
CLIコマンドの実装とtmux統合
"""

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import libtmux
except ImportError:
    libtmux = None  # type: ignore

from .tmux_integration import HiveTmuxIntegration


@dataclass
class WorkerInfo:
    """Worker情報"""

    name: str
    pane_id: str
    active: bool
    last_activity: datetime | None = None


@dataclass
class MessageInfo:
    """メッセージ情報"""

    from_worker: str
    to_worker: str
    message: str
    timestamp: datetime
    priority: str = "normal"  # normal, urgent
    message_type: str = "command"  # command, response, status


class HiveCLI:
    """Hive CLI コア機能"""

    VALID_WORKERS = ["queen", "architect", "frontend", "backend", "devops", "tester"]

    def __init__(self) -> None:
        """初期化"""
        self.project_root = Path(__file__).parent.parent
        self.tmux_integration = HiveTmuxIntegration(self.project_root)
        self.current_worker = self._detect_current_worker()
        self.tmux_session = self._get_tmux_session()

    def _detect_current_worker(self) -> str:
        """現在のWorkerを検出"""
        # tmux統合機能を使用して現在のworkerを検出
        tmux_worker = self.tmux_integration.get_current_worker()
        if tmux_worker and tmux_worker in self.VALID_WORKERS:
            return tmux_worker

        # 環境変数から判定
        worker_from_env = os.environ.get("HIVE_WORKER_NAME")
        if worker_from_env in self.VALID_WORKERS:
            return worker_from_env

        # デフォルト
        return "unknown"

    def _is_in_tmux(self) -> bool:
        """tmux環境内かどうか判定"""
        return self.tmux_integration.is_in_tmux()

    def _get_tmux_session(self) -> Any | None:
        """tmuxセッションを取得"""
        if not libtmux or not self._is_in_tmux():
            return None

        try:
            server = libtmux.Server()
            # "hive"セッションを探す
            for session in server.sessions:
                if session.name == "hive":
                    return session
        except Exception:
            pass

        return None

    def _get_current_tmux_pane(self) -> dict[str, Any] | None:
        """現在のtmux paneを取得"""
        try:
            result = subprocess.run(
                [
                    "tmux",
                    "display-message",
                    "-p",
                    "-F",
                    "#{pane_id}:#{pane_title}:#{pane_current_command}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                parts = result.stdout.strip().split(":")
                if len(parts) >= 3:
                    return {
                        "pane_id": parts[0],
                        "pane_title": parts[1],
                        "current_command": parts[2],
                    }
        except Exception:
            pass

        return None

    def _get_all_workers(self) -> list[WorkerInfo]:
        """全Workerの情報を取得"""
        workers = []

        if not self.tmux_session:
            # tmuxなしの場合は仮想的なworker情報を返す
            for worker in self.VALID_WORKERS:
                workers.append(
                    WorkerInfo(
                        name=worker,
                        pane_id="virtual",
                        active=worker == self.current_worker,
                    )
                )
            return workers

        try:
            # tmuxセッション内のpaneを検索
            for window in self.tmux_session.windows:
                for pane in window.panes:
                    pane_info = pane.cmd(
                        "display-message",
                        "-p",
                        "-F",
                        "#{pane_title}:#{pane_current_command}",
                    )
                    if pane_info:
                        title_cmd = pane_info.split(":")
                        if len(title_cmd) >= 1:
                            title = title_cmd[0].lower()
                            for worker in self.VALID_WORKERS:
                                if worker in title:
                                    workers.append(
                                        WorkerInfo(
                                            name=worker,
                                            pane_id=pane.id,
                                            active=pane.is_active(),
                                        )
                                    )
                                    break
        except Exception:
            pass

        return workers

    def send_message(
        self, recipient: str, message: str, priority: str = "normal"
    ) -> None:
        """メッセージを送信"""
        if recipient not in self.VALID_WORKERS:
            raise ValueError(
                f"無効なWorker名: {recipient}. 有効な名前: {', '.join(self.VALID_WORKERS)}"
            )

        print(f"📤 {self.current_worker} → {recipient}: {message}")

        # メッセージをファイルに保存（旧Combシステムとの互換性）
        self._save_message_to_file(recipient, message, priority)

        # tmux paneにメッセージを送信
        self._send_to_tmux_pane(recipient, message, priority)

        print(f"✅ メッセージを {recipient} に送信しました")

    def who_am_i(self) -> None:
        """現在のWorkerを表示"""
        print(f"🐝 現在のWorker: {self.current_worker}")

        if self._is_in_tmux():
            pane_info = self._get_current_tmux_pane()
            if pane_info:
                print(
                    f"📍 tmux pane: {pane_info['pane_id']} ({pane_info['pane_title']})"
                )

        env_worker = os.environ.get("HIVE_WORKER_NAME")
        if env_worker:
            print(f"🌍 環境変数: HIVE_WORKER_NAME={env_worker}")

    def status(self) -> None:
        """Hiveの状態を表示"""
        print("🐝 Hive Status")
        print("=" * 50)

        # 基本情報
        print(f"📁 プロジェクトルート: {self.project_root}")
        print(f"🔄 現在のWorker: {self.current_worker}")
        print(f"🖥️  tmux環境: {'✅' if self.tmux_integration.is_in_tmux() else '❌'}")

        # Tmux状態の詳細
        tmux_status = self.tmux_integration.get_session_status()
        print(f"🐝 Hiveセッション: {'✅' if tmux_status['session_exists'] else '❌'}")

        if tmux_status["session_exists"]:
            print(f"\n👥 Workers ({len(tmux_status['workers'])}):")
            for worker_name, worker_info in tmux_status["workers"].items():
                status_icon = "🟢" if worker_info["is_active"] else "⚪"
                mapped_icon = "✅" if worker_info["mapped"] else "❌"
                print(
                    f"   {status_icon} {worker_name} (pane: {worker_info['pane_index']}) {mapped_icon}"
                )

            if tmux_status["unmapped_panes"]:
                print(
                    f"\n⚠️ マッピングされていないpane ({len(tmux_status['unmapped_panes'])}):"
                )
                for pane in tmux_status["unmapped_panes"]:
                    print(f"   ❓ {pane['pane_title']} (pane: {pane['pane_index']})")
        else:
            # フォールバック: 旧来の方法でWorker状態を表示
            workers = self._get_all_workers()
            print(f"\n👥 Workers ({len(workers)}):")
            for worker in workers:
                status_icon = "🟢" if worker.active else "⚪"
                print(f"   {status_icon} {worker.name} (pane: {worker.pane_id})")

        # メッセージ統計
        self._show_message_statistics()

    def broadcast_message(self, message: str) -> None:
        """全Workerにメッセージを送信"""
        print(f"📢 {self.current_worker} が全Workerに送信: {message}")

        success_count = 0
        for worker in self.VALID_WORKERS:
            if worker != self.current_worker:  # 自分以外に送信
                try:
                    self._save_message_to_file(worker, message, "normal")
                    self._send_to_tmux_pane(worker, message, "normal")
                    success_count += 1
                except Exception as e:
                    print(f"⚠️ {worker} への送信に失敗: {e}")

        print(f"✅ {success_count} 人のWorkerに送信しました")

    def urgent_message(self, recipient: str, message: str) -> None:
        """緊急メッセージを送信"""
        print(f"🚨 緊急メッセージ: {self.current_worker} → {recipient}")
        self.send_message(recipient, message, priority="urgent")

    def init_project(self, project_name: str, project_type: str = "web-app") -> None:
        """新しいプロジェクトを初期化"""
        print(f"🚀 新しいプロジェクトを初期化: {project_name} ({project_type})")

        # .hiveディレクトリが既に存在する場合の確認
        hive_dir = self.project_root / ".hive"
        if hive_dir.exists():
            response = input(
                "⚠️ .hiveディレクトリが既に存在します。上書きしますか？ (y/N): "
            )
            if response.lower() not in ["y", "yes"]:
                print("❌ 初期化をキャンセルしました")
                return

        # プロジェクトテンプレートを読み込み
        template_path = (
            self.project_root / "templates" / "projects" / f"{project_type}.json"
        )
        if not template_path.exists():
            raise ValueError(
                f"プロジェクトテンプレート '{project_type}' が見つかりません"
            )

        with open(template_path, encoding="utf-8") as f:
            template = json.load(f)

        # プロジェクト固有の変数を設定
        variables = template["variables"].copy()
        variables["PROJECT_NAME"] = project_name

        # .hiveディレクトリの作成
        hive_dir.mkdir(exist_ok=True)

        # workers ディレクトリの作成
        workers_dir = hive_dir / "workers"
        workers_dir.mkdir(exist_ok=True)

        # 各Workerのディレクトリとファイルを作成
        for worker in self.VALID_WORKERS:
            worker_dir = workers_dir / worker
            worker_dir.mkdir(exist_ok=True)

            # ROLEファイルの生成
            self._generate_role_file(worker, variables)

            # 初期タスクファイルの生成
            if worker in template["initial_tasks"]:
                self._generate_tasks_file(worker, template["initial_tasks"][worker])

            # context.mdファイルの生成
            self._generate_context_file(worker, variables)

        # プロジェクト設定ファイルの作成
        self._generate_project_config(template, project_name)

        # workers.jsonファイルの生成
        self._generate_workers_json()

        # tmuxマッピングの初期化
        self._initialize_tmux_mapping()

        print(f"✅ プロジェクト '{project_name}' の初期化が完了しました")
        print("📁 設定ファイル: .hive/")
        print("📋 各Workerの役割: .hive/workers/<worker>/ROLE.md")
        print("📝 初期タスク: .hive/workers/<worker>/tasks.md")
        print("📄 Worker設定: .hive/workers.json")
        print("🔗 コンテキスト: .hive/workers/<worker>/context.md")
        print("🎛️  tmuxマッピング: .hive/tmux/workers.json")

    def bootstrap_project(self, project_type: str, project_name: str) -> None:
        """プロジェクトをブートストラップ（従来機能）"""
        print(f"🚀 プロジェクトブートストラップ: {project_type} - {project_name}")
        print("💡 ヒント: 新しいプロジェクトには 'hive init' を使用してください")

        # プロジェクトテンプレートを読み込み
        template_path = (
            self.project_root / "templates" / "projects" / f"{project_type}.json"
        )
        if not template_path.exists():
            raise ValueError(
                f"プロジェクトテンプレート '{project_type}' が見つかりません"
            )

        with open(template_path, encoding="utf-8") as f:
            template = json.load(f)

        # プロジェクト固有の変数を設定
        variables = template["variables"].copy()
        variables["PROJECT_NAME"] = project_name

        # .hiveディレクトリの作成
        hive_dir = self.project_root / ".hive"
        hive_dir.mkdir(exist_ok=True)

        # workers ディレクトリの作成
        workers_dir = hive_dir / "workers"
        workers_dir.mkdir(exist_ok=True)

        # 各Workerのディレクトリとファイルを作成
        for worker in self.VALID_WORKERS:
            worker_dir = workers_dir / worker
            worker_dir.mkdir(exist_ok=True)

            # ROLEファイルの生成
            self._generate_role_file(worker, variables, hive_dir)

            # 初期タスクファイルの生成
            if worker in template["initial_tasks"]:
                self._generate_tasks_file(
                    worker, template["initial_tasks"][worker], hive_dir
                )

        # プロジェクト設定ファイルの作成
        self._generate_project_config(template, project_name, hive_dir)

        print(f"✅ プロジェクト '{project_name}' のブートストラップが完了しました")
        print("📁 設定ファイル: .hive/")
        print("📋 各Workerの役割: .hive/workers/<worker>/ROLE.md")
        print("📝 初期タスク: .hive/workers/<worker>/tasks.md")

    def who_am_i_detailed(self) -> None:
        """詳細な役割情報を表示"""
        print(f"🐝 現在のWorker: {self.current_worker}")

        # ROLEファイルの確認
        role_file = (
            self.project_root / ".hive" / "workers" / self.current_worker / "ROLE.md"
        )
        if role_file.exists():
            print(f"📋 役割定義: {role_file}")
            # 役割の要約を表示
            with open(role_file, encoding="utf-8") as f:
                content = f.read()
                # 基本的な役割セクションを抽出
                lines = content.split("\n")
                in_basic_role = False
                for line in lines:
                    if line.startswith("## 🎯 基本的な役割"):
                        in_basic_role = True
                    elif line.startswith("## ") and in_basic_role:
                        break
                    elif in_basic_role and line.strip():
                        print(f"   {line}")
        else:
            print("⚠️ 役割定義ファイルが見つかりません")
            print(
                "   プロジェクトをブートストラップしてください: hive bootstrap <type> <name>"
            )

    def show_my_role(self) -> None:
        """完全な役割定義を表示"""
        role_file = (
            self.project_root / ".hive" / "workers" / self.current_worker / "ROLE.md"
        )
        if role_file.exists():
            with open(role_file, encoding="utf-8") as f:
                content = f.read()
                print(content)
        else:
            print("⚠️ 役割定義ファイルが見つかりません")
            print(
                "   プロジェクトをブートストラップしてください: hive bootstrap <type> <name>"
            )

    def remind_me(self) -> None:
        """現在の役割とタスクを確認"""
        print(f"🐝 現在のWorker: {self.current_worker}")

        # 役割の要約
        role_file = (
            self.project_root / ".hive" / "workers" / self.current_worker / "ROLE.md"
        )
        if role_file.exists():
            with open(role_file, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
                for line in lines:
                    if line.startswith("### 主な責務"):
                        print("\n📋 主な責務:")
                        break
                in_duties = False
                for line in lines:
                    if line.startswith("### 主な責務"):
                        in_duties = True
                    elif line.startswith("### ") and in_duties:
                        break
                    elif in_duties and line.strip().startswith("- "):
                        print(f"   {line}")

        # 現在のタスク
        tasks_file = (
            self.project_root / ".hive" / "workers" / self.current_worker / "tasks.md"
        )
        if tasks_file.exists():
            print("\n📝 現在のタスク:")
            with open(tasks_file, encoding="utf-8") as f:
                content = f.read()
                print(content)
        else:
            print("\n📝 現在のタスク: まだ設定されていません")

    def _generate_role_file(
        self, worker: str, variables: dict[str, str], hive_dir: Path | None = None
    ) -> None:
        """Workerの役割ファイルを生成"""
        template_path = self.project_root / "templates" / "roles" / f"{worker}.md"
        if not template_path.exists():
            print(f"⚠️ 役割テンプレート '{worker}' が見つかりません")
            return

        with open(template_path, encoding="utf-8") as f:
            template_content = f.read()

        # 変数の置換
        for var_name, var_value in variables.items():
            template_content = template_content.replace(
                f"{{{{{var_name}}}}}", var_value
            )

        # ファイルに書き込み（hive_dirが指定されていない場合はデフォルトを使用）
        if hive_dir is None:
            hive_dir = self.project_root / ".hive"
        role_file = hive_dir / "workers" / worker / "ROLE.md"
        with open(role_file, "w", encoding="utf-8") as f:
            f.write(template_content)

    def _generate_tasks_file(
        self, worker: str, tasks: list[str], hive_dir: Path | None = None
    ) -> None:
        """Workerの初期タスクファイルを生成"""
        tasks_content = f"# {worker.title()} Worker - 初期タスク\n\n"
        tasks_content += "## 🎯 現在のタスク\n\n"

        for i, task in enumerate(tasks, 1):
            tasks_content += f"{i}. {task}\n"

        tasks_content += "\n## ✅ 完了したタスク\n\n"
        tasks_content += "（まだありません）\n"

        if hive_dir is None:
            hive_dir = self.project_root / ".hive"
        tasks_file = hive_dir / "workers" / worker / "tasks.md"
        with open(tasks_file, "w", encoding="utf-8") as f:
            f.write(tasks_content)

    def _generate_project_config(
        self, template: dict[str, Any], project_name: str, hive_dir: Path | None = None
    ) -> None:
        """プロジェクト設定ファイルを生成"""
        config = {
            "project_name": project_name,
            "project_type": template["name"],
            "project_description": template["description"],
            "variables": template["variables"],
            "created_at": datetime.now().isoformat(),
            "workers": self.VALID_WORKERS,
        }

        if hive_dir is None:
            hive_dir = self.project_root / ".hive"
        config_file = hive_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _generate_context_file(self, worker: str, variables: dict[str, str]) -> None:
        """Workerのコンテキストファイルを生成"""
        context_content = f"""# {worker.title()} Worker - プロジェクトコンテキスト

## 🎯 プロジェクト概要
- **プロジェクト名**: {variables.get("PROJECT_NAME", "Unknown")}
- **プロジェクトタイプ**: {variables.get("PROJECT_TYPE", "Unknown")}
- **技術スタック**: {variables.get("PROJECT_TECH_STACK", "Unknown")}

## 🤝 連携する他のWorkers
- **Queen Worker**: プロジェクト管理・調整
- **Architect Worker**: システム設計・技術判断
- **Frontend Worker**: UI/UX開発
- **Backend Worker**: サーバーサイド開発
- **DevOps Worker**: インフラ・運用
- **Tester Worker**: 品質保証・テスト

## 📚 プロジェクト固有情報
{variables.get("PROJECT_DESCRIPTION", "プロジェクトの説明がありません")}

## 🔄 現在のフェーズ
初期設定フェーズ - プロジェクトの基盤構築中

## 📝 重要なメモ
- このファイルは {worker} Workerの作業コンテキストを保持します
- プロジェクトの進行に応じて更新してください
- 他のWorkerとの連携情報を記録してください

## 🔗 関連リソース
- プロジェクト設定: `.hive/config.json`
- Worker設定: `.hive/workers.json`
- 役割定義: `.hive/workers/{worker}/ROLE.md`
- タスク管理: `.hive/workers/{worker}/tasks.md`
"""

        context_file = self.project_root / ".hive" / "workers" / worker / "context.md"
        with open(context_file, "w", encoding="utf-8") as f:
            f.write(context_content)

    def _generate_workers_json(self) -> None:
        """workers.json設定ファイルを生成"""
        workers_config: dict[str, Any] = {
            "version": "1.0",
            "description": "Hive Workers Configuration",
            "workers": {},
        }

        for worker in self.VALID_WORKERS:
            workers_config["workers"][worker] = {
                "name": worker,
                "title": f"{worker.title()} Worker",
                "active": True,
                "role_file": f".hive/workers/{worker}/ROLE.md",
                "tasks_file": f".hive/workers/{worker}/tasks.md",
                "context_file": f".hive/workers/{worker}/context.md",
                "communication": {"priority": "normal", "channels": ["tmux", "file"]},
            }

        workers_file = self.project_root / ".hive" / "workers.json"
        with open(workers_file, "w", encoding="utf-8") as f:
            json.dump(workers_config, f, ensure_ascii=False, indent=2)

    def _initialize_tmux_mapping(self) -> None:
        """tmuxマッピングを初期化"""
        try:
            # tmux統合機能を使用してマッピングを保存
            self.tmux_integration.save_current_mapping()
        except Exception:
            # tmux環境でない場合は警告を出さずにスキップ
            pass

    def tmux_status(self) -> None:
        """詳細なtmux状態を表示"""
        status = self.tmux_integration.get_session_status()

        print("🐝 Hive Tmux Status")
        print("=" * 50)

        print(f"🖥️  tmux環境: {'✅' if status['in_tmux'] else '❌'}")
        print(
            f"🐝 セッション '{status['session_name']}': {'✅' if status['session_exists'] else '❌'}"
        )

        if status["session_exists"]:
            print("\n👥 Worker-Pane Mappings:")
            for worker_name, worker_info in status["workers"].items():
                mapped_icon = "✅" if worker_info["mapped"] else "❌"
                active_icon = "🟢" if worker_info["is_active"] else "⚪"
                pane_id = worker_info["pane_id"] or "N/A"
                print(
                    f"   {mapped_icon} {active_icon} {worker_name:<10} -> pane:{worker_info['pane_index']} ({pane_id})"
                )

            if status["unmapped_panes"]:
                print("\n⚠️ マッピングされていないpane:")
                for pane in status["unmapped_panes"]:
                    print(
                        f"   ❓ {pane['pane_title']} (pane:{pane['pane_index']}, id:{pane['pane_id']})"
                    )
        else:
            print("\n⚠️  Hiveセッションが見つかりません")
            print(
                "   ヒント: 'tmux new-session -s hive' でセッションを作成してください"
            )

    def save_tmux_mapping(self) -> None:
        """現在のtmuxマッピングを保存"""
        try:
            self.tmux_integration.save_current_mapping()
            print("✅ tmuxマッピングを保存しました")
            print("   設定ファイル: .hive/tmux/workers.json")
        except Exception as e:
            print(f"⚠️ マッピング保存エラー: {e}")

    def verify_project_config(self) -> None:
        """プロジェクト設定を検証"""
        print("🔍 プロジェクト設定を検証中...")

        issues = []
        hive_dir = self.project_root / ".hive"

        # 基本ディレクトリの存在確認
        if not hive_dir.exists():
            issues.append("⚠️ .hiveディレクトリが存在しません")

        # 必須ファイルの存在確認
        required_files: list[tuple[str, str]] = [
            (".hive/config.json", "プロジェクト設定"),
            (".hive/workers.json", "Worker設定"),
        ]

        for file_path, description in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                issues.append(f"⚠️ {description}ファイルが存在しません: {file_path}")

        # 各Workerディレクトリの存在確認
        workers_dir = hive_dir / "workers"
        if workers_dir.exists():
            for worker in self.VALID_WORKERS:
                worker_dir = workers_dir / worker
                if not worker_dir.exists():
                    issues.append(f"⚠️ {worker} Workerディレクトリが存在しません")
                    continue

                # Worker必須ファイルの確認
                worker_files: list[tuple[Path, str]] = [
                    (worker_dir / "ROLE.md", "役割定義"),
                    (worker_dir / "tasks.md", "タスク管理"),
                    (worker_dir / "context.md", "コンテキスト"),
                ]

                for file_path_obj, description in worker_files:
                    if not file_path_obj.exists():
                        issues.append(
                            f"⚠️ {worker} Workerの{description}ファイルが存在しません: {file_path_obj}"
                        )

        if issues:
            print(f"❌ {len(issues)}個の問題が見つかりました:")
            for issue in issues:
                print(f"   {issue}")

            response = input("\n🔧 問題を自動修復しますか？ (y/N): ")
            if response.lower() in ["y", "yes"]:
                self._repair_project_config()
        else:
            print("✅ プロジェクト設定に問題はありません")

    def _repair_project_config(self) -> None:
        """プロジェクト設定を修復"""
        print("🔧 プロジェクト設定を修復中...")

        # 現在の設定を読み込み（存在する場合）
        config_file = self.project_root / ".hive" / "config.json"
        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    current_config = json.load(f)
                project_name = current_config.get("project_name", "Unknown Project")
                project_type = current_config.get("project_type", "web-app")
            except Exception:
                project_name = "Unknown Project"
                project_type = "web-app"
        else:
            project_name = "Unknown Project"
            project_type = "web-app"

        # プロジェクトを再初期化
        try:
            self.init_project(project_name, project_type)
            print("✅ プロジェクト設定の修復が完了しました")
        except Exception as e:
            print(f"❌ 修復に失敗しました: {e}")

    def _save_message_to_file(
        self, recipient: str, message: str, priority: str
    ) -> None:
        """メッセージをファイルに保存（旧Combシステムとの互換性）"""
        try:
            # メッセージディレクトリを作成
            messages_dir = self.project_root / ".hive" / "messages"
            messages_dir.mkdir(parents=True, exist_ok=True)

            # メッセージファイルを作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{self.current_worker}_to_{recipient}.json"
            filepath = messages_dir / filename

            message_data = {
                "from_worker": self.current_worker,
                "to_worker": recipient,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "priority": priority,
                "message_type": "command",
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(message_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠️ メッセージファイル保存エラー: {e}")

    def _send_to_tmux_pane(self, recipient: str, message: str, priority: str) -> None:
        """tmux paneにメッセージを送信"""
        if not self.tmux_integration.is_in_tmux():
            return

        try:
            # 新しいtmux統合機能を使用
            success = self.tmux_integration.send_message_to_pane(
                recipient, f"{self.current_worker}: {message}", priority
            )

            if not success:
                print(f"⚠️ tmuxメッセージ送信失敗: {recipient} (pane not found)")

        except Exception as e:
            print(f"⚠️ tmux送信エラー: {e}")

    def _show_message_statistics(self) -> None:
        """メッセージ統計を表示"""
        try:
            messages_dir = self.project_root / ".hive" / "messages"
            if not messages_dir.exists():
                print("\n📊 メッセージ統計: メッセージなし")
                return

            message_files = list(messages_dir.glob("*.json"))
            if not message_files:
                print("\n📊 メッセージ統計: メッセージなし")
                return

            print(f"\n📊 メッセージ統計: {len(message_files)} 件")

            # 最新メッセージを表示
            latest_files = sorted(
                message_files, key=lambda f: f.stat().st_mtime, reverse=True
            )[:3]
            print("   最新メッセージ:")
            for file in latest_files:
                try:
                    with open(file, encoding="utf-8") as f:
                        data = json.load(f)
                        timestamp = datetime.fromisoformat(data["timestamp"]).strftime(
                            "%H:%M"
                        )
                        print(
                            f"   • {timestamp} {data['from_worker']} → {data['to_worker']}"
                        )
                except Exception:
                    pass

        except Exception as e:
            print(f"⚠️ 統計取得エラー: {e}")
