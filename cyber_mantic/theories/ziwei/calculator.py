"""
紫微斗数 - 计算器
"""
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from .constants import *
from utils.lunar_calendar import LunarCalendar


class ZiWeiCalculator:
    """紫微斗数计算器"""

    def __init__(self):
        pass

    def calculate_ziwei(
        self,
        birth_year: int,
        birth_month: int,
        birth_day: int,
        birth_hour: int,
        gender: str,
        calendar_type: str = "solar"
    ) -> Dict[str, Any]:
        """
        计算紫微斗数命盘

        Args:
            birth_year: 出生年
            birth_month: 出生月
            birth_day: 出生日
            birth_hour: 出生时（0-23）
            gender: 性别 "male"/"female"
            calendar_type: 历法类型 "solar"/"lunar"

        Returns:
            紫微斗数命盘信息
        """
        # 转换为农历
        if calendar_type == "solar":
            solar_date = datetime(birth_year, birth_month, birth_day, birth_hour)
            lunar_info = LunarCalendar.get_full_info(solar_date, birth_hour)
            lunar_year = lunar_info["year"]
            lunar_month = lunar_info["month"]
            lunar_day = lunar_info["day"]
        else:
            lunar_year = birth_year
            lunar_month = birth_month
            lunar_day = birth_day
            # 获取干支信息
            solar_date = LunarCalendar.lunar_to_solar(lunar_year, lunar_month, lunar_day)
            lunar_info = LunarCalendar.get_full_info(solar_date, birth_hour)

        # 1. 确定命宫
        ming_gong_dizhi = self._calculate_ming_gong(lunar_month, birth_hour)

        # 2. 确定身宫
        shen_gong_dizhi = self._calculate_shen_gong(lunar_month, birth_hour)

        # 3. 确定五局
        year_gan_zhi = lunar_info["year_gan_zhi"]
        wu_ju = self._determine_wu_ju(year_gan_zhi, ming_gong_dizhi)

        # 4. 安主星
        palaces = self._arrange_palaces(ming_gong_dizhi, shen_gong_dizhi)
        self._place_main_stars(palaces, lunar_day, wu_ju, ming_gong_dizhi)

        # 5. 安四化
        year_gan = year_gan_zhi[0]
        self._place_transformations(palaces, year_gan)

        # 6. 安辅星和煞星（简化）
        self._place_minor_stars(palaces, lunar_year, lunar_month, lunar_day, birth_hour)

        # 7. 确定命主和身主
        ming_zhu = MING_ZHU_TABLE.get(ming_gong_dizhi, "贪狼")
        year_zhi = year_gan_zhi[1]
        shen_zhu = SHEN_ZHU_TABLE.get(year_zhi, "火星")

        # 8. 分析命盘
        analysis = self._analyze_chart(palaces, ming_gong_dizhi, gender)

        return {
            "农历生日": f"{lunar_year}年{lunar_month}月{lunar_day}日",
            "干支": {
                "年": year_gan_zhi,
                "月": lunar_info.get("month_gan_zhi", ""),
                "日": lunar_info.get("day_gan_zhi", ""),
                "时": lunar_info.get("hour_gan_zhi", "")
            },
            "命宫": ming_gong_dizhi,
            "身宫": shen_gong_dizhi,
            "五局": wu_ju,
            "命主": ming_zhu,
            "身主": shen_zhu,
            "十二宫": palaces,
            "分析": analysis,
            "confidence": 0.8
        }

    def _calculate_ming_gong(self, lunar_month: int, birth_hour: int) -> str:
        """
        计算命宫

        Args:
            lunar_month: 农历月
            birth_hour: 出生时（0-23）

        Returns:
            命宫地支
        """
        # 将小时转换为地支
        hour_zhi_index = ((birth_hour + 1) // 2) % 12

        # 正月起寅宫（地支索引2），顺数到出生月
        month_pos = (2 + lunar_month - 1) % 12

        # 从出生月逆数到出生时辰
        ming_gong_index = (month_pos - hour_zhi_index) % 12

        return DI_ZHI_ORDER[ming_gong_index]

    def _calculate_shen_gong(self, lunar_month: int, birth_hour: int) -> str:
        """
        计算身宫

        Args:
            lunar_month: 农历月
            birth_hour: 出生时（0-23）

        Returns:
            身宫地支
        """
        # 正月起寅宫，顺数到出生月
        month_pos = (2 + lunar_month - 1) % 12

        # 从出生月顺数到出生时辰
        hour_zhi_index = ((birth_hour + 1) // 2) % 12
        shen_gong_index = (month_pos + hour_zhi_index) % 12

        return DI_ZHI_ORDER[shen_gong_index]

    def _determine_wu_ju(self, year_gan_zhi: str, ming_gong_dizhi: str) -> str:
        """
        确定五局（根据年干支和命宫）

        Args:
            year_gan_zhi: 年干支
            ming_gong_dizhi: 命宫地支

        Returns:
            五局名称（如"水二局"）
        """
        # 简化处理：根据命宫地支的纳音五行确定
        # 实际需要根据年干支和命宫综合判断
        nayin_map = {
            "子": "水", "丑": "土", "寅": "木", "卯": "木",
            "辰": "土", "巳": "火", "午": "火", "未": "土",
            "申": "金", "酉": "金", "戌": "土", "亥": "水"
        }

        nayin = nayin_map.get(ming_gong_dizhi, "土")
        ju_number = WU_JU_TABLE.get(nayin, 5)

        return f"{nayin}{['', '', '二', '三', '四', '五', '六'][ju_number]}局"

    def _arrange_palaces(self, ming_gong_dizhi: str, shen_gong_dizhi: str) -> List[Dict[str, Any]]:
        """
        排布十二宫

        Args:
            ming_gong_dizhi: 命宫地支
            shen_gong_dizhi: 身宫地支

        Returns:
            十二宫列表
        """
        palaces = []
        ming_gong_index = DI_ZHI_ORDER.index(ming_gong_dizhi)

        for i, palace_name in enumerate(TWELVE_PALACES):
            dizhi_index = (ming_gong_index + i) % 12
            dizhi = DI_ZHI_ORDER[dizhi_index]

            palace = {
                "宫位": palace_name,
                "地支": dizhi,
                "是命宫": (dizhi == ming_gong_dizhi),
                "是身宫": (dizhi == shen_gong_dizhi),
                "主星": [],
                "辅星": [],
                "煞星": [],
                "四化": [],
                "特质": PALACE_CHARACTERISTICS.get(palace_name, "")
            }

            palaces.append(palace)

        return palaces

    def _place_main_stars(
        self,
        palaces: List[Dict[str, Any]],
        lunar_day: int,
        wu_ju: str,
        ming_gong_dizhi: str
    ):
        """
        安主星（简化版）

        Args:
            palaces: 十二宫列表
            lunar_day: 农历日
            wu_ju: 五局
            ming_gong_dizhi: 命宫地支
        """
        # 根据五局确定紫微星位置
        if "二局" in wu_ju:
            ju_key = "水二局"
        elif "三局" in wu_ju:
            ju_key = "木三局"
        elif "四局" in wu_ju:
            ju_key = "金四局"
        elif "五局" in wu_ju:
            ju_key = "土五局"
        else:
            ju_key = "火六局"

        ziwei_dizhi = ZIWEI_POSITIONS[ju_key].get(lunar_day, "寅")

        # 找到紫微星所在宫位
        ziwei_index = None
        for i, palace in enumerate(palaces):
            if palace["地支"] == ziwei_dizhi:
                ziwei_index = i
                palace["主星"].append("紫微")
                break

        if ziwei_index is None:
            ziwei_index = 0

        # 简化的主星排布（实际需要复杂的组合规则）
        # 这里只演示部分主星的基本排布
        star_offsets = {
            "天机": 1,
            "太阳": 4,
            "武曲": 5,
            "天同": 6,
            "廉贞": 7,
            "天府": 0,  # 天府系统与紫微系统分开计算
            "太阴": 0,
            "贪狼": 2,
            "巨门": 3,
            "天相": 8,
            "天梁": 9,
            "七杀": 10,
            "破军": 11
        }

        # 安主星（简化处理）
        for star, offset in star_offsets.items():
            if star not in ["天府", "太阴"]:  # 这些星需要特殊处理
                palace_index = (ziwei_index + offset) % 12
                if star not in palaces[palace_index]["主星"]:
                    palaces[palace_index]["主星"].append(star)

    def _place_transformations(self, palaces: List[Dict[str, Any]], year_gan: str):
        """
        安四化

        Args:
            palaces: 十二宫列表
            year_gan: 年天干
        """
        transformations = TRANSFORMATION_TABLE.get(year_gan, {})

        for transformation_type, star_name in transformations.items():
            # 找到该星所在的宫位
            for palace in palaces:
                if star_name in palace["主星"]:
                    transformation_full = f"化{transformation_type}"
                    if transformation_full not in palace["四化"]:
                        palace["四化"].append(transformation_full)
                    break

    def _place_minor_stars(
        self,
        palaces: List[Dict[str, Any]],
        lunar_year: int,
        lunar_month: int,
        lunar_day: int,
        birth_hour: int
    ):
        """
        安辅星和煞星（简化版）

        Args:
            palaces: 十二宫列表
            lunar_year: 农历年
            lunar_month: 农历月
            lunar_day: 农历日
            birth_hour: 出生时
        """
        # 简化处理：随机分配部分辅星和煞星
        # 实际需要根据复杂的排布规则

        # 文昌、文曲根据出生时辰排布
        hour_zhi_index = ((birth_hour + 1) // 2) % 12

        # 文昌
        wenchang_index = (hour_zhi_index + 2) % 12
        if "文昌" not in palaces[wenchang_index]["辅星"]:
            palaces[wenchang_index]["辅星"].append("文昌")

        # 文曲
        wenqu_index = (hour_zhi_index + 8) % 12
        if "文曲" not in palaces[wenqu_index]["辅星"]:
            palaces[wenqu_index]["辅星"].append("文曲")

        # 左辅、右弼（简化）
        zuofu_index = (lunar_month - 1) % 12
        if "左辅" not in palaces[zuofu_index]["辅星"]:
            palaces[zuofu_index]["辅星"].append("左辅")

        youbi_index = (12 - lunar_month + 1) % 12
        if "右弼" not in palaces[youbi_index]["辅星"]:
            palaces[youbi_index]["辅星"].append("右弼")

    def _analyze_chart(
        self,
        palaces: List[Dict[str, Any]],
        ming_gong_dizhi: str,
        gender: str
    ) -> Dict[str, Any]:
        """
        分析命盘

        Args:
            palaces: 十二宫列表
            ming_gong_dizhi: 命宫地支
            gender: 性别

        Returns:
            分析结果
        """
        # 找到命宫
        ming_gong = None
        for palace in palaces:
            if palace["是命宫"]:
                ming_gong = palace
                break

        if ming_gong is None:
            return {"整体评价": "命盘信息不完整"}

        # 分析命宫主星
        main_stars = ming_gong.get("主星", [])
        transformations = ming_gong.get("四化", [])

        # 基本性格分析
        personality_traits = []
        if "紫微" in main_stars:
            personality_traits.append("领导能力强、有贵气、自尊心强")
        if "天机" in main_stars:
            personality_traits.append("聪明机智、善于谋略、思维活跃")
        if "太阳" in main_stars:
            personality_traits.append("光明磊落、积极进取、有正义感")
        if "武曲" in main_stars:
            personality_traits.append("刚毅果断、善于理财、讲求实际")
        if "天同" in main_stars:
            personality_traits.append("温和善良、注重享受、人缘好")

        # 事业分析
        career_palace = None
        for palace in palaces:
            if palace["宫位"] == "官禄":
                career_palace = palace
                break

        career_analysis = "事业运势"
        if career_palace and career_palace.get("主星"):
            career_stars = career_palace["主星"]
            if "紫微" in career_stars or "天府" in career_stars:
                career_analysis = "适合领导管理、政府机关或大企业工作"
            elif "武曲" in career_stars:
                career_analysis = "适合金融、财务、会计等财经相关工作"
            elif "天机" in career_stars:
                career_analysis = "适合策划、咨询、教育等智慧型工作"

        # 财运分析
        wealth_palace = None
        for palace in palaces:
            if palace["宫位"] == "财帛":
                wealth_palace = palace
                break

        wealth_analysis = "财运状况"
        if wealth_palace and wealth_palace.get("主星"):
            wealth_stars = wealth_palace["主星"]
            if "武曲" in wealth_stars or "天府" in wealth_stars:
                wealth_analysis = "财运佳，善于理财积财"
            elif "贪狼" in wealth_stars:
                wealth_analysis = "财运变化大，适合投资但需谨慎"
            elif "化禄" in wealth_palace.get("四化", []):
                wealth_analysis = "财运旺盛，有意外之财"

        # 综合评分
        score = 0.5  # 基础分
        if main_stars:
            score += 0.1
        if "化禄" in transformations:
            score += 0.15
        elif "化权" in transformations:
            score += 0.1
        elif "化科" in transformations:
            score += 0.05
        if "化忌" in transformations:
            score -= 0.1

        score = max(0.3, min(1.0, score))

        return {
            "整体评价": "命盘结构完整",
            "性格特质": personality_traits if personality_traits else ["需要结合具体星曜分析"],
            "事业运势": career_analysis,
            "财运状况": wealth_analysis,
            "命宫主星": main_stars,
            "命宫四化": transformations,
            "综合评分": score
        }
