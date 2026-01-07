"""
紫微斗数 - 理论实现
"""
from typing import Dict, Any, List
from theories.base import BaseTheory
from models import UserInput
from .calculator import ZiWeiCalculator


class ZiWeiTheory(BaseTheory):
    """紫微斗数理论"""

    def __init__(self):
        self.calculator = ZiWeiCalculator()
        super().__init__()

    def get_name(self) -> str:
        """获取理论名称"""
        return "紫微斗数"

    def get_required_fields(self) -> List[str]:
        """获取必需字段"""
        return [
            "question_type",
            "question_description",
            "birth_year",
            "birth_month",
            "birth_day",
            "birth_hour",  # 紫微斗数必须有时辰
            "gender"  # 紫微斗数需要性别
        ]

    def get_optional_fields(self) -> List[str]:
        """获取可选字段"""
        return [
            "calendar_type"  # 历法类型
        ]

    def get_field_weights(self) -> Dict[str, float]:
        """获取字段权重"""
        return {
            "question_type": 0.15,
            "question_description": 0.15,
            "birth_year": 0.15,
            "birth_month": 0.15,
            "birth_day": 0.15,
            "birth_hour": 0.2,  # 时辰非常重要
            "gender": 0.05
        }

    def get_min_completeness(self) -> float:
        """获取最小完备度要求"""
        return 0.95  # 紫微斗数要求很高的信息完备度

    def calculate(self, user_input: UserInput) -> Dict[str, Any]:
        """
        计算紫微斗数命盘

        Args:
            user_input: 用户输入数据

        Returns:
            紫微斗数计算结果
        """
        # 检查必需字段
        if user_input.birth_hour is None:
            raise ValueError("紫微斗数必须提供出生时辰")

        if user_input.gender is None:
            raise ValueError("紫微斗数必须提供性别信息")

        # 检查是否有多人分析请求
        if hasattr(user_input, 'additional_persons') and user_input.additional_persons:
            self.logger.warning(
                f"{self.get_name()}暂不支持多人分析，将仅分析主要咨询者，"
                f"忽略其他{len(user_input.additional_persons)}人的信息"
            )

        # 执行紫微斗数计算
        result = self.calculator.calculate_ziwei(
            birth_year=user_input.birth_year,
            birth_month=user_input.birth_month,
            birth_day=user_input.birth_day,
            birth_hour=user_input.birth_hour,
            gender=user_input.gender,
            calendar_type=getattr(user_input, 'calendar_type', 'solar')
        )

        # 添加基础信息
        result['问题类型'] = user_input.question_type
        result['问题描述'] = user_input.question_description

        return result

    def to_standard_answer(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        将紫微斗数结果转换为标准答案格式

        Args:
            result: 计算结果

        Returns:
            标准答案字典
        """
        analysis = result.get('分析', {})
        score = analysis.get('综合评分', 0.5)

        # 判断等级
        if score >= 0.8:
            judgment = '大吉'
            judgment_level = score
        elif score >= 0.65:
            judgment = '吉'
            judgment_level = score
        elif score >= 0.4:
            judgment = '平'
            judgment_level = score
        elif score >= 0.25:
            judgment = '凶'
            judgment_level = score
        else:
            judgment = '大凶'
            judgment_level = score

        # 综合建议
        advice_parts = []

        # 性格特质
        personality = analysis.get('性格特质', [])
        if personality:
            advice_parts.append(f"性格特质：{' '.join(personality)}")

        # 事业运势
        career = analysis.get('事业运势', '')
        if career:
            advice_parts.append(f"事业方向：{career}")

        # 财运状况
        wealth = analysis.get('财运状况', '')
        if wealth:
            advice_parts.append(f"财运：{wealth}")

        # 命宫信息
        ming_gong_stars = analysis.get('命宫主星', [])
        if ming_gong_stars:
            advice_parts.append(f"命宫主星：{' '.join(ming_gong_stars)}")

        advice = '\n'.join(advice_parts) if advice_parts else "请参考详细命盘分析"

        return {
            'judgment': judgment,
            'judgment_level': judgment_level,
            'timing': '长期命理',  # 紫微斗数主要看长期运势
            'advice': advice,
            'confidence': result.get('confidence', 0.8),
            'detailed_result': result  # 保留完整结果供LLM解读
        }
