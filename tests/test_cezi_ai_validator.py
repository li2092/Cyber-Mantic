"""
测字术AI验证器测试
"""
import pytest
from theories.cezi.ai_validator import CeZiAIValidator, get_cezi_validator
from theories.cezi.calculator import CeZiCalculator


class TestCeZiAIValidator:
    """测字术AI验证器测试"""

    def test_validator_singleton(self):
        """测试验证器单例"""
        validator1 = get_cezi_validator()
        validator2 = get_cezi_validator()
        assert validator1 is validator2

    def test_validator_initialization(self):
        """测试验证器初始化"""
        validator = CeZiAIValidator()
        assert validator is not None
        assert validator.logger is not None

    def test_compare_results_consistent(self):
        """测试对比结果：一致的情况"""
        validator = CeZiAIValidator()

        ai_result = {
            "stroke_count": 10,
            "structure": "左右"
        }

        is_consistent, differences = validator._compare_results(
            code_stroke_count=10,
            code_structure="左右",
            ai_result=ai_result
        )

        assert is_consistent is True
        assert len(differences) == 0

    def test_compare_results_stroke_diff(self):
        """测试对比结果：笔画数不同"""
        validator = CeZiAIValidator()

        ai_result = {
            "stroke_count": 12,
            "structure": "左右"
        }

        is_consistent, differences = validator._compare_results(
            code_stroke_count=10,
            code_structure="左右",
            ai_result=ai_result
        )

        assert is_consistent is False
        assert "stroke_count" in differences
        assert "代码=10" in differences["stroke_count"]
        assert "AI=12" in differences["stroke_count"]

    def test_compare_results_structure_diff(self):
        """测试对比结果：结构不同"""
        validator = CeZiAIValidator()

        ai_result = {
            "stroke_count": 10,
            "structure": "上下"
        }

        is_consistent, differences = validator._compare_results(
            code_stroke_count=10,
            code_structure="左右",
            ai_result=ai_result
        )

        assert is_consistent is False
        assert "structure" in differences
        assert "代码=左右" in differences["structure"]
        assert "AI=上下" in differences["structure"]

    def test_compare_results_stroke_exact_match_required(self):
        """测试对比结果：笔画数要求完全一致"""
        validator = CeZiAIValidator()

        # 差1画也应该认为不一致（要求绝对准确）
        ai_result = {
            "stroke_count": 11,
            "structure": "左右"
        }

        is_consistent, differences = validator._compare_results(
            code_stroke_count=10,
            code_structure="左右",
            ai_result=ai_result
        )

        assert is_consistent is False
        assert "stroke_count" in differences

    def test_compare_results_both_diff(self):
        """测试对比结果：笔画和结构都不同"""
        validator = CeZiAIValidator()

        ai_result = {
            "stroke_count": 15,
            "structure": "包围"
        }

        is_consistent, differences = validator._compare_results(
            code_stroke_count=10,
            code_structure="左右",
            ai_result=ai_result
        )

        assert is_consistent is False
        assert "stroke_count" in differences
        assert "structure" in differences


class TestCeZiCalculatorWithAI:
    """测字术计算器AI集成测试"""

    def test_calculator_init_with_ai(self):
        """测试计算器初始化（启用AI）"""
        calculator = CeZiCalculator(use_ai_validation=True)
        assert calculator.use_ai_validation is True
        assert calculator.validator is not None

    def test_calculator_init_without_ai(self):
        """测试计算器初始化（禁用AI）"""
        calculator = CeZiCalculator(use_ai_validation=False)
        assert calculator.use_ai_validation is False
        assert calculator.validator is None

    def test_analyze_character_without_ai(self):
        """测试字符分析（禁用AI）"""
        calculator = CeZiCalculator(use_ai_validation=False)

        result = calculator.analyze_character("好", "测好字")

        assert result is not None
        assert result["测字"] == "好"
        assert "基本信息" in result
        assert "笔画分析" in result
        assert "结构分析" in result
        assert "AI验证" in result["基本信息"]
        assert result["基本信息"]["AI验证"] is False

    def test_analyze_character_common_chars(self):
        """测试常见汉字分析（无AI）"""
        calculator = CeZiCalculator(use_ai_validation=False)

        # 测试几个常见字
        test_chars = ["好", "福", "喜", "吉", "凶"]

        for char in test_chars:
            result = calculator.analyze_character(char, f"测{char}字")
            assert result is not None
            assert result["测字"] == char
            assert result["基本信息"]["笔画数"] > 0
            assert result["吉凶判断"] in ["吉", "凶", "平"]
            assert 0 <= result["综合评分"] <= 1

    def test_analyze_split_with_ai_parts(self):
        """测试拆字分析（有AI部件）"""
        calculator = CeZiCalculator(use_ai_validation=False)

        # 模拟有AI拆字部件的情况
        splits = calculator._analyze_split("好", ["女", "子"])

        assert len(splits) > 0
        assert any("AI拆字" in s.get("方法", "") for s in splits)
        first_split = splits[0]
        assert "女" in first_split.get("部件", "")
        assert "子" in first_split.get("部件", "")

    def test_analyze_split_without_ai_parts(self):
        """测试拆字分析（无AI部件）"""
        calculator = CeZiCalculator(use_ai_validation=False)

        splits = calculator._analyze_split("好", None)

        assert len(splits) > 0
        # 应该有传统的拆字方法
        methods = [s.get("方法", "") for s in splits]
        assert "观形" in methods or "取象" in methods

    def test_analyze_structure_with_type(self):
        """测试指定结构类型的分析"""
        calculator = CeZiCalculator(use_ai_validation=False)

        # 测试不同的结构类型
        structures = ["左右", "上下", "包围", "半包围", "独体"]

        for structure in structures:
            result = calculator._analyze_structure_with_type("测", structure)
            assert result["结构类型"] == structure
            assert "吉凶" in result
            assert "说明" in result

    def test_empty_character(self):
        """测试空字符输入"""
        calculator = CeZiCalculator(use_ai_validation=False)

        result = calculator.analyze_character("", "")

        assert result is not None
        assert result["测字"] == ""
        assert "错误" in result
        assert result["吉凶判断"] == "平"

    def test_multi_character_input(self):
        """测试多字符输入（只取第一个）"""
        calculator = CeZiCalculator(use_ai_validation=False)

        result = calculator.analyze_character("好事", "测好事")

        assert result is not None
        assert result["测字"] == "好"  # 只取第一个字


class TestCeZiAIValidatorIntegration:
    """测字术AI验证器集成测试（需要API）"""

    @pytest.mark.skip(reason="需要真实的API调用，跳过以避免API成本")
    async def test_validate_character_async_real_api(self):
        """测试异步验证（真实API调用）"""
        validator = CeZiAIValidator()

        result = await validator.validate_character_async(
            character="好",
            code_stroke_count=6,
            code_structure="左右"
        )

        assert result is not None
        assert "validation_success" in result
        assert "final_stroke_count" in result
        assert "final_structure" in result

    @pytest.mark.skip(reason="需要真实的API调用，跳过以避免API成本")
    def test_validate_character_sync_real_api(self):
        """测试同步验证（真实API调用）"""
        validator = CeZiAIValidator()

        result = validator.validate_character(
            character="好",
            code_stroke_count=6,
            code_structure="左右"
        )

        assert result is not None
        assert "validation_success" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
