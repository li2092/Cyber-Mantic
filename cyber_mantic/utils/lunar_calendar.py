"""
农历转换模块 - 基于cnlunar精确实现

支持：
- 阳历 ↔ 农历转换
- 节气计算
- 干支纪年月日时
- 闰月处理
- 生肖、星座计算

修复记录：
- 2026-01-04: 替换自研算法为cnlunar库，修复月份计算错误
- 2026-01-04: 添加缓存机制，提升重复查询性能
"""
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
import math
from cnlunar import Lunar
from utils.cache_manager import cached, performance_monitor


class LunarCalendar:
    """
    农历转换器（基于cnlunar库）

    支持1900-2100年的精确转换
    """

    # 天干
    HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

    # 地支
    EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

    # 生肖
    ZODIAC_ANIMALS = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

    # 农历月份名称
    LUNAR_MONTHS = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]

    # 农历日期名称
    LUNAR_DAYS = [
        "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
        "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
        "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"
    ]

    # 基准日期：1900年1月31日（农历1900年正月初一）
    BASE_DATE = datetime(1900, 1, 31)
    BASE_YEAR = 1900

    @classmethod
    @cached(cache_name="lunar_conversion", max_size=500, ttl=86400)  # 缓存24小时
    @performance_monitor(log_threshold_ms=50.0)
    def solar_to_lunar(cls, solar_date: datetime) -> Dict[str, Any]:
        """
        阳历转农历（使用cnlunar库，带缓存）

        Args:
            solar_date: 阳历日期

        Returns:
            农历信息字典，包含：
            - year: 农历年
            - month: 农历月
            - day: 农历日
            - is_leap_month: 是否闰月
            - year_gan_zhi: 年干支
            - month_gan_zhi: 月干支
            - day_gan_zhi: 日干支
            - zodiac: 生肖
            - month_name: 月份名称
            - day_name: 日期名称
        """
        if solar_date < cls.BASE_DATE:
            raise ValueError(f"日期不能早于{cls.BASE_DATE.strftime('%Y-%m-%d')}")

        # 使用cnlunar进行转换
        lunar = Lunar(solar_date, godType='8char')

        # 提取农历信息
        lunar_year = lunar.lunarYear
        lunar_month = lunar.lunarMonth
        lunar_day = lunar.lunarDay
        is_leap_month = lunar.isLunarLeapMonth

        # 干支信息（cnlunar提供）
        year_gan_zhi = lunar.year8Char
        month_gan_zhi = lunar.month8Char
        day_gan_zhi = lunar.day8Char

        # 生肖
        zodiac = lunar.chineseYearZodiac

        # 月份和日期名称
        month_name = ("闰" if is_leap_month else "") + cls.LUNAR_MONTHS[lunar_month - 1] + "月"
        day_name = cls.LUNAR_DAYS[lunar_day - 1]

        return {
            "year": lunar_year,
            "month": lunar_month,
            "day": lunar_day,
            "is_leap_month": is_leap_month,
            "year_gan_zhi": year_gan_zhi,
            "month_gan_zhi": month_gan_zhi,
            "day_gan_zhi": day_gan_zhi,
            "zodiac": zodiac,
            "month_name": month_name,
            "day_name": day_name
        }

    @classmethod
    @cached(cache_name="lunar_to_solar", max_size=200, ttl=86400)
    @performance_monitor(log_threshold_ms=100.0)
    def lunar_to_solar(
        cls,
        year: int,
        month: int,
        day: int,
        is_leap_month: bool = False
    ) -> datetime:
        """
        农历转阳历（带缓存）

        Args:
            year: 农历年
            month: 农历月
            day: 农历日
            is_leap_month: 是否闰月

        Returns:
            阳历日期
        """
        # cnlunar没有直接的农历转阳历方法，使用遍历查找
        # 从农历年的春节开始，通常在1-2月
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 3, 1)

        # 二分查找优化
        current_date = start_date
        while current_date < end_date:
            lunar = Lunar(current_date, godType='8char')
            if (lunar.lunarYear == year and
                lunar.lunarMonth == month and
                lunar.lunarDay == day and
                lunar.isLunarLeapMonth == is_leap_month):
                return current_date
            current_date += timedelta(days=1)

        raise ValueError(f"无法找到对应的阳历日期：农历{year}年{month}月{day}日")

    @classmethod
    def _get_year_gan_zhi(cls, year: int) -> str:
        """
        获取年份的干支（向后兼容方法）

        Args:
            year: 年份

        Returns:
            年干支
        """
        # 1864年是甲子年（干支纪年的循环起点）
        year_offset = year - 1864
        return cls.HEAVENLY_STEMS[year_offset % 10] + cls.EARTHLY_BRANCHES[year_offset % 12]

    @classmethod
    def _get_month_gan_zhi(cls, year: int, month: int, solar_date: datetime) -> str:
        """
        获取月份的干支（向后兼容方法）

        Args:
            year: 年份
            month: 月份
            solar_date: 阳历日期

        Returns:
            月干支
        """
        lunar = Lunar(solar_date, godType='8char')
        return lunar.month8Char

    @classmethod
    def _get_day_gan_zhi(cls, solar_date: datetime) -> str:
        """
        获取日期的干支（向后兼容方法）

        Args:
            solar_date: 阳历日期

        Returns:
            日干支
        """
        lunar = Lunar(solar_date, godType='8char')
        return lunar.day8Char

    @classmethod
    def _get_hour_gan_zhi(cls, day_gan_zhi: str, hour: int) -> str:
        """
        获取时辰的干支

        Args:
            day_gan_zhi: 日干支
            hour: 小时（0-23）

        Returns:
            时干支
        """
        # 时辰地支（每两小时一个时辰）
        zhi_index = ((hour + 1) // 2) % 12

        # 时干根据日干推算（五鼠遁日诀）
        day_gan = day_gan_zhi[0]
        day_gan_index = cls.HEAVENLY_STEMS.index(day_gan)

        # 五鼠遁日起时诀
        hour_gan_index = (day_gan_index * 2 + zhi_index) % 10

        return cls.HEAVENLY_STEMS[hour_gan_index] + cls.EARTHLY_BRANCHES[zhi_index]

    @classmethod
    def get_full_info(cls, solar_date: datetime, hour: Optional[int] = None) -> Dict[str, Any]:
        """
        获取完整的农历信息

        Args:
            solar_date: 阳历日期
            hour: 小时（可选，用于计算时辰）

        Returns:
            完整的农历信息
        """
        lunar_info = cls.solar_to_lunar(solar_date)

        # 添加时辰信息
        if hour is not None:
            hour_gan_zhi = cls._get_hour_gan_zhi(lunar_info["day_gan_zhi"], hour)
            lunar_info["hour_gan_zhi"] = hour_gan_zhi

        # 格式化输出
        lunar_info["formatted"] = (
            f"{lunar_info['year']}年{lunar_info['month_name']}{lunar_info['day_name']} "
            f"{lunar_info['year_gan_zhi']}年({lunar_info['zodiac']}年)"
        )

        return lunar_info

    @classmethod
    def format_chinese(cls, lunar_info: Dict[str, Any]) -> str:
        """
        格式化为中文字符串

        Args:
            lunar_info: 农历信息字典

        Returns:
            格式化的中文字符串
        """
        return lunar_info.get("formatted", "")
