"""
MBTI性格分析器测试
"""
import pytest
from utils.mbti_analyzer import MBTIAnalyzer


class TestMBTIAnalyzer:
    """MBTI分析器测试"""

    def setup_method(self):
        """设置测试"""
        self.analyzer = MBTIAnalyzer()

    def test_all_16_types_exist(self):
        """测试16种MBTI类型都存在"""
        expected_types = [
            "INTJ", "INTP", "ENTJ", "ENTP",  # NT分析师
            "INFJ", "INFP", "ENFJ", "ENFP",  # NF外交官
            "ISTJ", "ISFJ", "ESTJ", "ESFJ",  # SJ守护者
            "ISTP", "ISFP", "ESTP", "ESFP",  # SP探险家
        ]

        for mbti_type in expected_types:
            assert mbti_type in self.analyzer.MBTI_PROFILES

    def test_profile_structure(self):
        """测试每个类型的属性结构完整"""
        required_keys = ["name", "traits", "strengths", "weaknesses",
                        "decision_style", "advice_keywords"]

        for mbti_type, profile in self.analyzer.MBTI_PROFILES.items():
            for key in required_keys:
                assert key in profile, f"{mbti_type} 缺少 {key}"

    def test_intj_profile(self):
        """测试INTJ类型详细信息"""
        intj = self.analyzer.MBTI_PROFILES["INTJ"]

        assert intj["name"] == "建筑师"
        assert "战略思维" in intj["traits"]
        assert "逻辑分析" in intj["strengths"]
        assert "过于理性" in intj["weaknesses"]
        assert "系统规划" in intj["advice_keywords"]

    def test_enfp_profile(self):
        """测试ENFP类型详细信息"""
        enfp = self.analyzer.MBTI_PROFILES["ENFP"]

        assert enfp["name"] == "竞选者"
        assert "热情洋溢" in enfp["traits"]
        assert "沟通能力" in enfp["strengths"]
        assert "缺乏专注" in enfp["weaknesses"]

    def test_traits_are_lists(self):
        """测试特质是列表类型"""
        for mbti_type, profile in self.analyzer.MBTI_PROFILES.items():
            assert isinstance(profile["traits"], list)
            assert len(profile["traits"]) > 0

    def test_strengths_are_lists(self):
        """测试优点是列表类型"""
        for mbti_type, profile in self.analyzer.MBTI_PROFILES.items():
            assert isinstance(profile["strengths"], list)
            assert len(profile["strengths"]) > 0

    def test_weaknesses_are_lists(self):
        """测试缺点是列表类型"""
        for mbti_type, profile in self.analyzer.MBTI_PROFILES.items():
            assert isinstance(profile["weaknesses"], list)
            assert len(profile["weaknesses"]) > 0

    def test_advice_keywords_are_lists(self):
        """测试建议关键词是列表类型"""
        for mbti_type, profile in self.analyzer.MBTI_PROFILES.items():
            assert isinstance(profile["advice_keywords"], list)
            assert len(profile["advice_keywords"]) > 0

    def test_decision_style_is_string(self):
        """测试决策风格是字符串类型"""
        for mbti_type, profile in self.analyzer.MBTI_PROFILES.items():
            assert isinstance(profile["decision_style"], str)
            assert len(profile["decision_style"]) > 0

    def test_all_groups_represented(self):
        """测试四大组别都有代表"""
        # NT分析师
        nt_types = ["INTJ", "INTP", "ENTJ", "ENTP"]
        for t in nt_types:
            assert t in self.analyzer.MBTI_PROFILES

        # NF外交官
        nf_types = ["INFJ", "INFP", "ENFJ", "ENFP"]
        for t in nf_types:
            assert t in self.analyzer.MBTI_PROFILES

        # SJ守护者
        sj_types = ["ISTJ", "ISFJ", "ESTJ", "ESFJ"]
        for t in sj_types:
            assert t in self.analyzer.MBTI_PROFILES

        # SP探险家
        sp_types = ["ISTP", "ISFP", "ESTP", "ESFP"]
        for t in sp_types:
            assert t in self.analyzer.MBTI_PROFILES

    def test_introvert_vs_extrovert(self):
        """测试内向和外向类型分类"""
        introverts = ["INTJ", "INTP", "INFJ", "INFP", "ISTJ", "ISFJ", "ISTP", "ISFP"]
        extroverts = ["ENTJ", "ENTP", "ENFJ", "ENFP", "ESTJ", "ESFJ", "ESTP", "ESFP"]

        for i_type in introverts:
            assert i_type.startswith("I")
            assert i_type in self.analyzer.MBTI_PROFILES

        for e_type in extroverts:
            assert e_type.startswith("E")
            assert e_type in self.analyzer.MBTI_PROFILES

    def test_unique_names(self):
        """测试每个类型的中文名称唯一"""
        names = [profile["name"] for profile in self.analyzer.MBTI_PROFILES.values()]
        assert len(names) == len(set(names))

    def test_rational_vs_emotional_types(self):
        """测试理性(T)和感性(F)类型"""
        thinking_types = [k for k in self.analyzer.MBTI_PROFILES.keys() if "T" in k[2]]
        feeling_types = [k for k in self.analyzer.MBTI_PROFILES.keys() if "F" in k[2]]

        assert len(thinking_types) == 8
        assert len(feeling_types) == 8

    def test_judging_vs_perceiving_types(self):
        """测试判断(J)和感知(P)类型"""
        judging_types = [k for k in self.analyzer.MBTI_PROFILES.keys() if k.endswith("J")]
        perceiving_types = [k for k in self.analyzer.MBTI_PROFILES.keys() if k.endswith("P")]

        assert len(judging_types) == 8
        assert len(perceiving_types) == 8

    def test_sensing_vs_intuition_types(self):
        """测试感觉(S)和直觉(N)类型"""
        sensing_types = [k for k in self.analyzer.MBTI_PROFILES.keys() if "S" in k[1]]
        intuition_types = [k for k in self.analyzer.MBTI_PROFILES.keys() if "N" in k[1]]

        assert len(sensing_types) == 8
        assert len(intuition_types) == 8

    def test_analyst_group_profiles(self):
        """测试分析师组(NT)的完整性"""
        analyst_types = ["INTJ", "INTP", "ENTJ", "ENTP"]

        for mbti_type in analyst_types:
            profile = self.analyzer.MBTI_PROFILES[mbti_type]
            assert profile is not None
            assert "name" in profile

    def test_diplomat_group_profiles(self):
        """测试外交官组(NF)的完整性"""
        diplomat_types = ["INFJ", "INFP", "ENFJ", "ENFP"]

        for mbti_type in diplomat_types:
            profile = self.analyzer.MBTI_PROFILES[mbti_type]
            assert profile is not None
            assert "name" in profile

    def test_sentinel_group_profiles(self):
        """测试守护者组(SJ)的完整性"""
        sentinel_types = ["ISTJ", "ISFJ", "ESTJ", "ESFJ"]

        for mbti_type in sentinel_types:
            profile = self.analyzer.MBTI_PROFILES[mbti_type]
            assert profile is not None
            assert "name" in profile

    def test_explorer_group_profiles(self):
        """测试探险家组(SP)的完整性"""
        explorer_types = ["ISTP", "ISFP", "ESTP", "ESFP"]

        for mbti_type in explorer_types:
            profile = self.analyzer.MBTI_PROFILES[mbti_type]
            assert profile is not None
            assert "name" in profile


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
