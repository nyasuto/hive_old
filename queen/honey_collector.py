"""
Honey Collection and Quality Management System

Issue #5の実装: Honey成果物収集・品質管理システム
完了したNectarからHoney（成果物）を収集し、品質チェックと分類を行う
"""

import hashlib
import json
import logging
import mimetypes
import shutil
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from comb.api import CombAPI
from queen.task_distributor import TaskDistributor


class HoneyType(Enum):
    """Honey成果物タイプ"""

    CODE = "code"
    DOCS = "docs"
    REPORTS = "reports"
    CONFIG = "config"
    DATA = "data"
    UNKNOWN = "unknown"


class QualityLevel(Enum):
    """品質レベル"""

    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"  # 70-89%
    ACCEPTABLE = "acceptable"  # 50-69%
    POOR = "poor"  # 0-49%


@dataclass
class HoneyArtifact:
    """Honey成果物データ構造"""

    honey_id: str
    nectar_id: str
    original_path: str
    collected_path: str
    honey_type: HoneyType
    file_size: int
    file_hash: str
    quality_score: float
    quality_level: QualityLevel
    metadata: dict[str, Any]
    collected_at: datetime
    worker_id: str

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data["honey_type"] = self.honey_type.value
        data["quality_level"] = self.quality_level.value
        data["collected_at"] = self.collected_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HoneyArtifact":
        """辞書から作成"""
        data["honey_type"] = HoneyType(data["honey_type"])
        data["quality_level"] = QualityLevel(data["quality_level"])
        data["collected_at"] = datetime.fromisoformat(data["collected_at"])
        return cls(**data)


@dataclass
class QualityReport:
    """品質レポート"""

    total_artifacts: int
    quality_distribution: dict[str, int]
    type_distribution: dict[str, int]
    average_quality: float
    recommendations: list[str]
    issues: list[str]
    generated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data["generated_at"] = self.generated_at.isoformat()
        return data


