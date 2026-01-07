"""
MBTI性格分析模块 - 用于术数分析的个性化建议
"""
from typing import Dict, List, Optional


class MBTIAnalyzer:
    """MBTI性格类型分析器"""

    # MBTI 16种类型的特征描述
    MBTI_PROFILES = {
        # 分析师组（NT）
        "INTJ": {
            "name": "建筑师",
            "traits": ["战略思维", "独立自主", "追求完美", "长远规划"],
            "strengths": ["逻辑分析", "系统思考", "执行力强", "目标明确"],
            "weaknesses": ["过于理性", "不善交际", "追求完美", "情感表达困难"],
            "decision_style": "理性分析型，注重长期战略规划",
            "advice_keywords": ["系统规划", "理性分析", "独立思考", "长期目标"]
        },
        "INTP": {
            "name": "逻辑学家",
            "traits": ["好奇求知", "逻辑思维", "创新思考", "理论探索"],
            "strengths": ["分析能力", "创造力", "思维灵活", "求知欲强"],
            "weaknesses": ["行动力弱", "完美主义", "社交困难", "实践不足"],
            "decision_style": "理性探索型，需要充分的逻辑论证",
            "advice_keywords": ["深度思考", "理论验证", "创新方案", "灵活调整"]
        },
        "ENTJ": {
            "name": "指挥官",
            "traits": ["领导力强", "果断决策", "目标导向", "效率至上"],
            "strengths": ["组织能力", "执行力", "战略眼光", "魄力"],
            "weaknesses": ["过于强势", "缺乏耐心", "忽视感受", "工作狂"],
            "decision_style": "果断执行型，快速决策并立即行动",
            "advice_keywords": ["快速决策", "果断执行", "目标明确", "效率优先"]
        },
        "ENTP": {
            "name": "辩论家",
            "traits": ["思维敏捷", "善于辩论", "创新思维", "挑战权威"],
            "strengths": ["口才好", "反应快", "适应力强", "视野广"],
            "weaknesses": ["缺乏耐心", "难以专注", "逃避决策", "不守常规"],
            "decision_style": "灵活创新型，喜欢探索多种可能性",
            "advice_keywords": ["多元方案", "灵活应变", "创新思路", "开放心态"]
        },

        # 外交官组（NF）
        "INFJ": {
            "name": "提倡者",
            "traits": ["理想主义", "洞察力强", "追求意义", "关怀他人"],
            "strengths": ["同理心", "直觉准", "有原则", "坚持理想"],
            "weaknesses": ["过于敏感", "容易倦怠", "完美主义", "过度付出"],
            "decision_style": "直觉理想型，重视内心价值观和长远意义",
            "advice_keywords": ["内在价值", "意义导向", "坚持原则", "关注感受"]
        },
        "INFP": {
            "name": "调停者",
            "traits": ["理想主义", "富有创意", "价值观强", "追求和谐"],
            "strengths": ["创造力", "同理心", "适应力", "开放心态"],
            "weaknesses": ["过于理想", "逃避冲突", "拖延倾向", "自我怀疑"],
            "decision_style": "价值导向型，需要与内心价值观一致",
            "advice_keywords": ["内心和谐", "价值认同", "循序渐进", "自我成长"]
        },
        "ENFJ": {
            "name": "主人公",
            "traits": ["魅力领袖", "关怀他人", "激励他人", "社交能力强"],
            "strengths": ["影响力", "组织力", "沟通能力", "热情"],
            "weaknesses": ["过度付出", "取悦他人", "忽视自我", "承担太多"],
            "decision_style": "关怀导向型，重视对他人的积极影响",
            "advice_keywords": ["人际和谐", "团队协作", "激励他人", "关注影响"]
        },
        "ENFP": {
            "name": "竞选者",
            "traits": ["热情洋溢", "富有创意", "社交达人", "追求自由"],
            "strengths": ["沟通能力", "创造力", "适应性", "乐观积极"],
            "weaknesses": ["缺乏专注", "情绪化", "难以坚持", "过度承诺"],
            "decision_style": "热情探索型，追随兴趣和可能性",
            "advice_keywords": ["保持热情", "多元发展", "人脉资源", "灵活调整"]
        },

        # 守护者组（SJ）
        "ISTJ": {
            "name": "物流师",
            "traits": ["务实可靠", "注重细节", "守规矩", "责任心强"],
            "strengths": ["执行力", "可靠性", "组织能力", "专注"],
            "weaknesses": ["缺乏灵活", "抗拒变化", "过于严肃", "忽视情感"],
            "decision_style": "稳健务实型，依据事实和既定规则",
            "advice_keywords": ["稳扎稳打", "按部就班", "风险控制", "持续坚持"]
        },
        "ISFJ": {
            "name": "守卫者",
            "traits": ["忠诚可靠", "关怀他人", "谦逊低调", "注重传统"],
            "strengths": ["责任心", "耐心", "细心", "支持性强"],
            "weaknesses": ["过度付出", "缺乏自信", "抗拒变化", "压抑情感"],
            "decision_style": "谨慎关怀型，重视责任和他人需求",
            "advice_keywords": ["关注细节", "稳定为主", "照顾他人", "循序渐进"]
        },
        "ESTJ": {
            "name": "总经理",
            "traits": ["务实高效", "组织能力强", "决策果断", "重视秩序"],
            "strengths": ["执行力", "管理能力", "责任心", "条理性"],
            "weaknesses": ["固执己见", "缺乏灵活", "过于强势", "忽视情感"],
            "decision_style": "务实执行型，快速决策并严格执行",
            "advice_keywords": ["高效执行", "明确规划", "团队管理", "结果导向"]
        },
        "ESFJ": {
            "name": "执政官",
            "traits": ["热心助人", "社交能力强", "注重和谐", "尽职尽责"],
            "strengths": ["人际关系", "组织能力", "责任心", "同理心"],
            "weaknesses": ["过度关注他人", "需要认可", "抗拒批评", "忽视自我"],
            "decision_style": "和谐导向型，重视人际关系和社会认可",
            "advice_keywords": ["人际和谐", "团队合作", "社会认可", "关怀他人"]
        },

        # 探险家组（SP）
        "ISTP": {
            "name": "鉴赏家",
            "traits": ["冷静理性", "动手能力强", "追求自由", "善于解决问题"],
            "strengths": ["实践能力", "应变能力", "独立性", "冷静"],
            "weaknesses": ["缺乏长远规划", "情感表达困难", "冒险倾向", "不善承诺"],
            "decision_style": "实践探索型，通过实际行动验证",
            "advice_keywords": ["实践验证", "灵活应对", "解决问题", "保持冷静"]
        },
        "ISFP": {
            "name": "探险家",
            "traits": ["艺术气质", "追求美感", "活在当下", "温和友善"],
            "strengths": ["创造力", "适应力", "审美能力", "开放心态"],
            "weaknesses": ["缺乏规划", "逃避冲突", "过于敏感", "难以决策"],
            "decision_style": "感性体验型，跟随内心感受",
            "advice_keywords": ["跟随直觉", "享受过程", "美感体验", "自由发展"]
        },
        "ESTP": {
            "name": "企业家",
            "traits": ["精力充沛", "行动力强", "善于社交", "追求刺激"],
            "strengths": ["应变能力", "社交能力", "行动力", "实用主义"],
            "weaknesses": ["冲动决策", "缺乏耐心", "风险偏好", "不重视规划"],
            "decision_style": "行动冒险型，快速行动抓住机会",
            "advice_keywords": ["快速行动", "抓住机会", "灵活应变", "果断尝试"]
        },
        "ESFP": {
            "name": "表演者",
            "traits": ["活泼开朗", "社交达人", "活在当下", "热爱生活"],
            "strengths": ["人际关系", "适应力", "乐观", "表现力"],
            "weaknesses": ["缺乏规划", "容易分心", "逃避问题", "冲动"],
            "decision_style": "热情体验型，享受当下和社交互动",
            "advice_keywords": ["享受当下", "人脉资源", "保持乐观", "灵活调整"]
        },
    }

    # MBTI维度解释
    DIMENSIONS = {
        "E/I": {
            "E": {"name": "外向", "desc": "从外部世界获取能量，善于社交"},
            "I": {"name": "内向", "desc": "从内心世界获取能量，善于独处"}
        },
        "S/N": {
            "S": {"name": "实感", "desc": "关注具体事实和细节，务实"},
            "N": {"name": "直觉", "desc": "关注抽象概念和可能性，理想"}
        },
        "T/F": {
            "T": {"name": "思考", "desc": "基于逻辑和客观标准决策"},
            "F": {"name": "情感", "desc": "基于价值观和他人感受决策"}
        },
        "J/P": {
            "J": {"name": "判断", "desc": "喜欢有计划和结构，追求确定性"},
            "P": {"name": "知觉", "desc": "喜欢灵活和开放，追求可能性"}
        }
    }

    @classmethod
    def get_profile(cls, mbti_type: str) -> Optional[Dict]:
        """
        获取MBTI类型的详细信息

        Args:
            mbti_type: MBTI类型（如"INTJ"）

        Returns:
            类型信息字典
        """
        mbti_type = mbti_type.upper().strip()
        return cls.MBTI_PROFILES.get(mbti_type)

    @classmethod
    def get_advice_for_question_type(cls, mbti_type: str, question_type: str) -> List[str]:
        """
        根据MBTI类型和问题类别生成个性化建议

        Args:
            mbti_type: MBTI类型
            question_type: 问题类别

        Returns:
            建议列表
        """
        profile = cls.get_profile(mbti_type)
        if not profile:
            return []

        advice = []

        # 基于MBTI特征的通用建议
        if question_type == "事业":
            if "T" in mbti_type:  # 思考型
                advice.append("建议用逻辑分析评估职业发展路径，列出利弊清单")
            else:  # 情感型
                advice.append("建议考虑工作是否符合你的价值观和热情所在")

            if "J" in mbti_type:  # 判断型
                advice.append("建议制定清晰的职业规划和时间表")
            else:  # 知觉型
                advice.append("建议保持灵活性，探索多种职业可能性")

        elif question_type == "财运":
            if "S" in mbti_type:  # 实感型
                advice.append("建议关注具体的理财产品和投资细节")
            else:  # 直觉型
                advice.append("建议从长远趋势和大局出发规划财务")

            if "P" in mbti_type:  # 知觉型
                advice.append("注意控制冲动消费，建立预算机制")

        elif question_type in ["感情", "婚姻"]:
            if "F" in mbti_type:  # 情感型
                advice.append("跟随你的内心感受，但也要理性评估实际情况")
            else:  # 思考型
                advice.append("在理性分析的同时，不要忽视情感的重要性")

            if "I" in mbti_type:  # 内向型
                advice.append("建议主动表达内心想法，增强沟通")

        elif question_type == "健康":
            if "J" in mbti_type:
                advice.append("建议制定规律的健康管理计划并坚持执行")
            else:
                advice.append("建议选择多样化的健康活动，保持新鲜感")

        elif question_type == "择时":
            if mbti_type.startswith("E"):  # 外向型
                advice.append("选择需要社交互动和团队合作的时机")
            else:  # 内向型
                advice.append("选择适合独立思考和专注工作的时机")

        # 添加决策风格相关建议
        if profile["decision_style"]:
            advice.append(f"根据你的决策风格（{profile['decision_style']}），" +
                         "建议采用适合自己的决策方法")

        return advice

    @classmethod
    def get_summary(cls, mbti_type: str) -> str:
        """
        获取MBTI类型的简要总结

        Args:
            mbti_type: MBTI类型

        Returns:
            总结文本
        """
        profile = cls.get_profile(mbti_type)
        if not profile:
            return f"未识别的MBTI类型: {mbti_type}"

        dimensions = []
        for i, (d, letter) in enumerate([("E/I", mbti_type[0]), ("S/N", mbti_type[1]),
                                          ("T/F", mbti_type[2]), ("J/P", mbti_type[3])]):
            dim_info = cls.DIMENSIONS[d][letter]
            dimensions.append(f"{dim_info['name']}({letter})")

        summary = f"""
【MBTI类型】{mbti_type} - {profile['name']}

【性格维度】{' | '.join(dimensions)}

【核心特质】{', '.join(profile['traits'])}

【优势】{', '.join(profile['strengths'])}

【注意事项】{', '.join(profile['weaknesses'])}

【决策风格】{profile['decision_style']}
"""
        return summary.strip()

    @classmethod
    def validate_mbti_type(cls, mbti_type: str) -> bool:
        """
        验证MBTI类型是否有效

        Args:
            mbti_type: MBTI类型

        Returns:
            是否有效
        """
        mbti_type = mbti_type.upper().strip()
        return mbti_type in cls.MBTI_PROFILES

    @classmethod
    def get_all_types(cls) -> List[str]:
        """获取所有MBTI类型列表"""
        return list(cls.MBTI_PROFILES.keys())
