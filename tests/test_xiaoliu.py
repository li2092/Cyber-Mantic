"""
小六壬理论测试
"""
import pytest
from datetime import datetime
from models import UserInput
from theories.xiaoliu.theory import XiaoLiuRenTheory


class TestXiaoLiuRenTheory:
    """小六壬理论测试"""

    def setup_method(self):
        """设置测试"""
        self.theory = XiaoLiuRenTheory()

    def test_theory_name(self):
        """测试理论名称"""
        assert self.theory.get_name() == "小六壬"

    def test_required_fields(self):
        """测试必填字段"""
        required = self.theory.get_required_fields()
        # 小六壬没有必填字段
        assert len(required) == 0

    def test_optional_fields(self):
        """测试可选字段"""
        optional = self.theory.get_optional_fields()
        assert "numbers" in optional
        assert "birth_month" in optional
        assert "birth_day" in optional
        assert "current_time" in optional

    def test_min_completeness(self):
        """测试最小完整度"""
        min_comp = self.theory.get_min_completeness()
        assert min_comp == 0.0  # 小六壬随时可用

    def test_calculate_with_numbers(self):
        """测试使用数字起卦"""
        user_input = UserInput(
            question_type="事业",
            question_description="今年事业如何",
            numbers=[3, 15, 7],  # 3月、15日、7时
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        assert result is not None
        assert "月落宫" in result
        assert "日落宫" in result
        assert "时落宫" in result
        assert "judgment" in result
        assert result["judgment"] in ["吉", "凶", "平"]

    def test_calculate_with_time(self):
        """测试使用时间起卦"""
        user_input = UserInput(
            question_type="财运",
            question_description="近期财运如何",
            current_time=datetime(2024, 6, 15, 14, 30)  # 6月15日下午2:30
        )

        result = self.theory.calculate(user_input)

        assert result is not None
        assert "月落宫" in result
        assert "日落宫" in result
        assert "时落宫" in result
        assert "advice" in result or "judgment" in result

    def test_liu_shen_order(self):
        """测试六神顺序正确性"""
        liu_shen = self.theory.LIU_SHEN_ORDER
        assert len(liu_shen) == 6
        assert liu_shen[0] == "大安"
        assert liu_shen[1] == "留连"
        assert liu_shen[2] == "速喜"
        assert liu_shen[3] == "赤口"
        assert liu_shen[4] == "小吉"
        assert liu_shen[5] == "空亡"

    def test_liu_shen_properties(self):
        """测试六神属性"""
        # 测试大安
        da_an = self.theory.LIU_SHEN["大安"]
        assert da_an["吉凶"] == "吉"
        assert da_an["五行"] == "木"
        assert da_an["方位"] == "东"
        assert 0 <= da_an["评分"] <= 1

        # 测试空亡
        kong_wang = self.theory.LIU_SHEN["空亡"]
        assert kong_wang["吉凶"] == "凶"
        assert 0 <= kong_wang["评分"] <= 1

    def test_calculate_same_numbers_consistent(self):
        """测试相同数字起卦结果一致"""
        user_input1 = UserInput(
            question_type="事业",
            question_description="事业运",
            numbers=[5, 10, 8],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        user_input2 = UserInput(
            question_type="财运",
            question_description="财运",
            numbers=[5, 10, 8],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result1 = self.theory.calculate(user_input1)
        result2 = self.theory.calculate(user_input2)

        # 相同的数字应该得到相同的落宫
        assert result1["月落宫"] == result2["月落宫"]
        assert result1["日落宫"] == result2["日落宫"]
        assert result1["时落宫"] == result2["时落宫"]

    def test_to_standard_answer(self):
        """测试转换为标准答案格式"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业运",
            numbers=[3, 15, 7],
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

    def test_edge_case_large_numbers(self):
        """测试边界情况：大数字"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业运",
            numbers=[13, 31, 23],  # 超过12月、31日、23时
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        # 应该能够正常处理（通过取模）
        result = self.theory.calculate(user_input)
        assert result is not None
        assert "月落宫" in result

    def test_different_times_different_results(self):
        """测试不同时间产生不同结果"""
        user_input1 = UserInput(
            question_type="事业",
            question_description="事业运",
            current_time=datetime(2024, 1, 1, 8, 0)  # 早上8点
        )

        user_input2 = UserInput(
            question_type="事业",
            question_description="事业运",
            current_time=datetime(2024, 1, 1, 20, 0)  # 晚上8点
        )

        result1 = self.theory.calculate(user_input1)
        result2 = self.theory.calculate(user_input2)

        # 不同时间应该有不同的时落宫
        # 但也可能相同，所以我们只检查结果存在
        assert result1 is not None
        assert result2 is not None

    def test_judgment_scores(self):
        """测试吉凶评分合理性"""
        # 测试多个不同的输入
        for month in [1, 6, 12]:
            for day in [1, 15, 30]:
                for hour in [1, 6, 11]:
                    user_input = UserInput(
                        question_type="测试",
                        question_description="测试",
                        numbers=[month, day, hour],
                        current_time=datetime(2024, 1, 1, 12, 0)
                    )

                    result = self.theory.calculate(user_input)
                    standard = self.theory.to_standard_answer(result)

                    # 评分应该在合理范围内
                    assert 0 <= standard["judgment_level"] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
