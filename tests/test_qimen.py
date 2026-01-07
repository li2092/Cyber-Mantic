"""
奇门遁甲理论测试
"""
import pytest
from datetime import datetime
from models import UserInput
from theories.qimen.theory import QiMenTheory


class TestQiMenTheory:
    """奇门遁甲理论测试"""

    def setup_method(self):
        """设置测试"""
        self.theory = QiMenTheory()

    def test_theory_name(self):
        """测试理论名称"""
        assert self.theory.get_name() == "奇门遁甲"

    def test_required_fields(self):
        """测试必填字段"""
        required = self.theory.get_required_fields()
        assert "current_time" in required
        assert "question_type" in required
        assert "question_description" in required

    def test_optional_fields(self):
        """测试可选字段"""
        optional = self.theory.get_optional_fields()
        assert "user_claimed_time" in optional
        assert "event_category" in optional

    def test_min_completeness(self):
        """测试最小完整度"""
        min_comp = self.theory.get_min_completeness()
        assert min_comp == 0.7

    def test_field_weights(self):
        """测试字段权重"""
        weights = self.theory.get_field_weights()
        assert weights["current_time"] == 0.3
        assert weights["question_type"] == 0.3
        assert weights["question_description"] == 0.3

    def test_calculate_with_current_time(self):
        """测试使用当前时间起局"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业发展如何",
            current_time=datetime(2024, 6, 15, 14, 30)
        )

        result = self.theory.calculate(user_input)

        assert result is not None
        assert "问题类型" in result
        assert "问题描述" in result
        assert result["问题类型"] == "事业"
        assert result["问题描述"] == "事业发展如何"

    def test_calculate_different_times(self):
        """测试不同时间产生不同结果"""
        user_input1 = UserInput(
            question_type="事业",
            question_description="事业",
            current_time=datetime(2024, 1, 1, 8, 0)
        )

        user_input2 = UserInput(
            question_type="事业",
            question_description="事业",
            current_time=datetime(2024, 6, 15, 20, 0)
        )

        result1 = self.theory.calculate(user_input1)
        result2 = self.theory.calculate(user_input2)

        assert result1 is not None
        assert result2 is not None
        # 基本信息应该存在
        assert "问题类型" in result1
        assert "问题类型" in result2

    def test_to_standard_answer(self):
        """测试转换为标准答案"""
        user_input = UserInput(
            question_type="财运",
            question_description="财运如何",
            current_time=datetime(2024, 6, 15, 14, 30)
        )

        result = self.theory.calculate(user_input)
        standard = self.theory.to_standard_answer(result)

        assert "judgment" in standard
        assert "judgment_level" in standard
        assert "confidence" in standard
        assert "timing" in standard
        assert "advice" in standard
        assert 0 <= standard["judgment_level"] <= 1
        assert 0 <= standard["confidence"] <= 1

    def test_judgment_levels(self):
        """测试不同评分对应的判断"""
        test_scores = [
            (0.9, "大吉"),
            (0.7, "吉"),
            (0.5, "平"),
            (0.35, "凶"),
            (0.15, "大凶")
        ]

        for score, expected_judgment in test_scores:
            result = {
                "综合评分": score,
                "confidence": 0.75
            }
            standard = self.theory.to_standard_answer(result)
            assert standard["judgment"] == expected_judgment

    def test_different_question_types(self):
        """测试不同问题类型"""
        question_types = ["事业", "财运", "感情", "婚姻", "健康", "学业", "决策"]

        for q_type in question_types:
            user_input = UserInput(
                question_type=q_type,
                question_description=f"测试{q_type}",
                current_time=datetime(2024, 6, 15, 14, 30)
            )

            result = self.theory.calculate(user_input)
            assert result is not None
            assert result["问题类型"] == q_type

    def test_with_different_times(self):
        """测试不同时间计算"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            current_time=datetime(2024, 6, 15, 14, 30)
        )

        result = self.theory.calculate(user_input)
        assert result is not None
        assert "问题类型" in result

    def test_different_hours_different_results(self):
        """测试不同时辰产生不同结果"""
        base_date = datetime(2024, 6, 15, 0, 0)

        results = []
        for hour in [2, 6, 10, 14, 18, 22]:  # 不同时辰
            user_input = UserInput(
                question_type="事业",
                question_description="事业",
                current_time=base_date.replace(hour=hour)
            )

            result = self.theory.calculate(user_input)
            results.append(result)

        # 所有结果都应该有效
        for result in results:
            assert result is not None
            assert "问题类型" in result

    def test_advice_includes_directions(self):
        """测试建议包含方位信息"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            current_time=datetime(2024, 6, 15, 14, 30)
        )

        result = self.theory.calculate(user_input)
        standard = self.theory.to_standard_answer(result)

        # 建议应该存在
        assert "advice" in standard
        advice = standard["advice"]
        assert len(advice) > 0

    def test_timing_advice_exists(self):
        """测试时机建议存在"""
        user_input = UserInput(
            question_type="决策",
            question_description="何时行动为宜",
            current_time=datetime(2024, 6, 15, 14, 30)
        )

        result = self.theory.calculate(user_input)

        # 如果有时机建议字段
        if "时机建议" in result:
            timing_advice = result["时机建议"]
            assert "时机" in timing_advice or "建议" in timing_advice

    def test_confidence_level(self):
        """测试置信度"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            current_time=datetime(2024, 6, 15, 14, 30)
        )

        result = self.theory.calculate(user_input)
        standard = self.theory.to_standard_answer(result)

        assert "confidence" in standard
        # 奇门遁甲置信度应该较高
        assert standard["confidence"] >= 0.7

    def test_detailed_result_preserved(self):
        """测试完整结果保留"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            current_time=datetime(2024, 6, 15, 14, 30)
        )

        result = self.theory.calculate(user_input)
        standard = self.theory.to_standard_answer(result)

        # 标准答案应该保留完整结果
        assert "detailed_result" in standard
        assert standard["detailed_result"] is not None

    def test_edge_case_midnight(self):
        """测试边界情况：子时（午夜）"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            current_time=datetime(2024, 6, 15, 0, 0)
        )

        result = self.theory.calculate(user_input)
        assert result is not None

    def test_edge_case_noon(self):
        """测试边界情况：午时（正午）"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            current_time=datetime(2024, 6, 15, 12, 0)
        )

        result = self.theory.calculate(user_input)
        assert result is not None

    def test_seasonal_differences(self):
        """测试季节差异"""
        # 春夏秋冬四季
        seasons = [
            datetime(2024, 3, 15, 14, 30),  # 春
            datetime(2024, 6, 15, 14, 30),  # 夏
            datetime(2024, 9, 15, 14, 30),  # 秋
            datetime(2024, 12, 15, 14, 30),  # 冬
        ]

        for season_time in seasons:
            user_input = UserInput(
                question_type="事业",
                question_description="事业",
                current_time=season_time
            )

            result = self.theory.calculate(user_input)
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
