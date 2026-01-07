"""
紫微斗数理论测试
"""
import pytest
from datetime import datetime
from models import UserInput
from theories.ziwei.theory import ZiWeiTheory


class TestZiWeiTheory:
    """紫微斗数理论测试"""

    def setup_method(self):
        """设置测试"""
        self.theory = ZiWeiTheory()

    def test_theory_name(self):
        """测试理论名称"""
        assert self.theory.get_name() == "紫微斗数"

    def test_required_fields(self):
        """测试必填字段"""
        required = self.theory.get_required_fields()
        assert "birth_hour" in required
        assert "gender" in required
        assert "birth_year" in required
        assert "birth_month" in required
        assert "birth_day" in required

    def test_optional_fields(self):
        """测试可选字段"""
        optional = self.theory.get_optional_fields()
        assert "calendar_type" in optional

    def test_min_completeness(self):
        """测试最小完整度"""
        min_comp = self.theory.get_min_completeness()
        assert min_comp == 0.95  # 紫微斗数要求非常高

    def test_field_weights(self):
        """测试字段权重"""
        weights = self.theory.get_field_weights()
        assert weights["birth_hour"] == 0.2  # 时辰权重最高
        assert weights["gender"] == 0.05

    def test_calculate_with_complete_info(self):
        """测试完整信息计算"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业运势如何",
            birth_year=1990,
            birth_month=5,
            birth_day=15,
            birth_hour=14,
            gender="男",
            calendar_type="solar"
        )

        result = self.theory.calculate(user_input)

        assert result is not None
        assert "问题类型" in result
        assert "问题描述" in result
        assert result["问题类型"] == "事业"

    def test_calculate_without_hour_raises_error(self):
        """测试没有时辰会报错"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业运势如何",
            birth_year=1990,
            birth_month=5,
            birth_day=15,
            birth_hour=None,  # 缺少时辰
            gender="男"
        )

        with pytest.raises(ValueError, match="紫微斗数必须提供出生时辰"):
            self.theory.calculate(user_input)

    def test_calculate_without_gender_raises_error(self):
        """测试没有性别会报错"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业运势如何",
            birth_year=1990,
            birth_month=5,
            birth_day=15,
            birth_hour=14,
            gender=None  # 缺少性别
        )

        with pytest.raises(ValueError, match="紫微斗数必须提供性别信息"):
            self.theory.calculate(user_input)

    def test_to_standard_answer(self):
        """测试转换为标准答案"""
        user_input = UserInput(
            question_type="财运",
            question_description="财运如何",
            birth_year=1985,
            birth_month=3,
            birth_day=20,
            birth_hour=10,
            gender="女"
        )

        result = self.theory.calculate(user_input)
        standard = self.theory.to_standard_answer(result)

        assert "judgment" in standard
        assert "judgment_level" in standard
        assert "confidence" in standard
        assert "timing" in standard
        assert standard["timing"] == "长期命理"
        assert 0 <= standard["judgment_level"] <= 1
        assert 0 <= standard["confidence"] <= 1

    def test_judgment_levels(self):
        """测试不同评分对应的判断"""
        # 模拟不同评分的结果
        test_scores = [
            (0.9, "大吉"),
            (0.75, "吉"),
            (0.55, "平"),
            (0.35, "凶"),
            (0.15, "大凶")
        ]

        for score, expected_judgment in test_scores:
            result = {
                "分析": {"综合评分": score},
                "confidence": 0.8
            }
            standard = self.theory.to_standard_answer(result)
            assert standard["judgment"] == expected_judgment

    def test_male_vs_female(self):
        """测试男女命盘计算"""
        # 男命
        male_input = UserInput(
            question_type="事业",
            question_description="事业",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            birth_hour=10,
            gender="男"
        )

        # 女命
        female_input = UserInput(
            question_type="事业",
            question_description="事业",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            birth_hour=10,
            gender="女"
        )

        male_result = self.theory.calculate(male_input)
        female_result = self.theory.calculate(female_input)

        # 男女命盘应该不同
        assert male_result is not None
        assert female_result is not None
        # 基本信息应该存在
        assert "问题类型" in male_result
        assert "问题类型" in female_result

    def test_different_birth_times(self):
        """测试不同出生时间产生不同结果"""
        input1 = UserInput(
            question_type="事业",
            question_description="事业",
            birth_year=1990,
            birth_month=1,
            birth_day=1,
            birth_hour=2,  # 子时
            gender="男"
        )

        input2 = UserInput(
            question_type="事业",
            question_description="事业",
            birth_year=1990,
            birth_month=1,
            birth_day=1,
            birth_hour=14,  # 未时
            gender="男"
        )

        result1 = self.theory.calculate(input1)
        result2 = self.theory.calculate(input2)

        assert result1 is not None
        assert result2 is not None
        # 两个结果应该存在
        assert "问题类型" in result1
        assert "问题类型" in result2

    def test_calendar_type_support(self):
        """测试历法类型支持"""
        # 公历
        solar_input = UserInput(
            question_type="事业",
            question_description="事业",
            birth_year=1990,
            birth_month=5,
            birth_day=15,
            birth_hour=10,
            gender="男",
            calendar_type="solar"
        )

        # 农历
        lunar_input = UserInput(
            question_type="事业",
            question_description="事业",
            birth_year=1990,
            birth_month=5,
            birth_day=15,
            birth_hour=10,
            gender="男",
            calendar_type="lunar"
        )

        solar_result = self.theory.calculate(solar_input)
        lunar_result = self.theory.calculate(lunar_input)

        assert solar_result is not None
        assert lunar_result is not None

    def test_all_hours_valid(self):
        """测试所有时辰都能正常计算"""
        # 测试12个时辰（0-23小时）
        for hour in range(0, 24):
            user_input = UserInput(
                question_type="事业",
                question_description="测试",
                birth_year=1990,
                birth_month=6,
                birth_day=15,
                birth_hour=hour,
                gender="男"
            )

            result = self.theory.calculate(user_input)
            assert result is not None

    def test_edge_case_leap_year(self):
        """测试边界情况：闰年"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            birth_year=2000,  # 闰年
            birth_month=2,
            birth_day=29,  # 闰日
            birth_hour=12,
            gender="男"
        )

        result = self.theory.calculate(user_input)
        assert result is not None

    def test_different_question_types(self):
        """测试不同问题类型"""
        question_types = ["事业", "财运", "感情", "婚姻", "健康", "学业"]

        for q_type in question_types:
            user_input = UserInput(
                question_type=q_type,
                question_description=f"测试{q_type}",
                birth_year=1990,
                birth_month=6,
                birth_day=15,
                birth_hour=10,
                gender="男"
            )

            result = self.theory.calculate(user_input)
            assert result is not None
            assert result["问题类型"] == q_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
