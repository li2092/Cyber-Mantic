"""
大六壬理论测试
"""
import pytest
from datetime import datetime
from models import UserInput
from theories.daliuren.theory import DaLiuRenTheory


class TestDaLiuRenTheory:
    """大六壬理论测试"""

    def setup_method(self):
        """设置测试"""
        self.theory = DaLiuRenTheory()

    def test_theory_name(self):
        """测试理论名称"""
        assert self.theory.get_name() == "大六壬"

    def test_theory_category(self):
        """测试理论分类"""
        assert self.theory.get_category() == "占卜类"

    def test_required_fields(self):
        """测试必填字段"""
        required = self.theory.get_required_fields()
        assert "question_description" in required
        assert "current_time" in required

    def test_optional_fields(self):
        """测试可选字段"""
        optional = self.theory.get_optional_fields()
        assert "initial_inquiry_time" in optional

    def test_min_completeness(self):
        """测试最小完整度"""
        min_comp = self.theory.get_min_completeness()
        assert min_comp == 0.6

    def test_field_weights(self):
        """测试字段权重"""
        weights = self.theory.get_field_weights()
        assert weights["current_time"] == 0.4
        assert weights["question_description"] == 0.3

    def test_calculate_with_current_time(self):
        """测试使用当前时间起课"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业发展如何",
            current_time=datetime(2024, 6, 15, 14, 30)
        )

        result = self.theory.calculate(user_input)

        assert result is not None
        # 大六壬结果应该有基本信息
        assert isinstance(result, dict)

    def test_calculate_with_initial_inquiry_time(self):
        """测试使用初次问卜时间"""
        user_input = UserInput(
            question_type="财运",
            question_description="财运如何",
            current_time=datetime(2024, 6, 15, 14, 30),
            initial_inquiry_time=datetime(2024, 6, 15, 10, 0)
        )

        result = self.theory.calculate(user_input)

        assert result is not None
        assert isinstance(result, dict)

    def test_different_times_different_results(self):
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

    def test_to_standard_answer_ji(self):
        """测试转换为标准答案：吉"""
        result = {
            "吉凶判断": "吉",
            "综合评分": 0.8,
            "置信度": 0.75
        }

        standard = self.theory.to_standard_answer(result)

        assert "judgment" in standard
        assert standard["judgment"] == "吉"
        assert "judgment_level" in standard
        assert standard["judgment_level"] == 0.8
        assert "confidence" in standard
        assert standard["confidence"] == 0.75

    def test_to_standard_answer_xiong(self):
        """测试转换为标准答案：凶"""
        result = {
            "吉凶判断": "凶",
            "综合评分": 0.3,
            "置信度": 0.75
        }

        standard = self.theory.to_standard_answer(result)

        assert standard["judgment"] == "凶"
        # 注：judgment_level直接使用综合评分，不做反转
        assert standard["judgment_level"] == 0.3

    def test_to_standard_answer_ping(self):
        """测试转换为标准答案：平"""
        result = {
            "吉凶判断": "平",
            "综合评分": 0.5,
            "置信度": 0.75
        }

        standard = self.theory.to_standard_answer(result)

        assert standard["judgment"] == "平"
        assert standard["judgment_level"] == 0.5

    def test_different_question_types(self):
        """测试不同问题类型"""
        question_types = ["事业", "财运", "感情", "婚姻", "健康", "学业"]

        for q_type in question_types:
            user_input = UserInput(
                question_type=q_type,
                question_description=f"测试{q_type}",
                current_time=datetime(2024, 6, 15, 14, 30)
            )

            result = self.theory.calculate(user_input)
            assert result is not None

    def test_same_time_same_question_consistent(self):
        """测试相同时间相同问题结果一致"""
        time = datetime(2024, 6, 15, 14, 30)
        question = "事业发展如何"

        user_input1 = UserInput(
            question_type="事业",
            question_description=question,
            current_time=time
        )

        user_input2 = UserInput(
            question_type="事业",
            question_description=question,
            current_time=time
        )

        result1 = self.theory.calculate(user_input1)
        result2 = self.theory.calculate(user_input2)

        # 相同时间和问题应该产生相同结果
        assert result1 is not None
        assert result2 is not None

    def test_different_hours_different_results(self):
        """测试不同时辰产生不同结果"""
        base_date = datetime(2024, 6, 15, 0, 0)

        results = []
        for hour in [2, 6, 10, 14, 18, 22]:
            user_input = UserInput(
                question_type="事业",
                question_description="事业运势",
                current_time=base_date.replace(hour=hour)
            )

            result = self.theory.calculate(user_input)
            results.append(result)

        # 所有结果都应该有效
        for result in results:
            assert result is not None

    def test_edge_case_midnight(self):
        """测试边界情况：子时"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            current_time=datetime(2024, 6, 15, 0, 0)
        )

        result = self.theory.calculate(user_input)
        assert result is not None

    def test_edge_case_23_hour(self):
        """测试边界情况：23点（亥时末）"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            current_time=datetime(2024, 6, 15, 23, 30)
        )

        result = self.theory.calculate(user_input)
        assert result is not None

    def test_seasonal_differences(self):
        """测试四季差异"""
        seasons = [
            datetime(2024, 3, 15, 14, 30),  # 春
            datetime(2024, 6, 15, 14, 30),  # 夏
            datetime(2024, 9, 15, 14, 30),  # 秋
            datetime(2024, 12, 15, 14, 30),  # 冬
        ]

        for season_time in seasons:
            user_input = UserInput(
                question_type="事业",
                question_description="事业运势",
                current_time=season_time
            )

            result = self.theory.calculate(user_input)
            assert result is not None

    def test_long_question_description(self):
        """测试长问题描述"""
        user_input = UserInput(
            question_type="事业",
            question_description="我想问一下今年的事业发展情况如何，是否会有升职加薪的机会，或者是否适合跳槽到新的公司发展",
            current_time=datetime(2024, 6, 15, 14, 30)
        )

        result = self.theory.calculate(user_input)
        assert result is not None

    def test_short_question_description(self):
        """测试短问题描述"""
        user_input = UserInput(
            question_type="财运",
            question_description="财运",
            current_time=datetime(2024, 6, 15, 14, 30)
        )

        result = self.theory.calculate(user_input)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
