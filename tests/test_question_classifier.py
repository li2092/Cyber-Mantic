"""
问题分类器测试
"""
import pytest
from utils.question_classifier import QuestionClassifier


class TestQuestionClassifier:
    """问题分类器测试"""

    def test_classify_empty_question(self):
        """测试空问题"""
        result = QuestionClassifier.classify("")
        assert result == "综合运势"

    def test_classify_none_question(self):
        """测试None问题"""
        result = QuestionClassifier.classify(None)
        assert result == "综合运势"

    def test_classify_career_keywords(self):
        """测试事业相关关键词"""
        career_questions = [
            "我的工作发展如何",
            "今年事业运势怎么样",
            "能升职吗",
        ]

        for question in career_questions:
            result = QuestionClassifier.classify(question)
            assert result == "事业"

    def test_classify_wealth_keywords(self):
        """测试财运相关关键词"""
        wealth_questions = [
            "今年财运如何",
            "适合投资吗",
            "能赚钱吗",
            "股票能涨吗",
            "生意能盈利吗"
        ]

        for question in wealth_questions:
            result = QuestionClassifier.classify(question)
            assert result == "财运"

    def test_classify_love_keywords(self):
        """测试感情相关关键词"""
        love_questions = [
            "我的感情运势如何",
            "能脱单吗",
            "这段恋爱怎么样",
            "他喜欢我吗",
            "会分手吗"
        ]

        for question in love_questions:
            result = QuestionClassifier.classify(question)
            assert result == "感情"

    def test_classify_marriage_keywords(self):
        """测试婚姻相关关键词"""
        marriage_questions = [
            "婚姻如何",
            "夫妻关系好吗",
            "会离婚吗",
        ]

        for question in marriage_questions:
            result = QuestionClassifier.classify(question)
            assert result == "婚姻"

    def test_classify_health_keywords(self):
        """测试健康相关关键词"""
        health_questions = [
            "身体健康如何",
            "疾病能康复吗",
            "需要手术吗",
            "体质怎么样",
            "失眠能好吗"
        ]

        for question in health_questions:
            result = QuestionClassifier.classify(question)
            assert result == "健康"

    def test_classify_study_keywords(self):
        """测试学业相关关键词"""
        study_questions = [
            "考试能过吗",
            "能考上研究生吗",
            "学业如何",
            "成绩会提高吗",
            "能录取吗"
        ]

        for question in study_questions:
            result = QuestionClassifier.classify(question)
            assert result == "学业"

    def test_classify_interpersonal_keywords(self):
        """测试人际相关关键词"""
        interpersonal_questions = [
            "人际关系如何",
            "朋友会帮我吗",
            "会有小人吗",
            "人缘怎么样"
        ]

        for question in interpersonal_questions:
            result = QuestionClassifier.classify(question)
            assert result == "人际"

    def test_classify_timing_keywords(self):
        """测试择时相关关键词"""
        timing_questions = [
            "哪天是吉日",
            "需要择日吗",
            "吉时是什么"
        ]

        for question in timing_questions:
            result = QuestionClassifier.classify(question)
            assert result == "择时"

    def test_classify_decision_keywords(self):
        """测试决策相关关键词"""
        decision_questions = [
            "该不该接受这个offer",
            "要不要买这套房",
            "如何选择",
            "能不能做这件事",
            "是否可行"
        ]

        for question in decision_questions:
            result = QuestionClassifier.classify(question)
            assert result == "决策"

    def test_classify_personality_keywords(self):
        """测试性格相关关键词"""
        personality_questions = [
            "我的性格内向吗",
            "他的脾气暴躁吗",
            "人品好不好",
            "个性特点是什么"
        ]

        for question in personality_questions:
            result = QuestionClassifier.classify(question)
            assert result == "性格"

    def test_keywords_map_completeness(self):
        """测试关键词映射完整性"""
        expected_categories = [
            "事业", "财运", "感情", "婚姻", "健康",
            "学业", "人际", "择时", "决策", "性格"
        ]

        for category in expected_categories:
            assert category in QuestionClassifier.KEYWORDS_MAP
            assert len(QuestionClassifier.KEYWORDS_MAP[category]) > 0

    def test_all_keywords_are_strings(self):
        """测试所有关键词都是字符串"""
        for category, keywords in QuestionClassifier.KEYWORDS_MAP.items():
            assert isinstance(keywords, list)
            for keyword in keywords:
                assert isinstance(keyword, str)
                assert len(keyword) > 0

    def test_no_duplicate_keywords_within_category(self):
        """测试分类内无重复关键词"""
        for category, keywords in QuestionClassifier.KEYWORDS_MAP.items():
            assert len(keywords) == len(set(keywords)), \
                f"{category} 分类内有重复关键词"

    def test_comprehensive_fortune(self):
        """测试综合运势分类"""
        general_questions = [
            "今年运势如何",
            "明年会怎么样",
            "整体运势",
            "运气好不好"
        ]

        for question in general_questions:
            result = QuestionClassifier.classify(question)
            # 应该是综合运势或某个具体分类
            assert result in ["综合运势", "择时", "决策"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
