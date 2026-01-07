"""
时间工具模块 - 真太阳时、节气计算、时间校验
"""
from datetime import datetime, timedelta
from typing import Tuple, Optional
import math


class TimeUtils:
    """时间工具类"""

    # 中国标准时区经度（东经120度）
    CHINA_STANDARD_LONGITUDE = 120.0

    # 地球自转一度对应的时间（分钟）
    MINUTES_PER_DEGREE = 4.0

    @staticmethod
    def calculate_true_solar_time(
        local_time: datetime,
        longitude: float
    ) -> datetime:
        """
        计算真太阳时

        真太阳时 = 平太阳时 + 时差修正
        平太阳时 = 北京时间 + (当地经度 - 120°) × 4分钟

        Args:
            local_time: 当地时间（北京时间）
            longitude: 当地经度（东经为正，西经为负）

        Returns:
            真太阳时
        """
        # 计算经度时差（分钟）
        longitude_diff = longitude - TimeUtils.CHINA_STANDARD_LONGITUDE
        time_diff_minutes = longitude_diff * TimeUtils.MINUTES_PER_DEGREE

        # 计算平太阳时
        mean_solar_time = local_time + timedelta(minutes=time_diff_minutes)

        # 计算时差修正（简化版，实际应使用更精确的公式）
        equation_of_time = TimeUtils._calculate_equation_of_time(local_time)

        # 真太阳时
        true_solar_time = mean_solar_time + timedelta(minutes=equation_of_time)

        return true_solar_time

    @staticmethod
    def _calculate_equation_of_time(date: datetime) -> float:
        """
        计算时差修正（Equation of Time）

        简化公式，实际天文计算更复杂

        Args:
            date: 日期

        Returns:
            时差（分钟）
        """
        # 计算年内第几天
        day_of_year = date.timetuple().tm_yday

        # 简化的时差公式
        B = 2 * math.pi * (day_of_year - 81) / 365

        # 时差（分钟）
        equation_of_time = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)

        return equation_of_time

    @staticmethod
    def validate_qimen_timestamp(
        user_time: datetime,
        server_time: datetime,
        max_diff_seconds: int = 300
    ) -> Tuple[bool, str]:
        """
        验证奇门遁甲起卦时间戳

        确保用户提交的时间与服务器时间差距不大，防止恶意篡改

        Args:
            user_time: 用户声称的起卦时间
            server_time: 服务器接收时间
            max_diff_seconds: 允许的最大时间差（秒），默认5分钟

        Returns:
            (是否有效, 说明信息)
        """
        # 计算时间差
        time_diff = abs((user_time - server_time).total_seconds())

        if time_diff <= max_diff_seconds:
            return True, f"时间验证通过（时间差: {time_diff:.0f}秒）"
        else:
            return False, f"时间差过大（{time_diff:.0f}秒），可能不是真实起卦时间"

    @staticmethod
    def get_solar_term(date: datetime) -> Tuple[str, datetime]:
        """
        获取指定日期所在的节气

        Args:
            date: 日期

        Returns:
            (节气名称, 节气时间)
        """
        # 简化实现，使用近似日期
        # 实际应使用精确的天文算法

        year = date.year
        month = date.month

        # 二十四节气近似日期（每年可能有1-2天偏差）
        solar_terms_dates = [
            ("小寒", (1, 6)), ("大寒", (1, 20)),
            ("立春", (2, 4)), ("雨水", (2, 19)),
            ("惊蛰", (3, 6)), ("春分", (3, 21)),
            ("清明", (4, 5)), ("谷雨", (4, 20)),
            ("立夏", (5, 6)), ("小满", (5, 21)),
            ("芒种", (6, 6)), ("夏至", (6, 21)),
            ("小暑", (7, 7)), ("大暑", (7, 23)),
            ("立秋", (8, 8)), ("处暑", (8, 23)),
            ("白露", (9, 8)), ("秋分", (9, 23)),
            ("寒露", (10, 8)), ("霜降", (10, 24)),
            ("立冬", (11, 8)), ("小雪", (11, 22)),
            ("大雪", (12, 7)), ("冬至", (12, 22)),
        ]

        # 找到最近的节气
        current_term = None
        min_diff = float('inf')

        for term_name, (term_month, term_day) in solar_terms_dates:
            term_date = datetime(year, term_month, term_day)
            diff = abs((date - term_date).days)

            if diff < min_diff:
                min_diff = diff
                current_term = (term_name, term_date)

            # 如果是跨年的情况，也检查去年的节气
            if month == 1:
                term_date_prev = datetime(year - 1, term_month, term_day)
                diff_prev = abs((date - term_date_prev).days)
                if diff_prev < min_diff:
                    min_diff = diff_prev
                    current_term = (term_name, term_date_prev)

        return current_term

    @staticmethod
    def get_current_solar_term(date: datetime) -> str:
        """
        获取当前所处的节气区间

        Args:
            date: 日期

        Returns:
            节气名称
        """
        term_name, term_date = TimeUtils.get_solar_term(date)

        # 判断是在节气前还是节气后
        if date >= term_date:
            return term_name
        else:
            # 返回上一个节气
            # 简化处理
            return term_name

    @staticmethod
    def get_shi_chen(hour: int, minute: int = 0) -> Tuple[str, int]:
        """
        获取时辰

        Args:
            hour: 小时（0-23）
            minute: 分钟（0-59）

        Returns:
            (时辰名称, 时辰索引)
        """
        shi_chen_map = [
            ("子时", 23, 1),   # 23:00-01:00
            ("丑时", 1, 3),    # 01:00-03:00
            ("寅时", 3, 5),    # 03:00-05:00
            ("卯时", 5, 7),    # 05:00-07:00
            ("辰时", 7, 9),    # 07:00-09:00
            ("巳时", 9, 11),   # 09:00-11:00
            ("午时", 11, 13),  # 11:00-13:00
            ("未时", 13, 15),  # 13:00-15:00
            ("申时", 15, 17),  # 15:00-17:00
            ("酉时", 17, 19),  # 17:00-19:00
            ("戌时", 19, 21),  # 19:00-21:00
            ("亥时", 21, 23),  # 21:00-23:00
        ]

        for idx, (name, start, end) in enumerate(shi_chen_map):
            if start <= hour < end:
                return name, idx

        # 默认返回子时（23:00之后）
        return "子时", 0

    @staticmethod
    def format_chinese_time(dt: datetime) -> str:
        """
        格式化为中文时间

        Args:
            dt: 时间

        Returns:
            中文时间字符串
        """
        shi_chen, _ = TimeUtils.get_shi_chen(dt.hour, dt.minute)
        return f"{dt.year}年{dt.month}月{dt.day}日 {shi_chen}"


