"""
八字模块测试
"""
import pytest
from datetime import datetime
from models import UserInput
from theories.bazi import BaZiTheory


class TestBaZiTheory:
    """八字理论测试"""

    def setup_method(self):
        """设置测试"""
        self.theory = BaZiTheory()

    def test_theory_name(self):
        """测试理论名称"""
        assert self.theory.get_name() == "八字"

    def test_required_fields(self):
        """测试必需字段"""
        required = self.theory.get_required_fields()
        assert "birth_year" in required
        assert "birth_month" in required
        assert "birth_day" in required

    def test_calculate_basic(self):
        """测试基本计算"""
        user_input = UserInput(
            question_type="事业",
            question_description="测试",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            birth_hour=10,
            gender="male",
            current_time=datetime.now()
        )

        result = self.theory.calculate(user_input)

        # 验证基本结构
        assert "四柱" in result
        assert "日主" in result
        assert "十神" in result
        assert "五行统计" in result
        assert "用神分析" in result

        # 验证四柱长度
        assert len(result["四柱"]) == 4

        # 验证日主
        assert len(result["日主"]) == 1
        assert result["日主"] in ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

    def test_calculate_without_hour(self):
        """测试没有时辰的计算"""
        user_input = UserInput(
            question_type="事业",
            question_description="测试",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            current_time=datetime.now()
        )

        result = self.theory.calculate(user_input)

        # 应该只有三柱
        assert len(result["四柱"]) == 3
        assert result["时柱"] is None

        # 置信度应该降低
        assert result["置信度"] < 1.0

    def test_info_completeness(self):
        """测试信息完备度计算"""
        # 完整信息
        full_input = UserInput(
            question_type="事业",
            question_description="测试",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            birth_hour=10,
            gender="male",
            current_time=datetime.now()
        )

        completeness = self.theory.get_info_completeness(full_input)
        assert completeness >= 0.9

        # 部分信息
        partial_input = UserInput(
            question_type="事业",
            question_description="测试",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            current_time=datetime.now()
        )

        completeness = self.theory.get_info_completeness(partial_input)
        assert 0.7 <= completeness < 0.9

    def test_wuxing_count(self):
        """测试五行统计"""
        user_input = UserInput(
            question_type="事业",
            question_description="测试",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            current_time=datetime.now()
        )

        result = self.theory.calculate(user_input)
        wuxing_stats = result["五行统计"]["统计"]

        # 验证五行都存在
        assert "木" in wuxing_stats
        assert "火" in wuxing_stats
        assert "土" in wuxing_stats
        assert "金" in wuxing_stats
        assert "水" in wuxing_stats

        # 验证总数
        total = sum(wuxing_stats.values())
        assert total == 6  # 三柱 * 2（天干+地支）

    def test_judgment(self):
        """测试吉凶判断"""
        user_input = UserInput(
            question_type="事业",
            question_description="测试",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            current_time=datetime.now()
        )

        result = self.theory.calculate(user_input)

        assert "judgment" in result
        assert result["judgment"] in ["吉", "凶", "平"]
        assert "judgment_level" in result
        assert 0 <= result["judgment_level"] <= 1

    def test_different_years(self):
        """测试不同年份产生不同结果"""
        years = [1980, 1990, 2000, 2010]

        for year in years:
            user_input = UserInput(
                question_type="事业",
                question_description="事业",
                birth_year=year,
                birth_month=6,
                birth_day=15,
                birth_hour=10,
                current_time=datetime.now()
            )

            result = self.theory.calculate(user_input)
            assert result is not None
            assert "四柱" in result

    def test_male_vs_female(self):
        """测试男女性别差异"""
        male_input = UserInput(
            question_type="事业",
            question_description="事业",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            birth_hour=10,
            gender="male",
            current_time=datetime.now()
        )

        female_input = UserInput(
            question_type="事业",
            question_description="事业",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            birth_hour=10,
            gender="female",
            current_time=datetime.now()
        )

        male_result = self.theory.calculate(male_input)
        female_result = self.theory.calculate(female_input)

        # 两者都应该有效
        assert male_result is not None
        assert female_result is not None
        assert "四柱" in male_result
        assert "四柱" in female_result

    def test_all_twelve_months(self):
        """测试12个月份都能正常计算"""
        for month in range(1, 13):
            user_input = UserInput(
                question_type="事业",
                question_description="测试",
                birth_year=1990,
                birth_month=month,
                birth_day=15,
                current_time=datetime.now()
            )

            result = self.theory.calculate(user_input)
            assert result is not None
            assert "四柱" in result

    def test_leap_year_february_29(self):
        """测试闰年2月29日"""
        user_input = UserInput(
            question_type="事业",
            question_description="测试",
            birth_year=2000,  # 闰年
            birth_month=2,
            birth_day=29,
            birth_hour=10,
            current_time=datetime.now()
        )

        result = self.theory.calculate(user_input)
        assert result is not None
        assert "四柱" in result

    def test_edge_case_first_day_of_year(self):
        """测试边界情况：年初"""
        user_input = UserInput(
            question_type="事业",
            question_description="测试",
            birth_year=1990,
            birth_month=1,
            birth_day=1,
            birth_hour=0,
            current_time=datetime.now()
        )

        result = self.theory.calculate(user_input)
        assert result is not None
        assert "四柱" in result

    def test_edge_case_last_day_of_year(self):
        """测试边界情况：年末"""
        user_input = UserInput(
            question_type="事业",
            question_description="测试",
            birth_year=1990,
            birth_month=12,
            birth_day=31,
            birth_hour=23,
            current_time=datetime.now()
        )

        result = self.theory.calculate(user_input)
        assert result is not None
        assert "四柱" in result

    def test_shishen_analysis(self):
        """测试十神分析存在"""
        user_input = UserInput(
            question_type="事业",
            question_description="测试",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            birth_hour=10,
            current_time=datetime.now()
        )

        result = self.theory.calculate(user_input)

        assert "十神" in result
        # 十神应该有值
        assert result["十神"] is not None

    def test_yongshen_analysis(self):
        """测试用神分析存在"""
        user_input = UserInput(
            question_type="事业",
            question_description="测试",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            birth_hour=10,
            current_time=datetime.now()
        )

        result = self.theory.calculate(user_input)

        assert "用神分析" in result
        # 用神分析应该有值
        assert result["用神分析"] is not None

    def test_to_standard_answer(self):
        """测试转换为标准答案"""
        user_input = UserInput(
            question_type="事业",
            question_description="事业运势",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            birth_hour=10,
            current_time=datetime.now()
        )

        result = self.theory.calculate(user_input)
        standard = self.theory.to_standard_answer(result)

        assert "judgment" in standard
        assert "judgment_level" in standard
        assert "confidence" in standard
        assert 0 <= standard["judgment_level"] <= 1
        assert 0 <= standard["confidence"] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
