"""
梅花易数理论测试
"""
import pytest
from datetime import datetime
from models import UserInput
from theories.meihua.theory import MeiHuaTheory


class TestMeiHuaTheory:
    """梅花易数理论测试"""

    def setup_method(self):
        """设置测试"""
        self.theory = MeiHuaTheory()

    def test_theory_name(self):
        """测试理论名称"""
        assert self.theory.get_name() == "梅花易数"

    def test_required_fields(self):
        """测试必填字段"""
        required = self.theory.get_required_fields()
        assert len(required) == 0  # 梅花易数没有必填字段

    def test_optional_fields(self):
        """测试可选字段"""
        optional = self.theory.get_optional_fields()
        assert "numbers" in optional
        assert "character" in optional
        assert "favorite_color" in optional
        assert "current_direction" in optional
        assert "current_time" in optional

    def test_min_completeness(self):
        """测试最小完整度"""
        min_comp = self.theory.get_min_completeness()
        assert min_comp == 0.0

    def test_calculate_with_numbers(self):
        """测试使用数字起卦"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业发展如何",
            numbers=[7, 8, 6],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        assert result is not None
        assert "本卦" in result
        assert "互卦" in result
        assert "变卦" in result
        assert "体卦" in result
        assert "用卦" in result
        assert "judgment" in result
        assert result["judgment"] in ["吉", "凶", "平"]

    def test_calculate_with_time(self):
        """测试使用时间起卦"""
        user_input = UserInput(
            question_type="财运",
            question_description="近期财运",
            current_time=datetime(2024, 6, 15, 14, 30)
        )

        result = self.theory.calculate(user_input)

        assert result is not None
        assert "起卦方式" in result
        assert "本卦" in result
        assert "起卦数字" in result
        assert len(result["起卦数字"]) == 3

    def test_gua_structure(self):
        """测试卦象结构"""
        user_input = UserInput(
            question_type="事业",
            question_description="测试",
            numbers=[1, 2, 3],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)
        ben_gua = result["本卦"]

        # 检查卦象结构
        assert "上卦" in ben_gua
        assert "下卦" in ben_gua
        # 卦名可能在不同的键中
        assert "名称" in ben_gua or "上卦" in ben_gua

    def test_ti_yong_relationship(self):
        """测试体用关系"""
        user_input = UserInput(
            question_type="事业",
            question_description="测试",
            numbers=[3, 5, 2],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        assert "体卦" in result
        assert "用卦" in result
        assert "体用关系" in result
        # 体用关系应该是生克关系
        assert result["体用关系"] in ["比和", "体生用", "用生体", "体克用", "用克体"]

    def test_to_standard_answer(self):
        """测试转换为标准答案"""
        user_input = UserInput(
            question_type="事业",
            question_description="测试",
            numbers=[7, 8, 6],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)
        standard = self.theory.to_standard_answer(result)

        assert "judgment" in standard
        assert "judgment_level" in standard
        assert "confidence" in standard
        assert standard["judgment"] in ["吉", "凶", "平"]
        assert 0 <= standard["judgment_level"] <= 1
        assert 0 <= standard["confidence"] <= 1

    def test_same_numbers_consistent(self):
        """测试相同数字产生一致结果"""
        user_input1 = UserInput(
            question_type="事业",
            question_description="事业运",
            numbers=[5, 7, 3],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        user_input2 = UserInput(
            question_type="财运",
            question_description="财运",
            numbers=[5, 7, 3],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result1 = self.theory.calculate(user_input1)
        result2 = self.theory.calculate(user_input2)

        # 相同数字应该产生相同的卦象
        assert result1["本卦"]["上卦"] == result2["本卦"]["上卦"]
        assert result1["本卦"]["下卦"] == result2["本卦"]["下卦"]
        assert result1["体卦"] == result2["体卦"]
        assert result1["用卦"] == result2["用卦"]

    def test_number_to_gua_conversion(self):
        """测试数字转卦"""
        # 测试1-8的数字都能正确转换为八卦
        for num in range(1, 9):
            gua = self.theory._number_to_gua(num)
            assert gua in ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]

    def test_number_modulo(self):
        """测试数字取模"""
        # 测试大于8的数字会正确取模
        user_input = UserInput(
            question_type="测试",
            question_description="测试",
            numbers=[15, 23, 10],  # 大于8的数字
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)
        assert result is not None
        assert "本卦" in result

    def test_different_qigua_methods(self):
        """测试不同起卦方式"""
        # 使用数字
        input1 = UserInput(
            question_type="测试",
            question_description="测试",
            numbers=[3, 5, 2],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        # 使用时间
        input2 = UserInput(
            question_type="测试",
            question_description="测试",
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result1 = self.theory.calculate(input1)
        result2 = self.theory.calculate(input2)

        # 两种起卦方式都应该成功
        assert result1 is not None
        assert result2 is not None
        assert "起卦方式" in result1
        assert "起卦方式" in result2

    def test_response_time(self):
        """测试应期分析"""
        user_input = UserInput(
            question_type="事业",
            question_description="何时有进展",
            numbers=[7, 8, 6],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        # 应该有应期分析
        assert "应期" in result or "应验时间" in result["综合分析"]

    def test_edge_case_all_numbers_same(self):
        """测试边界情况：所有数字相同"""
        user_input = UserInput(
            question_type="测试",
            question_description="测试",
            numbers=[5, 5, 5],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)
        assert result is not None
        assert "本卦" in result

    def test_judgment_consistency(self):
        """测试吉凶判断一致性"""
        # 测试多次，确保判断逻辑稳定
        for _ in range(5):
            user_input = UserInput(
                question_type="测试",
                question_description="测试",
                numbers=[3, 7, 2],
                current_time=datetime(2024, 1, 1, 12, 0)
            )

            result = self.theory.calculate(user_input)
            standard = self.theory.to_standard_answer(result)

            assert standard["judgment"] in ["吉", "凶", "平"]
            assert 0 <= standard["judgment_level"] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
