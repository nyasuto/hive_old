"""
Agent Mixins Tests

エージェントMixinクラスのテストスイート
"""

import unittest

from hive.agents.mixins import ErrorHandlingMixin, ValidationMixin, WorkLogMixin


class _TestMixinImplementation(ValidationMixin, ErrorHandlingMixin, WorkLogMixin):
    """テスト用のMixin実装クラス"""

    def __init__(self):
        self.worker_id = "test_worker"
        self.comb_api = None  # CombAPIは使用しない
        self.logger = None


class TestValidationMixin(unittest.TestCase):
    """ValidationMixinのテスト"""

    def setUp(self):
        self.mixin = _TestMixinImplementation()

    def test_validate_input_success(self):
        """入力検証成功テスト"""
        input_data = {"field1": "value1", "field2": "value2"}
        required_fields = ["field1", "field2"]

        result = self.mixin.validate_input(input_data, required_fields)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_input_missing_fields(self):
        """必須フィールド不足テスト"""
        input_data = {"field1": "value1"}
        required_fields = ["field1", "field2", "field3"]

        result = self.mixin.validate_input(input_data, required_fields)

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "field2" in str(result["errors"])
        assert "field3" in str(result["errors"])

    def test_validate_input_none_data(self):
        """None入力テスト"""
        input_data = None
        required_fields = ["field1"]

        result = self.mixin.validate_input(input_data, required_fields)

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_input_empty_required_fields(self):
        """必須フィールドなしテスト"""
        input_data = {"field1": "value1"}
        required_fields = []

        result = self.mixin.validate_input(input_data, required_fields)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_output_success(self):
        """出力検証成功テスト"""
        output_data = {"result": "success"}
        expected_type = dict

        result = self.mixin.validate_output(output_data, expected_type)

        assert result["valid"] is True
        assert result["type_match"] is True
        assert len(result["errors"]) == 0

    def test_validate_output_type_mismatch(self):
        """出力型不一致テスト"""
        output_data = "string_instead_of_dict"
        expected_type = dict

        result = self.mixin.validate_output(output_data, expected_type)

        assert result["valid"] is False
        assert result["type_match"] is False
        assert len(result["errors"]) > 0


class TestErrorHandlingMixin(unittest.TestCase):
    """ErrorHandlingMixinのテスト"""

    def setUp(self):
        self.mixin = _TestMixinImplementation()

    def test_handle_exception(self):
        """例外処理テスト"""
        test_exception = ValueError("Test error message")
        context = "test_method"

        result = self.mixin.handle_exception(test_exception, context)

        assert result["error_type"] == "ValueError"
        assert result["error_message"] == "Test error message"
        assert result["context"] == "test_method"
        assert result["handled"] is True

    def test_create_error_response(self):
        """エラーレスポンス作成テスト"""
        error_message = "Test error occurred"

        result = self.mixin.create_error_response(error_message)

        assert result["success"] is False
        assert result["error"]["message"] == error_message
        assert result["error"]["code"] == "UNKNOWN_ERROR"
        assert "timestamp" in result["error"]

    def test_create_success_response(self):
        """成功レスポンス作成テスト"""
        data = {"result": "success", "value": 42}

        result = self.mixin.create_success_response(data)

        assert result["success"] is True
        assert result["data"]["result"] == "success"
        assert result["data"]["value"] == 42
        assert "timestamp" in result

    def test_create_success_response_none_data(self):
        """成功レスポンス作成テスト（データなし）"""
        result = self.mixin.create_success_response(None)

        assert result["success"] is True
        assert "data" not in result
        assert "timestamp" in result


class TestWorkLogMixin(unittest.TestCase):
    """WorkLogMixinのテスト"""

    def setUp(self):
        self.mixin = _TestMixinImplementation()

    def test_add_technical_decision(self):
        """技術的決定追加テスト - CombAPIが無い場合はFalseを返す"""
        result = self.mixin.add_technical_decision(
            "Database Choice",
            "Selected PostgreSQL for data persistence",
            ["MySQL", "MongoDB", "SQLite"],
        )

        # CombAPIが無い場合はFalseを返すことを確認
        assert result is False

    def test_add_challenge(self):
        """課題追加テスト - CombAPIが無い場合はFalseを返す"""
        result = self.mixin.add_challenge(
            "Performance bottleneck in data processing",
            "Investigating optimization strategies",
        )

        # CombAPIが無い場合はFalseを返すことを確認
        assert result is False

    def test_add_metrics(self):
        """メトリクス追加テスト - CombAPIが無い場合はFalseを返す"""
        metrics = {"performance": 95, "errors": 0}

        result = self.mixin.add_metrics(metrics)

        # CombAPIが無い場合はFalseを返すことを確認
        assert result is False

    def test_get_current_task(self):
        """現在のタスク取得テスト - CombAPIが無い場合はNoneを返す"""
        result = self.mixin.get_current_task()

        # CombAPIが無い場合はNoneを返すことを確認
        assert result is None


if __name__ == "__main__":
    unittest.main()
