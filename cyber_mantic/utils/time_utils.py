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


# ==================== V2增强：真太阳时计算器 ====================

# 中国主要城市经度表
CITY_LONGITUDES = {
    # 直辖市
    "北京": 116.4,
    "天津": 117.2,
    "上海": 121.5,
    "重庆": 106.5,
    # 华东
    "杭州": 120.2,
    "南京": 118.8,
    "苏州": 120.6,
    "无锡": 120.3,
    "宁波": 121.5,
    "合肥": 117.3,
    "济南": 117.0,
    "青岛": 120.4,
    "福州": 119.3,
    "厦门": 118.1,
    "南昌": 115.9,
    # 华南
    "广州": 113.3,
    "深圳": 114.1,
    "珠海": 113.6,
    "东莞": 113.7,
    "佛山": 113.1,
    "海口": 110.3,
    "南宁": 108.3,
    # 华中
    "武汉": 114.3,
    "长沙": 113.0,
    "郑州": 113.7,
    "开封": 114.3,
    # 华北
    "石家庄": 114.5,
    "太原": 112.5,
    "呼和浩特": 111.7,
    # 东北
    "沈阳": 123.4,
    "大连": 121.6,
    "长春": 125.3,
    "哈尔滨": 126.6,
    # 西南
    "成都": 104.1,
    "昆明": 102.7,
    "贵阳": 106.7,
    "拉萨": 91.1,
    # 西北
    "西安": 108.9,
    "兰州": 103.8,
    "西宁": 101.8,
    "银川": 106.3,
    "乌鲁木齐": 87.6,
    # 特别行政区
    "香港": 114.2,
    "澳门": 113.5,
    # 台湾
    "台北": 121.5,
    "高雄": 120.3,
}


class TrueSolarTimeCalculator:
    """
    V2真太阳时计算器

    功能：
    1. 根据城市名称自动获取经度
    2. 计算真太阳时
    3. 生成时辰校正说明
    4. 与ShichenHandler集成
    """

    def __init__(self, default_longitude: float = 120.0):
        """
        初始化计算器

        Args:
            default_longitude: 默认经度（未知城市时使用）
        """
        self.default_longitude = default_longitude
        self.city_longitudes = CITY_LONGITUDES.copy()

    def get_longitude(self, city: Optional[str] = None) -> float:
        """
        获取城市经度

        Args:
            city: 城市名称

        Returns:
            经度值
        """
        if city:
            # 尝试精确匹配
            if city in self.city_longitudes:
                return self.city_longitudes[city]

            # 尝试模糊匹配
            for known_city, lng in self.city_longitudes.items():
                if known_city in city or city in known_city:
                    return lng

        return self.default_longitude

    def calculate(
        self,
        local_time: datetime,
        city: Optional[str] = None,
        longitude: Optional[float] = None
    ) -> dict:
        """
        计算真太阳时

        Args:
            local_time: 北京时间
            city: 城市名称（优先使用）
            longitude: 经度（城市未知时使用）

        Returns:
            计算结果字典
        """
        # 确定经度
        if longitude is None:
            longitude = self.get_longitude(city)

        # 计算真太阳时
        true_solar_time = TimeUtils.calculate_true_solar_time(local_time, longitude)

        # 计算时差
        time_diff = true_solar_time - local_time
        diff_minutes = time_diff.total_seconds() / 60

        # 获取时辰
        local_shichen, local_idx = TimeUtils.get_shi_chen(local_time.hour, local_time.minute)
        true_shichen, true_idx = TimeUtils.get_shi_chen(true_solar_time.hour, true_solar_time.minute)

        # 判断是否跨时辰
        shichen_changed = local_idx != true_idx

        # 生成说明
        if abs(diff_minutes) < 1:
            correction_note = "时差极小，无需校正"
        elif diff_minutes > 0:
            correction_note = f"真太阳时比北京时间快{abs(diff_minutes):.1f}分钟"
        else:
            correction_note = f"真太阳时比北京时间慢{abs(diff_minutes):.1f}分钟"

        if shichen_changed:
            correction_note += f"（注意：时辰由{local_shichen}变为{true_shichen}）"

        return {
            "local_time": local_time,
            "true_solar_time": true_solar_time,
            "longitude": longitude,
            "city": city,
            "time_diff_minutes": diff_minutes,
            "local_shichen": local_shichen,
            "true_shichen": true_shichen,
            "shichen_changed": shichen_changed,
            "correction_note": correction_note,
            # 便于UI显示
            "local_time_str": local_time.strftime("%Y-%m-%d %H:%M"),
            "true_time_str": true_solar_time.strftime("%Y-%m-%d %H:%M"),
        }

    def should_use_true_solar_time(
        self,
        city: Optional[str] = None,
        longitude: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        判断是否需要使用真太阳时

        Args:
            city: 城市名称
            longitude: 经度

        Returns:
            (是否建议使用, 说明)
        """
        if longitude is None:
            longitude = self.get_longitude(city)

        # 计算与标准经度的差距
        diff = abs(longitude - 120.0)

        if diff < 5:
            return False, "该地区与北京时间基准相近，可使用标准时间"
        elif diff < 15:
            return True, f"该地区经度差{diff:.1f}°，建议使用真太阳时以提高精度"
        else:
            return True, f"该地区经度差{diff:.1f}°，强烈建议使用真太阳时"

    def get_correction_for_birth(
        self,
        birth_year: int,
        birth_month: int,
        birth_day: int,
        birth_hour: int,
        birth_minute: int = 0,
        city: Optional[str] = None,
        longitude: Optional[float] = None
    ) -> dict:
        """
        获取出生时间的真太阳时校正

        Args:
            birth_year, birth_month, birth_day: 出生日期
            birth_hour, birth_minute: 出生时间
            city: 出生城市
            longitude: 出生地经度

        Returns:
            校正结果
        """
        try:
            local_time = datetime(birth_year, birth_month, birth_day, birth_hour, birth_minute)
            result = self.calculate(local_time, city, longitude)

            # 添加出生信息专用字段
            result["birth_hour_corrected"] = result["true_solar_time"].hour
            result["birth_minute_corrected"] = result["true_solar_time"].minute
            result["use_corrected"] = result["shichen_changed"]

            if result["shichen_changed"]:
                result["recommendation"] = f"出生时辰应使用{result['true_shichen']}进行分析"
            else:
                result["recommendation"] = "时辰校正后无变化，可使用原始时辰"

            return result

        except Exception as e:
            return {
                "error": str(e),
                "use_corrected": False,
                "recommendation": "无法进行真太阳时校正，使用原始时间"
            }


# V2便捷函数

def calculate_true_solar_time(
    local_time: datetime,
    city: Optional[str] = None,
    longitude: Optional[float] = None
) -> dict:
    """
    计算真太阳时（V2便捷函数）

    Args:
        local_time: 北京时间
        city: 城市名称
        longitude: 经度

    Returns:
        计算结果字典
    """
    calculator = TrueSolarTimeCalculator()
    return calculator.calculate(local_time, city, longitude)


def get_city_longitude(city: str) -> float:
    """
    获取城市经度（V2便捷函数）

    Args:
        city: 城市名称

    Returns:
        经度值
    """
    calculator = TrueSolarTimeCalculator()
    return calculator.get_longitude(city)


def correct_birth_time(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    city: Optional[str] = None
) -> dict:
    """
    校正出生时间（V2便捷函数）

    Args:
        year, month, day, hour, minute: 出生时间
        city: 出生城市

    Returns:
        校正结果
    """
    calculator = TrueSolarTimeCalculator()
    return calculator.get_correction_for_birth(year, month, day, hour, minute, city)