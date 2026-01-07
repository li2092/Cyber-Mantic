"""
QuestionClassifier - 问题类型智能识别工具

从用户问题描述中识别问题类型（事业/财运/感情等）
"""

from typing import Dict, List, Tuple


class QuestionClassifier:
    """问题类型分类器"""

    # 问题类型关键词映射
    KEYWORDS_MAP: Dict[str, List[str]] = {
        "事业": [
            "工作", "事业", "职业", "升职", "跳槽", "晋升", "转行",
            "创业", "合作", "项目", "业务", "公司", "职场", "岗位",
            "发展", "前途", "机会", "竞争", "同事", "上司", "领导",
            "离职", "求职", "应聘", "面试"
        ],
        "财运": [
            "财运", "财富", "赚钱", "收入", "投资", "理财", "股票",
            "基金", "房产", "资产", "存款", "贷款", "债务", "借钱",
            "经济", "金钱", "钱财", "发财", "破财", "花销", "开销",
            "生意", "盈利", "亏损", "收益"
        ],
        "感情": [
            "感情", "恋爱", "爱情", "对象", "伴侣", "恋人", "追求",
            "表白", "分手", "复合", "单身", "脱单", "相亲", "约会",
            "喜欢", "爱", "情侣", "男友", "女友", "前任", "现任",
            "暗恋", "告白", "情感"
        ],
        "婚姻": [
            "婚姻", "结婚", "嫁娶", "婚礼", "夫妻", "配偶", "老公",
            "老婆", "丈夫", "妻子", "离婚", "复婚", "婚外", "出轨",
            "婆媳", "姻缘", "婚配", "嫁", "娶", "婚后", "婚前"
        ],
        "健康": [
            "健康", "身体", "疾病", "生病", "医疗", "治疗", "手术",
            "养生", "调理", "病情", "康复", "体质", "精神", "心理",
            "失眠", "焦虑", "抑郁", "痊愈", "病愈", "体检"
        ],
        "学业": [
            "学业", "学习", "考试", "升学", "高考", "中考", "研究生",
            "考研", "留学", "学校", "成绩", "分数", "录取", "专业",
            "学历", "毕业", "论文", "答辩", "考证", "资格证"
        ],
        "人际": [
            "人际", "关系", "朋友", "友谊", "社交", "交友", "人缘",
            "合得来", "相处", "矛盾", "冲突", "争执", "吵架", "和好",
            "小人", "贵人", "帮助", "支持", "背叛", "信任"
        ],
        "择时": [
            "什么时候", "何时", "时机", "时间", "日期", "吉日", "吉时",
            "选日子", "挑日子", "择日", "适合", "最佳时间", "良辰",
            "吉凶", "宜", "忌", "时辰"
        ],
        "决策": [
            "选择", "决定", "决策", "该不该", "要不要", "能不能",
            "可行", "建议", "方案", "对策", "策略", "怎么办",
            "如何", "是否", "值得", "合适", "适合", "可以"
        ],
        "性格": [
            "性格", "脾气", "秉性", "天性", "特点", "特质", "个性",
            "气质", "本性", "为人", "品性", "人品", "性情"
        ]
    }

    @classmethod
    def classify(cls, question: str) -> str:
        """
        分类问题类型

        Args:
            question: 用户问题描述

        Returns:
            问题类型（事业/财运/感情/婚姻/健康/学业/人际/择时/决策/性格/综合运势）
        """
        if not question:
            return "综合运势"

        question_lower = question.lower()

        # 计算每个类型的匹配分数
        scores: Dict[str, int] = {}

        for qtype, keywords in cls.KEYWORDS_MAP.items():
            score = 0
            for keyword in keywords:
                if keyword in question_lower:
                    # 关键词越长，权重越高（更精确）
                    score += len(keyword)
            scores[qtype] = score

        # 找出最高分
        max_score = max(scores.values())

        # 如果没有任何匹配，返回综合运势
        if max_score == 0:
            return "综合运势"

        # 返回得分最高的类型
        for qtype, score in scores.items():
            if score == max_score:
                return qtype

        return "综合运势"

    @classmethod
    def classify_with_confidence(cls, question: str) -> Tuple[str, float]:
        """
        分类问题类型并返回置信度

        Args:
            question: 用户问题描述

        Returns:
            (问题类型, 置信度0-1)
        """
        if not question:
            return "综合运势", 0.0

        question_lower = question.lower()

        # 计算每个类型的匹配分数
        scores: Dict[str, int] = {}
        total_keywords_count = 0

        for qtype, keywords in cls.KEYWORDS_MAP.items():
            score = 0
            for keyword in keywords:
                if keyword in question_lower:
                    score += len(keyword)
                    total_keywords_count += 1
            scores[qtype] = score

        # 如果没有任何匹配
        if total_keywords_count == 0:
            return "综合运势", 0.0

        # 找出最高分和次高分
        sorted_scores = sorted(scores.values(), reverse=True)
        max_score = sorted_scores[0]
        second_max_score = sorted_scores[1] if len(sorted_scores) > 1 else 0

        # 计算置信度：最高分与次高分的差距越大，置信度越高
        if max_score == 0:
            confidence = 0.0
        else:
            # 归一化置信度
            confidence = min(1.0, (max_score - second_max_score) / max_score)
            # 至少0.3的基础置信度
            confidence = max(0.3, confidence)

        # 返回得分最高的类型
        for qtype, score in scores.items():
            if score == max_score:
                return qtype, confidence

        return "综合运势", 0.0


# 便捷函数
def classify_question(question: str) -> str:
    """
    分类问题类型

    Args:
        question: 用户问题描述

    Returns:
        问题类型
    """
    return QuestionClassifier.classify(question)


def classify_question_with_confidence(question: str) -> Tuple[str, float]:
    """
    分类问题类型并返回置信度

    Args:
        question: 用户问题描述

    Returns:
        (问题类型, 置信度)
    """
    return QuestionClassifier.classify_with_confidence(question)
