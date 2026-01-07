"""
奇门遁甲 - 计算器
"""
from datetime import datetime
from typing import Dict, List, Any, Tuple
from .constants import *
from utils.time_utils import TimeUtils, TimestampValidator


class QiMenCalculator:
    """奇门遁甲计算器"""

    def __init__(self):
        self.time_validator = TimestampValidator(max_diff_seconds=300)

    def calculate_qimen(
        self,
        query_time: datetime,
        user_claimed_time: datetime = None,
        event_category: str = None
    ) -> Dict[str, Any]:
        """
        计算奇门遁甲

        Args:
            query_time: 实际起局时间（服务器时间）
            user_claimed_time: 用户声称的时间
            event_category: 事项类别

        Returns:
            奇门遁甲计算结果
        """
        # 时间验证
        if user_claimed_time:
            is_valid, validation_message = self.time_validator.get_validated_time(
                user_claimed_time,
                "奇门遁甲起局"
            )
            actual_time = is_valid
        else:
            actual_time = query_time
            validation_message = f"使用服务器时间起局：{TimeUtils.format_chinese_time(query_time)}"

        # 获取节气
        solar_term, _ = TimeUtils.get_solar_term(actual_time)

        # 确定阴阳遁
        dun_type = self._determine_yin_yang_dun(solar_term)

        # 计算局数
        ju_number = self._calculate_ju_number(solar_term, actual_time)

        # 计算元（上中下元）
        yuan = self._calculate_yuan(solar_term, actual_time)

        # 排九宫
        nine_palaces = self._arrange_nine_palaces(dun_type, ju_number, actual_time)

        # 确定值符值使
        duty_symbol, duty_envoy = self._calculate_duty(nine_palaces, actual_time)

        # 分析用神
        event_palace = self._analyze_event_palace(event_category, nine_palaces)

        # 分析吉凶方位
        lucky_directions, unlucky_directions = self._analyze_directions(nine_palaces)

        # 时机建议
        timing_advice = self._analyze_timing(nine_palaces, actual_time)

        # 格局分析
        patterns = self._analyze_patterns(nine_palaces)

        # 综合评分
        overall_score = self._calculate_overall_score(nine_palaces, patterns)

        return {
            "起局时间": TimeUtils.format_chinese_time(actual_time),
            "时间验证": validation_message,
            "节气": solar_term,
            "阴阳遁": dun_type,
            "局数": ju_number,
            "元": yuan,
            "九宫": nine_palaces,
            "值符": duty_symbol,
            "值使": duty_envoy,
            "用神宫位": event_palace,
            "吉利方位": lucky_directions,
            "不利方位": unlucky_directions,
            "时机建议": timing_advice,
            "格局": patterns,
            "综合评分": overall_score,
            "confidence": 0.75
        }

    def _determine_yin_yang_dun(self, solar_term: str) -> str:
        """确定阴阳遁"""
        return YIN_YANG_DUN.get(solar_term, "阳遁")

    def _calculate_ju_number(self, solar_term: str, date: datetime) -> int:
        """
        计算局数

        Args:
            solar_term: 节气
            date: 日期

        Returns:
            局数（1-9）
        """
        ju_list = JIEQI_JU.get(solar_term, [1, 2, 3])

        # 简化处理：根据日期判断上中下元
        day_in_term = (date.day - 1) % 15  # 简化计算

        if day_in_term < 5:
            yuan_index = 0  # 上元
        elif day_in_term < 10:
            yuan_index = 1  # 中元
        else:
            yuan_index = 2  # 下元

        return ju_list[yuan_index]

    def _calculate_yuan(self, solar_term: str, date: datetime) -> str:
        """计算元"""
        day_in_term = (date.day - 1) % 15

        if day_in_term < 5:
            return "上元"
        elif day_in_term < 10:
            return "中元"
        else:
            return "下元"

    def _arrange_nine_palaces(
        self,
        dun_type: str,
        ju_number: int,
        time: datetime
    ) -> List[Dict[str, Any]]:
        """
        排九宫

        Args:
            dun_type: 阴遁或阳遁
            ju_number: 局数
            time: 时间

        Returns:
            九宫列表
        """
        palaces = []

        # 简化的排盘逻辑
        # 实际奇门遁甲排盘非常复杂，这里只是示例

        for i, palace_name in enumerate(NINE_PALACES):
            # 计算九星位置（简化）
            star_index = (ju_number + i) % 9
            star = NINE_STARS[star_index]

            # 计算八门位置（简化）
            door_index = (ju_number + i) % 8
            door = EIGHT_DOORS[door_index]

            # 计算八神位置（简化）
            god_index = (time.hour + i) % 8
            god = EIGHT_GODS[god_index]

            # 天干地支（简化）
            stem_index = (ju_number + i) % 10
            stem = TEN_STEMS[stem_index]

            branch_index = (time.hour // 2 + i) % 12
            branch = TWELVE_BRANCHES[branch_index]

            palace = {
                "宫位": palace_name,
                "方位": PALACE_DIRECTIONS[palace_name],
                "九星": star,
                "八门": door,
                "八神": god,
                "天干": stem,
                "地支": branch,
                "九星属性": STAR_PROPERTIES.get(star, {}),
                "八门属性": DOOR_PROPERTIES.get(door, {}),
                "八神属性": GOD_PROPERTIES.get(god, {})
            }

            palaces.append(palace)

        return palaces

    def _calculate_duty(
        self,
        nine_palaces: List[Dict[str, Any]],
        time: datetime
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """计算值符值使"""
        # 简化处理：值符为第一个吉星所在宫位
        duty_symbol = None
        for palace in nine_palaces:
            if palace["九星属性"].get("吉凶") == "吉":
                duty_symbol = palace
                break

        if duty_symbol is None:
            duty_symbol = nine_palaces[0]

        # 值使为第一个吉门所在宫位
        duty_envoy = None
        for palace in nine_palaces:
            if palace["八门属性"].get("吉凶") == "吉":
                duty_envoy = palace
                break

        if duty_envoy is None:
            duty_envoy = nine_palaces[1]

        return duty_symbol, duty_envoy

    def _analyze_event_palace(
        self,
        event_category: str,
        nine_palaces: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析事项用神落宫"""
        # 根据事项类别确定用神
        category_palace_map = {
            "事业": "乾",
            "财运": "坤",
            "感情": "兑",
            "健康": "坎",
            "学业": "震",
            "人际": "巽"
        }

        palace_name = category_palace_map.get(event_category, "中")

        # 找到对应宫位
        for palace in nine_palaces:
            if palace["宫位"] == palace_name:
                return palace

        return nine_palaces[4]  # 默认返回中宫

    def _analyze_directions(
        self,
        nine_palaces: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """分析吉凶方位"""
        lucky = []
        unlucky = []

        for palace in nine_palaces:
            door_jiong = palace["八门属性"].get("吉凶")
            star_jiong = palace["九星属性"].get("吉凶")

            direction = palace["方位"]

            # 门和星都吉
            if door_jiong == "吉" and star_jiong == "吉":
                lucky.append(direction)
            # 门和星都凶
            elif door_jiong == "凶" and star_jiong == "凶":
                unlucky.append(direction)

        return lucky, unlucky

    def _analyze_timing(
        self,
        nine_palaces: List[Dict[str, Any]],
        time: datetime
    ) -> Dict[str, str]:
        """分析时机"""
        # 简化处理
        shi_chen, _ = TimeUtils.get_shi_chen(time.hour, time.minute)

        # 找到当前时辰对应的宫位
        current_palace = nine_palaces[time.hour % 9]

        if current_palace["八门属性"].get("吉凶") == "吉":
            return {
                "当前时辰": shi_chen,
                "时机": "适宜",
                "建议": "当前时机较好，可以行动"
            }
        else:
            return {
                "当前时辰": shi_chen,
                "时机": "不宜",
                "建议": "建议等待时机，择吉而行"
            }

    def _analyze_patterns(
        self,
        nine_palaces: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析格局"""
        patterns = []

        # 简化的格局判断
        # 实际需要根据复杂的规则判断

        # 检查是否有三奇得使
        jimen_count = sum(1 for p in nine_palaces if p["八门属性"].get("吉凶") == "吉")

        if jimen_count >= 5:
            patterns.append({
                "格局": "吉门过半",
                "吉凶": "吉",
                "说明": "吉门过半，诸事顺利"
            })

        return patterns

    def _calculate_overall_score(
        self,
        nine_palaces: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]]
    ) -> float:
        """计算综合评分"""
        score = 0.5  # 基础分

        # 吉门加分
        jimen_count = sum(1 for p in nine_palaces if p["八门属性"].get("吉凶") == "吉")
        score += (jimen_count / 8) * 0.2

        # 吉星加分
        jixing_count = sum(1 for p in nine_palaces if p["九星属性"].get("吉凶") == "吉")
        score += (jixing_count / 9) * 0.2

        # 格局加分
        for pattern in patterns:
            if pattern["吉凶"] == "吉":
                score += 0.1

        return min(score, 1.0)
