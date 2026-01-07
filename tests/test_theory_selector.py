"""
理论选择器测试
"""
import pytest
from datetime import datetime
from models import UserInput
from core.theory_selector import TheorySelector


class TestTheorySelector:
    """理论选择器测试"""

    def setup_method(self):
        """设置测试"""
        self.selector = TheorySelector()

    def test_select_with_full_info(self):
        """测试完整信息的理论选择"""
        user_input = UserInput(
            question_type="事业",
            question_description="想知道今年事业运势",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            birth_hour=10,
            gender="male",
            numbers=[3, 7, 5],
            current_time=datetime.now()
        )

        selected, missing_info = self.selector.select_theories(user_input)

        # 应该选择3-5个理论
        assert 3 <= len(selected) <= 5

        # 不应该有缺失信息提示
        assert missing_info is None

        # 验证选择结果结构
        for theory_info in selected:
            assert "theory" in theory_info
            assert "fitness" in theory_info
            assert "priority" in theory_info
            assert theory_info["fitness"] > 0

    def test_select_with_minimal_info(self):
        """测试最少信息的理论选择"""
        user_input = UserInput(
            question_type="决策",
            question_description="今天办事顺利吗",
            numbers=[3, 5, 7],
            current_time=datetime.now()
        )

        selected, missing_info = self.selector.select_theories(user_input)

        # 应该至少选择小六壬
        theory_names = [t["theory"] for t in selected]
        assert "小六壬" in theory_names

        # 可能有缺失信息建议
        if missing_info:
            assert isinstance(missing_info, list)

    def test_execution_order(self):
        """测试执行顺序"""
        selected = [
            {"theory": "八字", "fitness": 0.8, "priority": "基础"},
            {"theory": "小六壬", "fitness": 0.9, "priority": "快速"},
            {"theory": "奇门遁甲", "fitness": 0.7, "priority": "深度"},
        ]

        order = self.selector.determine_execution_order(selected)

        # 快速理论应该在前面
        assert order.index("小六壬") < order.index("八字")
        assert order.index("八字") < order.index("奇门遁甲")

    def test_question_matching(self):
        """测试问题匹配度计算"""
        # 事业问题应该与八字匹配度高
        score = self.selector.calculate_question_matching("事业", "八字")
        assert score > 0.5

        # 择时问题应该与奇门遁甲匹配度高
        # score = self.selector.calculate_question_matching("择时", "奇门遁甲")
        # assert score > 0.7

    def test_different_question_types(self):
        """测试不同问题类型"""
        question_types = ["事业", "财运", "感情", "健康", "决策"]

        for question_type in question_types:
            user_input = UserInput(
                question_type=question_type,
                question_description=f"关于{question_type}的问题",
                birth_year=1990,
                birth_month=6,
                birth_day=15,
                numbers=[3, 5, 7],
                current_time=datetime.now()
            )

            selected, _ = self.selector.select_theories(user_input)

            # 每种问题类型都应该能选择到理论
            assert len(selected) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
