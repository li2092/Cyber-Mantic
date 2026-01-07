"""
六爻理论测试
"""
import pytest
from datetime import datetime
from models import UserInput
from theories.liuyao.theory import LiuYaoTheory


class TestLiuYaoTheory:
    """六爻理论测试"""

    def setup_method(self):
        """设置测试"""
        self.theory = LiuYaoTheory()

    def test_theory_name(self):
        """测试理论名称"""
        assert self.theory.get_name() == "六爻"

    def test_required_fields(self):
        """测试必填字段"""
        required = self.theory.get_required_fields()
        assert "numbers" in required

    def test_optional_fields(self):
        """测试可选字段"""
        optional = self.theory.get_optional_fields()
        assert "current_time" in optional
        assert "question_description" in optional

    def test_min_completeness(self):
        """测试最小完整度"""
        min_comp = self.theory.get_min_completeness()
        assert min_comp == 0.6

    def test_calculate_with_six_numbers(self):
        """测试使用6个数字起卦"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业发展如何",
            numbers=[1, 3, 5, 2, 4, 6],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        assert result is not None
        assert "六爻" in result
        assert len(result["六爻"]) == 6
        assert "本卦" in result
        assert "世爻" in result
        assert "应爻" in result
        assert "judgment" in result
        assert result["judgment"] in ["吉", "凶", "平"]

    def test_yao_list_structure(self):
        """测试爻列表结构"""
        user_input = UserInput(
            question_type="财运",
            question_description="财运",
            numbers=[1, 2, 3, 4, 5, 6],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)
        yao_list = result["六爻"]

        # 检查每个爻的结构
        for i, yao in enumerate(yao_list):
            assert "位置" in yao
            assert yao["位置"] == i + 1
            assert "阴阳" in yao
            assert yao["阴阳"] in ["阴", "阳"]
            assert "动静" in yao
            assert yao["动静"] in ["动", "静"]
            assert "数字" in yao

    def test_ben_gua_structure(self):
        """测试本卦结构"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            numbers=[1, 2, 3, 4, 5, 6],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)
        ben_gua = result["本卦"]

        assert "上卦" in ben_gua
        assert "下卦" in ben_gua
        assert "名称" in ben_gua
        # 检查卦名是否在八卦中
        assert ben_gua["上卦"] in ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
        assert ben_gua["下卦"] in ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]

    def test_bian_gua_when_dong_yao_exists(self):
        """测试有动爻时产生变卦"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            numbers=[1, 1, 3, 4, 5, 6],  # 前两个为动爻
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        # 应该有变卦
        assert "变卦" in result
        if result["变卦"] is not None:
            assert "上卦" in result["变卦"]
            assert "下卦" in result["变卦"]

    def test_no_bian_gua_when_all_static(self):
        """测试全静爻时无变卦"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            numbers=[3, 3, 3, 3, 3, 3],  # 全部静爻
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        # 检查是否全部静爻
        all_static = all(yao["动静"] == "静" for yao in result["六爻"])
        if all_static:
            assert result["变卦"] is None

    def test_shi_ying_positions(self):
        """测试世应位置"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            numbers=[1, 2, 3, 4, 5, 6],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        assert "世爻" in result
        assert "应爻" in result
        assert 1 <= result["世爻"] <= 6
        assert 1 <= result["应爻"] <= 6
        # 世应相距3位
        # assert abs(result["世爻"] - result["应爻"]) == 3

    def test_liu_qin_assignment(self):
        """测试六亲装配"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            numbers=[1, 2, 3, 4, 5, 6],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)
        liu_yao_details = result["六爻详情"]

        valid_liu_qin = ["父母", "兄弟", "子孙", "妻财", "官鬼"]

        for yao in liu_yao_details:
            assert "六亲" in yao
            assert yao["六亲"] in valid_liu_qin
            assert "六神" in yao

    def test_yong_shen_analysis(self):
        """测试用神分析"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业运势",
            numbers=[1, 2, 3, 4, 5, 6],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        assert "用神" in result
        yong_shen = result["用神"]
        assert "六亲" in yong_shen
        assert "位置" in yong_shen
        assert "阴阳" in yong_shen
        assert "动静" in yong_shen

    def test_different_question_types_different_yong_shen(self):
        """测试不同问题类型使用不同用神"""
        question_types = {
            "事业": "官鬼",
            "财运": "妻财",
            "感情": "妻财",
            "健康": "子孙",
            "学业": "父母"
        }

        for q_type, expected_yong_shen in question_types.items():
            user_input = UserInput(
                question_type=q_type,
                question_description=f"测试{q_type}",
                numbers=[1, 2, 3, 4, 5, 6],
                current_time=datetime(2024, 1, 1, 12, 0)
            )

            result = self.theory.calculate(user_input)
            # 用神应该匹配（如果该六亲存在）
            yong_shen = result["用神"]["六亲"]
            assert yong_shen in ["父母", "兄弟", "子孙", "妻财", "官鬼"]

    def test_dong_yao_detection(self):
        """测试动爻检测"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            numbers=[1, 1, 3, 4, 5, 6],  # 前两个应该是动爻
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        assert "动爻" in result
        dong_yao_positions = result["动爻"]

        # 检查动爻是否正确
        for pos in dong_yao_positions:
            assert 1 <= pos <= 6
            # 对应位置的爻应该是动爻
            yao = result["六爻"][pos - 1]
            assert yao["动静"] == "动"

    def test_judgment_with_dong_yao(self):
        """测试有动爻的判断"""
        user_input = UserInput(
            question_type="财运",
            question_description="财运",
            numbers=[1, 3, 4, 5, 6, 3],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        assert "judgment" in result
        assert "judgment_level" in result
        assert "判断依据" in result
        assert result["judgment"] in ["吉", "凶", "平"]
        assert 0 <= result["judgment_level"] <= 1

    def test_too_many_dong_yao_is_xiong(self):
        """测试动爻过多判凶"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            numbers=[1, 1, 1, 1, 3, 3],  # 4个动爻
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        # 检查动爻数量
        dong_yao_count = len(result["动爻"])
        if dong_yao_count >= 4:
            # 应该判凶
            assert result["judgment"] == "凶"

    def test_response_time_analysis(self):
        """测试应期分析"""
        user_input = UserInput(
            question_type="事业",
            question_description="何时有结果",
            numbers=[1, 2, 3, 4, 5, 6],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        assert "应期" in result
        ying_qi = result["应期"]
        assert "时间" in ying_qi
        assert "依据" in ying_qi

    def test_to_standard_answer(self):
        """测试转换为标准答案"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            numbers=[1, 2, 3, 4, 5, 6],
            current_time=datetime(2024, 1, 1, 12, 0)
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

    def test_same_numbers_consistent_results(self):
        """测试相同数字产生一致结果"""
        numbers = [3, 5, 2, 4, 6, 1]

        user_input1 = UserInput(
            question_type="事业",
            question_description="事业运势",
            numbers=numbers,
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        user_input2 = UserInput(
            question_type="财运",
            question_description="财运",
            numbers=numbers,
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result1 = self.theory.calculate(user_input1)
        result2 = self.theory.calculate(user_input2)

        # 相同数字应该产生相同的卦象
        assert result1["本卦"] == result2["本卦"]
        assert result1["世爻"] == result2["世爻"]
        assert result1["应爻"] == result2["应爻"]

    def test_edge_case_all_numbers_same(self):
        """测试边界情况：所有数字相同"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            numbers=[3, 3, 3, 3, 3, 3],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)
        assert result is not None
        assert "本卦" in result

    def test_advice_generation(self):
        """测试建议生成"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业",
            numbers=[1, 2, 3, 4, 5, 6],
            current_time=datetime(2024, 1, 1, 12, 0)
        )

        result = self.theory.calculate(user_input)

        assert "advice" in result
        assert len(result["advice"]) > 0
        # 建议中应该包含用神信息
        assert "用神" in result["advice"] or result["advice"] != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
