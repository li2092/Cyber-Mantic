"""
大六壬理论封装
"""
from typing import Dict, Any, List
from theories.base import BaseTheory
from models import UserInput
from .calculator_v2 import DaLiuRenCalculatorV2  # 使用完整版V2计算器
import json


class DaLiuRenTheory(BaseTheory):
    """大六壬理论"""

    def __init__(self):
        self.calculator = DaLiuRenCalculatorV2()  # 使用V2版本
        super().__init__()

    def get_name(self) -> str:
        return "大六壬"

    def get_category(self) -> str:
        return "占卜类"

    def get_required_fields(self) -> List[str]:
        return ["question_description", "current_time"]

    def get_optional_fields(self) -> List[str]:
        return ["initial_inquiry_time"]

    def get_field_weights(self) -> Dict[str, float]:
        return {
            "question_description": 0.3,
            "current_time": 0.4,
            "initial_inquiry_time": 0.3
        }

    def get_min_completeness(self) -> float:
        return 0.6  # 只需时间和问题即可

    def calculate(self, user_input: UserInput) -> Dict[str, Any]:
        """执行大六壬计算"""
        # 检查是否有多人分析请求
        if hasattr(user_input, 'additional_persons') and user_input.additional_persons:
            self.logger.warning(
                f"{self.get_name()}暂不支持多人分析，将仅分析主要咨询者，"
                f"忽略其他{len(user_input.additional_persons)}人的信息"
            )

        time = user_input.initial_inquiry_time or user_input.current_time

        result = self.calculator.calculate_daliuren(
            year=time.year,
            month=time.month,
            day=time.day,
            hour=time.hour,
            question=user_input.question_description
        )

        # V2版本已包含计算说明，无需重复添加
        # 如果V2未提供，则添加默认说明
        if '计算说明' not in result:
            result['计算说明'] = "使用完整版大六壬起课算法（V2），包含九宗门发用规则"

        return result

    def to_standard_answer(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转换为标准答案格式"""
        # 提取吉凶判断
        judgment = result.get("吉凶判断", result.get("judgment", "平"))
        judgment_level = result.get("综合评分", result.get("judgment_level", 0.5))

        # 提取应期（大六壬的时机信息）
        timing = result.get("应期", result.get("timing"))

        # 提取建议
        advice = result.get("advice", result.get("建议"))

        return {
            "judgment": judgment,
            "judgment_level": judgment_level,
            "timing": timing,
            "advice": advice,
            "confidence": result.get("confidence", 0.75)
        }
