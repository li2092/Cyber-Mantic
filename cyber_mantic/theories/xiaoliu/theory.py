"""
小六壬理论类
"""
from typing import Dict, Any, List, Optional
from models import UserInput
from theories.base import BaseTheory


class XiaoLiuRenTheory(BaseTheory):
    """小六壬理论"""

    # 六神定义
    LIU_SHEN = {
        "大安": {"吉凶": "吉", "五行": "木", "方位": "东", "主事": "平安、稳定", "评分": 0.75},
        "留连": {"吉凶": "凶", "五行": "土", "方位": "中", "主事": "拖延、纠缠", "评分": 0.3},
        "速喜": {"吉凶": "吉", "五行": "火", "方位": "南", "主事": "喜事、快速", "评分": 0.9},
        "赤口": {"吉凶": "凶", "五行": "金", "方位": "西", "主事": "口舌、官非", "评分": 0.2},
        "小吉": {"吉凶": "吉", "五行": "水", "方位": "北", "主事": "小吉、和合", "评分": 0.65},
        "空亡": {"吉凶": "凶", "五行": "土", "方位": "中", "主事": "落空、不成", "评分": 0.1},
    }

    # 六神顺序（从大安开始顺时针）
    LIU_SHEN_ORDER = ["大安", "留连", "速喜", "赤口", "小吉", "空亡"]

    def __init__(self):
        super().__init__()

    def get_name(self) -> str:
        return "小六壬"

    def get_required_fields(self) -> List[str]:
        return []  # 小六壬可以使用多种起卦方式

    def get_optional_fields(self) -> List[str]:
        return ["numbers", "birth_month", "birth_day", "current_time"]

    def get_field_weights(self) -> Dict[str, float]:
        return {
            "numbers": 0.5,
            "birth_month": 0.2,
            "birth_day": 0.2,
            "current_time": 0.1
        }

    def get_min_completeness(self) -> float:
        return 0.0  # 小六壬可以随时使用

    def calculate(self, user_input: UserInput) -> Dict[str, Any]:
        """
        计算小六壬

        Args:
            user_input: 用户输入

        Returns:
            小六壬计算结果
        """
        # 检查是否有多人分析请求
        if hasattr(user_input, 'additional_persons') and user_input.additional_persons:
            self.logger.warning(
                f"{self.get_name()}暂不支持多人分析，将仅分析主要咨询者，"
                f"忽略其他{len(user_input.additional_persons)}人的信息"
            )

        # 确定起卦方式
        if user_input.numbers and len(user_input.numbers) >= 3:
            # 使用数字起卦
            month_num = user_input.numbers[0]
            day_num = user_input.numbers[1]
            hour_num = user_input.numbers[2]
        else:
            # 使用时间起卦
            current_time = user_input.current_time
            month_num = current_time.month
            day_num = current_time.day
            hour_num = current_time.hour // 2  # 转换为时辰（0-11）

        # 月落宫
        month_position_index = (month_num - 1) % 6
        month_position = self.LIU_SHEN_ORDER[month_position_index]

        # 日落宫（从月落宫开始数）
        day_position_index = (month_position_index + day_num - 1) % 6
        day_position = self.LIU_SHEN_ORDER[day_position_index]

        # 时落宫（从日落宫开始数）
        hour_position_index = (day_position_index + hour_num) % 6
        final_position = self.LIU_SHEN_ORDER[hour_position_index]

        # 获取最终落宫的信息
        liu_shen_info = self.LIU_SHEN[final_position]

        # 判断吉凶
        judgment = liu_shen_info["吉凶"]
        judgment_level = liu_shen_info["评分"]

        # 生成建议
        advice = self._generate_advice(final_position, liu_shen_info)

        return {
            "起卦数字": [month_num, day_num, hour_num],
            "月落宫": month_position,
            "日落宫": day_position,
            "时落宫": final_position,
            "最终落宫": final_position,
            "六神信息": liu_shen_info,
            "judgment": judgment,
            "judgment_level": judgment_level,
            "advice": advice,
            "confidence": 1.0  # 小六壬结构简单，置信度固定
        }

    def _generate_advice(self, position: str, info: Dict[str, str]) -> str:
        """生成建议"""
        advice_map = {
            "大安": "事情平稳，可以按计划进行，不必着急",
            "留连": "事情有阻碍，容易拖延，建议耐心等待时机",
            "速喜": "吉利之象，事情进展快速，宜抓住机会",
            "赤口": "需防口舌是非，谨言慎行，避免争执",
            "小吉": "小有吉利，事情顺利但不宜期望过高",
            "空亡": "事情容易落空，建议重新评估或另作打算"
        }
        return advice_map.get(position, "请谨慎行事")

    def to_standard_answer(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转换为标准答案格式"""
        return {
            'judgment': result.get('judgment', '平'),
            'judgment_level': result.get('judgment_level', 0.5),
            'timing': None,  # 小六壬主要看吉凶，不特别论时机
            'advice': result.get('advice'),
            'confidence': result.get('confidence', 1.0)
        }