class TimestampValidator:
    """时间戳验证器"""

    def __init__(self, max_diff_seconds: int = 300):
        """
        初始化验证器

        Args:
            max_diff_seconds: 允许的最大时间差（秒）
        """
        self.max_diff_seconds = max_diff_seconds

    def validate(
        self,
        user_time: datetime,
        purpose: str = "起卦"
    ) -> Tuple[bool, str, datetime]:
        """
        验证时间戳

        Args:
            user_time: 用户提供的时间
            purpose: 用途说明

        Returns:
            (是否有效, 说明信息, 验证时间)
        """
        server_time = datetime.now()

        is_valid, message = TimeUtils.validate_qimen_timestamp(
            user_time,
            server_time,
            self.max_diff_seconds
        )

        if is_valid:
            return True, f"{purpose}时间验证通过：{TimeUtils.format_chinese_time(user_time)}", user_time
        else:
            # 如果时间差太大，使用服务器时间
            warning = f"警告：{message}，将使用服务器时间作为{purpose}时间"
            return False, warning, server_time

    def get_validated_time(
        self,
        user_time: Optional[datetime] = None,
        purpose: str = "起卦"
    ) -> Tuple[datetime, str]:
        """
        获取验证后的时间

        Args:
            user_time: 用户提供的时间（可选）
            purpose: 用途说明

        Returns:
            (验证后的时间, 说明信息)
        """
        if user_time is None:
            # 如果用户没有提供时间，使用当前时间
            current_time = datetime.now()
            return current_time, f"使用当前时间作为{purpose}时间：{TimeUtils.format_chinese_time(current_time)}"

        is_valid, message, validated_time = self.validate(user_time, purpose)
        return validated_time, message


# 便捷函数
def get_true_solar_time(local_time: datetime, longitude: float) -> datetime:
    """获取真太阳时（便捷函数）"""
    return TimeUtils.calculate_true_solar_time(local_time, longitude)


def validate_qimen_time(user_time: datetime) -> Tuple[bool, str]:
    """验证奇门遁甲时间（便捷函数）"""
    validator = TimestampValidator()
    is_valid, message, _ = validator.validate(user_time, "奇门遁甲起局")
    return is_valid, message


def get_current_shi_chen() -> Tuple[str, int]:
    """获取当前时辰（便捷函数）"""
    now = datetime.now()
    return TimeUtils.get_shi_chen(now.hour, now.minute)