class HoneyCollector:
    """
    Honey成果物収集・品質管理システム

    完了したNectarから成果物を収集し、品質チェックと分類を実行
    """

    def __init__(self, queen_worker_id: str = "queen"):
        self.queen_worker_id = queen_worker_id
        self.comb_api = CombAPI(queen_worker_id)
        self.task_distributor = TaskDistributor(queen_worker_id)
        self.logger = logging.getLogger(__name__)

        # Honey保存ディレクトリ
        self.honey_dir = Path(".hive/honey")
        self.honey_dir.mkdir(parents=True, exist_ok=True)

        # サブディレクトリ
        self.code_dir = self.honey_dir / "code"
        self.docs_dir = self.honey_dir / "docs"
        self.reports_dir = self.honey_dir / "reports"
        self.config_dir = self.honey_dir / "config"
        self.data_dir = self.honey_dir / "data"

        for dir_path in [
            self.code_dir,
            self.docs_dir,
            self.reports_dir,
            self.config_dir,
            self.data_dir,
        ]:
            dir_path.mkdir(exist_ok=True)

        # 収集履歴ディレクトリ
        self.collection_history_dir = self.honey_dir / "history"
        self.collection_history_dir.mkdir(exist_ok=True)

        # 重複チェック用ハッシュ記録
        self.hash_registry_file = self.honey_dir / "hash_registry.json"
        self.hash_registry = self._load_hash_registry()

        # 品質チェック設定
        self.quality_config = {
            "code_extensions": {".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c"},
            "docs_extensions": {".md", ".txt", ".rst", ".pdf", ".html"},
            "config_extensions": {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"},
            "min_file_size": 1,  # 最小ファイルサイズ（バイト）
            "max_file_size": 100 * 1024 * 1024,  # 最大ファイルサイズ（100MB）
        }

    def collect_completed_nectars(self) -> list[HoneyArtifact]:
        """
        完了したNectarから成果物を自動収集

        Returns:
            収集されたHoney成果物リスト
        """
        completed_nectars = self.task_distributor.get_completed_nectars()
        collected_artifacts = []

        for nectar in completed_nectars:
            try:
                artifacts = self._collect_nectar_artifacts(nectar)
                collected_artifacts.extend(artifacts)
                self.logger.info(
                    f"Collected {len(artifacts)} artifacts from nectar {nectar.nectar_id}"
                )
            except Exception as e:
                self.logger.error(f"Failed to collect artifacts from {nectar.nectar_id}: {e}")

        self._save_collection_history(collected_artifacts)
        return collected_artifacts

    def collect_manual_artifacts(self, file_paths: list[str], nectar_id: str | None = None) -> list[HoneyArtifact]:
        """
        手動で指定されたファイルを収集

        Args:
            file_paths: 収集するファイルパスリスト
            nectar_id: 関連するNectar ID（任意）

        Returns:
            収集されたHoney成果物リスト
        """
        collected_artifacts = []

        for file_path in file_paths:
            try:
                path = Path(file_path)
                if not path.exists():
                    self.logger.warning(f"File not found: {file_path}")
                    continue

                artifact = self._create_honey_artifact(
                    path, nectar_id or "manual", "manual"
                )
                if artifact:
                    collected_artifacts.append(artifact)
                    self.logger.info(f"Manually collected: {file_path}")

            except Exception as e:
                self.logger.error(f"Failed to collect {file_path}: {e}")

        self._save_collection_history(collected_artifacts)
        return collected_artifacts

    def generate_quality_report(self) -> QualityReport:
        """
        収集された成果物の品質レポート生成

        Returns:
            品質レポート
        """
        all_artifacts = self._load_all_artifacts()

        # 品質分布計算
        quality_distribution: dict[str, int] = defaultdict(int)
        type_distribution: dict[str, int] = defaultdict(int)
        total_quality = 0.0

        for artifact in all_artifacts:
            quality_distribution[artifact.quality_level.value] += 1
            type_distribution[artifact.honey_type.value] += 1
            total_quality += artifact.quality_score

        average_quality = total_quality / len(all_artifacts) if all_artifacts else 0

        # 推奨事項とissue生成
        recommendations = self._generate_recommendations(all_artifacts, average_quality)
        issues = self._identify_quality_issues(all_artifacts)

        return QualityReport(
            total_artifacts=len(all_artifacts),
            quality_distribution=dict(quality_distribution),
            type_distribution=dict(type_distribution),
            average_quality=average_quality,
            recommendations=recommendations,
            issues=issues,
            generated_at=datetime.now(),
        )

    def get_honey_by_type(self, honey_type: HoneyType) -> list[HoneyArtifact]:
        """
        タイプ別Honey成果物取得

        Args:
            honey_type: Honeyタイプ

        Returns:
            指定タイプのHoney成果物リスト
        """
        type_dir = self._get_type_directory(honey_type)
        artifacts = []

        for artifact_file in type_dir.glob("*.json"):
            try:
                with open(artifact_file, encoding="utf-8") as f:
                    data = json.load(f)
                artifact = HoneyArtifact.from_dict(data)
                artifacts.append(artifact)
            except Exception as e:
                self.logger.error(f"Failed to load artifact {artifact_file}: {e}")

        return artifacts

    def cleanup_old_honey(self, days_to_keep: int = 30) -> int:
        """
        古いHoney成果物をクリーンアップ

        Args:
            days_to_keep: 保持日数

        Returns:
            削除したファイル数
        """
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        deleted_count = 0

        for type_dir in [self.code_dir, self.docs_dir, self.reports_dir, self.config_dir, self.data_dir]:
            for artifact_file in type_dir.glob("*.json"):
                try:
                    if artifact_file.stat().st_mtime < cutoff_date:
                        # JSONメタデータから実ファイルパスを取得して削除
                        with open(artifact_file, encoding="utf-8") as f:
                            data = json.load(f)

                        collected_path = Path(data["collected_path"])
                        if collected_path.exists():
                            collected_path.unlink()

                        artifact_file.unlink()
                        deleted_count += 1

                except Exception as e:
                    self.logger.error(f"Failed to cleanup {artifact_file}: {e}")

        self.logger.info(f"Cleaned up {deleted_count} old honey artifacts")
        return deleted_count

    def _collect_nectar_artifacts(self, nectar: Any) -> list[HoneyArtifact]:
        """Nectarから成果物を収集"""
        artifacts = []

        # expected_honeyからファイルパスを推定
        expected_paths = self._extract_file_paths_from_nectar(nectar)

        for file_path in expected_paths:
            path = Path(file_path)
            if path.exists():
                artifact = self._create_honey_artifact(path, nectar.nectar_id, nectar.assigned_to)
                if artifact:
                    artifacts.append(artifact)

        return artifacts

    def _extract_file_paths_from_nectar(self, nectar: Any) -> list[str]:
        """Nectarから期待されるファイルパスを抽出"""
        file_paths = []

        # expected_honeyから推定
        for _expected in nectar.expected_honey:
            # 一般的なファイルパターンをチェック
            common_paths = [
                f"{nectar.title.lower().replace(' ', '_')}.py",
                f"{nectar.title.lower().replace(' ', '_')}.md",
                "README.md",
                f"docs/{nectar.title.lower().replace(' ', '_')}.md",
                f"src/{nectar.title.lower().replace(' ', '_')}.py",
            ]
            file_paths.extend(common_paths)

        # メタデータから追加パスを取得
        if hasattr(nectar, 'metadata') and nectar.metadata and "output_files" in nectar.metadata:
            file_paths.extend(nectar.metadata["output_files"])

        return list(set(file_paths))  # 重複を除去

    def _create_honey_artifact(self, file_path: Path, nectar_id: str, worker_id: str) -> HoneyArtifact | None:
        """Honey成果物を作成"""
        try:
            # ファイル情報取得
            file_size = file_path.stat().st_size
            file_hash = self._calculate_file_hash(file_path)

            # 重複チェック
            if file_hash in self.hash_registry:
                self.logger.info(f"Duplicate file detected: {file_path}")
                return None

            # ファイルタイプ分類
            honey_type = self._classify_file_type(file_path)

            # 品質スコア計算
            quality_score = self._calculate_quality_score(file_path, honey_type)
            quality_level = self._determine_quality_level(quality_score)

            # 収集先パス決定
            type_dir = self._get_type_directory(honey_type)
            honey_id = f"honey-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{file_hash[:8]}"
            collected_path = type_dir / f"{honey_id}{file_path.suffix}"

            # ファイルをコピー
            shutil.copy2(file_path, collected_path)

            # メタデータ作成
            metadata = {
                "mime_type": mimetypes.guess_type(str(file_path))[0],
                "original_name": file_path.name,
                "extension": file_path.suffix,
                "created_at": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            }

            artifact = HoneyArtifact(
                honey_id=honey_id,
                nectar_id=nectar_id,
                original_path=str(file_path),
                collected_path=str(collected_path),
                honey_type=honey_type,
                file_size=file_size,
                file_hash=file_hash,
                quality_score=quality_score,
                quality_level=quality_level,
                metadata=metadata,
                collected_at=datetime.now(),
                worker_id=worker_id,
            )

            # メタデータを保存
            self._save_artifact_metadata(artifact)

            # ハッシュレジストリに追加
            self.hash_registry[file_hash] = {
                "honey_id": honey_id,
                "original_path": str(file_path),
                "collected_at": datetime.now().isoformat(),
            }
            self._save_hash_registry()

            return artifact

        except Exception as e:
            self.logger.error(f"Failed to create honey artifact for {file_path}: {e}")
            return None

    def _classify_file_type(self, file_path: Path) -> HoneyType:
        """ファイルタイプを分類"""
        extension = file_path.suffix.lower()

        code_extensions = self.quality_config.get("code_extensions", set())
        docs_extensions = self.quality_config.get("docs_extensions", set())
        config_extensions = self.quality_config.get("config_extensions", set())

        if isinstance(code_extensions, set) and extension in code_extensions:
            return HoneyType.CODE
        elif isinstance(docs_extensions, set) and extension in docs_extensions:
            return HoneyType.DOCS
        elif isinstance(config_extensions, set) and extension in config_extensions:
            return HoneyType.CONFIG
        elif extension in {".csv", ".json", ".xml", ".sql"}:
            return HoneyType.DATA
        elif extension in {".log", ".out", ".report"}:
            return HoneyType.REPORTS
        else:
            return HoneyType.UNKNOWN

    def _calculate_quality_score(self, file_path: Path, honey_type: HoneyType) -> float:
        """品質スコアを計算"""
        score = 0.0

        try:
            # ファイルサイズチェック
            file_size = file_path.stat().st_size
            min_file_size = self.quality_config.get("min_file_size", 1)
            max_file_size = self.quality_config.get("max_file_size", 100 * 1024 * 1024)

            if isinstance(min_file_size, int) and file_size < min_file_size:
                score = 0.0
            elif isinstance(max_file_size, int) and file_size > max_file_size:
                score = 20.0
            else:
                score += 30.0  # 基本点

            # ファイルタイプ別品質チェック
            if honey_type == HoneyType.CODE:
                score += self._check_code_quality(file_path)
            elif honey_type == HoneyType.DOCS:
                score += self._check_docs_quality(file_path)
            elif honey_type == HoneyType.CONFIG:
                score += self._check_config_quality(file_path)

            # ファイル名の適切性チェック
            if self._check_filename_quality(file_path):
                score += 10.0

        except Exception as e:
            self.logger.error(f"Failed to calculate quality score for {file_path}: {e}")
            score = 50.0  # デフォルト点

        return min(100.0, max(0.0, score))

    def _check_code_quality(self, file_path: Path) -> float:
        """コード品質チェック"""
        score = 0.0

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # 基本的な品質チェック
            if len(lines) > 10:  # 十分な長さ
                score += 20.0

            # コメント率チェック
            comment_lines = [line for line in lines if line.strip().startswith("#") or line.strip().startswith("//")]
            if len(comment_lines) / len(lines) > 0.1:  # 10%以上のコメント
                score += 15.0

            # 関数定義の存在チェック
            if "def " in content or "function " in content:
                score += 15.0

            # import文の存在チェック
            if "import " in content or "from " in content:
                score += 10.0

            # 基本的な構文チェック（エラーがないことを確認）
            if not any(keyword in content for keyword in ["TODO", "FIXME", "XXX"]):
                score += 10.0

        except Exception:
            score = 10.0  # エラー時は低いスコア

        return score

    def _check_docs_quality(self, file_path: Path) -> float:
        """ドキュメント品質チェック"""
        score = 0.0

        try:
            content = file_path.read_text(encoding="utf-8")

            # 長さチェック
            if len(content) > 100:
                score += 25.0

            # Markdown形式チェック
            if file_path.suffix == ".md":
                if content.startswith("#"):  # ヘッダーがある
                    score += 15.0
                if "```" in content:  # コードブロックがある
                    score += 10.0

            # 日本語/英語の適切な使用
            if any(ord(char) > 127 for char in content):  # 非ASCII文字（日本語など）
                score += 10.0

            # 構造化されているかチェック
            lines = content.split("\n")
            if any(line.startswith("#") for line in lines):  # 見出しがある
                score += 10.0

        except Exception:
            score = 20.0

        return score

    def _check_config_quality(self, file_path: Path) -> float:
        """設定ファイル品質チェック"""
        score = 30.0  # 基本点

        try:
            if file_path.suffix == ".json":
                content = file_path.read_text(encoding="utf-8")
                json.loads(content)  # JSONとして正しい
                score += 30.0
            elif file_path.suffix in {".yaml", ".yml"}:
                # YAML形式の基本チェック
                content = file_path.read_text(encoding="utf-8")
                if ":" in content:  # key-value構造
                    score += 30.0
            else:
                score += 20.0

        except Exception:
            score = 20.0

        return score

    def _check_filename_quality(self, file_path: Path) -> bool:
        """ファイル名の適切性チェック"""
        name = file_path.name

        # 適切な命名規則をチェック
        if name.count(".") == 1 and file_path.suffix:  # 拡張子が適切
            if not any(char in name for char in [" ", "　"]):  # スペースがない
                if name.replace("_", "").replace("-", "").replace(".", "").isalnum():  # 英数字+記号のみ
                    return True

        return False

    def _determine_quality_level(self, score: float) -> QualityLevel:
        """品質スコアから品質レベルを決定"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 70:
            return QualityLevel.GOOD
        elif score >= 50:
            return QualityLevel.ACCEPTABLE
        else:
            return QualityLevel.POOR

    def _calculate_file_hash(self, file_path: Path) -> str:
        """ファイルのハッシュを計算"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _get_type_directory(self, honey_type: HoneyType) -> Path:
        """Honeyタイプに対応するディレクトリを取得"""
        type_dirs = {
            HoneyType.CODE: self.code_dir,
            HoneyType.DOCS: self.docs_dir,
            HoneyType.REPORTS: self.reports_dir,
            HoneyType.CONFIG: self.config_dir,
            HoneyType.DATA: self.data_dir,
            HoneyType.UNKNOWN: self.honey_dir,
        }
        return type_dirs.get(honey_type, self.honey_dir)

    def _save_artifact_metadata(self, artifact: HoneyArtifact) -> None:
        """成果物メタデータを保存"""
        type_dir = self._get_type_directory(artifact.honey_type)
        metadata_file = type_dir / f"{artifact.honey_id}.json"

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(artifact.to_dict(), f, ensure_ascii=False, indent=2)

    def _load_hash_registry(self) -> dict[str, dict[str, Any]]:
        """ハッシュレジストリをロード"""
        if self.hash_registry_file.exists():
            try:
                with open(self.hash_registry_file, encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, dict):
                        return loaded_data
            except Exception as e:
                self.logger.error(f"Failed to load hash registry: {e}")
        return {}

    def _save_hash_registry(self) -> None:
        """ハッシュレジストリを保存"""
        try:
            with open(self.hash_registry_file, "w", encoding="utf-8") as f:
                json.dump(self.hash_registry, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save hash registry: {e}")

    def _save_collection_history(self, artifacts: list[HoneyArtifact]) -> None:
        """収集履歴を保存"""
        if not artifacts:
            return

        history_file = self.collection_history_dir / f"collection-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        history_data = {
            "collected_at": datetime.now().isoformat(),
            "artifact_count": len(artifacts),
            "artifacts": [artifact.to_dict() for artifact in artifacts],
        }

        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save collection history: {e}")

    def _load_all_artifacts(self) -> list[HoneyArtifact]:
        """すべての成果物を読み込み"""
        artifacts = []

        for honey_type in HoneyType:
            artifacts.extend(self.get_honey_by_type(honey_type))

        return artifacts

    def _generate_recommendations(self, artifacts: list[HoneyArtifact], average_quality: float) -> list[str]:
        """推奨事項を生成"""
        recommendations = []

        if average_quality < 60:
            recommendations.append("Overall quality is below acceptable level. Review development practices.")

        # タイプ別の推奨事項
        type_counts: dict[HoneyType, int] = defaultdict(int)
        for artifact in artifacts:
            type_counts[artifact.honey_type] += 1

        if type_counts[HoneyType.CODE] > type_counts[HoneyType.DOCS] * 2:
            recommendations.append("Consider increasing documentation coverage.")

        if type_counts[HoneyType.UNKNOWN] > 0:
            recommendations.append("Review and properly classify unknown file types.")

        # 品質分布の推奨事項
        poor_count = len([a for a in artifacts if a.quality_level == QualityLevel.POOR])
        if poor_count > len(artifacts) * 0.2:  # 20%以上がPOOR
            recommendations.append("High number of poor quality artifacts. Implement quality gates.")

        return recommendations

    def _identify_quality_issues(self, artifacts: list[HoneyArtifact]) -> list[str]:
        """品質問題を特定"""
        issues = []

        # 重複ファイルの問題
        hash_counts: dict[str, int] = defaultdict(int)
        for artifact in artifacts:
            hash_counts[artifact.file_hash] += 1

        duplicates = {h: c for h, c in hash_counts.items() if c > 1}
        if duplicates:
            issues.append(f"Found {len(duplicates)} duplicate file groups")

        # 小さすぎるファイル
        tiny_files = [a for a in artifacts if a.file_size < 10]
        if tiny_files:
            issues.append(f"Found {len(tiny_files)} very small files (< 10 bytes)")

        # 品質スコアが低いファイル
        low_quality = [a for a in artifacts if a.quality_score < 30]
        if low_quality:
            issues.append(f"Found {len(low_quality)} low quality files (score < 30)")

        return issues

    def get_collection_stats(self) -> dict[str, Any]:
        """収集統計を取得"""
        all_artifacts = self._load_all_artifacts()

        return {
            "total_artifacts": len(all_artifacts),
            "type_distribution": {
                honey_type.value: len([a for a in all_artifacts if a.honey_type == honey_type])
                for honey_type in HoneyType
            },
            "quality_distribution": {
                quality.value: len([a for a in all_artifacts if a.quality_level == quality])
                for quality in QualityLevel
            },
            "average_quality": sum(a.quality_score for a in all_artifacts) / len(all_artifacts) if all_artifacts else 0,
            "total_size_mb": sum(a.file_size for a in all_artifacts) / (1024 * 1024),
            "unique_nectars": len({a.nectar_id for a in all_artifacts}),
            "collection_history_files": len(list(self.collection_history_dir.glob("*.json"))),
        }

