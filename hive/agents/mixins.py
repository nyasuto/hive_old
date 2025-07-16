"""
Agent Mixins

エージェントが共通で使用する機能をMixinとして提供します。
"""

import logging
from typing import Any

from comb.api import CombAPI
from comb.message_router import Message, MessagePriority


class LoggingMixin:
    """ログ機能のMixin"""

    def setup_logger(self, logger_name: str) -> None:
        """ログ設定"""
        self.logger = logging.getLogger(logger_name)

    def log_info(self, message: str) -> None:
        """情報ログ"""
        if hasattr(self, "logger"):
            self.logger.info(message)

    def log_warning(self, message: str) -> None:
        """警告ログ"""
        if hasattr(self, "logger"):
            self.logger.warning(message)

    def log_error(self, message: str, exc_info: bool = False) -> None:
        """エラーログ"""
        if hasattr(self, "logger"):
            self.logger.error(message, exc_info=exc_info)


class CommunicationMixin:
    """通信機能のMixin"""

    def setup_communication(self, worker_id: str) -> None:
        """通信設定"""
        self.comb_api = CombAPI(worker_id)
        self.worker_id = worker_id

    def send_notification(
        self,
        to_worker: str,
        content: dict[str, Any],
        priority: MessagePriority = MessagePriority.MEDIUM,
    ) -> bool:
        """通知送信"""
        return self.comb_api.send_notification(to_worker, content, priority)

    def send_error_notification(
        self,
        to_worker: str,
        error_message: str,
        error_details: dict[str, Any] | None = None,
    ) -> bool:
        """エラー通知送信"""
        return self.comb_api.send_error(to_worker, error_message, error_details)

    def ping_worker(self, worker_id: str) -> bool:
        """Worker ping"""
        return self.comb_api.ping(worker_id)

    def handle_ping(self, message: Message) -> bool:
        """Ping応答"""
        return self.comb_api.pong(message)


class WorkLogMixin:
    """作業ログ機能のMixin"""

    def add_technical_decision(
        self, decision: str, reasoning: str, alternatives: list[str] | None = None
    ) -> bool:
        """技術的決定記録"""
        if hasattr(self, "comb_api"):
            return self.comb_api.add_technical_decision(
                decision, reasoning, alternatives
            )
        return False

    def add_challenge(self, challenge: str, solution: str | None = None) -> bool:
        """課題記録"""
        if hasattr(self, "comb_api"):
            return self.comb_api.add_challenge(challenge, solution)
        return False

    def add_metrics(self, metrics: dict[str, Any]) -> bool:
        """メトリクス記録"""
        if hasattr(self, "comb_api"):
            return self.comb_api.add_metrics(metrics)
        return False

    def get_current_task(self) -> dict[str, Any] | None:
        """現在のタスク情報取得"""
        if hasattr(self, "comb_api"):
            return self.comb_api.get_current_task()
        return None


class ValidationMixin:
    """検証機能のMixin"""

    def validate_input(
        self, input_data: Any, required_fields: list[str]
    ) -> dict[str, Any]:
        """入力検証"""
        validation_result = {"valid": True, "errors": [], "missing_fields": []}

        if not isinstance(input_data, dict):
            validation_result["valid"] = False
            validation_result["errors"].append("Input must be a dictionary")
            return validation_result

        for field in required_fields:
            if field not in input_data:
                validation_result["valid"] = False
                validation_result["missing_fields"].append(field)

        if validation_result["missing_fields"]:
            validation_result["errors"].append(
                f"Missing required fields: {validation_result['missing_fields']}"
            )

        return validation_result

    def validate_output(
        self, output_data: Any, expected_type: type = dict
    ) -> dict[str, Any]:
        """出力検証"""
        validation_result = {"valid": True, "errors": [], "type_match": True}

        if not isinstance(output_data, expected_type):
            validation_result["valid"] = False
            validation_result["type_match"] = False
            validation_result["errors"].append(
                f"Expected {expected_type.__name__}, got {type(output_data).__name__}"
            )

        return validation_result


class ErrorHandlingMixin:
    """エラーハンドリング機能のMixin"""

    def handle_exception(
        self, exception: Exception, context: str = ""
    ) -> dict[str, Any]:
        """例外処理"""
        error_info = {
            "error_type": type(exception).__name__,
            "error_message": str(exception),
            "context": context,
            "handled": True,
        }

        if hasattr(self, "logger"):
            self.logger.error(f"Exception in {context}: {exception}", exc_info=True)

        return error_info

    def create_error_response(
        self, error_message: str, error_code: str = "UNKNOWN_ERROR"
    ) -> dict[str, Any]:
        """エラーレスポンス作成"""
        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": error_message,
                "timestamp": "2025-01-01T00:00:00",  # 実際の実装では現在時刻を使用
            },
        }

    def create_success_response(self, data: Any = None) -> dict[str, Any]:
        """成功レスポンス作成"""
        response = {
            "success": True,
            "timestamp": "2025-01-01T00:00:00",  # 実際の実装では現在時刻を使用
        }

        if data is not None:
            response["data"] = data

        return response
