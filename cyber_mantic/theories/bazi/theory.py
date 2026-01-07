"""
八字理论类
"""
from typing import Dict, Any, List
from models import UserInput
from theories.base import BaseTheory
from .calculator import BaZiCalculator


class BaZiTheory(BaseTheory):
    """八字理论"""

    def __init__(self):
        self.calculator = BaZiCalculator()
        super().__init__()

    def get_name(self) -> str:
        return "八字"

    def get_required_fields(self) -> List[str]:
        return ["birth_year", "birth_month", "birth_day"]

    def get_optional_fields(self) -> List[str]:
        return ["birth_hour", "gender", "birth_place_lng"]

    def get_field_weights(self) -> Dict[str, float]:
        return {
            "birth_year": 0.25,
            "birth_month": 0.25,
            "birth_day": 0.25,
            "birth_hour": 0.15,
            "gender": 0.05,
            "birth_place_lng": 0.05
        }

    def get_min_completeness(self) -> float:
        return 0.75  # 至少需要年月日

    def calculate(self, user_input: UserInput) -> Dict[str, Any]:
        """
        计算八字

        Args:
            user_input: 用户输入

        Returns:
            八字计算结果
        """
        # 计算主人八字
        result = self.calculator.calculate_full_bazi(
            year=user_input.birth_year,
            month=user_input.birth_month,
            day=user_input.birth_day,
            hour=user_input.birth_hour,
            gender=user_input.gender,
            calendar_type=user_input.calendar_type
        )

        # 添加初步判断（基于用神和五行）
        useful_god_analysis = result["用神分析"]
        wuxing_stats = result["五行统计"]

        # 简单的吉凶判断（基于五行平衡）
        wuxing_count = wuxing_stats["统计"]
        max_count = max(wuxing_count.values())
        min_count = min(wuxing_count.values())
        balance = 1 - (max_count - min_count) / sum(wuxing_count.values())

        judgment = "吉" if balance > 0.6 else ("平" if balance > 0.4 else "凶")
        judgment_level = balance

        result["judgment"] = judgment
        result["judgment_level"] = judgment_level
        result["advice"] = f"根据八字分析，您的五行{useful_god_analysis['日主强弱']}，用神为{useful_god_analysis['用神']}"

        # 如果有额外人物信息，进行多人八字分析
        if user_input.additional_persons and len(user_input.additional_persons) > 0:
            result["多人分析"] = self._analyze_multiple_persons(user_input, result)

        return result

    def _analyze_multiple_persons(self, user_input: UserInput, main_person_bazi: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析多人八字关系（姻缘匹配、帮人问事等）

        Args:
            user_input: 用户输入
            main_person_bazi: 主要人物的八字结果

        Returns:
            多人关系分析结果
        """
        multi_analysis = {
            "涉及人数": len(user_input.additional_persons) + 1,  # 包括主人
            "主要人物": user_input.name or "本人",
            "其他人物": []
        }

        # 分析每个额外人物与主人的关系
        for person in user_input.additional_persons:
            # 计算该人物的八字
            person_bazi = self.calculator.calculate_full_bazi(
                year=person.birth_year,
                month=person.birth_month,
                day=person.birth_day,
                hour=person.birth_hour or 12,  # 如果没有时辰，默认午时
                gender=person.gender,
                calendar_type="solar"  # 假设额外人物使用公历
            )

            # 根据标签判断关系类型
            relationship_type = self._determine_relationship_type(person.label, user_input.question_description)

            person_analysis = {
                "姓名/标签": person.label,
                "关系类型": relationship_type,
                "八字概要": f"{person_bazi['年柱']['天干']}{person_bazi['年柱']['地支']}年 {person_bazi['日柱']['天干']}{person_bazi['日柱']['地支']}日",
                "日主": person_bazi["日主"]
            }

            # 如果是姻缘/婚配类型，计算匹配度
            if relationship_type in ["姻缘", "婚配", "配偶"]:
                compatibility = self.calculator.calculate_marriage_compatibility(
                    main_person_bazi,
                    person_bazi
                )
                person_analysis["姻缘匹配度"] = compatibility

            # 如果是亲属/问事类型，分析代问情况
            elif relationship_type in ["父母", "子女", "亲属", "朋友", "其他"]:
                person_analysis["代问分析"] = {
                    "说明": f"为{person.label}代问，可结合其八字特点进行针对性分析",
                    "八字特点": {
                        "五行": person_bazi["五行统计"]["统计"],
                        "用神": person_bazi["用神分析"]["用神"],
                        "日主强弱": person_bazi["用神分析"]["日主强弱"]
                    }
                }

            multi_analysis["其他人物"].append(person_analysis)

        return multi_analysis

    def _determine_relationship_type(self, label: str, question: str) -> str:
        """
        根据标签和问题判断关系类型

        Args:
            label: 人物标签
            question: 用户问题

        Returns:
            关系类型
        """
        # 姻缘相关关键词
        marriage_keywords = ["对象", "男友", "女友", "伴侣", "配偶", "老公", "老婆", "丈夫", "妻子", "恋人", "爱人"]
        if any(kw in label for kw in marriage_keywords):
            return "姻缘"

        if any(kw in question for kw in ["姻缘", "婚配", "合婚", "结婚", "婚姻"]):
            return "婚配"

        # 亲属关系
        if any(kw in label for kw in ["父", "母", "爸", "妈", "爷", "奶", "公", "婆"]):
            return "父母"

        if any(kw in label for kw in ["儿", "女", "子", "孩"]):
            return "子女"

        if any(kw in label for kw in ["兄", "弟", "姐", "妹", "亲戚", "亲人"]):
            return "亲属"

        if any(kw in label for kw in ["朋友", "同事", "伙伴"]):
            return "朋友"

        return "其他"

    def to_standard_answer(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转换为标准答案格式"""
        return {
            'judgment': result.get('judgment', '平'),
            'judgment_level': result.get('judgment_level', 0.5),
            'timing': None,  # 八字的时机需要通过大运流年分析
            'advice': result.get('advice'),
            'confidence': result.get('confidence', result.get('置信度', 0.8))
        }
